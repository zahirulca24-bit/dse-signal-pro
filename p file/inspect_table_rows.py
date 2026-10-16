with open('latest_sector.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

table = re.search(r'<table[^>]*>(.*?)</table>', text, re.DOTALL | re.IGNORECASE)
if table:
    tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', table.group(1), re.DOTALL | re.IGNORECASE)
    if tbody:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL | re.IGNORECASE)
        print("Total rows in table:", len(rows))
        for r in rows[:10]:
            cells = [re.sub(r'<[^>]+>', '', td).strip() for td in re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL | re.IGNORECASE)]
            print(cells)
    else:
        print("No tbody found in table")
else:
    print("No table found")
