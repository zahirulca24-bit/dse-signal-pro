"""
Comprehensive Automated Smoke Test Suite for DSE Signal Pro.
Tests:
  1. Frontend Assets (HTML, CSS, JS syntax, TradingView library)
  2. FastAPI Backend Engine (Routes, 6-Pillar Analyst Engine, History, Screener)
  3. Live HTTP Server Loopback (Real TCP Socket, Headers, Content-Length, Data Delivery)
"""

import os
import sys
import time
import json
import urllib.request
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "Backend"
APP_DIR = ROOT / "app"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

passed_tests = 0
failed_tests = 0

def log_test(name: str, passed: bool, detail: str = ""):
    global passed_tests, failed_tests
    if passed:
        passed_tests += 1
        print(f"  [PASS] {name} {f'({detail})' if detail else ''}")
    else:
        failed_tests += 1
        print(f"  [FAIL] {name} {f'- {detail}' if detail else ''}")

def run_smoke_tests():
    print("\n" + "=" * 70)
    print("      DSE SIGNAL PRO — AUTOMATED SMOKE TEST SUITE")
    print("=" * 70 + "\n")

    # -------------------------------------------------------------
    # SUITE 1: FRONTEND ASSETS & SYNTAX INTEGRITY
    # -------------------------------------------------------------
    print("--- 1. Testing Frontend Static Assets & Syntax ---")
    
    # 1.1 index.html
    index_file = APP_DIR / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        has_deck = "chart-analyst-deck" in content
        has_table = "screenerTableBody" in content
        has_lines_btn = "togglePlanLinesBtn" in content
        log_test("HTML Markup Integrity", has_deck and has_table and has_lines_btn, 
                 "Analyst Deck, Screener Table, & Trade Lines button verified")
    else:
        log_test("HTML Markup Integrity", False, "app/index.html not found")

    # 1.2 LightweightCharts Library
    lc_file = APP_DIR / "js" / "lightweight-charts.standalone.production.js"
    log_test("TradingView LightweightCharts Library", lc_file.exists() and lc_file.stat().st_size > 100000,
             f"Size: {lc_file.stat().st_size // 1024} KB")

    # 1.3 CSS Palette & Styles
    css_file = APP_DIR / "css" / "style.css"
    if css_file.exists():
        css_txt = css_file.read_text(encoding="utf-8")
        has_verdict = ".verdict-buy" in css_txt and ".chart-analyst-deck" in css_txt
        log_test("CSS Stylesheet & Theme", has_verdict, "Analyst verdict badges and deck styles present")
    else:
        log_test("CSS Stylesheet", False, "style.css not found")

    # 1.4 JavaScript Syntax Check via Node.js
    try:
        res = subprocess.run(["node", "-c", str(APP_DIR / "js" / "app.js")], 
                             capture_output=True, text=True, cwd=str(ROOT))
        log_test("JS Syntax Compilation (node -c)", res.returncode == 0, 
                 "No syntax errors in app.js" if res.returncode == 0 else res.stderr.strip())
    except Exception as e:
        log_test("JS Syntax Compilation", False, str(e))

    # -------------------------------------------------------------
    # SUITE 2: FASTAPI UNIFIED BACKEND & ANALYST ENGINE
    # -------------------------------------------------------------
    print("\n--- 2. Testing FastAPI Unified Backend Engine ---")
    try:
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)

        # 2.1 Static Root Mount
        r = client.get("/")
        log_test("GET / (Frontend Static Mounting)", r.status_code == 200 and "DSE Signal" in r.text, 
                 f"Status: {r.status_code}")

        # 2.2 Market Summary
        r = client.get("/api/market-summary")
        data = r.json()
        log_test("GET /api/market-summary", r.status_code == 200 and data.get("total_symbols") == 393,
                 f"Total symbols: {data.get('total_symbols')}, Advances: {data.get('advances')}")

        # 2.3 Stock History (GP)
        r = client.get("/api/history?symbol=GP")
        data = r.json()
        candles = data.get("candles", [])
        log_test("GET /api/history?symbol=GP", r.status_code == 200 and len(candles) >= 400,
                 f"Status: {r.status_code}, Candles returned: {len(candles)}")

        # 2.4 Stock History (SQURPHARMA)
        r = client.get("/api/history?symbol=SQURPHARMA")
        data = r.json()
        candles_sq = data.get("candles", [])
        log_test("GET /api/history?symbol=SQURPHARMA", r.status_code == 200 and len(candles_sq) >= 400,
                 f"Status: {r.status_code}, Candles returned: {len(candles_sq)}")

        # 2.5 Sector Rotation
        r = client.get("/api/sectors/rotation")
        data = r.json()
        sectors = data.get("sectors", [])
        log_test("GET /api/sectors/rotation", r.status_code == 200 and len(sectors) >= 15,
                 f"Sectors tracked: {len(sectors)}")

        # 2.6 Screener Engine (6-Pillar Results)
        r = client.get("/api/screener")
        data = r.json()
        results = data.get("results", [])
        stats = data.get("stats", {})
        log_test("GET /api/screener", r.status_code == 200 and len(results) >= 390,
                 f"Screened stocks: {len(results)}, Buy setups: {stats.get('BUY_SETUP', 0)}, Avoid: {stats.get('AVOID', 0)}")

        # 2.7 6-Pillar Analyst Decision for ANWARGALV (BUY SETUP)
        r = client.get("/api/analyst/ANWARGALV")
        data = r.json()
        plan = data.get("trade_plan", {})
        is_buy = data.get("verdict") == "BUY SETUP" and data.get("category") == "A" and plan.get("rrr", 0) >= 2.0
        log_test("Analyst Decision: ANWARGALV", is_buy, 
                 f"Verdict: {data.get('verdict')}, Cat: {data.get('category')}, RRR: {plan.get('rrr')}:1")

        # 2.8 6-Pillar Analyst Decision for ABBANK (AVOID Z-Category)
        r = client.get("/api/analyst/ABBANK")
        data = r.json()
        is_avoid = data.get("verdict") == "AVOID" and data.get("category") == "Z"
        log_test("Analyst Decision: ABBANK (Z-Disqualification)", is_avoid,
                 f"Verdict: {data.get('verdict')}, Cat: {data.get('category')}, SubType: {data.get('sub_type')}")

        # 2.9 Grouped Verdicts
        r = client.get("/api/analyst/verdicts")
        data = r.json()
        counts = data.get("counts", {})
        log_test("GET /api/analyst/verdicts", r.status_code == 200 and counts.get("BUY_SETUP", 0) > 0,
                 f"BUY_SETUP: {counts.get('BUY_SETUP')}, WAIT: {counts.get('WAIT')}, AVOID: {counts.get('AVOID')}")

    except Exception as e:
        log_test("FastAPI Unified Backend Engine", False, str(e))

    # -------------------------------------------------------------
    # SUITE 3: STANDALONE SERVER REAL NETWORK LOOPBACK TEST
    # -------------------------------------------------------------
    print("\n--- 3. Testing Standalone HTTP Server on Loopback Socket ---")
    test_port = 8099
    py_exec = ROOT / "Backend" / ".venv" / "Scripts" / "python.exe"
    if not py_exec.exists():
        py_exec = Path(sys.executable)

    # Temporary environment setting test port
    server_env = os.environ.copy()
    server_env["PORT"] = str(test_port)

    # Launch server with modified port via env var
    cmd = [str(py_exec), "app/server.py"]

    proc = None
    try:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), env=server_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait up to 6 seconds for socket initialization and data indexing
        server_ready = False
        for _ in range(25):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/market-summary", timeout=0.8) as test_resp:
                    if test_resp.status == 200:
                        server_ready = True
                        break
            except Exception:
                time.sleep(0.3)

        if not server_ready:
            raise RuntimeError(f"Server on port {test_port} did not start in time.")

        # 3.1 Live GET /
        url_root = f"http://127.0.0.1:{test_port}/"
        with urllib.request.urlopen(url_root, timeout=3) as resp:
            content = resp.read().decode('utf-8')
            log_test("Live HTTP: GET / (HTML Delivery)", resp.status == 200 and "DSE Signal" in content,
                     f"HTTP {resp.status}, Content-Length: {len(content)}")

        # 3.2 Live GET /api/history?symbol=GP (Verify Fix for Missing Return & Content-Length)
        url_hist = f"http://127.0.0.1:{test_port}/api/history?symbol=GP"
        with urllib.request.urlopen(url_hist, timeout=3) as resp:
            raw = resp.read().decode('utf-8')
            j = json.loads(raw)
            candles = j.get("candles", [])
            log_test("Live HTTP: GET /api/history?symbol=GP", resp.status == 200 and len(candles) >= 400,
                     f"HTTP {resp.status}, JSON parsed cleanly, {len(candles)} candles")

        # 3.3 Live GET /api/screener
        url_scr = f"http://127.0.0.1:{test_port}/api/screener"
        with urllib.request.urlopen(url_scr, timeout=3) as resp:
            raw = resp.read().decode('utf-8')
            j = json.loads(raw)
            res_cnt = len(j.get("results", []))
            log_test("Live HTTP: GET /api/screener", resp.status == 200 and res_cnt >= 390,
                     f"HTTP {resp.status}, Total results: {res_cnt}")

        # 3.4 Live GET /api/analyst/GP
        url_an = f"http://127.0.0.1:{test_port}/api/analyst/GP"
        with urllib.request.urlopen(url_an, timeout=3) as resp:
            raw = resp.read().decode('utf-8')
            j = json.loads(raw)
            log_test("Live HTTP: GET /api/analyst/GP", resp.status == 200 and "trade_plan" in j,
                     f"HTTP {resp.status}, Verdict: {j.get('verdict')}")

    except Exception as e:
        log_test("Live HTTP Loopback Test", False, str(e))
    finally:
        if proc:
            proc.terminate()
            proc.wait(timeout=3)

    # -------------------------------------------------------------
    # SMOKE TEST SUMMARY REPORT
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"      SMOKE TEST SUMMARY: {passed_tests} PASSED | {failed_tests} FAILED")
    print("=" * 70)
    
    if failed_tests == 0:
        print("\n>>> ALL SMOKE TESTS PASSED! System is 100% operational. <<<\n")
        return 0
    else:
        print(f"\n>>> WARNING: {failed_tests} test(s) failed. Please review the details above. <<<\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_smoke_tests())
