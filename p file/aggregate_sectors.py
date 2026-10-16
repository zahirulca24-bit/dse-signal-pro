import urllib.request
import json
from collections import defaultdict

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
req = urllib.request.Request('https://www.dse.com.bd/api/live/snapshot', headers=headers)

with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read().decode('utf-8'))

prices = data.get('prices', {})
cols = prices.get('cols', [])
rows = prices.get('rows', [])

col_idx = {c: i for i, c in enumerate(cols)}

sector_groups = defaultdict(list)
for r in rows:
    code = r[col_idx['code']]
    ltp = r[col_idx['ltp']]
    sector = r[col_idx['sector']]
    category = r[col_idx['category']]
    sector_groups[sector].append({'code': code, 'ltp': ltp, 'category': category})

# Let's save a summary and full json
summary = {}
for s, items in sorted(sector_groups.items()):
    items_sorted = sorted(items, key=lambda x: x['code'])
    summary[s] = {
        'count': len(items_sorted),
        'stocks': items_sorted
    }

print(f"Total Sectors: {len(summary)}")
for s, d in summary.items():
    print(f"Sector: {s} | Count: {d['count']}")

with open('dse_sector_stocks.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)

print("Saved dse_sector_stocks.json successfully")
