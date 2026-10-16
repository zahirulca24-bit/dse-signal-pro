from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BACKEND = Path(__file__).resolve().parents[2]

STOCK_FILE = ROOT / "dse_all_stocks_2y_ohlcv.csv"
SECTOR_FILE = BACKEND / "data/processed/sector_rotation_latest.csv"
OUTPUT = BACKEND / "data/processed/stock_scan_latest.csv"

EXCLUDED = {
    "Mutual Funds", "Corporate Bond",
    "Treasury Bond", "Debenture"
}


def rsi14(close):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    ag = gain.ewm(
        alpha=1/14, adjust=False, min_periods=14
    ).mean()

    al = loss.ewm(
        alpha=1/14, adjust=False, min_periods=14
    ).mean()

    rs = ag / al.replace(0, float("nan"))
    result = 100 - 100 / (1 + rs)

    result = result.mask((al == 0) & (ag > 0), 100)
    result = result.mask((al == 0) & (ag == 0), 50)
    return result


def number(value, digits=2):
    if pd.isna(value):
        return None
    return round(float(value), digits)


def scan_stocks(save_csv=True):
    if not STOCK_FILE.exists():
        raise FileNotFoundError(f"Missing: {STOCK_FILE}")

    if not SECTOR_FILE.exists():
        raise FileNotFoundError(
            "Run sector_rotation first: sector CSV missing"
        )

    columns = [
        "symbol", "name", "sector", "trade_date",
        "open", "high", "low", "close", "volume"
    ]

    df = pd.read_csv(
        STOCK_FILE, usecols=columns, low_memory=False
    )

    sector_df = pd.read_csv(SECTOR_FILE)
    sector_df["sector"] = sector_df["sector"].str.strip()

    sector_map = sector_df.set_index("sector").to_dict("index")

    df["trade_date"] = pd.to_datetime(
        df["trade_date"], errors="coerce"
    )

    df["symbol"] = (
        df["symbol"].astype("string").str.strip().str.upper()
    )

    df["sector"] = (
        df["sector"].astype("string").str.strip()
    )

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

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
        (df["high"] >= df[["open", "low", "close"]].max(axis=1)) &
        (df["low"] <= df[["open", "high", "close"]].min(axis=1))
    ]

    df = df[~df["sector"].isin(EXCLUDED)].copy()
    df["volume"] = df["volume"].fillna(0).clip(lower=0)

    df = df.sort_values(["symbol", "trade_date"])
    df = df.drop_duplicates(
        ["symbol", "trade_date"], keep="last"
    )

    market_date = df["trade_date"].max()

    if pd.isna(market_date):
        raise ValueError("No valid stock market dates found")

    results = []

    for symbol, g in df.groupby("symbol", sort=False):
        g = g.sort_values("trade_date")

        if len(g) < 60:
            continue

        last = g.iloc[-1]
        close = g["close"]

        ema20 = close.ewm(
            span=20, adjust=False
        ).mean()

        ema50 = close.ewm(
            span=50, adjust=False
        ).mean()

        rsi = rsi14(close)

        macd = (
            close.ewm(span=12, adjust=False).mean()
            - close.ewm(span=26, adjust=False).mean()
        )

        macd_sig = macd.ewm(
            span=9, adjust=False
        ).mean()

        avg_volume = (
            g["volume"].shift(1)
            .rolling(20, min_periods=15).mean()
            .iloc[-1]
        )

        volume_ratio = (
            last["volume"] / avg_volume
            if pd.notna(avg_volume) and avg_volume > 0
            else 0.0
        )

        previous_high = (
            g["high"].shift(1)
            .rolling(20, min_periods=20).max()
            .iloc[-1]
        )

        breakout = bool(
            pd.notna(previous_high)
            and last["close"] > previous_high
        )

        momentum5 = (
            close.iloc[-1] / close.iloc[-6] - 1
        ) * 100

        sector = str(last["sector"])
        info = sector_map.get(sector, {})

        phase = str(info.get("phase", "UNKNOWN"))
        rotation_score = float(
            info.get("rotation_score", 0) or 0
        )

        sector_count = int(info.get("stocks", 0) or 0)

        sector_aligned = bool(
            phase == "OUTPERFORMING"
            and rotation_score >= 60
            and sector_count >= 5
            and str(info.get("data_status")) == "LATEST"
        )

        price = float(close.iloc[-1])
        e20 = float(ema20.iloc[-1])
        e50 = float(ema50.iloc[-1])
        r = float(rsi.iloc[-1])

        macd_bullish = bool(
            macd.iloc[-1] > macd_sig.iloc[-1]
        )

        score = 0
        score += 15 if price > e20 else 0
        score += 15 if e20 > e50 else 0
        score += 15 if 50 <= r <= 70 else 0
        score += 15 if macd_bullish else 0
        score += 15 if volume_ratio >= 1.5 else 0
        score += 15 if breakout else 0
        score += 10 if sector_aligned else 0

        latest = last["trade_date"] == market_date

        if not latest:
            signal = "STALE_DATA"
        elif (
            score >= 80
            and price > e20 > e50
            and breakout
            and sector_aligned
            and volume_ratio >= 1.5
        ):
            signal = "STRONG_WATCH"
        elif (
            score >= 60
            and price > e20
            and macd_bullish
            and last["volume"] > 0
        ):
            signal = "BULLISH_WATCH"
        elif score >= 45:
            signal = "NEUTRAL"
        else:
            signal = "WEAK"

        if price > e20 > e50:
            trend = "UPTREND"
        elif price < e20 < e50:
            trend = "DOWNTREND"
        else:
            trend = "MIXED"

        results.append({
            "symbol": symbol,
            "name": str(last["name"]),
            "sector": sector,
            "trade_date": last["trade_date"].strftime("%Y-%m-%d"),
            "market_date": market_date.strftime("%Y-%m-%d"),
            "close": number(price),
            "ema20": number(e20),
            "ema50": number(e50),
            "rsi14": number(r),
            "volume_ratio": number(volume_ratio),
            "momentum5_pct": number(momentum5),
            "macd_bullish": macd_bullish,
            "breakout20": breakout,
            "sector_phase": phase,
            "sector_rotation_score": number(rotation_score),
            "sector_aligned": sector_aligned,
            "trend": trend,
            "score": score,
            "signal": signal
        })

    if not results:
        raise ValueError("No stocks have 60 valid observations")

    result = pd.DataFrame(results)

    # Rank current data first, then score
    result["is_latest"] = (
        result["trade_date"] == result["market_date"]
    )

    result = result.sort_values(
        ["is_latest", "score", "momentum5_pct"],
        ascending=[False, False, False]
    )

    result = result.drop(columns=["is_latest"])
    result = result.reset_index(drop=True)

    if save_csv:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(OUTPUT, index=False)

    return result.to_dict(orient="records")


if __name__ == "__main__":
    print("\n========== DSE STOCK SCANNER ==========")

    data = scan_stocks(save_csv=True)
    table = pd.DataFrame(data)

    print(f"Total scanned stocks: {len(data)}")
    print("\n========== TOP 25 STOCKS ==========")

    print(
        table[[
            "symbol", "sector", "score",
            "signal", "trend", "rsi14",
            "volume_ratio", "sector_aligned"
        ]].head(25).to_string(index=False)
    )

    print(f"\nSaved: {OUTPUT}")
