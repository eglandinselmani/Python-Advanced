"""Market data service.

Two providers:
  * LIVE      – Yahoo Finance public chart endpoint (used when reachable, MARKET_DATA_MODE=auto)
  * SIMULATED – deterministic synthetic prices, used when the internet is unavailable.

Every quote / candle series carries a `source` field ("live" | "simulated") so that
simulated prices are NEVER presented as real market data.
"""
from __future__ import annotations

import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock

import numpy as np
import pandas as pd
import requests

from backend.config import settings


@dataclass(frozen=True)
class Asset:
    symbol: str
    name: str
    category: str          # crypto | stocks | forex | commodities | indices
    base_price: float      # reference level for the simulator
    yahoo: str
    daily_vol: float       # typical daily volatility (simulator)
    base_volume: float     # typical daily volume (simulator)
    market_cap: float | None
    description: str


def _a(*args):
    return Asset(*args)


CATALOG: list[Asset] = [
    # --- Crypto
    _a("BTC/USD", "Bitcoin", "crypto", 95000, "BTC-USD", 0.025, 3.5e4, 1.9e12,
       "Bitcoin is the first decentralised cryptocurrency, created in 2009. It runs on a proof-of-work blockchain with a fixed supply of 21 million coins."),
    _a("ETH/USD", "Ethereum", "crypto", 3300, "ETH-USD", 0.03, 4.0e5, 4.0e11,
       "Ethereum is a programmable blockchain that supports smart contracts and decentralised applications. Its native currency is ether (ETH)."),
    _a("SOL/USD", "Solana", "crypto", 180, "SOL-USD", 0.045, 6.0e6, 8.5e10,
       "Solana is a high-throughput proof-of-stake blockchain designed for fast, low-cost decentralised applications."),
    _a("BNB/USD", "BNB", "crypto", 620, "BNB-USD", 0.03, 1.5e6, 9.0e10,
       "BNB is the native token of the BNB Chain ecosystem, originally launched by the Binance exchange."),
    _a("XRP/USD", "XRP", "crypto", 2.3, "XRP-USD", 0.04, 9.0e8, 1.3e11,
       "XRP is the token of the XRP Ledger, designed for fast, low-cost international payments."),
    _a("ADA/USD", "Cardano", "crypto", 0.9, "ADA-USD", 0.04, 4.0e8, 3.2e10,
       "Cardano is a proof-of-stake blockchain platform developed with a research-driven approach."),
    _a("DOGE/USD", "Dogecoin", "crypto", 0.35, "DOGE-USD", 0.05, 3.0e9, 5.0e10,
       "Dogecoin began in 2013 as a joke cryptocurrency based on a popular meme and grew into a widely traded coin."),
    # --- Stocks
    _a("AAPL", "Apple Inc.", "stocks", 230, "AAPL", 0.015, 5.5e7, 3.5e12,
       "Apple designs consumer electronics, software and services, including the iPhone, Mac, iPad and Apple Watch."),
    _a("TSLA", "Tesla, Inc.", "stocks", 350, "TSLA", 0.035, 9.0e7, 1.1e12,
       "Tesla designs and manufactures electric vehicles, battery energy storage and solar products."),
    _a("NVDA", "NVIDIA Corp.", "stocks", 140, "NVDA", 0.03, 3.0e8, 3.4e12,
       "NVIDIA designs GPUs and AI computing platforms used in gaming, data centres and autonomous vehicles."),
    _a("MSFT", "Microsoft Corp.", "stocks", 430, "MSFT", 0.012, 2.2e7, 3.2e12,
       "Microsoft develops software (Windows, Office), cloud services (Azure) and gaming (Xbox)."),
    _a("AMZN", "Amazon.com Inc.", "stocks", 200, "AMZN", 0.018, 4.0e7, 2.1e12,
       "Amazon operates the world's largest online marketplace and the AWS cloud computing platform."),
    _a("GOOGL", "Alphabet Inc.", "stocks", 175, "GOOGL", 0.016, 2.5e7, 2.1e12,
       "Alphabet is the parent company of Google, owning Search, YouTube, Android and Google Cloud."),
    _a("META", "Meta Platforms", "stocks", 580, "META", 0.02, 1.4e7, 1.5e12,
       "Meta owns Facebook, Instagram and WhatsApp and invests in virtual and augmented reality."),
    _a("AMD", "Advanced Micro Devices", "stocks", 150, "AMD", 0.028, 5.0e7, 2.4e11,
       "AMD designs CPUs, GPUs and adaptive chips for PCs, servers and game consoles."),
    _a("NFLX", "Netflix, Inc.", "stocks", 700, "NFLX", 0.02, 3.5e6, 3.0e11,
       "Netflix is a global streaming service producing and distributing films and series."),
    _a("JPM", "JPMorgan Chase", "stocks", 240, "JPM", 0.013, 9.0e6, 6.8e11,
       "JPMorgan Chase is the largest US bank, active in investment banking, retail banking and asset management."),
    # --- Forex
    _a("EUR/USD", "Euro / US Dollar", "forex", 1.08, "EURUSD=X", 0.005, 1.0e9, None,
       "The most traded currency pair in the world: how many US dollars one euro buys."),
    _a("GBP/USD", "British Pound / US Dollar", "forex", 1.27, "GBPUSD=X", 0.006, 7.0e8, None,
       "Known as 'Cable', this pair shows how many US dollars one pound sterling buys."),
    _a("USD/JPY", "US Dollar / Japanese Yen", "forex", 150, "JPY=X", 0.006, 8.0e8, None,
       "How many Japanese yen one US dollar buys; heavily influenced by interest-rate differences."),
    _a("USD/CHF", "US Dollar / Swiss Franc", "forex", 0.88, "CHF=X", 0.005, 3.0e8, None,
       "How many Swiss francs one US dollar buys; the franc is a traditional safe-haven currency."),
    _a("AUD/USD", "Australian Dollar / US Dollar", "forex", 0.66, "AUDUSD=X", 0.006, 4.0e8, None,
       "A commodity-linked pair that often follows metals prices and risk appetite."),
    # --- Commodities
    _a("XAU/USD", "Gold", "commodities", 2650, "GC=F", 0.01, 2.0e5, None,
       "Gold is a precious metal used as a store of value and a classic safe-haven asset."),
    _a("XAG/USD", "Silver", "commodities", 31, "SI=F", 0.018, 8.0e4, None,
       "Silver is both a precious metal and an industrial metal used in electronics and solar panels."),
    _a("WTI", "Crude Oil WTI", "commodities", 70, "CL=F", 0.02, 3.0e5, None,
       "West Texas Intermediate is the main US crude oil benchmark."),
    _a("BRENT", "Brent Crude Oil", "commodities", 74, "BZ=F", 0.02, 2.0e5, None,
       "Brent is the international benchmark for crude oil prices, extracted from the North Sea."),
    _a("NG", "Natural Gas", "commodities", 2.9, "NG=F", 0.035, 2.0e5, None,
       "Natural gas futures track the price of gas used for heating and electricity generation."),
    _a("HG", "Copper", "commodities", 4.2, "HG=F", 0.015, 7.0e4, None,
       "Copper is an industrial metal often seen as a barometer of global economic health."),
    # --- Indices
    _a("SPX", "S&P 500", "indices", 5900, "^GSPC", 0.009, 3.5e9, None,
       "The S&P 500 tracks 500 of the largest US listed companies."),
    _a("NDX", "Nasdaq 100", "indices", 20500, "^NDX", 0.012, 5.0e8, None,
       "The Nasdaq-100 tracks the 100 largest non-financial companies on the Nasdaq exchange."),
    _a("DJI", "Dow Jones Industrial", "indices", 43000, "^DJI", 0.008, 3.0e8, None,
       "The Dow Jones Industrial Average tracks 30 large US blue-chip companies."),
    _a("DAX", "DAX 40", "indices", 19500, "^GDAXI", 0.009, 8.0e7, None,
       "The DAX tracks the 40 largest German companies listed in Frankfurt."),
    _a("FTSE", "FTSE 100", "indices", 8200, "^FTSE", 0.007, 6.0e8, None,
       "The FTSE 100 tracks the 100 largest companies listed on the London Stock Exchange."),
    _a("N225", "Nikkei 225", "indices", 39000, "^N225", 0.011, 1.2e8, None,
       "The Nikkei 225 tracks 225 large companies on the Tokyo Stock Exchange."),
]
ASSETS: dict[str, Asset] = {a.symbol: a for a in CATALOG}
CATEGORIES = ["crypto", "stocks", "forex", "commodities", "indices"]

TIMEFRAMES: dict[str, int] = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600,
    "4h": 14400, "1d": 86400, "1w": 604800, "1M": 2592000,
}


class UnknownSymbol(KeyError):
    pass


def normalize_symbol(raw: str) -> str:
    """Accept 'btc-usd', 'BTC/USD', 'BTCUSD' ... and return the canonical symbol."""
    s = raw.strip().upper().replace("-", "/").replace("_", "/")
    if s in ASSETS:
        return s
    flat = s.replace("/", "")
    for sym in ASSETS:
        if sym.replace("/", "") == flat:
            return sym
    raise UnknownSymbol(raw)


def get_asset(raw: str) -> Asset:
    return ASSETS[normalize_symbol(raw)]


def search_assets(q: str, category: str | None = None) -> list[Asset]:
    q = q.strip().lower()
    out = []
    for a in CATALOG:
        if category and a.category != category:
            continue
        if not q or q in a.symbol.lower() or q in a.name.lower():
            out.append(a)
    return out


# ----------------------------------------------------------------------------- simulator
_PERIODS = np.array([1.1e8, 3e7, 8e6, 2e6, 6e5, 2e5, 8e4, 2.7e4, 9e3, 3e3, 1.1e3, 400, 130, 47, 19], dtype=float)
_sim_params: dict[str, tuple[np.ndarray, np.ndarray]] = {}


def _params(asset: Asset):
    if asset.symbol not in _sim_params:
        rng = np.random.default_rng(zlib.crc32(asset.symbol.encode()))
        phases = rng.uniform(0, 2 * np.pi, len(_PERIODS))
        amp = 0.5 * asset.daily_vol * np.maximum(np.sqrt(_PERIODS / 86400), 0.04)
        amp = np.minimum(amp, 0.12)
        _sim_params[asset.symbol] = (phases, amp)
    return _sim_params[asset.symbol]


def _sim_price(asset: Asset, t: np.ndarray) -> np.ndarray:
    """Continuous deterministic price path as a function of epoch seconds."""
    phases, amp = _params(asset)
    t = np.asarray(t, dtype=float)
    ang = 2 * np.pi * t[..., None] / _PERIODS + phases
    return asset.base_price * np.exp((amp * np.sin(ang)).sum(axis=-1))


def _decimals(price: float) -> int:
    return 2 if price >= 100 else 3 if price >= 10 else 4 if price >= 1 else 5


def _sim_history(asset: Asset, timeframe: str, limit: int, now: float | None = None) -> pd.DataFrame:
    step = TIMEFRAMES[timeframe]
    now = now or time.time()
    last_start = (int(now) // step) * step
    starts = last_start - step * np.arange(limit - 1, -1, -1)
    m = 24 if step >= 3600 else 12
    frac = np.arange(0, m + 1) / m
    samples = starts[:, None] + step * frac[None, :]
    # the still-forming bar only extends to "now"
    samples = np.minimum(samples, now)
    prices = _sim_price(asset, samples)
    o, c = prices[:, 0], prices[:, -1]
    h, lo = prices.max(axis=1), prices.min(axis=1)
    # volume: activity grows with bar range, deterministic pseudo-random noise per bar
    idx = starts // step
    noise = np.abs(np.sin(idx * 12.9898 + zlib.crc32(asset.symbol.encode()) % 1000) * 43758.5453) % 1
    rng_pct = (h - lo) / o
    per_bar = asset.base_volume * step / 86400
    vol = per_bar * (0.5 + noise) * (1 + 20 * rng_pct / max(asset.daily_vol, 1e-6) * 0.1)
    d = _decimals(asset.base_price)
    df = pd.DataFrame({
        "time": pd.to_datetime(starts, unit="s", utc=True),
        "open": o.round(d), "high": h.round(d), "low": lo.round(d), "close": c.round(d),
        "volume": vol.round(2),
    })
    return df


# ----------------------------------------------------------------------------- live provider
_YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
_YAHOO_PARAMS = {  # timeframe -> (interval, range, resample rule)
    "1m": ("1m", "1d", None), "5m": ("5m", "5d", None), "15m": ("15m", "1mo", None),
    "30m": ("30m", "1mo", None), "1h": ("60m", "6mo", None), "4h": ("60m", "6mo", "4h"),
    "1d": ("1d", "5y", None), "1w": ("1wk", "10y", None), "1M": ("1mo", "max", None),
}
_down_until: dict[str, float] = {}   # provider name -> retry timestamp
_lock = Lock()
_cache: dict[tuple, tuple[float, object]] = {}


def _cached(key, ttl, fn):
    now = time.time()
    with _lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
    val = fn()
    with _lock:
        _cache[key] = (now, val)
    return val


def provider_ok(name: str) -> bool:
    return settings.MARKET_DATA_MODE != "simulated" and time.time() >= _down_until.get(name, 0.0)


def live_enabled() -> bool:
    """True while at least one live provider is believed to be reachable."""
    return provider_ok("yahoo") or provider_ok("binance")


def _mark_down(name: str):
    _down_until[name] = time.time() + 120  # retry that provider after 2 minutes


# ----------------------------------------------------------------------------- Binance (crypto, real time, no API key)
BINANCE = {"BTC/USD": "BTCUSDT", "ETH/USD": "ETHUSDT", "SOL/USD": "SOLUSDT", "BNB/USD": "BNBUSDT",
           "XRP/USD": "XRPUSDT", "ADA/USD": "ADAUSDT", "DOGE/USD": "DOGEUSDT"}
_BINANCE_HOSTS = ["https://data-api.binance.vision", "https://api.binance.com"]


def _binance_get(path: str, params: dict):
    last = None
    for host in _BINANCE_HOSTS:
        try:
            r = requests.get(host + path, params=params, timeout=4)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # try the next mirror
            last = e
    raise last


def _binance_history(asset: Asset, timeframe: str, limit: int) -> pd.DataFrame:
    rows = _binance_get("/api/v3/klines", {"symbol": BINANCE[asset.symbol], "interval": timeframe, "limit": limit})
    df = pd.DataFrame(rows).iloc[:, :6]
    df.columns = ["time", "open", "high", "low", "close", "volume"]
    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df


def _binance_quote(asset: Asset) -> dict:
    t = _binance_get("/api/v3/ticker/24hr", {"symbol": BINANCE[asset.symbol]})
    return {"price": float(t["lastPrice"]), "prev_close": float(t["lastPrice"]) - float(t["priceChange"]),
            "high": float(t["highPrice"]), "low": float(t["lowPrice"]), "volume": float(t["volume"]), "source": "live"}


def _yahoo_fetch(asset: Asset, interval: str, rng: str):
    r = requests.get(_YAHOO.format(sym=asset.yahoo), params={"interval": interval, "range": rng},
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    ts = res.get("timestamp") or []
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({"time": pd.to_datetime(ts, unit="s", utc=True), "open": q["open"], "high": q["high"],
                       "low": q["low"], "close": q["close"], "volume": q["volume"]}).dropna(subset=["close"])
    df["volume"] = df["volume"].fillna(0)
    return df, res.get("meta", {})


def _live_history(asset: Asset, timeframe: str) -> pd.DataFrame:
    interval, rng, resample = _YAHOO_PARAMS[timeframe]
    df, _ = _yahoo_fetch(asset, interval, rng)
    if resample:
        df = (df.set_index("time").resample(resample)
              .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
              .dropna().reset_index())
    return df


# ----------------------------------------------------------------------------- public API
def get_history(symbol: str, timeframe: str, limit: int = 300) -> tuple[pd.DataFrame, str]:
    """Return (candles DataFrame, source)."""
    asset = get_asset(symbol)
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"Unknown timeframe '{timeframe}'")
    limit = max(5, min(limit, 1000))
    if asset.symbol in BINANCE and provider_ok("binance"):
        try:
            df = _cached(("bhist", asset.symbol, timeframe, limit), 1.0, lambda: _binance_history(asset, timeframe, limit))
            if len(df) >= 5:
                return df, "live"
        except Exception:
            _mark_down("binance")
    if provider_ok("yahoo"):
        try:
            df = _cached(("hist", asset.symbol, timeframe), 10, lambda: _live_history(asset, timeframe))
            if len(df) >= 5:
                return df.tail(limit).reset_index(drop=True), "live"
        except Exception:
            _mark_down("yahoo")
    return _sim_history(asset, timeframe, limit), "simulated"


def _sim_quote(asset: Asset) -> dict:
    now = time.time()
    price = float(_sim_price(asset, np.array([now]))[0])
    day = _sim_history(asset, "1h", 25, now)
    prev_close = float(_sim_price(asset, np.array([now - 86400]))[0])
    last24 = day.tail(24)
    high = max(float(last24["high"].max()), price)
    low = min(float(last24["low"].min()), price)
    return {"price": price, "prev_close": prev_close, "high": high, "low": low,
            "volume": float(last24["volume"].sum()), "source": "simulated"}


def _live_quote(asset: Asset) -> dict:
    df, meta = _yahoo_fetch(asset, "1d", "5d")
    price = float(meta.get("regularMarketPrice") or df["close"].iloc[-1])
    prev = float(meta.get("chartPreviousClose") or df["close"].iloc[-2] if len(df) > 1 else price)
    return {"price": price, "prev_close": prev,
            "high": float(meta.get("regularMarketDayHigh") or df["high"].iloc[-1]),
            "low": float(meta.get("regularMarketDayLow") or df["low"].iloc[-1]),
            "volume": float(meta.get("regularMarketVolume") or df["volume"].iloc[-1]), "source": "live"}


def get_quote(symbol: str) -> dict:
    asset = get_asset(symbol)
    raw = None
    if asset.symbol in BINANCE and provider_ok("binance"):
        try:
            raw = _cached(("bquote", asset.symbol), 1.0, lambda: _binance_quote(asset))
        except Exception:
            _mark_down("binance")
    if raw is None and provider_ok("yahoo"):
        try:
            raw = _cached(("quote", asset.symbol), 10, lambda: _live_quote(asset))
        except Exception:
            _mark_down("yahoo")
    if raw is None:
        raw = _cached(("squote", asset.symbol), 1.0, lambda: _sim_quote(asset))
    d = _decimals(asset.base_price)
    price = round(raw["price"], d)
    prev = raw["prev_close"]
    change = price - prev
    return {
        "symbol": asset.symbol, "name": asset.name, "category": asset.category,
        "price": price, "prev_close": round(prev, d), "change": round(change, d),
        "change_pct": round(change / prev * 100, 3) if prev else 0.0,
        "high": round(raw["high"], d), "low": round(raw["low"], d),
        "volume": round(raw["volume"], 2),
        "market_cap": asset.market_cap, "source": raw["source"],
    }


def get_quotes(symbols: list[str] | None = None) -> list[dict]:
    syms = symbols or [a.symbol for a in CATALOG]
    if live_enabled() and len(syms) > 3:  # parallel fetch when talking to live APIs
        with ThreadPoolExecutor(max_workers=8) as ex:
            return list(ex.map(get_quote, syms))
    return [get_quote(s) for s in syms]


def get_performance(symbol: str) -> dict[str, float | None]:
    """Percentage performance over several look-back windows (from daily candles)."""
    df, _ = get_history(symbol, "1d", 400)
    close = df["close"].reset_index(drop=True)
    last = float(close.iloc[-1])
    out: dict[str, float | None] = {}
    for label, n in [("1W", 5), ("1M", 21), ("3M", 63), ("6M", 126), ("1Y", 252)]:
        if len(close) > n:
            ref = float(close.iloc[-1 - n])
            out[label] = round((last / ref - 1) * 100, 2)
        else:
            out[label] = None
    return out


def data_status() -> dict:
    live = False
    if settings.MARKET_DATA_MODE != "simulated":
        for sym in ("BTC/USD", "AAPL"):          # probe one asset per provider (cached)
            try:
                live = get_quote(sym)["source"] == "live" or live
            except Exception:
                pass
    return {
        "mode": settings.MARKET_DATA_MODE, "live": live, "source": "live" if live else "simulated",
        "providers": {"crypto": "Binance (real time)" if provider_ok("binance") else "unavailable",
                      "other": "Yahoo Finance (may be delayed)" if provider_ok("yahoo") else "unavailable"},
        "message": ("Live prices: crypto from Binance (real time), other assets from Yahoo Finance (may be delayed)." if live else
                    "SIMULATED DEMONSTRATION DATA – prices are generated locally and are NOT real market prices."),
    }


def overview(category: str | None = None) -> dict:
    syms = [a.symbol for a in (search_assets("", category))]
    quotes = get_quotes(syms)
    by_change = sorted(quotes, key=lambda q: q["change_pct"], reverse=True)
    by_activity = sorted(quotes, key=lambda q: q["volume"] * q["price"], reverse=True)
    adv = sum(1 for q in quotes if q["change_pct"] > 0)
    dec = sum(1 for q in quotes if q["change_pct"] < 0)
    avg = sum(q["change_pct"] for q in quotes) / len(quotes) if quotes else 0
    return {
        "category": category or "all",
        "gainers": [q for q in by_change if q["change_pct"] > 0][:5],
        "losers": [q for q in reversed(by_change) if q["change_pct"] < 0][:5],
        "most_active": by_activity[:5],
        "stats": {"assets": len(quotes), "advancing": adv, "declining": dec,
                  "average_change_pct": round(avg, 3),
                  "best": by_change[0]["symbol"] if quotes else None,
                  "worst": by_change[-1]["symbol"] if quotes else None},
        "source": quotes[0]["source"] if quotes else "simulated",
    }
