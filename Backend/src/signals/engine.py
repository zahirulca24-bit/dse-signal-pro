"""
6-Pillar Professional Analyst Decision Engine for Dhaka Stock Exchange (DSE).
Combines:
  1. Broad Market Regime (DSEX Advance/Decline & Liquidity)
  2. Sector Rotation (Leading, Recovering, Cooling, Lagging)
  3. Fundamental Health & DSE Category (A/B vs Z-disqualification)
  4. Technical Confluence (EMA20/50, RSI Momentum, Volume Expansion, Breakout)
  5. Strict Risk/Reward Calculus (Entry, SL, Targets, RRR >= 1:2.0)
  6. Edge-verified Verdict Generation: BUY SETUP | WAIT | AVOID | EXIT/SELL
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from src.signals.risk import calculate_trade_plan
except ModuleNotFoundError:
    from Backend.src.signals.risk import calculate_trade_plan

ROOT = Path(__file__).resolve().parents[3]
SECTOR_JSON = ROOT / "p file" / "dse_sector_stocks.json"
SECTOR_ROTATION_CSV = ROOT / "Backend" / "data" / "processed" / "sector_rotation_latest.csv"

# Global cache for categories and sector rotation
_category_cache: Dict[str, str] = {}
_sector_rotation_cache: Dict[str, Dict[str, Any]] = {}

def load_category_map() -> Dict[str, str]:
    """Loads official DSE stock categories (A, B, N, Z) from dse_sector_stocks.json."""
    global _category_cache
    if _category_cache:
        return _category_cache
        
    if not SECTOR_JSON.exists():
        return {}
        
    try:
        with open(SECTOR_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for sec_name, sec_data in data.items():
                if isinstance(sec_data, dict):
                    for stock in sec_data.get('stocks', []):
                        code = str(stock.get('code', '')).strip().upper()
                        cat = str(stock.get('category', 'A')).strip().upper()
                        if code:
                            _category_cache[code] = cat
    except Exception as e:
        print("Warning: Failed to load category mapping:", e)
        
    return _category_cache

def load_sector_rotation() -> Dict[str, Dict[str, Any]]:
    """Loads sector rotation phases and scores."""
    global _sector_rotation_cache
    if _sector_rotation_cache:
        return _sector_rotation_cache
        
    if not SECTOR_ROTATION_CSV.exists():
        return {}
        
    try:
        import csv
        with open(SECTOR_ROTATION_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sec = row.get('sector', '').strip()
                if sec:
                    _sector_rotation_cache[sec] = {
                        'phase': row.get('phase', 'UNKNOWN'),
                        'rotation_score': float(row.get('rotation_score', 0) or 0),
                        'return_5d_pct': float(row.get('return_5d_pct', 0) or 0),
                        'relative_strength_5d': float(row.get('relative_strength_5d', 0) or 0),
                        'volume_ratio': float(row.get('volume_ratio', 1.0) or 1.0)
                    }
    except Exception as e:
        print("Warning: Failed to load sector rotation:", e)
        
    return _sector_rotation_cache

def evaluate_market_regime(market_stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Pillar 1: Evaluates overall DSEX Market Regime."""
    if not market_stats:
        return {'regime': 'NEUTRAL', 'health': 'FAIR', 'score': 50, 'summary': 'Market data balanced'}
        
    adv = market_stats.get('advances', 0)
    dec = market_stats.get('declines', 0)
    turnover = market_stats.get('estimated_turnover_cr', 0)
    
    total = adv + dec
    if total == 0:
        return {'regime': 'NEUTRAL', 'health': 'FAIR', 'score': 50, 'summary': 'Market in balance'}
        
    adv_ratio = adv / total
    
    if adv_ratio >= 0.60 and turnover >= 450:
        return {
            'regime': 'BULLISH',
            'health': 'STRONG',
            'score': 85,
            'summary': f'মার্কেট পজিটিভ: ক্রেতাদের আধিক্য ({adv} Adv vs {dec} Dec), টার্নওভার Tk {turnover:.0f} কোটি।'
        }
    elif adv_ratio <= 0.35 or turnover < 250:
        return {
            'regime': 'RISK_OFF',
            'health': 'WEAK',
            'score': 30,
            'summary': f'মার্কেট সতর্কতামূলক: বিক্রির চাপ বেশি ({dec} Dec vs {adv} Adv), সতর্ক ট্রেডিং কাম্য।'
        }
    else:
        return {
            'regime': 'RANGE_BOUND',
            'health': 'MODERATE',
            'score': 55,
            'summary': f'মার্কেট সাইডওয়েজ: সীমিত ওঠানামা ({adv} Adv vs {dec} Dec), সিলেক্টিভ স্টক বাছাই প্রয়োজন।'
        }

def analyze_stock(
    stock_data: Dict[str, Any],
    candles: Optional[List[Dict[str, float]]] = None,
    market_stats: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes the 6-Pillar Decision Engine for a single stock.
    Returns:
        verdict: 'BUY SETUP' | 'WAIT' | 'AVOID' | 'EXIT / SELL'
        verdict_badge: Color and UI styling
        pillars: Detailed scores and findings across all 6 pillars
        trade_plan: Entry, Stop-Loss, Target 1, Target 2, RRR
        rationale_bn: Professional Bengali institutional rationale
        rationale_en: English institutional rationale
    """
    cat_map = load_category_map()
    sec_map = load_sector_rotation()
    market_eval = evaluate_market_regime(market_stats)
    
    symbol = stock_data.get('symbol', '').upper()
    sector = stock_data.get('sector', 'Others')
    ltp = float(stock_data.get('ltp', stock_data.get('close', 0.0)))
    rsi = float(stock_data.get('rsi14', 50.0))
    vol_ratio = float(stock_data.get('vol_ratio', stock_data.get('volume_ratio', 1.0)))
    breakout20 = bool(stock_data.get('breakout20', False))
    ma14 = float(stock_data.get('ma14', 0.0))
    ema20 = float(stock_data.get('ema20', ma14 or ltp))
    ema50 = float(stock_data.get('ema50', ma14 or ltp))
    macd_bullish = bool(
        stock_data.get('macd', 0) > stock_data.get('signal', 0) 
        if 'macd' in stock_data else stock_data.get('macd_bullish', False)
    )

    # 1. PILLAR 3: FUNDAMENTAL CATEGORY CHECK (Immediate Z-Category disqualification)
    category = cat_map.get(symbol, 'A')
    
    # 2. PILLAR 2: SECTOR ROTATION CHECK
    sec_info = sec_map.get(sector, {})
    sec_phase = sec_info.get('phase', 'UNKNOWN')
    sec_rot_score = sec_info.get('rotation_score', 50.0)
    
    # 3. PILLAR 5: RISK & EXECUTION CALCULUS
    if not candles and 'history' in stock_data:
        candles = stock_data['history']
        
    trade_plan = calculate_trade_plan(candles or [], current_price=ltp, breakout_level=ltp if breakout20 else None)
    
    # 4. PILLAR 4: TECHNICAL CONFLUENCE SCORING
    tech_score = 0
    if ltp > ema20: tech_score += 20
    if ema20 > ema50: tech_score += 15
    if 45 <= rsi <= 68: tech_score += 20
    elif rsi > 70: tech_score -= 10 # Overbought penalty
    elif rsi < 35: tech_score -= 10 # Oversold knife penalty
    
    if vol_ratio >= 1.5: tech_score += 20
    elif vol_ratio >= 1.1: tech_score += 10
    
    if breakout20: tech_score += 15
    if macd_bullish: tech_score += 10

    # 5. SYNTHESIZE ALL 6 PILLARS INTO 4 ANALYST VERDICTS
    
    # CASE 1: HARD DISQUALIFICATION -> AVOID (Z-Category or severe breakdown)
    if category == 'Z':
        verdict = 'AVOID'
        rationale_bn = (
            f"⛔ এড়িয়ে চলুন: {symbol} হলো DSE 'Z' ক্যাটাগরি (ডিফল্ট/লোকসানি) শেয়ার। "
            "প্রাতিষ্ঠানিক নীতিমালায় ঝুঁকিপূর্ণ পেনি ও জেড-ক্যাটাগরির শেয়ারে মূলধন আটকানো নিষেধ।"
        )
        rationale_en = (
            f"AVOID: {symbol} is classified as DSE 'Z' Category. High fundamental risk, "
            "poor governance, and potential trading suspension trap."
        )
        sub_type = 'Z_CATEGORY_RISK'

    elif ltp < ema20 < ema50 and rsi < 40 and not breakout20:
        verdict = 'AVOID'
        rationale_bn = (
            f"⛔ এড়িয়ে চলুন: শেয়ারটি শক্ত ডাউনট্রেন্ডে (EMA20 ও EMA50 এর নিচে) আছে। "
            "কোনো রিভার্সাল ও ভলিউম সাপোর্ট ছাড়া বটম ফিশিং মারাত্মক লোকসানের কারণ হতে পারে।"
        )
        rationale_en = (
            f"AVOID: Persistent downtrend below key moving averages. No accumulation confirmation."
        )
        sub_type = 'BEARISH_DOWNTREND'

    # CASE 2: STOP-LOSS / EXIT CONDITION
    elif trade_plan['stop_loss'] > 0 and ltp < (trade_plan['stop_loss'] * 0.99):
        verdict = 'EXIT / SELL'
        rationale_bn = (
            f"⚠️ প্রস্থান / সেল: প্রাইস মূল সাপোর্ট ও স্টপ-লস জোন (Tk {trade_plan['stop_loss']:.2f}) ভেঙে নিচে নেমেছে। "
            "মূলধন সুরক্ষার স্বার্থে কোনো ইমোশন ছাড়া পজিশন খালি করা উচিত।"
        )
        rationale_en = (
            f"EXIT / SELL: Price breached stop-loss level (Tk {trade_plan['stop_loss']:.2f}). Capital defense triggered."
        )
        sub_type = 'STOP_LOSS_BREACHED'

    # CASE 3: BUY SETUP CONDITIONS (High Confluence + Valid RRR >= 1:2.0 + Non-Z)
    elif (
        category in ('A', 'B') 
        and tech_score >= 60 
        and ltp >= ema20 
        and rsi < 70 
        and trade_plan['is_rrr_valid']
        and (breakout20 or vol_ratio >= 1.3 or sec_phase in ('OUTPERFORMING', 'RECOVERING'))
    ):
        verdict = 'BUY SETUP'
        rationale_bn = (
            f"🟢 বায় সেটআপ: ক্যাটাগরি '{category}' শেয়ার। প্রাইস EMA20 এর উপরে শক্তিশালী কনসলিডেশন এবং "
            f"ভলিউম সমর্থন ({vol_ratio:.1f}x) সহ অবস্থান করছে। "
            f"স্টপ-লস Tk {trade_plan['stop_loss']:.2f} এবং ১ম টার্গেট Tk {trade_plan['target_1']:.2f} (RRR {trade_plan['rrr']}:1) চমৎকার।"
        )
        rationale_en = (
            f"BUY SETUP: High-confluence setup with {trade_plan['rrr']}:1 RRR. "
            f"Category {category}, robust moving average alignment, and healthy volume participation."
        )
        sub_type = 'HIGH_CONFLUENCE_BUY'

    # CASE 4: WAIT / MONITOR CONDITIONS
    elif rsi >= 70:
        verdict = 'WAIT'
        rationale_bn = (
            f"⏳ অপেক্ষা করুন (ওভারবট): RSI ({rsi:.1f}) অতি-ক্রয় জোনে চলে গেছে। "
            "এখন প্রবেশ করলে প্রফিট টেকিং ও সংশোধনে পড়ার ঝুঁকি থাকে। EMA20 সাপোর্টে পুলব্যাকের অপেক্ষা করুন।"
        )
        rationale_en = (
            f"WAIT: Overbought momentum (RSI {rsi:.1f}). Chasing prices here exposes to pullback risk. Await dip."
        )
        sub_type = 'OVERBOUGHT_WAIT'

    elif not trade_plan['is_rrr_valid']:
        verdict = 'WAIT'
        rationale_bn = (
            f"⏳ অপেক্ষা করুন (ঝুঁকি/লাভ অনুপাত কম): বর্তমান প্রাইসে সম্ভাব্য লাভের চেয়ে পতনের ঝুঁকি বেশি (RRR {trade_plan['rrr']}:1 < 1:2.0)। "
            "উপযুক্ত মূল্যে বা সাপোর্টের কাছাকাছি না পাওয়া পর্যন্ত নতুন বাই থেকে বিরত থাকুন।"
        )
        rationale_en = (
            f"WAIT: Inadequate Risk/Reward Ratio ({trade_plan['rrr']}:1). Minimum institutional requirement is 2:1."
        )
        sub_type = 'POOR_RRR_WAIT'

    else:
        # Quality stock or neutral setup awaiting catalyst
        verdict = 'WAIT'
        rationale_bn = (
            f"⏳ পর্যবেক্ষণ করুন: শেয়ারটি সাইডওয়েজ বা প্রাথমিক রেঞ্জে আছে। "
            "নিশ্চিত ব্রেকআউট বা প্রাতিষ্ঠানিক ভলিউম বৃদ্ধির পরেই কেবল এন্ট্রি নেওয়া শ্রেয়।"
        )
        rationale_en = (
            f"WAIT: Consolidating. Awaiting clear breakout volume or catalyst before initiating entry."
        )
        sub_type = 'CONSOLIDATION_WAIT'

    # Package pillar details
    pillars = {
        'market': {
            'regime': market_eval['regime'],
            'score': market_eval['score'],
            'summary': market_eval['summary']
        },
        'sector': {
            'sector': sector,
            'phase': sec_phase,
            'rotation_score': sec_rot_score
        },
        'fundamental': {
            'category': category,
            'status': 'QUALIFIED' if category in ('A', 'B') else 'DISQUALIFIED'
        },
        'technical': {
            'tech_score': tech_score,
            'rsi14': rsi,
            'vol_ratio': vol_ratio,
            'breakout20': breakout20,
            'trend': 'UPTREND' if ltp > ema20 > ema50 else ('DOWNTREND' if ltp < ema20 < ema50 else 'SIDEWAYS')
        },
        'risk': {
            'entry_price': trade_plan['entry_price'],
            'stop_loss': trade_plan['stop_loss'],
            'target_1': trade_plan['target_1'],
            'target_2': trade_plan['target_2'],
            'risk_pct': trade_plan['risk_pct'],
            'reward_pct': trade_plan['reward_pct'],
            'rrr': trade_plan['rrr'],
            'is_rrr_valid': trade_plan['is_rrr_valid']
        }
    }

    return {
        'symbol': symbol,
        'category': category,
        'sector': sector,
        'ltp': ltp,
        'verdict': verdict,
        'sub_type': sub_type,
        'rationale_bn': rationale_bn,
        'rationale_en': rationale_en,
        'trade_plan': trade_plan,
        'pillars': pillars
    }
