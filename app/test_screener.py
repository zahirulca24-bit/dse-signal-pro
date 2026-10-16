import os, csv
from collections import defaultdict

data_file = r'D:\My DSE signal\dse_all_stocks_2y_ohlcv.csv'
symbols_candles = defaultdict(list)

with open(data_file, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        symbols_candles[row['symbol']].append({
            'date': row['trade_date'],
            'open': float(row['open'] or 0),
            'high': float(row['high'] or 0),
            'low': float(row['low'] or 0),
            'close': float(row['close'] or 0),
            'volume': float(row['volume'] or 0),
            'sector': row.get('sector', ''),
            'name': row.get('name', '')
        })

print(f'Total symbols loaded: {len(symbols_candles)}')

screener_results = []

for sym, candles in symbols_candles.items():
    if len(candles) < 26:
        continue
    candles.sort(key=lambda x: x['date'])
    
    latest = candles[-1]
    prev = candles[-2]
    c = latest['close']
    v = latest['volume']
    if c <= 0: continue
    
    prev_c = prev['close']
    chg = c - prev_c
    chg_pct = (chg / prev_c * 100) if prev_c > 0 else 0.0
    
    # 52w high & low (last 240 candles)
    last_year = candles[-240:] if len(candles) >= 240 else candles
    h52 = max(x['high'] for x in last_year)
    l52 = min(x['low'] for x in last_year if x['low'] > 0)
    
    # MA 14
    ma14 = sum(x['close'] for x in candles[-14:]) / 14
    
    # Vol 20 SMA
    vol20 = sum(x['volume'] for x in candles[-20:]) / 20
    
    # RSI 14
    gains, losses = 0.0, 0.0
    for i in range(len(candles)-14, len(candles)):
        d = candles[i]['close'] - candles[i-1]['close']
        if d >= 0: gains += d
        else: losses -= d
    rs = (gains / 14) / (losses / 14) if losses > 0 else 100
    rsi14 = round(100 - (100 / (1 + rs)), 1)
    
    # MACD
    k12 = 2 / (12 + 1)
    k26 = 2 / (26 + 1)
    ema12 = candles[0]['close']
    ema26 = candles[0]['close']
    for c_item in candles[1:]:
        ema12 = c_item['close'] * k12 + ema12 * (1 - k12)
        ema26 = c_item['close'] * k26 + ema26 * (1 - k26)
    macd_val = ema12 - ema26
    
    # Signals
    signals = []
    if macd_val > 0: signals.append('MACD_BULL')
    if rsi14 < 35: signals.append('RSI_OVERSOLD')
    if rsi14 > 70: signals.append('RSI_OVERBOUGHT')
    if v >= 1.8 * vol20 and v > 50000: signals.append('VOL_SURGE')
    if c > ma14: signals.append('ABOVE_MA14')
    if h52 > 0 and c >= 0.90 * h52: signals.append('NEAR_52W_HIGH')
    
    screener_results.append({
        'symbol': sym,
        'name': latest['name'],
        'sector': latest['sector'] or 'Others',
        'ltp': round(c, 2),
        'change_pct': round(chg_pct, 2),
        'volume': int(v),
        'ma14': round(ma14, 2),
        'vol20': int(vol20),
        'rsi14': rsi14,
        'macd': round(macd_val, 2),
        'high52': round(h52, 2),
        'low52': round(l52, 2),
        'signals': signals
    })

print(f'Screener processed: {len(screener_results)} stocks')
vol_surges = [x for x in screener_results if 'VOL_SURGE' in x['signals']]
oversolds = [x for x in screener_results if 'RSI_OVERSOLD' in x['signals']]
macd_bulls = [x for x in screener_results if 'MACD_BULL' in x['signals']]
print(f'Volume Surges: {len(vol_surges)}, sample: {[x["symbol"] for x in vol_surges[:5]]}')
print(f'RSI Oversolds: {len(oversolds)}, sample: {[x["symbol"] for x in oversolds[:5]]}')
print(f'MACD Bullish: {len(macd_bulls)}, sample: {[x["symbol"] for x in macd_bulls[:5]]}')
