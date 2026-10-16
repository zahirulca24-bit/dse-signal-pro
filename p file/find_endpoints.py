with open('latest_sector.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import urllib.request

scripts = re.findall(r'<script[^>]*src=[\"\'](/_next/static/chunks/[^\"\']+)[\"\']', text)
print("Found chunks in latest_sector.html:", len(scripts), scripts)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for s in scripts:
    url = 'https://www.dse.com.bd' + s
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            js = r.read().decode('utf-8', errors='ignore')
            # search for api endpoints
            endpoints = re.findall(r'[\"\'](/api/[a-zA-Z0-9_\-\?&=/]+)[\"\']', js)
            if endpoints:
                print(f"File {s} -> Endpoints:", set(endpoints))
            # search for fetch or axios
            fetches = re.findall(r'fetch\([\"\'`]([^\"\'`]+)[\"\'`]', js)
            if fetches:
                print(f"File {s} -> Fetches:", set(fetches))
    except Exception as e:
        print(f"Error reading {s}: {e}")
