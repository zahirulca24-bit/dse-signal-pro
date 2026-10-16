import re
import json

with open('latest_sector.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's check for Next.js payload or HTML tables
tables = re.findall(r'<table[^>]*>(.*?)</table>', content, re.DOTALL | re.IGNORECASE)
print("Tables found:", len(tables))

# Check for push chunks in Next.js App Router
chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*\"(.*?)\"\]\)', content)
print("Chunks found:", len(chunks))

# Check if there are company names, LTP, sector names
sectors_found = set()
for m in re.finditer(r'Bank|Financial Institutions|Insurance|Textile|Pharmaceuticals|Engineering|Food & Allied', content):
    sectors_found.add(m.group(0))
print("Sectors detected:", sectors_found)

# Let's search for json-like structures
# Look for tradingCode or ltp or lastTradedPrice
symbols = re.findall(r'\"([A-Z0-9_\-]{2,15})\"', content)
print("Some uppercase tokens:", [s for s in symbols if len(s) > 2][:30])

# Let's search for patterns with prices
patterns = re.findall(r'([A-Z0-9]{3,15})[^\d]{1,20}(\d+\.\d+)', content)
print("Sample symbol + price matches:", patterns[:20])
