import http.server
import socketserver
import urllib.parse
import os
import sys
import csv
import json
from collections import defaultdict

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "Backend"))
try:
    from src.signals.engine import analyze_stock
except Exception as e:
    analyze_stock = None
    print("Notice: engine import:", e)

DATA_FILE = os.path.join(BASE_DIR, "dse_all_stocks_2y_ohlcv.csv")
SYMBOL_DIR = os.path.join(BASE_DIR, "by_symbol")
STATIC_DIR = os.path.join(BASE_DIR, "app")
SCAN_FILE = os.path.join(BASE_DIR, "Backend", "data", "processed", "stock_scan_latest.csv")
ROTATION_FILE = os.path.join(BASE_DIR, "Backend", "data", "processed", "sector_rotation_latest.csv")

print("Initializing DSE Data Engine...")
symbols_meta = {}
summary_list = []
market_stats = {}
top_gainers = []
top_losers = []
top_volume = []
sectors_summary = []
screener_data = {'total': 0, 'stats': {}, 'results': []}
quant_stocks = []
quant_rotation = []

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

def load_data():
    global symbols_meta, summary_list, market_stats, top_gainers, top_losers, top_volume, sectors_summary, screener_data, quant_stocks, quant_rotation
    if not os.path.exists(DATA_FILE):
        print(f"Warning: {DATA_FILE} not found!")
        return

    # Load Backend quantitative scanner data if present
    quant_dict = {}
    quant_stocks = []
    if os.path.exists(SCAN_FILE):
        try:
            with open(SCAN_FILE, 'r', encoding='utf-8') as sf:
                sr = csv.DictReader(sf)
                for r in sr:
                    quant_stocks.append(r)
                    sym = r.get('symbol', '').upper()
                    if sym:
                        quant_dict[sym] = r
        except Exception as e:
            print("Note: Could not read SCAN_FILE:", e)

    quant_rotation = []
    if os.path.exists(ROTATION_FILE):
        try:
            with open(ROTATION_FILE, 'r', encoding='utf-8') as rf:
                rr = csv.DictReader(rf)
                for r in rr:
                    quant_rotation.append(r)
        except Exception as e:
            print("Note: Could not read ROTATION_FILE:", e)

    symbols_meta.clear()
    summary_list.clear()
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = row['symbol']
            dt = row['trade_date']
            o = float(row['open']) if row['open'] else 0.0
            h = float(row['high']) if row['high'] else 0.0
            l = float(row['low']) if row['low'] else 0.0
            c = float(row['close']) if row['close'] else 0.0
            v = float(row['volume']) if row['volume'] else 0.0
            
            if sym not in symbols_meta:
                symbols_meta[sym] = {
                    'symbol': sym,
                    'name': row.get('name', ''),
                    'sector': row.get('sector', ''),
                    'history': []
                }
            symbols_meta[sym]['history'].append((dt, o, h, l, c, v))
            
    adv, dec, unch = 0, 0, 0
    tot_vol = 0
    tot_turnover = 0.0
    latest_dt = ""
    sector_agg = defaultdict(lambda: {'count': 0, 'turnover': 0.0, 'chg_sum': 0.0})
    screener_results = []
    
    for sym, meta in symbols_meta.items():
        hist = meta['history']
        hist.sort(key=lambda x: x[0])
        latest = hist[-1] if hist else ('', 0, 0, 0, 0, 0)
        prev = hist[-2] if len(hist) >= 2 else latest
        
        ltp = latest[4]
        prev_close = prev[4]
        chg = ltp - prev_close
        chg_pct = (chg / prev_close * 100) if prev_close > 0 else 0.0
        vol = latest[5]
        latest_dt = max(latest_dt, latest[0])
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

        # --- Algorithmic Strategy Screener Engine ---
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

            q_info = quant_dict.get(sym, {})
            score = float(q_info.get('score', 50)) if q_info.get('score') else 50
            quant_signal = q_info.get('signal', 'NEUTRAL')
            trend = q_info.get('trend', 'MIXED')
            breakout20 = q_info.get('breakout20') in ('True', 'true', True)
            sector_phase = q_info.get('sector_phase', '')

            if breakout20:
                signals.append('BREAKOUT_20D')
            if quant_signal in ('BULLISH_WATCH', 'ACCUMULATION', 'BUY'):
                signals.append('QUANT_BUY')

            # 6-Pillar Professional Analyst Decision Engine Execution
            category = 'A'
            verdict = 'WAIT'
            sub_type = 'CONSOLIDATION_WAIT'
            rationale_bn = 'পর্যবেক্ষণ করুন'
            rationale_en = 'WAIT: Monitor'
            trade_plan = {}
            pillars = {}

            if analyze_stock:
                try:
                    candle_dicts = [{'open': x[1], 'high': x[2], 'low': x[3], 'close': x[4], 'volume': x[5]} for x in hist[-30:]]
                    ares = analyze_stock({
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

                    category = ares['category']
                    verdict = ares['verdict']
                    sub_type = ares['sub_type']
                    rationale_bn = ares['rationale_bn']
                    rationale_en = ares['rationale_en']
                    trade_plan = ares['trade_plan']
                    pillars = ares['pillars']

                    if verdict == 'BUY SETUP':
                        signals.append('BUY_SETUP')
                    elif verdict == 'WAIT':
                        signals.append('WAIT')
                    elif verdict == 'AVOID':
                        signals.append('AVOID')
                    elif verdict == 'EXIT / SELL':
                        signals.append('EXIT_SELL')

                    if category == 'A':
                        signals.append('CAT_A')
                    elif category == 'Z':
                        signals.append('CAT_Z')

                    if trade_plan.get('is_rrr_valid'):
                        signals.append('RRR_VALID')
                except Exception as ex:
                    pass

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
                'h52': round(h52, 2),
                'l52': round(l52, 2),
                'signals': signals,
                'score': score,
                'quant_signal': quant_signal,
                'trend': trend,
                'breakout20': breakout20,
                'sector_phase': sector_phase,
                'category': category,
                'verdict': verdict,
                'sub_type': sub_type,
                'rationale_bn': rationale_bn,
                'rationale_en': rationale_en,
                'trade_plan': trade_plan,
                'pillars': pillars
            })
        
    top_gainers = sorted([s for s in summary_list if s['change_pct'] > 0], key=lambda x: x['change_pct'], reverse=True)[:10]
    top_losers = sorted([s for s in summary_list if s['change_pct'] < 0], key=lambda x: x['change_pct'])[:10]
    top_volume = sorted(summary_list, key=lambda x: x['turnover_cr'], reverse=True)[:10]

    sectors_summary = []
    for s_name, agg in sector_agg.items():
        cnt = agg['count']
        avg_chg = agg['chg_sum'] / cnt if cnt > 0 else 0.0
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
    print(f"Data Engine Ready! Indexed {len(symbols_meta)} symbols. Screener results={len(screener_results)}. Signals={dict(counts)}")

load_data()

class DSEHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/api/market-summary':
            self.send_json(market_stats)
            return

        elif path == '/api/top-movers':
            self.send_json({
                'gainers': top_gainers,
                'losers': top_losers,
                'most_active': top_volume
            })
            return

        elif path == '/api/sectors-summary':
            self.send_json(sectors_summary)
            return

        elif path == '/api/screener':
            self.send_json(screener_data)
            return

        elif path in ('/api/stocks/scan', '/api/v1/stocks/scan'):
            self.send_json({'status': 'success', 'total_stocks': len(quant_stocks), 'stocks': quant_stocks})
            return

        elif path in ('/api/sectors/rotation', '/api/v1/sectors/rotation'):
            self.send_json({'status': 'success', 'total_sectors': len(quant_rotation), 'sectors': quant_rotation})
            return

        elif path == '/api/favorites':
            fav_data = [s for s in summary_list if s['symbol'] in FAVORITES_LIST]
            fav_data.sort(key=lambda x: FAVORITES_LIST.index(x['symbol']) if x['symbol'] in FAVORITES_LIST else 99)
            self.send_json(fav_data)
            return

        elif path == '/api/symbols':
            self.send_json(summary_list)
            return

        elif path == '/api/history':
            sym = query.get('symbol', ['SQURPHARMA'])[0].upper()
            csv_path = os.path.join(SYMBOL_DIR, f"{sym}.csv")
            if os.path.exists(csv_path):
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
                self.send_json({'symbol': sym, 'count': len(records), 'candles': records})
                return
            else:
                self.send_json({'error': 'Symbol not found'}, status=404)
                return

        elif path.startswith('/api/analyst/') or path.startswith('/api/v1/analyst/'):
            parts = path.rstrip('/').split('/')
            target = parts[-1].upper()
            if target == 'VERDICTS':
                results = screener_data.get('results', [])
                grouped = {
                    "BUY_SETUP": [r for r in results if r.get('verdict') == 'BUY SETUP'],
                    "WAIT": [r for r in results if r.get('verdict') == 'WAIT'],
                    "AVOID": [r for r in results if r.get('verdict') == 'AVOID'],
                    "EXIT_SELL": [r for r in results if r.get('verdict') == 'EXIT / SELL']
                }
                self.send_json({
                    "status": "success",
                    "counts": {k: len(v) for k, v in grouped.items()},
                    "verdicts": grouped
                })
                return
            else:
                for item in screener_data.get('results', []):
                    if item.get('symbol') == target:
                        self.send_json({
                            "status": "success",
                            "symbol": target,
                            "category": item.get('category'),
                            "verdict": item.get('verdict'),
                            "sub_type": item.get('sub_type'),
                            "rationale_bn": item.get('rationale_bn'),
                            "rationale_en": item.get('rationale_en'),
                            "trade_plan": item.get('trade_plan'),
                            "pillars": item.get('pillars')
                        })
                        return
                self.send_json({'error': f"Symbol '{target}' not found"}, status=404)
                return

        return super().do_GET()

    def send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DSEHandler) as httpd:
        print(f"[*] DSE Web Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
