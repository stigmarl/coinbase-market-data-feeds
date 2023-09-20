import json

from websockets.sync.client import connect

from db import Session, insert_feed_message

COINBASE_WS_FEED = "wss://ws-feed.exchange.coinbase.com"

subscribe_message = {
    "type": "subscribe",
    "product_ids": ["BTC-USD"],
    "channels": ["ticker_batch"],
}


def hello():
    with connect(COINBASE_WS_FEED) as websocket:
        session = Session()

        websocket.send(json.dumps(subscribe_message))
        # receive subscriptions message
        running = True
        while running:
            try:
                message = json.loads(websocket.recv())
                insert_feed_message(message, session)
                print(f"Received {message}")
            except KeyboardInterrupt:
                session.close()
                running = False
                print("Finished!")
            except:
                session.close()
                running = False
                print("Finished!")


if __name__ == "__main__":
    hello()
