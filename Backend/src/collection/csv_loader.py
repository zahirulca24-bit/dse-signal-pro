import os
import sys
import csv
from pathlib import Path
from collections import defaultdict

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from src.signals.engine import analyze_stock
except ModuleNotFoundError:
    from Backend.src.signals.engine import analyze_stock

ROOT = Path(__file__).resolve().parents[3]
DATA_FILE = ROOT / "dse_all_stocks_2y_ohlcv.csv"
SYMBOL_DIR = ROOT / "by_symbol"
SCAN_FILE = ROOT / "Backend" / "data" / "processed" / "stock_scan_latest.csv"

symbols_meta = {}
summary_list = []
market_stats = {}
top_gainers = []
top_losers = []
top_volume = []
sectors_summary = []
screener_data = {'total': 0, 'stats': {}, 'results': []}

FAVORITES_LIST = ['FEKDIL', 'LOVELLO', 'MATINSPINN', 'AZIZPIPES', 'BDFINANCE', 'SQURPHARMA', 'ORIONPHARM', 'BATBC', 'GP']

def calc_ema(prices, period):
    if not prices:
        return []
    k = 2.0 / (period + 1)
    val = prices[0]
    out = [val]
    for p in prices[1:]:
        val = p * k + val * (1.0 - k)
        out.append(val)
    return out

def load_market_data():
    global symbols_meta, summary_list, market_stats, top_gainers, top_losers, top_volume, sectors_summary, screener_data
    if not DATA_FILE.exists():
        print(f"Warning: {DATA_FILE} not found!")
        return

    # Load stock scan quantitative data if available
    quant_scores = {}
    if SCAN_FILE.exists():
        try:
            with open(SCAN_FILE, 'r', encoding='utf-8') as sf:
                sreader = csv.DictReader(sf)
                for srow in sreader:
                    sym = srow.get('symbol', '').upper()
                    if sym:
                        quant_scores[sym] = {
                            'score': float(srow.get('score', 0)) if srow.get('score') else 0,
                            'signal': srow.get('signal', 'NEUTRAL'),
                            'trend': srow.get('trend', 'MIXED'),
                            'breakout20': srow.get('breakout20', 'False') in ('True', 'true', True),
                            'sector_phase': srow.get('sector_phase', ''),
                            'sector_aligned': srow.get('sector_aligned', 'False') in ('True', 'true', True),
                            'momentum5_pct': float(srow.get('momentum5_pct', 0)) if srow.get('momentum5_pct') else 0
                        }
        except Exception as e:
            print("Notice: Error reading stock_scan_latest.csv:", e)

    symbols_meta.clear()
    summary_list.clear()

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = row.get('symbol', '').strip().upper()
            if not sym:
                continue
            dt = row.get('trade_date', '')
            try:
                o = float(row['open']) if row['open'] else 0.0
                h = float(row['high']) if row['high'] else 0.0
                l = float(row['low']) if row['low'] else 0.0
                c = float(row['close']) if row['close'] else 0.0
                v = float(row['volume']) if row['volume'] else 0.0
            except:
                continue

            if sym not in symbols_meta:
                symbols_meta[sym] = {
                    'symbol': sym,
                    'name': row.get('name', sym),
                    'sector': row.get('sector', 'Others'),
                    'history': []
                }
            symbols_meta[sym]['history'].append((dt, o, h, l, c, v))

    tot_vol = 0
    tot_turnover = 0
    adv, dec, unch = 0, 0, 0
    latest_dt = '2026-10-15'
    sector_agg = defaultdict(lambda: {'count': 0, 'turnover': 0.0, 'chg_sum': 0.0})
    screener_results = []

    for sym, meta in symbols_meta.items():
        hist = meta['history']
        if not hist:
            continue
        hist.sort(key=lambda x: x[0])
        latest = hist[-1]
        prev = hist[-2] if len(hist) > 1 else latest
        latest_dt = latest[0]

        ltp = latest[4]
        prev_close = prev[4]
        chg = ltp - prev_close
        chg_pct = (chg / prev_close * 100) if prev_close > 0 else 0.0
        vol = latest[5]
        val = ltp * vol

        tot_vol += vol
        tot_turnover += val

        if chg > 0.001:
            adv += 1
        elif chg < -0.001:
            dec += 1
        else:
            unch += 1

        sec = meta['sector'] or 'Others'
        sector_agg[sec]['count'] += 1
        sector_agg[sec]['turnover'] += val
        sector_agg[sec]['chg_sum'] += chg_pct

        summary_list.append({
            'symbol': sym,
            'name': meta['name'],
            'sector': sec,
            'date': latest[0],
            'ltp': round(ltp, 2),
            'prev_close': round(prev_close, 2),
            'change': round(chg, 2),
            'change_pct': round(chg_pct, 2),
            'volume': int(vol),
            'turnover_cr': round(val / 10000000, 2)
        })

        # --- Algorithmic & Quantitative Strategy Screener Engine ---
        if len(hist) >= 26 and ltp > 0:
            year_candles = hist[-240:] if len(hist) >= 240 else hist
            h52 = max(x[2] for x in year_candles)
            l52 = min(x[3] for x in year_candles if x[3] > 0) or 1.0

            ma14 = sum(x[4] for x in hist[-14:]) / 14.0
            vol20 = sum(x[5] for x in hist[-20:]) / 20.0
            vol_ratio = round(vol / vol20, 2) if vol20 > 0 else 0.0

            # RSI 14
            gains, losses = 0.0, 0.0
            for i in range(len(hist)-14, len(hist)):
                d = hist[i][4] - hist[i-1][4]
                if d >= 0: gains += d
                else: losses -= d
            rs = (gains / 14.0) / (losses / 14.0) if losses > 0 else 100.0
            rsi14 = round(100.0 - (100.0 / (1.0 + rs)), 1)

            # MACD
            closes = [x[4] for x in hist]
            ema12 = calc_ema(closes, 12)
            ema26 = calc_ema(closes, 26)
            macd_series = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
            signal_series = calc_ema(macd_series, 9)
            macd_curr = macd_series[-1]
            sig_curr = signal_series[-1]
            macd_prev = macd_series[-2]
            sig_prev = signal_series[-2]

            signals = []
            if macd_prev <= sig_prev and macd_curr > sig_curr:
                signals.append('MACD_CROSS_BULLISH')
            elif macd_curr > sig_curr:
                signals.append('MACD_BULLISH')

            if rsi14 <= 35:
                signals.append('RSI_OVERSOLD')
            elif rsi14 >= 70:
                signals.append('RSI_OVERBOUGHT')

            if vol_ratio >= 1.8 and vol > 5000:
                signals.append('VOL_SURGE')

            if ltp > ma14:
                signals.append('ABOVE_MA14')

            if h52 > 0 and (ltp / h52) >= 0.95:
                signals.append('NEAR_52W_HIGH')
            elif l52 > 0 and (ltp / l52) <= 1.05:
                signals.append('NEAR_52W_LOW')

            # Quantitative scan metadata integration
            q_info = quant_scores.get(sym, {})
            score = q_info.get('score', 50)
            trade_signal = q_info.get('signal', 'NEUTRAL')
            trend = q_info.get('trend', 'MIXED')
            breakout20 = q_info.get('breakout20', False)
            sector_phase = q_info.get('sector_phase', '')

            if breakout20:
                signals.append('BREAKOUT_20D')
            if trade_signal in ('BULLISH_WATCH', 'ACCUMULATION', 'BUY'):
                signals.append('QUANT_BUY')

            # 6-Pillar Professional Analyst Decision Engine Execution
            candle_dicts = [{'open': x[1], 'high': x[2], 'low': x[3], 'close': x[4], 'volume': x[5]} for x in hist[-30:]]
            analyst_res = analyze_stock({
                'symbol': sym,
                'name': meta['name'],
                'sector': sec,
                'ltp': ltp,
                'rsi14': rsi14,
                'vol_ratio': vol_ratio,
                'breakout20': breakout20,
                'ema20': ema12[-1] if len(ema12) > 0 else ltp,
                'ema50': ema26[-1] if len(ema26) > 0 else ltp,
                'macd': macd_curr,
                'signal': sig_curr
            }, candles=candle_dicts, market_stats={'advances': adv, 'declines': dec, 'estimated_turnover_cr': tot_turnover / 10000000})

            # Add analyst verdict signals for filtering
            v = analyst_res['verdict']
            if v == 'BUY SETUP':
                signals.append('BUY_SETUP')
            elif v == 'WAIT':
                signals.append('WAIT')
            elif v == 'AVOID':
                signals.append('AVOID')
            elif v == 'EXIT / SELL':
                signals.append('EXIT_SELL')

            if analyst_res['category'] == 'A':
                signals.append('CAT_A')
            elif analyst_res['category'] == 'Z':
                signals.append('CAT_Z')

            if analyst_res['trade_plan']['is_rrr_valid']:
                signals.append('RRR_VALID')

            screener_results.append({
                'symbol': sym,
                'name': meta['name'],
                'sector': sec,
                'ltp': round(ltp, 2),
                'change_pct': round(chg_pct, 2),
                'volume': int(vol),
                'vol_ratio': vol_ratio,
                'turnover_cr': round(val / 10000000, 2),
                'rsi14': rsi14,
                'ma14': round(ma14, 2),
                'macd': round(macd_curr, 2),
                'signal': round(sig_curr, 2),
                'signals': signals,
                'score': score,
                'quant_signal': trade_signal,
                'trend': trend,
                'sector_phase': sector_phase,
                'breakout20': breakout20,
                'category': analyst_res['category'],
                'verdict': analyst_res['verdict'],
                'sub_type': analyst_res['sub_type'],
                'rationale_bn': analyst_res['rationale_bn'],
                'rationale_en': analyst_res['rationale_en'],
                'trade_plan': analyst_res['trade_plan'],
                'pillars': analyst_res['pillars']
            })

    summary_list.sort(key=lambda x: x['symbol'])
    top_gainers = sorted(summary_list, key=lambda x: x['change_pct'], reverse=True)[:10]
    top_losers = sorted(summary_list, key=lambda x: x['change_pct'])[:10]
    top_volume = sorted(summary_list, key=lambda x: x['turnover_cr'], reverse=True)[:10]

    sectors_summary.clear()
    for s_name, agg in sector_agg.items():
        cnt = agg['count']
        avg_chg = (agg['chg_sum'] / cnt) if cnt > 0 else 0.0
        sectors_summary.append({
            'sector': s_name,
            'count': cnt,
            'avg_change_pct': round(avg_chg, 2),
            'turnover_cr': round(agg['turnover'] / 10000000, 2)
        })
    sectors_summary.sort(key=lambda x: x['avg_change_pct'], reverse=True)

    counts = defaultdict(int)
    for r in screener_results:
        for s in r['signals']:
            counts[s] += 1

    screener_data = {
        'total': len(screener_results),
        'stats': dict(counts),
        'results': screener_results
    }

    market_stats = {
        'total_symbols': len(symbols_meta),
        'advances': adv,
        'declines': dec,
        'unchanged': unch,
        'latest_date': latest_dt,
        'total_volume': int(tot_vol),
        'estimated_turnover_cr': round(tot_turnover / 10000000, 2)
    }
    print(f"[*] DSE Data Engine Loaded: {len(symbols_meta)} symbols, {len(screener_results)} screened.")

def get_history(symbol: str):
    sym = symbol.strip().upper()
    csv_path = SYMBOL_DIR / f"{sym}.csv"
    if not csv_path.exists():
        return None
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                records.append({
                    'time': row['trade_date'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
            except:
                pass
    records.sort(key=lambda x: x['time'])
    return {'symbol': sym, 'count': len(records), 'candles': records}

# Auto-initialize on import
load_market_data()
