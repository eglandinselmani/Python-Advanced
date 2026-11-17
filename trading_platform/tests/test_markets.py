import math

import pandas as pd
import pytest

from backend.services import technical_analysis as ta, market_data


def test_list_and_filter(client):
    r = client.get("/api/markets")
    assert r.status_code == 200 and len(r.json()) >= 30
    assert all(q["source"] == "simulated" for q in r.json())  # simulated is always labelled
    crypto = client.get("/api/markets", params={"category": "crypto"}).json()
    assert crypto and all(q["category"] == "crypto" for q in crypto)
    assert [q["symbol"] for q in client.get("/api/markets", params={"q": "tesla"}).json()] == ["TSLA"]
    assert client.get("/api/markets", params={"category": "bogus"}).status_code == 422


def test_status_reports_simulated(client):
    s = client.get("/api/markets/status").json()
    assert s["live"] is False and "SIMULATED" in s["message"]


def test_asset_detail_and_symbol_forms(client):
    for form in ("BTC/USD", "BTC-USD", "btcusd"):
        r = client.get(f"/api/markets/{form}")
        assert r.status_code == 200 and r.json()["symbol"] == "BTC/USD"
    d = client.get("/api/markets/AAPL").json()
    assert d["description"] and set(d["performance"]) == {"1W", "1M", "3M", "6M", "1Y"}
    assert client.get("/api/markets/NOPE").status_code == 404


@pytest.mark.parametrize("tf", list(market_data.TIMEFRAMES))
def test_history_all_timeframes(client, tf):
    r = client.get("/api/markets/EUR-USD/history", params={"timeframe": tf, "limit": 120})
    assert r.status_code == 200
    c = r.json()["candles"]
    assert len(c) == 120
    for k in c:
        assert k["high"] >= max(k["open"], k["close"]) and k["low"] <= min(k["open"], k["close"])
    times = [k["time"] for k in c]
    assert times == sorted(times)


def test_history_validation(client):
    assert client.get("/api/markets/AAPL/history", params={"timeframe": "2d"}).status_code == 422
    assert client.get("/api/markets/AAPL/history", params={"limit": 5000}).status_code == 422
    assert client.get("/api/markets/NOPE/history").status_code == 404


def test_overview(client):
    o = client.get("/api/markets/overview", params={"category": "stocks"}).json()
    assert len(o["gainers"]) <= 5 and len(o["losers"]) <= 5
    gains = [q["change_pct"] for q in o["gainers"]]
    losses = [q["change_pct"] for q in o["losers"]]
    assert gains == sorted(gains, reverse=True) and losses == sorted(losses)
    assert all(q["change_pct"] > 0 for q in o["gainers"]) and all(q["change_pct"] < 0 for q in o["losers"])
    assert o["stats"]["advancing"] + o["stats"]["declining"] <= o["stats"]["assets"]


def test_news_and_calendar_are_labelled(client):
    n = client.get("/api/markets/news").json()
    assert n["source"] == "sample" and "SAMPLE" in n["notice"] and n["items"]
    assert "SAMPLE" in client.get("/api/markets/calendar").json()["notice"]


# ---------------- indicators: verified against hand calculations
def test_sma_ema_hand_values():
    s = pd.Series([1.0, 2, 3, 4, 5])
    assert ta.sma(s, 3).tolist()[2:] == [2.0, 3.0, 4.0]
    e = ta.ema(s, 3)  # alpha = 0.5, seeded with first value
    assert e.iloc[2] == pytest.approx(2.25)       # ((1*.5+2*.5)=1.5 ; 1.5*.5+3*.5)=2.25
    assert e.iloc[4] == pytest.approx(4.0625)


def test_rsi_extremes_and_range():
    up = pd.Series(range(1, 40), dtype=float)
    assert ta.rsi(up).iloc[-1] == 100.0
    assert ta.rsi(up[::-1].reset_index(drop=True)).iloc[-1] == pytest.approx(0.0, abs=1e-9)
    df, _ = market_data.get_history("AAPL", "1h", 300)
    r = ta.rsi(df["close"]).dropna()
    assert ((r >= 0) & (r <= 100)).all()


def test_rsi_wilder_reference_value():
    # Published StockCharts RSI example: first RSI(14) = 70.53 (later values checked against a naive reference)
    closes = [44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433, 46.0826,
              45.8931, 46.0328, 45.6140, 46.2820, 46.2820, 46.0328]
    r = ta.rsi(pd.Series(closes), 14)
    assert r.iloc[14] == pytest.approx(70.53, abs=0.05)
    assert r.iloc[:14].isna().all()
    # independent, loop-based Wilder reference over a longer random series
    import random
    random.seed(1)
    px = [100.0]
    for _ in range(80):
        px.append(px[-1] + random.uniform(-2, 2))
    ups = [max(b - a, 0) for a, b in zip(px, px[1:])]
    dns = [max(a - b, 0) for a, b in zip(px, px[1:])]
    ag, al = sum(ups[:14]) / 14, sum(dns[:14]) / 14
    expected = [100 - 100 / (1 + ag / al)]
    for u, d in zip(ups[14:], dns[14:]):
        ag, al = (ag * 13 + u) / 14, (al * 13 + d) / 14
        expected.append(100 - 100 / (1 + ag / al))
    got = ta.rsi(pd.Series(px), 14).dropna().tolist()
    assert got == pytest.approx(expected)


def test_bollinger_and_macd():
    df, _ = market_data.get_history("BTC/USD", "1h", 300)
    b = ta.bollinger(df["close"], 20, 2).dropna()
    assert (b["upper"] >= b["middle"]).all() and (b["middle"] >= b["lower"]).all()
    assert (b["upper"] - b["middle"]).iloc[-1] == pytest.approx(2 * df["close"].tail(20).std(ddof=0))
    m = ta.macd(df["close"]).dropna()
    assert (m["histogram"] - (m["macd"] - m["signal"])).abs().max() < 1e-9


def test_obv():
    close, vol = pd.Series([1, 2, 1.5, 1.5, 3.0]), pd.Series([10, 20, 30, 40, 50.0])
    assert ta.obv(close, vol).tolist() == [0, 20, -10, -10, 40]


def test_indicator_endpoint(client):
    r = client.get("/api/markets/AAPL/indicators", params={"timeframe": "1d", "limit": 200})
    assert r.status_code == 200
    j = r.json()
    for key in ("sma_20", "ema_50", "rsi_14", "macd", "macd_signal", "macd_histogram", "bb_upper", "bb_lower", "volume_sma", "obv"):
        assert key in j["series"] and len(j["series"][key]) == len(j["timestamps"]) == 200
    assert j["series"]["sma_20"][0] is None and j["series"]["sma_20"][-1] is not None
    assert client.get("/api/markets/AAPL/indicators", params={"indicators": "foo"}).status_code == 422
    assert client.get("/api/markets/AAPL/indicators", params={"indicators": "sma:0"}).status_code == 422
