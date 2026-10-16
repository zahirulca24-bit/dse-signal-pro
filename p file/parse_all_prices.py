with open('latest_sector.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Look for patterns of stocks and prices
# Earlier we saw: {"code":"SQUARETEXT","price":"48.50","change":0.4140786749482461,"delta":0.20000000000000284}
# Let's extract all of them!
matches = re.findall(r'\{\"code\":\"([^\"]+)\",\"price\":\"([^\"]+)\"', text)
print(f"Direct regex found: {len(matches)} stocks with prices")
if matches:
    print("Sample 10:", matches[:10])

# Let's see if there are more
all_codes = re.findall(r'\"code\":\"([A-Z0-9_\-\.]+)\"', text)
print(f"Total codes found: {len(all_codes)}")
