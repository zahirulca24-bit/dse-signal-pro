import urllib.request
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}
req = urllib.request.Request('https://www.dse.com.bd/markets/latest-share-price?view=sector', headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print('Status:', r.status, 'Len:', len(html))
        with open('latest_sector.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Saved to latest_sector.html')
except Exception as e:
    print('Err:', e)
