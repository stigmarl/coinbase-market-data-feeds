import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def show_runtime_elapsed(df: pd.DataFrame):
    """Prints current/max timestamp and total runtime of the application in seconds.

    Args:
        df (pd.DataFrame): Collected feed message data.
    """
    print("*" * 40)
    print(f"Current timestamp: {df.index.max()}")
    print(
        f"Total runtime: {(df.index.max() - df.index.min()) / pd.Timedelta('1s'):.1f} seconds"
    )
    print("*" * 40)


def show_current_bid_ask(df: pd.DataFrame):
    """Prints the highest bid and lowest ask, with quantities, in the current,
    most recent feed message. Expects the following DataFrame columns:
    - highest_bid
    - highest_bid_quantity
    - lowest_ask
    - lowest_ask_quantity

    Args:
        df (pd.DataFrame): Collected feed message data.
    """
    current = df.iloc[-1]

    print(f"Current highest bid: {current['highest_bid']}")
    print(f"At quantity:     {current['highest_bid_quantity']}")
    print(f"Current lowest ask:  {current['lowest_ask']}")
    print(f"At quantity:     {current['lowest_ask_quantity']}")
    print("-" * 40 + "\n")


def show_largest_diff_bid_ask(df: pd.DataFrame):
    """Prints the largest difference between highest ask and
    lowest ask in the data collected so far. Expects the following
    DataFrame columns:
    - diff

    Args:
        df (pd.DataFrame): Collected feed message data.
    """

    highest_diff = df[df["diff"].abs().max() == df["diff"].abs()].iloc[0]
    print(f"Biggest difference between bid and ask: {highest_diff['diff']:.3f}")
    print("-" * 40 + "\n")


def show_average_mid_price(df: pd.DataFrame):
    """Prints the average mid-price in the last 1, 5 and 15 minutes.
    Expects the following DataFrame columns:
    - mid_price

    Args:
        df (pd.DataFrame): Collected feed message data.
    """

    mid_price = df[["mid_price"]]
    for m in [1, 5, 15]:
        avg_mid_price = (
            mid_price.resample(f"{m}min", origin="end").mean().iloc[-1]["mid_price"]
        )
        print(f"Average mid-price in last {m} minutes: {avg_mid_price:.3f}")
    print("-" * 40 + "\n")


def show_forecasts(df: pd.DataFrame):
    """Prints the forecasted mid-price error in 60 seconds,
    in addition to the average mid-price forecasting errors in the
    last 1, 5 and 15 minutes. Expects the following DataFrame columns:
    - mid_price_pred_60s
    - forecast_error

    Args:
        df (pd.DataFrame): Collected feed message data.
    """

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


def print_insights(df_output: pd.DataFrame):
    """Prints insights calculated from the collected data:
    - Elapsed runtime and current timestamp.
    - Current highest bid and lowest ask, with quantites.
    - Largest difference between highest bid and lowest ask seen so far.
    - Average mid-price in the last 1, 5, 15 minutes.
    - Forecasted mid-price in 60 seconds.
    - Forecasting error on predicted mid-price in the last 1, 5, 15 minutes.

    Args:
        df_output (pd.DataFrame): Collected feed message data.
    """

    print()

    show_runtime_elapsed(df_output)

    show_current_bid_ask(df_output)

    show_largest_diff_bid_ask(df_output)

    show_average_mid_price(df_output)

    show_forecasts(df_output)


def create_predictor(df: pd.DataFrame) -> LinearRegression:
    """Creates a linear regression model to predict future mid-price values.
    Expects the following DataFrame columns:
    - mid_price

    Args:
        df (pd.DataFrame): Collected feed message data.

    Returns:
        LinearRegression: Linear model fitted to the mid-price values seen so far.
    """
    linear_regressor = LinearRegression()
    X = df.index.values.astype("int64").reshape(-1, 1)
    Y = df["mid_price"].values.astype("float64").reshape(-1, 1)
    linear_regressor.fit(X, Y)

    return linear_regressor


def calculate_forecasts(df: pd.DataFrame) -> pd.DataFrame:
    """Trains a new predictor, predicts a forecasted mid-price value
    60 seconds in the future relative to the most recent timestamp,
    adds the value to the most recent row, and calculates the forecasting error.
    Expects the following DataFrame columns:
    - mid_price

    Assumes that a new row is added to the DataFrame every 5 seconds, as the forecast
    for 60 seconds ahead is stored in the current row. The forecasted value for the
    current row therefore will be 12 rows back, i.e. 12 * 5 seconds = 60 seconds ago.

    Args:
        df (pd.DataFrame): Collected feed message data.

    Returns:
        pd.DataFrame: Added columns of future mid-price forecasts and errors:
        - mid_price_pred_60s
        - mid_price_pred
        - forecast_error
    """
    reg = create_predictor(df)

    tp_shift = np.array(df.index.shift(60, freq="s").max().value).reshape(-1, 1)

    mid_price_pred = reg.predict(tp_shift)

    df.at[df.index.max(), "mid_price_pred_60s"] = mid_price_pred[0]

    df["mid_price_pred"] = df["mid_price_pred_60s"].shift(12)
    df["forecast_error"] = (df["mid_price"] - df["mid_price_pred"]).abs()

    return df
