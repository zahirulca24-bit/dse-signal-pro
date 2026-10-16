from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
INPUT = BASE / "data" / "processed" / "sector_ohlcv.csv"
OUTPUT = BASE / "data" / "processed" / "sector_scan_latest.csv"


def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.ewm(
        alpha=1 / period, adjust=False,
        min_periods=period
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period, adjust=False,
        min_periods=period
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50)

    return rsi


def safe_number(value, decimals=2):
    if pd.isna(value) or not np.isfinite(float(value)):
        return None
    return round(float(value), decimals)


def scan_sectors(save_csv=False):
    if not INPUT.exists():
        raise FileNotFoundError(
            "sector_ohlcv.csv missing. Run sector_data_builder first."
        )

    df = pd.read_csv(INPUT)

    required = [
        "sector", "trade_date", "close", "volume",
        "stocks", "advancers", "decliners"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["trade_date"] = pd.to_datetime(
        df["trade_date"], errors="coerce"
    )

    for col in ["close", "volume", "stocks", "advancers"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=[
        "sector", "trade_date", "close"
    ])

    df = df[df["close"] > 0]
    df = df.sort_values(["sector", "trade_date"])

    market_date = df["trade_date"].max()
    results = []

    for sector, group in df.groupby("sector"):
        g = group.drop_duplicates(
            "trade_date", keep="last"
        ).sort_values("trade_date").copy()

        if len(g) < 55:
            continue

        close = g["close"]

        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()

        rsi = calculate_rsi(close)

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()

        macd = ema12 - ema26
        macd_signal = macd.ewm(
            span=9, adjust=False
        ).mean()

        previous_volume = g["volume"].shift(1)

        avg_volume20 = previous_volume.rolling(
            window=20, min_periods=10
        ).mean()

        last = g.iloc[-1]
        i = -1

        volume_base = avg_volume20.iloc[i]

        volume_ratio = (
            last["volume"] / volume_base
            if pd.notna(volume_base) and volume_base > 0
            else np.nan
        )

        breadth = (
            last["advancers"] / last["stocks"] * 100
            if pd.notna(last["stocks"]) and last["stocks"] > 0
            else np.nan
        )

        return_5d = (
            close.iloc[-1] / close.iloc[-6] - 1
        ) * 100

        score = 0

        if close.iloc[i] > ema20.iloc[i]:
            score += 20

        if ema20.iloc[i] > ema50.iloc[i]:
            score += 20

        if 50 <= rsi.iloc[i] <= 70:
            score += 15

        if macd.iloc[i] > macd_signal.iloc[i]:
            score += 20

        if pd.notna(volume_ratio) and volume_ratio >= 1.3:
            score += 15

        if pd.notna(breadth) and breadth >= 60:
            score += 10

        if score >= 80:
            signal = "STRONG_BULLISH_SETUP"
        elif score >= 65:
            signal = "BULLISH_WATCH"
        elif score >= 45:
            signal = "NEUTRAL"
        else:
            signal = "WEAK_TREND"

        if close.iloc[i] > ema20.iloc[i] > ema50.iloc[i]:
            trend = "UPTREND"
        elif close.iloc[i] < ema20.iloc[i] < ema50.iloc[i]:
            trend = "DOWNTREND"
        else:
            trend = "MIXED"

        results.append({
            "sector": str(sector),
            "trade_date": last["trade_date"].strftime("%Y-%m-%d"),
            "data_status": (
                "LATEST"
                if last["trade_date"] == market_date
                else "STALE"
            ),
            "close": safe_number(close.iloc[i]),
            "ema20": safe_number(ema20.iloc[i]),
            "ema50": safe_number(ema50.iloc[i]),
            "rsi14": safe_number(rsi.iloc[i]),
            "macd": safe_number(macd.iloc[i], 4),
            "macd_signal": safe_number(macd_signal.iloc[i], 4),
            "volume_ratio": safe_number(volume_ratio),
            "breadth_pct": safe_number(breadth),
            "return_5d_pct": safe_number(return_5d),
            "stocks": int(last["stocks"]),
            "trend": trend,
            "score": score,
            "signal": signal
        })

    if not results:
        raise ValueError("Not enough sector history for scanning")

    result = pd.DataFrame(results)

    result = result.sort_values(
        ["score", "return_5d_pct"],
        ascending=[False, False]
    ).reset_index(drop=True)

    if save_csv:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(OUTPUT, index=False)

    return result.to_dict(orient="records")


if __name__ == "__main__":
    print("\n========== DSE SECTOR MARKET SCANNER ==========")

    results = scan_sectors(save_csv=True)

    table = pd.DataFrame(results)

    print(table[[
        "sector", "trade_date", "score",
        "signal", "trend", "rsi14",
        "volume_ratio", "breadth_pct"
    ]].to_string(index=False))

    print(f"\nTotal scanned sectors: {len(results)}")
    print(f"Saved: {OUTPUT}")
