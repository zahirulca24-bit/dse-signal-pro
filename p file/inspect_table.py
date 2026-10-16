with open('latest_sector.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Let's inspect the table found
tables = re.findall(r'<table[^>]*>(.*?)</table>', content, re.DOTALL | re.IGNORECASE)
if tables:
    print("Table length:", len(tables[0]))
    # print first 500 chars of table
    print("Table preview:\n", tables[0][:500])

# Let's inspect the next.js chunks
chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*\"(.*?)\"\]\)', content)
full_chunk_text = ""
for i, c in enumerate(chunks):
    # unescape json string
    try:
        # replace escaped quotes
        c_unesc = c.encode('utf-8').decode('unicode_escape')
        full_chunk_text += c_unesc
    except Exception as e:
        full_chunk_text += c

print("Total unescaped chunk length:", len(full_chunk_text))

# Let's look for known trading codes like 'SQURPHARMA', 'GP', 'BATBC', 'BRACBANK'
for code in ['SQURPHARMA', 'GP', 'BATBC', 'BRACBANK', 'BEXIMCO', 'WALTONHIL', 'OLYMPIC']:
    pos = full_chunk_text.find(code)
    print(f"Code {code}: found at {pos}")
    if pos != -1:
        print(f"Context for {code}:", full_chunk_text[max(0, pos-100):min(len(full_chunk_text), pos+200)])
        break
