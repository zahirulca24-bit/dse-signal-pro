from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from src.core.config import settings
from src.scanner.sector_scanner import scan_sectors
from src.scanner.sector_rotation import get_rotation
from src.scanner.stock_scanner import scan_stocks
from src.collection import csv_loader

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@router.get("/modules")
def get_modules():
    return {
        "data_collection": "active",
        "technical_analysis": "active",
        "market_scanner": "active",
        "sector_rotation": "active",
        "signal_engine": "active",
        "ai_prediction": "planned"
    }

# --- Quantitative Scanner & Rotation APIs ---

@router.get("/sectors/scan")
def get_sector_scan():
    try:
        sectors = scan_sectors(save_csv=False)
        return {
            "status": "success",
            "total_sectors": len(sectors),
            "sectors": sectors
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/sectors/rotation")
def get_sector_rotation():
    try:
        rotation = get_rotation(save_csv=False)
        return {
            "status": "success",
            "total_sectors": len(rotation),
            "sectors": rotation
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/stocks/scan")
def stock_scanner_api(limit: Optional[int] = Query(None, description="Limit number of stocks returned (default: all)")):
    try:
        stocks = scan_stocks(save_csv=False)
        total = len(stocks)
        if limit is not None and limit > 0:
            stocks = stocks[:limit]
        return {
            "status": "success",
            "total_stocks": total,
            "count": len(stocks),
            "stocks": stocks
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

# --- Core Market & Frontend Endpoints ---

@router.get("/market-summary")
def get_market_summary():
    return csv_loader.market_stats

@router.get("/top-movers")
def get_top_movers():
    return {
        "gainers": csv_loader.top_gainers,
        "losers": csv_loader.top_losers,
        "most_active": csv_loader.top_volume
    }

@router.get("/sectors-summary")
def get_sectors_summary():
    return csv_loader.sectors_summary

@router.get("/screener")
def get_screener():
    return csv_loader.screener_data

@router.get("/favorites")
def get_favorites():
    fav_data = [s for s in csv_loader.summary_list if s['symbol'] in csv_loader.FAVORITES_LIST]
    fav_data.sort(key=lambda x: csv_loader.FAVORITES_LIST.index(x['symbol']) if x['symbol'] in csv_loader.FAVORITES_LIST else 99)
    return fav_data

@router.get("/symbols")
def get_symbols():
    return csv_loader.summary_list

@router.get("/history")
def get_stock_history(symbol: str = Query("SQURPHARMA", description="Stock symbol code")):
    res = csv_loader.get_history(symbol)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    return res

@router.get("/analyst/verdicts")
def get_all_analyst_verdicts():
    results = csv_loader.screener_data.get('results', [])
    grouped = {
        "BUY_SETUP": [r for r in results if r.get('verdict') == 'BUY SETUP'],
        "WAIT": [r for r in results if r.get('verdict') == 'WAIT'],
        "AVOID": [r for r in results if r.get('verdict') == 'AVOID'],
        "EXIT_SELL": [r for r in results if r.get('verdict') == 'EXIT / SELL']
    }
    return {
        "status": "success",
        "counts": {k: len(v) for k, v in grouped.items()},
        "verdicts": grouped
    }

@router.get("/analyst/{symbol}")
def get_analyst_decision(symbol: str):
    sym = symbol.strip().upper()
    results = csv_loader.screener_data.get('results', [])
    for item in results:
        if item.get('symbol') == sym:
            return {
                "status": "success",
                "symbol": sym,
                "category": item.get('category'),
                "verdict": item.get('verdict'),
                "sub_type": item.get('sub_type'),
                "rationale_bn": item.get('rationale_bn'),
                "rationale_en": item.get('rationale_en'),
                "trade_plan": item.get('trade_plan'),
                "pillars": item.get('pillars')
            }
    raise HTTPException(status_code=404, detail=f"Analysis for symbol '{sym}' not found")

@router.get("/ai/audit")
def get_ai_stock_audit(
    symbol: str = Query("FEKDIL", description="Stock symbol"),
    period: str = Query("6M", description="Period: 3M, 6M, 1Y, ALL"),
    strategy: str = Query("ALL", description="Strategy filter: ALL, BREAKOUT, VOLUME, EMA_ALIGN")
):
    try:
        from src.prediction.stock_auditor import audit_stock_history
        res = audit_stock_history(symbol=symbol, period=period, strategy_filter=strategy)
        if res.get("status") == "error":
            raise HTTPException(status_code=404, detail=res.get("message", "Symbol audit failed"))
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/model-status")
def get_ai_model_status():
    """Returns Walk-Forward incremental training status and validation scorecard."""
    try:
        from src.prediction.train import get_model_status
        return get_model_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



