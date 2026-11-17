from tests.conftest import register_and_login


def test_register_login_me(client):
    h = register_and_login(client)
    me = client.get("/api/auth/me", headers=h)
    assert me.status_code == 200 and me.json()["username"] == "alice"
    assert "password" not in str(me.json())


def test_password_is_hashed(client):
    from backend.security.authentication import hash_password, verify_password
    h = hash_password("Secret123")
    assert h != "Secret123" and h.startswith("$2") and verify_password("Secret123", h)
    assert not verify_password("wrong", h)


def test_duplicate_username_and_email(client):
    register_and_login(client)
    r = client.post("/api/auth/register", json={"username": "ALICE", "email": "x@example.com", "password": "Passw0rd1"})
    assert r.status_code == 409
    r = client.post("/api/auth/register", json={"username": "bob", "email": "alice@example.com", "password": "Passw0rd1"})
    assert r.status_code == 409


def test_registration_validation(client):
    bad = [{"username": "ab", "email": "a@b.com", "password": "Passw0rd1"},
           {"username": "valid", "email": "not-an-email", "password": "Passw0rd1"},
           {"username": "valid", "email": "a@b.com", "password": "short1"},
           {"username": "valid", "email": "a@b.com", "password": "onlyletters"},
           {"username": "bad name!", "email": "a@b.com", "password": "Passw0rd1"}]
    for payload in bad:
        assert client.post("/api/auth/register", json=payload).status_code == 422, payload


def test_wrong_password_and_unknown_user(client):
    register_and_login(client)
    assert client.post("/api/auth/login", json={"username": "alice", "password": "Nope12345"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "ghost", "password": "Nope12345"}).status_code == 401


def test_protected_routes_require_token(client):
    for method, url in [("get", "/api/auth/me"), ("get", "/api/watchlist"), ("get", "/api/portfolio"),
                        ("get", "/api/trading/orders"), ("get", "/api/trading/positions"),
                        ("get", "/api/trading/history"), ("get", "/api/alerts"), ("get", "/api/users/me/settings")]:
        assert getattr(client, method)(url).status_code == 401, url
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_swagger_oauth_form_login(client):
    register_and_login(client)
    r = client.post("/api/auth/token", data={"username": "alice", "password": "Passw0rd123"})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"


def test_users_cannot_see_each_other(client):
    a = register_and_login(client, "alice")
    b = register_and_login(client, "bob")
    client.post("/api/trading/buy", json={"symbol": "AAPL", "quantity": 5}, headers=a)
    client.post("/api/alerts", json={"symbol": "AAPL", "target_price": 1, "condition": "above"}, headers=a)
    assert client.get("/api/trading/positions", headers=b).json() == []
    assert client.get("/api/trading/orders", headers=b).json() == []
    assert client.get("/api/alerts", headers=b).json() == []
    assert client.get("/api/portfolio", headers=b).json()["balance"] == 100000.0
    alert_id = client.get("/api/alerts", headers=a).json()[0]["id"]
    assert client.delete(f"/api/alerts/{alert_id}", headers=b).status_code == 404


def test_settings_and_password_change(client, auth):
    s = client.get("/api/users/me/settings", headers=auth).json()
    assert s["theme"] == "dark"
    r = client.put("/api/users/me/settings", json={"theme": "light", "timeframe": "4h", "default_symbol": "eth-usd"}, headers=auth)
    assert r.json()["theme"] == "light" and r.json()["default_symbol"] == "ETH/USD"
    assert client.put("/api/users/me/settings", json={"theme": "pink"}, headers=auth).status_code == 422
    assert client.post("/api/users/me/password", json={"current_password": "bad", "new_password": "NewPass123"},
                       headers=auth).status_code == 400
    assert client.post("/api/users/me/password", json={"current_password": "Passw0rd123", "new_password": "NewPass123"},
                       headers=auth).status_code == 204
    assert client.post("/api/auth/login", json={"username": "alice", "password": "NewPass123"}).status_code == 200
