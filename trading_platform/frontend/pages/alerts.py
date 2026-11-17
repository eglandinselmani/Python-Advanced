"""Price alerts and notification centre."""
import pandas as pd
import streamlit as st

from frontend import state
from frontend.components.styles import fmt_price


def render():
    api = state.api()
    st.title("Price Alerts")
    names = [a["symbol"] for a in state.all_assets()]
    default = st.session_state.pop("alert_symbol", None) or st.session_state.get("symbol", "BTC/USD")
    left, right = st.columns([1, 2], gap="large")
    with left:
        with st.form("alert_form"):
            st.markdown("**New alert**")
            sym = st.selectbox("Asset", names, index=names.index(default) if default in names else 0)
            cur = state.call(api.asset, sym)
            cond = st.radio("Condition", ["above", "below"], horizontal=True)
            price = st.number_input("Target price", min_value=0.0, value=float(cur["price"]) if cur else 1.0, format="%.4f")
            if cur:
                st.caption(f"Current price: {fmt_price(cur['price'])}")
            if st.form_submit_button("Create alert", type="primary", width="stretch"):
                if state.call(api.create_alert, sym, price, cond):
                    st.toast("Alert created", icon="🔔")
                    st.rerun()
    with right:
        alerts = state.call(api.alerts, default=[]) or []
        st.markdown("**Your alerts**")
        if not alerts:
            st.info("No alerts yet. Create one on the left – you will be notified when the price crosses your target.")
        for a in alerts:
            c = st.columns([1.3, 1.6, 1.4, 1.5, 0.8], vertical_alignment="center")
            c[0].markdown(f"**{a['symbol']}**")
            c[1].write(f"{a['condition'].title()} {fmt_price(a['target_price'])}")
            c[2].markdown("🟢 Active" if a["status"] == "active" else "✅ Triggered")
            c[3].caption(a["created_at"][:16].replace("T", " ") if a["status"] == "active" else f"hit @ {fmt_price(a['triggered_price'])}")
            if c[4].button("", key=f"del_alert_{a['id']}", icon=":material/delete:", help="Delete alert"):
                state.call(api.delete_alert, a["id"]); st.rerun()
        st.divider()
        st.markdown("**Notifications**")
        notes = state.call(api.notifications, default=[]) or []
        if st.button("Mark all as read", key="alerts_mark_read"):
            state.call(api.mark_notifications_read); st.rerun()
        for n in notes[:15]:
            st.markdown(f"{'🔵 ' if not n['is_read'] else ''}{n['message']}  \n<span class='tv-muted' style='font-size:.72rem'>{n['kind']} · {n['created_at'][:16].replace('T', ' ')} UTC</span>",
                        unsafe_allow_html=True)
