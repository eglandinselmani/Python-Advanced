from pydantic import BaseModel


class Quote(BaseModel):
    symbol: str
    name: str
    category: str
    price: float
    prev_close: float
    change: float
    change_pct: float
    high: float
    low: float
    volume: float
    market_cap: float | None = None
    source: str  # "live" | "simulated"


class AssetDetail(Quote):
    description: str
    performance: dict[str, float | None]


class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class HistoryResponse(BaseModel):
    symbol: str
    timeframe: str
    source: str
    candles: list[Candle]


class IndicatorResponse(BaseModel):
    symbol: str
    timeframe: str
    source: str
    timestamps: list[str]
    series: dict[str, list[float | None]]
