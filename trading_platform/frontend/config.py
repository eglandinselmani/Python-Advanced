"""Frontend configuration: backend URL, themes and static option lists."""
import os

from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
APP_NAME = "Chartly"

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
TF_LABELS = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1H", "4h": "4H", "1d": "1D", "1w": "1W", "1M": "1M"}
CHART_TYPES = {"candles": "Candles", "line": "Line", "area": "Area"}
CATEGORIES = {"crypto": "Crypto", "stocks": "Stocks", "forex": "Forex", "commodities": "Commodities", "indices": "Indices"}

# label -> API indicator token(s)
INDICATOR_OPTIONS = {
    "Volume": "volume", "SMA 20": "sma:20", "SMA 50": "sma:50", "EMA 20": "ema:20", "EMA 50": "ema:50",
    "Bollinger Bands": "bb:20", "RSI (14)": "rsi:14", "MACD": "macd",
}

THEMES = {
    "dark": dict(bg="#131722", panel="#1e222d", panel2="#2a2e39", border="#2a2e39", text="#d1d4dc",
                 muted="#787b86", accent="#2962ff", up="#089981", down="#f23645", grid="#1f2433",
                 hover="#2a2e39", input="#1e222d", plotly="plotly_dark"),
    "light": dict(bg="#ffffff", panel="#f8f9fd", panel2="#eef0f5", border="#e0e3eb", text="#131722",
                  muted="#6a6d78", accent="#2962ff", up="#089981", down="#f23645", grid="#eef0f5",
                  hover="#eef0f5", input="#ffffff", plotly="plotly_white"),
}
