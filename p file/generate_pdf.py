import json
import os
import subprocess
import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
report_dir = os.path.join(base_dir, "report")
os.makedirs(report_dir, exist_ok=True)

json_path = os.path.join(os.path.dirname(__file__), "dse_sector_stocks.json")
if not os.path.exists(json_path):
    json_path = os.path.join(report_dir, "dse_sector_stocks.json")

html_path = os.path.join(report_dir, "dse_sector_report.html")
pdf_path = os.path.join(report_dir, "DSE_Sector_Wise_Stock_Report.pdf")

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

sector_info = {
    'Bank': {'bn': 'ব্যাংকিং খাত', 'type': 'Equity'},
    'Financial In': {'bn': 'আর্থিক প্রতিষ্ঠান (NBFI)', 'type': 'Equity'},
    'Insurance': {'bn': 'বীমা খাত (সাধারণ ও জীবন)', 'type': 'Equity'},
    'FoodAllied': {'bn': 'খাদ্য ও আনুষঙ্গিক', 'type': 'Equity'},
    'PharmaChem': {'bn': 'ওষুধ ও রসায়ন', 'type': 'Equity'},
    'Textile': {'bn': 'বস্ত্র ও পোশাক শিল্প', 'type': 'Equity'},
    'Engineering': {'bn': 'প্রকৌশল খাত', 'type': 'Equity'},
    'FuelPower': {'bn': 'জ্বালানি ও বিদ্যুৎ', 'type': 'Equity'},
    'Cement': {'bn': 'সিমেন্ট শিল্প', 'type': 'Equity'},
    'Telecom': {'bn': 'টেলিযোগাযোগ', 'type': 'Equity'},
    'IT': {'bn': 'তথ্যপ্রযুক্তি', 'type': 'Equity'},
    'Ceramic': {'bn': 'সিরামিক শিল্প', 'type': 'Equity'},
    'Tannery': {'bn': 'চামড়া শিল্প', 'type': 'Equity'},
    'PaperPrint': {'bn': 'কাগজ ও প্রকাশনা', 'type': 'Equity'},
    'Jute': {'bn': 'পাট শিল্প', 'type': 'Equity'},
    'ServRealEst': {'bn': 'সেবা ও আবাসন', 'type': 'Equity'},
    'TravelLeisur': {'bn': 'ভ্রমণ ও অবকাশ', 'type': 'Equity'},
    'Misc': {'bn': 'বিবিধ খাত', 'type': 'Equity'},
    'MutFund': {'bn': 'মিউচুয়াল ফান্ড', 'type': 'Fund'},
    'CorpBond': {'bn': 'কর্পোরেট বন্ড / সুকুক', 'type': 'Debt'},
    'Debenture': {'bn': 'ডিবেঞ্চার', 'type': 'Debt'},
    'TBond': {'bn': 'সরকারি ট্রেজারি বন্ড (BGTB)', 'type': 'Debt'}
}

# Preferred order of sectors
sector_order = [
    'Bank', 'Financial In', 'Insurance', 'FoodAllied', 'PharmaChem', 
    'Textile', 'Engineering', 'FuelPower', 'Cement', 'Telecom', 
    'IT', 'Ceramic', 'Tannery', 'PaperPrint', 'Jute', 
    'ServRealEst', 'TravelLeisur', 'Misc', 'MutFund', 'CorpBond', 
    'Debenture', 'TBond'
]

total_securities = sum(data[s]['count'] for s in data)

html_content = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<title>DSE Sector-Wise Stock Analysis & Price Report</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 10mm 12mm 12mm 12mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Kalpurush", sans-serif;
    color: #1e293b;
    background: #fff;
    margin: 0;
    padding: 0;
    font-size: 11px;
    line-height: 1.4;
  }}
  .header {{
    border-bottom: 3px solid #1e3a8a;
    padding-bottom: 12px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .header-left h1 {{
    font-size: 22px;
    margin: 0 0 4px 0;
    color: #0f172a;
    letter-spacing: -0.5px;
  }}
  .header-left p {{
    margin: 0;
    color: #475569;
    font-size: 12px;
    font-weight: 500;
  }}
  .header-right {{
    text-align: right;
    font-size: 10px;
    color: #64748b;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 600;
  }}
  .badge-primary {{ background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}
  .badge-count {{ background: #f1f5f9; color: #334155; font-size: 10px; padding: 2px 6px; border-radius: 4px; }}
  
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 20px;
  }}
  .stat-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 10px 12px;
  }}
  .stat-card .label {{
    font-size: 10px;
    text-transform: uppercase;
    color: #64748b;
    font-weight: 600;
    letter-spacing: 0.5px;
  }}
  .stat-card .val {{
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    margin-top: 2px;
  }}
  
  .summary-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 25px;
    font-size: 10.5px;
  }}
  .summary-table th {{
    background: #1e3a8a;
    color: #fff;
    text-align: left;
    padding: 6px 10px;
    font-weight: 600;
  }}
  .summary-table td {{
    padding: 5px 10px;
    border-bottom: 1px solid #e2e8f0;
  }}
  .summary-table tr:nth-child(even) td {{
    background: #f8fafc;
  }}

  .sector-section {{
    margin-bottom: 18px;
    page-break-inside: avoid;
  }}
  .sector-header {{
    background: #f1f5f9;
    border-left: 4px solid #1e3a8a;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    border-radius: 0 4px 4px 0;
  }}
  .sector-header span.sec-type {{
    font-size: 9.5px;
    color: #64748b;
    font-weight: normal;
  }}

  .stock-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
  }}
  .stock-item {{
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 5px 8px;
    background: #fff;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .stock-item .sym {{
    font-weight: 700;
    font-size: 10.5px;
    color: #1e293b;
  }}
  .stock-item .sym-cat {{
    font-size: 8px;
    color: #94a3b8;
    margin-left: 3px;
  }}
  .stock-item .price {{
    font-weight: 600;
    font-size: 10.5px;
    color: #047857;
  }}
  .stock-item .price.zero {{
    color: #94a3b8;
    font-weight: normal;
  }}

  .page-break {{
    page-break-before: always;
  }}
  
  .footer-note {{
    margin-top: 30px;
    border-top: 1px solid #cbd5e1;
    padding-top: 8px;
    font-size: 9px;
    color: #64748b;
    text-align: center;
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>Dhaka Stock Exchange (DSE)</h1>
    <p>Sector-Wise Comprehensive Market, Stock Listing & Price Analysis</p>
  </div>
  <div class="header-right">
    <div><strong>Workspace:</strong> D:\\My DSE signal</div>
    <div><strong>Source:</strong> DSE Live Feed & Database</div>
    <div><strong>Generated:</strong> {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}</div>
  </div>
</div>

<div class="stats-grid">
  <div class="stat-card">
    <div class="label">Total Sectors</div>
    <div class="val">22</div>
  </div>
  <div class="stat-card">
    <div class="label">Total Listed Securities</div>
    <div class="val">{total_securities}</div>
  </div>
  <div class="stat-card">
    <div class="label">Industry / Equity Sectors</div>
    <div class="val">18</div>
  </div>
  <div class="stat-card">
    <div class="label">Funds & Debt Instruments</div>
    <div class="val">4</div>
  </div>
</div>

<h3 style="font-size: 13px; margin: 15px 0 8px 0; color: #1e3a8a;">১. সেক্টরভিত্তিক সংক্ষিপ্ত পরিসংখ্যান (Sector Summary)</h3>
<table class="summary-table">
  <thead>
    <tr>
      <th style="width: 35px;">#</th>
      <th>সেক্টরের নাম (Sector Name)</th>
      <th>খাতের বিবরণ (Description)</th>
      <th>ধরন (Type)</th>
      <th style="text-align: right;">মোট স্টক সংখ্যা (Quantity)</th>
    </tr>
  </thead>
  <tbody>
"""

for idx, s in enumerate(sector_order, 1):
    info = sector_info.get(s, {'bn': s, 'type': 'Equity'})
    cnt = data[s]['count']
    html_content += f"""
    <tr>
      <td>{idx}</td>
      <td><strong>{s}</strong></td>
      <td>{info['bn']}</td>
      <td><span class="badge badge-primary">{info['type']}</span></td>
      <td style="text-align: right; font-weight: bold;">{cnt}</td>
    </tr>"""

html_content += f"""
    <tr style="background: #e2e8f0; font-weight: bold;">
      <td colspan="4" style="text-align: right;">সর্বমোট সিকিউরিটিজ সংখ্যা (Total Securities):</td>
      <td style="text-align: right; font-size: 12px; color: #1e3a8a;">{total_securities}</td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<h3 style="font-size: 13px; margin: 0 0 12px 0; color: #1e3a8a;">২. সেক্টর অনুযায়ী সকল স্টকের ট্রেডিং কোড এবং সর্বশেষ দর (Detailed Stock List & LTP)</h3>
<p style="font-size: 9.5px; color: #64748b; margin-top: -6px; margin-bottom: 14px;">(দর উল্লেখ করা হয়েছে বাংলাদেশী টাকা - ৳ তে। ০.০ ৳ নির্দেশ করে যে স্টকে সংশ্লিষ্ট সেশনে কোনো লেনদেন ঘটেনি বা সাময়িক স্থগিত)</p>
"""

for s in sector_order:
    info = sector_info.get(s, {'bn': s, 'type': 'Equity'})
    st_list = data[s]['stocks']
    
    html_content += f"""
<div class="sector-section">
  <div class="sector-header">
    <div>
      <span>{s}</span> 
      <span style="font-weight: normal; color: #475569;">— {info['bn']}</span>
    </div>
    <div>
      <span class="sec-type" style="margin-right: 8px;">[{info['type']}]</span>
      <span class="badge-count">মোট {len(st_list)} টি</span>
    </div>
  </div>
  <div class="stock-grid">"""

    for st in st_list:
        code = st['code']
        ltp = st['ltp']
        cat = st.get('category', '')
        price_str = f"{ltp:,.2f} ৳" if ltp > 0 else "0.00 ৳"
        zero_cls = " zero" if ltp == 0 else ""
        cat_badge = f'<span class="sym-cat">({cat})</span>' if cat else ""
        
        html_content += f"""
    <div class="stock-item">
      <span class="sym">{code}{cat_badge}</span>
      <span class="price{zero_cls}">{price_str}</span>
    </div>"""

    html_content += """
  </div>
</div>
"""

html_content += """
<div class="footer-note">
  This document was automatically compiled from Dhaka Stock Exchange (DSE) official market data. Prepared for technical analysis, systematic research & signal automation in D:\\My DSE signal.
</div>

</body>
</html>
"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"HTML generated at: {html_path}")

# Now convert to PDF using Headless Edge
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if os.path.exists(edge_path):
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]
    print("Converting HTML to PDF with Edge headless...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(pdf_path):
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"SUCCESS! PDF created at: {pdf_path} ({size_kb:.1f} KB)")
    else:
        print("Failed to generate PDF. Return code:", res.returncode, "Stderr:", res.stderr)
else:
    print("Edge path not found.")
