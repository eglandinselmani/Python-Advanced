"""User profile and preferences (stored in the database through the API)."""
import streamlit as st

from frontend import state
from frontend.config import CHART_TYPES, INDICATOR_OPTIONS, TF_LABELS, TIMEFRAMES


def render():
    api = state.api()
    st.title("Settings")
    user = st.session_state.get("user", {})
    s = state.settings()
    t1, t2, t3 = st.tabs(["Preferences", "Profile", "Security"])
    with t1:
        with st.form("prefs"):
            c1, c2 = st.columns(2)
            theme = c1.radio("Theme", ["dark", "light"], index=0 if s.get("theme") != "light" else 1, horizontal=True, format_func=str.title)
            ct = c2.radio("Preferred chart type", list(CHART_TYPES), index=list(CHART_TYPES).index(s.get("chart_type", "candles")),
                          horizontal=True, format_func=CHART_TYPES.get)
            tf = c1.selectbox("Preferred timeframe", TIMEFRAMES, index=TIMEFRAMES.index(s.get("timeframe", "1h")), format_func=TF_LABELS.get)
            names = [a["symbol"] for a in state.all_assets()]
            sym = c2.selectbox("Default symbol", names, index=names.index(s.get("default_symbol", "BTC/USD")) if s.get("default_symbol") in names else 0)
            inds = st.multiselect("Default indicators", list(INDICATOR_OPTIONS), default=state.indicator_labels_from_tokens(s.get("indicators", "volume")))
            if st.form_submit_button("Save preferences", type="primary"):
                res = state.save_settings(theme=theme, chart_type=ct, timeframe=tf, default_symbol=sym, indicators=state.tokens_from_labels(inds))
                if res:
                    for k in [k for k in st.session_state if k.endswith(("_tf", "_ct", "_ind"))]:
                        del st.session_state[k]
                    st.session_state.symbol = sym
                    st.toast("Preferences saved", icon="✅")
                    st.rerun()
    with t2:
        st.markdown(f"**Username:** {user.get('username')}  \n**Email:** {user.get('email')}  \n**Member since:** {str(user.get('created_at', ''))[:10]}")
        pf = state.call(api.portfolio)
        if pf:
            st.metric("Paper account equity", f"${pf['total_equity']:,.2f}")
    with t3:
        with st.form("pw"):
            cur = st.text_input("Current password", type="password")
            new = st.text_input("New password (min 8 chars, letters + digits)", type="password")
            if st.form_submit_button("Change password"):
                if state.call(api.change_password, cur, new, default=False) is not False:
                    st.success("Password updated.")
