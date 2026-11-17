import pytest

START = 100_000.0


def buy(c, h, sym="AAPL", qty=10, **kw):
    return c.post("/api/trading/buy", json={"symbol": sym, "quantity": qty, **kw}, headers=h)


def sell(c, h, sym="AAPL", qty=10, **kw):
    return c.post("/api/trading/sell", json={"symbol": sym, "quantity": qty, **kw}, headers=h)


def test_market_buy_updates_cash_and_position(client, auth):
    r = buy(client, auth, qty=10)
    assert r.status_code == 201
    o = r.json()
    assert o["status"] == "filled" and o["side"] == "buy" and o["execution_price"] > 0
    cost = o["execution_price"] * 10
    p = client.get("/api/portfolio", headers=auth).json()
    assert p["balance"] == pytest.approx(START - cost, abs=0.01)
    pos = client.get("/api/trading/positions", headers=auth).json()
    assert len(pos) == 1 and pos[0]["quantity"] == 10 and pos[0]["average_entry_price"] == pytest.approx(o["execution_price"])
    tx = client.get("/api/trading/history", headers=auth).json()
    assert tx[0]["transaction_type"] == "BUY" and tx[0]["total_value"] == pytest.approx(cost)


def test_equity_identity(client, auth):
    buy(client, auth, "BTC/USD", 0.5)
    buy(client, auth, "TSLA", 20)
    p = client.get("/api/portfolio", headers=auth).json()
    assert p["total_equity"] == pytest.approx(p["balance"] + p["positions_value"], abs=0.02)
    assert p["total_pnl"] == pytest.approx(p["realized_pnl"] + p["unrealized_pnl"], abs=0.05)
    assert p["total_equity"] == pytest.approx(START + p["total_pnl"], abs=0.01)


def test_average_entry_price_over_two_buys(client, auth, monkeypatch):
    from backend.services import market_data, trading_engine
    real = market_data.get_quote
    state = {"p": 100.0}
    monkeypatch.setattr(trading_engine.market_data, "get_quote", lambda s: {**real(s), "price": state["p"]})
    buy(client, auth, qty=10)
    state["p"] = 200.0
    buy(client, auth, qty=10)
    pos = client.get("/api/trading/positions", headers=auth).json()[0]
    assert pos["quantity"] == 20 and pos["average_entry_price"] == pytest.approx(150.0)


def test_sell_realizes_pnl_exactly(client, auth, monkeypatch):
    from backend.services import market_data, trading_engine
    real = market_data.get_quote
    state = {"p": 100.0}
    monkeypatch.setattr(trading_engine.market_data, "get_quote", lambda s: {**real(s), "price": state["p"]})
    buy(client, auth, qty=10)                 # cost 1000
    state["p"] = 120.0
    r = sell(client, auth, qty=4)             # +80 realized
    assert r.status_code == 201
    p = client.get("/api/portfolio", headers=auth).json()
    assert p["realized_pnl"] == pytest.approx(80.0)
    assert p["unrealized_pnl"] == pytest.approx(6 * 20.0)   # 6 shares left, +20 each
    assert p["balance"] == pytest.approx(START - 1000 + 480)
    tx = client.get("/api/trading/history", headers=auth).json()
    assert tx[0]["transaction_type"] == "SELL" and tx[0]["realized_pnl"] == pytest.approx(80.0)
    sell(client, auth, qty=6)                 # close fully
    assert client.get("/api/trading/positions", headers=auth).json() == []
    p = client.get("/api/portfolio", headers=auth).json()
    assert p["realized_pnl"] == pytest.approx(200.0) and p["total_equity"] == pytest.approx(START + 200.0)


def test_rejections(client, auth):
    assert buy(client, auth, qty=0).status_code == 422
    assert buy(client, auth, qty=-5).status_code == 422
    assert buy(client, auth, sym="NOPE").status_code == 404
    assert buy(client, auth, order_type="limit").status_code == 422          # missing limit price
    assert buy(client, auth, order_type="stop").status_code == 422
    r = buy(client, auth, "BTC/USD", 1000)                                    # way over $100k
    assert r.status_code == 400 and "Insufficient balance" in r.json()["detail"]
    r = sell(client, auth, qty=1)                                             # nothing owned
    assert r.status_code == 400 and "Insufficient position" in r.json()["detail"]
    buy(client, auth, qty=5)
    assert sell(client, auth, qty=6).status_code == 400
    # failed orders leave no trace
    assert len(client.get("/api/trading/orders", headers=auth).json()) == 1
    assert client.get("/api/portfolio", headers=auth).json()["balance"] < START


def test_limit_buy_stays_pending_reserves_cash_then_cancels(client, auth):
    price = client.get("/api/markets/AAPL").json()["price"]
    r = buy(client, auth, qty=10, order_type="limit", limit_price=round(price * 0.5, 2))
    o = r.json()
    assert r.status_code == 201 and o["status"] == "pending" and o["execution_price"] is None
    p = client.get("/api/portfolio", headers=auth).json()
    assert p["balance"] == START and p["reserved_balance"] == pytest.approx(10 * o["limit_price"])
    assert p["available_balance"] == pytest.approx(START - 10 * o["limit_price"])
    assert client.get("/api/trading/positions", headers=auth).json() == []
    c = client.delete(f"/api/trading/orders/{o['id']}", headers=auth)
    assert c.status_code == 200 and c.json()["status"] == "cancelled"
    assert client.delete(f"/api/trading/orders/{o['id']}", headers=auth).status_code == 400
    assert client.get("/api/portfolio", headers=auth).json()["reserved_balance"] == 0


def test_marketable_limit_fills_at_market_price(client, auth):
    price = client.get("/api/markets/AAPL").json()["price"]
    r = buy(client, auth, qty=3, order_type="limit", limit_price=round(price * 1.5, 2)).json()
    assert r["status"] == "filled" and r["execution_price"] <= r["limit_price"]


def test_pending_limit_fills_when_price_reaches_it(client, auth, monkeypatch):
    from backend.services import market_data, trading_engine
    real = market_data.get_quote
    state = {"p": 100.0}
    monkeypatch.setattr(trading_engine.market_data, "get_quote", lambda s: {**real(s), "price": state["p"]})
    o = buy(client, auth, qty=10, order_type="limit", limit_price=90.0).json()
    assert o["status"] == "pending"
    assert client.get("/api/trading/positions", headers=auth).json() == []
    state["p"] = 89.0
    orders = client.get("/api/trading/orders", headers=auth).json()   # listing triggers matching
    assert orders[0]["status"] == "filled" and orders[0]["execution_price"] == 89.0
    pos = client.get("/api/trading/positions", headers=auth).json()[0]
    assert pos["quantity"] == 10 and pos["average_entry_price"] == 89.0


def test_pending_sell_reserves_shares(client, auth):
    buy(client, auth, qty=10)
    price = client.get("/api/markets/AAPL").json()["price"]
    assert sell(client, auth, qty=8, order_type="limit", limit_price=round(price * 2, 2)).json()["status"] == "pending"
    assert sell(client, auth, qty=3).status_code == 400          # only 2 unreserved shares remain
    assert sell(client, auth, qty=2).status_code == 201


def test_cash_reservation_blocks_overspending(client, auth):
    price = client.get("/api/markets/AAPL").json()["price"]
    lim = round(price * 0.5, 2)
    assert buy(client, auth, qty=int(START / lim) - 1, order_type="limit", limit_price=lim).status_code == 201
    assert buy(client, auth, qty=int(START / price)).status_code == 400


def test_orders_filter_and_history_order(client, auth):
    buy(client, auth, qty=1)
    buy(client, auth, qty=2)
    sell(client, auth, qty=1)
    orders = client.get("/api/trading/orders", headers=auth).json()
    assert [o["id"] for o in orders] == sorted([o["id"] for o in orders], reverse=True)
    assert len(client.get("/api/trading/orders", params={"status": "filled"}, headers=auth).json()) == 3
    assert client.get("/api/trading/orders", params={"status": "x"}, headers=auth).status_code == 422
    assert len(client.get("/api/trading/history", headers=auth).json()) == 3


def test_portfolio_performance_and_reset(client, auth):
    buy(client, auth, qty=5)
    sell(client, auth, qty=5)
    perf = client.get("/api/portfolio/performance", headers=auth).json()
    assert perf["total_trades"] == 2 and perf["closed_trades"] == 1 and len(perf["equity_curve"]) >= 2
    assert client.get("/api/portfolio/balance", headers=auth).json()["total_equity"] > 0
    r = client.post("/api/portfolio/reset", headers=auth).json()
    assert r["balance"] == START and r["positions"] == [] and r["realized_pnl"] == 0
    assert client.get("/api/trading/history", headers=auth).json() == []


def test_alerts_crud_and_trigger(client, auth):
    price = client.get("/api/markets/AAPL").json()["price"]
    a = client.post("/api/alerts", json={"symbol": "aapl", "target_price": price * 0.5, "condition": "above"}, headers=auth)
    assert a.status_code == 201 and a.json()["status"] == "active"
    far = client.post("/api/alerts", json={"symbol": "AAPL", "target_price": price * 3, "condition": "above"}, headers=auth).json()
    assert client.post("/api/alerts", json={"symbol": "NOPE", "target_price": 1, "condition": "above"}, headers=auth).status_code == 404
    assert client.post("/api/alerts", json={"symbol": "AAPL", "target_price": -1, "condition": "above"}, headers=auth).status_code == 422
    assert client.post("/api/alerts", json={"symbol": "AAPL", "target_price": 1, "condition": "sideways"}, headers=auth).status_code == 422
    alerts = {x["id"]: x for x in client.get("/api/alerts", headers=auth).json()}
    assert alerts[a.json()["id"]]["status"] == "triggered" and alerts[far["id"]]["status"] == "active"
    notes = client.get("/api/alerts/notifications", headers=auth).json()
    assert any(n["kind"] == "alert" for n in notes)
    assert client.post("/api/alerts/notifications/read", headers=auth).status_code == 204
    assert all(n["is_read"] for n in client.get("/api/alerts/notifications", headers=auth).json())
    assert client.delete(f"/api/alerts/{far['id']}", headers=auth).status_code == 204
    assert client.delete(f"/api/alerts/{far['id']}", headers=auth).status_code == 404


def test_equity_curve_never_drops_when_buying(client, auth):
    """Regression: snapshots taken before the position was flushed showed equity = cash only."""
    buy(client, auth, "BTC/USD", 0.5)
    buy(client, auth, "AAPL", 50)
    sell(client, auth, "AAPL", 20)
    curve = [pt["equity"] for pt in client.get("/api/portfolio/performance", headers=auth).json()["equity_curve"]]
    assert len(curve) >= 3 and min(curve) > START * 0.98 and max(curve) < START * 1.02
