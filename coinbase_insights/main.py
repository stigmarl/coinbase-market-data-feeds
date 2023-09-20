import json
from datetime import datetime
from typing import Any, Dict

import pandas as pd
from websockets.sync.client import connect

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


def build_dataframe(df_output, df_message):
    df_payload = pd.DataFrame([payload])
    df_output = pd.concat([df_output, df_payload])
    df_output["diff"] = df_output["highest_bid"] - df_output["lowest_ask"]

    return df_output


def print_insights(df_output):
    df_output.index = pd.DatetimeIndex(df_output.time)
    current = df_output.iloc[-1]

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

    df_output["mid_price"] = df_output.loc[:, ["highest_bid", "lowest_ask"]].mean(
        axis=1
    )

    mid_price = df_output[["mid_price"]]
    for m in [1, 5, 15]:
        avg_mid_price = mid_price.resample(f"{m}min").mean().iloc[-1]
        print(f"Average mid-price in last {m} minutes: {avg_mid_price}")
    print("\n\n")


if __name__ == "__main__":
    with connect(COINBASE_WS_FEED) as websocket:
        subscribe_message = create_subscribe_message("ETH-USD")
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
                print_insights(df_output)

            except KeyboardInterrupt:
                print("Finished!")
