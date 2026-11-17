from fastapi import APIRouter, HTTPException, Query

from backend.schemas.market import AssetDetail, HistoryResponse, IndicatorResponse, Quote
from backend.services import market_data, news, technical_analysis

router = APIRouter(prefix="/api/markets", tags=["Markets"])


def _asset(symbol: str):
    try:
        return market_data.get_asset(symbol)
    except market_data.UnknownSymbol:
        raise HTTPException(404, f"Unknown asset '{symbol}'")


def _history(symbol: str, timeframe: str, limit: int):
    _asset(symbol)
    try:
        return market_data.get_history(symbol, timeframe, limit)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("", response_model=list[Quote], summary="List quotes (optionally filtered)")
def list_markets(category: str | None = Query(None, pattern="^(crypto|stocks|forex|commodities|indices)$"),
                 q: str = ""):
    return market_data.get_quotes([a.symbol for a in market_data.search_assets(q, category)])


@router.get("/status", summary="Which data source is active (live vs simulated)")
def status():
    return market_data.data_status()


@router.get("/overview", summary="Top gainers / losers / most active and statistics")
def overview(category: str | None = Query(None, pattern="^(crypto|stocks|forex|commodities|indices)$")):
    return market_data.overview(category)


@router.get("/news", summary="Financial news (real RSS if reachable, otherwise labelled samples)")
def get_news(category: str | None = Query(None, pattern="^(crypto|stocks|markets)$")):
    return news.get_news(category)


@router.get("/calendar", summary="Economic calendar (sample data)")
def calendar():
    return news.economic_calendar()


@router.get("/{symbol:path}/history", response_model=HistoryResponse)
def history(symbol: str, timeframe: str = "1h", limit: int = Query(300, ge=5, le=1000)):
    df, source = _history(symbol, timeframe, limit)
    candles = [{"time": t.isoformat(), "open": float(o), "high": float(h), "low": float(lo),
                "close": float(c), "volume": float(v)}
               for t, o, h, lo, c, v in zip(df["time"], df["open"], df["high"], df["low"], df["close"], df["volume"])]
    return {"symbol": market_data.normalize_symbol(symbol), "timeframe": timeframe, "source": source, "candles": candles}


@router.get("/{symbol:path}/indicators", response_model=IndicatorResponse)
def indicators(symbol: str, timeframe: str = "1h", limit: int = Query(300, ge=5, le=1000),
               indicators: str = "sma:20,ema:50,rsi:14,macd,bb:20,vol"):
    df, source = _history(symbol, timeframe, limit)
    try:
        series = technical_analysis.compute(df, [t for t in indicators.split(",") if t.strip()])
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"symbol": market_data.normalize_symbol(symbol), "timeframe": timeframe, "source": source,
            "timestamps": [t.isoformat() for t in df["time"]], "series": series}


@router.get("/{symbol:path}", response_model=AssetDetail)
def asset_detail(symbol: str):
    a = _asset(symbol)
    return {**market_data.get_quote(a.symbol), "description": a.description,
            "performance": market_data.get_performance(a.symbol)}
