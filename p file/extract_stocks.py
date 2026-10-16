with open('latest_sector.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re
import json

# Find all JSON-like objects with "code" and "price"
items = re.findall(r'\{\"code\":\"([^\"]+)\",\"price\":\"([^\"]+)\"(?:,\"change\":([^,\}]+))?(?:,\"delta\":([^,\}]+))?[^\}]*\}', content)
print("Total code+price items found:", len(items))
if items:
    print("First 10 items:", items[:10])

# Let's search if sector mapping exists in content
# Look for "sector" or sector names around JSON
sector_matches = re.findall(r'\"([^\"]*sector[^\"]*)\"', content, re.I)
print("Sector keywords in strings:", set(sector_matches))

# Let's see if there are other data structures
# Let's extract all json arrays or objects in the chunks
chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*\"(.*?)\"\]\)', content)
full_str = ""
for c in chunks:
    try:
        full_str += c.encode('utf-8').decode('unicode_escape')
    except:
        full_str += c

# Look for sector names in full_str
for s in ['Bank', 'Textile', 'Pharmaceuticals & Chemicals', 'Engineering', 'Food & Allied', 'Fuel & Power', 'Insurance', 'IT Sector', 'Telecommunication']:
    idx = full_str.find(s)
    print(f"Sector '{s}' at {idx}")
    if idx != -1:
        print(f"Around '{s}':", full_str[max(0, idx-50):min(len(full_str), idx+200)])
