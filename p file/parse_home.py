import urllib.request
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
req = urllib.request.Request('https://www.dse.com.bd/', headers=headers)
with urllib.request.urlopen(req, timeout=15) as r:
    html = r.read().decode('utf-8', errors='ignore')

# Search for api calls, json endpoints, or js files
scripts = re.findall(r'<script[^>]*src=[\"\']([^\"\']+)[\"\']', html)
print("Scripts:", scripts[:10])

# Search for any endpoint like /api/ or market data
apis = set(re.findall(r'[\"\'](/api/[^\"\']+|https?://[^\"\']+/api/[^\"\']+)[\"\']', html))
print("APIs:", apis)

# Search for word 'sector' or 'stock'
sector_links = set(re.findall(r'href=[\"\'](/[^\"\']*sector[^\"\']*)[\"\']', html, re.I))
print("Sector links:", sector_links)
