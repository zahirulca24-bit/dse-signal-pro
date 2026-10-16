import json

with open('dse_sector_stocks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sector_full_names = {
    'Bank': 'Bank (ব্যাংকিং)',
    'Financial In': 'Financial Institutions (আর্থিক প্রতিষ্ঠান / NBFI)',
    'Insurance': 'Insurance (বীমা খাত)',
    'FoodAllied': 'Food & Allied (খাদ্য ও আনুষঙ্গিক)',
    'PharmaChem': 'Pharmaceuticals & Chemicals (ওষুধ ও রসায়ন)',
    'Textile': 'Textile (বস্ত্র খাত)',
    'Engineering': 'Engineering (প্রকৌশল খাত)',
    'FuelPower': 'Fuel & Power (জ্বালানি ও বিদ্যুৎ)',
    'Cement': 'Cement (সিমেন্ট)',
    'Telecom': 'Telecommunication (টেলিযোগাযোগ)',
    'IT': 'IT Sector (তথ্যপ্রযুক্তি)',
    'Ceramic': 'Ceramics Sector (সিরামিক)',
    'Tannery': 'Tannery Industries (চামড়া শিল্প)',
    'PaperPrint': 'Paper & Printing (কাগজ ও প্রকাশনা)',
    'Jute': 'Jute (পাট শিল্প)',
    'ServRealEst': 'Services & Real Estate (সেবা ও আবাসন)',
    'TravelLeisur': 'Travel & Leisure (ভ্রমণ ও অবকাশ)',
    'Misc': 'Miscellaneous (বিবিধ)',
    'MutFund': 'Mutual Funds (মিউচুয়াল ফান্ড)',
    'CorpBond': 'Corporate Bond (কর্পোরেট বন্ড / সুকুক)',
    'Debenture': 'Debenture (ডিবেঞ্চার)',
    'TBond': 'Treasury Bond (সরকারি ট্রেজারি বন্ড)'
}

output = []
for s_key, s_name in sector_full_names.items():
    if s_key in data:
        st_list = data[s_key]['stocks']
        output.append(f"\n### {s_name} — মোট {len(st_list)} টি")
        lines = [f"**{st['code']}**: {st['ltp']} ৳" for st in st_list]
        output.append(", ".join(lines))

with open('formatted_output.txt', 'w', encoding='utf-8') as f:
    f.write("\n".join(output))

print("Wrote formatted_output.txt successfully")
