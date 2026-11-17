"""News and economic calendar."""
import pandas as pd
import streamlit as st

from frontend import state


def _feed(category):
    data = state.call(state.api().news, category, default={"items": [], "notice": None})
    if data["notice"]:
        st.markdown(f"<div class='tv-banner'><b>Sample content.</b> {data['notice']}</div>", unsafe_allow_html=True)
    for it in data["items"]:
        title = f"[{it['title']}]({it['url']})" if it.get("url") else f"**{it['title']}**"
        tag = "LIVE" if it["source"] == "live" else "SAMPLE"
        st.markdown(f"{title}  \n<span class='tv-muted'>{it['category'].title()} · {tag} · {(it.get('published') or '')[:25]}</span>  \n{it['summary']}",
                    unsafe_allow_html=True)
        st.divider()


def render():
    st.title("News & Economic Calendar")
    t1, t2, t3, t4 = st.tabs(["All news", "Crypto", "Stocks", "Economic calendar"])
    with t1: _feed(None)
    with t2: _feed("crypto")
    with t3: _feed("stocks")
    with t4:
        cal = state.call(state.api().calendar)
        if cal:
            st.markdown(f"<div class='tv-banner'><b>Sample content.</b> {cal['notice']}</div>", unsafe_allow_html=True)
            df = pd.DataFrame(cal["events"])
            df.columns = ["Date", "Country", "Event", "Impact"]
            st.dataframe(df, hide_index=True, width="stretch")
