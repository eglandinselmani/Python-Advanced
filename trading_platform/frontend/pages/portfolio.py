"""Portfolio overview: balances, P&L, allocation, equity curve, positions."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from frontend import state
from frontend.components.market_cards import stat_card
from frontend.components.styles import money, pct_class
from frontend.config import THEMES


def render():
    api = state.api()
    t = THEMES.get(state.settings().get("theme", "dark"), THEMES["dark"])
    st.title("Portfolio")
    pf = state.call(api.portfolio)
    if not pf:
        return
    c = st.columns(4)
    with c[0]: stat_card("Total equity", money(pf["total_equity"]), f"{pf['return_pct']:+.2f}% vs ${pf['initial_balance']:,.0f} start", pct_class(pf["return_pct"]))
    with c[1]: stat_card("Cash balance", money(pf["balance"]), f"available {money(pf['available_balance'])}")
    with c[2]: stat_card("Unrealized P&L", money(pf["unrealized_pnl"], True), "open positions", pct_class(pf["unrealized_pnl"]))
    with c[3]: stat_card("Realized P&L", money(pf["realized_pnl"], True), "closed trades", pct_class(pf["realized_pnl"]))
    st.write("")
    left, right = st.columns([2, 1], gap="medium")
    perf = state.call(api.performance)
    with left:
        st.subheader("Equity curve")
        curve = perf["equity_curve"] if perf else []
        if len(curve) >= 2:
            df = pd.DataFrame(curve)
            df["time"] = pd.to_datetime(df["time"])
            fig = go.Figure(go.Scatter(x=df["time"], y=df["equity"], mode="lines+markers", line=dict(color=t["accent"], width=2),
                                       fill="tozeroy", fillcolor="rgba(41,98,255,.1)"))
            lo, hi = df["equity"].min(), df["equity"].max()
            pad = max((hi - lo) * 0.2, 50)
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor=t["bg"], plot_bgcolor=t["bg"], font=dict(color=t["text"]),
                              yaxis=dict(range=[lo - pad, hi + pad], gridcolor=t["grid"], side="right"), xaxis=dict(gridcolor=t["grid"]))
            st.plotly_chart(fig, width="stretch", key="equity_curve")
        else:
            st.info("The equity curve appears after your first trades.")
        if perf:
            p = st.columns(3)
            p[0].metric("Total trades", perf["total_trades"])
            p[1].metric("Closed trades", perf["closed_trades"])
            p[2].metric("Win rate", f"{perf['win_rate_pct']}%" if perf["win_rate_pct"] is not None else "—")
    with right:
        st.subheader("Allocation")
        parts = [{"name": "Cash", "value": pf["balance"]}] + [{"name": p["symbol"], "value": p["market_value"]} for p in pf["positions"]]
        fig = px.pie(pd.DataFrame(parts), names="name", values="value", hole=0.6,
                     color_discrete_sequence=["#2962ff", "#089981", "#f7c548", "#ab47bc", "#00bcd4", "#ff9800", "#f23645", "#8d6e63"])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor=t["bg"], font=dict(color=t["text"]),
                          legend=dict(font=dict(color=t["text"])))
        st.plotly_chart(fig, width="stretch", key="alloc")

    st.subheader("Open positions")
    if pf["positions"]:
        df = pd.DataFrame(pf["positions"])[["symbol", "name", "quantity", "average_entry_price", "current_price", "market_value", "unrealized_pnl", "unrealized_pnl_pct", "daily_pnl"]]
        df.columns = ["Symbol", "Name", "Qty", "Avg entry", "Last", "Market value", "Unrealized P&L", "P&L %", "Daily P&L"]
        st.dataframe(df, hide_index=True, width="stretch",
                     column_config={"P&L %": st.column_config.NumberColumn(format="%+.2f%%")})
    else:
        st.info("You have no open positions. Open the **Paper Trading** page to place an order.")
    st.subheader("Transaction history")
    tx = state.call(api.transactions, default=[]) or []
    if tx:
        df = pd.DataFrame(tx)[["created_at", "transaction_type", "symbol", "quantity", "price", "total_value", "realized_pnl"]]
        df.columns = ["Time (UTC)", "Type", "Symbol", "Qty", "Price", "Total value", "Realized P&L"]
        tcol = next(c for c in df.columns if c in ("Time (UTC)", "Created (UTC)"))
        df[tcol] = df[tcol].str[:19].str.replace("T", " ")
        st.dataframe(df, hide_index=True, width="stretch")
        st.download_button("Download transactions (CSV)", df.to_csv(index=False), "transactions.csv", "text/csv")
    else:
        st.caption("No transactions yet.")
    with st.expander("Danger zone"):
        st.write("Reset your paper account to $100,000 and delete all positions, orders and transactions.")
        if st.checkbox("I understand this cannot be undone", key="reset_ok") and st.button("Reset paper account", key="reset_btn"):
            state.call(api.reset_portfolio)
            st.toast("Account reset to $100,000", icon="♻️")
            st.rerun()
