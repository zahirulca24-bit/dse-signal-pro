with open('sectors_page.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import json

chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*\"(.*?)\"\]\)', text)
c10 = chunks[10]
unesc = c10.encode('utf-8').decode('unicode_escape')

# extract json from unesc
# It starts with 5:
data_str = unesc[unesc.find('{'):]
print("data_str length:", len(data_str))

# let's find the rows array
rows_match = re.search(r'\"rows\":\s*(\[.*?\])\s*\}', data_str)
if rows_match:
    rows = json.loads(rows_match.group(1))
    print(f"Total sectors in list: {len(rows)}")
    for r in rows:
        print(r)
else:
    print(data_str[:1000])
