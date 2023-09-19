import json

from websockets.sync.client import connect

COINBASE_WS_FEED = "wss://ws-feed.exchange.coinbase.com"

subscribe_message = {
    "type": "subscribe",
    "product_ids": ["BTC-USD"],
    "channels": ["ticker_batch", {"name": "ticker", "product_ids": ["BTC-USD"]}],
}


def hello():
    with connect(COINBASE_WS_FEED) as websocket:
        websocket.send(json.dumps(subscribe_message))
        while True:
            message = json.loads(websocket.recv())
            print(f"Received {message}")


if __name__ == "__main__":
    hello()
