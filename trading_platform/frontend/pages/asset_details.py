"""Detailed asset view."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend import state
from frontend.components import charts
from frontend.components.market_cards import stat_card
from frontend.components.styles import fmt_price, pct_class
from frontend.components.trading_panel import trading_panel
from frontend.config import THEMES


def _fmt_big(v):
    if v is None: return "—"
    for unit, d in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= d: return f"{v / d:,.2f}{unit}"
    return f"{v:,.2f}"


def render():
    api = state.api()
    names = [a["symbol"] for a in state.all_assets()]
    sym = st.session_state.setdefault("symbol", "BTC/USD")
    c0, c1 = st.columns([2, 5], vertical_alignment="bottom")
    pick = c0.selectbox("Asset", names, index=names.index(sym) if sym in names else 0, key="asset_pick")
    if pick != sym:
        st.session_state.symbol = sym = pick
    q = state.call(api.asset, sym)
    if not q:
        return
    watch = {w["symbol"] for w in state.call(api.watchlist, default=[]) or []}
    with c1:
        b = st.columns([1.3, 1.3, 4])
        if sym in watch:
            if b[0].button("Remove from watchlist", icon=":material/star:", key="ad_unwatch"):
                state.call(api.watchlist_remove, sym); st.rerun()
        elif b[0].button("Add to watchlist", icon=":material/star_border:", type="primary", key="ad_watch"):
            state.call(api.watchlist_add, sym); st.rerun()
        if b[1].button("Create alert", icon=":material/add_alert:", key="ad_alert"):
            st.session_state.alert_symbol = sym
            state.goto("alerts"); st.rerun()
    charts.symbol_header(q)
    main, side = st.columns([3.4, 1.2], gap="medium")
    with main:
        charts.chart_panel(sym, "asset", height=560)
    with side:
        trading_panel(sym, "asset")

    st.write("")
    c = st.columns(5)
    with c[0]: stat_card("Price", fmt_price(q["price"]), f"{q['change_pct']:+.2f}% today", pct_class(q["change_pct"]))
    with c[1]: stat_card("Day high", fmt_price(q["high"]))
    with c[2]: stat_card("Day low", fmt_price(q["low"]))
    with c[3]: stat_card("Volume", _fmt_big(q["volume"]))
    with c[4]: stat_card("Market cap", ("$" + _fmt_big(q["market_cap"])) if q["market_cap"] else "n/a", "approximate reference value" if q["market_cap"] else "not applicable to this asset class")
    st.write("")
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        st.subheader("About")
        st.write(q["description"])
        st.caption(f"Category: {q['category'].title()} · Data: {q['source']}")
    with right:
        st.subheader("Historical performance")
        perf = {k: v for k, v in q["performance"].items() if v is not None}
        if perf:
            t = THEMES.get(state.settings().get("theme", "dark"), THEMES["dark"])
            fig = go.Figure(go.Bar(x=list(perf), y=list(perf.values()), marker_color=[t["up"] if v >= 0 else t["down"] for v in perf.values()],
                                   text=[f"{v:+.2f}%" for v in perf.values()], textposition="outside"))
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor=t["bg"], plot_bgcolor=t["bg"],
                              font=dict(color=t["text"]), yaxis=dict(gridcolor=t["grid"], ticksuffix="%"), xaxis=dict(showgrid=False))
            st.plotly_chart(fig, width="stretch", key="perf_bar")
