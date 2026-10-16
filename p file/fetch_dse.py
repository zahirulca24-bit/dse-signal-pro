import urllib.request
import re

urls = [
    'https://www.dse.com.bd/sector_wise_company_list.php',
    'https://www.dse.com.bd/latest_share_price_all.php',
    'https://www.dse.com.bd/latest_share_price.php'
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

for url in urls:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            print(f"SUCCESS: {url} (Length: {len(content)})")
    except Exception as e:
        print(f"FAILED: {url} -> {e}")
