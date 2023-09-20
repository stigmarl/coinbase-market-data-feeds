import json
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from websockets.sync.client import connect

engine = create_engine("sqlite:///database.db", echo=True)
Base = declarative_base()


class FeedMessage(Base):
    __tablename__ = "feed_message"
    timestamp = Column(DateTime, primary_key=True)
    product_id = Column(String(20), primary_key=True)
    price = Column(Float)
    highest_bid = Column(Float)
    highest_bid_quantity = Column(Float)
    lowest_ask = Column(Float)
    lowest_ask_quantity = Column(Float)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


COINBASE_WS_FEED = "wss://ws-feed.exchange.coinbase.com"

subscribe_message = {
    "type": "subscribe",
    "product_ids": ["BTC-USD"],
    "channels": ["ticker_batch"],
}


def hello():
    with connect(COINBASE_WS_FEED) as websocket:
        websocket.send(json.dumps(subscribe_message))
        running = True
        while running:
            try:
                message = json.loads(websocket.recv())
                if message["type"] == "subscriptions":
                    continue
                feed_message = FeedMessage()
                # 2023-09-20T15:35:35.033824Z
                feed_message.timestamp = datetime.strptime(
                    message["time"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                feed_message.product_id = message["product_id"]
                feed_message.price = message["price"]
                feed_message.highest_bid = message["best_bid"]
                feed_message.highest_bid_quantity = message["best_bid_size"]
                feed_message.lowest_ask = message["best_ask"]
                feed_message.lowest_ask_quantity = message["best_ask_size"]
                session.add(feed_message)
                session.commit()
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
