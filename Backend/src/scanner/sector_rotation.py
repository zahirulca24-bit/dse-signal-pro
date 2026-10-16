from pathlib import Path
import json
import pandas as pd

from src.scanner.sector_scanner import scan_sectors

BASE = Path(__file__).resolve().parents[2]
INPUT = BASE / "data" / "processed" / "sector_ohlcv.csv"
OUTPUT = BASE / "data" / "processed" / "sector_rotation_latest.csv"


def get_rotation(save_csv=False):
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing: {INPUT}")

    df = pd.read_csv(INPUT, parse_dates=["trade_date"])

    required = [
        "sector", "trade_date", "close",
        "volume", "stocks", "advancers"
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    for col in ["close", "volume", "stocks", "advancers"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["sector", "trade_date", "close"])
    df = df[df["close"] > 0]
    df = df.sort_values(["sector", "trade_date"])
    df = df.drop_duplicates(
        ["sector", "trade_date"], keep="last"
    )

    # Equal-weight daily sector benchmark (not DSEX)
    df["daily_return"] = df.groupby("sector")[
        "close"
    ].pct_change(fill_method=None)

    benchmark = (
        df.groupby("trade_date")["daily_return"]
        .mean().sort_index()
    )

    technical = {
        item["sector"]: item
        for item in scan_sectors(save_csv=False)
    }

    market_date = df["trade_date"].max()
    records = []

    for sector, group in df.groupby("sector"):
        g = group.sort_values("trade_date").copy()

        if len(g) < 60:
            continue

        last = g.iloc[-1]
        close = g["close"]

        sector_5d = (close.iloc[-1] / close.iloc[-6] - 1) * 100
        sector_20d = (close.iloc[-1] / close.iloc[-21] - 1) * 100

        bench = benchmark.loc[:last["trade_date"]].dropna()

        if len(bench) < 20:
            continue

        bench_5d = ((1 + bench.tail(5)).prod() - 1) * 100
        bench_20d = ((1 + bench.tail(20)).prod() - 1) * 100

        rs5 = sector_5d - bench_5d
        rs20 = sector_20d - bench_20d

        tech = technical.get(sector, {})
        technical_score = int(tech.get("score", 0))

        stocks = int(last["stocks"]) if pd.notna(last["stocks"]) else 0

        breadth = (
            last["advancers"] / stocks * 100
            if stocks > 0 and pd.notna(last["advancers"])
            else 0
        )

        volume_ratio = tech.get("volume_ratio")
        volume_ratio = float(volume_ratio or 0)

        # Relative strength classification
        if rs5 > 0 and rs20 > 0:
            phase = "OUTPERFORMING"
        elif rs5 > 0 and rs20 <= 0:
            phase = "RECOVERING"
        elif rs5 <= 0 and rs20 > 0:
            phase = "COOLING"
        else:
            phase = "UNDERPERFORMING"

        # Rotation rank score - heuristic, not probability
        rs5_points = max(0, min(35, 17.5 + rs5 * 5))
        rs20_points = max(0, min(35, 17.5 + rs20 * 2))
        breadth_points = max(0, min(20, breadth / 5))
        volume_points = max(0, min(10, volume_ratio * 5))

        rotation_score = round(
            rs5_points + rs20_points +
            breadth_points + volume_points, 1
        )

        if stocks < 5:
            indication = "LOW_COVERAGE"
        elif (
            phase == "OUTPERFORMING"
            and technical_score >= 65
            and breadth >= 55
        ):
            indication = "BULLISH_CONFIRMATION"
        elif (
            phase == "RECOVERING"
            and breadth >= 55
            and volume_ratio >= 1
        ):
            indication = "EARLY_WATCH"
        elif (
            phase == "UNDERPERFORMING"
            and technical_score < 45
        ):
            indication = "WEAK_WARNING"
        else:
            indication = "MONITOR"

        records.append({
            "sector": sector,
            "trade_date": last["trade_date"].strftime("%Y-%m-%d"),
            "data_status": (
                "LATEST"
                if last["trade_date"] == market_date
                else "STALE"
            ),
            "stocks": stocks,
            "return_5d_pct": round(sector_5d, 2),
            "return_20d_pct": round(sector_20d, 2),
            "relative_strength_5d": round(rs5, 2),
            "relative_strength_20d": round(rs20, 2),
            "breadth_pct": round(breadth, 2),
            "volume_ratio": round(volume_ratio, 2),
            "technical_score": technical_score,
            "rotation_score": rotation_score,
            "phase": phase,
            "indication": indication
        })

    if not records:
        raise ValueError("Insufficient sector history")

    result = pd.DataFrame(records)

    result = result.sort_values(
        ["rotation_score", "relative_strength_5d"],
        ascending=[False, False]
    ).reset_index(drop=True)

    result.insert(0, "rank", range(1, len(result) + 1))

    if save_csv:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(OUTPUT, index=False)

    return json.loads(result.to_json(orient="records"))


if __name__ == "__main__":
    print("\n========== SECTOR ROTATION SCANNER ==========")

    results = get_rotation(save_csv=True)
    table = pd.DataFrame(results)

    print(table[[
        "rank", "sector", "rotation_score",
        "relative_strength_5d",
        "relative_strength_20d",
        "phase", "indication"
    ]].to_string(index=False))

    print(f"\nTotal sectors: {len(results)}")
    print(f"Saved: {OUTPUT}")
