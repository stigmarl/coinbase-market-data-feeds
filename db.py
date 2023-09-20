from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Float, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

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


def insert_feed_message(message: dict[str, Any], session: Session):
    feed_message = FeedMessage()
    feed_message.timestamp = datetime.strptime(message["time"], "%Y-%m-%dT%H:%M:%S.%fZ")
    feed_message.product_id = message["product_id"]
    feed_message.price = message["price"]
    feed_message.highest_bid = message["best_bid"]
    feed_message.highest_bid_quantity = message["best_bid_size"]
    feed_message.lowest_ask = message["best_ask"]
    feed_message.lowest_ask_quantity = message["best_ask_size"]
    session.add(feed_message)
    session.commit()


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
