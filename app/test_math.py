# Test math for MA 14, RSI 14, MACD in Python to ensure correctness
import csv

candles = []
with open(r'D:\My DSE signal\by_symbol\SQURPHARMA.csv') as f:
    for r in csv.DictReader(f):
        candles.append({
            'time': r['trade_date'],
            'open': float(r['open']),
            'high': float(r['high']),
            'low': float(r['low']),
            'close': float(r['close']),
            'volume': float(r['volume'])
        })

candles.sort(key=lambda x: x['time'])

# 1. MA 14
ma14 = []
for i in range(13, len(candles)):
    avg = sum(c['close'] for c in candles[i-13:i+1]) / 14
    ma14.append((candles[i]['time'], round(avg, 2)))

# 2. RSI 14
gains, losses = 0.0, 0.0
for i in range(1, 14):
    d = candles[i]['close'] - candles[i-1]['close']
    if d >= 0: gains += d
    else: losses -= d
avg_g = gains / 14
avg_l = losses / 14
rs = avg_g / avg_l if avg_l > 0 else 100
rsi = [ (candles[13]['time'], round(100 - (100/(1+rs)), 2)) ]
for i in range(14, len(candles)):
    d = candles[i]['close'] - candles[i-1]['close']
    g = d if d >= 0 else 0.0
    l = -d if d < 0 else 0.0
    avg_g = (avg_g * 13 + g) / 14
    avg_l = (avg_l * 13 + l) / 14
    rs = avg_g / avg_l if avg_l > 0 else 100
    rsi.append((candles[i]['time'], round(100 - (100/(1+rs)), 2)))

print(f"Candles: {len(candles)}")
print(f"Latest Close: {candles[-1]['close']}, MA14: {ma14[-1][1]}, RSI14: {rsi[-1][1]}")
