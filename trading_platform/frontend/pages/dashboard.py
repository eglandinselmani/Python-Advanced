"""Main terminal: ticker strip, chart, watchlist, order ticket, portfolio summary, movers, news."""
import pandas as pd
import streamlit as st

from frontend import state
from frontend.components import charts
from frontend.components.market_cards import mover_list, stat_card, ticker_strip
from frontend.components.styles import money, pct_class
from frontend.components.trading_panel import trading_panel
from frontend.components.watchlist_panel import watchlist_panel


def render():
    api = state.api()
    ticker_strip(["SPX", "NDX", "BTC/USD", "ETH/USD", "EUR/USD", "XAU/USD"])
    st.write("")
    sym = st.session_state.setdefault("symbol", state.settings().get("default_symbol", "BTC/USD"))
    main, side = st.columns([3.6, 1.15], gap="medium")

    with main:
        top = st.columns([4, 1.6], vertical_alignment="center")
        q = state.call(api.asset, sym)
        with top[0]:
            if q:
                charts.symbol_header(q)
        with top[1]:
            layout = st.segmented_control("Layout", ["1 chart", "2 charts", "4 charts"], default="1 chart", key="layout",
                                          label_visibility="collapsed") or "1 chart"
        if layout == "1 chart":
            charts.chart_panel(sym, "main", height=700)
        else:
            n = 2 if layout == "2 charts" else 4
            _, ct, _ = charts.controls("multi")
            tf = st.session_state.get("multi_tf") or "1h"
            names = [a["symbol"] for a in state.all_assets()]
            cols = st.columns(2)
            defaults = [sym, "ETH/USD", "AAPL", "EUR/USD"]
            for i in range(n):
                with cols[i % 2]:
                    pick = st.selectbox(f"Chart {i + 1}", names, index=names.index(defaults[i]) if defaults[i] in names else 0,
                                        key=f"multi_sym_{i}", label_visibility="collapsed")
                    charts.chart_panel(pick, f"multi{i}", height=330 if n == 4 else 440, show_controls=False, timeframe=tf)

    with side:
        watchlist_panel()
        st.divider()
        trading_panel(sym, "dash")

    # ---------- portfolio strip + tabs
    st.write("")
    pf = state.call(api.portfolio)
    if pf:
        c = st.columns(5)
        with c[0]: stat_card("Total balance (equity)", money(pf["total_equity"]), f"{pf['return_pct']:+.2f}% all-time", pct_class(pf["return_pct"]))
        with c[1]: stat_card("Daily P&L", money(pf["daily_pnl"], True), "open positions, vs previous close", pct_class(pf["daily_pnl"]))
        with c[2]: stat_card("Cash available", money(pf["available_balance"]), f"reserved {money(pf['reserved_balance'])}")
        with c[3]: stat_card("Unrealized P&L", money(pf["unrealized_pnl"], True), f"{len(pf['positions'])} open positions", pct_class(pf["unrealized_pnl"]))
        with c[4]: stat_card("Realized P&L", money(pf["realized_pnl"], True), "closed trades", pct_class(pf["realized_pnl"]))
    st.write("")
    t1, t2, t3 = st.tabs(["Market movers", "Recent transactions", "Market news"])
    with t1:
        ov = state.call(api.overview)
        if ov:
            a, b, c = st.columns(3)
            with a: mover_list("Top gainers", ov["gainers"])
            with b: mover_list("Top losers", ov["losers"])
            with c: mover_list("Most active (turnover)", ov["most_active"], "volume")
    with t2:
        tx = state.call(api.transactions, 8, default=[]) or []
        if tx:
            df = pd.DataFrame(tx)[["created_at", "transaction_type", "symbol", "quantity", "price", "total_value", "realized_pnl"]]
            df.columns = ["Time (UTC)", "Type", "Symbol", "Qty", "Price", "Total", "Realized P&L"]
            tcol = next(c for c in df.columns if c in ("Time (UTC)", "Created (UTC)"))
            df[tcol] = df[tcol].str[:19].str.replace("T", " ")
            st.dataframe(df, hide_index=True, width="stretch")
        else:
            st.info("No transactions yet – place your first paper trade with the order ticket.")
    with t3:
        news = state.call(api.news, default={"items": [], "notice": None})
        if news["notice"]:
            st.markdown(f"<div class='tv-banner'>{news['notice']}</div>", unsafe_allow_html=True)
        for it in news["items"][:5]:
            title = f"[{it['title']}]({it['url']})" if it.get("url") else f"**{it['title']}**"
            st.markdown(f"{title}  \n<span class='tv-muted'>{it['category'].title()} · {it['summary'][:140]}</span>", unsafe_allow_html=True)
