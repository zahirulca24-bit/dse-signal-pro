// DSE Signal Pro - Unified Dashboard & Multi-Pane Analytics Engine (v6)

// Global Chart Instances
let chartPrice = null;
let chartRSI = null;
let chartMACD = null;

// Global Series
let candleSeries = null;
let ma14Series = null;
let volumeSeries = null;
let volSmaSeries = null;

let rsiSeries = null;
let macdLineSeries = null;
let signalLineSeries = null;
let histogramSeries = null;

// Created Price Lines for drawings
let customPriceLines = [];

// State Data
let activeSymbol = 'GP';
let rawHistoryData = [];
let indicatorData = {
  ma14: [],
  volSma: [],
  rsi: [],
  macd: { macd: [], signal: [], hist: [] }
};

let allSymbolsData = [];
let topMoversData = { gainers: [], losers: [], most_active: [] };
let favoritesData = [];
let sectorsData = [];
let sectorRotationData = [];
let activeDrawerTab = 'gainers';
let activeDashMoversTab = 'gainers';

// Resizable Pane Ratios
let paneRatios = {
  price: 0.55,
  rsi: 0.225,
  macd: 0.225
};

// Drawing Tools State
let activeDrawingTool = 'crosshair';
let isDrawing = false;
let drawStartPoint = null;
let userDrawings = [];

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initSidebarToggle();
  initDrawerCollapse();
  initDrawerResize();
  initHeaderMetrics();
  initKeyboardSearch();
  initDashTabs();
  initScreenerEvents();
  initTradePlanToggle();
  initSectorEvents();
  initPortfolioEvents();
  initAiAnalystEvents();

  // Load backend data
  loadAllMarketData();

  // Multi-pane Chart Initialization & Resizers
  initMultiPaneCharts();
  initPaneResizers();

  // Drawing Tools
  initDrawingTools();

  // Restore saved active symbol and page
  const savedSymbol = localStorage.getItem('dse_active_symbol') || 'GP';
  activeSymbol = savedSymbol;
  loadSymbolData(activeSymbol);

  const savedPage = localStorage.getItem('dse_active_page') || 'dashboard';
  switchToPage(savedPage);
});

// 1. Navigation Switching
function switchToPage(target) {
  const navItems = document.querySelectorAll('.nav-item');
  const pages = document.querySelectorAll('.page-view');

  navItems.forEach(n => {
    if (n.getAttribute('data-page') === target) n.classList.add('active');
    else n.classList.remove('active');
  });

  pages.forEach(p => {
    if (p.id === `page-${target}`) p.classList.add('active');
    else p.classList.remove('active');
  });

  // Drawer Toggle button in header only relevant on Chart page
  const drawerBtn = document.getElementById('drawerToggleBtn');
  if (drawerBtn) {
    drawerBtn.style.display = (target === 'chart') ? 'flex' : 'none';
  }

  try {
    localStorage.setItem('dse_active_page', target);
  } catch (e) {}

  if (target === 'chart') {
    requestAnimationFrame(() => {
      handleResize();
      if (chartPrice) {
        chartPrice.priceScale('right').applyOptions({ autoScale: true });
        chartPrice.timeScale().fitContent();
      }
      if (chartRSI) {
        chartRSI.priceScale('right').applyOptions({ autoScale: true });
        chartRSI.timeScale().fitContent();
      }
      if (chartMACD) {
        chartMACD.priceScale('right').applyOptions({ autoScale: true });
        chartMACD.timeScale().fitContent();
      }
    });
    setTimeout(() => {
      handleResize();
      if (chartPrice) {
        chartPrice.priceScale('right').applyOptions({ autoScale: true });
        chartPrice.timeScale().fitContent();
      }
      if (chartRSI) {
        chartRSI.priceScale('right').applyOptions({ autoScale: true });
        chartRSI.timeScale().fitContent();
      }
      if (chartMACD) {
        chartMACD.priceScale('right').applyOptions({ autoScale: true });
        chartMACD.timeScale().fitContent();
      }
    }, 120);
  }
}

function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const target = item.getAttribute('data-page');
      if (target) switchToPage(target);
    });
  });

  const openChartBtn = document.getElementById('openChartStudioBtn');
  if (openChartBtn) {
    openChartBtn.addEventListener('click', () => {
      switchToPage('chart');
    });
  }
}

function initDashTabs() {
  document.querySelectorAll('.movers-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.movers-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeDashMoversTab = tab.getAttribute('data-tab');
      renderDashboardMovers();
    });
  });
}

// 2. Sidebar Toggle
function initSidebarToggle() {
  const btn = document.getElementById('collapseBtn');
  const sidebar = document.getElementById('sidebar');
  if (btn && sidebar) {
    btn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      setTimeout(handleResize, 200);
    });
  }
}

// 3. Right Market Drawer Toggle & Resizer (StockNow Watchlist Panel)
function initDrawerCollapse() {
  const toggleBtn = document.getElementById('drawerToggleBtn');
  const drawer = document.getElementById('marketDrawer');
  const resizer = document.getElementById('drawerResizer');
  const icon = document.getElementById('drawerToggleIcon');

  if (toggleBtn && drawer) {
    toggleBtn.addEventListener('click', () => {
      drawer.classList.toggle('collapsed');
      const isCollapsed = drawer.classList.contains('collapsed');
      if (resizer) resizer.style.display = isCollapsed ? 'none' : 'block';
      icon.innerText = isCollapsed ? '⫷' : '⫸';
      toggleBtn.title = isCollapsed ? 'Open Watchlist Panel' : 'Hide Watchlist Panel';
      setTimeout(handleResize, 180);
    });
  }
}

function initDrawerResize() {
  const resizer = document.getElementById('drawerResizer');
  const drawer = document.getElementById('marketDrawer');
  if (!resizer || !drawer) return;

  // Restore saved width from localStorage
  const savedW = localStorage.getItem('dse_drawer_width');
  if (savedW && !drawer.classList.contains('collapsed')) {
    const w = Math.min(650, Math.max(180, parseInt(savedW, 10)));
    drawer.style.width = `${w}px`;
  }

  let isDragging = false;
  let startX = 0;
  let startW = 0;

  resizer.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX;
    startW = drawer.getBoundingClientRect().width;
    drawer.classList.add('resizing');
    resizer.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dx = startX - e.clientX; // Dragging towards left widens drawer
    const newW = Math.min(650, Math.max(180, Math.round(startW + dx)));
    drawer.style.width = `${newW}px`;
    handleResize();
  });

  document.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      drawer.classList.remove('resizing');
      resizer.classList.remove('dragging');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      try {
        localStorage.setItem('dse_drawer_width', Math.round(drawer.getBoundingClientRect().width));
      } catch (e) {}
      handleResize();
    }
  });
}

// 4. Top Header & Dashboard Metrics
async function initHeaderMetrics() {
  try {
    const res = await fetch('/api/market-summary');
    if (!res.ok) return;
    const d = await res.json();
    
    // Header Ribbon
    document.getElementById('turnoverVal').innerText = `${d.estimated_turnover_cr} Cr ৳`;
    document.getElementById('advCount').innerText = d.advances;
    document.getElementById('decCount').innerText = d.declines;
    document.getElementById('unchCount').innerText = d.unchanged;
    document.getElementById('marketDate').innerText = d.latest_date;

    // Dashboard Hero Cards
    document.getElementById('cardTurnover').innerText = `${d.estimated_turnover_cr} Cr ৳`;
    document.getElementById('cardVolume').innerText = `Total Traded: ${(d.total_volume / 1000000).toFixed(1)}M Shares`;
    
    const ratio = (d.advances / (d.declines || 1)).toFixed(2);
    document.getElementById('cardRatio').innerText = `${ratio}x (Bullish)`;
    document.getElementById('cardBreadthDetail').innerText = `${d.advances} Advancing vs ${d.declines} Declining`;
  } catch (err) {
    console.error('Header metrics err:', err);
  }
}

// 5. Load Market Datasets
async function loadAllMarketData() {
  try {
    const [moversRes, symsRes, favsRes, secRes, rotRes] = await Promise.all([
      fetch('/api/top-movers'),
      fetch('/api/symbols'),
      fetch('/api/favorites'),
      fetch('/api/sectors-summary'),
      fetch('/api/sectors/rotation').catch(() => null)
    ]);

    topMoversData = await moversRes.json();
    allSymbolsData = await symsRes.json();
    favoritesData = await favsRes.json();
    sectorsData = await secRes.json();
    if (rotRes && rotRes.ok) {
      try {
        const rotData = await rotRes.json();
        sectorRotationData = rotData.sectors || [];
      } catch (e) {}
    }

    // Populate Dashboard (Page 1)
    renderDashboardMovers();
    renderDashboardSectors();
    renderDashboardFavorites();
    initDashQuickPills();

    // Populate Chart Studio (Page 2) Drawer
    renderDrawerTable();
    initDrawerTabs();

    // Populate Smart Screener (Page 3)
    loadScreenerData();
  } catch (err) {
    console.error('Error loading market data:', err);
  }
}

// --- Dashboard Page 1 Renderers ---

function initDashQuickPills() {
  document.querySelectorAll('.dash-pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const sym = btn.getAttribute('data-sym');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });
}

function renderDashboardMovers() {
  const tbody = document.getElementById('dashMoversTableBody');
  if (!tbody) return;

  let list = [];
  if (activeDashMoversTab === 'gainers') list = topMoversData.gainers || [];
  else if (activeDashMoversTab === 'losers') list = topMoversData.losers || [];
  else list = topMoversData.most_active || [];

  tbody.innerHTML = list.slice(0, 8).map(item => {
    const isUp = item.change_pct >= 0;
    const sign = isUp ? '+' : '';
    const badgeCls = isUp ? 'green' : 'red';
    return `
      <tr data-symbol="${item.symbol}">
        <td class="sym">${item.symbol}</td>
        <td class="sec">${item.sector || 'Others'}</td>
        <td class="num">${item.ltp.toFixed(2)}</td>
        <td class="num"><span class="pill-change ${badgeCls}">${sign}${item.change_pct.toFixed(2)}%</span></td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('tr').forEach(row => {
    row.addEventListener('click', () => {
      const sym = row.getAttribute('data-symbol');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });
}

function renderDashboardSectors() {
  const container = document.getElementById('sectorsBarList');
  if (!container || !sectorsData || sectorsData.length === 0) return;

  document.getElementById('cardTopSector').innerText = sectorsData[0].sector;
  document.getElementById('cardTopSectorDetail').innerText = `Avg: +${sectorsData[0].avg_change_pct}% (${sectorsData[0].count} stocks)`;

  container.innerHTML = sectorsData.map(sec => {
    const isPos = sec.avg_change_pct >= 0;
    const sign = isPos ? '+' : '';
    const barCls = isPos ? 'pos' : 'neg';
    const barWidth = Math.min(Math.abs(sec.avg_change_pct) * 20, 100);
    const colorCls = isPos ? 'color: var(--color-green);' : 'color: var(--color-red);';

    return `
      <div class="sector-bar-row">
        <div class="sec-name-wrap">
          <span style="font-weight: 600; color: #fff;">${sec.sector}</span>
          <span style="font-size: 9.5px; color: var(--text-dim);">(${sec.count})</span>
        </div>
        <div class="sec-bar-track">
          <div class="sec-bar-fill ${barCls}" style="width: ${barWidth}%;"></div>
        </div>
        <div style="font-weight: 700; font-size: 10.5px; ${colorCls} text-align: right; width: 60px;">
          ${sign}${sec.avg_change_pct}%
        </div>
      </div>
    `;
  }).join('');
}

function renderDashboardFavorites() {
  const grid = document.getElementById('favoritesGrid');
  if (!grid || !favoritesData) return;

  grid.innerHTML = favoritesData.map(item => {
    const isUp = item.change_pct >= 0;
    const sign = isUp ? '+' : '';
    const badgeCls = isUp ? 'green' : 'red';

    return `
      <div class="fav-card" data-symbol="${item.symbol}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span class="fav-sym">${item.symbol}</span>
          <span class="pill-change ${badgeCls}">${sign}${item.change_pct}%</span>
        </div>
        <div class="fav-price">${item.ltp.toFixed(2)} ৳</div>
        <div class="fav-sub">
          <span style="color: var(--text-dim);">${item.sector}</span>
          <span style="color: var(--text-muted); font-size: 9.5px;">${(item.volume / 1000).toFixed(0)}k vol</span>
        </div>
      </div>
    `;
  }).join('');

  grid.querySelectorAll('.fav-card').forEach(card => {
    card.addEventListener('click', () => {
      const sym = card.getAttribute('data-symbol');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });
}

// --- Chart Studio Page 2 Renderers (StockNow Style) ---

function initMultiPaneCharts() {
  const stack = document.getElementById('panesStack');
  const pPrice = document.getElementById('canvasPrice');
  const pRSI = document.getElementById('canvasRSI');
  const pMACD = document.getElementById('canvasMACD');
  const wPrice = document.getElementById('panePriceWrapper');
  const wRSI = document.getElementById('paneRSIWrapper');
  const wMACD = document.getElementById('paneMACDWrapper');

  if (!stack || !pPrice || !pRSI || !pMACD || typeof LightweightCharts === 'undefined') return;

  const stackW = stack.clientWidth || 900;
  const stackH = stack.clientHeight || 650;
  const totalH = Math.max(260, stackH - 10);

  const priceH = Math.max(120, Math.floor(totalH * paneRatios.price));
  const rsiH = Math.max(50, Math.floor(totalH * paneRatios.rsi));
  const macdH = Math.max(50, totalH - priceH - rsiH);

  if (wPrice) { wPrice.style.flex = 'none'; wPrice.style.height = `${priceH}px`; }
  if (wRSI) { wRSI.style.flex = 'none'; wRSI.style.height = `${rsiH}px`; }
  if (wMACD) { wMACD.style.flex = 'none'; wMACD.style.height = `${macdH}px`; }

  const commonOptions = {
    layout: {
      background: { color: '#000000' },
      textColor: '#888892',
      fontSize: 10.5,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    },
    grid: {
      vertLines: { color: '#131313' },
      horzLines: { color: '#131313' },
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: { color: '#444444', width: 1, style: 2 },
      horzLine: { color: '#444444', width: 1, style: 2 },
    },
    rightPriceScale: {
      borderColor: '#1e1e1e',
      autoScale: true,
    },
    timeScale: {
      borderColor: '#1e1e1e',
      timeVisible: true,
      secondsVisible: false,
    },
  };

  // 1. Main Price Chart
  chartPrice = LightweightCharts.createChart(pPrice, {
    ...commonOptions,
    width: stackW,
    height: priceH,
    rightPriceScale: {
      borderColor: '#1e1e1e',
      autoScale: true,
      scaleMargins: { top: 0.08, bottom: 0.22 },
    },
  });

  candleSeries = chartPrice.addCandlestickSeries({
    upColor: '#2ebd85',
    downColor: '#f6465d',
    borderUpColor: '#2ebd85',
    borderDownColor: '#f6465d',
    wickUpColor: '#2ebd85',
    wickDownColor: '#f6465d',
  });

  ma14Series = chartPrice.addLineSeries({
    color: '#00b4d8', // Cyan MA 14
    lineWidth: 1.5,
    title: '',
  });

  volumeSeries = chartPrice.addHistogramSeries({
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume_scale',
  });

  // Dedicated overlay volume price scale (confined strictly to bottom 18%)
  volumeSeries.priceScale().applyOptions({
    autoScale: true,
    scaleMargins: {
      top: 0.82,
      bottom: 0,
    },
  });

  volSmaSeries = chartPrice.addLineSeries({
    color: '#00b4d8', // Cyan Volume 20 SMA
    lineWidth: 1.2,
    priceScaleId: 'volume_scale',
  });

  // 2. RSI 14 Chart
  chartRSI = LightweightCharts.createChart(pRSI, {
    ...commonOptions,
    width: stackW,
    height: rsiH,
    rightPriceScale: {
      borderColor: '#1e1e1e',
      autoScale: true,
      scaleMargins: { top: 0.12, bottom: 0.12 },
    },
    timeScale: { visible: false },
  });

  rsiSeries = chartRSI.addLineSeries({
    color: '#ab47bc', // Purple RSI 14
    lineWidth: 1.5,
  });

  rsiSeries.createPriceLine({ price: 70, color: '#787b86', lineWidth: 1, lineStyle: 2, title: '70' });
  rsiSeries.createPriceLine({ price: 30, color: '#787b86', lineWidth: 1, lineStyle: 2, title: '30' });
  rsiSeries.createPriceLine({ price: 50, color: '#262626', lineWidth: 1, lineStyle: 3 });

  // 3. MACD Chart
  chartMACD = LightweightCharts.createChart(pMACD, {
    ...commonOptions,
    width: stackW,
    height: macdH,
    rightPriceScale: {
      borderColor: '#1e1e1e',
      autoScale: true,
      scaleMargins: { top: 0.12, bottom: 0.12 },
    },
  });

  histogramSeries = chartMACD.addHistogramSeries({ lineWidth: 1 });
  macdLineSeries = chartMACD.addLineSeries({ color: '#2962ff', lineWidth: 1.5 });
  signalLineSeries = chartMACD.addLineSeries({ color: '#ff6d00', lineWidth: 1.5 });
  macdLineSeries.createPriceLine({ price: 0, color: '#363a45', lineWidth: 1, lineStyle: 1 });

  // Synchronize Visible Time Range across all 3 charts
  let isSyncing = false;
  function syncTimeRange(sender, targets) {
    sender.timeScale().subscribeVisibleTimeRangeChange(range => {
      if (isSyncing || !range) return;
      isSyncing = true;
      targets.forEach(t => t.timeScale().setVisibleRange(range));
      isSyncing = false;
      redrawUserDrawings();
    });
  }

  syncTimeRange(chartPrice, [chartRSI, chartMACD]);
  syncTimeRange(chartRSI, [chartPrice, chartMACD]);
  syncTimeRange(chartMACD, [chartPrice, chartRSI]);

  // Crosshair Sync & Readout Update
  chartPrice.subscribeCrosshairMove(param => handleCrosshairMove(param));
  chartRSI.subscribeCrosshairMove(param => handleCrosshairMove(param));
  chartMACD.subscribeCrosshairMove(param => handleCrosshairMove(param));

  // Double Click to instantly auto-fit price scale and time scale
  pPrice.addEventListener('dblclick', () => {
    chartPrice.priceScale('right').applyOptions({ autoScale: true });
    chartPrice.timeScale().fitContent();
  });
  pRSI.addEventListener('dblclick', () => {
    chartRSI.priceScale('right').applyOptions({ autoScale: true });
  });
  pMACD.addEventListener('dblclick', () => {
    chartMACD.priceScale('right').applyOptions({ autoScale: true });
  });

  window.addEventListener('resize', handleResize);

  // Timeframe Buttons
  document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyTimeframe(btn.getAttribute('data-range'));
    });
  });

  setTimeout(handleResize, 100);
}

// Interactive Draggable Splitters for Resizing Price, RSI, and MACD Panes
function initPaneResizers() {
  const saved = localStorage.getItem('dse_pane_ratios');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (parsed.price >= 0.35 && parsed.price <= 0.72 && parsed.rsi >= 0.15 && parsed.macd >= 0.15) {
        paneRatios = parsed;
      } else {
        localStorage.removeItem('dse_pane_ratios');
        paneRatios = { price: 0.56, rsi: 0.22, macd: 0.22 };
      }
    } catch (e) {
      paneRatios = { price: 0.56, rsi: 0.22, macd: 0.22 };
    }
  } else {
    paneRatios = { price: 0.56, rsi: 0.22, macd: 0.22 };
  }

  const stack = document.getElementById('panesStack');
  const resizerPriceRSI = document.getElementById('resizerPriceRSI');
  const resizerRSIMACD = document.getElementById('resizerRSIMACD');
  if (!stack || !resizerPriceRSI || !resizerRSIMACD) return;

  let activeResizer = null;
  let startY = 0;
  let initialHeights = { price: 0, rsi: 0, macd: 0 };

  function onMouseDown(e, type) {
    activeResizer = type;
    startY = e.clientY;
    const p1 = document.getElementById('panePriceWrapper');
    const p2 = document.getElementById('paneRSIWrapper');
    const p3 = document.getElementById('paneMACDWrapper');

    initialHeights = {
      price: p1 ? p1.getBoundingClientRect().height : 320,
      rsi: p2 ? p2.getBoundingClientRect().height : 120,
      macd: p3 ? p3.getBoundingClientRect().height : 120
    };

    if (type === 'price-rsi') resizerPriceRSI.classList.add('dragging');
    if (type === 'rsi-macd') resizerRSIMACD.classList.add('dragging');

    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  }

  resizerPriceRSI.addEventListener('mousedown', (e) => onMouseDown(e, 'price-rsi'));
  resizerRSIMACD.addEventListener('mousedown', (e) => onMouseDown(e, 'rsi-macd'));

  document.addEventListener('mousemove', (e) => {
    if (!activeResizer) return;
    const dy = e.clientY - startY;
    const totalAvailH = initialHeights.price + initialHeights.rsi + initialHeights.macd;
    if (totalAvailH <= 0) return;

    const minPrice = 180;
    const minRsi = 90;
    const minMacd = 90;

    if (activeResizer === 'price-rsi') {
      let newPriceH = initialHeights.price + dy;
      let newRsiH = initialHeights.rsi - dy;

      if (newPriceH < minPrice) {
        newPriceH = minPrice;
        newRsiH = (initialHeights.price + initialHeights.rsi) - minPrice;
      }
      if (newRsiH < minRsi) {
        newRsiH = minRsi;
        newPriceH = (initialHeights.price + initialHeights.rsi) - minRsi;
      }

      paneRatios.price = newPriceH / totalAvailH;
      paneRatios.rsi = newRsiH / totalAvailH;
      paneRatios.macd = initialHeights.macd / totalAvailH;
    } else if (activeResizer === 'rsi-macd') {
      let newRsiH = initialHeights.rsi + dy;
      let newMacdH = initialHeights.macd - dy;

      if (newRsiH < minRsi) {
        newRsiH = minRsi;
        newMacdH = (initialHeights.rsi + initialHeights.macd) - minRsi;
      }
      if (newMacdH < minMacd) {
        newMacdH = minMacd;
        newRsiH = (initialHeights.rsi + initialHeights.macd) - minMacd;
      }

      paneRatios.price = initialHeights.price / totalAvailH;
      paneRatios.rsi = newRsiH / totalAvailH;
      paneRatios.macd = newMacdH / totalAvailH;
    }

    applyPaneHeights();
  });

  document.addEventListener('mouseup', () => {
    if (activeResizer) {
      activeResizer = null;
      resizerPriceRSI.classList.remove('dragging');
      resizerRSIMACD.classList.remove('dragging');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      try {
        localStorage.setItem('dse_pane_ratios', JSON.stringify(paneRatios));
      } catch (e) {}
      applyPaneHeights();
    }
  });
}

function applyPaneHeights() {
  const stack = document.getElementById('panesStack');
  const wPrice = document.getElementById('panePriceWrapper');
  const wRSI = document.getElementById('paneRSIWrapper');
  const wMACD = document.getElementById('paneMACDWrapper');

  if (!stack || !chartPrice || !chartRSI || !chartMACD) return;

  const stackW = stack.clientWidth || 900;
  const totalH = Math.max(380, stack.clientHeight - 12);

  const minRsi = 100;
  const minMacd = 100;
  const minPrice = 180;

  let rsiH = Math.max(minRsi, Math.floor(totalH * paneRatios.rsi));
  let macdH = Math.max(minMacd, Math.floor(totalH * paneRatios.macd));
  let priceH = totalH - rsiH - macdH;

  if (priceH < minPrice) {
    priceH = minPrice;
    const remaining = Math.max(minRsi + minMacd, totalH - priceH);
    rsiH = Math.floor(remaining * 0.5);
    macdH = remaining - rsiH;
  }

  if (wPrice) { wPrice.style.flex = 'none'; wPrice.style.height = `${priceH}px`; }
  if (wRSI) { wRSI.style.flex = 'none'; wRSI.style.height = `${rsiH}px`; }
  if (wMACD) { wMACD.style.flex = 'none'; wMACD.style.height = `${macdH}px`; }

  chartPrice.applyOptions({ width: stackW, height: priceH });
  chartRSI.applyOptions({ width: stackW, height: rsiH });
  chartMACD.applyOptions({ width: stackW, height: macdH });

  resizeDrawingCanvas();
}

function handleResize() {
  applyPaneHeights();
}

// Load Stock Data & Calculate Technicals (With Auto Price Scale & Positioning)
async function loadSymbolData(symbol) {
  activeSymbol = symbol;
  try {
    localStorage.setItem('dse_active_symbol', symbol);
  } catch (e) {}
  document.getElementById('chartSymbol').innerText = symbol;

  try {
    const res = await fetch(`/api/history?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('Symbol not found');
    const data = await res.json();
    rawHistoryData = data.candles || [];

    if (rawHistoryData.length === 0) return;

    computeAllIndicators(rawHistoryData);

    // Reset price scales to autoScale before applying new dataset
    if (chartPrice) chartPrice.priceScale('right').applyOptions({ autoScale: true });
    if (chartRSI) chartRSI.priceScale('right').applyOptions({ autoScale: true });
    if (chartMACD) chartMACD.priceScale('right').applyOptions({ autoScale: true });
    if (volumeSeries) volumeSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: { top: 0.82, bottom: 0 } });

    // 1. Candlestick Data
    const candleData = rawHistoryData.map(c => ({
      time: c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close
    }));
    candleSeries.setData(candleData);

    // 2. MA 14 Data (Cyan Line)
    ma14Series.setData(indicatorData.ma14);

    // 3. Volume Data & 20 SMA
    const volData = rawHistoryData.map(c => ({
      time: c.time,
      value: c.volume,
      color: c.close >= c.open ? 'rgba(46, 189, 133, 0.38)' : 'rgba(246, 70, 93, 0.38)'
    }));
    volumeSeries.setData(volData);
    volSmaSeries.setData(indicatorData.volSma);

    // 4. RSI 14 Data (Purple Line)
    rsiSeries.setData(indicatorData.rsi);

    // 5. MACD Data (Histogram + Blue/Orange Lines)
    histogramSeries.setData(indicatorData.macd.hist);
    macdLineSeries.setData(indicatorData.macd.macd);
    signalLineSeries.setData(indicatorData.macd.signal);

    // Update Header Badges
    const latest = rawHistoryData[rawHistoryData.length - 1];
    const prev = rawHistoryData.length > 1 ? rawHistoryData[rawHistoryData.length - 2] : latest;
    const chg = latest.close - prev.close;
    const pct = (chg / prev.close * 100).toFixed(2);
    const sign = chg >= 0 ? '+' : '';

    const badge = document.getElementById('chartBadge');
    if (badge) {
      badge.innerText = `${latest.close.toFixed(2)} ৳ (${sign}${pct}%)`;
      badge.className = `pill-change ${chg >= 0 ? 'green' : 'red'}`;
    }

    updateReadoutToLatest();
    updateChartAnalystDeck(symbol);

    // Auto-fit both axes (X: timeScale, Y: priceScale) across ALL 3 PANES
    chartPrice.timeScale().fitContent();
    chartPrice.priceScale('right').applyOptions({ autoScale: true });
    if (chartRSI) {
      chartRSI.timeScale().fitContent();
      chartRSI.priceScale('right').applyOptions({ autoScale: true });
    }
    if (chartMACD) {
      chartMACD.timeScale().fitContent();
      chartMACD.priceScale('right').applyOptions({ autoScale: true });
    }

    setTimeout(() => {
      handleResize();
      chartPrice.timeScale().fitContent();
      chartPrice.priceScale('right').applyOptions({ autoScale: true });
      if (chartRSI) {
        chartRSI.timeScale().fitContent();
        chartRSI.priceScale('right').applyOptions({ autoScale: true });
      }
      if (chartMACD) {
        chartMACD.timeScale().fitContent();
        chartMACD.priceScale('right').applyOptions({ autoScale: true });
      }
    }, 60);
  } catch (err) {
    console.error(`Error loading ${symbol}:`, err);
  }
}

// 6-Pillar Analyst Strategy Deck & Chart Execution Lines
let activePlanLines = [];
let showPlanLines = true;

async function updateChartAnalystDeck(symbol) {
  const sym = symbol.toUpperCase();
  let info = rawScreenerData.find(s => s.symbol === sym);

  if (!info) {
    try {
      const res = await fetch(`/api/analyst/${sym}`);
      if (res.ok) {
        info = await res.json();
      }
    } catch (e) {}
  }

  const vBadge = document.getElementById('deckVerdictBadge');
  const cBadge = document.getElementById('deckCategoryBadge');
  const eEl = document.getElementById('deckEntry');
  const slEl = document.getElementById('deckSL');
  const t1El = document.getElementById('deckT1');
  const rrrEl = document.getElementById('deckRRR');
  const ratBn = document.getElementById('deckRationaleBn');

  // Clear existing plan lines on candleSeries
  activePlanLines.forEach(pl => {
    try { candleSeries.removePriceLine(pl); } catch (e) {}
  });
  activePlanLines = [];

  if (!info) {
    if (vBadge) { vBadge.className = 'verdict-badge verdict-wait'; vBadge.innerText = '⏳ MONITOR'; }
    if (cBadge) { cBadge.className = 'badge-cat badge-cat-a'; cBadge.innerText = 'CAT A'; }
    if (eEl) eEl.innerText = '--';
    if (slEl) slEl.innerText = '--';
    if (t1El) t1El.innerText = '--';
    if (rrrEl) rrrEl.innerText = '--';
    if (ratBn) ratBn.innerText = 'বিশ্লেষণ ডেটা পাওয়া যায়নি';
    return;
  }

  const v = info.verdict || 'WAIT';
  const cat = (info.category || 'A').toUpperCase();
  const plan = info.trade_plan || {};

  // Verdict Styling
  if (vBadge) {
    if (v === 'BUY SETUP') {
      vBadge.className = 'verdict-badge verdict-buy';
      vBadge.innerText = '🟢 BUY SETUP';
    } else if (v === 'WAIT') {
      vBadge.className = 'verdict-badge verdict-wait';
      vBadge.innerText = '⏳ WAIT';
    } else if (v === 'AVOID') {
      vBadge.className = 'verdict-badge verdict-avoid';
      vBadge.innerText = '⛔ AVOID';
    } else {
      vBadge.className = 'verdict-badge verdict-exit';
      vBadge.innerText = '⚠️ EXIT / SELL';
    }
  }

  // Category Styling
  if (cBadge) {
    cBadge.className = `badge-cat badge-cat-${cat.toLowerCase()}`;
    cBadge.innerText = `CAT ${cat}`;
    cBadge.title = cat === 'Z' ? 'DSE Z-Category: High Default Risk' : (cat === 'A' ? 'DSE A-Category: Top Quality (>=10% Div)' : 'DSE Category');
  }

  // Plan values
  if (eEl) eEl.innerText = plan.entry_price ? `৳${plan.entry_price.toFixed(1)}` : '--';
  if (slEl) slEl.innerText = plan.stop_loss ? `৳${plan.stop_loss.toFixed(1)} (-${plan.risk_pct}%)` : '--';
  if (t1El) t1El.innerText = plan.target_1 ? `৳${plan.target_1.toFixed(1)} (+${plan.reward_pct}%)` : '--';
  if (rrrEl) rrrEl.innerText = plan.rrr ? `${plan.rrr}:1` : '--';
  if (ratBn) {
    ratBn.innerText = info.rationale_bn || info.rationale_en || 'পর্যবেক্ষণ করুন';
    if (ratBn.parentElement) ratBn.parentElement.title = info.rationale_en || '';
  }

  // Draw Stop Loss, Target 1, Target 2, Entry Lines on Chart if enabled
  if (showPlanLines && candleSeries && plan.entry_price > 0) {
    try {
      const entryLine = candleSeries.createPriceLine({
        price: plan.entry_price,
        color: '#38bdf8',
        lineWidth: 1.5,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: `ENTRY ৳${plan.entry_price.toFixed(1)}`
      });
      activePlanLines.push(entryLine);

      if (plan.stop_loss > 0) {
        const slLine = candleSeries.createPriceLine({
          price: plan.stop_loss,
          color: '#f6465d',
          lineWidth: 1.5,
          lineStyle: 2, // Dashed
          axisLabelVisible: true,
          title: `STOP LOSS ৳${plan.stop_loss.toFixed(1)} (-${plan.risk_pct}%)`
        });
        activePlanLines.push(slLine);
      }

      if (plan.target_1 > 0) {
        const t1Line = candleSeries.createPriceLine({
          price: plan.target_1,
          color: '#2ebd85',
          lineWidth: 1.5,
          lineStyle: 2, // Dashed
          axisLabelVisible: true,
          title: `TARGET 1 ৳${plan.target_1.toFixed(1)} (+${plan.reward_pct}%)`
        });
        activePlanLines.push(t1Line);
      }

      if (plan.target_2 > 0) {
        const t2Line = candleSeries.createPriceLine({
          price: plan.target_2,
          color: '#2ebd85',
          lineWidth: 1,
          lineStyle: 3, // Dotted
          axisLabelVisible: true,
          title: `TARGET 2 ৳${plan.target_2.toFixed(1)}`
        });
        activePlanLines.push(t2Line);
      }
    } catch (err) {
      console.warn("Could not draw plan price lines:", err);
    }
  }
}

function initTradePlanToggle() {
  const btn = document.getElementById('togglePlanLinesBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      showPlanLines = !showPlanLines;
      btn.classList.toggle('active', showPlanLines);
      btn.innerText = showPlanLines ? '🎯 Trade Lines: ON' : '🎯 Trade Lines: OFF';
      updateChartAnalystDeck(activeSymbol);
    });
  }
}

// Indicator Calculation Engine
function computeAllIndicators(candles) {
  // 1. MA 14
  const ma = [];
  for (let i = 0; i < candles.length; i++) {
    if (i < 13) continue;
    let sum = 0;
    for (let j = 0; j < 14; j++) sum += candles[i - j].close;
    ma.push({ time: candles[i].time, value: +(sum / 14).toFixed(2) });
  }
  indicatorData.ma14 = ma;

  // 2. Volume 20 SMA
  const vSma = [];
  for (let i = 0; i < candles.length; i++) {
    if (i < 19) continue;
    let sum = 0;
    for (let j = 0; j < 20; j++) sum += candles[i - j].volume;
    vSma.push({ time: candles[i].time, value: +(sum / 20).toFixed(0) });
  }
  indicatorData.volSma = vSma;

  // 3. RSI 14 (Wilder's Standard)
  const rsi = [];
  if (candles.length > 14) {
    let gains = 0, losses = 0;
    for (let i = 1; i <= 14; i++) {
      let diff = candles[i].close - candles[i - 1].close;
      if (diff >= 0) gains += diff;
      else losses -= diff;
    }
    let avgGain = gains / 14;
    let avgLoss = losses / 14;
    let rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    rsi.push({ time: candles[14].time, value: +(100 - (100 / (1 + rs))).toFixed(2) });

    for (let i = 15; i < candles.length; i++) {
      let diff = candles[i].close - candles[i - 1].close;
      let g = diff >= 0 ? diff : 0;
      let l = diff < 0 ? -diff : 0;
      avgGain = (avgGain * 13 + g) / 14;
      avgLoss = (avgLoss * 13 + l) / 14;
      rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      rsi.push({ time: candles[i].time, value: +(100 - (100 / (1 + rs))).toFixed(2) });
    }
  }
  indicatorData.rsi = rsi;

  // 4. MACD (12, 26, 9 EMA)
  function calcEMA(period) {
    const k = 2 / (period + 1);
    const res = [];
    let ema = candles[0].close;
    res.push({ time: candles[0].time, val: ema });
    for (let i = 1; i < candles.length; i++) {
      ema = candles[i].close * k + ema * (1 - k);
      res.push({ time: candles[i].time, val: ema });
    }
    return res;
  }

  const ema12 = calcEMA(12);
  const ema26 = calcEMA(26);
  const macdMap = new Map();
  const macdArr = [];

  for (let i = 0; i < candles.length; i++) {
    const diff = ema12[i].val - ema26[i].val;
    macdMap.set(candles[i].time, diff);
    macdArr.push({ time: candles[i].time, value: +diff.toFixed(2) });
  }

  const k9 = 2 / (9 + 1);
  const signalArr = [];
  let sigEma = macdArr[0].value;
  signalArr.push({ time: macdArr[0].time, value: +sigEma.toFixed(2) });

  for (let i = 1; i < macdArr.length; i++) {
    sigEma = macdArr[i].value * k9 + sigEma * (1 - k9);
    signalArr.push({ time: macdArr[i].time, value: +sigEma.toFixed(2) });
  }

  const histArr = [];
  for (let i = 0; i < macdArr.length; i++) {
    const diff = macdArr[i].value - signalArr[i].value;
    histArr.push({
      time: macdArr[i].time,
      value: +diff.toFixed(2),
      color: diff >= 0 ? '#2ebd85' : '#f6465d'
    });
  }

  indicatorData.macd = { macd: macdArr, signal: signalArr, hist: histArr };
}

// Crosshair Readout Sync
function handleCrosshairMove(param) {
  if (!param.time || !param.seriesData) {
    updateReadoutToLatest();
    return;
  }

  const cData = param.seriesData.get(candleSeries);
  const vData = param.seriesData.get(volumeSeries);
  const maData = param.seriesData.get(ma14Series);
  const volSmaData = param.seriesData.get(volSmaSeries);
  const rsiData = param.seriesData.get(rsiSeries);
  const histData = param.seriesData.get(histogramSeries);
  const macdData = param.seriesData.get(macdLineSeries);
  const sigData = param.seriesData.get(signalLineSeries);

  const setT = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
  const fmt = (v) => {
    if (v === undefined || v === null || isNaN(v)) return '--';
    const n = Number(v);
    if (n >= 1000000) return (n / 1000000).toFixed(2) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(2) + 'K';
    return n.toLocaleString();
  };

  if (cData) {
    const o = cData.open.toFixed(2);
    const h = cData.high.toFixed(2);
    const l = cData.low.toFixed(2);
    const c = cData.close.toFixed(2);
    const chg = cData.close - cData.open;
    const pct = cData.open > 0 ? (chg / cData.open * 100).toFixed(2) : '0.00';
    const isUp = cData.close >= cData.open;
    const sign = isUp ? '+' : '';

    setT('valO', o); setT('legO', o);
    setT('valH', h); setT('legH', h);
    setT('valL', l); setT('legL', l);
    setT('valC', c); setT('legC', c);

    const legChg = document.getElementById('legChgBadge');
    if (legChg) {
      legChg.innerText = `${sign}${chg.toFixed(2)} (${sign}${pct}%)`;
      legChg.className = `pill-change ${isUp ? 'green' : 'red'}`;
    }

    const dot = document.getElementById('legDot');
    if (dot) dot.className = `legend-dot ${isUp ? 'green' : 'red'}`;
  }

  if (vData) {
    const vStr = fmt(vData.value);
    setT('valVol', vStr);
    setT('legVol', vStr);
    setT('legVolVal', vStr);
  }

  if (volSmaData) {
    const sStr = fmt(volSmaData.value);
    setT('valVolSMA', sStr);
    setT('legVolSMA', sStr);
  }

  if (maData) {
    const m = Number(maData.value).toFixed(2);
    setT('valMA14', m);
    setT('legMA14', m);
  }

  if (rsiData) {
    const r = Number(rsiData.value).toFixed(2);
    setT('valRSI', r);
    setT('legRSI', r);
  }

  if (histData) {
    const hi = Number(histData.value).toFixed(2);
    setT('valMACDHist', hi);
    setT('legMACDHist', hi);
  }

  if (macdData) {
    const ml = Number(macdData.value).toFixed(2);
    setT('valMACDLine', ml);
    setT('legMACDLine', ml);
  }

  if (sigData) {
    const sl = Number(sigData.value).toFixed(2);
    setT('valMACDSig', sl);
    setT('legMACDSig', sl);
  }
}

function updateReadoutToLatest() {
  if (!rawHistoryData || rawHistoryData.length === 0) return;
  const last = rawHistoryData[rawHistoryData.length - 1];
  const prev = rawHistoryData.length > 1 ? rawHistoryData[rawHistoryData.length - 2] : last;

  const setT = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
  const fmt = (v) => {
    if (v === undefined || v === null || isNaN(v)) return '--';
    const n = Number(v);
    if (n >= 1000000) return (n / 1000000).toFixed(2) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(2) + 'K';
    return n.toLocaleString();
  };

  const o = last.open.toFixed(2);
  const h = last.high.toFixed(2);
  const l = last.low.toFixed(2);
  const c = last.close.toFixed(2);
  const chg = last.close - prev.close;
  const pct = prev.close > 0 ? (chg / prev.close * 100).toFixed(2) : '0.00';
  const isUp = chg >= 0;
  const sign = isUp ? '+' : '';

  setT('chartSymbol', activeSymbol);
  setT('legSymbol', activeSymbol);
  setT('valO', o); setT('legO', o);
  setT('valH', h); setT('legH', h);
  setT('valL', l); setT('legL', l);
  setT('valC', c); setT('legC', c);

  const legChg = document.getElementById('legChgBadge');
  if (legChg) {
    legChg.innerText = `${sign}${chg.toFixed(2)} (${sign}${pct}%)`;
    legChg.className = `pill-change ${isUp ? 'green' : 'red'}`;
  }

  const dot = document.getElementById('legDot');
  if (dot) dot.className = `legend-dot ${isUp ? 'green' : 'red'}`;

  const vStr = fmt(last.volume);
  setT('valVol', vStr);
  setT('legVol', vStr);
  setT('legVolVal', vStr);

  const maLast = indicatorData.ma14[indicatorData.ma14.length - 1];
  if (maLast) {
    const m = maLast.value.toFixed(2);
    setT('valMA14', m);
    setT('legMA14', m);
  }

  const vSmaLast = indicatorData.volSma[indicatorData.volSma.length - 1];
  if (vSmaLast) {
    const s = fmt(vSmaLast.value);
    setT('valVolSMA', s);
    setT('legVolSMA', s);
  }

  const rsiLast = indicatorData.rsi[indicatorData.rsi.length - 1];
  if (rsiLast) {
    const r = rsiLast.value.toFixed(2);
    setT('valRSI', r);
    setT('legRSI', r);
  }

  const histLast = indicatorData.macd.hist[indicatorData.macd.hist.length - 1];
  if (histLast) {
    const hi = histLast.value.toFixed(2);
    setT('valMACDHist', hi);
    setT('legMACDHist', hi);
  }

  const macdLast = indicatorData.macd.macd[indicatorData.macd.macd.length - 1];
  if (macdLast) {
    const ml = macdLast.value.toFixed(2);
    setT('valMACDLine', ml);
    setT('legMACDLine', ml);
  }

  const sigLast = indicatorData.macd.signal[indicatorData.macd.signal.length - 1];
  if (sigLast) {
    const sl = sigLast.value.toFixed(2);
    setT('valMACDSig', sl);
    setT('legMACDSig', sl);
  }
}

function applyTimeframe(range) {
  if (!chartPrice || rawHistoryData.length === 0) return;
  const total = rawHistoryData.length;
  let count = total;
  if (range === '1M') count = 22;
  else if (range === '3M') count = 66;
  else if (range === '6M') count = 130;
  else if (range === '1Y') count = 240;

  const startIdx = Math.max(0, total - count);
  const fromTime = rawHistoryData[startIdx].time;
  const toTime = rawHistoryData[total - 1].time;

  chartPrice.timeScale().setVisibleRange({ from: fromTime, to: toTime });
}

// 7. Drawing Tools Engine (Trendlines, Horizontal Lines, Measure)
function initDrawingTools() {
  const overlay = document.getElementById('drawingCanvas');
  const buttons = document.querySelectorAll('.draw-btn[data-tool]');
  const clearBtn = document.getElementById('clearDrawBtn');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeDrawingTool = btn.getAttribute('data-tool');

      if (activeDrawingTool === 'crosshair') {
        overlay.classList.remove('active-draw');
      } else {
        overlay.classList.add('active-draw');
      }
    });
  });

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      userDrawings = [];
      customPriceLines.forEach(pl => candleSeries.removePriceLine(pl));
      customPriceLines = [];
      redrawUserDrawings();
    });
  }

  resizeDrawingCanvas();

  overlay.addEventListener('mousedown', (e) => {
    if (activeDrawingTool === 'crosshair') return;
    const rect = overlay.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    isDrawing = true;
    drawStartPoint = { x, y };

    if (activeDrawingTool === 'horzline') {
      const price = candleSeries.coordinateToPrice(y);
      if (price !== null) {
        const pl = candleSeries.createPriceLine({
          price: +price.toFixed(2),
          color: '#38bdf8',
          lineWidth: 1.5,
          lineStyle: 0,
          title: `H-Line: ${price.toFixed(2)}`
        });
        customPriceLines.push(pl);
      }
      isDrawing = false;
    }
  });

  overlay.addEventListener('mousemove', (e) => {
    if (!isDrawing || !drawStartPoint) return;
    const rect = overlay.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    redrawUserDrawings();
    const ctx = overlay.getContext('2d');

    if (activeDrawingTool === 'trendline') {
      ctx.beginPath();
      ctx.moveTo(drawStartPoint.x, drawStartPoint.y);
      ctx.lineTo(currentX, currentY);
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2;
      ctx.stroke();
    } else if (activeDrawingTool === 'measure') {
      ctx.strokeStyle = '#a855f7';
      ctx.fillStyle = 'rgba(168, 85, 247, 0.1)';
      ctx.strokeRect(drawStartPoint.x, drawStartPoint.y, currentX - drawStartPoint.x, currentY - drawStartPoint.y);
      ctx.fillRect(drawStartPoint.x, drawStartPoint.y, currentX - drawStartPoint.x, currentY - drawStartPoint.y);

      const p1 = candleSeries.coordinateToPrice(drawStartPoint.y);
      const p2 = candleSeries.coordinateToPrice(currentY);
      if (p1 && p2) {
        const diff = p2 - p1;
        const pct = (diff / p1 * 100).toFixed(2);
        ctx.fillStyle = '#fff';
        ctx.font = '11px sans-serif';
        ctx.fillText(`Δ: ${diff.toFixed(2)} (${pct}%)`, currentX + 8, currentY);
      }
    }
  });

  overlay.addEventListener('mouseup', (e) => {
    if (!isDrawing || !drawStartPoint) return;
    const rect = overlay.getBoundingClientRect();
    const endX = e.clientX - rect.left;
    const endY = e.clientY - rect.top;

    if (activeDrawingTool === 'trendline' && (Math.abs(endX - drawStartPoint.x) > 5 || Math.abs(endY - drawStartPoint.y) > 5)) {
      userDrawings.push({
        type: 'trendline',
        x1: drawStartPoint.x,
        y1: drawStartPoint.y,
        x2: endX,
        y2: endY
      });
    }

    isDrawing = false;
    drawStartPoint = null;
    redrawUserDrawings();
  });
}

function resizeDrawingCanvas() {
  const overlay = document.getElementById('drawingCanvas');
  const wrapper = document.getElementById('panePriceWrapper');
  if (overlay && wrapper) {
    overlay.width = wrapper.clientWidth;
    overlay.height = wrapper.clientHeight;
    redrawUserDrawings();
  }
}

function redrawUserDrawings() {
  const overlay = document.getElementById('drawingCanvas');
  if (!overlay) return;
  const ctx = overlay.getContext('2d');
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  userDrawings.forEach(d => {
    if (d.type === 'trendline') {
      ctx.beginPath();
      ctx.moveTo(d.x1, d.y1);
      ctx.lineTo(d.x2, d.y2);
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  });
}

// 8. Right Market Drawer (Chart Studio Page 2)
function initDrawerTabs() {
  document.querySelectorAll('.drawer-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.drawer-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeDrawerTab = tab.getAttribute('data-tab');
      renderDrawerTable();
    });
  });

  const folderSelect = document.getElementById('drawerFolderSelect');
  if (folderSelect) {
    folderSelect.addEventListener('change', () => {
      renderDrawerTable();
    });
  }

  document.querySelectorAll('.drawer-subfolder').forEach(el => {
    el.addEventListener('click', () => {
      const f = el.getAttribute('data-f');
      if (f && folderSelect) {
        folderSelect.value = f;
        renderDrawerTable();
      }
    });
  });
}

function renderDrawerTable() {
  const thead = document.getElementById('drawerTableHead');
  const tbody = document.getElementById('drawerTableBody');
  if (!tbody || !thead) return;

  thead.innerHTML = `
    <tr>
      <th>Code</th>
      <th>Sector</th>
      <th style="text-align: right;">Last (৳)</th>
      <th style="text-align: right;">Ch%</th>
    </tr>
  `;

  let list = [];
  if (activeDrawerTab === 'favorites') {
    const fName = document.getElementById('drawerFolderSelect')?.value || 'Trade';
    const syms = (userWatchlists && userWatchlists[fName]) ? userWatchlists[fName] : DEFAULT_WATCHLISTS['Trade'];
    list = syms.map(s => {
      return (allSymbolsData || []).find(item => item.symbol === s) || 
             (rawScreenerData || []).find(item => item.symbol === s) || {
               symbol: s,
               sector: 'Others',
               ltp: 0,
               change_pct: 0
             };
    });
  } else if (activeDrawerTab === 'gainers') {
    list = topMoversData.gainers || [];
  } else if (activeDrawerTab === 'active') {
    list = topMoversData.most_active || [];
  } else {
    list = allSymbolsData || [];
  }

  tbody.innerHTML = list.map(item => {
    const isUp = item.change_pct >= 0;
    const sign = isUp ? '+' : '';
    const badgeCls = isUp ? 'green' : 'red';
    const isSel = item.symbol === activeSymbol ? ' selected' : '';

    return `
      <tr data-symbol="${item.symbol}" class="${isSel}">
        <td class="sym">${item.symbol}</td>
        <td class="sec">${item.sector || 'Others'}</td>
        <td class="num">${item.ltp ? item.ltp.toFixed(2) : '--'}</td>
        <td class="num"><span class="pill-change ${badgeCls}">${sign}${item.change_pct ? item.change_pct.toFixed(2) : '0.00'}%</span></td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('tr').forEach(row => {
    row.addEventListener('click', () => {
      const sym = row.getAttribute('data-symbol');
      if (sym) {
        tbody.querySelectorAll('tr').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');
        loadSymbolData(sym);
      }
    });
  });
}

// 9. Keyboard Search
function initKeyboardSearch() {
  const input = document.getElementById('globalSearch');
  if (!input) return;

  window.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault();
      input.focus();
    }
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const sym = input.value.trim().toUpperCase();
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
        input.value = '';
        input.blur();
      }
    }
  });
}

// ========================================================
// PAGE 3: SMART SCREENER & STRATEGY SCANNER ENGINE
// ========================================================

let rawScreenerData = [];
let screenerStats = {};
let activeScreenerStrategy = 'all';

async function loadScreenerData() {
  const tbody = document.getElementById('screenerTableBody');
  try {
    const res = await fetch('/api/screener');
    if (!res.ok) throw new Error('Screener API error');
    const data = await res.json();
    rawScreenerData = data.results || [];
    screenerStats = data.stats || {};

    // Update Counter Badges for 6-Pillar Analyst Framework
    const countAllEl = document.getElementById('countAll');
    if (countAllEl) countAllEl.innerText = data.total || rawScreenerData.length;
    
    const bsEl = document.getElementById('countBuySetup');
    if (bsEl) bsEl.innerText = screenerStats['BUY_SETUP'] || rawScreenerData.filter(s => s.verdict === 'BUY SETUP').length;

    const wEl = document.getElementById('countWait');
    if (wEl) wEl.innerText = screenerStats['WAIT'] || rawScreenerData.filter(s => s.verdict === 'WAIT').length;

    const avEl = document.getElementById('countAvoid');
    if (avEl) avEl.innerText = screenerStats['AVOID'] || rawScreenerData.filter(s => s.verdict === 'AVOID').length;

    const caEl = document.getElementById('countCatA');
    if (caEl) caEl.innerText = screenerStats['CAT_A'] || rawScreenerData.filter(s => s.category === 'A').length;

    const vsEl = document.getElementById('countVolSurge');
    if (vsEl) vsEl.innerText = screenerStats['VOL_SURGE'] || 0;
    
    const totEl = document.getElementById('totalScreenerCount');
    if (totEl) totEl.innerText = data.total || rawScreenerData.length;

    // Populate Sectors Dropdown
    populateScreenerSectors();

    // Render Screener Table
    filterAndRenderScreener();

    // Update current active chart analyst deck if chart view is open
    if (activeSymbol) {
      updateChartAnalystDeck(activeSymbol);
    }

    // Render Sector Matrix & Deep Dive (Page 4)
    renderSectorMatrix();

    // Render Watchlists & Portfolio (Page 5)
    renderWatchlists();
    renderPortfolio();
  } catch (err) {
    console.error('Error loading screener data:', err);
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; color: var(--color-red); padding: 30px;">Error loading screener: ${err.message}</td></tr>`;
    }
  }
}

function populateScreenerSectors() {
  const select = document.getElementById('screenerSectorSelect');
  if (!select) return;

  const sectors = Array.from(new Set(rawScreenerData.map(s => s.sector).filter(Boolean))).sort();
  select.innerHTML = '<option value="ALL">All Sectors (22)</option>' + 
    sectors.map(sec => `<option value="${sec}">${sec}</option>`).join('');
}

function filterAndRenderScreener() {
  const tbody = document.getElementById('screenerTableBody');
  const search = (document.getElementById('screenerSearchInput')?.value || '').trim().toUpperCase();
  const sector = document.getElementById('screenerSectorSelect')?.value || 'ALL';
  const verdictFilter = document.getElementById('screenerVerdictSelect')?.value || 'ALL';
  const categoryFilter = document.getElementById('screenerCategorySelect')?.value || 'ALL';
  const sort = document.getElementById('screenerSortSelect')?.value || 'turnover';

  let list = rawScreenerData.filter(item => {
    // 1. Strategy Card Filter
    if (activeScreenerStrategy !== 'all') {
      if (!item.signals || !item.signals.includes(activeScreenerStrategy)) return false;
    }

    // 2. Search Filter
    if (search) {
      const matchSym = item.symbol.toUpperCase().includes(search);
      const matchName = (item.name || '').toUpperCase().includes(search);
      if (!matchSym && !matchName) return false;
    }

    // 3. Sector Filter
    if (sector !== 'ALL' && item.sector !== sector) return false;

    // 4. Verdict Filter
    if (verdictFilter !== 'ALL' && item.verdict !== verdictFilter) return false;

    // 5. Category Filter
    if (categoryFilter !== 'ALL' && item.category !== categoryFilter) return false;

    return true;
  });

  // Sorting
  if (sort === 'turnover') {
    list.sort((a, b) => (b.turnover_cr || 0) - (a.turnover_cr || 0));
  } else if (sort === 'rrr_desc') {
    list.sort((a, b) => (b.trade_plan?.rrr || 0) - (a.trade_plan?.rrr || 0));
  } else if (sort === 'vol_ratio') {
    list.sort((a, b) => (b.vol_ratio || 0) - (a.vol_ratio || 0));
  } else if (sort === 'change_desc') {
    list.sort((a, b) => b.change_pct - a.change_pct);
  } else if (sort === 'change_asc') {
    list.sort((a, b) => a.change_pct - b.change_pct);
  } else if (sort === 'rsi_asc') {
    list.sort((a, b) => a.rsi14 - b.rsi14);
  } else if (sort === 'symbol') {
    list.sort((a, b) => a.symbol.localeCompare(b.symbol));
  }

  // Update Count
  const matchCountEl = document.getElementById('matchCount');
  if (matchCountEl) matchCountEl.innerText = list.length;

  if (!tbody) return;

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; color: var(--text-dim); padding: 40px;">No stocks match your active filters. Try switching strategy card or resetting category/verdict.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(item => {
    const isUp = item.change_pct >= 0;
    const sign = isUp ? '+' : '';
    const badgeCls = isUp ? 'green' : 'red';

    // Official DSE Category Badge
    const cat = (item.category || 'A').toUpperCase();
    const catBadge = `<span class="badge-cat badge-cat-${cat.toLowerCase()}">CAT ${cat}</span>`;

    // Official Analyst Verdict Badge
    let verdictBadge = '';
    const v = item.verdict || 'WAIT';
    if (v === 'BUY SETUP') {
      verdictBadge = `<span class="verdict-badge verdict-buy">🟢 BUY SETUP</span>`;
    } else if (v === 'WAIT') {
      verdictBadge = `<span class="verdict-badge verdict-wait">⏳ WAIT</span>`;
    } else if (v === 'AVOID') {
      verdictBadge = `<span class="verdict-badge verdict-avoid">⛔ AVOID</span>`;
    } else {
      verdictBadge = `<span class="verdict-badge verdict-exit">⚠️ EXIT/SELL</span>`;
    }

    // Trade Plan
    const plan = item.trade_plan || {};
    const entryStr = plan.entry_price ? `E: ${plan.entry_price.toFixed(1)}` : `E: ${item.ltp.toFixed(1)}`;
    const slStr = plan.stop_loss ? `SL: ${plan.stop_loss.toFixed(1)}` : 'SL: --';
    const t1Str = plan.target_1 ? `T1: ${plan.target_1.toFixed(1)}` : 'T1: --';
    const tradePlanHtml = `
      <div class="plan-chip-group">
        <span class="plan-chip-val" title="Entry Price">${entryStr}</span>
        <span class="plan-chip-val sl" title="Stop-Loss Price (${plan.risk_pct || 0}% risk)">${slStr}</span>
        <span class="plan-chip-val t1" title="Target 1 Price (${plan.reward_pct || 0}% gain)">${t1Str}</span>
      </div>
    `;

    // RRR Badge
    let rrrHtml = '<span class="rrr-pill rrr-poor">--</span>';
    if (plan.rrr) {
      const isGood = plan.rrr >= 2.0;
      rrrHtml = `<span class="rrr-pill ${isGood ? 'rrr-good' : 'rrr-poor'}" title="Risk/Reward Ratio">${plan.rrr}:1</span>`;
    }

    // Vol Ratio Badge
    let volRatioBadge = `${item.vol_ratio}x`;
    if (item.vol_ratio >= 1.8) {
      volRatioBadge = `<span class="tag-badge surge">${item.vol_ratio}x 🔥</span>`;
    }

    // RSI Badge
    let rsiBadge = `${item.rsi14}`;
    if (item.rsi14 <= 35) {
      rsiBadge = `<span class="tag-badge oversold">${item.rsi14} 💎</span>`;
    } else if (item.rsi14 >= 70) {
      rsiBadge = `<span class="tag-badge" style="background: rgba(246, 70, 93, 0.15); color: #f6465d;">${item.rsi14} ⚠️</span>`;
    }

    // Institutional Rationale (Bengali + English tooltip)
    const ratBn = item.rationale_bn || item.rationale_en || '--';
    const ratEn = item.rationale_en || '';

    return `
      <tr data-sym="${item.symbol}">
        <td>
          <div class="screener-sym-col">
            <div style="display: flex; align-items: center; gap: 5px;">
              <span class="screener-sym-name">${item.symbol}</span>
              ${catBadge}
            </div>
            <span class="screener-sub-name" title="${item.name}">${item.name || ''}</span>
          </div>
        </td>
        <td>${verdictBadge}</td>
        <td>${tradePlanHtml}</td>
        <td style="text-align: center;">${rrrHtml}</td>
        <td style="color: var(--text-muted); font-size: 11px;">${item.sector}</td>
        <td style="text-align: right; font-weight: 700; color: #fff;">${item.ltp.toFixed(2)}</td>
        <td style="text-align: right;"><span class="pill-change ${badgeCls}">${sign}${item.change_pct.toFixed(2)}%</span></td>
        <td style="text-align: right;">${volRatioBadge}</td>
        <td style="text-align: right; font-weight: 600; color: #e2e8f0;">${item.turnover_cr} Cr</td>
        <td style="text-align: right;">${rsiBadge}</td>
        <td>
          <div class="screener-rationale-cell" title="${ratEn}">
            ${ratBn}
          </div>
        </td>
        <td style="text-align: center;">
          <button class="screener-action-btn" data-sym="${item.symbol}">📈 Chart</button>
        </td>
      </tr>
    `;
  }).join('');

  // Click row or button to jump to chart
  tbody.querySelectorAll('.screener-action-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const sym = btn.getAttribute('data-sym');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });

  tbody.querySelectorAll('tr').forEach(row => {
    row.addEventListener('click', () => {
      const sym = row.getAttribute('data-sym');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });
}

function initScreenerEvents() {
  // Strategy cards click
  document.querySelectorAll('.strategy-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.strategy-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      activeScreenerStrategy = card.getAttribute('data-strategy');
      filterAndRenderScreener();
    });
  });

  // Filter controls
  document.getElementById('screenerSearchInput')?.addEventListener('input', () => filterAndRenderScreener());
  document.getElementById('screenerSectorSelect')?.addEventListener('change', () => filterAndRenderScreener());
  document.getElementById('screenerVerdictSelect')?.addEventListener('change', () => filterAndRenderScreener());
  document.getElementById('screenerCategorySelect')?.addEventListener('change', () => filterAndRenderScreener());
  document.getElementById('screenerSortSelect')?.addEventListener('change', () => filterAndRenderScreener());

  // Refresh Button
  document.getElementById('refreshScreenerBtn')?.addEventListener('click', () => {
    loadScreenerData();
  });
}

// ========================================================
// PAGE 4: SECTOR MATRIX & DEEP DIVE ENGINE
// ========================================================

let selectedSector = 'Pharmaceuticals & Chemicals';
let sectorMatrixData = [];

function renderSectorMatrix() {
  const grid = document.getElementById('sectorMatrixGrid');
  if (!grid || !rawScreenerData || rawScreenerData.length === 0) return;

  // 1. Group stocks by Sector
  const sectorGroups = {};
  rawScreenerData.forEach(item => {
    const sec = item.sector || 'Others';
    if (!sectorGroups[sec]) {
      sectorGroups[sec] = {
        name: sec,
        count: 0,
        turnover_cr: 0,
        chg_sum: 0,
        adv: 0,
        dec: 0,
        unch: 0,
        stocks: []
      };
    }
    const g = sectorGroups[sec];
    g.count += 1;
    g.turnover_cr += (item.turnover_cr || 0);
    g.chg_sum += item.change_pct;
    if (item.change_pct > 0.001) g.adv += 1;
    else if (item.change_pct < -0.001) g.dec += 1;
    else g.unch += 1;
    g.stocks.push(item);
  });

  sectorMatrixData = Object.values(sectorGroups).map(g => ({
    ...g,
    avg_change_pct: g.count > 0 ? (g.chg_sum / g.count) : 0,
    turnover_cr: Math.round(g.turnover_cr * 100) / 100
  }));

  // If selected sector is not in data, pick the first one
  if (!sectorMatrixData.some(s => s.name === selectedSector)) {
    selectedSector = sectorMatrixData[0]?.name || '';
  }

  // 2. Sort Sectors
  const sort = document.getElementById('sectorMatrixSort')?.value || 'turnover';
  if (sort === 'turnover') {
    sectorMatrixData.sort((a, b) => b.turnover_cr - a.turnover_cr);
  } else if (sort === 'gainers') {
    sectorMatrixData.sort((a, b) => b.avg_change_pct - a.avg_change_pct);
  } else if (sort === 'losers') {
    sectorMatrixData.sort((a, b) => a.avg_change_pct - b.avg_change_pct);
  } else if (sort === 'count') {
    sectorMatrixData.sort((a, b) => b.count - a.count);
  }

  // 3. Render Sector Cards
  grid.innerHTML = sectorMatrixData.map(sec => {
    const isUp = sec.avg_change_pct >= 0;
    const sign = isUp ? '+' : '';
    const badgeCls = isUp ? 'green' : 'red';
    const isAct = sec.name === selectedSector ? ' active' : '';

    const tot = sec.count || 1;
    const advPct = (sec.adv / tot) * 100;
    const decPct = (sec.dec / tot) * 100;
    const unchPct = (sec.unch / tot) * 100;

    const rInfo = (sectorRotationData || []).find(r => (r.sector || '').trim().toLowerCase() === sec.name.trim().toLowerCase()) || {};
    const phase = rInfo.phase || '';
    const rs5d = rInfo.relative_strength_5d !== undefined ? `${rInfo.relative_strength_5d > 0 ? '+' : ''}${rInfo.relative_strength_5d}` : '';
    
    let phaseBadge = '';
    if (phase === 'LEADING' || phase === 'OUTPERFORMING') {
      phaseBadge = `<span class="tag-badge green" style="font-size: 9px; padding: 1px 5px;" title="Rotation Phase: ${phase} • RS 5D: ${rs5d}">🚀 ${phase}</span>`;
    } else if (phase === 'RECOVERING') {
      phaseBadge = `<span class="tag-badge orange" style="font-size: 9px; padding: 1px 5px;" title="Rotation Phase: ${phase}">⚡ ${phase}</span>`;
    } else if (phase === 'WEAKENING') {
      phaseBadge = `<span class="tag-badge" style="font-size: 9px; padding: 1px 5px; color: #f59e0b; border: 1px solid rgba(245,158,11,0.3);" title="Rotation Phase: ${phase}">⚠️ ${phase}</span>`;
    } else if (phase === 'LAGGING') {
      phaseBadge = `<span class="tag-badge red" style="font-size: 9px; padding: 1px 5px;" title="Rotation Phase: ${phase}">🔻 ${phase}</span>`;
    }

    return `
      <div class="sector-tile-card${isAct}" data-sector="${sec.name}">
        <div class="sector-tile-top">
          <div>
            <div class="sector-tile-name" style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
              <span>${sec.name}</span>
              ${phaseBadge}
            </div>
            <div class="sector-tile-count">${sec.count} Listed Stocks${rs5d ? ` • RS: <b>${rs5d}</b>` : ''}</div>
          </div>
          <span class="pill-change ${badgeCls}">${sign}${sec.avg_change_pct.toFixed(2)}%</span>
        </div>

        <div class="sector-tile-stats">
          <div class="sector-tile-turnover">Turnover: <b>${sec.turnover_cr.toFixed(1)} Cr</b></div>
          <div style="font-size: 10px; color: var(--text-dim);">
            <span style="color: var(--color-green); font-weight: 600;">${sec.adv}▲</span> 
            <span style="color: var(--color-red); font-weight: 600;">${sec.dec}▼</span>
          </div>
        </div>

        <!-- Mini Breadth Progress Bar -->
        <div class="sector-breadth-mini">
          <div class="sector-breadth-adv" style="width: ${advPct}%;"></div>
          <div class="sector-breadth-unch" style="width: ${unchPct}%;"></div>
          <div class="sector-breadth-dec" style="width: ${decPct}%;"></div>
        </div>
      </div>
    `;
  }).join('');

  // Attach Tile Click Handlers
  grid.querySelectorAll('.sector-tile-card').forEach(card => {
    card.addEventListener('click', () => {
      grid.querySelectorAll('.sector-tile-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      selectedSector = card.getAttribute('data-sector');
      renderSectorDrilldown();

      // Scroll smoothly to drilldown section if needed
      document.getElementById('sectorDrilldownSection')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });

  // Render initial drilldown
  renderSectorDrilldown();
}

function renderSectorDrilldown() {
  const currentSec = sectorMatrixData.find(s => s.name === selectedSector);
  if (!currentSec) return;

  const isUp = currentSec.avg_change_pct >= 0;
  const sign = isUp ? '+' : '';
  const badgeCls = isUp ? 'green' : 'red';

  // Update Drilldown Header
  const titleEl = document.getElementById('drilldownSectorName');
  if (titleEl) titleEl.innerText = currentSec.name;

  const badgeEl = document.getElementById('drilldownSectorBadge');
  if (badgeEl) {
    badgeEl.innerText = `${sign}${currentSec.avg_change_pct.toFixed(2)}%`;
    badgeEl.className = `pill-change ${badgeCls}`;
  }

  const countEl = document.getElementById('drilldownCount');
  if (countEl) countEl.innerText = `${currentSec.count} Stocks`;

  const toEl = document.getElementById('drilldownTurnover');
  if (toEl) toEl.innerText = `${currentSec.turnover_cr.toFixed(2)} Cr ৳`;

  const brEl = document.getElementById('drilldownBreadth');
  if (brEl) brEl.innerHTML = `<span style="color: var(--color-green);">${currentSec.adv} Adv</span> / <span style="color: var(--color-red);">${currentSec.dec} Dec</span> / <span>${currentSec.unch} Unch</span>`;

  // Filter stocks inside this sector
  const search = (document.getElementById('drilldownSearch')?.value || '').trim().toUpperCase();
  let stocks = (currentSec.stocks || []).filter(item => {
    if (!search) return true;
    return item.symbol.toUpperCase().includes(search) || (item.name || '').toUpperCase().includes(search);
  });

  // Sort by Turnover within sector
  stocks.sort((a, b) => (b.turnover_cr || 0) - (a.turnover_cr || 0));

  const tbody = document.getElementById('drilldownTableBody');
  if (!tbody) return;

  if (stocks.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 30px;">No stocks match '${search}' in ${currentSec.name}.</td></tr>`;
    return;
  }

  tbody.innerHTML = stocks.map(item => {
    const sUp = item.change_pct >= 0;
    const sSign = sUp ? '+' : '';
    const sBadgeCls = sUp ? 'green' : 'red';

    // RSI Tag
    let rsiBadge = `${item.rsi14}`;
    if (item.rsi14 <= 35) rsiBadge = `<span class="tag-badge oversold">${item.rsi14} 💎</span>`;
    else if (item.rsi14 >= 70) rsiBadge = `<span class="tag-badge" style="color: #f87171;">${item.rsi14} ⚠️</span>`;

    // MA 14 Tag
    const isAboveMA = item.ltp >= item.ma14;
    const maTag = isAboveMA ? `<span class="tag-badge ma14">Above</span>` : `<span style="font-size: 9.5px; color: var(--text-dim);">Below</span>`;

    // Active Signals
    const signalBadges = (item.signals || []).map(s => {
      if (s === 'VOL_SURGE') return `<span class="tag-badge surge">Vol Surge</span>`;
      if (s === 'MACD_CROSS_BULLISH') return `<span class="tag-badge macd">MACD Cross</span>`;
      if (s === 'RSI_OVERSOLD') return `<span class="tag-badge oversold">RSI Oversold</span>`;
      if (s === 'ABOVE_MA14') return `<span class="tag-badge ma14">> MA14</span>`;
      if (s === 'NEAR_52W_HIGH') return `<span class="tag-badge h52">52W High</span>`;
      return '';
    }).join(' ');

    return `
      <tr data-sym="${item.symbol}">
        <td>
          <div class="screener-sym-col">
            <span class="screener-sym-name">${item.symbol}</span>
            <span class="screener-sub-name" title="${item.name}">${item.name || ''}</span>
          </div>
        </td>
        <td style="text-align: right; font-weight: 700; color: #fff;">${item.ltp.toFixed(2)}</td>
        <td style="text-align: right;"><span class="pill-change ${sBadgeCls}">${sSign}${item.change_pct.toFixed(2)}%</span></td>
        <td style="text-align: right; color: var(--text-muted);">${item.volume.toLocaleString()}</td>
        <td style="text-align: right; font-weight: 600; color: #e2e8f0;">${item.turnover_cr} Cr</td>
        <td style="text-align: right;">${rsiBadge}</td>
        <td style="text-align: right; color: var(--text-muted);">${item.ma14.toFixed(2)} ${maTag}</td>
        <td><div style="display: flex; gap: 4px; flex-wrap: wrap;">${signalBadges || '<span style="color: var(--text-dim); font-size: 10px;">--</span>'}</div></td>
        <td style="text-align: center;">
          <button class="screener-action-btn" data-sym="${item.symbol}">📈 View</button>
        </td>
      </tr>
    `;
  }).join('');

  // Row and button click to open chart
  tbody.querySelectorAll('.screener-action-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const sym = btn.getAttribute('data-sym');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });

  tbody.querySelectorAll('tr').forEach(row => {
    row.addEventListener('click', () => {
      const sym = row.getAttribute('data-sym');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });
}

function initSectorEvents() {
  document.getElementById('sectorMatrixSort')?.addEventListener('change', () => renderSectorMatrix());
  document.getElementById('drilldownSearch')?.addEventListener('input', () => renderSectorDrilldown());
}

// ========================================================
// PAGE 5: WATCHLIST & PORTFOLIO ENGINE
// ========================================================

const DEFAULT_WATCHLISTS = {
  'Trade': ['BEXIMCO', 'BRACBANK', 'CROWNCMNT', 'EGEN', 'ENVOYTEX', 'GP', 'HWAWELLTEX', 'IBP', 'KPPL', 'SAIHAMCOT', 'SAMATALETH', 'SHURWID', 'SONALIANSH', 'SPCERAMICS', 'TECHNODRUG', 'USMANIAGL', 'FEKDIL', 'LOVELLO', 'MATINSPINN'],
  'up trand': ['SQURPHARMA', 'ORIONPHARM', 'BATBC', 'GP'],
  'for now': ['SAIHAMTEX', 'FEKDIL', 'LOVELLO'],
  'SME': ['LOVELLO', 'MKFOOTWEAR', 'ACHIASF'],
  'NEW WATCH LIST': ['BDTHAI', 'EBL', 'ROBI'],
  'important watch list': ['GP', 'BATBC', 'SQURPHARMA']
};

let userWatchlists = (() => {
  try {
    const saved = localStorage.getItem('dse_watchlists');
    return saved ? JSON.parse(saved) : DEFAULT_WATCHLISTS;
  } catch (e) {
    return DEFAULT_WATCHLISTS;
  }
})();

let activeWatchlistFolder = 'Trade';

const DEFAULT_HOLDINGS = [
  { symbol: 'SQURPHARMA', buy_price: 210.50, qty: 500 },
  { symbol: 'LOVELLO', buy_price: 68.00, qty: 1200 },
  { symbol: 'GP', buy_price: 320.00, qty: 300 }
];

let userHoldings = (() => {
  try {
    const saved = localStorage.getItem('dse_holdings');
    return saved ? JSON.parse(saved) : DEFAULT_HOLDINGS;
  } catch (e) {
    return DEFAULT_HOLDINGS;
  }
})();

function saveWatchlists() {
  try {
    localStorage.setItem('dse_watchlists', JSON.stringify(userWatchlists));
  } catch (e) {
    console.error('Error saving watchlists:', e);
  }
}

function saveHoldings() {
  try {
    localStorage.setItem('dse_holdings', JSON.stringify(userHoldings));
  } catch (e) {
    console.error('Error saving holdings:', e);
  }
}

// --- Watchlists Functions ---
function renderWatchlists() {
  renderWatchlistFolders();
  renderWatchlistStocks();
}

function renderWatchlistFolders() {
  const container = document.getElementById('watchlistFoldersRow');
  if (!container) return;

  const folderNames = Object.keys(userWatchlists);
  if (!userWatchlists[activeWatchlistFolder] && folderNames.length > 0) {
    activeWatchlistFolder = folderNames[0];
  }

  container.innerHTML = folderNames.map(fName => {
    const count = (userWatchlists[fName] || []).length;
    const isAct = fName === activeWatchlistFolder ? ' active' : '';
    return `
      <button class="folder-tab-btn${isAct}" data-folder="${fName}">
        <span>📁 ${fName}</span>
        <span class="folder-tab-count">${count}</span>
      </button>
    `;
  }).join('') + `
    <button class="folder-tab-btn" id="btnCreateNewFolder" style="border-style: dashed; color: #38bdf8;">
      <span>+ New Folder</span>
    </button>
  `;

  // Folder click handlers
  container.querySelectorAll('.folder-tab-btn[data-folder]').forEach(btn => {
    btn.addEventListener('click', () => {
      activeWatchlistFolder = btn.getAttribute('data-folder');
      renderWatchlistFolders();
      renderWatchlistStocks();
    });
  });

  // Create folder prompt
  document.getElementById('btnCreateNewFolder')?.addEventListener('click', () => {
    const name = prompt('Enter new watchlist folder name:');
    if (name && name.trim()) {
      const cleanName = name.trim();
      if (!userWatchlists[cleanName]) {
        userWatchlists[cleanName] = [];
        activeWatchlistFolder = cleanName;
        saveWatchlists();
        renderWatchlistFolders();
        renderWatchlistStocks();
      }
    }
  });
}

function renderWatchlistStocks() {
  const titleEl = document.getElementById('activeFolderNameTitle');
  if (titleEl) titleEl.innerText = `Folder: ${activeWatchlistFolder}`;

  const symbols = userWatchlists[activeWatchlistFolder] || [];
  const countEl = document.getElementById('activeFolderStockCount');
  if (countEl) countEl.innerText = `${symbols.length} Stocks`;

  const tbody = document.getElementById('watchlistTableBody');
  if (!tbody) return;

  if (symbols.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-dim); padding: 30px;">This folder is empty. Use the input above to add stocks.</td></tr>`;
    return;
  }

  const items = symbols.map(sym => {
    const found = (rawScreenerData || []).find(s => s.symbol === sym) || 
                  (allSymbolsData || []).find(s => s.symbol === sym) || {
                    symbol: sym,
                    name: sym,
                    sector: 'Unknown',
                    ltp: 0,
                    change_pct: 0,
                    volume: 0,
                    turnover_cr: 0,
                    rsi14: '--',
                    ma14: 0,
                    signals: []
                  };
    return found;
  });

  tbody.innerHTML = items.map(item => {
    const isUp = item.change_pct >= 0;
    const sign = isUp ? '+' : '';
    const badgeCls = isUp ? 'green' : 'red';

    // Active Signals
    const signalBadges = (item.signals || []).map(s => {
      if (s === 'VOL_SURGE') return `<span class="tag-badge surge">Vol Surge</span>`;
      if (s === 'MACD_CROSS_BULLISH') return `<span class="tag-badge macd">MACD Cross</span>`;
      if (s === 'RSI_OVERSOLD') return `<span class="tag-badge oversold">RSI Oversold</span>`;
      if (s === 'ABOVE_MA14') return `<span class="tag-badge ma14">> MA14</span>`;
      return '';
    }).join(' ');

    return `
      <tr data-sym="${item.symbol}">
        <td>
          <div class="screener-sym-col">
            <span class="screener-sym-name">${item.symbol}</span>
            <span class="screener-sub-name" title="${item.name}">${item.name || ''}</span>
          </div>
        </td>
        <td style="color: var(--text-muted); font-size: 11px;">${item.sector || 'Others'}</td>
        <td style="text-align: right; font-weight: 700; color: #fff;">${item.ltp ? item.ltp.toFixed(2) : '--'}</td>
        <td style="text-align: right;"><span class="pill-change ${badgeCls}">${sign}${item.change_pct ? item.change_pct.toFixed(2) : '0.00'}%</span></td>
        <td style="text-align: right; color: var(--text-muted);">${item.volume ? item.volume.toLocaleString() : '--'}</td>
        <td style="text-align: right; font-weight: 600; color: #e2e8f0;">${item.turnover_cr ? item.turnover_cr + ' Cr' : '--'}</td>
        <td style="text-align: right;">${item.rsi14 || '--'}</td>
        <td style="text-align: right; color: var(--text-muted);">${item.ma14 ? item.ma14.toFixed(2) : '--'}</td>
        <td><div style="display: flex; gap: 4px; flex-wrap: wrap;">${signalBadges || '<span style="color: var(--text-dim); font-size: 10px;">--</span>'}</div></td>
        <td style="text-align: center;">
          <div style="display: flex; gap: 6px; justify-content: center; align-items: center;">
            <button class="screener-action-btn" data-action="view" data-sym="${item.symbol}">📈 View</button>
            <button class="btn-icon-danger" data-action="remove" data-sym="${item.symbol}" title="Remove from this watchlist">✕</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Row and action button listeners
  tbody.querySelectorAll('.screener-action-btn[data-action="view"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const sym = btn.getAttribute('data-sym');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });

  tbody.querySelectorAll('.btn-icon-danger[data-action="remove"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const sym = btn.getAttribute('data-sym');
      if (sym && userWatchlists[activeWatchlistFolder]) {
        userWatchlists[activeWatchlistFolder] = userWatchlists[activeWatchlistFolder].filter(s => s !== sym);
        saveWatchlists();
        renderWatchlistFolders();
        renderWatchlistStocks();
      }
    });
  });

  tbody.querySelectorAll('tr').forEach(row => {
    row.addEventListener('click', () => {
      const sym = row.getAttribute('data-sym');
      if (sym) {
        loadSymbolData(sym);
        switchToPage('chart');
      }
    });
  });
}

// --- Portfolio Functions ---
function renderPortfolio() {
  const tbody = document.getElementById('holdingsTableBody');
  if (!tbody) return;

  let totalCost = 0;
  let totalValue = 0;
  let totalDailyProfit = 0;

  if (userHoldings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 30px;">No holdings recorded yet. Add your first trade above!</td></tr>`;
  } else {
    tbody.innerHTML = userHoldings.map((h, idx) => {
      const stock = (rawScreenerData || []).find(s => s.symbol === h.symbol) || 
                    (allSymbolsData || []).find(s => s.symbol === h.symbol) || {
                      symbol: h.symbol,
                      name: h.symbol,
                      ltp: h.buy_price,
                      change: 0,
                      change_pct: 0
                    };
      
      const ltp = stock.ltp || h.buy_price;
      const cost = h.buy_price * h.qty;
      const val = ltp * h.qty;
      const profit = val - cost;
      const profitPct = cost > 0 ? (profit / cost) * 100 : 0;
      const dailyProfit = (stock.change || 0) * h.qty;

      totalCost += cost;
      totalValue += val;
      totalDailyProfit += dailyProfit;

      const isProfit = profit >= 0;
      const sign = isProfit ? '+' : '';
      const badgeCls = isProfit ? 'green' : 'red';

      return `
        <tr data-sym="${h.symbol}">
          <td>
            <div class="screener-sym-col">
              <span class="screener-sym-name">${h.symbol}</span>
              <span class="screener-sub-name">${stock.name || ''}</span>
            </div>
          </td>
          <td style="text-align: right; color: var(--text-muted);">${h.buy_price.toFixed(2)}</td>
          <td style="text-align: right; font-weight: 600; color: #fff;">${h.qty.toLocaleString()}</td>
          <td style="text-align: right; color: var(--text-muted);">৳ ${cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
          <td style="text-align: right; font-weight: 700; color: #fff;">৳ ${ltp.toFixed(2)}</td>
          <td style="text-align: right; font-weight: 700; color: #e2e8f0;">৳ ${val.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
          <td style="text-align: right; font-weight: 700;"><span class="pill-change ${badgeCls}">${sign}৳ ${profit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span></td>
          <td style="text-align: right;"><span class="pill-change ${badgeCls}">${sign}${profitPct.toFixed(2)}%</span></td>
          <td style="text-align: center;">
            <div style="display: flex; gap: 6px; justify-content: center; align-items: center;">
              <button class="screener-action-btn" data-action="view" data-sym="${h.symbol}">📈 View</button>
              <button class="btn-icon-danger" data-action="delete" data-idx="${idx}" title="Delete holding">🗑️</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    // Actions in holdings
    tbody.querySelectorAll('.screener-action-btn[data-action="view"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const sym = btn.getAttribute('data-sym');
        if (sym) {
          loadSymbolData(sym);
          switchToPage('chart');
        }
      });
    });

    tbody.querySelectorAll('.btn-icon-danger[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.getAttribute('data-idx'));
        if (!isNaN(idx)) {
          userHoldings.splice(idx, 1);
          saveHoldings();
          renderPortfolio();
        }
      });
    });

    tbody.querySelectorAll('tr').forEach(row => {
      row.addEventListener('click', () => {
        const sym = row.getAttribute('data-sym');
        if (sym) {
          loadSymbolData(sym);
          switchToPage('chart');
        }
      });
    });
  }

  // Update Hero Cards
  const totalProfit = totalValue - totalCost;
  const totalProfitPct = totalCost > 0 ? (totalProfit / totalCost) * 100 : 0;
  const isUp = totalProfit >= 0;
  const sign = isUp ? '+' : '';

  const vEl = document.getElementById('portTotalValue');
  if (vEl) vEl.innerText = `৳ ${totalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

  const cEl = document.getElementById('portTotalCost');
  if (cEl) cEl.innerText = `৳ ${totalCost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

  const pEl = document.getElementById('portTotalProfit');
  if (pEl) {
    pEl.innerText = `${sign}৳ ${totalProfit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    pEl.style.color = isUp ? 'var(--color-green)' : 'var(--color-red)';
  }

  const pctEl = document.getElementById('portProfitPct');
  if (pctEl) pctEl.innerText = `${sign}${totalProfitPct.toFixed(2)}% Overall Return`;

  const dEl = document.getElementById('portDailyProfit');
  if (dEl) {
    const dSign = totalDailyProfit >= 0 ? '+' : '';
    dEl.innerText = `${dSign}৳ ${totalDailyProfit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    dEl.style.color = totalDailyProfit >= 0 ? 'var(--color-green)' : 'var(--color-red)';
  }

  const countEl = document.getElementById('portStockCount');
  if (countEl) countEl.innerText = `${userHoldings.length} Holdings Active`;
}

// --- Event Listeners for Page 5 ---
function initPortfolioEvents() {
  // Subnav View Switching
  const btnWatchlists = document.getElementById('tabWatchlistsBtn');
  const btnPortfolio = document.getElementById('tabPortfolioBtn');
  const cWatchlists = document.getElementById('viewWatchlistsContainer');
  const cPortfolio = document.getElementById('viewPortfolioContainer');

  if (btnWatchlists && btnPortfolio && cWatchlists && cPortfolio) {
    btnWatchlists.addEventListener('click', () => {
      btnWatchlists.classList.add('active');
      btnPortfolio.classList.remove('active');
      cWatchlists.style.display = 'flex';
      cPortfolio.style.display = 'none';
    });

    btnPortfolio.addEventListener('click', () => {
      btnPortfolio.classList.add('active');
      btnWatchlists.classList.remove('active');
      cPortfolio.style.display = 'flex';
      cWatchlists.style.display = 'none';
      renderPortfolio();
    });
  }

  // Add stock to current watchlist
  const addStockBtn = document.getElementById('addStockBtn');
  const addStockInput = document.getElementById('addStockInput');
  if (addStockBtn && addStockInput) {
    addStockBtn.addEventListener('click', () => {
      const sym = addStockInput.value.trim().toUpperCase();
      if (!sym) return;
      if (!userWatchlists[activeWatchlistFolder]) {
        userWatchlists[activeWatchlistFolder] = [];
      }
      if (!userWatchlists[activeWatchlistFolder].includes(sym)) {
        userWatchlists[activeWatchlistFolder].push(sym);
        saveWatchlists();
        renderWatchlistFolders();
        renderWatchlistStocks();
        addStockInput.value = '';
      }
    });

    addStockInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') addStockBtn.click();
    });
  }

  // Add holding to portfolio
  const addHoldingBtn = document.getElementById('addHoldingBtn');
  const symInput = document.getElementById('holdingSymbolInput');
  const priceInput = document.getElementById('holdingBuyPriceInput');
  const qtyInput = document.getElementById('holdingQtyInput');

  if (addHoldingBtn && symInput && priceInput && qtyInput) {
    addHoldingBtn.addEventListener('click', () => {
      const sym = symInput.value.trim().toUpperCase();
      const price = parseFloat(priceInput.value);
      const qty = parseInt(qtyInput.value);

      if (!sym || isNaN(price) || isNaN(qty) || price <= 0 || qty <= 0) {
        alert('Please enter valid Symbol, Buy Price and Quantity.');
        return;
      }

      userHoldings.push({ symbol: sym, buy_price: price, qty: qty });
      saveHoldings();
      renderPortfolio();

      symInput.value = '';
      priceInput.value = '';
      qtyInput.value = '';
    });
  }
}

// ========================================================
// PAGE 6: AI STOCK ANALYST & BACKTEST AUDITOR CONTROLLER
// ========================================================

function initAiAnalystEvents() {
  const periodBtns = document.querySelectorAll('.ai-period-btn');
  let activeAiPeriodCode = '6M';
  let activeAiPeriodText = 'Last 6 Months';

  periodBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      periodBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeAiPeriodCode = btn.getAttribute('data-period') || '6M';
      activeAiPeriodText = btn.innerText.trim();
      const symInput = document.getElementById('aiSymbolQueryInput');
      const sym = symInput ? symInput.value.trim().toUpperCase() || 'FEKDIL' : 'FEKDIL';
      renderAiReport(sym);
    });
  });

  const runBtn = document.getElementById('runAiAnalysisBtn');
  const symInput = document.getElementById('aiSymbolQueryInput');
  const stratSelect = document.getElementById('aiStrategyFilterSelect');

  if (stratSelect) {
    stratSelect.addEventListener('change', () => {
      const sym = symInput ? symInput.value.trim().toUpperCase() || 'FEKDIL' : 'FEKDIL';
      renderAiReport(sym);
    });
  }

  async function renderAiReport(sym) {
    const symbol = (sym || 'FEKDIL').trim().toUpperCase();
    const container = document.getElementById('aiTradesListContainer');
    if (!container) return;

    const strategy = stratSelect ? stratSelect.value : 'ALL';
    
    // Show loading state
    container.innerHTML = `
      <div style="text-align: center; padding: 50px 20px; color: var(--text-dim);">
        <div style="font-size: 24px; margin-bottom: 10px;">⏳</div>
        <div style="font-size: 13px; font-weight: 600; color: #fff; margin-bottom: 6px;">Scanning historical bars for ${symbol}...</div>
        <div style="font-size: 11px;">Auditing candlestick patterns, EMA confluences, and volume breakouts...</div>
      </div>
    `;

    try {
      const url = `/api/ai/audit?symbol=${encodeURIComponent(symbol)}&period=${encodeURIComponent(activeAiPeriodCode)}&strategy=${encodeURIComponent(strategy)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();

      const trades = data.trades || [];
      const traps = data.avoided_traps || [];

      // Render Trades Timeline
      if (trades.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 40px 20px; color: var(--text-dim);">
            <div style="font-size: 22px; margin-bottom: 8px;">🛡️</div>
            <div style="font-size: 13px; font-weight: 600; color: #e2e8f0; margin-bottom: 4px;">উক্ত পিরিয়ডে কোনো কনফার্মড বাই সিগন্যাল পাওয়া যায়নি</div>
            <div style="font-size: 11px;">বটটি ক্যাপিটাল সুরক্ষার লক্ষ্যে কোনো হাই-রিস্ক ট্রেড নেয়নি এবং ফলস ব্রেকআউট এড়িয়েছে।</div>
          </div>
        `;
      } else {
        container.innerHTML = trades.map((t, i) => {
          const isWin = t.outcome === 'win';
          const outcomeClass = isWin ? 'win' : 'loss';
          const outcomeLabel = isWin ? `🟢 TARGET HIT (+${t.gain_pct}%)` : `🔴 STOP LOSS (${t.gain_pct}%)`;
          const gainPrefix = t.gain_pct > 0 ? '+' : '';

          return `
            <div class="ai-trade-card">
              <div class="ai-trade-card-top">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                  <span style="font-size: 12px; font-weight: 800; color: #fff;">#${i + 1} • ${t.date}</span>
                  <span class="ai-strategy-tag">${t.strategy}</span>
                </div>
                <span class="ai-outcome-tag ${outcomeClass}">${outcomeLabel}</span>
              </div>

              <div class="ai-trade-plan-row">
                <span>Entry: <b>৳${Number(t.entry).toFixed(2)}</b></span>
                <span class="sl-val">SL: <b>৳${Number(t.sl).toFixed(2)} (${t.sl_pct}%)</b></span>
                <span class="tp-val">TP: <b>৳${Number(t.tp).toFixed(2)} (+${t.tp_pct}%)</b></span>
                <span class="rrr-val">RRR: <b>${t.rrr}</b></span>
                <button class="btn-primary" style="margin-left: auto; font-size: 10px; padding: 3px 8px; cursor: pointer;" onclick="loadSymbolData('${data.symbol}'); switchToPage('chart');">📈 View on Chart</button>
              </div>

              <div class="ai-trade-rationale">
                <span style="color: var(--text-dim);">লজিক: </span>${t.rationale}
              </div>
            </div>
          `;
        }).join('');
      }

      // Update Hero Scorecards
      const countBadge = document.getElementById('aiTradesCountBadge');
      if (countBadge) countBadge.innerText = `${trades.length} Setups Found`;

      const totalVal = document.getElementById('aiTotalTradesVal');
      if (totalVal) totalVal.innerText = `${trades.length} Trades`;

      const subtitle = document.getElementById('aiPeriodSubtitle');
      if (subtitle) subtitle.innerText = `Analyzed Period: ${activeAiPeriodText} (${data.symbol})`;

      const winRateEl = document.getElementById('aiWinRateVal');
      if (winRateEl) {
        winRateEl.innerText = `${data.win_rate}%`;
        winRateEl.style.color = data.win_rate >= 60 ? 'var(--color-green)' : (data.win_rate >= 40 ? '#fbbf24' : '#ef4444');
      }

      const winCountSub = document.getElementById('aiWinCountSub');
      if (winCountSub) winCountSub.innerText = `${data.win_count} Target Hits vs ${data.loss_count} Stop Loss`;

      const profitFactorVal = document.getElementById('aiProfitFactorVal');
      if (profitFactorVal) profitFactorVal.innerText = `${data.profit_factor}x`;

      const profitFactorCard = profitFactorVal ? profitFactorVal.closest('.dash-card') : null;
      if (profitFactorCard) {
        const sub = profitFactorCard.querySelector('.dash-card-sub');
        if (sub) sub.innerText = `Avg Gain: +${data.avg_gain}% | Avg Loss: -${data.avg_loss}%`;
      }

      const scoreMarkVal = document.getElementById('aiScoreMarkVal');
      if (scoreMarkVal) scoreMarkVal.innerText = `${data.bot_score} / 100`;

      const scoreMarkCard = scoreMarkVal ? scoreMarkVal.closest('.dash-card') : null;
      if (scoreMarkCard) {
        const sub = scoreMarkCard.querySelector('.dash-card-sub');
        if (sub) sub.innerText = `Grade ${data.bot_grade} • Traps Filtered: ${traps.length} Avoided`;
      }

      // Update Avoided Traps List (Why we didn't trade)
      const avoidedList = document.getElementById('aiAvoidedReasonsList');
      if (avoidedList) {
        if (traps.length > 0) {
          avoidedList.innerHTML = traps.map(trap => `
            <li><b>${trap.title}:</b> ${trap.reason}</li>
          `).join('');
        } else {
          avoidedList.innerHTML = `<li>উক্ত পিরিয়ডে কোনো ঝুঁকিপূর্ণ লো-ভলিউম ট্র্যাপ বা ওভারবট কন্ডিশন তৈরি হয়নি।</li>`;
        }
      }

      // Update Teacher Evaluation Commentary
      const teacherEl = document.getElementById('aiTeacherComments');
      if (teacherEl && data.teacher_comments) {
        teacherEl.innerText = data.teacher_comments;
      }

      // Update Teacher Bar Metric
      const barFill = document.querySelector('.ai-teacher-card .ai-bar-metric div[style*="width"]');
      const barPct = document.querySelector('.ai-teacher-card .ai-bar-metric span:last-child');
      if (barFill) barFill.style.width = `${data.bot_score}%`;
      if (barPct) barPct.innerText = `${data.bot_score}%`;

    } catch (err) {
      console.error('Failed to load AI audit report:', err);
      container.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #ef4444;">
          <div style="font-size: 20px; margin-bottom: 6px;">⚠️</div>
          <div>Failed to audit stock data: ${err.message}</div>
        </div>
      `;
    }
  }

  if (runBtn && symInput) {
    runBtn.addEventListener('click', () => {
      const sym = symInput.value.trim().toUpperCase() || 'FEKDIL';
      runBtn.innerHTML = '<span>⏳ Scanning Data...</span>';
      renderAiReport(sym).finally(() => {
        runBtn.innerHTML = '<span>🔍 Scan & Audit Trades</span>';
      });
    });

    symInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') runBtn.click();
    });
  }

  // Initial render preview with real backend data
  renderAiReport('FEKDIL');
}

