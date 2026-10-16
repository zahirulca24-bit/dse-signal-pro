import os
import csv
import json
from collections import defaultdict

data_file = r"D:\My DSE signal\dse_all_stocks_2y_ohlcv.csv"
symbol_dir = r"D:\My DSE signal\by_symbol"

print("Indexing DSE master dataset...")
symbols_meta = {}
latest_market_data = {}

# Read master CSV to get latest date and records
# Columns: ['symbol', 'name', 'sector', 'trade_date', 'open', 'high', 'low', 'close', 'volume']
with open(data_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sym = row['symbol']
        dt = row['trade_date']
        c = float(row['close']) if row['close'] else 0.0
        v = float(row['volume']) if row['volume'] else 0.0
        
        if sym not in symbols_meta:
            symbols_meta[sym] = {
                'symbol': sym,
                'name': row.get('name', ''),
                'sector': row.get('sector', ''),
                'history_dates': []
            }
        
        # Track latest 2 dates for price change calculation
        meta = symbols_meta[sym]
        meta['history_dates'].append((dt, c, v))

print(f"Total Unique Symbols indexed: {len(symbols_meta)}")

# Calculate current price, previous price, change, and change% for each symbol
summary_list = []
advances, declines, unchanged = 0, 0, 0
total_turnover_est = 0.0

for sym, meta in symbols_meta.items():
    dates = meta['history_dates']
    dates.sort(key=lambda x: x[0])
    
    latest = dates[-1] if dates else ('', 0, 0)
    prev = dates[-2] if len(dates) >= 2 else latest
    
    ltp = latest[1]
    prev_close = prev[1]
    chg = ltp - prev_close
    chg_pct = (chg / prev_close * 100) if prev_close > 0 else 0.0
    vol = latest[2]
    val_est = ltp * vol
    total_turnover_est += val_est
    
    if chg > 0.001:
        advances += 1
    elif chg < -0.001:
        declines += 1
    else:
        unchanged += 1
        
    summary_list.append({
        'symbol': sym,
        'name': meta['name'],
        'sector': meta['sector'],
        'date': latest[0],
        'ltp': ltp,
        'prev_close': prev_close,
        'change': round(chg, 2),
        'change_pct': round(chg_pct, 2),
        'volume': int(vol)
    })

print(f"Summary computed: Advances={advances}, Declines={declines}, Unchanged={unchanged}")
print(f"Sample symbol: {summary_list[0]}")
