"""Watchlist management page."""
import pandas as pd
import streamlit as st

from frontend import state
from frontend.components.styles import fmt_price, pct_class, source_badge


def render():
    api = state.api()
    st.title("Watchlist")
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    items = state.call(api.watchlist, default=[]) or []
    have = {i["symbol"] for i in items}
    options = [f"{a['symbol']} — {a['name']}" for a in state.all_assets() if a["symbol"] not in have]
    pick = c1.selectbox("Search and add an asset", options, index=None, placeholder="Type to search (e.g. MSFT, gold, ethereum)…", key="wlp_pick")
    if c2.button("Add to watchlist", type="primary", disabled=pick is None, width="stretch"):
        if state.call(api.watchlist_add, pick.split(" — ")[0]):
            st.toast("Added to watchlist", icon="⭐")
            st.rerun()
    if not items:
        st.info("Your watchlist is empty.")
        return
    st.markdown("<div class='wl-head'><span>Asset</span><span>Price · Change · High/Low · Actions</span></div>", unsafe_allow_html=True)
    for it in sorted(items, key=lambda i: not i["favorite"]):
        with st.container(key=f"wlrow_p_{it['symbol']}"):
            c = st.columns([2.2, 1.4, 1.2, 1.1, 1.1, 0.7, 0.7, 0.7], vertical_alignment="center")
            c[0].markdown(f"<span class='wl-row' style='text-align:left'><b>{'★ ' if it['favorite'] else ''}{it['symbol']}</b><br><small>{it['name']}</small></span>", unsafe_allow_html=True)
            c[1].markdown(f"<div class='wl-row'>{fmt_price(it['price'])}</div>", unsafe_allow_html=True)
            c[2].markdown(f"<div class='wl-row {pct_class(it['change_pct'])}'>{it['change_pct']:+.2f}%</div>", unsafe_allow_html=True)
            c[3].markdown(f"<div class='wl-row'><small>H</small> {fmt_price(it['high'])}</div>", unsafe_allow_html=True)
            c[4].markdown(f"<div class='wl-row'><small>L</small> {fmt_price(it['low'])}</div>", unsafe_allow_html=True)
            if c[5].button("", key=f"wp_open_{it['symbol']}", icon=":material/open_in_new:", help="Open asset details"):
                state.goto("asset", it["symbol"]); st.rerun()
            if c[6].button("", key=f"wp_fav_{it['symbol']}", icon=":material/star:", help="Toggle favorite"):
                state.call(api.watchlist_favorite, it["symbol"]); st.rerun()
            if c[7].button("", key=f"wp_rm_{it['symbol']}", icon=":material/delete:", help="Remove"):
                state.call(api.watchlist_remove, it["symbol"]); st.toast(f"Removed {it['symbol']}"); st.rerun()
    st.markdown(source_badge(items[0]["source"]), unsafe_allow_html=True)
