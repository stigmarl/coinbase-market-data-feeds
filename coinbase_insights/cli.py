import json
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import typer
from websockets.sync.client import connect

from coinbase_insights import __app_name__, __version__
from coinbase_insights.insights import calculate_forecasts, print_insights

COINBASE_WS_FEED = "wss://ws-feed.exchange.coinbase.com"

app = typer.Typer()


def create_subscribe_message(product_id: str) -> Dict[str, Any]:
    """Creates a subscribe message used to subscribe to a specific product
    in the Coinbase `ticker_batch` channel.

    Args:
        product_id (str): Coinbase product to receive feed messages for.

    Returns:
        Dict[str, Any]: Payload for subscribing to websocket.
    """
    return {
        "type": "subscribe",
        "product_ids": [product_id],
        "channels": ["ticker_batch"],
    }


def process_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Processes a feed message to rename and cast message keys and
    values to suitabler names and types.

    Args:
        message (Dict[str, Any]): Coinbase `ticker_batch` message.

    Returns:
        Dict[str, Any]: Processed message with keys and values:
        - time: datetime
        - product_id: str
        - price: float
        - highest_bid: float
        - highest_bid_quantity: float
        - lowest_ask: float
        - lowest_ask_quantity: float

    """

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


def build_dataframe(df_output: pd.DataFrame, message: Dict[str, Any]):
    """Appends the most recent feed message to the already collected
    feed message DataFrame. Sets the payload time as index, and adds
    the `diff` and `mid_price` columns.

    Args:
        df_output (pd.DataFrame): Previously collected feed message data.
        message (Dict[str, Any]): Processed recent feed message.

    Returns:
        pd.DataFrame: Collected feed message data with most recent message.
    """
    df_payload = pd.DataFrame([message])
    df_payload.index = pd.DatetimeIndex(df_payload.time)
    df_payload["diff"] = df_payload["highest_bid"] - df_payload["lowest_ask"]
    df_payload["mid_price"] = df_payload.loc[:, ["highest_bid", "lowest_ask"]].mean(
        axis=1
    )
    df_output = pd.concat([df_output, df_payload])

    return df_output


@app.command(
    "run",
    help="Receive metrics every five seconds for a specified Coinbase product.",
    short_help="Run application to receive metrics.",
)
def run(
    product_id: str = typer.Option(
        "ETH-USD", "--product-id", prompt="Coinbase product id?"
    )
):
    with connect(COINBASE_WS_FEED) as websocket:
        subscribe_message = create_subscribe_message(product_id)
        websocket.send(json.dumps(subscribe_message))

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
                df_output = build_dataframe(df_output, payload)

                df_output = calculate_forecasts(df_output)

                print_insights(df_output)

            except KeyboardInterrupt:
                print("Keyboard interrupt received, closing down...")
                exit()


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
