"""Chartly – TradingView-inspired paper-trading terminal (Streamlit frontend).

Start the backend first (or use `python run.py`):   streamlit run frontend/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from frontend import state
from frontend.api_client import APIError, BackendUnavailable
from frontend.components import sidebar, styles
from frontend.config import APP_NAME
from frontend.pages import (alerts, asset_details, dashboard, markets, news, paper_trading, portfolio,
                            settings, watchlist)

st.set_page_config(page_title=f"{APP_NAME} – Trading terminal", page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")

PAGES = {"dashboard": dashboard, "markets": markets, "watchlist": watchlist, "asset": asset_details,
         "trading": paper_trading, "portfolio": portfolio, "alerts": alerts, "news": news, "settings": settings}


def auth_screen():
    styles.inject("dark")
    st.markdown("<div class='tv-auth'>", unsafe_allow_html=True)
    st.markdown(f"<div class='tv-hero'>{styles.LOGO_SVG}<h1>{APP_NAME}</h1><p>Professional charts. Risk-free paper trading.</p></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        login_tab, reg_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            with st.form("login"):
                u = st.text_input("Username", key="login_user")
                p = st.text_input("Password", type="password", key="login_pass")
                if st.form_submit_button("Log in", type="primary", width="stretch"):
                    try:
                        token = state.api().login(u, p)
                        st.session_state.token = token
                        st.session_state.user = state.api().me()
                        st.session_state.page = "dashboard"
                        st.rerun()
                    except BackendUnavailable as e:
                        st.error(e.message)
                    except APIError as e:
                        st.error(e.message)
        with reg_tab:
            with st.form("register"):
                ru = st.text_input("Username", key="reg_user", help="3–30 characters: letters, digits, _ . -")
                re_ = st.text_input("Email", key="reg_email")
                rp = st.text_input("Password", type="password", key="reg_pass", help="At least 8 characters with a letter and a digit")
                rp2 = st.text_input("Confirm password", type="password", key="reg_pass2")
                if st.form_submit_button("Create account", type="primary", width="stretch"):
                    if rp != rp2:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            state.api().register(ru, re_, rp)
                            st.session_state.token = state.api().login(ru, rp)
                            st.session_state.user = state.api().me()
                            st.session_state.page = "dashboard"
                            st.rerun()
                        except (APIError, BackendUnavailable) as e:
                            st.error(e.message)
        st.caption("Educational paper-trading project · no real money · not financial advice")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    if not st.session_state.get("token"):
        auth_screen()
        return
    st.session_state.setdefault("page", "dashboard")
    settings_ = state.settings()
    styles.inject(settings_.get("theme", "dark"))
    st.session_state.setdefault("symbol", settings_.get("default_symbol", "BTC/USD"))
    sidebar.left_toolbar()
    status = state.call(state.api().market_status, quiet=True)
    sidebar.top_bar(status)
    PAGES.get(st.session_state.page, dashboard).render()


main()
