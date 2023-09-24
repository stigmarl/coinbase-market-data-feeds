import json
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import typer
from websockets.sync.client import connect

from coinbase_insights import __app_name__, __version__
from coinbase_insights.db import Session, insert_feed_message
from coinbase_insights.insights import create_predictor, print_insights

COINBASE_WS_FEED = "wss://ws-feed.exchange.coinbase.com"

app = typer.Typer()


def create_subscribe_message(product_id: str):
    return {
        "type": "subscribe",
        "product_ids": [product_id],
        "channels": ["ticker_batch"],
    }


def process_message(message: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "time": datetime.strptime(message["time"], "%Y-%m-%dT%H:%M:%S.%fZ"),
        "product_id": message["product_id"],
        "price": float(message["price"]),
        "highest_bid": float(message["best_bid"]),
        "highest_bid_quantity": float(message["best_bid_size"]),
        "lowest_ask": float(message["best_ask"]),
        "lowest_ask_quantity": float(message["best_ask_size"]),
    }

    return payload


def build_dataframe(df_output, message):
    df_payload = pd.DataFrame([message])
    df_payload.index = pd.DatetimeIndex(df_payload.time)
    df_payload["diff"] = df_payload["highest_bid"] - df_payload["lowest_ask"]
    df_payload["mid_price"] = df_payload.loc[:, ["highest_bid", "lowest_ask"]].mean(
        axis=1
    )
    df_output = pd.concat([df_output, df_payload])

    return df_output


@app.command("run")
def run(
    product_id: str = typer.Option(
        "ETH-USD", "--product-id", prompt="Coinbase product id?"
    )
):
    with connect(COINBASE_WS_FEED) as websocket:
        subscribe_message = create_subscribe_message(product_id)
        websocket.send(json.dumps(subscribe_message))

        session = Session()

        df_output = pd.DataFrame()
        is_running = True
        while is_running:
            try:
                message = json.loads(websocket.recv())

                if message["type"] == "error":
                    print(f"{message['message']}: {message['reason']}")
                    exit()
                elif message["type"] == "subscriptions":
                    print(f"Subscribed to channels: {message['channels']}")
                    continue

                payload = process_message(message)
                # insert_feed_message(payload, session)
                session.commit()
                df_output = build_dataframe(df_output, payload)

                reg = create_predictor(df_output)
                tp_shift = np.array(
                    df_output.index.shift(60, freq="s").max().value
                ).reshape(-1, 1)
                mid_price_pred = reg.predict(tp_shift)
                df_output.at[
                    df_output.index.max(), "mid_price_pred_60s"
                ] = mid_price_pred[0]
                df_output["mid_price_pred"] = df_output["mid_price_pred_60s"].shift(12)
                df_output["forecast_error"] = (
                    df_output["mid_price"] - df_output["mid_price_pred"]
                ).abs()

                print_insights(df_output)

            except KeyboardInterrupt:
                print("Finished!")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return
