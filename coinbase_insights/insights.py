import pandas as pd


def current_bid_ask():
    df = pd.read_sql("feed_message", "sqlite:///database.db")
    print(df.iloc[-1])


def largest_diff_bid_ask():
    df = pd.read_sql("feed_message", "sqlite:///database.db")
    df["diff"] = df["highest_bid"] - df["lowest_ask"]
    print(df[df["diff"].abs().max() == df["diff"].abs()])


def mid_price():
    df = pd.read_sql("feed_message", "sqlite:///database.db")
    df.index = pd.DatetimeIndex(df.timestamp)
    df["mid_price"] = df.loc[:, ["highest_bid", "lowest_ask"]].mean(axis=1)
    a = df[["mid_price"]]
    a.resample("1min").mean()
    print(a.resample("1min").mean())


largest_diff_bid_ask()
