"""
JST ALPHA — Dashboard de Trading con IA
Tema: Negro profundo · Oro · Blanco institucional
Inspirado en terminales BTG Pactual / BICE Inversiones
Ejecutar: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime

# ── Auto-setup en Streamlit Community Cloud ────────────────────
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_IS_CLOUD = not os.path.exists(os.path.join(_BASE, "data", "indices", "SP500.csv"))
if _IS_CLOUD:
    try:
        import sys; sys.path.insert(0, _BASE)
        import setup_cloud  # noqa: F401
    except Exception:
        pass

try:
    import pytz
    _PYTZ_OK = True
except ImportError:
    _PYTZ_OK = False

st.set_page_config(
    page_title="JST Alpha · Trading Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PWA: manifest + service worker + viewport ──────────────
st.markdown("""
<link rel="manifest" href="app/static/manifest.json">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="JST Alpha">
<meta name="theme-color" content="#c5a860">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="apple-touch-icon" href="app/static/icon-192.png">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('app/static/sw.js')
      .then(r => console.log('SW registrado:', r.scope))
      .catch(e => console.warn('SW error:', e));
  });
}
</script>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ══════════════════════════════════════════════════════════════════
# MARKET STATUS
# ══════════════════════════════════════════════════════════════════

def get_market_status():
    try:
        if _PYTZ_OK:
            now_et = datetime.now(pytz.timezone("America/New_York"))
        else:
            from datetime import timezone, timedelta
            now_et = datetime.now(timezone(timedelta(hours=-4)))
        market_open = (
            now_et.weekday() < 5
            and (9 * 60 + 30) <= (now_et.hour * 60 + now_et.minute) <= (16 * 60)
        )
    except Exception:
        market_open = False
    status_color = "#00cc55" if market_open else "#cc3300"
    status_text  = "MERCADO ABIERTO" if market_open else "MERCADO CERRADO"
    return status_color, status_text


# ══════════════════════════════════════════════════════════════════
# CSS — TEMA TERMINAL FINANCIERO OSCURO
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Inter:wght@300;400;500;600&display=swap');

/* ════════════════════════════════════════════════════════
   PALETA JST ALPHA (idéntica al reporte PDF)
   Fondo:   #f8f7f4  (crema cálido)
   Tarjeta: #ffffff  con borde dorado
   Mármol:  gradiente crema/beige
   Texto:   #0a0a0a  (casi negro)
   Label:   #6b5a2a  (marrón dorado legible)
   Positivo:#0066cc  (azul institucional)
   Negativo:#cc3300  (rojo institucional)
   Oro:     #c5a860
   Sidebar: #0a0a0a  (negro)
════════════════════════════════════════════════════════ */

/* ── BASE ─────────────────────────────────────────────── */
html, body, .stApp {
    background: #f8f7f4 !important;
    font-family: 'Inter', sans-serif;
    color: #0a0a0a;
}
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 100%;
}

/* ── SIDEBAR (negro, igual que header PDF) ────────────── */
[data-testid="stSidebar"] {
    background: #0a0a0a !important;
    border-right: 1px solid rgba(197,168,96,0.2) !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
/* Forzar todo texto del sidebar a blanco — override del color: #0a0a0a del body */
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .sidebar-logo-title span { color: #c5a860 !important; }
[data-testid="stSidebar"] .sidebar-logo-sub { color: rgba(197,168,96,0.55) !important; }
[data-testid="stSidebar"] .sidebar-clock-date { color: rgba(197,168,96,0.6) !important; }
[data-testid="stSidebar"] .stRadio label { color: rgba(197,168,96,0.7) !important; }
[data-testid="stSidebar"] .sidebar-footer { color: rgba(197,168,96,0.35) !important; }

.sidebar-logo {
    padding: 22px 20px 14px;
    border-bottom: 1px solid rgba(197,168,96,0.2);
    margin-bottom: 10px;
}
.sidebar-logo-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem; font-weight: 800;
    color: #ffffff;                       /* blanco sobre negro */
    letter-spacing: 6px; text-transform: uppercase; line-height: 1;
}
.sidebar-logo-title span { color: #c5a860; }
.sidebar-logo-sub {
    font-size: 0.56rem; color: rgba(197,168,96,0.55);
    letter-spacing: 3px; text-transform: uppercase;
    margin-top: 5px; font-weight: 400;
}
.sidebar-clock { padding: 10px 20px 8px; border-bottom: 1px solid rgba(197,168,96,0.12); margin-bottom: 8px; }
.sidebar-clock-time { font-size: 1.05rem; font-weight: 600; color: #ffffff; letter-spacing: 2px; }
.sidebar-clock-date { font-size: 0.6rem; color: rgba(197,168,96,0.6); letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }

[data-testid="stSidebar"] .stRadio > div { display: flex; flex-direction: column; gap: 3px; padding: 0 12px; }
[data-testid="stSidebar"] .stRadio label {
    padding: 10px 14px !important; border-radius: 4px !important; cursor: pointer !important;
    color: rgba(197,168,96,0.7) !important; font-size: 0.74rem !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
    border: 1px solid transparent !important; font-weight: 500 !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(197,168,96,0.08) !important;
    border-color: rgba(197,168,96,0.3) !important;
    color: #c5a860 !important;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p { color: inherit !important; }

/* Botones de nav sidebar — estilo menu item */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: rgba(197,168,96,0.7) !important;
    border: 1px solid transparent !important;
    border-radius: 4px !important;
    font-size: 0.74rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(197,168,96,0.08) !important;
    border-color: rgba(197,168,96,0.3) !important;
    color: #c5a860 !important;
}

.sidebar-footer {
    padding: 12px 20px; border-top: 1px solid rgba(197,168,96,0.15);
    font-size: 0.58rem; color: rgba(197,168,96,0.35);
    letter-spacing: 2px; text-transform: uppercase; margin-top: 16px;
}

/* ── SECTION LABEL (igual que encabezado de tabla PDF) ── */
.section-header {
    font-size: 0.62rem; letter-spacing: 3px; text-transform: uppercase;
    color: #a07820; font-weight: 700;
    padding: 6px 0 7px;
    border-bottom: 1.5px solid rgba(197,168,96,0.35);
    margin-bottom: 10px;
}

/* ── TARJETA ESTÁNDAR (fondo blanco, borde dorado) ─────── */
.card {
    background: #ffffff;
    border: 1.5px solid rgba(197,168,96,0.4);
    border-top: 2.5px solid #c5a860;
    border-radius: 5px;
    padding: 14px 16px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(197,168,96,0.08);
}
.card-label {
    font-size: 0.6rem; letter-spacing: 3px; text-transform: uppercase;
    color: #6b5a2a; font-weight: 700;
}
.card-value {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem; font-weight: 800; color: #0a0a0a;
    margin: 5px 0 4px; letter-spacing: 0.5px;
}
.card-pos { color: #0066cc; font-size: 0.8rem; font-weight: 700; }
.card-neg { color: #cc3300; font-size: 0.8rem; font-weight: 700; }

/* mantener clase antigua para no romper código existente */
.dark-card { background:#ffffff; border:1.5px solid rgba(197,168,96,0.4); border-top:2.5px solid #c5a860; border-radius:5px; padding:14px 16px; margin-bottom:10px; box-shadow:0 2px 8px rgba(197,168,96,0.08); }
.dark-card-label { font-size:0.6rem; letter-spacing:3px; text-transform:uppercase; color:#6b5a2a; font-weight:700; }
.dark-card-value { font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:800; color:#0a0a0a; margin:5px 0 4px; }
.dark-card-change-pos { color:#0066cc; font-size:0.8rem; font-weight:700; }
.dark-card-change-neg { color:#cc3300; font-size:0.8rem; font-weight:700; }

/* ── METRIC CONTAINERS (st.metric) ─────────────────────── */
[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1.5px solid rgba(197,168,96,0.35) !important;
    border-top: 2.5px solid #c5a860 !important;
    border-radius: 5px !important;
    padding: 12px 16px !important;
    box-shadow: 0 2px 8px rgba(197,168,96,0.07) !important;
}
[data-testid="metric-container"] label {
    color: #6b5a2a !important;
    font-size: 0.6rem !important; letter-spacing: 2px !important;
    text-transform: uppercase !important; font-weight: 700 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0a0a0a !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 1.3rem !important; font-weight: 800 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] { color: #0066cc !important; }

/* ── BUTTONS (períodos) ─────────────────────────────────── */
.stButton > button {
    background: #ffffff !important; color: #6b5a2a !important;
    border: 1.5px solid rgba(197,168,96,0.45) !important;
    border-radius: 3px !important; font-size: 0.72rem !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
    font-weight: 600 !important; padding: 6px 10px !important;
}
.stButton > button:hover {
    background: #c5a860 !important; color: #0a0a0a !important;
    border-color: #c5a860 !important; font-weight: 700 !important;
}

/* ── TABS ───────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1.5px solid rgba(197,168,96,0.25); }
.stTabs [data-baseweb="tab"] {
    color: #6b5a2a !important; font-size: 0.72rem; letter-spacing: 2px;
    text-transform: uppercase; padding: 10px 18px; background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #0a0a0a !important; font-weight: 700 !important;
    border-bottom: 2.5px solid #c5a860 !important;
    background: rgba(197,168,96,0.07) !important;
    border-radius: 3px 3px 0 0 !important;
}

/* ── INPUTS ─────────────────────────────────────────────── */
.stSelectbox label, .stTextInput label {
    color: #6b5a2a !important; font-size: 0.65rem !important;
    letter-spacing: 2px !important; text-transform: uppercase !important; font-weight: 700 !important;
}
.stCheckbox label { color: #0a0a0a !important; font-size: 0.8rem !important; font-weight: 500 !important; }
.stTextInput input {
    background: #ffffff !important; border: 1.5px solid rgba(197,168,96,0.4) !important;
    color: #0a0a0a !important; border-radius: 3px !important;
}

/* ── HEADINGS ───────────────────────────────────────────── */
h1, h2, h3, h4 {
    color: #0a0a0a !important;
    font-family: 'Playfair Display', serif !important; letter-spacing: 1px;
}
h3 { font-size: 1.1rem !important; }
h4 { font-size: 0.95rem !important; }
p, label, .stMarkdown p { color: #0a0a0a !important; }

/* ── NEWS CARDS ─────────────────────────────────────────── */
.noticia-row {
    background: #ffffff; border-radius: 4px; padding: 13px 16px; margin-bottom: 8px;
    border: 1px solid rgba(197,168,96,0.25); border-left: 3px solid #c5a860;
    box-shadow: 0 1px 4px rgba(197,168,96,0.06);
}
.noticia-titulo { color: #0a0a0a; font-size: 0.87rem; font-weight: 500; line-height: 1.45; }
.noticia-meta   { color: #6b5a2a; font-size: 0.68rem; margin-top: 5px; letter-spacing: 1px; text-transform: uppercase; }

/* ── BADGES ─────────────────────────────────────────────── */
.badge-compra-fuerte { background:rgba(0,102,204,0.1); color:#0066cc; border:1px solid rgba(0,102,204,0.4); padding:4px 14px; border-radius:3px; font-size:0.73rem; font-weight:700; }
.badge-compra        { background:rgba(0,102,204,0.06); color:#0066cc; border:1px solid rgba(0,102,204,0.25); padding:4px 14px; border-radius:3px; font-size:0.73rem; font-weight:600; }
.badge-neutral       { background:rgba(107,90,42,0.08); color:#6b5a2a; border:1px solid rgba(197,168,96,0.35); padding:4px 14px; border-radius:3px; font-size:0.73rem; font-weight:600; }
.badge-venta         { background:rgba(204,51,0,0.08); color:#cc3300; border:1px solid rgba(204,51,0,0.3); padding:4px 14px; border-radius:3px; font-size:0.73rem; font-weight:600; }
.badge-venta-fuerte  { background:rgba(204,51,0,0.12); color:#cc3300; border:1px solid rgba(204,51,0,0.45); padding:4px 14px; border-radius:3px; font-size:0.73rem; font-weight:700; }

/* ── DATAFRAME ──────────────────────────────────────────── */
.stDataFrame { border: 1.5px solid rgba(197,168,96,0.25) !important; border-radius: 5px !important; }

/* ── ALERTS ─────────────────────────────────────────────── */
.stAlert { background:#fffdf5 !important; border:1px solid rgba(197,168,96,0.3) !important; color:#0a0a0a !important; border-radius:4px !important; }

/* ── SCROLLBAR ──────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f0ede6; }
::-webkit-scrollbar-thumb { background: rgba(197,168,96,0.35); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #c5a860; }

hr { border-color: rgba(197,168,96,0.25) !important; }

/* ── INDICATOR CHIP ─────────────────────────────────────── */
.ind-chip {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 11px; border-radius: 3px;
    border: 1.5px solid rgba(197,168,96,0.35);
    font-size: 0.7rem; letter-spacing: 1px;
    color: #0a0a0a; font-weight: 600;
    background: #ffffff; cursor: pointer;
}
.ind-chip:hover { background: rgba(197,168,96,0.12); border-color: #c5a860; }

/* ════════════════════════════════════════════════════════
   MOBILE — iPhone / Android (breakpoint 768px)
════════════════════════════════════════════════════════ */
@media (max-width: 768px) {

  /* ── Contenedor sin padding excesivo ── */
  .main .block-container {
    padding: 0.4rem 0.5rem 2rem !important;
    max-width: 100vw !important;
  }

  /* ── Ocultar header de Streamlit en mobile ── */
  header[data-testid="stHeader"] { display: none !important; }
  #MainMenu { visibility: hidden !important; }
  footer    { display: none !important; }

  /* ── Sidebar compacta ── */
  [data-testid="stSidebar"] {
    min-width: 80vw !important;
    max-width: 80vw !important;
  }
  .sidebar-logo { padding: 16px 14px 12px; }
  .sidebar-logo-title { font-size: 1.2rem !important; letter-spacing: 4px; }
  .sidebar-logo-sub   { font-size: 0.52rem !important; }
  [data-testid="stSidebar"] .stRadio label {
    font-size: 0.82rem !important;
    padding: 12px 14px !important;
    letter-spacing: 1px !important;
  }

  /* ── Cards ── */
  .card, .dark-card {
    padding: 12px 14px !important;
    margin-bottom: 10px !important;
    border-radius: 8px !important;
  }
  .card-value, .dark-card-value { font-size: 1.2rem !important; }
  .card-label, .dark-card-label { font-size: 0.58rem !important; }

  /* ── Métricas st.metric ── */
  [data-testid="metric-container"] {
    padding: 10px 12px !important;
    border-radius: 8px !important;
    margin-bottom: 8px !important;
  }
  [data-testid="metric-container"] label {
    font-size: 0.55rem !important;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.1rem !important;
  }

  /* ── Botones (período / barra) — touch-friendly ── */
  .stButton > button {
    min-height: 40px !important;
    font-size: 0.7rem !important;
    padding: 8px 6px !important;
    letter-spacing: 1px !important;
    border-radius: 6px !important;
  }

  /* ── Columns con scroll horizontal cuando no caben ── */
  div[data-testid="stHorizontalBlock"] {
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    -webkit-overflow-scrolling: touch !important;
    scrollbar-width: none !important;
    padding-bottom: 4px !important;
  }
  div[data-testid="stHorizontalBlock"]::-webkit-scrollbar { display: none !important; }

  /* ── Ticker bar ── */
  .ticker-bar {
    font-size: 0.68rem !important;
    padding: 7px 12px !important;
  }

  /* ── Section headers ── */
  .section-header {
    font-size: 0.6rem !important;
    letter-spacing: 2px !important;
    padding: 8px 0 8px !important;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    -webkit-overflow-scrolling: touch !important;
  }
  .stTabs [data-baseweb="tab"] {
    font-size: 0.68rem !important;
    padding: 10px 12px !important;
    letter-spacing: 0.5px !important;
    white-space: nowrap !important;
  }

  /* ── Gráfico Plotly ── */
  .js-plotly-plot .plotly, .js-plotly-plot { min-height: 300px !important; }

  /* ── Selectbox / Inputs ── */
  .stSelectbox > div > div { font-size: 0.8rem !important; }
  .stTextInput input { font-size: 0.85rem !important; min-height: 40px !important; }
  .stCheckbox label { font-size: 0.78rem !important; }
  .stCheckbox { min-height: 36px !important; display: flex !important; align-items: center !important; }

  /* ── Noticias ── */
  .noticia-row { padding: 12px 14px !important; border-radius: 8px !important; }
  .noticia-titulo { font-size: 0.85rem !important; line-height: 1.5 !important; }
  .noticia-meta   { font-size: 0.65rem !important; }

  /* ── Dataframe ── */
  .stDataFrame { font-size: 0.75rem !important; border-radius: 8px !important; }

  /* ── Headings de página ── */
  h1 { font-size: 1.3rem !important; }
  h2 { font-size: 1.1rem !important; }

  /* ── Análisis multitemporal — scroll horizontal en mobile ── */
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 110px !important;
  }

  /* ── HR separadores ── */
  hr { margin: 8px 0 !important; }
}

/* ── iPhone SE / pantallas muy pequeñas ── */
@media (max-width: 390px) {
  .main .block-container { padding: 0.3rem 0.3rem 80px !important; }
  .card-value, .dark-card-value { font-size: 1rem !important; }
  [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 0.95rem !important; }
  .stButton > button { font-size: 0.62rem !important; min-height: 38px !important; }
  .sidebar-logo-title { font-size: 1rem !important; }
}

/* ── Padding bottom para no quedar detrás del bottom nav ── */
@media (max-width: 768px) {
  .main .block-container { padding-bottom: 80px !important; }
  /* Gráfico más compacto en mobile */
  .js-plotly-plot .plotly svg { max-height: 380px !important; }
}

/* ════════════════════════════════════════════════════════
   BOTTOM NAV BAR — solo mobile
════════════════════════════════════════════════════════ */
.jst-bottom-nav {
  display: none;
}
@media (max-width: 768px) {
  .jst-bottom-nav {
    display: flex !important;
    position: fixed;
    bottom: 0; left: 0; right: 0;
    z-index: 99999;
    background: #0a0a0a;
    border-top: 1.5px solid rgba(197,168,96,0.3);
    height: 62px;
    align-items: stretch;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.5);
    -webkit-backdrop-filter: blur(10px);
    backdrop-filter: blur(10px);
  }
  .jst-bnav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-decoration: none !important;
    color: rgba(197,168,96,0.45) !important;
    font-size: 0.52rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    gap: 3px;
    padding: 6px 2px;
    border: none;
    background: none;
    transition: color 0.15s, background 0.15s;
    -webkit-tap-highlight-color: transparent;
  }
  .jst-bnav-item:active { background: rgba(197,168,96,0.1); }
  .jst-bnav-item.active {
    color: #c5a860 !important;
    border-top: 2px solid #c5a860;
  }
  .jst-bnav-icon {
    font-size: 1.25rem;
    line-height: 1;
  }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# HELPERS DE CARGA
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def cargar_csv(ruta, skiprows=None):
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        kw = {"index_col": 0, "parse_dates": True}
        if skiprows:
            kw["skiprows"] = skiprows
        df = pd.read_csv(ruta, **kw)
        df = df[pd.to_datetime(df.index, errors="coerce").notna()]
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def cargar_hoja(ruta, hoja):
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        return pd.read_excel(ruta, sheet_name=hoja)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def cargar_noticias():
    ruta = os.path.join(DATA_DIR, "noticias", "noticias_hoy.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        return pd.read_csv(ruta, encoding="utf-8-sig").head(100)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120)
def cargar_social(tipo=None):
    ruta = os.path.join(DATA_DIR, "social", "social_hoy.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ruta, encoding="utf-8-sig")
        return df[df["Tipo"] == tipo] if tipo else df
    except Exception:
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════════
# INDICADORES TÉCNICOS
# ══════════════════════════════════════════════════════════════════

def ema(s, p):
    return s.ewm(span=p, adjust=False).mean()

def sma(s, p):
    return s.rolling(p).mean()

def rsi(s, p=14):
    d = s.diff()
    g = d.clip(lower=0)
    l = (-d).clip(lower=0)
    return 100 - 100 / (1 + g.ewm(com=p - 1, min_periods=p).mean() / l.ewm(com=p - 1, min_periods=p).mean())

def macd(s):
    m = ema(s, 12) - ema(s, 26)
    sig = ema(m, 9)
    return m, sig, m - sig

def bollinger(s, p=20, k=2):
    m = sma(s, p)
    std = s.rolling(p).std()
    return m + k * std, m, m - k * std

def fibonacci(high, low):
    mx, mn = high.max(), low.min()
    r = mx - mn
    return {
        "100%":  round(mx, 2),
        "78.6%": round(mx - .236 * r, 2),
        "61.8%": round(mx - .382 * r, 2),
        "50.0%": round(mx - .5   * r, 2),
        "38.2%": round(mx - .618 * r, 2),
        "23.6%": round(mx - .764 * r, 2),
        "0%":    round(mn, 2),
    }

def td_sequential(close, high, low):
    """
    TD Sequential — FASE 1 SETUP únicamente.

    SELL Setup: close[i] >= close[i-4] durante 9 consecutivas → tendencia alcista agotada
    BUY  Setup: close[i] <  close[i-4] durante 9 consecutivas → tendencia bajista agotada
    Si una vela rompe la condición → conteo reinicia desde 0.
    Solo se marca cuando la secuencia de 9 se completa.
    """
    n = len(close)
    c = close.values

    sell_s    = np.zeros(n, int)
    buy_s     = np.zeros(n, int)
    setup_sig = [""] * n

    sell_cnt = 0
    buy_cnt  = 0

    for i in range(4, n):

        if c[i] >= c[i - 4]:
            sell_cnt += 1
            buy_cnt   = 0
        else:
            buy_cnt  += 1
            sell_cnt  = 0

        sell_s[i] = min(sell_cnt, 9)
        buy_s[i]  = min(buy_cnt,  9)

        if sell_cnt == 9:
            setup_sig[i] = "▼ TD SELL SETUP 9"
            sell_cnt = 0

        elif buy_cnt == 9:
            setup_sig[i] = "▲ TD BUY SETUP 9"
            buy_cnt = 0

    empty   = pd.Series(np.zeros(n, int), index=close.index)
    empty_s = pd.Series([""] * n,         index=close.index)
    return (
        pd.Series(buy_s,     index=close.index),
        pd.Series(sell_s,    index=close.index),
        empty,
        empty,
        pd.Series(setup_sig, index=close.index),
        empty_s,
    )


def adx(high, low, close, p=14):
    """Average Directional Index — retorna (ADX, +DI, -DI)."""
    h = high.values; l = low.values; c = close.values
    n = len(c)
    tr = np.zeros(n); pdm = np.zeros(n); ndm = np.zeros(n)
    for i in range(1, n):
        hl = h[i] - l[i]
        hpc = abs(h[i] - c[i-1])
        lpc = abs(l[i] - c[i-1])
        tr[i] = max(hl, hpc, lpc)
        up = h[i] - h[i-1]; dn = l[i-1] - l[i]
        pdm[i] = up if (up > dn and up > 0) else 0
        ndm[i] = dn if (dn > up and dn > 0) else 0
    def wilder_smooth(arr, n):
        out = np.zeros(len(arr))
        out[n] = arr[1:n+1].sum()
        for i in range(n+1, len(arr)):
            out[i] = out[i-1] - out[i-1]/n + arr[i]
        return out
    atr14 = wilder_smooth(tr, p)
    pdm14 = wilder_smooth(pdm, p)
    ndm14 = wilder_smooth(ndm, p)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = np.where(atr14 > 0, 100 * pdm14 / atr14, 0)
        ndi = np.where(atr14 > 0, 100 * ndm14 / atr14, 0)
        dx  = np.where((pdi + ndi) > 0, 100 * np.abs(pdi - ndi) / (pdi + ndi), 0)
    adx_out = np.zeros(n)
    adx_out[2*p] = dx[p:2*p+1].mean()
    for i in range(2*p+1, n):
        adx_out[i] = (adx_out[i-1] * (p-1) + dx[i]) / p
    idx = close.index
    return pd.Series(adx_out, index=idx), pd.Series(pdi, index=idx), pd.Series(ndi, index=idx)


def stochastic(high, low, close, k=14, d=3):
    """Oscilador Estocástico — retorna (%K, %D)."""
    ll = low.rolling(k).min()
    hh = high.rolling(k).max()
    pct_k = 100 * (close - ll) / (hh - ll + 1e-10)
    pct_d = pct_k.rolling(d).mean()
    return pct_k, pct_d


def ichimoku(high, low, close):
    """Ichimoku Cloud — retorna dict con las 5 líneas."""
    tenkan  = (high.rolling(9).max()  + low.rolling(9).min())  / 2
    kijun   = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senA    = ((tenkan + kijun) / 2).shift(26)
    senB    = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    chikou  = close.shift(-26)
    return {"tenkan": tenkan, "kijun": kijun, "senA": senA, "senB": senB, "chikou": chikou}


def obv(close, volume):
    """On-Balance Volume."""
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum()


def vwap(high, low, close, volume):
    """VWAP diario (aproximado sobre el período seleccionado)."""
    typical = (high + low + close) / 3
    return (typical * volume).cumsum() / volume.cumsum()


# ══════════════════════════════════════════════════════════════════
# CONSTANTES DE COLOR
# ══════════════════════════════════════════════════════════════════

ORO    = "#c5a860"
BLANCO = "#ffffff"
GRID   = "rgba(197,168,96,0.08)"
BG     = "rgba(0,0,0,0)"

INST = {
    "alza":    "#0066cc",
    "baja":    "#cc3300",
    "ema20":   "#e6a817",
    "ema50":   "#2196f3",
    "ema100":  "#9c27b0",
    "ema200":  "#f44336",
    "bb":      "#607d8b",
    "macd":    "#2196f3",
    "signal":  "#ff9800",
    "hist+":   "#0066cc",
    "hist-":   "#cc3300",
    "rsi":     "#9c27b0",
    "stoch":   "#e91e63",
    "adx":     "#ff9800",
    "vol+":    "rgba(0,102,204,0.45)",
    "vol-":    "rgba(204,51,0,0.45)",
    "vol_usd": "rgba(197,168,96,0.35)",
}


# ══════════════════════════════════════════════════════════════════
# MÉTRICAS DE RIESGO
# ══════════════════════════════════════════════════════════════════

def calc_metricas_riesgo(close, periodo_dias, benchmark_close=None):
    ret = close.pct_change().dropna()
    if len(ret) < 5:
        return {}

    trading_days = 252
    std_anual    = float(ret.std() * np.sqrt(trading_days) * 100)

    roll_max  = close.cummax()
    drawdown  = (close - roll_max) / roll_max * 100
    max_dd    = float(drawdown.min())

    ret_periodo = float((close.iloc[-1] / close.iloc[0] - 1) * 100)

    mejor_dia = float(ret.max() * 100)
    peor_dia  = float(ret.min() * 100)

    ret_acum  = close.pct_change(20).dropna() * 100
    mejor_mes = float(ret_acum.max()) if len(ret_acum) else 0
    peor_mes  = float(ret_acum.min()) if len(ret_acum) else 0

    rf_diario = 0.045 / trading_days
    exceso    = ret - rf_diario
    sharpe    = float(exceso.mean() / ret.std() * np.sqrt(trading_days)) if ret.std() > 0 else 0

    beta = None
    if benchmark_close is not None and len(benchmark_close) > 10:
        bench_ret = benchmark_close.pct_change().dropna()
        common    = ret.index.intersection(bench_ret.index)
        if len(common) > 10:
            cov   = ret.loc[common].cov(bench_ret.loc[common])
            var_b = bench_ret.loc[common].var()
            beta  = round(cov / var_b, 3) if var_b > 0 else None

    return {
        "Retorno período":  f"{ret_periodo:+.2f}%",
        "Std Dev anual":    f"{std_anual:.2f}%",
        "Max Drawdown":     f"{max_dd:.2f}%",
        "Mejor día":        f"{mejor_dia:+.2f}%",
        "Peor día":         f"{peor_dia:+.2f}%",
        "Mejor mes (20d)":  f"{mejor_mes:+.2f}%",
        "Peor mes (20d)":   f"{peor_mes:+.2f}%",
        "Sharpe Ratio":     f"{sharpe:.3f}",
        "Beta vs SP500":    f"{beta:.3f}" if beta else "N/A",
    }


# ══════════════════════════════════════════════════════════════════
# ANÁLISIS MULTITEMPORAL DE VELAS
# ══════════════════════════════════════════════════════════════════

_TF_CONFIG_CORTO = [
    ("5 min",   "5m",  "5d"),
    ("15 min",  "15m", "5d"),
    ("30 min",  "30m", "5d"),
    ("1 hora",  "1h",  "30d"),
    ("4 horas", "1h",  "60d"),   # se resamplea a 4h
]
_TF_CONFIG_LARGO = [
    ("4 horas", "1h",  "60d"),   # se resamplea a 4h
    ("Diario",  "1d",  "2y"),
    ("Semanal", "1wk", "5y"),
    ("Mensual", "1mo", "5y"),
]
_PERIODOS_CORTOS = {"1D", "2D", "1S"}

def _señal_vela(df_tf, nombre_tf):
    """Calcula señal simple para un DataFrame OHLCV de una temporalidad."""
    try:
        if df_tf is None or len(df_tf) < 30:
            return None
        # Si es 4 horas, resamplear desde 1h
        if nombre_tf == "4 horas":
            df_tf = df_tf.resample("4h").agg({
                "Open": "first", "High": "max", "Low": "min",
                "Close": "last", "Volume": "sum"
            }).dropna(subset=["Close"])
        if len(df_tf) < 10:
            return None

        close = df_tf["Close"].dropna()
        open_ = df_tf["Open"].dropna()

        # Última vela
        ult_close = float(close.iloc[-1])
        ult_open  = float(open_.iloc[-1])
        vela_dir  = "ALCISTA" if ult_close > ult_open else "BAJISTA"
        vela_col  = "#00cc55" if ult_close > ult_open else "#ff3333"

        # Tendencia EMA 20 vs EMA 50
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
        tendencia = "ALCISTA" if ema20 > ema50 else "BAJISTA"
        tend_col  = "#00cc55" if ema20 > ema50 else "#ff3333"

        # RSI 14
        delta = close.diff().dropna()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, float("nan"))
        rsi   = (100 - 100 / (1 + rs)).iloc[-1]
        if rsi >= 70:
            rsi_txt, rsi_col = "SOBRECOMPRA", "#ff6644"
        elif rsi <= 30:
            rsi_txt, rsi_col = "SOBREVENTA",  "#4da6ff"
        else:
            rsi_txt, rsi_col = "NEUTRAL",     "#aaaaaa"

        # Señal global: si tendencia EMA y vela coinciden → fuerte
        if tendencia == vela_dir == "ALCISTA":
            señal, señal_col = "COMPRA", "#00cc55"
        elif tendencia == vela_dir == "BAJISTA":
            señal, señal_col = "VENTA", "#ff3333"
        else:
            señal, señal_col = "NEUTRAL", "#aaaaaa"

        return {
            "tf": nombre_tf,
            "vela": vela_dir, "vela_col": vela_col,
            "tendencia": tendencia, "tend_col": tend_col,
            "rsi": round(float(rsi), 1), "rsi_txt": rsi_txt, "rsi_col": rsi_col,
            "señal": señal, "señal_col": señal_col,
        }
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def analisis_multitemporal(ticker, periodo_actual):
    """Descarga datos intraday/diario y retorna señales por temporalidad."""
    import yfinance as yf
    configs = _TF_CONFIG_CORTO if periodo_actual in _PERIODOS_CORTOS else _TF_CONFIG_LARGO
    resultados = []
    for nombre_tf, interval, period in configs:
        try:
            df_tf = yf.download(ticker, interval=interval, period=period,
                                progress=False, auto_adjust=True)
            if df_tf.empty:
                continue
            # Aplanar MultiIndex si aplica
            if isinstance(df_tf.columns, pd.MultiIndex):
                df_tf.columns = df_tf.columns.get_level_values(0)
            res = _señal_vela(df_tf, nombre_tf)
            if res:
                resultados.append(res)
        except Exception:
            continue
    return resultados


_TICKER_MAP = {
    "S&P 500":      "^GSPC",  "Nasdaq":       "^IXIC",  "Dow Jones":    "^DJI",
    "Oro":          "GC=F",   "Petróleo WTI": "CL=F",   "Plata":        "SI=F",
    "Cobre":        "HG=F",   "Bitcoin":      "BTC-USD", "Litio ETF":   "LIT",
    "Albemarle":    "ALB",    "SQM":          "SQM",
}

_BARRAS_1D = [("1 min", "1m"), ("5 min", "5m"), ("10 min", "_10m"), ("15 min", "15m")]
_BARRAS_2D = [("5 min", "5m"), ("10 min", "_10m"), ("15 min", "15m"), ("30 min", "30m")]

@st.cache_data(ttl=120, show_spinner=False)
def cargar_intraday(ticker, interval, periodo):
    """Descarga datos intraday de yfinance para períodos 1D/2D."""
    import yfinance as yf
    # Para 10 min: descargamos 5m y resampleamos
    fetch_interval = "5m" if interval == "_10m" else interval
    period_str = "1d" if periodo == "1D" else "2d"
    # 1m solo disponible últimos 7 días → siempre funciona para 1D/2D
    df = yf.download(ticker, interval=fetch_interval, period=period_str,
                     progress=False, auto_adjust=True)
    if df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
    if interval == "_10m":
        df = df.resample("10min").agg({
            "Open": "first", "High": "max", "Low": "min",
            "Close": "last", "Volume": "sum"
        }).dropna(subset=["Close"])
    return df


# ══════════════════════════════════════════════════════════════════
# SCREENER DE SEÑALES — MACD y TD Sequential
# ══════════════════════════════════════════════════════════════════

def _calc_macd(close):
    """Retorna (macd_line, signal_line) como Series."""
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd  = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def _calc_td_seq(close):
    """Retorna lista de señales setup: 'BUY9' o 'SELL9' por índice."""
    c = close.values
    n = len(c)
    señales = {}
    sell_cnt = buy_cnt = 0
    for i in range(4, n):
        if c[i] >= c[i - 4]:
            sell_cnt += 1; buy_cnt = 0
        else:
            buy_cnt += 1; sell_cnt = 0
        if sell_cnt == 9:
            señales[i] = "SELL9"; sell_cnt = 0
        elif buy_cnt == 9:
            señales[i] = "BUY9"; buy_cnt = 0
    return señales


def _escanear_grupo(carpeta, indice_label, ventana=5):
    """Escanea todas las CSVs de una carpeta y devuelve señales en la ventana indicada."""
    resultados = []
    if not os.path.exists(carpeta):
        return resultados
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".csv") and not f.startswith("_")]
    for fname in archivos:
        ticker = fname.replace(".csv", "")
        ruta   = os.path.join(carpeta, fname)
        try:
            df = pd.read_csv(ruta, index_col=0, parse_dates=True, skiprows=[1, 2])
            df.index = pd.to_datetime(df.index, errors="coerce")
            df = df[df.index.notna()]
            if "Close" not in df.columns or len(df) < 40:
                continue
            close = pd.to_numeric(df["Close"], errors="coerce").dropna()
            if len(close) < 40:
                continue

            precio_actual = float(close.iloc[-1])
            precio_ant    = float(close.iloc[-2]) if len(close) >= 2 else precio_actual
            cambio_pct    = round((precio_actual / precio_ant - 1) * 100, 2)

            # ── MACD crossover ────────────────────────────────────
            macd_l, sig_l = _calc_macd(close)
            # Crossover: busca en las últimas `ventana` barras
            for i in range(-ventana, 0):
                idx = len(macd_l) + i
                if idx < 1:
                    continue
                prev_diff = float(macd_l.iloc[idx - 1]) - float(sig_l.iloc[idx - 1])
                curr_diff = float(macd_l.iloc[idx])     - float(sig_l.iloc[idx])
                fecha_str = str(close.index[idx])[:10]
                if prev_diff < 0 and curr_diff >= 0:
                    resultados.append({
                        "Ticker": ticker, "Índice": indice_label,
                        "Señal": "MACD_BUY", "Fecha": fecha_str,
                        "Precio": round(precio_actual, 2), "Cambio%": cambio_pct,
                        "MACD": round(curr_diff, 4),
                    })
                    break
                elif prev_diff > 0 and curr_diff <= 0:
                    resultados.append({
                        "Ticker": ticker, "Índice": indice_label,
                        "Señal": "MACD_SELL", "Fecha": fecha_str,
                        "Precio": round(precio_actual, 2), "Cambio%": cambio_pct,
                        "MACD": round(curr_diff, 4),
                    })
                    break

            # ── TD Sequential ─────────────────────────────────────
            td_señales = _calc_td_seq(close)
            n = len(close)
            for offset in range(ventana, 0, -1):
                idx = n - offset
                if idx in td_señales:
                    tipo_td = td_señales[idx]
                    fecha_str = str(close.index[idx])[:10]
                    resultados.append({
                        "Ticker": ticker, "Índice": indice_label,
                        "Señal": f"TD_{tipo_td}", "Fecha": fecha_str,
                        "Precio": round(precio_actual, 2), "Cambio%": cambio_pct,
                        "MACD": "-",
                    })

        except Exception:
            continue
    return resultados


@st.cache_data(ttl=3600, show_spinner=False)
def screener_señales(ventana=5):
    """Escanea SP500, Nasdaq100 y Dow30. ventana = días de lookback. Cachea 1 hora."""
    grupos = [
        (os.path.join(DATA_DIR, "raw", "sp500"),    "SP500"),
        (os.path.join(DATA_DIR, "raw", "nasdaq100"), "Nasdaq100"),
        (os.path.join(DATA_DIR, "raw", "dow30"),     "Dow30"),
    ]
    todos = []
    for carpeta, label in grupos:
        todos.extend(_escanear_grupo(carpeta, label, ventana=ventana))
    df = pd.DataFrame(todos) if todos else pd.DataFrame()
    return df


# ══════════════════════════════════════════════════════════════════
# GRÁFICO INTERACTIVO COMPLETO
# ══════════════════════════════════════════════════════════════════

def grafico_interactivo(df, titulo, indicadores):
    close = df["Close"].dropna()
    high  = df["High"].dropna()   if "High"   in df.columns else close
    low   = df["Low"].dropna()    if "Low"    in df.columns else close
    open_ = df["Open"].dropna()   if "Open"   in df.columns else close
    vol   = df["Volume"].dropna() if "Volume" in df.columns else None

    vol_usd = (vol * close).dropna() if vol is not None else None

    tiene_macd    = "MACD" in indicadores
    tiene_rsi     = "RSI"  in indicadores
    tiene_vol_usd = vol_usd is not None
    n_rows = (1
        + (1 if tiene_vol_usd else 0)
        + (1 if tiene_macd    else 0)
        + (1 if tiene_rsi     else 0)
    )

    row_h = [0.52]
    if tiene_vol_usd: row_h.append(0.12)
    if tiene_macd:    row_h.append(0.18)
    if tiene_rsi:     row_h.append(0.18)
    total = sum(row_h); row_h = [r / total for r in row_h]

    subtitles = [""] * n_rows
    row_vol = row_macd = row_rsi = None
    r = 2
    if tiene_vol_usd: row_vol  = r; subtitles[r - 1] = "Volumen USD"; r += 1
    if tiene_macd:    row_macd = r; subtitles[r - 1] = "MACD";        r += 1
    if tiene_rsi:     row_rsi  = r; subtitles[r - 1] = "RSI 14";      r += 1

    fig = make_subplots(
        rows=n_rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.02, row_heights=row_h,
        subplot_titles=subtitles,
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=open_, high=high, low=low, close=close, name="Precio",
        increasing_fillcolor=INST["alza"], increasing_line_color=INST["alza"],
        decreasing_fillcolor=INST["baja"], decreasing_line_color=INST["baja"],
    ), row=1, col=1)

    tabla = {}
    ultimo = float(close.iloc[-1]) if len(close) else None

    colores_ema = {10: "#00e5ff", 20: INST["ema20"], 50: INST["ema50"], 100: INST["ema100"], 200: INST["ema200"]}
    for p in [10, 20, 50, 100, 200]:
        k = f"EMA {p}"
        if k in indicadores:
            v = ema(close, p)
            fig.add_trace(go.Scatter(
                x=df.index, y=v, name=k,
                line=dict(color=colores_ema[p], width=1.6), opacity=0.95,
            ), row=1, col=1)
            vv = float(v.iloc[-1]) if len(v) else None
            tabla[k] = {
                "Valor":    round(vv, 2) if vv else "-",
                "vs Precio": f"{round((ultimo / vv - 1) * 100, 2)}%" if ultimo and vv else "-",
                "Señal":    "↑ Sobre" if ultimo and vv and ultimo > vv else "↓ Bajo",
            }

    if "Bollinger Bands" in indicadores:
        bu, bm, bl = bollinger(close)
        fig.add_trace(go.Scatter(x=df.index, y=bu, name="BB Upper",
            line=dict(color=INST["bb"], width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=bl, name="BB Lower",
            line=dict(color=INST["bb"], width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(96,125,139,0.06)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=bm, name="BB Media",
            line=dict(color=INST["bb"], width=1, dash="dashdot")), row=1, col=1)
        posb = round((close.iloc[-1] - bl.iloc[-1]) / (bu.iloc[-1] - bl.iloc[-1]) * 100, 1) if len(close) else 0
        tabla["Bollinger"] = {
            "Upper": round(float(bu.iloc[-1]), 2), "Media": round(float(bm.iloc[-1]), 2),
            "Lower": round(float(bl.iloc[-1]), 2), "%B": f"{posb}%",
            "Señal": "SOBRECOMPRA" if posb > 80 else ("SOBREVENTA" if posb < 20 else "NEUTRAL"),
        }

    if "Fibonacci" in indicadores:
        niveles = fibonacci(high, low)
        cols_fib = [
            "rgba(255,100,100,0.7)", "rgba(255,165,0,0.7)", ORO,
            "rgba(255,255,255,0.5)", "rgba(100,180,255,0.7)",
            "rgba(160,140,255,0.7)", "rgba(200,100,200,0.7)",
        ]
        for (nivel, valor), col in zip(niveles.items(), cols_fib):
            fig.add_hline(y=valor, line_dash="dot", line_color=col, opacity=0.6,
                annotation_text=f" {nivel}  {valor:,.2f}",
                annotation_font_color=col, annotation_font_size=9, row=1, col=1)
        tabla["Fibonacci"] = niveles

    if "TD Sequential" in indicadores:
        bull_s, bear_s, bull_cd, bear_cd, setup_sig, cd_sig = td_sequential(close, high, low)
        rng = max(float(close.max() - close.min()), 0.01)

        # Solo se marca el triángulo cuando la secuencia de 9 se completa

        # ── SELL Setup 9 completo: triángulo ROJO ARRIBA ──────────
        s9_sell = setup_sig[setup_sig.str.contains("SELL", na=False)]
        if len(s9_sell):
            fig.add_trace(go.Scatter(
                x=s9_sell.index,
                y=high.reindex(s9_sell.index) + rng * 0.04,
                mode="markers+text",
                name="TD SELL Setup 9",
                text=["9"] * len(s9_sell),
                textposition="top center",
                textfont=dict(color="#ff3333", size=13, family="Arial Black"),
                marker=dict(symbol="triangle-down", size=18, color="#ff3333",
                            line=dict(color="white", width=1.5)),
            ), row=1, col=1)

        # ── BUY Setup 9 completo: triángulo VERDE ABAJO ───────────
        s9_buy = setup_sig[setup_sig.str.contains("BUY", na=False)]
        if len(s9_buy):
            fig.add_trace(go.Scatter(
                x=s9_buy.index,
                y=low.reindex(s9_buy.index) - rng * 0.04,
                mode="markers+text",
                name="TD BUY Setup 9",
                text=["9"] * len(s9_buy),
                textposition="bottom center",
                textfont=dict(color="#00cc55", size=13, family="Arial Black"),
                marker=dict(symbol="triangle-up", size=18, color="#00cc55",
                            line=dict(color="white", width=1.5)),
            ), row=1, col=1)

        # ── Estado actual ─────────────────────────────────────────
        ult = setup_sig[setup_sig != ""].iloc[-1] if len(setup_sig[setup_sig != ""]) else "Sin señal"
        tabla["TD Sequential"] = {
            "Última señal":      ult,
            "Setup SELL actual": int(bear_s.iloc[-1]),
            "Setup BUY actual":  int(bull_s.iloc[-1]),
        }

    if "VWAP" in indicadores and vol is not None:
        vwap_line = vwap(high, low, close, vol)
        fig.add_trace(go.Scatter(x=df.index, y=vwap_line, name="VWAP",
            line=dict(color="#ff9800", width=1.4, dash="dash")), row=1, col=1)
        ult_vwap = float(vwap_line.dropna().iloc[-1]) if len(vwap_line.dropna()) else None
        ult_c    = float(close.iloc[-1]) if len(close) else None
        tabla["VWAP"] = {
            "VWAP":    round(ult_vwap, 2) if ult_vwap else "-",
            "vs Precio": f"{round((ult_c/ult_vwap-1)*100,2)}%" if ult_vwap and ult_c else "-",
            "Señal":   "↑ Sobre VWAP" if (ult_c and ult_vwap and ult_c > ult_vwap) else "↓ Bajo VWAP",
        }

    if tiene_vol_usd and row_vol:
        cvol = [INST["vol+"] if c >= o else INST["vol-"] for c, o in zip(close, open_)]
        fig.add_trace(go.Bar(
            x=df.index, y=vol_usd, name="Vol USD",
            marker_color=cvol, marker_line_width=0, showlegend=True,
        ), row=row_vol, col=1)
        vol_ma20 = vol_usd.rolling(20).mean()
        fig.add_trace(go.Scatter(
            x=df.index, y=vol_ma20, name="Vol MA20",
            line=dict(color=INST["ema20"], width=1.2, dash="dot"), showlegend=False,
        ), row=row_vol, col=1)
        fig.update_yaxes(tickformat=".2s", row=row_vol, col=1)

    if tiene_macd and row_macd:
        ml, sl, hl = macd(close)
        ch = [INST["hist+"] if v >= 0 else INST["hist-"] for v in hl.fillna(0)]
        fig.add_trace(go.Bar(
            x=df.index, y=hl, name="MACD Hist",
            marker_color=ch, marker_line_width=0, showlegend=False,
        ), row=row_macd, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=ml, name="MACD",
            line=dict(color=INST["macd"], width=1.5)), row=row_macd, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=sl, name="Signal",
            line=dict(color=INST["signal"], width=1.5)), row=row_macd, col=1)
        fig.add_hline(y=0, line_dash="solid", line_color="rgba(0,0,0,0.15)",
                      line_width=1, row=row_macd, col=1)
        cruce = "ALCISTA" if float(ml.iloc[-1]) > float(sl.iloc[-1]) else "BAJISTA"
        tabla["MACD"] = {
            "MACD":      round(float(ml.iloc[-1]), 4),
            "Signal":    round(float(sl.iloc[-1]), 4),
            "Histograma":round(float(hl.iloc[-1]), 4),
            "Cruce":     cruce,
            "Señal":     "↑ COMPRA" if cruce == "ALCISTA" else "↓ VENTA",
        }

    if tiene_rsi and row_rsi:
        rv = rsi(close)
        fig.add_trace(go.Scatter(x=df.index, y=rv, name="RSI 14",
            line=dict(color=INST["rsi"], width=1.5)), row=row_rsi, col=1)
        fig.add_hline(y=70, line_dash="dot",
            line_color=INST["baja"], opacity=0.6, row=row_rsi, col=1)
        fig.add_hline(y=30, line_dash="dot",
            line_color=INST["alza"], opacity=0.6, row=row_rsi, col=1)
        fig.add_hline(y=50, line_dash="dot",
            line_color="rgba(0,0,0,0.15)", line_width=1, row=row_rsi, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(204,51,0,0.04)",  line_width=0, row=row_rsi, col=1)
        fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,102,204,0.04)", line_width=0, row=row_rsi, col=1)
        rv_ = round(float(rv.iloc[-1]), 2) if len(rv) else 0
        tabla["RSI"] = {
            "RSI 14": rv_,
            "Zona":   "SOBRECOMPRA" if rv_ > 70 else ("SOBREVENTA" if rv_ < 30 else "NEUTRAL"),
            "Señal":  "↑ COMPRA" if rv_ < 35 else ("↓ VENTA" if rv_ > 65 else "→ ESPERAR"),
        }

    GRID_LIGHT = "rgba(197,168,96,0.15)"
    fig.update_layout(
        title=dict(text=titulo, font=dict(color="#0a0a0a", size=14, family="Playfair Display")),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(color="#0a0a0a", size=10),
        xaxis_rangeslider_visible=False,
        legend=dict(
            bgcolor="rgba(248,247,244,0.95)",
            bordercolor="rgba(197,168,96,0.4)",
            borderwidth=1,
            font=dict(size=10, color="#0a0a0a"),
            orientation="h", yanchor="bottom", y=1.01,
        ),
        height=700,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    for i in range(1, n_rows + 1):
        fig.update_xaxes(gridcolor=GRID_LIGHT, row=i, col=1, color="#555",
                         linecolor="rgba(197,168,96,0.3)", tickfont=dict(color="#555", size=10))
        fig.update_yaxes(gridcolor=GRID_LIGHT, row=i, col=1, color="#555",
                         linecolor="rgba(197,168,96,0.3)", tickfont=dict(color="#555", size=10))
    return fig, tabla


def badge_señal(señal):
    mapa = {
        "COMPRA FUERTE": "badge-compra-fuerte",
        "COMPRA":        "badge-compra",
        "NEUTRAL":       "badge-neutral",
        "VENTA":         "badge-venta",
        "VENTA FUERTE":  "badge-venta-fuerte",
    }
    clase = mapa.get(señal, "badge-neutral")
    return f'<span class="{clase}">{señal}</span>'


# ══════════════════════════════════════════════════════════════════
# GRÁFICO DE BARRAS MACRO
# ══════════════════════════════════════════════════════════════════

def grafico_barras(df_macro, categoria):
    df = df_macro[df_macro["Categoría"] == categoria].dropna(subset=["Cambio Día %"])
    if df.empty:
        return go.Figure()
    colores = [
        "rgba(0,102,204,0.75)" if v >= 0 else "rgba(204,51,0,0.75)"
        for v in df["Cambio Día %"]
    ]
    fig = go.Figure(go.Bar(
        x=df["Activo"], y=df["Cambio Día %"],
        marker_color=colores,
        text=df["Cambio Día %"].round(2).astype(str) + "%",
        textposition="outside",
        marker_line_width=0,
    ))
    fig.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(color="#555555"),
        height=260,
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(gridcolor=GRID, color="rgba(80,60,10,0.6)"),
        yaxis=dict(gridcolor=GRID, color="rgba(80,60,10,0.6)"),
        title=dict(
            text=f"Variación Diaria — {categoria}",
            font=dict(color=BLANCO, size=12, family="Playfair Display"),
        ),
    )
    return fig


# ══════════════════════════════════════════════════════════════════
# TABLA HTML COMPACTA (Dashboard Macro columna izquierda)
# ══════════════════════════════════════════════════════════════════

def tabla_html(titulo, filas):
    # Todo inline styles — las clases CSS no funcionan en HTML inyectado por Streamlit
    rows = ""
    for i, (nombre, valor, cambio) in enumerate(filas):
        color_chg = "#0066cc" if cambio >= 0 else "#cc3300"
        signo = "▲" if cambio >= 0 else "▼"
        bg_row = "rgba(197,168,96,0.06)" if i % 2 == 0 else "rgba(255,255,255,0.5)"
        rows += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:7px 12px;border-bottom:1px solid rgba(197,168,96,0.07);background:{bg_row};">'
            f'<span style="color:#222;font-size:.78rem;font-family:Inter,sans-serif;">{nombre}</span>'
            f'<span style="color:#0a0a0a;font-weight:600;font-size:.78rem;font-family:Inter,sans-serif;">{valor}</span>'
            f'<span style="color:{color_chg};font-size:.74rem;font-weight:700;">{signo}{abs(cambio):.2f}%</span>'
            f'</div>'
        )
    return (
        # Fondo mármol: gradiente suave crema/beige con vetas doradas via background
        f'<div style="'
        f'background:linear-gradient(135deg,#fdf9f2 0%,#f8f2e4 40%,#fdf6eb 70%,#f5ede0 100%);'
        f'border:1.5px solid rgba(197,168,96,0.55);'
        f'border-left:3px solid #c5a860;'
        f'border-radius:6px;margin-bottom:14px;overflow:hidden;'
        f'box-shadow:0 2px 12px rgba(197,168,96,0.12),inset 0 0 40px rgba(197,168,96,0.03);">'
        f'<div style="padding:8px 12px 7px;'
        f'background:linear-gradient(90deg,rgba(197,168,96,0.12),rgba(197,168,96,0.04));'
        f'border-bottom:1px solid rgba(197,168,96,0.3);'
        f'font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:#a07820;font-weight:700;">{titulo}</div>'
        f'{rows}'
        f'</div>'
    )


# ══════════════════════════════════════════════════════════════════
# NAVEGACIÓN — query params como única fuente de verdad
# ══════════════════════════════════════════════════════════════════

_NAV_ITEMS = [
    ("dashboard",   "◈", "Macro",    "◈  Dashboard Macro"),
    ("tecnico",     "◎", "Técnico",  "◎  Análisis Técnico"),
    ("screener",    "▲", "Señales",  "▲  Screener / Señales"),
    ("noticias",    "◉", "Noticias", "◉  Noticias"),
    ("fundamental", "◆", "Fund.",    "◆  Fundamentales"),
    ("social",      "◇", "Social",   "◇  Social & Podcasts"),
]
_NAV_QP_MAP = {qk: full for qk, _, _, full in _NAV_ITEMS}

# Página activa desde query param (default: dashboard)
_qp_active = st.query_params.get("page", "dashboard")
if _qp_active not in _NAV_QP_MAP:
    _qp_active = "dashboard"
pagina = _NAV_QP_MAP[_qp_active]

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════

status_color, status_text = get_market_status()
now_str  = datetime.now().strftime("%H:%M:%S")
date_str = datetime.now().strftime("%A, %d %b %Y").upper()

with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-logo">
      <div class="sidebar-logo-title">JST <span>ALPHA</span></div>
      <div class="sidebar-logo-sub">Trading Intelligence Platform</div>
      <div class="market-status" style="color:{status_color};border-color:rgba(197,168,96,0.2);">
        <span style="display:inline-block;width:7px;height:7px;border-radius:50%;
                     background:{status_color};box-shadow:0 0 6px {status_color};"></span>
        {status_text}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sidebar-clock">
      <div class="sidebar-clock-time">{now_str}</div>
      <div class="sidebar-clock-date">{date_str}</div>
    </div>
    """, unsafe_allow_html=True)

    # Botones de navegación — actualizan query param
    for _qk, _icon, _short, _full in _NAV_ITEMS:
        _is_active = (_qk == _qp_active)
        _btn_label = f"{_icon}  {_full.split('  ', 1)[1]}"
        if _is_active:
            st.markdown(
                f"<div style='background:rgba(197,168,96,0.15);border-left:3px solid #c5a860;"
                f"border-radius:4px;padding:10px 14px;margin-bottom:3px;"
                f"font-size:0.74rem;letter-spacing:2px;text-transform:uppercase;"
                f"color:#c5a860;font-weight:700;cursor:default;'>{_btn_label}</div>",
                unsafe_allow_html=True,
            )
        else:
            if st.button(_btn_label, key=f"sb_{_qk}", use_container_width=True):
                st.query_params["page"] = _qk
                st.rerun()

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    if st.button("↺  Actualizar datos", key="btn_refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"""
    <div class="sidebar-footer">
      v2.0 · JST Alpha<br>
      <span style="color:rgba(197,168,96,0.2);">──────────────────</span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# BOTTOM NAV BAR — fija en mobile
# ══════════════════════════════════════════════════════════════════

_bnav_html = '<nav class="jst-bottom-nav">'
for _bk, _bicon, _blabel, _ in _NAV_ITEMS:
    _bactive_cls = "active" if _bk == _qp_active else ""
    _bnav_html += (
        f'<a href="?page={_bk}" class="jst-bnav-item {_bactive_cls}">'
        f'<span class="jst-bnav-icon">{_bicon}</span>'
        f'<span>{_blabel}</span></a>'
    )
_bnav_html += '</nav>'
st.markdown(_bnav_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PÁGINA 1 — DASHBOARD MACRO
# ══════════════════════════════════════════════════════════════════

if "Dashboard" in pagina:
    df_macro = cargar_hoja(os.path.join(DATA_DIR, "TRADING_DATA.xlsx"), "Resumen Macro")

    # ── Page title ───────────────────────────────────────────────
    st.markdown("""
    <div style="padding:4px 0 16px;border-bottom:2px solid rgba(197,168,96,0.25);margin-bottom:18px;">
      <span style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:800;
                   color:#0a0a0a;letter-spacing:5px;text-transform:uppercase;">
        JST <span style="color:#c5a860;">ALPHA</span>
      </span>
      <span style="color:rgba(140,110,30,0.7);font-size:0.62rem;
                   letter-spacing:4px;text-transform:uppercase;margin-left:18px;font-weight:600;">
        Dashboard Macro · Mercados Globales
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── HERO STRIP: 6 tarjetas clave ────────────────────────────
    HERO_MAP = {
        "SP500":       ("S&P 500",  "ÍNDICES"),
        "NASDAQ_COMP": ("Nasdaq",   "ÍNDICES"),
        "DOW_JONES":   ("Dow Jones","ÍNDICES"),
        "Oro":         ("Oro",      "COMMODITIES"),
        "Petroleo_WTI":("Petróleo", "COMMODITIES"),
        "Bitcoin":     ("Bitcoin",  "COMMODITIES"),
    }

    hero_cards_html = ""
    if not df_macro.empty:
        for activo_key, (display_name, cat) in HERO_MAP.items():
            match = df_macro[df_macro["Activo"].astype(str).str.upper().str.replace(" ", "_") == activo_key.upper()]
            if match.empty:
                match = df_macro[df_macro["Activo"].astype(str).str.contains(activo_key.replace("_", " "), case=False, na=False)]
            if not match.empty:
                row = match.iloc[0]
                val = float(row.get("Último Valor", 0) or 0)
                chg = float(row.get("Cambio Día %", 0) or 0)
                color_chg = "#0066cc" if chg >= 0 else "#cc3300"
                sig = "▲" if chg >= 0 else "▼"
                fmt = f"{val:,.0f}" if val > 100 else f"{val:,.2f}"
                hero_cards_html += (
                    f'<div style="flex:1;'
                    f'background:linear-gradient(135deg,#fdf9f2 0%,#f8f2e4 50%,#fdf6eb 100%);'
                    f'border:1.5px solid rgba(197,168,96,0.5);'
                    f'border-top:2.5px solid #c5a860;'
                    f'border-radius:6px;padding:12px 14px;min-width:0;'
                    f'box-shadow:0 2px 10px rgba(197,168,96,0.1);">'
                    f'<div style="font-size:0.58rem;letter-spacing:3px;text-transform:uppercase;'
                    f'color:#a07820;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{display_name}</div>'
                    f'<div style="font-family:\'Playfair Display\',serif;font-size:1.18rem;font-weight:800;color:#0a0a0a;margin:5px 0 4px;">{fmt}</div>'
                    f'<div style="color:{color_chg};font-size:0.76rem;font-weight:700;">{sig} {abs(chg):.2f}%</div>'
                    f'</div>'
                )

    st.markdown(
        f'<div style="display:flex;gap:10px;margin-bottom:20px;">{hero_cards_html}</div>',
        unsafe_allow_html=True
    )

    # ── 3 COLUMNAS PRINCIPALES ───────────────────────────────────
    col_left, col_center, col_right = st.columns([2.4, 4.8, 2.4])

    # ── LEFT COLUMN ──────────────────────────────────────────────
    with col_left:
        if not df_macro.empty:
            # Índices Globales
            df_idx = df_macro[df_macro["Categoría"] == "ÍNDICES"]
            filas_idx = []
            for _, r in df_idx.iterrows():
                filas_idx.append((
                    str(r.get("Activo", ""))[:14],
                    f"{float(r.get('Último Valor', 0) or 0):,.0f}",
                    float(r.get("Cambio Día %", 0) or 0),
                ))
            if filas_idx:
                st.markdown(tabla_html("ÍNDICES GLOBALES", filas_idx), unsafe_allow_html=True)

            # Monedas
            df_fx = df_macro[df_macro["Categoría"] == "MONEDAS"]
            filas_fx = []
            for _, r in df_fx.iterrows():
                filas_fx.append((
                    str(r.get("Activo", ""))[:14],
                    f"{float(r.get('Último Valor', 0) or 0):.4f}",
                    float(r.get("Cambio Día %", 0) or 0),
                ))
            if filas_fx:
                st.markdown(tabla_html("MONEDAS FX", filas_fx), unsafe_allow_html=True)

            # Tasas UST
            df_usd = df_macro[df_macro["Categoría"] == "TASAS UST"]
            filas_usd = []
            for _, r in df_usd.iterrows():
                filas_usd.append((
                    str(r.get("Activo", ""))[:14],
                    f"{float(r.get('Último Valor', 0) or 0):.2f}%",
                    float(r.get("Cambio Día %", 0) or 0),
                ))
            if filas_usd:
                st.markdown(tabla_html("TASAS UST", filas_usd), unsafe_allow_html=True)

    # ── CENTER COLUMN ────────────────────────────────────────────
    with col_center:
        st.markdown("""
        <div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:#c5a860;font-weight:700;
                    padding:6px 0 8px;border-bottom:1px solid rgba(197,168,96,0.3);margin-bottom:10px;">
          S&amp;P 500 — Gráfico Principal
        </div>""", unsafe_allow_html=True)

        # Period selector buttons
        periodos_map_dash = {"1S": -5, "1M": -22, "3M": -66, "6M": -126, "1A": -252, "5A": None}
        periodo_dash = st.session_state.get("periodo_dash", "3M")
        p_cols = st.columns(len(periodos_map_dash))
        for i, (label, _) in enumerate(periodos_map_dash.items()):
            with p_cols[i]:
                activo = (label == periodo_dash)
                btn_style = "background:#c5a860!important;color:#0a0a0a!important;border-color:#c5a860!important;font-weight:700!important;" if activo else ""
                if st.button(label, key=f"dash_per_{label}", use_container_width=True):
                    st.session_state["periodo_dash"] = label
                    st.rerun()
                if activo:
                    st.markdown(f"""
                    <style>
                    div[data-testid="stButton"] button[kind="secondary"]:has(div:contains("{label}")) {{
                        {btn_style}
                    }}
                    </style>""", unsafe_allow_html=True)

        periodo_dash = st.session_state.get("periodo_dash", "3M")
        ruta_sp = os.path.join(DATA_DIR, "indices", "SP500.csv")
        df_sp = cargar_csv(ruta_sp, skiprows=[1, 2])

        if not df_sp.empty and "Close" in df_sp.columns:
            corte_dash = periodos_map_dash.get(periodo_dash, -66)
            if corte_dash is None:
                df_sp_plot = df_sp.copy()
            else:
                df_sp_plot = df_sp.iloc[corte_dash:].copy()

            fig_sp = go.Figure()
            fig_sp.add_trace(go.Scatter(
                x=df_sp_plot.index, y=df_sp_plot["Close"],
                fill="tozeroy",
                fillcolor="rgba(0,102,204,0.15)",
                line=dict(color="#0066cc", width=2.5),
                name="S&P 500",
            ))
            fig_sp.update_layout(
                paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
                height=320, margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(
                    gridcolor="rgba(197,168,96,0.12)",
                    color="rgba(255,255,255,0.4)",
                    tickfont=dict(color="rgba(255,255,255,0.45)", size=9),
                    showgrid=True,
                ),
                yaxis=dict(
                    gridcolor="rgba(197,168,96,0.12)",
                    color="rgba(255,255,255,0.4)",
                    tickfont=dict(color="rgba(255,255,255,0.45)", size=9),
                    showgrid=True,
                    tickformat=",.0f",
                ),
                showlegend=False,
                font=dict(size=10, color="rgba(255,255,255,0.45)"),
            )
            st.plotly_chart(fig_sp, use_container_width=True)
        else:
            st.markdown("""
            <div style="background:#fff;height:320px;border:1px solid rgba(197,168,96,0.12);
                        border-radius:4px;display:flex;align-items:center;justify-content:center;
                        color:rgba(197,168,96,0.35);font-size:0.75rem;letter-spacing:2px;">
              Cargando mercados...
            </div>""", unsafe_allow_html=True)

        # Curva de Rendimientos UST bajo el gráfico SP500
        if not df_macro.empty:
            st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:#c5a860;font-weight:700;padding:6px 0 8px;border-bottom:1px solid rgba(197,168,96,0.3);margin:14px 0 10px;">CURVA UST — Yield Curve</div>', unsafe_allow_html=True)
            df_usd_c = df_macro[df_macro["Categoría"] == "TASAS UST"].dropna(subset=["Último Valor"])
            if not df_usd_c.empty:
                fig_c = go.Figure(go.Scatter(
                    x=df_usd_c["Activo"], y=df_usd_c["Último Valor"],
                    mode="lines+markers",
                    line=dict(color=ORO, width=2),
                    marker=dict(size=7, color=ORO, line=dict(color="#0a0a0a", width=1)),
                    fill="tozeroy", fillcolor="rgba(197,168,96,0.05)",
                ))
                fig_c.update_layout(
                    paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                    height=200, margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(gridcolor=GRID, color="rgba(80,60,10,0.6)"),
                    yaxis=dict(gridcolor=GRID, color="rgba(80,60,10,0.6)", title="Yield %"),
                    showlegend=False,
                    font=dict(size=10, color="rgba(80,60,10,0.6)"),
                )
                st.plotly_chart(fig_c, use_container_width=True)

    # ── RIGHT COLUMN ─────────────────────────────────────────────
    with col_right:
        if not df_macro.empty:
            # Commodities
            df_com = df_macro[df_macro["Categoría"] == "COMMODITIES"]
            filas_com = []
            for _, r in df_com.iterrows():
                val = float(r.get("Último Valor", 0) or 0)
                filas_com.append((
                    str(r.get("Activo", ""))[:14],
                    f"{val:,.2f}" if val < 10000 else f"{val:,.0f}",
                    float(r.get("Cambio Día %", 0) or 0),
                ))
            if filas_com:
                st.markdown(tabla_html("COMMODITIES", filas_com), unsafe_allow_html=True)

        # Top gainers / losers from SP500 Empresas
        df_emp = cargar_hoja(os.path.join(DATA_DIR, "TRADING_DATA.xlsx"), "SP500 Empresas")
        if not df_emp.empty and "Cambio Día %" in df_emp.columns and "Ticker" in df_emp.columns:
            df_emp_s = df_emp.dropna(subset=["Cambio Día %"]).copy()
            df_emp_s["Cambio Día %"] = pd.to_numeric(df_emp_s["Cambio Día %"], errors="coerce")
            df_emp_s = df_emp_s.dropna(subset=["Cambio Día %"])

            # Mayores alzas
            top5 = df_emp_s.nlargest(5, "Cambio Día %")
            filas_top = []
            for _, r in top5.iterrows():
                filas_top.append((
                    str(r.get("Ticker", ""))[:8],
                    f"${float(r.get('Último Precio', 0) or 0):,.2f}",
                    float(r.get("Cambio Día %", 0) or 0),
                ))
            if filas_top:
                st.markdown(tabla_html("MAYORES ALZAS", filas_top), unsafe_allow_html=True)

            # Mayores bajas
            bot5 = df_emp_s.nsmallest(5, "Cambio Día %")
            filas_bot = []
            for _, r in bot5.iterrows():
                filas_bot.append((
                    str(r.get("Ticker", ""))[:8],
                    f"${float(r.get('Último Precio', 0) or 0):,.2f}",
                    float(r.get("Cambio Día %", 0) or 0),
                ))
            if filas_bot:
                st.markdown(tabla_html("MAYORES BAJAS", filas_bot), unsafe_allow_html=True)

    # ── SEGUNDA FILA: Breadth + Noticias preview ─────────────────
    st.markdown("<hr style='margin:18px 0 14px;border-color:rgba(197,168,96,0.18)!important;'>", unsafe_allow_html=True)
    br_left, br_center, br_right = st.columns([2.4, 4.8, 2.4])

    with br_left:
        # ── Market Breadth (cuántas subieron/bajaron) ─────────────
        st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:#a07820;font-weight:700;padding:5px 0 8px;border-bottom:1.5px solid rgba(197,168,96,0.3);margin-bottom:10px;">AMPLITUD DE MERCADO</div>', unsafe_allow_html=True)

        df_emp_all = cargar_hoja(os.path.join(DATA_DIR, "TRADING_DATA.xlsx"), "SP500 Empresas")
        df_nq_all  = cargar_hoja(os.path.join(DATA_DIR, "TRADING_DATA.xlsx"), "Nasdaq100 Empresas")

        for nombre_idx, df_idx_b in [("S&P 500", df_emp_all), ("Nasdaq 100", df_nq_all)]:
            if df_idx_b.empty or "Cambio Día %" not in df_idx_b.columns:
                continue
            df_b = df_idx_b.dropna(subset=["Cambio Día %"]).copy()
            df_b["Cambio Día %"] = pd.to_numeric(df_b["Cambio Día %"], errors="coerce")
            n_up  = int((df_b["Cambio Día %"] > 0).sum())
            n_dn  = int((df_b["Cambio Día %"] < 0).sum())
            n_tot = len(df_b)
            pct_up = n_up / n_tot * 100 if n_tot > 0 else 0
            color_breadth = "#0066cc" if pct_up >= 50 else "#cc3300"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#fdf9f2,#f5ede0);
                        border:1.5px solid rgba(197,168,96,0.45);border-left:3px solid #c5a860;
                        border-radius:6px;padding:10px 14px;margin-bottom:10px;">
              <div style="font-size:0.6rem;letter-spacing:2px;text-transform:uppercase;
                          color:#a07820;font-weight:700;margin-bottom:6px;">{nombre_idx}</div>
              <div style="display:flex;gap:12px;align-items:center;">
                <div style="text-align:center;">
                  <div style="color:#0066cc;font-size:1.1rem;font-weight:800;
                              font-family:'Playfair Display',serif;">{n_up}</div>
                  <div style="font-size:0.6rem;color:#6b5a2a;letter-spacing:1px;">ALZAN</div>
                </div>
                <div style="text-align:center;">
                  <div style="color:#cc3300;font-size:1.1rem;font-weight:800;
                              font-family:'Playfair Display',serif;">{n_dn}</div>
                  <div style="font-size:0.6rem;color:#6b5a2a;letter-spacing:1px;">CAEN</div>
                </div>
                <div style="flex:1;background:#e8e4da;border-radius:4px;height:8px;overflow:hidden;">
                  <div style="width:{pct_up:.1f}%;background:{color_breadth};height:100%;border-radius:4px;"></div>
                </div>
                <div style="color:{color_breadth};font-size:0.78rem;font-weight:700;">{pct_up:.0f}%</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Noticias preview (últimas 4) ──────────────────────────
        st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:#a07820;font-weight:700;padding:5px 0 8px;border-bottom:1.5px solid rgba(197,168,96,0.3);margin-bottom:10px;margin-top:4px;">ÚLTIMAS NOTICIAS</div>', unsafe_allow_html=True)
        df_news_p = cargar_noticias()
        if not df_news_p.empty and "Relevante" in df_news_p.columns:
            df_news_p = df_news_p[df_news_p["Relevante"] == "SÍ"].head(4)
        for _, nr in df_news_p.head(4).iterrows():
            tit = str(nr.get("Título", ""))[:80]
            fnt = str(nr.get("Fuente", "")).upper()
            url = str(nr.get("URL", "#"))
            st.markdown(f"""
            <div style="padding:7px 0;border-bottom:1px solid rgba(197,168,96,0.1);">
              <div style="font-size:0.58rem;color:#a07820;letter-spacing:2px;font-weight:700;margin-bottom:3px;">{fnt}</div>
              <a href="{url}" target="_blank" style="color:#0a0a0a;text-decoration:none;
                 font-size:0.76rem;line-height:1.4;">{tit}...</a>
            </div>
            """, unsafe_allow_html=True)

    with br_center:
        # ── Resultados de Cías + Upgrades/Downgrades ──────────────
        tab_earn, tab_upgr, tab_econ = st.tabs(["◆ Resultados Cías.", "◎ Upgrades/Downgrades", "◈ Eventos Económicos"])

        with tab_earn:
            st.markdown('<div style="font-size:0.62rem;color:#6b5a2a;letter-spacing:2px;margin-bottom:10px;">Earnings más recientes del S&P 500 — datos en tiempo real</div>', unsafe_allow_html=True)
            try:
                import yfinance as yf
                tickers_earn = ["AAPL","MSFT","AMZN","GOOGL","META","NVDA","TSLA","JPM","V","UNH"]
                earn_rows = []
                for tk in tickers_earn:
                    try:
                        t_obj = yf.Ticker(tk)
                        cal = t_obj.calendar
                        if cal is not None and not cal.empty:
                            earn_date = str(list(cal.get("Earnings Date", [None]))[0])[:10] if "Earnings Date" in cal else "N/D"
                        else:
                            earn_date = "N/D"
                        fi = t_obj.fast_info
                        earn_rows.append({
                            "Ticker": tk,
                            "Próx. Earnings": earn_date,
                            "Precio": f"${fi.get('last_price', 0):,.2f}" if hasattr(fi, "get") else "-",
                        })
                    except Exception:
                        earn_rows.append({"Ticker": tk, "Próx. Earnings": "N/D", "Precio": "-"})
                if earn_rows:
                    df_earn = pd.DataFrame(earn_rows)
                    st.dataframe(df_earn, hide_index=True, use_container_width=True)
            except Exception as e:
                st.markdown(f'<div style="color:#cc3300;font-size:0.75rem;">Error cargando earnings: {e}</div>', unsafe_allow_html=True)

        with tab_upgr:
            st.markdown('<div style="font-size:0.62rem;color:#6b5a2a;letter-spacing:2px;margin-bottom:10px;">Upgrades y Downgrades recientes — top tickers</div>', unsafe_allow_html=True)
            try:
                import yfinance as yf
                tickers_upgr = ["AAPL","MSFT","NVDA","META","AMZN","GOOGL","TSLA","JPM","GS","BAC"]
                upgr_rows = []
                for tk in tickers_upgr:
                    try:
                        t_obj = yf.Ticker(tk)
                        recs = t_obj.recommendations
                        if recs is not None and not recs.empty:
                            last = recs.sort_index().iloc[-1]
                            firma = str(last.get("Firm", last.get("firm", "N/D")))
                            accion = str(last.get("To Grade", last.get("toGrade", "N/D")))
                            upgr_rows.append({"Ticker": tk, "Firma": firma[:20], "Calificación": accion})
                    except Exception:
                        pass
                if upgr_rows:
                    df_upgr = pd.DataFrame(upgr_rows)
                    def color_upgr(val):
                        v = str(val).lower()
                        if any(x in v for x in ["buy","outperform","strong","overweight"]):
                            return "color:#0066cc;font-weight:700"
                        if any(x in v for x in ["sell","under","reduce","downgrade"]):
                            return "color:#cc3300;font-weight:700"
                        return "color:#0a0a0a"
                    st.dataframe(
                        df_upgr.style.map(color_upgr, subset=["Calificación"]),
                        hide_index=True, use_container_width=True
                    )
                else:
                    st.info("Sin datos de upgrades/downgrades disponibles")
            except Exception as e:
                st.markdown(f'<div style="color:#cc3300;font-size:0.75rem;">Error: {e}</div>', unsafe_allow_html=True)

        with tab_econ:
            st.markdown('<div style="font-size:0.62rem;color:#6b5a2a;letter-spacing:2px;margin-bottom:10px;">Principales eventos económicos de la semana</div>', unsafe_allow_html=True)
            # Eventos económicos — datos estáticos actualizados manualmente o via futuro script
            eventos_eco = [
                {"Día": "Lunes",    "Evento": "ISM Manufacturing PMI (EE.UU.)",       "Impacto": "ALTO",  "País": "🇺🇸"},
                {"Día": "Martes",   "Evento": "JOLTS Job Openings",                   "Impacto": "ALTO",  "País": "🇺🇸"},
                {"Día": "Miércoles","Evento": "ADP Non-Farm Employment",              "Impacto": "MEDIO", "País": "🇺🇸"},
                {"Día": "Miércoles","Evento": "FOMC Minutes",                          "Impacto": "ALTO",  "País": "🇺🇸"},
                {"Día": "Jueves",   "Evento": "Initial Jobless Claims",               "Impacto": "MEDIO", "País": "🇺🇸"},
                {"Día": "Viernes",  "Evento": "Non-Farm Payrolls",                    "Impacto": "ALTO",  "País": "🇺🇸"},
                {"Día": "Viernes",  "Evento": "Unemployment Rate",                    "Impacto": "ALTO",  "País": "🇺🇸"},
            ]
            for ev in eventos_eco:
                imp_color = "#cc3300" if ev["Impacto"] == "ALTO" else "#e6a817"
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:7px 10px;
                            border-bottom:1px solid rgba(197,168,96,0.1);
                            background:rgba(197,168,96,0.03);border-radius:3px;margin-bottom:4px;">
                  <div style="font-size:0.65rem;color:#6b5a2a;font-weight:700;min-width:60px;">{ev['Día'][:3].upper()}</div>
                  <div style="font-size:0.8rem;color:#0a0a0a;flex:1;">{ev['País']} {ev['Evento']}</div>
                  <div style="font-size:0.6rem;font-weight:700;color:{imp_color};
                              border:1px solid {imp_color};padding:2px 8px;border-radius:3px;">{ev['Impacto']}</div>
                </div>
                """, unsafe_allow_html=True)

    with br_right:
        # ── Podcast preview ────────────────────────────────────────
        st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:#a07820;font-weight:700;padding:5px 0 8px;border-bottom:1.5px solid rgba(197,168,96,0.3);margin-bottom:10px;">PODCASTS RECIENTES</div>', unsafe_allow_html=True)
        df_pod = cargar_social("PODCAST")
        if not df_pod.empty:
            for _, pr in df_pod.head(5).iterrows():
                tit_p = str(pr.get("Título", ""))[:60]
                fnt_p = str(pr.get("Fuente", "")).upper()
                url_p = str(pr.get("URL", "#"))
                st.markdown(f"""
                <div style="padding:8px 0;border-bottom:1px solid rgba(197,168,96,0.1);">
                  <div style="font-size:0.58rem;color:#c5a860;letter-spacing:2px;font-weight:700;margin-bottom:3px;">◎ {fnt_p}</div>
                  <a href="{url_p}" target="_blank"
                     style="color:#0a0a0a;text-decoration:none;font-size:0.75rem;line-height:1.4;">{tit_p}...</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:rgba(197,168,96,0.4);font-size:0.72rem;letter-spacing:1px;">Sin podcasts — ejecuta src/09_social_media.py</div>', unsafe_allow_html=True)

        # ── Gráfico Variación por categoría ───────────────────────
        if not df_macro.empty:
            st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:#a07820;font-weight:700;padding:5px 0 8px;border-bottom:1.5px solid rgba(197,168,96,0.3);margin-bottom:10px;margin-top:14px;">VARIACIÓN POR CATEGORÍA</div>', unsafe_allow_html=True)
            cat_sel = st.selectbox("", ["COMMODITIES", "ÍNDICES", "MONEDAS", "TASAS UST"], key="cat_bar_dash", label_visibility="collapsed")
            fig_bar = grafico_barras(df_macro, cat_sel)
            if fig_bar.data:
                st.plotly_chart(fig_bar, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PÁGINA 2 — ANÁLISIS TÉCNICO
# ══════════════════════════════════════════════════════════════════

elif "Técnico" in pagina:
    # ── Pre-selección desde Screener (query params) ──────────────
    _at_ticker_qp = st.query_params.get("ticker", None)
    _at_indice_qp = st.query_params.get("indice", None)
    if _at_ticker_qp and _at_indice_qp:
        _presel_flag = f"_presel_{_at_ticker_qp}_{_at_indice_qp}"
        if not st.session_state.get(_presel_flag):
            _mercado_from_qp = {
                "SP500":     "Empresas SP500",
                "Nasdaq100": "Empresas Nasdaq100",
                "Dow30":     "Empresas Dow30",
            }.get(_at_indice_qp, "Empresas SP500")
            st.session_state["at_mercado"] = _mercado_from_qp
            st.session_state["at_emp"]     = _at_ticker_qp
            st.session_state[_presel_flag] = True
        # Banner de contexto (siempre visible mientras esté el QP)
        st.markdown(
            f"<div style='background:rgba(197,168,96,0.12);border-left:3px solid #c5a860;"
            f"border-radius:4px;padding:9px 14px;font-size:.76rem;color:#0a0a0a;"
            f"margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;'>"
            f"<span>📊 Señal detectada en <b style='font-family:Playfair Display,serif;"
            f"font-size:.95rem;'>{_at_ticker_qp}</b> &nbsp;<span style='font-size:.6rem;"
            f"color:rgba(107,90,42,0.6);'>{_at_indice_qp}</span></span>"
            f"<a href='?page=screener' style='color:#c5a860;text-decoration:none;"
            f"font-size:.68rem;letter-spacing:1px;'>← Volver a Señales</a></div>",
            unsafe_allow_html=True,
        )

    st.markdown("""
    <div style="padding:0 0 14px;">
      <span style="font-family:'Playfair Display',serif;font-size:1.3rem;
                   color:#ffffff;letter-spacing:4px;text-transform:uppercase;">
        Análisis Técnico
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Selector de mercado + período ────────────────────────────
    sel_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    with sel_cols[0]:
        mercado = st.selectbox(
            "Mercado",
            ["Índices", "Commodities", "Empresas SP500", "Empresas Nasdaq100", "Empresas Dow30"],
            key="at_mercado",
        )

    # Period buttons
    periodos_map = {"1D": -1, "2D": -2, "1S": -5, "1M": -22, "3M": -66, "6M": -126, "1A": -252, "YTD": 0, "3A": -756, "5A": None}
    periodo_actual = st.session_state.get("periodo_sel", "1A")
    for i, (label, _) in enumerate(list(periodos_map.items())[:11]):
        with sel_cols[i + 1]:
            if st.button(label, key=f"per_{label}", use_container_width=True):
                st.session_state["periodo_sel"] = label
                st.rerun()

    periodo_actual = st.session_state.get("periodo_sel", "1A")

    # ── Selector de Tamaño de Barra (solo para 1D / 2D) ──────────
    es_intraday = periodo_actual in ("1D", "2D")
    if es_intraday:
        _barras_opts = _BARRAS_1D if periodo_actual == "1D" else _BARRAS_2D
        barra_actual = st.session_state.get("barra_sel", _barras_opts[1][1])  # default 5m
        # Si el barra_actual no es válido para este período, resetear
        if barra_actual not in [b[1] for b in _barras_opts]:
            barra_actual = _barras_opts[1][1]
        st.markdown(
            "<div style='font-size:.62rem;color:rgba(107,90,42,0.8);letter-spacing:2px;"
            "text-transform:uppercase;font-weight:700;margin-bottom:6px;'>TAMAÑO DE BARRA</div>",
            unsafe_allow_html=True,
        )
        _bcols = st.columns([1] * len(_barras_opts) + [4])
        for _bi, (_blabel, _bval) in enumerate(_barras_opts):
            with _bcols[_bi]:
                _active = barra_actual == _bval
                _btn_style = (
                    f"background:{'#c5a860' if _active else '#ffffff'} !important;"
                    f"color:{'#0a0a0a' if _active else '#6b5a2a'} !important;"
                    f"border:1.5px solid #c5a860 !important;font-weight:{'800' if _active else '600'} !important;"
                )
                st.markdown(f"<style>#barra_btn_{_bval} button{{{_btn_style}}}</style>", unsafe_allow_html=True)
                if st.button(_blabel, key=f"barra_btn_{_bval}", use_container_width=True):
                    st.session_state["barra_sel"] = _bval
                    st.rerun()
        barra_actual = st.session_state.get("barra_sel", _barras_opts[1][1])
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-size:.7rem;color:rgba(197,168,96,0.6);letter-spacing:2px;"
        f"margin-bottom:10px;'>PERÍODO ACTIVO: <b style='color:{ORO};'>{periodo_actual}</b>"
        + (f" &nbsp;·&nbsp; BARRA: <b style='color:{ORO};'>{st.session_state.get('barra_sel','5m')}</b>" if es_intraday else "")
        + "</div>",
        unsafe_allow_html=True,
    )

    def get_corte(label, df_index=None):
        if label == "YTD":
            return pd.Timestamp(datetime.now().year, 1, 1)
        return {"1D": -1, "2D": -2, "1S": -5, "1M": -22, "3M": -66, "6M": -126, "1A": -252, "3A": -756, "5A": None}.get(label, -252)

    # ── Selección de instrumento ─────────────────────────────────
    if mercado == "Índices":
        ops = {
            "S&P 500":   ("SP500",        "indices"),
            "Nasdaq":    ("NASDAQ_COMP",   "indices"),
            "Dow Jones": ("DOW_JONES",     "indices"),
        }
        sel = st.selectbox("Instrumento", list(ops.keys()), key="at_inst_idx")
        nombre_arch, sub = ops[sel]; titulo = sel
        ruta = os.path.join(DATA_DIR, sub, f"{nombre_arch}.csv")

    elif mercado == "Commodities":
        ops = {
            "Oro":           "Oro",
            "Petróleo WTI":  "Petroleo_WTI",
            "Plata":         "Plata",
            "Cobre":         "Cobre",
            "Bitcoin":       "Bitcoin",
            "Litio ETF":     "Litio_ETF",
            "Albemarle":     "Albemarle_Litio",
            "SQM":           "SQM_Litio",
        }
        sel = st.selectbox("Instrumento", list(ops.keys()), key="at_inst_cmd")
        nombre_arch = ops[sel]; titulo = sel
        ruta = os.path.join(DATA_DIR, "commodities", f"{nombre_arch}.csv")

    else:
        raw = {"Empresas SP500": "sp500", "Empresas Nasdaq100": "nasdaq100", "Empresas Dow30": "dow30"}[mercado]
        hoja = {
            "Empresas SP500":   "SP500 Empresas",
            "Empresas Nasdaq100": "Nasdaq100 Empresas",
            "Empresas Dow30":   "Dow30 Empresas",
        }[mercado]
        df_lista = cargar_hoja(os.path.join(DATA_DIR, "TRADING_DATA.xlsx"), hoja)
        cb, co = st.columns([2, 1])
        with cb:
            buscar = st.text_input("Buscar ticker", "", key="at_buscar").upper()
        with co:
            orden = st.selectbox("Ordenar", ["Cambio Día %", "Cambio 1M %", "Cambio 1A %"], key="at_orden")
        if not df_lista.empty:
            df_f = df_lista[df_lista["Ticker"].str.contains(buscar, na=False)] if buscar else df_lista
            sel = st.selectbox("Empresa", df_f.sort_values(orden, ascending=False)["Ticker"].tolist(), key="at_emp")
        else:
            sel = st.text_input("Ticker", "AAPL", key="at_ticker_manual").upper()
        titulo = sel
        ruta = os.path.join(DATA_DIR, "raw", raw, f"{sel}.csv")

    # ── Selector de indicadores ──────────────────────────────────
    st.markdown('<div class="section-header" style="margin-top:10px;">INDICADORES</div>', unsafe_allow_html=True)
    todos = [
        "EMA 10", "EMA 20", "EMA 50", "EMA 100", "EMA 200",
        "Bollinger Bands", "Fibonacci", "TD Sequential",
        "MACD", "RSI", "VWAP",
    ]
    defaults = ["EMA 50", "EMA 200", "MACD", "RSI"]
    colores_chip = {
        "EMA 10":          "#00e5ff",
        "EMA 20":          INST["ema20"],
        "EMA 50":          INST["ema50"],
        "EMA 100":         INST["ema100"],
        "EMA 200":         INST["ema200"],
        "Bollinger Bands": INST["bb"],
        "Fibonacci":       "#ff9966",
        "TD Sequential":   "#00cc55",
        "MACD":            INST["macd"],
        "RSI":             INST["rsi"],
        "VWAP":            "#ff9800",
    }
    cols_cb = st.columns(len(todos))
    indicadores_sel = []
    for i, ind in enumerate(todos):
        with cols_cb[i]:
            dot_color = colores_chip.get(ind, ORO)
            st.markdown(
                f"<div style='text-align:center;color:{dot_color};font-size:.85rem;margin-bottom:2px;'>●</div>",
                unsafe_allow_html=True,
            )
            if st.checkbox(ind, value=(ind in defaults), key=f"cb_{ind}"):
                indicadores_sel.append(ind)

    st.markdown("<hr style='margin:10px 0;border-color:rgba(197,168,96,0.15)!important;'>", unsafe_allow_html=True)

    # ── Gráfico ──────────────────────────────────────────────────
    _yf_tick = _TICKER_MAP.get(titulo, titulo)

    if es_intraday:
        # Modo intraday: datos en tiempo real desde yfinance
        _barra_load = st.session_state.get("barra_sel",
                      (_BARRAS_1D if periodo_actual == "1D" else _BARRAS_2D)[1][1])
        with st.spinner(f"Cargando datos intraday {_barra_load.replace('_10m','10m')} ..."):
            df_plot = cargar_intraday(_yf_tick, _barra_load, periodo_actual)
        _data_empty = df_plot.empty
    else:
        df_raw = cargar_csv(ruta, skiprows=[1, 2])
        _data_empty = df_raw.empty
        if not _data_empty:
            corte = get_corte(periodo_actual)
            if corte is None:
                df_plot = df_raw.copy()
            elif isinstance(corte, pd.Timestamp):
                df_plot = df_raw[df_raw.index >= corte].copy()
            else:
                df_plot = df_raw.iloc[corte:].copy()

    if _data_empty:
        st.markdown(f"""
        <div style="background:#ffffff;border:1px solid rgba(197,168,96,0.2);border-radius:4px;
                    padding:24px;text-align:center;color:rgba(197,168,96,0.5);
                    font-size:0.8rem;letter-spacing:2px;">
          SIN DATOS DISPONIBLES PARA <b>{titulo}</b>
        </div>""", unsafe_allow_html=True)
    else:
        if not indicadores_sel:
            st.markdown("""
            <div style="background:#ffffff;border:1px solid rgba(197,168,96,0.15);
                        border-radius:4px;padding:16px;color:rgba(197,168,96,0.6);
                        font-size:0.78rem;letter-spacing:1px;text-align:center;">
              Selecciona al menos un indicador para visualizar el gráfico
            </div>""", unsafe_allow_html=True)
        else:
            fig, tabla_ind = grafico_interactivo(df_plot, titulo, indicadores_sel)
            st.plotly_chart(fig, use_container_width=True)

            # ── Indicadores + Métricas de Riesgo ──────────────────
            col_ind, col_risk = st.columns([1.2, 1])

            with col_ind:
                st.markdown('<div class="section-header">VALORES ACTUALES DE INDICADORES</div>', unsafe_allow_html=True)
                if tabla_ind:
                    filas = []
                    for nombre_i, vals in tabla_ind.items():
                        for k, v in vals.items():
                            filas.append({"Indicador": nombre_i, "Métrica": k, "Valor": str(v)})
                    df_tab = pd.DataFrame(filas)

                    def color_val(val):
                        v = str(val)
                        if any(x in v for x in ["COMPRA", "Sobre", "ALCISTA", "BUY", "↑"]):
                            return "color:#0066cc;font-weight:700"
                        if any(x in v for x in ["VENTA", "Bajo", "BAJISTA", "SELL", "↓"]):
                            return "color:#cc3300;font-weight:700"
                        return "color:#0a0a0a"

                    st.dataframe(
                        df_tab.style.map(color_val, subset=["Valor"]),
                        width="stretch", hide_index=True, height=300,
                    )

            with col_risk:
                st.markdown('<div class="section-header">MÉTRICAS DE RIESGO</div>', unsafe_allow_html=True)
                ruta_sp2 = os.path.join(DATA_DIR, "indices", "SP500.csv")
                df_sp2 = cargar_csv(ruta_sp2, skiprows=[1, 2])
                bench = df_sp2["Close"].reindex(df_plot.index).ffill() if not df_sp2.empty else None
                metricas = calc_metricas_riesgo(df_plot["Close"].dropna(), len(df_plot), bench)
                if metricas:
                    cols_r = st.columns(2)
                    for i, (k, v) in enumerate(metricas.items()):
                        with cols_r[i % 2]:
                            color = (
                                "#4da6ff" if "+" in str(v) and "Sharpe" not in k and "Beta" not in k
                                else ("#ff6644" if "-" in str(v) and "Sharpe" not in k and "Beta" not in k
                                      else "#0a0a0a")
                            )
                            st.markdown(f"""
                            <div class="dark-card" style="padding:10px 14px;margin-bottom:6px;">
                              <div class="dark-card-label">{k}</div>
                              <div style="font-size:1.05rem;font-weight:700;color:{color};
                                          margin-top:3px;font-family:'Playfair Display',serif;">{v}</div>
                            </div>""", unsafe_allow_html=True)

        # ── Mini métricas de precio ────────────────────────────────
        close = df_plot["Close"].dropna()
        if len(close) >= 2:
            st.markdown("<hr style='margin:10px 0;border-color:rgba(197,168,96,0.12)!important;'>", unsafe_allow_html=True)
            u = float(close.iloc[-1]); a = float(close.iloc[-2])
            vol_usd_20 = None
            if "Volume" in df_plot.columns:
                vol_usd_20 = float((df_plot["Volume"] * df_plot["Close"]).tail(20).mean())
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Último precio", f"{u:,.2f}", f"{round((u / a - 1) * 100, 2)}%")
            c2.metric("Máx período",   f"{float(df_plot['High'].max()):,.2f}" if "High" in df_plot.columns else "-")
            c3.metric("Mín período",   f"{float(df_plot['Low'].min()):,.2f}"  if "Low"  in df_plot.columns else "-")
            c4.metric("Vol USD 20d",   f"${vol_usd_20/1e9:.2f}B" if vol_usd_20 and vol_usd_20 > 1e9
                                        else (f"${vol_usd_20/1e6:.1f}M" if vol_usd_20 else "-"))
            acciones = None
            _ticker_yf_map = {
                "S&P 500":      "^GSPC",  "Nasdaq":       "^IXIC",  "Dow Jones":    "^DJI",
                "Oro":          "GC=F",   "Petróleo WTI": "CL=F",   "Plata":        "SI=F",
                "Cobre":        "HG=F",   "Bitcoin":      "BTC-USD", "Litio ETF":   "LIT",
                "Albemarle":    "ALB",    "SQM":          "SQM",
            }
            _yf_ticker = _ticker_yf_map.get(titulo, titulo)
            try:
                import yfinance as yf
                info = yf.Ticker(_yf_ticker).fast_info
                acciones = info.get("shares", None)
            except Exception:
                pass
            c5.metric("Acciones (M)", f"{acciones/1e6:,.0f}" if acciones else "-")
            c6.metric("Días en gráfico", f"{len(close)}")

        # ── Análisis Multitemporal de Velas ───────────────────────
        st.markdown("<hr style='margin:14px 0;border-color:rgba(197,168,96,0.15)!important;'>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">ANÁLISIS MULTITEMPORAL DE VELAS</div>', unsafe_allow_html=True)

        _ticker_yf_map2 = {
            "S&P 500":      "^GSPC",  "Nasdaq":       "^IXIC",  "Dow Jones":    "^DJI",
            "Oro":          "GC=F",   "Petróleo WTI": "CL=F",   "Plata":        "SI=F",
            "Cobre":        "HG=F",   "Bitcoin":      "BTC-USD", "Litio ETF":   "LIT",
            "Albemarle":    "ALB",    "SQM":          "SQM",
        }
        _yf_ticker2 = _ticker_yf_map2.get(titulo, titulo)
        _label_tipo = "corto plazo" if periodo_actual in _PERIODOS_CORTOS else "mediano/largo plazo"
        st.markdown(
            f"<div style='font-size:.7rem;color:rgba(197,168,96,0.55);letter-spacing:2px;"
            f"margin-bottom:12px;'>PERÍODO ACTIVO: <b>{periodo_actual}</b> — "
            f"Temporalidades de <b>{_label_tipo}</b></div>",
            unsafe_allow_html=True,
        )

        with st.spinner("Descargando datos multitemporal..."):
            _mt_resultados = analisis_multitemporal(_yf_ticker2, periodo_actual)

        if not _mt_resultados:
            st.markdown(
                "<div style='color:rgba(197,168,96,0.45);font-size:.8rem;'>Sin datos disponibles para análisis multitemporal.</div>",
                unsafe_allow_html=True,
            )
        else:
            _mt_cols = st.columns(len(_mt_resultados))
            for _ci, _r in enumerate(_mt_resultados):
                with _mt_cols[_ci]:
                    st.markdown(f"""
                    <div style="background:#0d0d0d;border:1px solid rgba(197,168,96,0.2);
                                border-radius:6px;padding:12px 10px;text-align:center;">
                      <div style="font-size:.65rem;color:{ORO};letter-spacing:2px;
                                  font-weight:700;margin-bottom:8px;">{_r['tf'].upper()}</div>
                      <div style="font-size:.72rem;color:#777;margin-bottom:4px;">VELA</div>
                      <div style="font-size:.88rem;font-weight:700;color:{_r['vela_col']};
                                  margin-bottom:8px;">{'▲' if _r['vela']=='ALCISTA' else '▼'} {_r['vela']}</div>
                      <div style="font-size:.72rem;color:#777;margin-bottom:4px;">TENDENCIA EMA</div>
                      <div style="font-size:.88rem;font-weight:700;color:{_r['tend_col']};
                                  margin-bottom:8px;">{'▲' if _r['tendencia']=='ALCISTA' else '▼'} {_r['tendencia']}</div>
                      <div style="font-size:.72rem;color:#777;margin-bottom:4px;">RSI {_r['rsi']}</div>
                      <div style="font-size:.82rem;font-weight:700;color:{_r['rsi_col']};
                                  margin-bottom:10px;">{_r['rsi_txt']}</div>
                      <div style="border-top:1px solid rgba(197,168,96,0.15);padding-top:8px;
                                  font-size:.95rem;font-weight:900;color:{_r['señal_col']};
                                  letter-spacing:1px;">{_r['señal']}</div>
                    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PÁGINA 3 — SCREENER / SEÑALES
# ══════════════════════════════════════════════════════════════════

elif "Screener" in pagina:
    st.markdown("""
    <div style="padding:0 0 10px;">
      <span style="font-family:'Playfair Display',serif;font-size:1.3rem;
                   color:#ffffff;letter-spacing:4px;text-transform:uppercase;">
        Screener · Señales de Trading
      </span>
      <div style="font-size:.62rem;color:rgba(197,168,96,0.55);letter-spacing:2px;
                  margin-top:5px;text-transform:uppercase;">
        MACD Crossover · TD Sequential Setup 9
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Botones de período ───────────────────────────────────────
    _SC_PERIODOS = [
        ("Diario",     5,  "D"),
        ("Semanal",    22, "S"),
        ("Trimestral", 66, "T"),
    ]
    if "sc_periodo" not in st.session_state:
        st.session_state["sc_periodo"] = "Diario"

    st.markdown(
        "<div style='font-size:.62rem;color:#a07820;letter-spacing:3px;"
        "text-transform:uppercase;font-weight:700;margin-bottom:8px;'>PERÍODO DE ANÁLISIS</div>",
        unsafe_allow_html=True,
    )
    _per_cols = st.columns([1, 1, 1, 3])
    for _pi, (_plabel, _pdias, _pkey) in enumerate(_SC_PERIODOS):
        with _per_cols[_pi]:
            _is_active_per = st.session_state["sc_periodo"] == _plabel
            if _is_active_per:
                st.markdown(
                    f"<div style='background:#c5a860;color:#0a0a0a;text-align:center;"
                    f"padding:9px 4px;border-radius:4px;font-size:.78rem;font-weight:800;"
                    f"letter-spacing:2px;cursor:default;border:1.5px solid #c5a860;'>"
                    f"{_plabel}</div>",
                    unsafe_allow_html=True,
                )
            else:
                if st.button(_plabel, key=f"sc_per_{_pkey}", use_container_width=True):
                    st.session_state["sc_periodo"] = _plabel
                    st.rerun()

    _sc_ventana_lbl = st.session_state["sc_periodo"]
    _sc_ventana = {lbl: d for lbl, d, _ in _SC_PERIODOS}[_sc_ventana_lbl]

    st.markdown(
        f"<div style='font-size:.68rem;color:rgba(197,168,96,0.55);letter-spacing:2px;"
        f"margin:6px 0 10px;'>PERÍODO ACTIVO: <b style='color:#c5a860;'>{_sc_ventana_lbl}</b>"
        f" &nbsp;·&nbsp; {_sc_ventana} días de trading</div>",
        unsafe_allow_html=True,
    )

    # ── Filtros secundarios ──────────────────────────────────────
    _scc1, _scc2, _scc3 = st.columns([2, 2, 1])
    with _scc1:
        _sc_indice = st.selectbox("Índice", ["Todos", "SP500", "Nasdaq100", "Dow30"], key="sc_idx")
    with _scc2:
        _sc_orden = st.selectbox("Ordenar", ["Ticker ↑", "Cambio% ↓", "Fecha ↓"], key="sc_ord")
    with _scc3:
        st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
        if st.button("↺ Scan", key="sc_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.spinner(f"Escaneando {_sc_ventana_lbl} ({_sc_ventana}d) en +600 empresas..."):
        _df_sc = screener_señales(ventana=_sc_ventana)

    if _df_sc.empty:
        st.warning("Sin datos. Ejecuta src/01_descargar_datos_historicos.py primero.")
    else:
        # Filtro índice
        if _sc_indice != "Todos":
            _df_sc = _df_sc[_df_sc["Índice"] == _sc_indice]

        # Orden
        if _sc_orden == "Fecha ↓":
            _df_sc = _df_sc.sort_values("Fecha", ascending=False)
        elif _sc_orden == "Cambio% ↓":
            _df_sc = _df_sc.sort_values("Cambio%", ascending=False)
        else:
            _df_sc = _df_sc.sort_values("Ticker")

        # ── Construir tabla pivote con X marks ─────────────────
        # Para cada empresa, saber si tiene MACD y/o TD señal
        def _build_tabla_x(df_raw, tipos_señal):
            """
            tipos_señal: dict  {"MACD": ["MACD_BUY","MACD_SELL"], "TD Sequential": ["TD_BUY9","TD_SELL9"]}
            Retorna DataFrame: Ticker | Índice | Precio | Cambio% | MACD | TD Sequential | Fecha
            """
            df_f = df_raw[df_raw["Señal"].isin(
                [s for lst in tipos_señal.values() for s in lst]
            )]
            if df_f.empty:
                return pd.DataFrame()

            tickers_info = {}
            for _, row in df_f.iterrows():
                tk = row["Ticker"]
                if tk not in tickers_info:
                    tickers_info[tk] = {
                        "Ticker": tk, "Índice": row["Índice"],
                        "Precio": row["Precio"], "Cambio%": row["Cambio%"],
                        "Fecha": row["Fecha"],
                    }
                    for col in tipos_señal:
                        tickers_info[tk][col] = ""
                for col, señales in tipos_señal.items():
                    if row["Señal"] in señales:
                        tickers_info[tk][col] = "✕"
                        # Fecha más reciente
                        if row["Fecha"] > tickers_info[tk]["Fecha"]:
                            tickers_info[tk]["Fecha"] = row["Fecha"]

            df_out = pd.DataFrame(list(tickers_info.values()))
            return df_out

        _tb_compra = _build_tabla_x(_df_sc, {
            "MACD":          ["MACD_BUY"],
            "TD Sequential": ["TD_BUY9"],
        })
        _tb_venta = _build_tabla_x(_df_sc, {
            "MACD":          ["MACD_SELL"],
            "TD Sequential": ["TD_SELL9"],
        })

        # ── Helper HTML para renderizar la tabla con X marks ────
        def _html_tabla_x(df_t, color_header, color_x):
            if df_t.empty:
                return "<div style='font-size:.78rem;color:rgba(107,90,42,0.5);padding:14px 0;'>Sin señales en el período seleccionado.</div>"

            cols_ind = ["MACD", "TD Sequential"]
            html = f"""
            <div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">
            <table style="width:100%;border-collapse:collapse;font-size:.82rem;">
              <thead>
                <tr style="background:{color_header}15;border-bottom:2px solid {color_header}40;">
                  <th style="text-align:left;padding:10px 12px;color:{color_header};
                             font-size:.62rem;letter-spacing:2px;font-weight:700;
                             text-transform:uppercase;white-space:nowrap;">EMPRESA</th>
                  <th style="text-align:center;padding:10px 8px;color:{color_header};
                             font-size:.62rem;letter-spacing:2px;font-weight:700;
                             text-transform:uppercase;">MACD</th>
                  <th style="text-align:center;padding:10px 8px;color:{color_header};
                             font-size:.62rem;letter-spacing:2px;font-weight:700;
                             text-transform:uppercase;">TD SEQ.</th>
                  <th style="text-align:right;padding:10px 8px;color:rgba(107,90,42,0.6);
                             font-size:.62rem;letter-spacing:1px;font-weight:600;">PRECIO</th>
                  <th style="text-align:right;padding:10px 8px;color:rgba(107,90,42,0.6);
                             font-size:.62rem;letter-spacing:1px;font-weight:600;">DÍA%</th>
                  <th style="text-align:right;padding:10px 8px;color:rgba(107,90,42,0.6);
                             font-size:.62rem;letter-spacing:1px;font-weight:600;white-space:nowrap;">SEÑAL</th>
                </tr>
              </thead>
              <tbody>"""

            for i, (_, row) in enumerate(df_t.iterrows()):
                bg = "rgba(197,168,96,0.04)" if i % 2 == 0 else "#ffffff"
                c_pct = float(row.get("Cambio%", 0))
                c_col = "#0066cc" if c_pct >= 0 else "#cc3300"
                c_arrow = "▲" if c_pct >= 0 else "▼"
                macd_x  = row.get("MACD", "")
                td_x    = row.get("TD Sequential", "")
                macd_cell = (
                    f'<span style="color:{color_x};font-size:1.1rem;font-weight:900;">{macd_x}</span>'
                    if macd_x else '<span style="color:#ddd;">—</span>'
                )
                td_cell = (
                    f'<span style="color:{color_x};font-size:1.1rem;font-weight:900;">{td_x}</span>'
                    if td_x else '<span style="color:#ddd;">—</span>'
                )
                # Link → Análisis Técnico con ticker pre-seleccionado
                _tk  = row['Ticker']
                _idx = row.get('Índice', 'SP500')
                _link = f"?page=tecnico&ticker={_tk}&indice={_idx}"
                html += f"""
                <tr style="background:{bg};border-bottom:1px solid rgba(197,168,96,0.1);
                           transition:background .15s;" onmouseover="this.style.background='rgba(197,168,96,0.1)'"
                           onmouseout="this.style.background='{bg}'">
                  <td style="padding:9px 12px;">
                    <a href="{_link}" style="text-decoration:none;display:inline-flex;align-items:center;gap:6px;">
                      <span style="font-family:'Playfair Display',serif;font-weight:800;
                                   font-size:.95rem;color:#0a0a0a;">{_tk}</span>
                      <span style="font-size:.55rem;color:rgba(107,90,42,0.45);
                                   letter-spacing:1px;">{_idx}</span>
                      <span style="font-size:.65rem;color:#c5a860;opacity:0.7;">↗</span>
                    </a>
                  </td>
                  <td style="text-align:center;padding:9px 8px;">{macd_cell}</td>
                  <td style="text-align:center;padding:9px 8px;">{td_cell}</td>
                  <td style="text-align:right;padding:9px 8px;font-weight:600;
                             color:#0a0a0a;">${float(row.get('Precio',0)):,.2f}</td>
                  <td style="text-align:right;padding:9px 8px;font-weight:700;
                             color:{c_col};">{c_arrow}{abs(c_pct):.2f}%</td>
                  <td style="text-align:right;padding:9px 8px;font-size:.68rem;
                             color:rgba(107,90,42,0.55);">{row.get('Fecha','')}</td>
                </tr>"""

            html += "</tbody></table></div>"
            return html

        # ── Tabs: COMPRA / VENTA ────────────────────────────────
        _tab_buy, _tab_sell = st.tabs(["▲  SEÑAL DE COMPRA", "▼  SEÑAL DE VENTA"])

        with _tab_buy:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            _n_buy = len(_tb_compra)
            _n_both_buy = int((_tb_compra["MACD"] == "✕").sum() & 0) if not _tb_compra.empty else 0
            if not _tb_compra.empty:
                _b1, _b2, _b3 = st.columns(3)
                _b1.metric("Total empresas", _n_buy)
                _b2.metric("Solo MACD",  int((_tb_compra["MACD"]=="✕").sum() if not _tb_compra.empty else 0))
                _b3.metric("Solo TD Seq", int((_tb_compra["TD Sequential"]=="✕").sum() if not _tb_compra.empty else 0))
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            st.markdown(_html_tabla_x(_tb_compra, "#0066cc", "#0066cc"), unsafe_allow_html=True)

            # Export Excel compras
            if not _tb_compra.empty:
                try:
                    import io as _io
                    _buf_c = _io.BytesIO()
                    with pd.ExcelWriter(_buf_c, engine="xlsxwriter") as _xw_c:
                        _tb_compra.to_excel(_xw_c, sheet_name="Señales Compra", index=False)
                    st.download_button(
                        "⬇ Exportar Compras Excel", data=_buf_c.getvalue(),
                        file_name=f"señales_compra_{_sc_ventana_lbl[:3].lower()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                except Exception:
                    pass

        with _tab_sell:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if not _tb_venta.empty:
                _v1, _v2, _v3 = st.columns(3)
                _v1.metric("Total empresas", len(_tb_venta))
                _v2.metric("Solo MACD",  int((_tb_venta["MACD"]=="✕").sum()))
                _v3.metric("Solo TD Seq", int((_tb_venta["TD Sequential"]=="✕").sum()))
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            st.markdown(_html_tabla_x(_tb_venta, "#cc3300", "#cc3300"), unsafe_allow_html=True)

            # Export Excel ventas
            if not _tb_venta.empty:
                try:
                    import io as _io
                    _buf_v = _io.BytesIO()
                    with pd.ExcelWriter(_buf_v, engine="xlsxwriter") as _xw_v:
                        _tb_venta.to_excel(_xw_v, sheet_name="Señales Venta", index=False)
                    st.download_button(
                        "⬇ Exportar Ventas Excel", data=_buf_v.getvalue(),
                        file_name=f"señales_venta_{_sc_ventana_lbl[:3].lower()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                except Exception:
                    pass


# PÁGINA 4 — NOTICIAS
# ══════════════════════════════════════════════════════════════════

elif "Noticias" in pagina:
    st.markdown("""
    <div style="padding:0 0 14px;">
      <span style="font-family:'Playfair Display',serif;font-size:1.3rem;
                   color:#ffffff;letter-spacing:4px;text-transform:uppercase;">
        Noticias Financieras
      </span>
    </div>
    """, unsafe_allow_html=True)

    df_news = cargar_noticias()

    if df_news.empty:
        st.markdown("""
        <div style="background:#ffffff;border:1px solid rgba(197,168,96,0.2);border-radius:4px;
                    padding:24px;text-align:center;color:rgba(197,168,96,0.5);
                    font-size:0.8rem;letter-spacing:2px;">
          SIN NOTICIAS — Ejecuta src/05_noticias_financieras.py
        </div>""", unsafe_allow_html=True)
    else:
        # Ticker de titulares
        titulares = " &nbsp;·&nbsp; ".join(
            df_news.head(8)["Título"].tolist()
        ) if "Título" in df_news.columns else ""
        st.markdown(f"""
        <div class="ticker-bar">
          <span>◉ FEED</span>
          {titulares}
        </div>""", unsafe_allow_html=True)

        # Métricas
        c1, c2, c3, c_sp = st.columns([1, 1, 1, 4])
        c1.metric("Total", len(df_news))
        c2.metric("Fuentes", df_news["Fuente"].nunique() if "Fuente" in df_news.columns else "-")
        c3.metric(
            "Relevantes",
            len(df_news[df_news["Relevante"] == "SÍ"]) if "Relevante" in df_news.columns else "-",
        )

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Filtros
        cf1, cf2, cf3 = st.columns([1, 2, 3])
        with cf1:
            solo = st.checkbox("Solo relevantes", value=True, key="news_rel")
        with cf2:
            fuentes = (
                ["Todas"] + sorted(df_news["Fuente"].unique().tolist())
                if "Fuente" in df_news.columns else ["Todas"]
            )
            fsrc = st.selectbox("Fuente", fuentes, key="news_src")

        df_n = df_news.copy()
        if solo and "Relevante" in df_n.columns:
            df_n = df_n[df_n["Relevante"] == "SÍ"]
        if fsrc != "Todas" and "Fuente" in df_n.columns:
            df_n = df_n[df_n["Fuente"] == fsrc]

        st.markdown(
            f"<div style='font-size:.7rem;color:rgba(197,168,96,0.5);letter-spacing:2px;"
            f"margin-bottom:12px;'>{len(df_n)} REGISTROS</div>",
            unsafe_allow_html=True,
        )

        for _, row in df_n.head(40).iterrows():
            fuente_str = str(row.get("Fuente", "")).upper()
            fecha_str  = str(row.get("Fecha", ""))
            titulo_str = str(row.get("Título", ""))
            url_str    = str(row.get("URL", "#"))
            st.markdown(f"""
            <div class="noticia-row">
              <div style="margin-bottom:6px;">
                <span style="font-size:0.6rem;letter-spacing:2px;text-transform:uppercase;
                             color:{ORO};font-weight:700;">{fuente_str}</span>
              </div>
              <div class="noticia-titulo">
                <a href="{url_str}" target="_blank"
                   style="color:#0a0a0a;text-decoration:none;">
                  {titulo_str}
                </a>
              </div>
              <div class="noticia-meta">◉ {fuente_str} &nbsp;·&nbsp; {fecha_str}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PÁGINA 4 — FUNDAMENTALES
# ══════════════════════════════════════════════════════════════════

elif "Fundamental" in pagina:
    st.markdown("""
    <div style="padding:4px 0 16px;border-bottom:2px solid rgba(197,168,96,0.25);margin-bottom:18px;">
      <span style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:800;
                   color:#0a0a0a;letter-spacing:5px;text-transform:uppercase;">
        JST <span style="color:#c5a860;">ALPHA</span>
      </span>
      <span style="color:rgba(140,110,30,0.7);font-size:0.62rem;
                   letter-spacing:4px;text-transform:uppercase;margin-left:18px;font-weight:600;">
        Análisis Fundamental · EERR Trimestral &amp; Anual · Ratios
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Selector principal ──────────────────────────────────────
    modo_fund = st.radio("", ["◆ Mercado / Heatmap", "◉ Ratios por Empresa", "◎ EERR Detallado"],
                         horizontal=True, key="modo_fund", label_visibility="collapsed")

    if modo_fund == "◆ Mercado / Heatmap":
        tab_sp, tab_nq, tab_dw = st.tabs([
            "◆  S&P 500",
            "◆  Nasdaq 100",
            "◆  Dow Jones 30",
        ])

        for tab, hoja in [
            (tab_sp, "SP500 Empresas"),
            (tab_nq, "Nasdaq100 Empresas"),
            (tab_dw, "Dow30 Empresas"),
        ]:
            with tab:
                df_f = cargar_hoja(os.path.join(DATA_DIR, "TRADING_DATA.xlsx"), hoja)
                if df_f.empty:
                    st.markdown("""
                    <div style="background:#ffffff;border:1px solid rgba(197,168,96,0.15);
                                border-radius:4px;padding:20px;text-align:center;
                                color:rgba(197,168,96,0.4);font-size:0.75rem;letter-spacing:2px;">
                      SIN DATOS DISPONIBLES
                    </div>""", unsafe_allow_html=True)
                    continue

                cb2, co2 = st.columns([2, 1])
                with cb2:
                    bus = st.text_input("Buscar ticker", "", key=f"b{hoja}").upper()
                with co2:
                    ord2 = st.selectbox(
                        "Ordenar por",
                        ["Cambio Día %", "Cambio 1M %", "Cambio 1A %"],
                        key=f"o{hoja}",
                    )

                df_ff = df_f[df_f["Ticker"].str.contains(bus, na=False)] if bus else df_f
                df_ff = df_ff.sort_values(ord2, ascending=False)

                # KPIs
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Empresas", len(df_ff))
                c2.metric("Subieron", len(df_ff[df_ff["Cambio Día %"] > 0]))
                c3.metric("Bajaron",  len(df_ff[df_ff["Cambio Día %"] < 0]))
                mejor = (
                    df_ff.nlargest(1, "Cambio Día %")["Ticker"].values[0]
                    if len(df_ff) else "-"
                )
                c4.metric("Mejor del día", mejor)

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

                # Heatmap Treemap
                df_heat = df_ff.dropna(subset=["Cambio Día %"]).head(80).copy()
                if not df_heat.empty:
                    df_heat["label"] = df_heat.apply(
                        lambda r: f"{r['Ticker']}<br>{r['Cambio Día %']:+.2f}%", axis=1
                    )
                    df_heat["abs_cap"] = df_heat["Último Precio"].abs().clip(lower=0.01)

                    fig_h = go.Figure(go.Treemap(
                        labels=df_heat["label"],
                        parents=[""] * len(df_heat),
                        values=df_heat["abs_cap"],
                        customdata=df_heat[["Ticker", "Cambio Día %", "Último Precio", "Cambio 1M %"]].values,
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>"
                            "Precio: $%{customdata[2]:.2f}<br>"
                            "Día: <b>%{customdata[1]:+.2f}%</b><br>"
                            "1M: %{customdata[3]:+.2f}%<extra></extra>"
                        ),
                        marker=dict(
                            colors=df_heat["Cambio Día %"],
                            colorscale=[
                                [0.0,  "#8B0000"],
                                [0.25, "#cc3300"],
                                [0.42, "#ff6666"],
                                [0.50, "#2a2a2a"],
                                [0.58, "#336633"],
                                [0.75, "#009900"],
                                [1.0,  "#004d00"],
                            ],
                            cmid=0,
                            showscale=True,
                            colorbar=dict(
                                title="% Día",
                                tickformat="+.1f",
                                thickness=12,
                                len=0.8,
                                tickfont=dict(color="#555555", size=9),
                                title_font=dict(color="rgba(197,168,96,0.6)", size=9),
                            ),
                        ),
                        textfont=dict(size=11, color="white", family="Arial Black"),
                        pathbar=dict(visible=False),
                    ))
                    fig_h.update_layout(
                        paper_bgcolor="#ffffff",
                        font=dict(color="#555555"),
                        height=420,
                        margin=dict(l=5, r=5, t=10, b=5),
                    )
                    st.plotly_chart(fig_h, use_container_width=True)

                # Tabla con filas alternadas
                st.markdown('<div class="section-header">TABLA DE EMPRESAS</div>', unsafe_allow_html=True)

                def style_fund_table(df_in):
                    def row_styles(row):
                        idx = row.name
                        bg = "#ffffff" if idx % 2 == 0 else "#f5f4f0"
                        styles = [f"background:{bg};color:#111;"] * len(row)
                        # Color change columns
                        for ci, col_name in enumerate(row.index):
                            if "Cambio" in str(col_name):
                                try:
                                    v = float(row[col_name])
                                    styles[ci] = (
                                        f"background:{bg};color:#4da6ff;font-weight:600;"
                                        if v >= 0
                                        else f"background:{bg};color:#ff6644;font-weight:600;"
                                    )
                                except Exception:
                                    pass
                        return styles

                    return df_in.style.apply(row_styles, axis=1)

                st.dataframe(
                    style_fund_table(df_ff.reset_index(drop=True)),
                    width="stretch",
                    hide_index=True,
                )

    elif modo_fund == "◉ Ratios por Empresa":
        # ── Selector empresa ──────────────────────────────────────
        FIN_DIR_Q = os.path.join(DATA_DIR, "financials")
        FIN_DIR_A = os.path.join(DATA_DIR, "financials_annual")

        col_sel1, col_sel2 = st.columns([2, 1])
        with col_sel1:
            ticker_rat = st.text_input("Ticker (ej: AAPL, MSFT, NVDA)", "AAPL", key="rat_ticker").upper().strip()
        with col_sel2:
            freq_rat = st.selectbox("Frecuencia", ["Trimestral", "Anual"], key="rat_freq")

        fin_dir_rat = FIN_DIR_Q if freq_rat == "Trimestral" else FIN_DIR_A

        def leer_fin(ticker, tipo, fin_dir):
            ruta = os.path.join(fin_dir, f"{ticker}_{tipo}.csv")
            if not os.path.exists(ruta):
                return pd.DataFrame()
            try:
                df = pd.read_csv(ruta, index_col=0)
                for c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
                return df
            except Exception:
                return pd.DataFrame()

        is_df = leer_fin(ticker_rat, "income",   fin_dir_rat)
        bs_df = leer_fin(ticker_rat, "balance",  fin_dir_rat)
        cf_df = leer_fin(ticker_rat, "cashflow", fin_dir_rat)

        if is_df.empty and bs_df.empty:
            st.warning(f"No hay datos para {ticker_rat} en modo {freq_rat}. Ejecuta primero los scripts de descarga.")
        else:
            # ── Extraer métricas clave ────────────────────────────
            def safe(df, row, default=np.nan):
                """Extrae una fila como Series, busca por nombre parcial."""
                if df.empty:
                    return pd.Series(dtype=float)
                matches = [r for r in df.index if row.lower() in r.lower()]
                if not matches:
                    return pd.Series(dtype=float)
                return df.loc[matches[0]].apply(pd.to_numeric, errors="coerce")

            rev       = safe(is_df, "Total Revenue")
            net_inc   = safe(is_df, "Net Income")
            ebit      = safe(is_df, "EBIT")
            ebitda    = safe(is_df, "EBITDA")
            gross     = safe(is_df, "Gross Profit")

            cash      = safe(bs_df, "Cash And Cash Equivalents")
            curr_a    = safe(bs_df, "Current Assets")
            curr_l    = safe(bs_df, "Current Liabilities")
            inv       = safe(bs_df, "Inventory")
            tot_a     = safe(bs_df, "Total Assets")
            tot_eq    = safe(bs_df, "Stockholders Equity")
            lt_debt   = safe(bs_df, "Long Term Debt")
            tot_debt  = safe(bs_df, "Total Debt")
            rec       = safe(bs_df, "Accounts Receivable")

            fcf       = safe(cf_df, "Free Cash Flow")
            capex     = safe(cf_df, "Capital Expenditure")
            cfo       = safe(cf_df, "Operating Cash Flow")

            # ── Calcular ratios ───────────────────────────────────
            def ratio_series(num, den):
                if num.empty or den.empty:
                    return pd.Series(dtype=float)
                common = num.index.intersection(den.index)
                if common.empty:
                    return pd.Series(dtype=float)
                with np.errstate(divide="ignore", invalid="ignore"):
                    return (num[common] / den[common]).round(3)

            ratios = {}
            # Liquidez
            if not curr_a.empty and not curr_l.empty:
                ratios["Ratio Corriente (x)"]     = ratio_series(curr_a, curr_l)
            if not curr_a.empty and not curr_l.empty and not inv.empty:
                ratios["Prueba Ácida (x)"]         = ratio_series(curr_a - inv.reindex(curr_a.index).fillna(0), curr_l)
            if not cash.empty and not curr_l.empty:
                ratios["Ratio de Caja (x)"]        = ratio_series(cash, curr_l)
            # Endeudamiento
            if not tot_debt.empty and not tot_eq.empty:
                ratios["Deuda/Equity (x)"]         = ratio_series(tot_debt, tot_eq)
            if not lt_debt.empty and not tot_a.empty:
                ratios["Deuda LP/Activos (x)"]     = ratio_series(lt_debt, tot_a)
            # Rentabilidad
            if not net_inc.empty and not rev.empty:
                ratios["Margen Neto (%)"]          = (ratio_series(net_inc, rev) * 100).round(2)
            if not gross.empty and not rev.empty:
                ratios["Margen Bruto (%)"]         = (ratio_series(gross, rev) * 100).round(2)
            if not ebitda.empty and not rev.empty:
                ratios["Margen EBITDA (%)"]        = (ratio_series(ebitda, rev) * 100).round(2)
            if not net_inc.empty and not tot_eq.empty:
                ratios["ROE (%)"]                  = (ratio_series(net_inc, tot_eq) * 100).round(2)
            if not net_inc.empty and not tot_a.empty:
                ratios["ROA (%)"]                  = (ratio_series(net_inc, tot_a) * 100).round(2)
            if not ebit.empty and not tot_a.empty:
                ratios["ROCE (%)"]                 = (ratio_series(ebit, tot_a) * 100).round(2)
            # Crecimiento revenue
            if not rev.empty and len(rev) >= 2:
                rev_sorted = rev.sort_index()
                ratios["Crec. Revenue (%)"]        = (rev_sorted.pct_change() * 100).round(2)

            # ── Mostrar en tarjetas por categoría ─────────────────
            categorias_rat = {
                "LIQUIDEZ":       ["Ratio Corriente (x)", "Prueba Ácida (x)", "Ratio de Caja (x)"],
                "ENDEUDAMIENTO":  ["Deuda/Equity (x)", "Deuda LP/Activos (x)"],
                "RENTABILIDAD":   ["Margen Neto (%)", "Margen Bruto (%)", "Margen EBITDA (%)", "ROE (%)", "ROA (%)", "ROCE (%)"],
                "CRECIMIENTO":    ["Crec. Revenue (%)"],
            }

            # Mostrar ticker info
            try:
                import yfinance as yf
                t_info = yf.Ticker(ticker_rat).fast_info
                precio = t_info.get("last_price", None)
                mktcap = t_info.get("market_cap", None)
                st.markdown(f"""
                <div style="display:flex;gap:14px;margin-bottom:16px;flex-wrap:wrap;">
                  <div class="card" style="padding:10px 14px;min-width:120px;">
                    <div class="card-label">Precio</div>
                    <div class="card-value" style="font-size:1.1rem;">${precio:,.2f}</div>
                  </div>
                  <div class="card" style="padding:10px 14px;min-width:120px;">
                    <div class="card-label">Mkt Cap</div>
                    <div class="card-value" style="font-size:1.1rem;">${mktcap/1e9:,.1f}B</div>
                  </div>
                </div>
                """, unsafe_allow_html=True) if precio and mktcap else None

                # Indicadores de valoración vía yfinance
                info_full = yf.Ticker(ticker_rat).info
                val_items = {
                    "P/E Ratio":      info_full.get("trailingPE"),
                    "P/S Ratio":      info_full.get("priceToSalesTrailing12Months"),
                    "P/BV Ratio":     info_full.get("priceToBook"),
                    "EV/EBITDA":      info_full.get("enterpriseToEbitda"),
                    "EPS (TTM)":      info_full.get("trailingEps"),
                    "Div. Yield (%)": round(info_full.get("dividendYield", 0) * 100, 2) if info_full.get("dividendYield") else None,
                    "PEG Ratio":      info_full.get("pegRatio"),
                    "Beta":           info_full.get("beta"),
                }
                val_items = {k: v for k, v in val_items.items() if v is not None}
                if val_items:
                    st.markdown('<div class="section-header">VALORACIÓN (Tiempo Real)</div>', unsafe_allow_html=True)
                    vcols = st.columns(4)
                    for i, (k, v) in enumerate(val_items.items()):
                        with vcols[i % 4]:
                            st.markdown(f"""
                            <div class="card" style="padding:10px 14px;margin-bottom:8px;">
                              <div class="card-label">{k}</div>
                              <div class="card-value" style="font-size:1rem;color:#0a0a0a;">{v:,.2f}</div>
                            </div>""", unsafe_allow_html=True)
            except Exception:
                pass

            for cat_name, rat_keys in categorias_rat.items():
                disponibles = {k: ratios[k] for k in rat_keys if k in ratios and not ratios[k].empty}
                if not disponibles:
                    continue
                st.markdown(f'<div class="section-header">{cat_name}</div>', unsafe_allow_html=True)
                rcols = st.columns(min(len(disponibles), 4))
                for i, (rat_name, rat_series) in enumerate(disponibles.items()):
                    with rcols[i % 4]:
                        ult_val = rat_series.dropna().iloc[-1] if len(rat_series.dropna()) else None
                        if ult_val is None:
                            continue
                        # Color basado en tipo de ratio
                        is_pct = "%" in rat_name
                        color = "#0a0a0a"
                        if "ROE" in rat_name or "ROA" in rat_name or "ROCE" in rat_name or "Margen" in rat_name:
                            color = "#0066cc" if ult_val > 0 else "#cc3300"
                        elif "Corriente" in rat_name or "Ácida" in rat_name:
                            color = "#0066cc" if ult_val >= 1 else "#cc3300"
                        elif "Deuda" in rat_name:
                            color = "#cc3300" if ult_val > 2 else "#0066cc"
                        elif "Crec" in rat_name:
                            color = "#0066cc" if ult_val > 0 else "#cc3300"
                        st.markdown(f"""
                        <div class="card" style="padding:10px 14px;margin-bottom:8px;">
                          <div class="card-label" style="font-size:0.55rem;">{rat_name}</div>
                          <div class="card-value" style="font-size:1rem;color:{color};">{ult_val:,.2f}</div>
                        </div>""", unsafe_allow_html=True)

                # Tabla histórica del ratio
                df_rat_hist = pd.DataFrame(disponibles).T
                df_rat_hist.columns = [str(c)[:10] for c in df_rat_hist.columns]
                st.dataframe(df_rat_hist, use_container_width=True)

    elif modo_fund == "◎ EERR Detallado":
        # ── EERR trimestral o anual por empresa ───────────────────
        FIN_DIR_Q2 = os.path.join(DATA_DIR, "financials")
        FIN_DIR_A2 = os.path.join(DATA_DIR, "financials_annual")

        ce1, ce2, ce3 = st.columns([2, 1, 1])
        with ce1:
            ticker_ee = st.text_input("Ticker", "AAPL", key="ee_ticker").upper().strip()
        with ce2:
            freq_ee = st.selectbox("Período", ["Trimestral", "Anual"], key="ee_freq")
        with ce3:
            estado_ee = st.selectbox("Estado", ["Income Statement", "Balance Sheet", "Cash Flow"], key="ee_estado")

        fin_dir_ee = FIN_DIR_Q2 if freq_ee == "Trimestral" else FIN_DIR_A2
        tipo_map = {"Income Statement": "income", "Balance Sheet": "balance", "Cash Flow": "cashflow"}
        tipo_ee  = tipo_map[estado_ee]

        ruta_ee = os.path.join(fin_dir_ee, f"{ticker_ee}_{tipo_ee}.csv")
        if not os.path.exists(ruta_ee):
            st.warning(f"No hay datos para {ticker_ee} ({freq_ee} / {estado_ee}). Ejecuta primero los scripts de descarga.")
        else:
            try:
                df_ee = pd.read_csv(ruta_ee, index_col=0)
                for c in df_ee.columns:
                    df_ee[c] = pd.to_numeric(df_ee[c], errors="coerce")
                df_ee.columns = [str(c)[:10] for c in df_ee.columns]

                st.markdown(f'<div class="section-header">{ticker_ee} · {estado_ee} · {freq_ee}</div>', unsafe_allow_html=True)

                def color_eerr(val):
                    try:
                        v = float(val)
                        if v < 0:
                            return "color:#cc3300;font-weight:600"
                        if v > 0:
                            return "color:#0a0a0a"
                    except Exception:
                        pass
                    return "color:#6b5a2a"

                st.dataframe(
                    df_ee.style.map(color_eerr),
                    use_container_width=True,
                    height=600,
                )

                # Mini gráfico de la métrica seleccionada
                metricas_disp = df_ee.index.tolist()
                met_sel = st.selectbox("Graficar métrica", metricas_disp, key="ee_metrica")
                if met_sel:
                    serie = df_ee.loc[met_sel].dropna().sort_index()
                    if len(serie) >= 2:
                        colores_bar = ["rgba(0,102,204,0.7)" if v >= 0 else "rgba(204,51,0,0.7)" for v in serie]
                        fig_eerr = go.Figure(go.Bar(
                            x=serie.index, y=serie.values,
                            marker_color=colores_bar, marker_line_width=0,
                            text=[f"{v/1e9:.2f}B" if abs(v) >= 1e9 else f"{v/1e6:.0f}M" for v in serie.values],
                            textposition="outside",
                        ))
                        fig_eerr.update_layout(
                            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                            height=280, margin=dict(l=10,r=10,t=30,b=10),
                            title=dict(text=f"{met_sel} — {ticker_ee} ({freq_ee})",
                                       font=dict(color="#0a0a0a", size=12)),
                            xaxis=dict(gridcolor=GRID, color="#555"),
                            yaxis=dict(gridcolor=GRID, color="#555"),
                            font=dict(color="#555"),
                        )
                        st.plotly_chart(fig_eerr, use_container_width=True)
            except Exception as e:
                st.error(f"Error cargando datos: {e}")


# ══════════════════════════════════════════════════════════════════
# PÁGINA 5 — SOCIAL & PODCASTS
# ══════════════════════════════════════════════════════════════════

elif "Social" in pagina:
    st.markdown("""
    <div style="padding:0 0 14px;">
      <span style="font-family:'Playfair Display',serif;font-size:1.3rem;
                   color:#ffffff;letter-spacing:4px;text-transform:uppercase;">
        Social &amp; Podcasts
      </span>
    </div>
    """, unsafe_allow_html=True)

    ca, ci = st.columns([1, 3])
    with ca:
        if st.button("↺  Actualizar feeds", key="soc_update", use_container_width=True):
            import subprocess, sys
            with st.spinner("Descargando feeds..."):
                subprocess.run(
                    [sys.executable, os.path.join(BASE_DIR, "src", "09_social_media.py")],
                    capture_output=True,
                )
            st.cache_data.clear()
            st.rerun()
    with ci:
        ruta_s = os.path.join(DATA_DIR, "social", "social_hoy.csv")
        if os.path.exists(ruta_s):
            mtime = datetime.fromtimestamp(os.path.getmtime(ruta_s))
            st.markdown(
                f"<div style='font-size:.72rem;color:rgba(197,168,96,0.6);letter-spacing:1px;"
                f"padding-top:10px;'>Última actualización: "
                f"<b style='color:{ORO};'>{mtime.strftime('%d/%m/%Y %H:%M')}</b></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='font-size:.72rem;color:#cc3300;letter-spacing:1px;padding-top:10px;'>"
                "Sin datos — pulsa Actualizar feeds</div>",
                unsafe_allow_html=True,
            )

    df_soc = cargar_social()
    if df_soc.empty:
        st.markdown("""
        <div style="background:#ffffff;border:1px solid rgba(197,168,96,0.15);
                    border-radius:4px;padding:24px;text-align:center;
                    color:rgba(197,168,96,0.45);font-size:0.8rem;letter-spacing:2px;">
          PULSA EL BOTÓN PARA CARGAR LOS FEEDS
        </div>""", unsafe_allow_html=True)
    else:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total",    len(df_soc))
        c2.metric("Podcasts", len(df_soc[df_soc["Tipo"] == "PODCAST"]))
        c3.metric("𝕏 Twitter",len(df_soc[df_soc["Tipo"] == "TWITTER"]))
        c4.metric("◈ Reddit", len(df_soc[df_soc["Tipo"] == "REDDIT"]))
        c5.metric("▶ YouTube",len(df_soc[df_soc["Tipo"] == "YOUTUBE"]))

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        tab_all, tab_tw, tab_pod, tab_red, tab_yt = st.tabs([
            "◇  Todo",
            "𝕏  Twitter",
            "◎  Podcasts",
            "◈  Reddit",
            "▶  YouTube",
        ])

        ICONOS = {
            "TWITTER": "𝕏",
            "PODCAST": "◎",
            "REDDIT":  "◈",
            "YOUTUBE": "▶",
        }
        CCOLOR = {
            "TWITTER": "rgba(197,168,96,0.85)",
            "PODCAST": "#c5a860",
            "REDDIT":  "rgba(197,168,96,0.7)",
            "YOUTUBE": "rgba(197,168,96,0.55)",
        }

        def render(df_i, max_i=50):
            if df_i.empty:
                st.markdown("""
                <div style="background:#ffffff;border:1px solid rgba(197,168,96,0.12);
                            border-radius:4px;padding:16px;text-align:center;
                            color:rgba(197,168,96,0.4);font-size:0.75rem;letter-spacing:2px;">
                  SIN DATOS
                </div>""", unsafe_allow_html=True)
                return
            for _, row in df_i.head(max_i).iterrows():
                tipo  = row.get("Tipo", "")
                ic    = ICONOS.get(tipo, "◇")
                col   = CCOLOR.get(tipo, ORO)
                res   = str(row.get("Resumen", "") or "")
                fuente_str = str(row.get("Fuente", "") or "")
                url_str    = str(row.get("URL", "#") or "#")
                titulo_str = str(row.get("Título", "") or "")
                fecha_str  = str(row.get("Fecha", "") or "")
                cat_str    = str(row.get("Categoría", "") or "")
                resumen_html = (
                    f"<div style='color:#555555;font-size:.74rem;"
                    f"margin-top:5px;line-height:1.4;'>{res[:180]}...</div>"
                    if res else ""
                )
                st.markdown(f"""
                <div class="noticia-row" style="border-left-color:{col};">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <span style="color:{col};font-size:.65rem;font-weight:700;
                                 letter-spacing:2px;text-transform:uppercase;">
                      {ic} {tipo} · {cat_str}
                    </span>
                    <span style="color:rgba(197,168,96,0.3);font-size:.65rem;">{fecha_str}</span>
                  </div>
                  <div style="color:rgba(197,168,96,0.5);font-size:.7rem;
                              margin-bottom:4px;letter-spacing:1px;">{fuente_str}</div>
                  <div class="noticia-titulo">
                    <a href="{url_str}" target="_blank"
                       style="color:#0a0a0a;text-decoration:none;">
                      {titulo_str}
                    </a>
                  </div>
                  {resumen_html}
                </div>""", unsafe_allow_html=True)

        with tab_all:
            bs = st.text_input("Buscar en feeds", "", key="bs_all")
            df_s = (
                df_soc[df_soc["Título"].str.contains(bs, case=False, na=False)]
                if bs else df_soc
            )
            render(df_s, 60)

        with tab_tw:
            df_tw = cargar_social("TWITTER")
            if not df_tw.empty:
                cats = ["Todas"] + sorted(df_tw["Categoría"].unique().tolist())
                csel = st.selectbox("Categoría", cats, key="tw_c")
                render(df_tw if csel == "Todas" else df_tw[df_tw["Categoría"] == csel], 60)
            else:
                render(pd.DataFrame())

        with tab_pod:
            df_p = cargar_social("PODCAST")
            if not df_p.empty:
                cols2 = st.columns(2)
                for i, (_, row) in enumerate(df_p.iterrows()):
                    with cols2[i % 2]:
                        fuente_str = str(row.get("Fuente", "") or "")
                        url_str    = str(row.get("URL", "#") or "#")
                        titulo_str = str(row.get("Título", "") or "")
                        resumen_str= str(row.get("Resumen", "") or "")[:100]
                        fecha_str  = str(row.get("Fecha", "") or "")
                        st.markdown(f"""
                        <div class="noticia-row" style="border-left-color:{ORO};">
                          <div style="color:{ORO};font-size:.65rem;font-weight:700;
                                      letter-spacing:2px;text-transform:uppercase;
                                      margin-bottom:6px;">◎ {fuente_str}</div>
                          <div class="noticia-titulo">
                            <a href="{url_str}" target="_blank"
                               style="color:#0a0a0a;text-decoration:none;">
                              {titulo_str}
                            </a>
                          </div>
                          <div style="color:#888888;font-size:.72rem;
                                      margin-top:6px;line-height:1.4;">{resumen_str}...</div>
                          <div style="color:rgba(197,168,96,0.3);font-size:.65rem;
                                      margin-top:5px;letter-spacing:1px;">{fecha_str}</div>
                        </div>""", unsafe_allow_html=True)
            else:
                render(pd.DataFrame())

        with tab_red:
            df_r = cargar_social("REDDIT")
            if not df_r.empty:
                subs = ["Todos"] + sorted(df_r["Fuente"].unique().tolist())
                ssel = st.selectbox("Subreddit", subs, key="red_s")
                render(df_r if ssel == "Todos" else df_r[df_r["Fuente"] == ssel], 50)
            else:
                render(pd.DataFrame())

        with tab_yt:
            df_y = cargar_social("YOUTUBE")
            if not df_y.empty:
                cols3 = st.columns(3)
                for i, (_, row) in enumerate(df_y.iterrows()):
                    with cols3[i % 3]:
                        fuente_str = str(row.get("Fuente", "") or "")
                        url_str    = str(row.get("URL", "#") or "#")
                        titulo_str = str(row.get("Título", "") or "")
                        fecha_str  = str(row.get("Fecha", "") or "")
                        st.markdown(f"""
                        <div class="noticia-row"
                             style="border-left-color:rgba(197,168,96,0.5);">
                          <div style="color:rgba(197,168,96,0.55);font-size:.65rem;
                                      font-weight:700;letter-spacing:2px;
                                      text-transform:uppercase;margin-bottom:5px;">
                            ▶ {fuente_str}
                          </div>
                          <div class="noticia-titulo">
                            <a href="{url_str}" target="_blank"
                               style="color:#0a0a0a;text-decoration:none;">
                              {titulo_str}
                            </a>
                          </div>
                          <div style="color:rgba(197,168,96,0.3);font-size:.65rem;
                                      margin-top:5px;letter-spacing:1px;">{fecha_str}</div>
                        </div>""", unsafe_allow_html=True)
            else:
                render(pd.DataFrame())
