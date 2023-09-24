import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def show_runtime_elapsed(df: pd.DataFrame):
    print("*" * 40)
    print(f"Current timestamp: {df.index.max()}")
    print(
        f"Total runtime: {(df.index.max() - df.index.min()) / pd.Timedelta('1s'):.1f} seconds"
    )
    print("*" * 40)


def show_current_bid_ask(df: pd.DataFrame):
    current = df.iloc[-1]

    print(f"Current highest bid: {current['highest_bid']}")
    print(f"At quantity:     {current['highest_bid_quantity']}")
    print(f"Current lowest ask:  {current['lowest_ask']}")
    print(f"At quantity:     {current['lowest_ask_quantity']}")
    print("-" * 40 + "\n")


def show_largest_diff_bid_ask(df: pd.DataFrame):
    highest_diff = df[df["diff"].abs().max() == df["diff"].abs()].iloc[0]
    print(f"Biggest difference between bid and ask: {highest_diff['diff']:.3f}")
    print("-" * 40 + "\n")


def show_average_mid_price(df: pd.DataFrame):
    mid_price = df[["mid_price"]]
    for m in [1, 5, 15]:
        avg_mid_price = (
            mid_price.resample(f"{m}min", origin="end").mean().iloc[-1]["mid_price"]
        )
        print(f"Average mid-price in last {m} minutes: {avg_mid_price:.3f}")
    print("-" * 40 + "\n")


def show_forecasts(df: pd.DataFrame):
    forecast_60s = df.iloc[-1]["mid_price_pred_60s"]
    print(f"Forecast in 60 s: {forecast_60s:.3f}")

    forecast_error = df[["forecast_error"]]
    for m in [1, 5, 15]:
        avg_forecast_error = (
            forecast_error.resample(f"{m}min", origin="end")
            .mean()
            .iloc[-1]["forecast_error"]
        )
        print(f"Average forecast error in last {m} minutes: {avg_forecast_error:.3f}")
    print("-" * 40 + "\n")


def print_insights(df_output):
    print()

    show_runtime_elapsed(df_output)

    show_current_bid_ask(df_output)

    show_largest_diff_bid_ask(df_output)

    show_average_mid_price(df_output)

    show_forecasts(df_output)


def create_predictor(df) -> LinearRegression:
    linear_regressor = LinearRegression()
    X = df.index.values.astype("int64").reshape(-1, 1)
    Y = df["mid_price"].values.astype("float64").reshape(-1, 1)
    linear_regressor.fit(X, Y)

    return linear_regressor


def calculate_forecasts(df: pd.DataFrame) -> pd.DataFrame:
    reg = create_predictor(df)

    tp_shift = np.array(df.index.shift(60, freq="s").max().value).reshape(-1, 1)

    mid_price_pred = reg.predict(tp_shift)

    df.at[df.index.max(), "mid_price_pred_60s"] = mid_price_pred[0]

    df["mid_price_pred"] = df["mid_price_pred_60s"].shift(12)
    df["forecast_error"] = (df["mid_price"] - df["mid_price_pred"]).abs()

    return df
