with open('latest_sector.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# find position of SQUARETEXT
pos = text.find('SQUARETEXT')
print("Position in raw text:", pos)
if pos != -1:
    print("Raw text surrounding SQUARETEXT:")
    print(repr(text[pos-100:pos+200]))
