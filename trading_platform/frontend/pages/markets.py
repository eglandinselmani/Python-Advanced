"""Market overview per asset class, plus a market heatmap."""
import pandas as pd
import plotly.express as px
import streamlit as st

from frontend import state
from frontend.components.market_cards import mover_list, stat_card
from frontend.components.styles import pct_class, source_badge
from frontend.config import CATEGORIES, THEMES


def _table(category: str):
    api = state.api()
    q = st.text_input("Filter", key=f"mk_q_{category}", placeholder="Filter by name or symbol…", label_visibility="collapsed")
    rows = state.call(api.markets, category, q, default=[]) or []
    if not rows:
        st.info("No assets match your search.")
        return
    df = pd.DataFrame(rows)[["symbol", "name", "price", "change_pct", "high", "low", "volume", "market_cap"]]
    df["market_cap"] = df["market_cap"].map(lambda v: "—" if pd.isna(v) else f"${v / 1e12:,.2f}T" if v >= 1e12 else f"${v / 1e9:,.1f}B")
    df.columns = ["Symbol", "Name", "Price", "Change %", "24h High", "24h Low", "Volume", "Market cap"]
    sel = st.dataframe(
        df, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row", key=f"mk_df_{category}",
        column_config={"Change %": st.column_config.NumberColumn(format="%+.2f%%"),
                       "Price": st.column_config.NumberColumn(format="%.4f"),
                       "Volume": st.column_config.NumberColumn(format="%.0f")})
    st.caption("Select a row to open the asset details.")
    if sel and sel["selection"]["rows"]:
        state.goto("asset", df.iloc[sel["selection"]["rows"][0]]["Symbol"])
        st.rerun()


def _category(category: str):
    ov = state.call(state.api().overview, category)
    if not ov:
        return
    s = ov["stats"]
    st.markdown(source_badge(ov["source"]), unsafe_allow_html=True)
    c = st.columns(4)
    with c[0]: stat_card("Assets tracked", str(s["assets"]))
    with c[1]: stat_card("Advancing / declining", f"{s['advancing']} / {s['declining']}")
    with c[2]: stat_card("Average change", f"{s['average_change_pct']:+.2f}%", cls=pct_class(s["average_change_pct"]))
    with c[3]: stat_card("Best / worst", f"{s['best']} / {s['worst']}")
    st.write("")
    a, b, c3 = st.columns(3)
    with a: mover_list("Top gainers", ov["gainers"])
    with b: mover_list("Top losers", ov["losers"])
    with c3: mover_list("Most active", ov["most_active"], "volume")
    st.write("")
    _table(category)


def _heatmap():
    t = THEMES.get(state.settings().get("theme", "dark"), THEMES["dark"])
    rows = state.call(state.api().markets, default=[]) or []
    if not rows:
        return
    df = pd.DataFrame(rows)
    df["size"] = df["market_cap"].fillna(df["price"] * df["volume"]).clip(lower=1) ** 0.5
    df["cat"] = df["category"].map(CATEGORIES)
    fig = px.treemap(df, path=[px.Constant("All markets"), "cat", "symbol"], values="size", color="change_pct",
                     color_continuous_scale=[(0, t["down"]), (0.5, t["panel2"]), (1, t["up"])], range_color=(-5, 5),
                     custom_data=["name", "price", "change_pct"])
    fig.update_traces(texttemplate="<b>%{label}</b><br>%{customdata[2]:+.2f}%", hovertemplate="<b>%{label}</b> %{customdata[0]}<br>Price %{customdata[1]}<br>Change %{customdata[2]:+.2f}%<extra></extra>",
                      marker_line_width=1, marker_line_color=t["bg"])
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor=t["bg"], font=dict(color="#fff"),
                      coloraxis_colorbar=dict(title="Change %", tickfont=dict(color=t["text"]), title_font=dict(color=t["text"])))
    st.plotly_chart(fig, width="stretch", key="heatmap")
    st.caption("Tile size ≈ market capitalisation (or traded value when no market cap exists). Colour = 24h change.")


def render():
    st.title("Markets")
    tabs = st.tabs([*CATEGORIES.values(), "Heatmap"])
    for tab, cat in zip(tabs, CATEGORIES):
        with tab:
            _category(cat)
    with tabs[-1]:
        _heatmap()
