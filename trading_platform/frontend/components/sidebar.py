"""Left vertical toolbar + top bar (search, data-source badge, notifications, profile)."""
import streamlit as st

from frontend import state
from frontend.components.styles import LOGO_SVG, source_badge
from frontend.config import APP_NAME

NAV = [
    ("dashboard", "Chart", ":material/candlestick_chart:"),
    ("markets", "Markets", ":material/public:"),
    ("watchlist", "Watchlist", ":material/star:"),
    ("asset", "Asset Details", ":material/info:"),
    ("trading", "Paper Trading", ":material/swap_vert:"),
    ("portfolio", "Portfolio", ":material/account_balance_wallet:"),
    ("alerts", "Alerts", ":material/notifications_active:"),
    ("news", "News & Calendar", ":material/newspaper:"),
    ("settings", "Settings", ":material/settings:"),
]


def _nav(page: str):
    st.session_state.page = page


def left_toolbar():
    with st.sidebar:
        st.markdown(f"<div class='tv-brand'>{LOGO_SVG}<div>{APP_NAME}<small>Paper trading</small></div></div>", unsafe_allow_html=True)
        for page, label, icon in NAV:
            st.button(label, key=f"nav_{page}", icon=icon, on_click=_nav, args=(page,),
                      type="primary" if st.session_state.get("page") == page else "secondary", width="stretch")
        st.markdown("<div class='tv-side-label'>Account</div>", unsafe_allow_html=True)
        st.button("Log out", key="nav_logout", icon=":material/logout:", on_click=state.logout, width="stretch")
        st.markdown("<div class='tv-muted' style='font-size:.66rem;padding:1rem .6rem'>Educational project.<br>No real money. Not financial advice.</div>",
                    unsafe_allow_html=True)


def _search_cb():
    sel = st.session_state.get("global_search")
    if sel:
        st.session_state.symbol = sel.split(" — ")[0]
        st.session_state.page = "asset"
        st.session_state.global_search = None


def top_bar(status: dict | None):
    user = st.session_state.get("user", {})
    notes = state.call(state.api().notifications, default=[], quiet=True) or []
    unread = [n for n in notes if not n["is_read"]]
    c1, c2, c3, c4 = st.columns([5, 3, 0.8, 1.6], vertical_alignment="center")
    with c1:
        opts = [f"{a['symbol']} — {a['name']}" for a in state.all_assets()]
        st.selectbox("Search", opts, index=None, key="global_search", placeholder="🔍  Search symbols, e.g. BTC, Apple, gold…",
                     label_visibility="collapsed", on_change=_search_cb)
    with c2:
        if status:
            st.markdown(f"<div style='text-align:right'>{source_badge(status['source'])}</div>", unsafe_allow_html=True)
    with c3:
        with st.popover(f"{len(unread)}" if unread else "", icon=":material/notifications:"):
            st.markdown("**Notifications**")
            if not notes:
                st.caption("Nothing yet.")
            for n in notes[:8]:
                dot = "🔵 " if not n["is_read"] else ""
                st.markdown(f"{dot}{n['message']}  \n<span class='tv-muted' style='font-size:.7rem'>{n['created_at'][:16].replace('T', ' ')} UTC</span>",
                            unsafe_allow_html=True)
            if unread and st.button("Mark all as read", key="mark_read"):
                state.call(state.api().mark_notifications_read)
                st.rerun()
    with c4:
        with st.popover(user.get("username", "Account"), icon=":material/account_circle:", width="stretch"):
            st.markdown(f"**{user.get('username', '')}**  \n<span class='tv-muted'>{user.get('email', '')}</span>", unsafe_allow_html=True)
            st.button("Settings & profile", key="top_settings", on_click=_nav, args=("settings",), icon=":material/settings:")
            st.button("Log out", key="top_logout", on_click=state.logout, icon=":material/logout:")
    if status and status["source"] != "live":
        st.markdown(f"<div class='tv-banner'><b>Simulated data.</b> {status['message']} Orders are executed on these simulated prices.</div>",
                    unsafe_allow_html=True)
