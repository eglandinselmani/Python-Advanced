"""Small reusable market widgets (stat cards, ticker strip, mover lists)."""
import streamlit as st

from frontend import state
from frontend.components.styles import fmt_price, pct_class


def _compact(v: float) -> str:
    for unit, d in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= d:
            return f"${v / d:,.1f}{unit}"
    return f"${v:,.0f}"


def stat_card(label: str, value: str, sub: str = "", cls: str = "") -> None:
    st.markdown(f"<div class='tv-card'><div class='lbl'>{label}</div><div class='val'>{value}</div>"
                f"<div class='sub {cls}'>{sub}</div></div>", unsafe_allow_html=True)


def ticker_strip(symbols: list[str]) -> None:
    quotes = {q["symbol"]: q for q in state.all_assets()}
    items = [quotes[s] for s in symbols if s in quotes]
    cols = st.columns(len(items))
    for col, q in zip(cols, items):
        with col:
            cls = pct_class(q["change_pct"])
            st.markdown(f"<div class='tv-card'><div class='tv-ticker'><span class='t1'>{q['symbol']}</span>"
                        f"<span class='t2'>{fmt_price(q['price'])}</span>"
                        f"<span class='t3 {cls}'>{q['change_pct']:+.2f}%</span></div></div>", unsafe_allow_html=True)


def mover_list(title: str, quotes: list[dict], metric: str = "change") -> None:
    rows = ""
    for q in quotes:
        cls = pct_class(q["change_pct"])
        right = f"<span class='{cls}'>{q['change_pct']:+.2f}%</span>" if metric == "change" else \
            f"<span class='tv-muted'>{_compact(q['volume'] * q['price'])}</span>"
        rows += (f"<div class='tv-row'><span><b>{q['symbol']}</b> <span class='tv-muted' style='font-size:.75rem'>"
                 f"{q['name'][:18]}</span></span><span>{fmt_price(q['price'])} &nbsp; {right}</span></div>")
    st.markdown(f"<div class='tv-card'><div class='tv-panel-title'>{title}</div>{rows}</div>", unsafe_allow_html=True)
