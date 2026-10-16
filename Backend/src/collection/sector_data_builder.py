from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "dse_all_stocks_2y_ohlcv.csv"
OUTPUT = ROOT / "Backend" / "data" / "processed" / "sector_ohlcv.csv"

COLUMNS = [
    "symbol", "sector", "trade_date",
    "open", "high", "low", "close", "volume"
]


def build_sector_ohlcv():
    print("\n========== DSE SECTOR OHLCV BUILDER ==========")

    if not INPUT.exists():
        raise FileNotFoundError(f"CSV missing: {INPUT}")

    df = pd.read_csv(INPUT, usecols=COLUMNS, low_memory=False)

    print(f"Loaded {len(df):,} stock records")

    # Clean column values
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["trade_date"] = pd.to_datetime(
        df["trade_date"], errors="coerce"
    )

    df["symbol"] = (
        df["symbol"].astype("string").str.strip().str.upper()
    )

    df["sector"] = df["sector"].astype("string").str.strip()

    df = df.dropna(subset=[
        "symbol", "sector", "trade_date",
        "open", "high", "low", "close"
    ])

    df = df[
        (df["symbol"] != "") &
        (df["sector"] != "")
    ]

    prices = ["open", "high", "low", "close"]

    df = df[(df[prices] > 0).all(axis=1)]

    df = df[
        (df["high"] >= df[["open", "close", "low"]].max(axis=1)) &
        (df["low"] <= df[["open", "close", "high"]].min(axis=1))
    ]

    df["volume"] = df["volume"].fillna(0).clip(lower=0)

    df = df.sort_values(["symbol", "trade_date"])
    df = df.drop_duplicates(
        ["symbol", "trade_date"], keep="last"
    )

    # Calculate previous closing price by stock
    df["prev_close"] = df.groupby(
        ["sector", "symbol"]
    )["close"].shift(1)

    df = df[df["prev_close"] > 0].copy()

    if df.empty:
        raise ValueError("No valid stock returns found")

    # Normalize prices against previous stock close
    for price in prices:
        df[price + "_ratio"] = (
            df[price] / df["prev_close"]
        )

    df["advancer"] = (df["close_ratio"] > 1).astype(int)
    df["decliner"] = (df["close_ratio"] < 1).astype(int)

    # Equal-weight synthetic sector returns
    daily = df.groupby(
        ["sector", "trade_date"], as_index=False
    ).agg(
        open_ratio=("open_ratio", "mean"),
        high_ratio=("high_ratio", "mean"),
        low_ratio=("low_ratio", "mean"),
        close_ratio=("close_ratio", "mean"),
        volume=("volume", "sum"),
        stocks=("symbol", "nunique"),
        advancers=("advancer", "sum"),
        decliners=("decliner", "sum")
    )

    daily = daily.sort_values(
        ["sector", "trade_date"]
    ).reset_index(drop=True)

    # Initial index baseline = 100
    daily["close_index"] = 100 * daily.groupby(
        "sector"
    )["close_ratio"].cumprod()

    daily["previous_index_close"] = (
        daily["close_index"] / daily["close_ratio"]
    )

    for price in ["open", "high", "low"]:
        daily[price] = (
            daily["previous_index_close"] *
            daily[price + "_ratio"]
        )

    daily["return_pct"] = (
        daily["close_ratio"] - 1
    ) * 100

    daily = daily.rename(columns={
        "close_index": "close"
    })

    result = daily[[
        "sector", "trade_date",
        "open", "high", "low", "close",
        "volume", "stocks",
        "advancers", "decliners", "return_pct"
    ]].copy()

    result["trade_date"] = (
        result["trade_date"].dt.strftime("%Y-%m-%d")
    )

    numeric = [
        "open", "high", "low",
        "close", "return_pct"
    ]

    result[numeric] = result[numeric].round(4)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)

    print("\nSECTOR DATA CREATED SUCCESSFULLY!")
    print(f"Total sectors: {result['sector'].nunique()}")
    print(f"Sector-day records: {len(result):,}")
    print(f"Saved: {OUTPUT}")

    print("\n========== LATEST SECTOR PERFORMANCE ==========")

    latest = (
        result.sort_values("trade_date")
        .groupby("sector")
        .tail(1)
        .sort_values("return_pct", ascending=False)
    )

    print(
        latest[[
            "sector", "trade_date",
            "close", "return_pct", "stocks"
        ]].to_string(index=False)
    )


if __name__ == "__main__":
    build_sector_ohlcv()
