import json
from datetime import datetime
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from websockets.sync.client import connect

from coinbase_insights.db import Session, insert_feed_message

COINBASE_WS_FEED = "wss://ws-feed.exchange.coinbase.com"


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


def print_insights(df_output):
    current = df_output.iloc[-1]

    print("*" * 40)
    print(f"Current timestamp: {current.time}")
    print(
        f"Total runtime: {(df_output.index.max() - df_output.index.min()) / pd.Timedelta('1s'):.1f} seconds"
    )
    print()

    print(f"Current highest bid: {current['highest_bid']}")
    print(f"\tAt quantity:     {current['highest_bid_quantity']}")
    print(f"Current lowest ask:  {current['lowest_ask']}")
    print(f"\tAt quantity:     {current['lowest_ask_quantity']}")
    print()

    highest_diff = df_output[
        df_output["diff"].abs().max() == df_output["diff"].abs()
    ].iloc[0]
    print(f"Highest diff: {highest_diff['diff']:.3f}")
    print()

    mid_price = df_output[["mid_price"]]
    for m in [1, 5, 15]:
        avg_mid_price = (
            mid_price.resample(f"{m}min", origin="end").mean().iloc[-1]["mid_price"]
        )
        print(f"Average mid-price in last {m} minutes: {avg_mid_price:.3f}")
    print("\n")

    forecast_60s = df_output.iloc[-1]["mid_price_pred_60s"]
    print(f"Forecast in 60 s: {forecast_60s:.3f}")

    forecast_error = df_output[["forecast_error"]]
    for m in [1, 5, 15]:
        avg_forecast_error = (
            forecast_error.resample(f"{m}min", origin="end")
            .mean()
            .iloc[-1]["forecast_error"]
        )
        print(f"Average forecast error in last {m} minutes: {avg_forecast_error:.3f}")
    print("\n")


def create_predictor(df) -> LinearRegression:
    linear_regressor = LinearRegression()
    X = df.index.values.astype("int64").reshape(-1, 1)
    Y = df["mid_price"].values.astype("float64").reshape(-1, 1)
    linear_regressor.fit(X, Y)

    return linear_regressor


if __name__ == "__main__":
    with connect(COINBASE_WS_FEED) as websocket:
        subscribe_message = create_subscribe_message("ETH-USD")
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
