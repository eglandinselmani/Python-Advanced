"""HTTP client for the FastAPI backend. The frontend NEVER touches the database directly."""
from __future__ import annotations

from urllib.parse import quote

import requests

from frontend.config import API_URL

# Replaceable transport (tests inject FastAPI's TestClient here).
_http = requests.Session()


class APIError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.message, self.status = message, status


class BackendUnavailable(APIError):
    pass


def _sym(symbol: str) -> str:
    return quote(symbol.replace("/", "-"), safe="-")


class APIClient:
    def __init__(self, token: str | None = None, base_url: str = API_URL):
        self.token, self.base_url = token, base_url

    # ---- transport
    def _request(self, method: str, path: str, *, json=None, params=None):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            r = _http.request(method, f"{self.base_url}{path}", json=json, params=params, headers=headers, timeout=15)
        except requests.exceptions.RequestException as e:
            raise BackendUnavailable(f"Cannot reach the backend at {self.base_url}. Is it running? ({type(e).__name__})")
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except ValueError:
                detail = r.text
            if isinstance(detail, list):
                detail = "; ".join(str(d.get("msg", d)) for d in detail)
            raise APIError(str(detail), r.status_code)
        return None if r.status_code == 204 or not r.content else r.json()

    # ---- auth
    def register(self, username, email, password):
        return self._request("POST", "/api/auth/register", json={"username": username, "email": email, "password": password})

    def login(self, username, password) -> str:
        return self._request("POST", "/api/auth/login", json={"username": username, "password": password})["access_token"]

    def me(self): return self._request("GET", "/api/auth/me")

    # ---- user
    def get_settings(self): return self._request("GET", "/api/users/me/settings")
    def update_settings(self, **kw): return self._request("PUT", "/api/users/me/settings", json=kw)
    def change_password(self, current, new):
        return self._request("POST", "/api/users/me/password", json={"current_password": current, "new_password": new})

    # ---- markets
    def markets(self, category=None, q=""):
        return self._request("GET", "/api/markets", params={k: v for k, v in {"category": category, "q": q}.items() if v})
    def market_status(self): return self._request("GET", "/api/markets/status")
    def overview(self, category=None): return self._request("GET", "/api/markets/overview", params={"category": category} if category else None)
    def asset(self, symbol): return self._request("GET", f"/api/markets/{_sym(symbol)}")
    def history(self, symbol, timeframe="1h", limit=300):
        return self._request("GET", f"/api/markets/{_sym(symbol)}/history", params={"timeframe": timeframe, "limit": limit})
    def indicators(self, symbol, timeframe, indicators: list[str], limit=300):
        return self._request("GET", f"/api/markets/{_sym(symbol)}/indicators",
                             params={"timeframe": timeframe, "limit": limit, "indicators": ",".join(indicators)})
    def news(self, category=None): return self._request("GET", "/api/markets/news", params={"category": category} if category else None)
    def calendar(self): return self._request("GET", "/api/markets/calendar")

    # ---- watchlist
    def watchlist(self): return self._request("GET", "/api/watchlist")
    def watchlist_add(self, symbol): return self._request("POST", "/api/watchlist", json={"symbol": symbol})
    def watchlist_remove(self, symbol): return self._request("DELETE", f"/api/watchlist/{_sym(symbol)}")
    def watchlist_favorite(self, symbol): return self._request("PUT", f"/api/watchlist/{_sym(symbol)}/favorite")

    # ---- trading
    def order(self, side, symbol, quantity, order_type="market", limit_price=None):
        body = {"symbol": symbol, "quantity": quantity, "order_type": order_type}
        if order_type == "limit":
            body["limit_price"] = limit_price
        return self._request("POST", f"/api/trading/{side}", json=body)
    def orders(self, status=None): return self._request("GET", "/api/trading/orders", params={"status": status} if status else None)
    def cancel_order(self, order_id): return self._request("DELETE", f"/api/trading/orders/{order_id}")
    def positions(self): return self._request("GET", "/api/trading/positions")
    def transactions(self, limit=200): return self._request("GET", "/api/trading/history", params={"limit": limit})

    # ---- portfolio
    def portfolio(self): return self._request("GET", "/api/portfolio")
    def performance(self): return self._request("GET", "/api/portfolio/performance")
    def reset_portfolio(self): return self._request("POST", "/api/portfolio/reset")

    # ---- alerts / notifications
    def alerts(self): return self._request("GET", "/api/alerts")
    def create_alert(self, symbol, target_price, condition):
        return self._request("POST", "/api/alerts", json={"symbol": symbol, "target_price": target_price, "condition": condition})
    def delete_alert(self, alert_id): return self._request("DELETE", f"/api/alerts/{alert_id}")
    def notifications(self): return self._request("GET", "/api/alerts/notifications")
    def mark_notifications_read(self): return self._request("POST", "/api/alerts/notifications/read")
