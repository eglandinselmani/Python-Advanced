"""Live-provider logic tested with a fake HTTP layer (no internet needed)."""
import pytest

from backend.config import settings
from backend.services import market_data as md


class FakeResp:
    def __init__(self, data):
        self._d = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


@pytest.fixture()
def live(monkeypatch):
    monkeypatch.setattr(settings, "MARKET_DATA_MODE", "auto")
    md._cache.clear()
    md._down_until.clear()
    yield
    md._cache.clear()
    md._down_until.clear()


def kline(i, o, h, l, c, v):
    t = 1_700_000_000_000 + i * 60_000
    return [t, str(o), str(h), str(l), str(c), str(v), t + 59_999, "0", 1, "0", "0", "0"]


def test_binance_history_and_quote_used_for_crypto(live, monkeypatch):
    calls = []

    def fake_get(url, params=None, **kw):
        calls.append(url)
        if url.endswith("/klines"):
            assert params["symbol"] == "BTCUSDT" and params["interval"] == "1m"
            return FakeResp([kline(i, 100 + i, 102 + i, 99 + i, 101 + i, 5) for i in range(10)])
        return FakeResp({"lastPrice": "110.5", "priceChange": "10.5", "highPrice": "120", "lowPrice": "95", "volume": "1234"})

    monkeypatch.setattr(md.requests, "get", fake_get)
    df, src = md.get_history("BTC/USD", "1m", 10)
    assert src == "live" and len(df) == 10 and df["close"].iloc[-1] == 110.0 and str(df["time"].dt.tz) == "UTC"
    q = md.get_quote("BTC/USD")
    assert q["source"] == "live" and q["price"] == 110.5 and q["prev_close"] == 100.0 and q["change_pct"] == 10.5
    assert all("binance" in c for c in calls)


def test_binance_failure_falls_back_without_killing_yahoo(live, monkeypatch):
    def fake_get(url, params=None, **kw):
        if "binance" in url:
            raise RuntimeError("blocked")
        raise RuntimeError("yahoo down too")

    monkeypatch.setattr(md.requests, "get", fake_get)
    df, src = md.get_history("BTC/USD", "5m", 50)
    assert src == "simulated" and len(df) == 50          # never presented as live
    assert not md.provider_ok("binance") and not md.provider_ok("yahoo")
    assert md.get_quote("ETH/USD")["source"] == "simulated"
    assert md.data_status()["live"] is False


def test_binance_down_still_allows_yahoo_for_stocks(live, monkeypatch):
    md._mark_down("binance")
    assert md.provider_ok("yahoo") and md.live_enabled()


def test_realtime_chart_changes_between_calls_in_simulated_mode(monkeypatch):
    """The simulator is a continuous function of time, so charts keep moving between refreshes."""
    import time
    monkeypatch.setattr(settings, "MARKET_DATA_MODE", "simulated")
    md._cache.clear()
    a = md._sim_history(md.get_asset("BTC/USD"), "1m", 5, now=time.time())
    b = md._sim_history(md.get_asset("BTC/USD"), "1m", 5, now=time.time() + 30)
    assert a["close"].iloc[-1] != b["close"].iloc[-1]
