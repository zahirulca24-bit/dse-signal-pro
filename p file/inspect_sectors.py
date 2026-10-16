with open('sectors_page.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Let's search for links or text inside sectors_page.html
links = re.findall(r'href=[\"\'](/companies/sectors/[^\"\']+)[\"\']', text)
print("Sector detail links:", len(links), links)

# Let's search for sector names and counts
# Usually has something like "Bank (36)" or "36 companies"
matches = re.findall(r'([A-Za-z &]+)\s*\((\d+)\)', text)
print("Name + count matches:", matches[:25])

# Let's look for any json or list items
chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*\"(.*?)\"\]\)', text)
print("Chunks:", len(chunks))
for i, c in enumerate(chunks):
    if 'Bank' in c or 'Textile' in c or 'companies' in c:
        print(f"Chunk {i} has keywords! Len {len(c)}")
        try:
            unesc = c.encode('utf-8').decode('unicode_escape')
            print(unesc[:400])
        except:
            print(c[:400])
