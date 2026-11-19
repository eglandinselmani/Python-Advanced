"""Plotly chart engine: candles/line/area, volume, overlays, RSI, MACD, crosshair, last-price tag."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from frontend import state
from frontend.components.styles import fmt_price, pct_class, source_badge
from frontend.config import CHART_TYPES, INDICATOR_OPTIONS, THEMES, TF_LABELS, TIMEFRAMES

PLOT_CONFIG = {
    "scrollZoom": True, "displaylogo": False, "responsive": True,
    "modeBarButtonsToAdd": ["drawline", "drawopenpath", "drawrect", "drawcircle", "eraseshape"],
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "filename": "chartly_chart", "scale": 2},
}


def _theme() -> dict:
    return THEMES.get(state.settings().get("theme", "dark"), THEMES["dark"])


def _rgba(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def build_figure(candles: list[dict], series: dict[str, list], ind_ts: list[str], symbol: str, chart_type: str,
                 selected: list[str], visible: int = 120, height: int = 560) -> go.Figure:
    t = _theme()
    df = pd.DataFrame(candles)
    df["dt"] = pd.to_datetime(df["time"])
    pos = {ts: i for i, ts in enumerate(ind_ts)}

    def col(name):  # align indicator values to candle timestamps
        vals = series.get(name)
        if vals is None:
            return None
        return [vals[pos[ts]] if ts in pos else None for ts in df["time"]]

    show_rsi, show_macd = "RSI (14)" in selected, "MACD" in selected
    panes = 1 + show_rsi + show_macd
    heights = {1: [1.0], 2: [0.72, 0.28], 3: [0.58, 0.21, 0.21]}[panes]
    fig = make_subplots(rows=panes, cols=1, shared_xaxes=True, vertical_spacing=0.025, row_heights=heights,
                        specs=[[{"secondary_y": True}]] + [[{}]] * (panes - 1))
    up, down = t["up"], t["down"]

    # ---- main series
    if chart_type == "line":
        fig.add_trace(go.Scatter(x=df["dt"], y=df["close"], mode="lines", name=symbol,
                                 line=dict(color=t["accent"], width=2), hovertemplate="%{y}"), row=1, col=1)
    elif chart_type == "area":
        fig.add_trace(go.Scatter(x=df["dt"], y=df["close"], mode="lines", name=symbol, fill="tozeroy",
                                 line=dict(color=t["accent"], width=2), fillcolor=_rgba(t["accent"], 0.15),
                                 hovertemplate="%{y}"), row=1, col=1)
    else:
        fig.add_trace(go.Candlestick(x=df["dt"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                                     name=symbol, increasing=dict(line=dict(color=up, width=1), fillcolor=up),
                                     decreasing=dict(line=dict(color=down, width=1), fillcolor=down)), row=1, col=1)

    # ---- overlays
    overlay_colors = {"sma_20": "#f7c548", "sma_50": "#ff9800", "ema_20": "#00bcd4", "ema_50": "#ab47bc"}
    names = {"sma_20": "SMA 20", "sma_50": "SMA 50", "ema_20": "EMA 20", "ema_50": "EMA 50"}
    for key, color in overlay_colors.items():
        if names[key] in selected and col(key) is not None:
            fig.add_trace(go.Scatter(x=df["dt"], y=col(key), mode="lines", name=names[key],
                                     line=dict(color=color, width=1.4), connectgaps=False), row=1, col=1)
    if "Bollinger Bands" in selected and col("bb_upper") is not None:
        fig.add_trace(go.Scatter(x=df["dt"], y=col("bb_lower"), mode="lines", name="BB lower",
                                 line=dict(color="#2196f3", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["dt"], y=col("bb_upper"), mode="lines", name="BB upper", fill="tonexty",
                                 fillcolor=_rgba("#2196f3", 0.08), line=dict(color="#2196f3", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["dt"], y=col("bb_middle"), mode="lines", name="BB basis",
                                 line=dict(color="#ff9800", width=1, dash="dot")), row=1, col=1)

    # ---- volume (overlay on the price pane, bottom ~20%)
    vis = df.tail(visible)
    if "Volume" in selected:
        colors = [_rgba(up, 0.45) if c >= o else _rgba(down, 0.45) for o, c in zip(df["open"], df["close"])]
        fig.add_trace(go.Bar(x=df["dt"], y=df["volume"], marker_color=colors, name="Volume", showlegend=False),
                      row=1, col=1, secondary_y=True)
        vmax = max(float(vis["volume"].max()), 1.0)
        fig.update_yaxes(range=[0, vmax * 5], showgrid=False, visible=False, secondary_y=True, row=1, col=1)
    else:
        fig.update_yaxes(visible=False, showgrid=False, secondary_y=True, row=1, col=1)

    # ---- RSI / MACD panes
    row = 2
    if show_rsi:
        fig.add_trace(go.Scatter(x=df["dt"], y=col("rsi_14"), mode="lines", name="RSI 14",
                                 line=dict(color="#7e57c2", width=1.5)), row=row, col=1)
        for lvl in (30, 70):
            fig.add_hline(y=lvl, line=dict(color=t["muted"], width=1, dash="dot"), row=row, col=1)
        fig.update_yaxes(range=[0, 100], tickvals=[30, 50, 70], side="right", row=row, col=1)
        row += 1
    if show_macd:
        hist = col("macd_histogram") or []
        fig.add_trace(go.Bar(x=df["dt"], y=hist, name="Histogram", showlegend=False,
                             marker_color=[_rgba(up if (h or 0) >= 0 else down, 0.6) for h in hist]), row=row, col=1)
        fig.add_trace(go.Scatter(x=df["dt"], y=col("macd"), mode="lines", name="MACD",
                                 line=dict(color="#2962ff", width=1.4)), row=row, col=1)
        fig.add_trace(go.Scatter(x=df["dt"], y=col("macd_signal"), mode="lines", name="Signal",
                                 line=dict(color="#ff9800", width=1.4)), row=row, col=1)
        fig.update_yaxes(side="right", row=row, col=1)

    # ---- last price tag
    last, prev = float(df["close"].iloc[-1]), float(df["open"].iloc[-1])
    tag = up if last >= prev else down
    fig.add_hline(y=last, line=dict(color=tag, width=1, dash="dot"), row=1, col=1)
    fig.add_annotation(x=1, xref="paper", y=last, yref="y", text=f"<b>{fmt_price(last)}</b>", showarrow=False,
                       xanchor="left", bgcolor=tag, font=dict(color="#fff", size=11), borderpad=3)

    # ---- initial viewport: last `visible` bars + a little empty space on the right
    bar = df["dt"].diff().median()
    x_range = [vis["dt"].iloc[0] - bar / 2, df["dt"].iloc[-1] + bar * 6]
    lo, hi = float(vis["low"].min()), float(vis["high"].max())
    for k in ("bb_lower", "bb_upper"):
        if "Bollinger Bands" in selected and col(k) is not None:
            vals = [v for v, d in zip(col(k), df["dt"]) if v is not None and d >= vis["dt"].iloc[0]]
            if vals:
                lo, hi = min(lo, min(vals)), max(hi, max(vals))
    pad = (hi - lo) * 0.06 or hi * 0.01
    fig.update_yaxes(range=[lo - pad, hi + pad], row=1, col=1, secondary_y=False)

    axis = dict(showgrid=True, gridcolor=t["grid"], zeroline=False, linecolor=t["border"], tickfont=dict(color=t["muted"], size=11),
                showspikes=True, spikemode="across", spikesnap="cursor", spikecolor=t["muted"], spikethickness=1, spikedash="dot")
    fig.update_xaxes(**axis, rangeslider_visible=False)
    fig.update_xaxes(range=x_range)
    fig.update_yaxes(**{**axis, "showspikes": True, "spikemode": "across"}, side="right", secondary_y=False)
    fig.update_layout(
        template=t["plotly"], height=height, margin=dict(l=8, r=70, t=34, b=8),
        paper_bgcolor=t["bg"], plot_bgcolor=t["bg"], font=dict(family="Inter, sans-serif", color=t["text"]),
        hovermode="x unified", hoverlabel=dict(bgcolor=t["panel"], bordercolor=t["border"], font=dict(color=t["text"], size=12)),
        dragmode="pan", showlegend=True, uirevision=f"{symbol}-{chart_type}",
        legend=dict(orientation="h", x=0, y=1.0, yanchor="bottom", itemsizing="constant", bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=t["muted"])),
        newshape=dict(line=dict(color=t["accent"], width=2)),
        xaxis_rangeslider_visible=False,
    )
    return fig


def _pref_cb(field: str, widget_key: str, indicators: bool = False):
    val = st.session_state.get(widget_key)
    if val is None:
        return
    state.save_settings(**{field: state.tokens_from_labels(val) if indicators else val})


def controls(key: str) -> tuple[str, str, list[str]]:
    """Timeframe pills, chart-type switch and indicator picker. Persisted to the user's settings."""
    s = state.settings()
    tf_key, ct_key, in_key = f"{key}_tf", f"{key}_ct", f"{key}_ind"
    st.session_state.setdefault(tf_key, s.get("timeframe", "1h"))
    st.session_state.setdefault(ct_key, s.get("chart_type", "candles"))
    st.session_state.setdefault(in_key, state.indicator_labels_from_tokens(s.get("indicators", "volume")))
    c1, c2, c3 = st.columns([5.2, 2.4, 3], vertical_alignment="center")
    with c1:
        st.pills("Timeframe", TIMEFRAMES, key=tf_key, format_func=TF_LABELS.get, label_visibility="collapsed",
                 on_change=_pref_cb, args=("timeframe", tf_key))
    with c2:
        st.segmented_control("Chart type", list(CHART_TYPES), key=ct_key, format_func=CHART_TYPES.get,
                             label_visibility="collapsed", on_change=_pref_cb, args=("chart_type", ct_key))
    with c3:
        st.multiselect("Indicators", list(INDICATOR_OPTIONS), key=in_key, placeholder="Indicators",
                       label_visibility="collapsed", on_change=_pref_cb, args=("indicators", in_key, True))
    tf = st.session_state.get(tf_key) or s.get("timeframe", "1h")
    ct = st.session_state.get(ct_key) or s.get("chart_type", "candles")
    return tf, ct, st.session_state.get(in_key) or []


REFRESH_SECONDS = 2


def _render_chart(symbol, key, tf, ct, selected, height):
    api = state.api()
    tokens = [INDICATOR_OPTIONS[l] for l in selected if l != "Volume"]
    hist = state.call(api.history, symbol, tf, 300)
    if not hist or not hist["candles"]:
        st.warning("No chart data available.")
        return
    series, ind_ts = {}, []
    if tokens:
        ind = state.call(api.indicators, symbol, tf, tokens, 300)
        if ind:
            series, ind_ts = ind["series"], ind["timestamps"]
    fig = build_figure(hist["candles"], series, ind_ts, symbol, ct, selected, height=height)
    st.plotly_chart(fig, config=PLOT_CONFIG, key=f"{key}_plot", width="stretch")


# Two variants of the same fragment: only the chart re-runs (zoom/pan are kept via uirevision).
_chart_live = st.fragment(run_every=REFRESH_SECONDS)(_render_chart)
_chart_static = st.fragment(_render_chart)


def chart_panel(symbol: str, key: str, height: int = 560, show_controls: bool = True,
                timeframe: str | None = None) -> None:
    if show_controls:
        tf, ct, selected = controls(key)
    else:
        s = state.settings()
        tf, ct = timeframe or s.get("timeframe", "1h"), s.get("chart_type", "candles")
        selected = state.indicator_labels_from_tokens(s.get("indicators", "volume"))
    live = st.toggle("● Live", value=True, key=f"{key}_live", help=f"Refresh the chart every {REFRESH_SECONDS} seconds")
    (_chart_live if live else _chart_static)(symbol, key, tf, ct, selected, height)


@st.fragment(run_every=REFRESH_SECONDS)
def live_header(symbol: str) -> None:
    q = state.call(state.api().asset, symbol, quiet=True)
    if q:
        symbol_header(q)


def symbol_header(q: dict) -> None:
    cls = pct_class(q["change_pct"])
    arrow = "▲" if q["change"] >= 0 else "▼"
    st.markdown(
        f"<div class='tv-symbol-head'><span class='sym'>{q['symbol']}</span><span class='nm'>{q['name']} · {q['category'].title()}</span>"
        f"<span class='px'>{fmt_price(q['price'])}</span>"
        f"<span class='{cls}' style='font-weight:600'>{arrow} {q['change']:+,.4f} ({q['change_pct']:+.2f}%)</span>"
        f"{source_badge(q['source'])}</div>", unsafe_allow_html=True)
