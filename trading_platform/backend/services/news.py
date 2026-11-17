"""News feed: real RSS headlines when reachable, otherwise clearly-labelled SAMPLE items."""
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

from backend.config import settings

FEEDS = {
    "crypto": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "stocks": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL,TSLA,NVDA&region=US&lang=en-US",
    "markets": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US",
}
_SAMPLE = [
    ("crypto", "Bitcoin consolidates as traders weigh ETF flows", "Sample article: spot ETF inflows slow while volatility stays subdued."),
    ("crypto", "Ethereum developers schedule next network upgrade test", "Sample article: testnet rollout planned ahead of mainnet activation."),
    ("crypto", "Solana network activity reaches new monthly high", "Sample article: transaction counts rise as DeFi usage grows."),
    ("stocks", "Chipmakers lead tech rally on strong AI demand", "Sample article: semiconductor stocks outperform the broader index."),
    ("stocks", "Apple supplier data points to steady device shipments", "Sample article: component orders suggest stable quarterly volumes."),
    ("stocks", "Electric-vehicle makers face margin pressure", "Sample article: price competition weighs on profitability."),
    ("markets", "Central bank signals cautious approach to rate cuts", "Sample article: policymakers want more evidence inflation is cooling."),
    ("markets", "Gold steadies near record levels as dollar softens", "Sample article: safe-haven demand supports precious metals."),
    ("markets", "Oil edges lower on rising inventories", "Sample article: crude stockpiles rose more than analysts expected."),
    ("markets", "Euro holds gains ahead of inflation data", "Sample article: traders await the next eurozone CPI release."),
]
_cache: dict = {}


def _fetch(category: str) -> list[dict]:
    r = requests.get(FEEDS[category], timeout=4, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    items = []
    for it in ET.fromstring(r.content).iter("item"):
        items.append({"title": (it.findtext("title") or "").strip(), "summary": (it.findtext("description") or "").strip()[:240],
                      "url": it.findtext("link"), "published": it.findtext("pubDate"),
                      "category": category, "source": "live"})
        if len(items) >= 10:
            break
    return items


def get_news(category: str | None = None) -> dict:
    cats = [category] if category in FEEDS else list(FEEDS)
    items: list[dict] = []
    if settings.MARKET_DATA_MODE != "simulated":
        for c in cats:
            hit = _cache.get(c)
            if hit and time.time() - hit[0] < 300:
                items += hit[1]
                continue
            try:
                got = _fetch(c)
                _cache[c] = (time.time(), got)
                items += got
            except Exception:
                pass
    if not items:
        now = datetime.now(timezone.utc)
        items = [{"title": t, "summary": s, "url": None, "published": (now - timedelta(hours=i * 3)).isoformat(),
                  "category": c, "source": "sample"} for i, (c, t, s) in enumerate(_SAMPLE) if c in cats]
    return {"items": items, "source": items[0]["source"],
            "notice": None if items[0]["source"] == "live" else
            "SAMPLE DEMONSTRATION CONTENT – these are not real news articles."}


def economic_calendar() -> dict:
    """Static sample calendar (no free keyless real-time API is used)."""
    today = datetime.now(timezone.utc).date()
    rows = [("US", "Non-Farm Payrolls", "High", 1), ("EU", "CPI Flash Estimate (YoY)", "High", 2),
            ("US", "FOMC Interest Rate Decision", "High", 3), ("UK", "GDP (QoQ)", "Medium", 4),
            ("JP", "BoJ Policy Statement", "High", 5), ("US", "Initial Jobless Claims", "Medium", 6),
            ("DE", "ZEW Economic Sentiment", "Low", 7)]
    return {"source": "sample", "notice": "SAMPLE DEMONSTRATION CALENDAR – dates and events are illustrative.",
            "events": [{"date": (today + timedelta(days=d)).isoformat(), "country": c, "event": e, "impact": i}
                       for c, e, i, d in rows]}
