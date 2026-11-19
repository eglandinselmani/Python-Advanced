"""Right-hand watchlist (auto-refreshing fragment)."""
import streamlit as st

from frontend import state
from frontend.components.styles import fmt_price, pct_class


def _select(symbol: str):
    st.session_state.symbol = symbol
    if st.session_state.get("page") not in ("dashboard",):
        st.session_state.page = "asset"


def _add():
    sym = st.session_state.get("wl_add")
    if sym:
        res = state.call(state.api().watchlist_add, sym.split(" — ")[0])
        if res:
            st.toast(f"Added {res['symbol']} to watchlist", icon="⭐")
        st.session_state.wl_add = None


def _remove(symbol: str):
    if state.call(state.api().watchlist_remove, symbol, default=None, quiet=True) is None:
        st.toast(f"Removed {symbol}", icon="🗑️")


@st.fragment(run_every=3)
def watchlist_panel(show_header: bool = True):
    api = state.api()
    items = state.call(api.watchlist, default=[]) or []
    if show_header:
        st.markdown("<div class='tv-panel-title'>Watchlist</div>", unsafe_allow_html=True)
    have = {i["symbol"] for i in items}
    options = [f"{a['symbol']} — {a['name']}" for a in state.all_assets() if a["symbol"] not in have]
    st.selectbox("Add symbol", options, index=None, key="wl_add", placeholder="＋ Add symbol…",
                 label_visibility="collapsed", on_change=_add)
    st.markdown("<div class='wl-head'><span>Symbol</span><span>Last &nbsp;&nbsp;&nbsp; Chg%</span></div>", unsafe_allow_html=True)
    for it in sorted(items, key=lambda i: not i["favorite"]):
        with st.container(key=f"wlrow_{it['symbol']}"):
            c1, c2, c3, c4 = st.columns([2.3, 1.55, 1.15, 0.45], vertical_alignment="center")
            with c1:
                star = "★ " if it["favorite"] else ""
                if st.button(f"{star}{it['symbol']}", key=f"wl_sel_{it['symbol']}", type="tertiary", help=it["name"]):
                    _select(it["symbol"])
                    st.rerun()
            with c2:
                st.markdown(f"<div class='wl-row'>{fmt_price(it['price'])}</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='wl-row {pct_class(it['change_pct'])}'>{it['change_pct']:+.2f}%</div>", unsafe_allow_html=True)
            with c4:
                with st.popover("", icon=":material/more_vert:", type="tertiary"):
                    if st.button("Remove" , key=f"wl_rm_{it['symbol']}", icon=":material/delete:"):
                        _remove(it["symbol"])
                        st.rerun(scope="fragment")
                    if st.button("Unfavorite" if it["favorite"] else "Favorite", key=f"wl_fav_{it['symbol']}", icon=":material/star:"):
                        state.call(api.watchlist_favorite, it["symbol"])
                        st.rerun(scope="fragment")
    if not items:
        st.info("Your watchlist is empty – add a symbol above.")
