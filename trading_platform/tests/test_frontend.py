"""Frontend tests: the real Streamlit app is executed with AppTest, and its HTTP layer is wired
to the real FastAPI app (TestClient). No mocks of business logic - pages call the actual REST API."""
import tempfile
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from frontend import api_client
from tests.conftest import build_client
from backend.main import app

APP = str(Path(__file__).resolve().parent.parent / "frontend" / "app.py")
PAGES = ["dashboard", "markets", "watchlist", "asset", "trading", "portfolio", "alerts", "news", "settings"]


@pytest.fixture()
def backend(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        client, _, engine = build_client(f"sqlite:///{d}/fe.db")
        monkeypatch.setattr(api_client, "_http", client)
        yield client
        engine.dispose()
        app.dependency_overrides.clear()


def btn(at, label):
    return next(b for b in at.button if b.label == label)


def new_app(timeout=60) -> AppTest:
    return AppTest.from_file(APP, default_timeout=timeout)


def logged_in(backend, page="dashboard") -> AppTest:
    api = api_client.APIClient()
    api.register("frank", "frank@example.com", "Passw0rd123")
    at = new_app()
    at.session_state["token"] = api.login("frank", "Passw0rd123")
    at.session_state["user"] = api_client.APIClient(at.session_state["token"]).me()
    at.session_state["page"] = page
    return at.run()


def test_login_screen_shown_when_logged_out(backend):
    at = new_app().run()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Log in", "Create account"]


def test_register_then_login_through_the_ui(backend):
    at = new_app().run()
    at.text_input(key="reg_user").input("grace")
    at.text_input(key="reg_email").input("grace@example.com")
    at.text_input(key="reg_pass").input("Passw0rd123")
    at.text_input(key="reg_pass2").input("Passw0rd123")
    btn(at, "Create account").click().run()
    assert not at.exception
    assert at.session_state["token"] and at.session_state["user"]["username"] == "grace"
    # log out then log in again with the same credentials
    at.session_state["token"] = None
    at.run()
    at.text_input(key="login_user").input("grace")
    at.text_input(key="login_pass").input("Passw0rd123")
    btn(at, "Log in").click().run()
    assert at.session_state["user"]["email"] == "grace@example.com"


def test_wrong_password_shows_error(backend):
    api_client.APIClient().register("henry", "henry@example.com", "Passw0rd123")
    at = new_app().run()
    at.text_input(key="login_user").input("henry")
    at.text_input(key="login_pass").input("WrongPass999")
    btn(at, "Log in").click().run()
    assert any("Incorrect username or password" in e.value for e in at.error)
    assert not at.session_state["token"] if "token" in at.session_state else True


def test_password_mismatch_on_register(backend):
    at = new_app().run()
    at.text_input(key="reg_user").input("ivan")
    at.text_input(key="reg_email").input("ivan@example.com")
    at.text_input(key="reg_pass").input("Passw0rd123")
    at.text_input(key="reg_pass2").input("Different123")
    btn(at, "Create account").click().run()
    assert any("do not match" in e.value for e in at.error)


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders_without_errors(backend, page):
    at = logged_in(backend, page)
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def test_dashboard_shows_balance_and_watchlist(backend):
    at = logged_in(backend)
    text = " ".join(m.value for m in at.markdown)
    assert "$100,000.00" in text and "BTC/USD" in text
    assert any(b.key == "wl_sel_AAPL" for b in at.button)           # default watchlist rendered from API


def test_navigation_buttons_switch_pages(backend):
    at = logged_in(backend)
    at.button(key="nav_portfolio").click().run()
    assert at.session_state["page"] == "portfolio" and any(t.value == "Portfolio" for t in at.title)
    at.button(key="nav_markets").click().run()
    assert at.session_state["page"] == "markets"
    assert not at.exception


def test_buy_through_order_ticket_updates_portfolio(backend):
    at = logged_in(backend, "trading")
    at.selectbox(key="pt_pick").select("AAPL").run()
    at.button(key="btn_buy").click().run()
    token = at.session_state["token"]
    pos = api_client.APIClient(token).positions()
    assert len(pos) == 1 and pos[0]["symbol"] == "AAPL"
    at.run()
    assert not at.exception
    at.button(key="btn_sell").click().run()
    assert api_client.APIClient(token).positions() == [] and len(api_client.APIClient(token).transactions()) == 2


def test_settings_theme_saved_and_applied(backend):
    at = logged_in(backend, "settings")
    at.radio[0].set_value("light")
    btn(at, "Save preferences").click().run()
    token = at.session_state["token"]
    assert api_client.APIClient(token).get_settings()["theme"] == "light"
    assert not at.exception


def test_watchlist_page_add_and_remove(backend):
    at = logged_in(backend, "watchlist")
    at.selectbox(key="wlp_pick").select("MSFT — Microsoft Corp.").run()
    btn(at, "Add to watchlist").click().run()
    token = at.session_state["token"]
    assert "MSFT" in [w["symbol"] for w in api_client.APIClient(token).watchlist()]
    at.button(key="wp_rm_MSFT").click().run()
    assert "MSFT" not in [w["symbol"] for w in api_client.APIClient(token).watchlist()]


def test_alert_created_from_ui(backend):
    at = logged_in(backend, "alerts")
    form_btn = btn(at, "Create alert")
    form_btn.click().run()
    assert len(api_client.APIClient(at.session_state["token"]).alerts()) == 1


def test_backend_down_shows_friendly_message(monkeypatch):
    import requests

    class Dead:
        def request(self, *a, **k):
            raise requests.exceptions.ConnectionError("down")
    monkeypatch.setattr(api_client, "_http", Dead())
    at = new_app().run()
    at.text_input(key="login_user").input("x")
    at.text_input(key="login_pass").input("y")
    btn(at, "Log in").click().run()
    assert any("Cannot reach the backend" in e.value for e in at.error)
