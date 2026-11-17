"""Session-state helpers shared by all pages."""
from __future__ import annotations

import streamlit as st

from frontend.api_client import APIClient, APIError, BackendUnavailable
from frontend.config import INDICATOR_OPTIONS


def api() -> APIClient:
    return APIClient(st.session_state.get("token"))


def logout() -> None:
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def call(fn, *args, default=None, quiet=False, **kwargs):
    """Call an API method; show a friendly error instead of a stack trace."""
    try:
        return fn(*args, **kwargs)
    except BackendUnavailable as e:
        st.error(f"🔌 {e.message}")
        st.stop()
    except APIError as e:
        if e.status == 401 and st.session_state.get("token"):
            logout()
            st.rerun()
        if not quiet:
            st.error(e.message)
        return default


def goto(page: str, symbol: str | None = None) -> None:
    st.session_state.page = page
    if symbol:
        st.session_state.symbol = symbol


def settings() -> dict:
    if "settings" not in st.session_state:
        st.session_state.settings = call(api().get_settings, default={}) or {}
    return st.session_state.settings


def save_settings(**kw) -> dict | None:
    res = call(api().update_settings, **kw)
    if res:
        st.session_state.settings = res
    return res


def indicator_labels_from_tokens(tokens: str) -> list[str]:
    wanted = {t.strip() for t in tokens.split(",") if t.strip()}
    return [label for label, tok in INDICATOR_OPTIONS.items() if tok in wanted]


def tokens_from_labels(labels: list[str]) -> str:
    return ",".join(INDICATOR_OPTIONS[l] for l in labels)


def all_assets() -> list[dict]:
    if "assets" not in st.session_state:
        st.session_state.assets = call(api().markets, default=[]) or []
    return st.session_state.assets
