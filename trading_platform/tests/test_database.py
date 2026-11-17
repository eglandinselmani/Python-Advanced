"""Watchlist + database persistence tests (including a simulated server restart)."""
import tempfile

from tests.conftest import build_client, register_and_login
from backend.main import app


def test_tables_exist(client):
    from backend.database import Base
    assert {"users", "watchlist_items", "portfolios", "orders", "transactions", "positions", "alerts",
            "user_settings"} <= set(Base.metadata.tables)


def test_default_watchlist_has_eight_assets(client, auth):
    w = client.get("/api/watchlist", headers=auth).json()
    assert [x["symbol"] for x in w] == ["BTC/USD", "ETH/USD", "SOL/USD", "AAPL", "TSLA", "NVDA", "EUR/USD", "XAU/USD"]
    assert all(x["price"] > 0 and "change_pct" in x and x["source"] for x in w)


def test_watchlist_add_remove_favorite(client, auth):
    assert client.post("/api/watchlist", json={"symbol": "msft"}, headers=auth).status_code == 201
    assert client.post("/api/watchlist", json={"symbol": "MSFT"}, headers=auth).status_code == 409
    assert client.post("/api/watchlist", json={"symbol": "NOPE"}, headers=auth).status_code == 404
    assert "MSFT" in [x["symbol"] for x in client.get("/api/watchlist", headers=auth).json()]
    assert client.put("/api/watchlist/BTC-USD/favorite", headers=auth).json()["favorite"] is True
    assert client.delete("/api/watchlist/BTC-USD", headers=auth).status_code == 204
    assert client.delete("/api/watchlist/BTC/USD", headers=auth).status_code == 404   # already removed
    assert "BTC/USD" not in [x["symbol"] for x in client.get("/api/watchlist", headers=auth).json()]


def test_watchlists_are_per_user(client):
    a, b = register_and_login(client, "alice"), register_and_login(client, "bob")
    client.delete("/api/watchlist/AAPL", headers=a)
    assert "AAPL" not in [x["symbol"] for x in client.get("/api/watchlist", headers=a).json()]
    assert "AAPL" in [x["symbol"] for x in client.get("/api/watchlist", headers=b).json()]


def test_full_integration_flow_with_restart():
    """register -> login -> watchlist -> buy -> portfolio -> sell -> history -> RESTART -> verify."""
    with tempfile.TemporaryDirectory() as d:
        url = f"sqlite:///{d}/persist.db"
        c, _, engine = build_client(url)
        h = register_and_login(c, "carol")
        assert c.post("/api/watchlist", json={"symbol": "AMD"}, headers=h).status_code == 201
        assert c.post("/api/trading/buy", json={"symbol": "NVDA", "quantity": 10}, headers=h).status_code == 201
        p = c.get("/api/portfolio", headers=h).json()
        assert p["positions"][0]["symbol"] == "NVDA" and p["balance"] < 100_000
        assert c.post("/api/trading/sell", json={"symbol": "NVDA", "quantity": 4}, headers=h).status_code == 201
        assert len(c.get("/api/trading/history", headers=h).json()) == 2
        c.put("/api/users/me/settings", json={"theme": "light"}, headers=h)
        c.post("/api/alerts", json={"symbol": "TSLA", "target_price": 9999, "condition": "above"}, headers=h)
        balance_before = c.get("/api/portfolio/balance", headers=h).json()["balance"]
        engine.dispose()
        app.dependency_overrides.clear()

        # ---- "restart": brand-new engine + session factory on the same file
        c2, _, engine2 = build_client(url)
        try:
            t = c2.post("/api/auth/login", json={"username": "carol", "password": "Passw0rd123"})
            assert t.status_code == 200
            h2 = {"Authorization": f"Bearer {t.json()['access_token']}"}
            assert c2.get("/api/auth/me", headers=h).status_code == 200           # old JWT still valid
            assert c2.get("/api/portfolio/balance", headers=h2).json()["balance"] == balance_before
            pos = c2.get("/api/trading/positions", headers=h2).json()
            assert pos[0]["symbol"] == "NVDA" and pos[0]["quantity"] == 6
            assert len(c2.get("/api/trading/history", headers=h2).json()) == 2
            assert "AMD" in [x["symbol"] for x in c2.get("/api/watchlist", headers=h2).json()]
            assert c2.get("/api/users/me/settings", headers=h2).json()["theme"] == "light"
            assert len(c2.get("/api/alerts", headers=h2).json()) == 1
        finally:
            engine2.dispose()
            app.dependency_overrides.clear()
