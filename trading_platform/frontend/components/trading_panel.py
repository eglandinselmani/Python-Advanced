"""Order ticket: market / limit, buy / sell. All validation and maths happen in the backend."""
import streamlit as st

from frontend import state
from frontend.components.styles import fmt_price, money

_CSS = """<style>
.st-key-btn_buy button { background:var(--up) !important; border-color:var(--up) !important; color:#fff !important; font-weight:600; }
.st-key-btn_sell button { background:var(--down) !important; border-color:var(--down) !important; color:#fff !important; font-weight:600; }
.st-key-btn_buy button:hover, .st-key-btn_sell button:hover { filter:brightness(1.12); color:#fff !important; }
</style>"""


def trading_panel(symbol: str, key: str = "tp") -> None:
    api = state.api()
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("<div class='tv-panel-title'>Order ticket · paper trading</div>", unsafe_allow_html=True)
    flash = st.session_state.pop(f"{key}_flash", None)
    if flash:
        (st.success if flash[0] == "ok" else st.error)(flash[1])
    q = state.call(api.asset, symbol)
    pf = state.call(api.portfolio)
    if not q or not pf:
        return
    held = next((p["quantity"] for p in pf["positions"] if p["symbol"] == q["symbol"]), 0.0)
    crypto = q["category"] in ("crypto", "forex")
    otype = st.pills("Order type", ["Market", "Limit"], default="Market", key=f"{key}_type", label_visibility="collapsed") or "Market"
    c1, c2 = st.columns(2)
    qty = c1.number_input("Quantity", min_value=0.0, value=0.1 if q["category"] == "crypto" else (1000.0 if q["category"] == "forex" else 1.0),
                          step=0.01 if q["category"] == "crypto" else (100.0 if q["category"] == "forex" else 1.0),
                          format="%.4f" if crypto else "%.2f", key=f"{key}_qty_{q['symbol']}")
    limit = None
    if otype == "Limit":
        limit = c2.number_input("Limit price", min_value=0.0, value=float(q["price"]), format="%.4f", key=f"{key}_lim_{q['symbol']}")
    else:
        c2.number_input("Market price", value=float(q["price"]), disabled=True, format="%.4f", key=f"{key}_mkt_{q['symbol']}")
    ref = limit if otype == "Limit" and limit else q["price"]
    st.markdown(
        f"<div class='tv-row'><span class='tv-muted'>Estimated value</span><b>{money(qty * ref)}</b></div>"
        f"<div class='tv-row'><span class='tv-muted'>Available balance</span><span>{money(pf['available_balance'])}</span></div>"
        f"<div class='tv-row'><span class='tv-muted'>You own</span><span>{held:g} {q['symbol']}</span></div>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    side = None
    if b1.button(f"Buy @ {fmt_price(ref)}", key="btn_buy", width="stretch"):
        side = "buy"
    if b2.button(f"Sell @ {fmt_price(ref)}", key="btn_sell", width="stretch"):
        side = "sell"
    if side:
        try:
            o = api.order(side, q["symbol"], qty, otype.lower(), limit)
            if o["status"] == "filled":
                msg = f"✅ {side.upper()} {qty:g} {q['symbol']} filled at {fmt_price(o['execution_price'])}"
            else:
                msg = f"🕒 Limit {side} order #{o['id']} placed – waiting for {fmt_price(o['limit_price'])}"
            st.session_state[f"{key}_flash"] = ("ok", msg)
        except Exception as e:  # APIError / BackendUnavailable
            st.session_state[f"{key}_flash"] = ("err", getattr(e, "message", str(e)))
        st.rerun()
    st.caption("Educational simulation – no real money is used.")
