"""
DSE Stock Historical Trade Auditor & Decision Rationale Engine.
Scans historical OHLCV data for any stock, detects validated setups,
tracks trade execution forward in time (Entry -> SL / TP),
identifies avoided trap days, and calculates bot performance metrics.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BY_SYMBOL_DIR = ROOT / "by_symbol"


def calculate_rsi14(series: pd.Series) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    al = loss.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = ag / al.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def audit_stock_history(
    symbol: str = "FEKDIL",
    period: str = "6M",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    strategy_filter: str = "ALL"
) -> Dict[str, Any]:
    sym = symbol.strip().upper()
    csv_path = BY_SYMBOL_DIR / f"{sym}.csv"

    if not csv_path.exists():
        return {
            "status": "error",
            "message": f"Historical CSV for '{sym}' not found in by_symbol directory."
        }

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return {"status": "error", "message": f"Failed to read CSV for '{sym}': {str(e)}"}

    if df.empty or "trade_date" not in df.columns:
        return {"status": "error", "message": f"Data for '{sym}' is empty or invalid."}

    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")
    df = df.dropna(subset=["trade_date", "close", "volume"]).sort_values("trade_date").reset_index(drop=True)

    if len(df) < 30:
        return {"status": "error", "message": f"Insufficient trading history for '{sym}' (less than 30 sessions)."}

    # Compute technical indicators across entire history
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["vol_sma20"] = df["volume"].shift(1).rolling(20, min_periods=10).mean()
    df["vol_ratio"] = df["volume"] / df["vol_sma20"].replace(0, np.nan)
    df["high20"] = df["high"].shift(1).rolling(20, min_periods=15).max()
    df["rsi14"] = calculate_rsi14(df["close"])

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # Determine Period Filtering
    max_dt = df["trade_date"].max()
    if start_date and end_date:
        mask = (df["trade_date"] >= pd.to_datetime(start_date)) & (df["trade_date"] <= pd.to_datetime(end_date))
    elif period == "3M":
        cutoff = max_dt - pd.Timedelta(days=95)
        mask = df["trade_date"] >= cutoff
    elif period == "6M":
        cutoff = max_dt - pd.Timedelta(days=185)
        mask = df["trade_date"] >= cutoff
    elif period == "1Y":
        cutoff = max_dt - pd.Timedelta(days=365)
        mask = df["trade_date"] >= cutoff
    else:  # ALL (2 Years)
        mask = pd.Series(True, index=df.index)

    period_df = df[mask].copy()
    if len(period_df) < 15:
        # Fallback to last 60 sessions if date range too narrow
        period_df = df.tail(60).copy()

    start_idx = period_df.index[0]
    end_idx = period_df.index[-1]

    trades: List[Dict[str, Any]] = []
    avoided_traps: List[Dict[str, Any]] = []

    in_trade = False
    entry_idx = 0
    curr_trade: Dict[str, Any] = {}

    # Scan session by session
    for i in range(max(25, start_idx), end_idx + 1):
        row = df.iloc[i]
        date_str = row["trade_date"].strftime("%Y-%m-%d")

        # 1. Manage Active Trade
        if in_trade:
            entry_p = curr_trade["entry"]
            sl_p = curr_trade["sl"]
            tp_p = curr_trade["tp"]

            if row["high"] >= tp_p:
                curr_trade["outcome"] = "win"
                curr_trade["exit_date"] = date_str
                curr_trade["exit_price"] = round(tp_p, 2)
                curr_trade["gain_pct"] = round(((tp_p - entry_p) / entry_p) * 100, 1)
                trades.append(curr_trade)
                in_trade = False
            elif row["low"] <= sl_p:
                curr_trade["outcome"] = "loss"
                curr_trade["exit_date"] = date_str
                curr_trade["exit_price"] = round(sl_p, 2)
                curr_trade["gain_pct"] = round(((sl_p - entry_p) / entry_p) * 100, 1)
                trades.append(curr_trade)
                in_trade = False
            elif (i - entry_idx) >= 15 or i == end_idx:
                # 15-day timeout or reached end of data
                gain = ((row["close"] - entry_p) / entry_p) * 100
                curr_trade["outcome"] = "win" if gain > 0 else "loss"
                curr_trade["exit_date"] = date_str
                curr_trade["exit_price"] = round(row["close"], 2)
                curr_trade["gain_pct"] = round(gain, 1)
                trades.append(curr_trade)
                in_trade = False
            continue

        # 2. Check Trap Defense (Where we avoided trading)
        prev_close = df.iloc[i - 1]["close"] if i > 0 else row["close"]
        day_chg_pct = ((row["close"] - prev_close) / prev_close) * 100 if prev_close > 0 else 0

        # Trap 1: Price Spike without Volume (Pump & Dump trap)
        if day_chg_pct >= 2.5 and row["vol_ratio"] < 0.8:
            avoided_traps.append({
                "date": date_str,
                "type": "LOW_VOLUME_TRAP",
                "title": f"{date_str} (লো-ভলিউম ফলস স্পাইক)",
                "reason": f"প্রাইস +{day_chg_pct:.1f}% বাড়লেও ভলিউম মাত্র {row['vol_ratio']:.1f}x ছিল। প্রাতিষ্ঠানিক সাপোর্ট না থাকায় ট্র্যাপ সন্দেহে এন্ট্রি দেওয়া হয়নি।"
            })
            continue

        # Trap 2: Overbought Chasing Risk
        if row["rsi14"] >= 72 and day_chg_pct > 1.0:
            avoided_traps.append({
                "date": date_str,
                "type": "OVERBOUGHT_RISK",
                "title": f"{date_str} (ওভারবট মোমেন্টাম ট্র্যাপ)",
                "reason": f"RSI {row['rsi14']:.1f} অতিরিক্ত ওভারবট জোনে প্রবেশ করায় টপ-বাই এড়িয়ে স্বাস্থ্যকর কারেকশনের অপেক্ষা করা হয়েছে।"
            })
            continue

        # Trap 3: Breakdown beneath EMA20 in downtrend
        if row["close"] < row["ema20"] < row["ema50"] and row["rsi14"] < 40 and day_chg_pct > 1.5:
            avoided_traps.append({
                "date": date_str,
                "type": "DOWNTREND_KNIFE",
                "title": f"{date_str} (ডাউনট্রেন্ড বটম-ফিশিং ফাঁদ)",
                "reason": f"প্রাইস প্রধান মুভিং এভারেজের (EMA 20 ও 50) নিচে অবস্থান করায় কোনো বটম ফিশিং বা ব্লাইন্ড বাই নেওয়া হয়নি।"
            })
            continue

        # 3. Detect Validated Setups
        is_breakout = (row["close"] > row["high20"]) and (row["vol_ratio"] >= 1.35) and (row["rsi14"] <= 70)
        is_ema_bounce = (row["low"] <= row["ema20"]) and (row["close"] > row["ema20"]) and (row["ema20"] > row["ema50"]) and (row["vol_ratio"] >= 1.2)
        is_smart_money = (row["vol_ratio"] >= 2.0) and (abs(row["close"] - row["open"]) / row["close"] < 0.02) and (45 <= row["rsi14"] <= 65)

        matched_strategy = None
        strategy_code = None
        strat_rationale = ""

        if is_breakout and (strategy_filter in ("ALL", "BREAKOUT")):
            matched_strategy = "⚡ 20-Day High Breakout + Volume Surge"
            strategy_code = "BREAKOUT"
            strat_rationale = f"প্রাইস ২০ দিনের সর্বোচ্চ পয়েন্ট ভেঙেছে, ভলিউম সাধারণ দিনের তুলনায় {row['vol_ratio']:.1f}x বেড়েছে এবং RSI ছিল {row['rsi14']:.1f} (সুইট-স্পট)।"
        elif is_ema_bounce and (strategy_filter in ("ALL", "EMA_ALIGN")):
            matched_strategy = "📈 EMA 20/50 Golden Pullback Entry"
            strategy_code = "EMA_ALIGN"
            strat_rationale = f"আপট্রেন্ড চলাকালীন প্রাইস EMA 20 সাপোর্টে টেস্ট করে শক্তিশালী বুলিশ রিভার্সাল কনফার্ম করেছে।"
        elif is_smart_money and (strategy_filter in ("ALL", "VOLUME")):
            matched_strategy = "🐋 Smart Money Accumulation (Vol Surge)"
            strategy_code = "VOLUME"
            strat_rationale = f"কনসলিডেশন রেঞ্জে প্রাতিষ্ঠানিক এক্যুমুলেশন ভলিউম ({row['vol_ratio']:.1f}x) ধরা পড়েছে।"

        if matched_strategy:
            in_trade = True
            entry_idx = i
            entry = float(row["close"])
            sl = round(entry * 0.965, 2)  # 3.5% Stop Loss
            risk = entry - sl
            tp = round(entry + (risk * 2.2), 2)  # 2.2:1 RRR (+7.7%)

            curr_trade = {
                "id": len(trades) + 1,
                "date": date_str,
                "strategy": matched_strategy,
                "strategy_code": strategy_code,
                "entry": round(entry, 2),
                "sl": sl,
                "sl_pct": -3.5,
                "tp": tp,
                "tp_pct": round(((tp - entry) / entry) * 100, 1),
                "rrr": "2.2:1",
                "rsi": round(float(row["rsi14"]), 1),
                "vol_ratio": round(float(row["vol_ratio"]), 1),
                "rationale": strat_rationale,
                "outcome": "active",
                "exit_date": date_str,
                "exit_price": round(entry, 2),
                "gain_pct": 0.0
            }

    # If last trade is still open at the end
    if in_trade:
        last_row = df.iloc[end_idx]
        gain = ((last_row["close"] - curr_trade["entry"]) / curr_trade["entry"]) * 100
        curr_trade["outcome"] = "win" if gain >= 0 else "loss"
        curr_trade["exit_date"] = last_row["trade_date"].strftime("%Y-%m-%d")
        curr_trade["exit_price"] = round(last_row["close"], 2)
        curr_trade["gain_pct"] = round(gain, 1)
        trades.append(curr_trade)

    # 4. Calculate Aggregate Metrics
    total_trades = len(trades)
    win_trades = [t for t in trades if t["outcome"] == "win"]
    loss_trades = [t for t in trades if t["outcome"] == "loss"]

    win_count = len(win_trades)
    loss_count = len(loss_trades)
    win_rate = round((win_count / total_trades * 100), 1) if total_trades > 0 else 0.0

    avg_gain = round(np.mean([t["gain_pct"] for t in win_trades]), 1) if win_trades else 0.0
    avg_loss = round(abs(np.mean([t["gain_pct"] for t in loss_trades])), 1) if loss_trades else 0.0

    gross_profit = sum([t["gain_pct"] for t in win_trades]) if win_trades else 0.0
    gross_loss = abs(sum([t["gain_pct"] for t in loss_trades])) if loss_trades else 1.0
    profit_factor = round(gross_profit / gross_loss, 1) if gross_loss > 0 else 2.5

    # Bot Knowledge Mark (0-100)
    score_mark = 50
    score_mark += int(win_rate * 0.30)  # Max +30 from win rate
    score_mark += min(15, int(profit_factor * 5))  # Max +15 from profit factor
    score_mark += min(10, len(avoided_traps) * 2)  # Max +10 from avoided traps
    score_mark = min(96, max(60, score_mark))

    grade = "A+" if score_mark >= 90 else ("A" if score_mark >= 80 else ("B" if score_mark >= 70 else "C"))

    # Synthesize Teacher Evaluation Commentary
    traps_count = len(avoided_traps)
    period_title = {
        "3M": "বিগত ৩ মাসের টেস্ট হরাইজনে",
        "6M": "বিগত ৬ মাসের ট্রেডিং পিরিয়ডে",
        "1Y": "১ বছরের ট্রেইন্ড বেসলাইনে",
        "ALL": "সম্পূর্ণ ২ বছরের হিস্টোরিক্যাল ডেটায়"
    }.get(period, "নির্দিষ্ট পিরিয়ডে")

    teacher_comments = (
        f"বটটি {period_title} {sym}-এর ক্যান্ডেলস্টিক ও ভলিউম ডেটা নিখুঁতভাবে অডিট করেছে। "
        f"মোট {total_trades}টি হাই-কনফ্লুয়েন্স ট্রেড সেটআপ শনাক্ত হয়েছে যার উইন রেট {win_rate}% "
        f"(গড় লাভ +{avg_gain}% বনাম ক্ষতি -{avg_loss}%)। "
        f"সবচেয়ে প্রশংসনীয় বিষয় হলো—বটটি {traps_count}টি ঝুঁকিপূর্ণ ফলস স্পাইক ও ওভারবট ট্র্যাপ সফলভাবে এড়িয়ে মূলধন সুরক্ষা করেছে।"
    )

    return {
        "status": "success",
        "symbol": sym,
        "period": period,
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_gain": avg_gain,
        "avg_loss": avg_loss,
        "bot_score": score_mark,
        "bot_grade": grade,
        "trades": trades,
        "avoided_traps": avoided_traps[:6],  # Top 6 most relevant traps
        "teacher_comments": teacher_comments
    }
