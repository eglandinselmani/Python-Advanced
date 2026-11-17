"""Custom CSS that turns Streamlit into a TradingView-style terminal (theme aware)."""
import streamlit as st

from frontend.config import THEMES

LOGO_SVG = ("<svg width='26' height='26' viewBox='0 0 26 26' fill='none'><rect width='26' height='26' rx='7' fill='#2962ff'/>"
            "<path d='M8 6v14M8 9h0M8 9v7' stroke='#fff' stroke-width='1.6' stroke-linecap='round'/>"
            "<rect x='6' y='9' width='4' height='7' rx='1' fill='#fff'/>"
            "<path d='M17 5v15' stroke='#fff' stroke-width='1.6' stroke-linecap='round'/>"
            "<rect x='15' y='8' width='4' height='8' rx='1' fill='#fff' fill-opacity='.55'/></svg>")


def inject(theme_name: str) -> None:
    t = THEMES.get(theme_name, THEMES["dark"])
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {{ --bg:{t['bg']}; --panel:{t['panel']}; --panel2:{t['panel2']}; --border:{t['border']}; --text:{t['text']};
        --muted:{t['muted']}; --accent:{t['accent']}; --up:{t['up']}; --down:{t['down']}; --hover:{t['hover']}; --input:{t['input']}; }}
html, body, [class*="css"], .stApp, button, input, textarea {{ font-family:'Inter',-apple-system,'Segoe UI',Roboto,sans-serif !important; }}
.stApp {{ background:var(--bg); color:var(--text); }}
.stApp, .stApp p, .stApp label, .stApp span, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp div[data-testid="stMarkdownContainer"] {{ color:var(--text); }}
[data-testid="stToolbar"], #MainMenu, footer {{ display:none !important; }}
header[data-testid="stHeader"] {{ background:transparent !important; height:2.2rem; }}
.block-container {{ padding:0.6rem 1.1rem 2rem 1.1rem !important; max-width:100% !important; }}
h1,h2,h3 {{ font-weight:600 !important; letter-spacing:-0.01em; }}
h1 {{ font-size:1.5rem !important; }} h2 {{ font-size:1.2rem !important; }} h3 {{ font-size:1rem !important; }}
hr {{ border-color:var(--border) !important; margin:0.6rem 0 !important; }}

/* ---------- left toolbar (sidebar) ---------- */
[data-testid="stSidebar"] {{ background:var(--panel) !important; border-right:1px solid var(--border); width:196px !important; min-width:196px !important; }}
[data-testid="stSidebar"] > div:first-child {{ width:196px !important; }}
[data-testid="stSidebarContent"] {{ padding:0.5rem 0.55rem !important; }}
[data-testid="stSidebar"] .stButton > button {{ width:100%; justify-content:flex-start; background:transparent; border:none; color:var(--muted);
    padding:0.5rem 0.7rem; border-radius:8px; font-weight:500; font-size:0.9rem; gap:0.6rem; box-shadow:none; }}
[data-testid="stSidebar"] .stButton > button:hover {{ background:var(--hover); color:var(--text); }}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{ background:rgba(41,98,255,.16); color:var(--accent); font-weight:600; }}
[data-testid="stSidebar"] .stButton > button p {{ color:inherit !important; }}
.tv-brand {{ display:flex; align-items:center; gap:.55rem; padding:.35rem .5rem 1rem .5rem; font-weight:700; font-size:1.2rem; letter-spacing:-.02em; color:var(--text); }}
.tv-brand small {{ display:block; font-size:.62rem; font-weight:500; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; }}
.tv-side-label {{ font-size:.66rem; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); padding:.8rem .6rem .25rem; }}

/* ---------- buttons / inputs ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{ background:var(--panel2); color:var(--text); border:1px solid var(--border); border-radius:6px;
    font-weight:500; transition:all .15s ease; min-height:2.2rem; }}
.stButton > button:hover, .stFormSubmitButton > button:hover {{ border-color:var(--accent); color:var(--accent); background:var(--panel2); }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{ background:var(--accent); border-color:var(--accent); color:#fff; }}
.stButton > button[kind="primary"]:hover {{ filter:brightness(1.12); color:#fff; }}
.stButton > button[kind="tertiary"] {{ background:transparent; border:none; padding:.1rem .2rem; justify-content:flex-start; font-weight:600; }}
.stButton > button[kind="tertiary"]:hover {{ color:var(--accent); background:transparent; }}
.stButton > button p {{ color:inherit !important; }}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, .stNumberInput input, .stTextInput input, textarea {{ background:var(--input) !important; border-color:var(--border) !important; color:var(--text) !important; border-radius:6px !important; }}
div[data-baseweb="select"] span, div[data-baseweb="select"] div, input {{ color:var(--text) !important; }}
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] > div, div[data-baseweb="menu"] {{ background:var(--panel) !important; color:var(--text) !important; }}
li[role="option"]:hover {{ background:var(--hover) !important; }}
[data-baseweb="tag"] {{ background:var(--panel2) !important; }}
.stNumberInput button {{ background:var(--panel2) !important; color:var(--text) !important; border-color:var(--border) !important; }}
[data-testid="stPills"] button, [data-testid="stSegmentedControl"] button {{ background:transparent; border:1px solid transparent; color:var(--muted); font-weight:500; border-radius:6px; padding:.15rem .55rem; min-height:1.9rem; }}
[data-testid="stPills"] button[aria-checked="true"], [data-testid="stPills"] button[aria-pressed="true"], [data-testid="stSegmentedControl"] button[aria-checked="true"], [data-testid="stSegmentedControl"] button[aria-pressed="true"] {{ background:rgba(41,98,255,.18); color:var(--accent); border-color:transparent; }}
[data-testid="stSegmentedControl"] {{ background:var(--panel); border-radius:8px; }}
.stRadio label, .stCheckbox label {{ color:var(--text) !important; }}

/* ---- Streamlit >=1.5x widgets (react-aria based) ---- */
[data-rac][role="group"], [data-testid="stTextInput"] [data-baseweb], [data-testid="stNumberInput"] [data-baseweb] {{ background:var(--input) !important; border:1px solid var(--border) !important; border-radius:6px !important; }}
[data-rac][role="group"] input, [data-rac][role="group"] button {{ background:transparent !important; color:var(--text) !important; }}
[data-rac][role="group"] svg {{ color:var(--muted) !important; fill:var(--muted); }}
[role="listbox"], [role="listbox"] [role="option"], [data-rac][role="dialog"] {{ background:var(--panel) !important; color:var(--text) !important; }}
[role="listbox"] [role="option"]:hover, [role="option"][data-focused="true"], [role="option"][data-hovered="true"] {{ background:var(--hover) !important; }}
[role="listbox"] *, [role="option"] * {{ color:var(--text); }}
[data-testid="stButtonGroup"] button {{ background:transparent !important; color:var(--muted) !important; border:1px solid var(--border) !important; border-radius:6px; font-weight:500; min-height:1.9rem; }}
[data-testid="stButtonGroup"] button p {{ color:inherit !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[aria-pressed="true"], [data-testid="stButtonGroup"] button[data-selected="true"] {{ background:rgba(41,98,255,.16) !important; color:var(--accent) !important; border-color:var(--accent) !important; }}
[data-testid="stPopover"] > div > button, [data-testid="stPopoverButton"] {{ background:var(--panel2) !important; color:var(--text) !important; border:1px solid var(--border) !important; }}
[data-testid="stPopover"] button p, [data-testid="stPopover"] button svg {{ color:inherit !important; }}
[data-testid="stPopoverBody"], div[data-testid="stPopoverBody"] > div {{ background:var(--panel) !important; color:var(--text); border:1px solid var(--border); }}
[data-testid="stNumberInputContainer"], [data-testid="stNumberInputContainer"] > div, [data-testid="stNumberInput"] [data-baseweb="input"] {{ background:var(--input) !important; border-color:var(--border) !important; border-radius:6px; }}
input::placeholder, textarea::placeholder {{ color:var(--muted) !important; opacity:1 !important; }}
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {{ background:transparent !important; color:var(--text) !important; }}
[data-testid="stNumberInput"] button {{ background:var(--panel2) !important; color:var(--text) !important; }}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button {{ border:none !important; }}
[class*="st-key-wlrow"] [data-testid="stPopover"] > div > button {{ background:transparent !important; border:none !important; }}
[data-testid="stTable"] td, [data-testid="stDataFrame"] {{ color:var(--text); }}

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{ gap:.25rem; border-bottom:1px solid var(--border); }}
.stTabs [data-baseweb="tab"] {{ color:var(--muted); font-weight:500; padding:.5rem .9rem; background:transparent; }}
.stTabs [aria-selected="true"] {{ color:var(--text) !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:var(--accent) !important; height:2px; }}

/* ---------- cards ---------- */
.tv-card {{ background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:.75rem .95rem; }}
.tv-card .lbl {{ color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; font-weight:500; }}
.tv-card .val {{ font-size:1.35rem; font-weight:600; margin-top:.15rem; font-variant-numeric:tabular-nums; }}
.tv-card .sub {{ font-size:.8rem; margin-top:.1rem; font-variant-numeric:tabular-nums; }}
.tv-up {{ color:var(--up) !important; }} .tv-down {{ color:var(--down) !important; }} .tv-muted {{ color:var(--muted) !important; }}
.tv-badge {{ display:inline-block; padding:.12rem .5rem; border-radius:20px; font-size:.68rem; font-weight:600; letter-spacing:.04em; }}
.tv-badge.sim {{ background:rgba(255,152,0,.15); color:#ff9800 !important; border:1px solid rgba(255,152,0,.4); }}
.tv-badge.live {{ background:rgba(8,153,129,.15); color:var(--up) !important; border:1px solid rgba(8,153,129,.4); }}
.tv-symbol-head {{ display:flex; align-items:baseline; gap:.8rem; flex-wrap:wrap; padding:.1rem .2rem .3rem; }}
.tv-symbol-head .sym {{ font-size:1.25rem; font-weight:700; }} .tv-symbol-head .nm {{ color:var(--muted); font-size:.85rem; }}
.tv-symbol-head .px {{ font-size:1.5rem; font-weight:600; font-variant-numeric:tabular-nums; }}
.tv-panel-title {{ font-size:.72rem; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); font-weight:600; padding:.15rem .1rem .35rem; }}
.tv-row {{ display:flex; justify-content:space-between; align-items:center; padding:.32rem .1rem; border-bottom:1px solid var(--border); font-size:.86rem; font-variant-numeric:tabular-nums; }}
.tv-row:last-child {{ border-bottom:none; }}
.tv-banner {{ background:rgba(255,152,0,.1); border:1px solid rgba(255,152,0,.35); color:#ff9800; border-radius:8px; padding:.45rem .8rem; font-size:.8rem; margin-bottom:.6rem; }}
.tv-banner b {{ color:#ff9800; }}
.tv-ticker {{ display:flex; flex-direction:column; gap:.05rem; }}
.tv-ticker .t1 {{ font-weight:600; font-size:.82rem; }} .tv-ticker .t2 {{ font-size:.95rem; font-variant-numeric:tabular-nums; font-weight:500; }} .tv-ticker .t3 {{ font-size:.76rem; font-variant-numeric:tabular-nums; }}
.tv-auth {{ max-width:430px; margin:6vh auto 0; }}
.tv-hero {{ text-align:center; margin-bottom:1.2rem; }} .tv-hero h1 {{ font-size:2rem !important; margin:.4rem 0 .2rem; }} .tv-hero p {{ color:var(--muted); }}

/* ---------- compact watchlist rows ---------- */
.wl-head {{ display:flex; justify-content:space-between; color:var(--muted); font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; padding:.2rem .3rem; border-bottom:1px solid var(--border); }}
[class*="st-key-wlrow"] div[data-testid="stHorizontalBlock"] {{ gap:.2rem; align-items:center; border-bottom:1px solid var(--border); padding:.05rem 0; }}
[class*="st-key-wlrow"] div[data-testid="stHorizontalBlock"]:hover {{ background:var(--hover); }}
[class*="st-key-wlrow"] [data-testid="stVerticalBlock"] {{ gap:0 !important; }}
[class*="st-key-wlrow"] [data-testid="stPopover"] svg:last-of-type:not(:first-of-type) {{ display:none; }}
[class*="st-key-wlrow"] .stButton > button {{ min-height:1.8rem; padding:.1rem .3rem; }}
.wl-row {{ font-size:.84rem; font-variant-numeric:tabular-nums; text-align:right; line-height:1.15; }}
.wl-row small {{ color:var(--muted); }}

[data-testid="stDataFrame"] {{ border:1px solid var(--border); border-radius:8px; }}
[data-testid="stMetric"] {{ background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:.6rem .8rem; }}
[data-testid="stMetricLabel"] p {{ color:var(--muted) !important; font-size:.75rem; }}
[data-testid="stExpander"] {{ background:var(--panel); border:1px solid var(--border); border-radius:8px; }}
[data-testid="stForm"] {{ background:var(--panel); border:1px solid var(--border); border-radius:10px; }}
[data-testid="stAlert"] {{ border-radius:8px; }}
[data-testid="stPopover"] > div > button {{ border-radius:20px; }}
::-webkit-scrollbar {{ width:8px; height:8px; }} ::-webkit-scrollbar-thumb {{ background:var(--panel2); border-radius:4px; }}
@media (max-width: 900px) {{ .block-container {{ padding:.5rem .5rem 2rem !important; }} .tv-symbol-head .px {{ font-size:1.2rem; }} }}
</style>""", unsafe_allow_html=True)


def pct_class(v: float) -> str:
    return "tv-up" if v > 0 else "tv-down" if v < 0 else "tv-muted"


def fmt_price(p: float) -> str:
    if p >= 1000: return f"{p:,.2f}"
    if p >= 100: return f"{p:,.2f}"
    if p >= 10: return f"{p:,.3f}"
    if p >= 1: return f"{p:,.4f}"
    return f"{p:,.5f}"


def money(v: float, signed: bool = False) -> str:
    return f"{'+' if signed and v > 0 else ''}{'-' if v < 0 else ''}${abs(v):,.2f}"


def source_badge(source: str) -> str:
    if source == "live":
        return "<span class='tv-badge live'>LIVE</span>"
    return "<span class='tv-badge sim'>SIMULATED</span>"
