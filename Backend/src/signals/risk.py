"""
Risk Management and Execution Planning Engine for DSE Stocks.
Calculates Entry Price, Dynamic Stop-Loss (Swing Low + ATR Buffer),
Target 1 & 2, and enforces minimum 1:2.0 Risk-Reward Ratio (RRR).
"""

from typing import List, Dict, Any, Optional

def calculate_atr(candles: List[Dict[str, float]], period: int = 14) -> float:
    """Calculate Average True Range (ATR) over candle history."""
    if len(candles) < 2:
        return 0.0
    
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]['high']
        l = candles[i]['low']
        prev_c = candles[i-1]['close']
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
        
    if not trs:
        return 0.0
        
    recent_trs = trs[-period:] if len(trs) >= period else trs
    return sum(recent_trs) / len(recent_trs)

def calculate_trade_plan(candles: List[Dict[str, float]], 
                         current_price: Optional[float] = None,
                         breakout_level: Optional[float] = None) -> Dict[str, Any]:
    """
    Computes an analyst-grade trade plan for a given stock candle series.
    Returns:
        entry_price: Suggested entry
        stop_loss: Calculated invalidation price
        target_1: First take-profit level (min 1:2.0 RRR)
        target_2: Extended profit level (1:3.0 RRR)
        risk_pct: Percentage risk per share
        reward_pct: Percentage gain to Target 1
        rrr: Risk to Reward Ratio (e.g., 2.2)
        is_rrr_valid: True if RRR >= 2.0 and risk_pct <= 7.0
        rationale: Explanation of the risk levels
    """
    if not candles or len(candles) < 5:
        return {
            'entry_price': current_price or 0.0,
            'stop_loss': 0.0,
            'target_1': 0.0,
            'target_2': 0.0,
            'risk_pct': 0.0,
            'reward_pct': 0.0,
            'rrr': 0.0,
            'is_rrr_valid': False,
            'rationale': "Insufficient price history for risk calculation."
        }
        
    last_candle = candles[-1]
    ltp = current_price if (current_price and current_price > 0) else last_candle['close']
    
    if ltp <= 0:
        return {
            'entry_price': 0.0,
            'stop_loss': 0.0,
            'target_1': 0.0,
            'target_2': 0.0,
            'risk_pct': 0.0,
            'reward_pct': 0.0,
            'rrr': 0.0,
            'is_rrr_valid': False,
            'rationale': "Invalid stock price."
        }

    # 1. Look back at recent 15 candles for swing support / resistance
    lookback = min(len(candles), 15)
    recent_candles = candles[-lookback:]
    
    swing_low = min(c['low'] for c in recent_candles if c['low'] > 0)
    swing_high = max(c['high'] for c in recent_candles)
    
    # 2. ATR Calculation
    atr = calculate_atr(candles, period=14)
    if atr <= 0:
        atr = ltp * 0.02  # fallback 2% of price
        
    # 3. Dynamic Entry: if breakout, entry is breakout or close
    entry = round(ltp, 2)
    
    # 4. Stop-loss calculation:
    # Placed below swing low with an ATR buffer (0.5 * ATR), but constrained to sensible bounds (2.5% to 6.5%)
    raw_sl = min(swing_low * 0.995, entry - (1.2 * atr))
    raw_risk = entry - raw_sl
    raw_risk_pct = (raw_risk / entry) * 100
    
    # Enforce professional risk constraints
    if raw_risk_pct > 7.0:
        # Tighter stop-loss to avoid excessive capital damage
        stop_loss = round(entry * 0.945, 2) # 5.5% max risk
    elif raw_risk_pct < 2.0:
        # Give enough breathing room so noise doesn't trigger stop
        stop_loss = round(entry * 0.97, 2)  # 3.0% minimum buffer
    else:
        stop_loss = round(raw_sl, 2)
        
    risk_per_share = max(entry - stop_loss, 0.1)
    risk_pct = round((risk_per_share / entry) * 100, 2)
    
    # 5. Target Calculation (Strict 1:2.0 and 1:3.0 Minimum RRR)
    # Check if swing_high offers immediate resistance
    r1_dist = swing_high - entry
    
    # Target 1 should be at least 2.0x risk
    min_t1 = entry + (2.0 * risk_per_share)
    target_1 = round(max(min_t1, swing_high if (r1_dist >= 2.0 * risk_per_share) else min_t1), 2)
    
    # Target 2 (Runner / 3.0x risk)
    target_2 = round(entry + (3.2 * risk_per_share), 2)
    
    reward_per_share = target_1 - entry
    reward_pct = round((reward_per_share / entry) * 100, 2)
    
    rrr = round(reward_per_share / risk_per_share, 2) if risk_per_share > 0 else 0.0
    
    is_rrr_valid = (rrr >= 2.0) and (risk_pct <= 7.0)
    
    rationale = (
        f"Entry @ Tk {entry:.2f} with Stop-Loss @ Tk {stop_loss:.2f} (-{risk_pct}% risk). "
        f"Target 1 @ Tk {target_1:.2f} (+{reward_pct}%) gives a {rrr}:1 Risk/Reward ratio."
    )
    
    return {
        'entry_price': entry,
        'stop_loss': stop_loss,
        'target_1': target_1,
        'target_2': target_2,
        'risk_amount': round(risk_per_share, 2),
        'risk_pct': risk_pct,
        'reward_pct': reward_pct,
        'rrr': rrr,
        'is_rrr_valid': is_rrr_valid,
        'rationale': rationale
    }
