# DSE Signal Pro — Institutional Trading Analytics & Charting Platform

An institutional-grade technical analysis, stock screening, and real-time charting platform tailored for the Dhaka Stock Exchange (DSE). Built with high-speed **FastAPI backend engine**, **StockNow-style multi-pane synchronized candlestick charting**, and a **6-Pillar Systematic Analyst Decision Engine**.

---

## 🌟 Key Features

### 1. 6-Pillar Analyst Decision Engine
Automated multi-factor quantitative and structural framework for every traded DSE equity:
- **Pillar 1 — Market Trend Regime:** Dynamic 50 & 200 EMA structure on DSEX benchmark and individual equities.
- **Pillar 2 — Sector Rotation:** Sector-level momentum ranking, Relative Strength (RS), and capital flow monitoring.
- **Pillar 3 — Smart Money Footprint:** Volume breakouts, institutional accumulation zones, and 20-period volume SMA tracking.
- **Pillar 4 — High-Probability Price Action:** Classic breakout setups, pullbacks to key support levels, and pivot validation.
- **Pillar 5 — Dynamic Risk/Reward Ratio (RRR):** Auto-calculated Stop Loss (SL) and Target (T1) guaranteeing strict $\ge 2:1$ RRR on all valid setups.
- **Pillar 6 — Regulatory Safeguards:** Strict category filters (A/B/N approval; automatic hard disqualification for high-risk 'Z' category stocks).

### 2. Multi-Pane Synchronized Chart Studio (StockNow-Style)
- **Primary Stage:** Pure Black & Charcoal Ash institutional theme with candlestick bars, Moving Average (MA 14), and Volume with 20 SMA.
- **RSI 14 Pane:** Overbought (70.00) / Oversold (30.00) reference lines with interactive crosshair sync.
- **MACD Pane:** 12/26 EMA with 9-period Signal Line and color-coded momentum histogram.
- **Interactive Trade Plan Lines:** Visual on-chart dashed overlays for Entry, Stop-Loss, and Target directly from the Analyst Decision Engine.
- **Draggable Multi-Pane Resizers:** Fully adjustable splitters allowing manual resizing of Price, RSI, and MACD panels with persistent layout saving.

### 3. Executive Dashboard & Screener
- **Market Hero Cards:** Real-time DSEX benchmark, daily turnover, advance/decline breadth ratio, and top sector barometer.
- **Top Movers:** Instant tabs for Top Gainers, Losers, and most active stocks by turnover.
- **Full Market Screener:** Filterable 392+ stock screener with 6-pillar verdicts (`BUY SETUP`, `WAIT`, `AVOID`, `EXIT / SELL`) and dual-language (Bangla & English) analyst rationales.

---

## 🚀 Quick Start (1-Click Launch)

### Prerequisites
- Python 3.10+ (Recommended Python 3.11 - 3.14)
- Git

### Running on Windows
Simply double-click or run:
```bat
start.bat
```
`start.bat` automatically:
1. Detects Python environment (virtual environment or global).
2. Closes any lingering port 8080 conflicts.
3. Launches the unified server at `http://localhost:8080`.
4. Automatically opens your default web browser to the platform.

### Running Automated Smoke Tests
To verify all frontend assets, backend API routes, and live loopback sockets:
```bat
test.bat
```
Or directly via Python:
```bash
python tests/smoke_test.py
```

---

## 📁 Repository Structure

```
.
├── app/                        # Frontend UI & Standalone Server
│   ├── css/
│   │   └── style.css           # Institutional Dark Theme & Flexbox Layout
│   ├── js/
│   │   ├── app.js              # State Manager, Chart Controllers & Resizers
│   │   └── lightweight-charts.standalone.production.js
│   ├── index.html              # Multi-page Single-Page App (Dashboard, Chart, Screener)
│   └── server.py               # Standalone Fallback HTTP Server
├── Backend/                    # FastAPI High-Performance Backend Engine
│   ├── src/                    # Signal & Screener Engine Source Code
│   ├── data/                   # Processed Scans & Sector Rotation Data
│   ├── main.py                 # FastAPI Application & Route Definitions
│   └── requirements.txt        # Backend Dependencies
├── by_symbol/                  # 2-Year OHLCV Historical CSVs by Stock
├── tests/
│   └── smoke_test.py           # Automated End-to-End Smoke Test Suite
├── dse_all_stocks_2y_ohlcv.csv # Master 2-Year Historical Market Data
├── start.bat                   # 1-Click Unified Startup Launcher
└── test.bat                    # 1-Click Automated Smoke Test Runner
```

---

## 🛠️ API Documentation

Once the server is running, explore the interactive OpenAPI documentation at:
- **Swagger UI:** `http://localhost:8080/docs`
- **ReDoc:** `http://localhost:8080/redoc`

Key endpoints:
- `GET /api/market-summary` — Real-time market advances, declines, and turnover.
- `GET /api/history?symbol=GP` — 470+ daily candlestick bars for specified ticker.
- `GET /api/screener` — Full market 6-pillar systematic verdicts and scores.
- `GET /api/analyst/{symbol}` — Deep-dive institutional verdict, trade plan, and rationales.

---

## 📄 License
MIT License. Built for algorithmic and quantitative trading research on the Dhaka Stock Exchange.
