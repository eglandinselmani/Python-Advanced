"""Paper-trading workspace: order ticket, open orders, positions, order history."""
import pandas as pd
import streamlit as st

from frontend import state
from frontend.components import charts
from frontend.components.styles import money
from frontend.components.trading_panel import trading_panel


def render():
    api = state.api()
    st.title("Paper Trading")
    st.caption("Practise with $100,000 of virtual money. Every order is validated and executed by the backend.")
    names = [a["symbol"] for a in state.all_assets()]
    sym = st.session_state.setdefault("symbol", "BTC/USD")
    left, right = st.columns([3, 1.2], gap="medium")
    with left:
        pick = st.selectbox("Instrument", names, index=names.index(sym) if sym in names else 0, key="pt_pick")
        st.session_state.symbol = sym = pick
        charts.chart_panel(sym, "pt", height=430)
    with right:
        trading_panel(sym, "pt")

    t1, t2, t3 = st.tabs(["Open positions", "Orders", "Transactions"])
    with t1:
        pos = state.call(api.positions, default=[]) or []
        if not pos:
            st.info("No open positions.")
        for p in pos:
            c = st.columns([1.4, 1, 1.2, 1.2, 1.3, 1.3, 1])
            c[0].markdown(f"**{p['symbol']}**<br><span class='tv-muted'>{p['name']}</span>", unsafe_allow_html=True)
            c[1].metric("Quantity", f"{p['quantity']:g}")
            c[2].metric("Avg entry", f"{p['average_entry_price']:,.4f}")
            c[3].metric("Last", f"{p['current_price']:,.4f}")
            c[4].metric("Value", money(p["market_value"]))
            c[5].metric("Unrealized P&L", money(p["unrealized_pnl"], True), f"{p['unrealized_pnl_pct']:+.2f}%")
            if c[6].button("Close", key=f"close_{p['symbol']}", help="Sell the entire position at market"):
                try:
                    api.order("sell", p["symbol"], p["quantity"], "market")
                    st.toast(f"Closed {p['symbol']}", icon="✅")
                except Exception as e:
                    st.error(getattr(e, "message", str(e)))
                st.rerun()
    with t2:
        orders = state.call(api.orders, default=[]) or []
        pending = [o for o in orders if o["status"] == "pending"]
        if pending:
            st.markdown("**Pending limit orders**")
            for o in pending:
                c = st.columns([1.2, 0.8, 1, 1, 1.4, 1])
                c[0].write(f"#{o['id']} **{o['symbol']}**")
                c[1].write(o["side"].upper())
                c[2].write(f"{o['quantity']:g}")
                c[3].write(f"@ {o['limit_price']:,.4f}")
                c[4].write(o["created_at"][:16].replace("T", " "))
                if c[5].button("Cancel", key=f"cancel_{o['id']}"):
                    state.call(api.cancel_order, o["id"]); st.rerun()
        if orders:
            df = pd.DataFrame(orders)[["id", "created_at", "symbol", "side", "order_type", "quantity", "limit_price", "execution_price", "status"]]
            df.columns = ["ID", "Created (UTC)", "Symbol", "Side", "Type", "Qty", "Limit", "Exec. price", "Status"]
            tcol = next(c for c in df.columns if c in ("Time (UTC)", "Created (UTC)"))
            df[tcol] = df[tcol].str[:19].str.replace("T", " ")
            st.dataframe(df, hide_index=True, width="stretch")
        else:
            st.info("No orders yet.")
    with t3:
        tx = state.call(api.transactions, default=[]) or []
        if tx:
            df = pd.DataFrame(tx)[["id", "created_at", "transaction_type", "symbol", "quantity", "price", "total_value", "realized_pnl"]]
            df.columns = ["ID", "Time (UTC)", "Type", "Symbol", "Qty", "Price", "Total value", "Realized P&L"]
            tcol = next(c for c in df.columns if c in ("Time (UTC)", "Created (UTC)"))
            df[tcol] = df[tcol].str[:19].str.replace("T", " ")
            st.dataframe(df, hide_index=True, width="stretch")
        else:
            st.info("No transactions yet.")
