"""
JST ALPHA — Reporte Diario de Cierre
Genera un PDF con resumen de mercado, señales técnicas y proyección estratégica.
Ejecutar: python3 src/10_reporte_diario.py
"""

import os, sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUT_DIR  = os.path.join(DATA_DIR, "reportes")
os.makedirs(OUT_DIR, exist_ok=True)

# ── PALETA DE COLORES JST ─────────────────────────────────────────
NEGRO  = colors.HexColor("#0a0a0a")
ORO    = colors.HexColor("#c5a860")
ORO_OSC= colors.HexColor("#a07820")
BLANCO = colors.white
GRIS   = colors.HexColor("#f5f4f0")
GRIS_MED=colors.HexColor("#888888")
ALZA   = colors.HexColor("#0066cc")
BAJA   = colors.HexColor("#cc3300")
MARMO  = colors.HexColor("#fdf9f2")

W, H = A4

# ── ESTILOS ───────────────────────────────────────────────────────
def estilos():
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=9,
                          textColor=NEGRO, leading=14)
    return {
        "titulo":    ParagraphStyle("titulo", fontName="Helvetica-Bold",
                                    fontSize=22, textColor=BLANCO, leading=28,
                                    spaceAfter=2),
        "subtitulo": ParagraphStyle("sub", fontName="Helvetica",
                                    fontSize=9, textColor=ORO, leading=12,
                                    letterSpacing=2),
        "seccion":   ParagraphStyle("sec", fontName="Helvetica-Bold",
                                    fontSize=10, textColor=ORO_OSC, leading=14,
                                    spaceBefore=14, spaceAfter=4,
                                    letterSpacing=1.5),
        "body":      base,
        "body_bold": ParagraphStyle("bb", fontName="Helvetica-Bold",
                                    fontSize=9, textColor=NEGRO, leading=14),
        "small":     ParagraphStyle("sm", fontName="Helvetica",
                                    fontSize=7.5, textColor=GRIS_MED, leading=11),
        "alza":      ParagraphStyle("alza", fontName="Helvetica-Bold",
                                    fontSize=9, textColor=ALZA, leading=14),
        "baja":      ParagraphStyle("baja", fontName="Helvetica-Bold",
                                    fontSize=9, textColor=BAJA, leading=14),
        "proyeccion":ParagraphStyle("proy", fontName="Helvetica",
                                    fontSize=9, textColor=NEGRO, leading=15,
                                    backColor=MARMO, borderPadding=8,
                                    borderColor=ORO, borderWidth=0.5),
        "centrado":  ParagraphStyle("cen", fontName="Helvetica",
                                    fontSize=8, textColor=GRIS_MED, leading=11,
                                    alignment=TA_CENTER),
    }

# ── HELPERS ───────────────────────────────────────────────────────
def cargar_macro():
    ruta = os.path.join(DATA_DIR, "TRADING_DATA.xlsx")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        return pd.read_excel(ruta, sheet_name="Resumen Macro")
    except:
        return pd.DataFrame()

def cargar_empresas(indice="SP500"):
    ruta = os.path.join(DATA_DIR, "TRADING_DATA.xlsx")
    hojas = {"SP500": "SP500 Empresas", "NASDAQ": "Nasdaq100 Empresas", "DOW": "Dow30 Empresas"}
    try:
        return pd.read_excel(ruta, sheet_name=hojas.get(indice, "SP500 Empresas"))
    except:
        return pd.DataFrame()

def cargar_indice(nombre_archivo):
    """Carga CSV de índice con formato yfinance (skiprows [1,2])."""
    ruta = os.path.join(DATA_DIR, "indices", f"{nombre_archivo}.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ruta, skiprows=[1, 2], index_col=0, parse_dates=True)
        df = df[pd.to_datetime(df.index, errors="coerce").notna()]
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    except:
        return pd.DataFrame()

def rsi_calc(s, p=14):
    d = s.diff()
    g = d.clip(lower=0); l = (-d).clip(lower=0)
    rs = g.ewm(com=p-1, min_periods=p).mean() / l.ewm(com=p-1, min_periods=p).mean()
    return (100 - 100 / (1 + rs)).iloc[-1]

def ema_calc(s, p):
    return s.ewm(span=p, adjust=False).mean().iloc[-1]

def max_drawdown(s):
    roll_max = s.cummax()
    dd = (s - roll_max) / roll_max * 100
    return float(dd.min())

def retorno_historico_dia_semana(close, dia_semana):
    """Estadística: % de veces que sube el día siguiente según día de la semana."""
    df = close.copy().to_frame("close")
    df["ret"] = df["close"].pct_change()
    df["dow"] = df.index.dayofweek
    dias_sig = df[df["dow"] == dia_semana]["ret"].dropna()
    if len(dias_sig) < 10:
        return None, None
    prob_sube = (dias_sig > 0).mean() * 100
    ret_med   = dias_sig.mean() * 100
    return round(prob_sube, 1), round(ret_med, 2)

def tabla_style_base(col_widths, header_bg=NEGRO):
    return TableStyle([
        ("BACKGROUND", (0,0), (-1,0), header_bg),
        ("TEXTCOLOR",  (0,0), (-1,0), BLANCO),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0), 8),
        ("FONTSIZE",   (0,1), (-1,-1), 8),
        ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
        ("TEXTCOLOR",  (0,1), (-1,-1), NEGRO),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLANCO, MARMO]),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#d4b870")),
        ("ALIGN",      (1,0), (-1,-1), "RIGHT"),
        ("ALIGN",      (0,0), (0,-1), "LEFT"),
        ("LEFTPADDING",  (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LINEBELOW", (0,0), (-1,0), 1.5, ORO),
    ])


# ── GENERADOR PRINCIPAL ───────────────────────────────────────────
def generar_reporte():
    E = estilos()
    hoy = datetime.now()
    fecha_str = hoy.strftime("%d de %B de %Y").upper()
    hora_str  = hoy.strftime("%H:%M")
    nombre_pdf = f"JST_ALPHA_Reporte_{hoy.strftime('%Y%m%d')}.pdf"
    ruta_pdf   = os.path.join(OUT_DIR, nombre_pdf)

    doc = SimpleDocTemplate(
        ruta_pdf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    story = []

    # ── HEADER ───────────────────────────────────────────────────
    # Banda negra con nombre
    header_data = [[
        Paragraph("JST <font color='#c5a860'>ALPHA</font>", E["titulo"]),
        Paragraph(f"REPORTE DIARIO DE CIERRE<br/>{fecha_str}  ·  {hora_str} HRS",
                  E["subtitulo"])
    ]]
    header_t = Table(header_data, colWidths=[9*cm, 8.5*cm])
    header_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NEGRO),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (0,-1), 16),
        ("RIGHTPADDING",(1,0), (1,-1), 16),
        ("ALIGN",      (1,0), (1,-1), "RIGHT"),
        ("TOPPADDING",  (0,0), (-1,-1), 14),
        ("BOTTOMPADDING",(0,0),(-1,-1), 14),
        ("LINEBELOW",  (0,0), (-1,-1), 2, ORO),
    ]))
    story.append(header_t)
    story.append(Spacer(1, 14))

    # ── DATOS ────────────────────────────────────────────────────
    df_macro = cargar_macro()
    df_sp500 = cargar_empresas("SP500")
    df_idx_sp = cargar_indice("SP500")
    df_idx_nq = cargar_indice("NASDAQ_COMP")
    df_idx_dj = cargar_indice("DOW_JONES")

    def macro_val(activo_key, campo="Último Valor"):
        if df_macro.empty: return None
        m = df_macro[df_macro["Activo"].astype(str).str.upper().str.replace(" ","_") == activo_key.upper()]
        if m.empty:
            m = df_macro[df_macro["Activo"].astype(str).str.contains(activo_key.replace("_"," "), case=False, na=False)]
        return float(m.iloc[0][campo]) if not m.empty else None

    # ── SECCIÓN 1: RESUMEN DE CIERRE ─────────────────────────────
    story.append(Paragraph("1.  RESUMEN DE CIERRE DE MERCADO", E["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ORO, spaceAfter=8))

    indices = [
        ("S&P 500",    "SP500",       df_idx_sp),
        ("NASDAQ",     "NASDAQ_COMP", df_idx_nq),
        ("DOW JONES",  "DOW_JONES",   df_idx_dj),
    ]

    idx_rows = [["ÍNDICE", "CIERRE", "DÍA %", "1M %", "1A %", "RSI 14", "EMA 200"]]
    for nombre, key, df_i in indices:
        val  = macro_val(key, "Último Valor")
        dia  = macro_val(key, "Cambio Día %")
        m1   = macro_val(key, "Cambio 1M %")
        a1   = macro_val(key, "Cambio 1A %")
        rsi_v = ema_v = "—"
        if df_i is not None and not df_i.empty and "Close" in df_i.columns:
            close = df_i["Close"].dropna()
            if len(close) >= 20:
                rsi_v = f"{rsi_calc(close):.1f}"
            if len(close) >= 200:
                ema_v = f"{ema_calc(close, 200):,.0f}"

        def fmt_pct(v):
            if v is None: return "—"
            return f"+{v:.2f}%" if v >= 0 else f"{v:.2f}%"

        idx_rows.append([
            nombre,
            f"{val:,.0f}" if val else "—",
            fmt_pct(dia), fmt_pct(m1), fmt_pct(a1),
            rsi_v, ema_v
        ])

    t_idx = Table(idx_rows, colWidths=[3.2*cm, 2.4*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.8*cm, 2.3*cm])
    ts = tabla_style_base(None)
    # Colorear columna Día %
    for r in range(1, len(idx_rows)):
        v = idx_rows[r][2]
        c = ALZA if v.startswith("+") else (BAJA if v.startswith("-") else NEGRO)
        ts.add("TEXTCOLOR", (2,r), (2,r), c)
        ts.add("FONTNAME",  (2,r), (2,r), "Helvetica-Bold")
    t_idx.setStyle(ts)
    story.append(t_idx)
    story.append(Spacer(1, 10))

    # Análisis narrativo del día
    sp_dia = macro_val("SP500", "Cambio Día %")
    nq_dia = macro_val("NASDAQ_COMP", "Cambio Día %")
    dj_dia = macro_val("DOW_JONES",  "Cambio Día %")

    def tendencia(v):
        if v is None: return "mixto"
        if v > 1.5:   return "fuerte alza"
        if v > 0.3:   return "alza moderada"
        if v > -0.3:  return "sesión neutral"
        if v > -1.5:  return "baja moderada"
        return "fuerte caída"

    narrativa = (
        f"El mercado cerró con <b>{tendencia(sp_dia)}</b> en el S&P 500 "
        f"({'+' if sp_dia and sp_dia>=0 else ''}{sp_dia:.2f}% {'✓' if sp_dia and sp_dia>0 else '✗' if sp_dia and sp_dia<0 else ''}), "
        f"acompañado por el Nasdaq ({'+' if nq_dia and nq_dia>=0 else ''}{nq_dia:.2f}%) "
        f"y el Dow Jones ({'+' if dj_dia and dj_dia>=0 else ''}{dj_dia:.2f}%). "
    ) if all(v is not None for v in [sp_dia, nq_dia, dj_dia]) else "Datos de mercado no disponibles."

    if sp_dia is not None:
        if sp_dia > 0 and nq_dia and nq_dia > 0:
            narrativa += "Amplitud positiva: los tres índices principales subieron en sincronía, señal constructiva."
        elif sp_dia < 0 and nq_dia and nq_dia < 0:
            narrativa += "Presión de venta generalizada. Sesión de risk-off en todos los índices principales."
        else:
            narrativa += "Divergencia entre índices: movimiento selectivo por sectores."

    story.append(Paragraph(narrativa, E["body"]))
    story.append(Spacer(1, 12))

    # ── SECCIÓN 2: COMMODITIES & MACRO ───────────────────────────
    story.append(Paragraph("2.  COMMODITIES Y MACRO GLOBAL", E["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ORO, spaceAfter=8))

    comm_keys = [
        ("Oro",          "Oro",          "GC=F",  "COMMODITIES"),
        ("Petróleo WTI", "Petroleo_WTI", "CL=F",  "COMMODITIES"),
        ("Bitcoin",      "Bitcoin",      "BTC-USD","COMMODITIES"),
        ("EUR/USD",      "EUR_USD",      "EURUSD=X","MONEDAS"),
        ("DXY Dollar",   "DXY_Dollar_Index","DX-Y.NYB","MONEDAS"),
        ("UST 10Y",      "UST_10Y",      "^TNX",  "TASAS UST"),
        ("UST 2Y",       "UST_3M",       "^IRX",  "TASAS UST"),
    ]

    comm_rows = [["ACTIVO", "VALOR", "DÍA %", "1M %", "LECTURA"]]
    for display, key, ticker, cat in comm_keys:
        if df_macro.empty:
            continue
        m = df_macro[df_macro["Categoría"] == cat]
        m2 = m[m["Activo"].astype(str).str.upper().str.replace(" ","_").str.contains(key.upper(), na=False)]
        if m2.empty:
            m2 = m[m["Ticker"].astype(str) == ticker]
        if m2.empty:
            continue
        row = m2.iloc[0]
        val = float(row.get("Último Valor", 0) or 0)
        dia = float(row.get("Cambio Día %", 0) or 0)
        m1v = float(row.get("Cambio 1M %", 0) or 0)

        if "UST" in display:
            fmt_val = f"{val:.2f}%"
        elif val > 1000:
            fmt_val = f"{val:,.0f}"
        else:
            fmt_val = f"{val:,.4f}" if val < 10 else f"{val:,.2f}"

        lectura = "—"
        if dia > 1.5:   lectura = "↑ Fuerte alza"
        elif dia > 0.3: lectura = "↑ Sube"
        elif dia > -0.3:lectura = "→ Lateral"
        elif dia > -1.5:lectura = "↓ Baja"
        else:           lectura = "↓ Fuerte caída"

        comm_rows.append([
            display, fmt_val,
            f"+{dia:.2f}%" if dia>=0 else f"{dia:.2f}%",
            f"+{m1v:.2f}%" if m1v>=0 else f"{m1v:.2f}%",
            lectura
        ])

    if len(comm_rows) > 1:
        t_comm = Table(comm_rows, colWidths=[3.5*cm, 2.5*cm, 2*cm, 2*cm, 5.1*cm])
        ts2 = tabla_style_base(None)
        for r in range(1, len(comm_rows)):
            v = comm_rows[r][2]
            c = ALZA if v.startswith("+") else (BAJA if v.startswith("-") else NEGRO)
            ts2.add("TEXTCOLOR", (2,r), (2,r), c)
            ts2.add("FONTNAME",  (2,r), (2,r), "Helvetica-Bold")
        t_comm.setStyle(ts2)
        story.append(t_comm)
    story.append(Spacer(1, 12))

    # ── SECCIÓN 3: TOP MOVERS SP500 ───────────────────────────────
    story.append(Paragraph("3.  MEJORES Y PEORES DEL DÍA — S&P 500", E["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ORO, spaceAfter=8))

    if not df_sp500.empty and "Cambio Día %" in df_sp500.columns:
        df_sp500["Cambio Día %"] = pd.to_numeric(df_sp500["Cambio Día %"], errors="coerce")
        top5  = df_sp500.dropna(subset=["Cambio Día %"]).nlargest(5, "Cambio Día %")
        bot5  = df_sp500.dropna(subset=["Cambio Día %"]).nsmallest(5, "Cambio Día %")

        movers_rows = [["MAYORES ALZAS", "DÍA %", "PRECIO", "", "MAYORES BAJAS", "DÍA %", "PRECIO"]]
        for i in range(5):
            tr = top5.iloc[i] if i < len(top5) else None
            br = bot5.iloc[i] if i < len(bot5) else None
            movers_rows.append([
                str(tr["Ticker"]) if tr is not None else "",
                f"+{tr['Cambio Día %']:.2f}%" if tr is not None else "",
                f"${tr.get('Último Precio',0):.2f}" if tr is not None else "",
                "",
                str(br["Ticker"]) if br is not None else "",
                f"{br['Cambio Día %']:.2f}%" if br is not None else "",
                f"${br.get('Último Precio',0):.2f}" if br is not None else "",
            ])

        t_mv = Table(movers_rows, colWidths=[2.5*cm,1.8*cm,1.8*cm,0.5*cm,2.5*cm,1.8*cm,1.8*cm])
        ts3 = TableStyle([
            ("BACKGROUND",    (0,0), (2,0), ALZA),
            ("BACKGROUND",    (4,0), (6,0), BAJA),
            ("BACKGROUND",    (3,0), (3,-1), BLANCO),
            ("TEXTCOLOR",     (0,0), (2,0), BLANCO),
            ("TEXTCOLOR",     (4,0), (6,0), BLANCO),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
            ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
            ("ROWBACKGROUNDS",(0,1), (2,-1), [BLANCO, colors.HexColor("#e8f0ff")]),
            ("ROWBACKGROUNDS",(4,1), (6,-1), [BLANCO, colors.HexColor("#fff0ee")]),
            ("ALIGN",         (1,0), (-1,-1), "RIGHT"),
            ("ALIGN",         (0,0), (0,-1), "LEFT"),
            ("ALIGN",         (4,0), (4,-1), "LEFT"),
            ("GRID",          (0,0), (2,-1), 0.4, colors.HexColor("#aac4ff")),
            ("GRID",          (4,0), (6,-1), 0.4, colors.HexColor("#ffaaa0")),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("RIGHTPADDING",  (0,0), (-1,-1), 6),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("TEXTCOLOR",     (1,1), (1,-1), ALZA),
            ("FONTNAME",      (1,1), (1,-1), "Helvetica-Bold"),
            ("TEXTCOLOR",     (5,1), (5,-1), BAJA),
            ("FONTNAME",      (5,1), (5,-1), "Helvetica-Bold"),
        ])
        t_mv.setStyle(ts3)
        story.append(t_mv)
    story.append(Spacer(1, 12))

    # ── SECCIÓN 4: SEÑALES TÉCNICAS ──────────────────────────────
    story.append(Paragraph("4.  SEÑALES TÉCNICAS ACTIVAS", E["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ORO, spaceAfter=8))

    tec_rows = [["ÍNDICE", "RSI 14", "ZONA RSI", "vs EMA 200", "vs EMA 50", "TENDENCIA"]]
    for nombre, key, df_i in indices:
        if df_i is None or df_i.empty or "Close" not in df_i.columns:
            tec_rows.append([nombre] + ["—"]*5); continue
        close = df_i["Close"].dropna()
        if len(close) < 50:
            tec_rows.append([nombre] + ["—"]*5); continue

        rsi_v  = rsi_calc(close) if len(close) >= 14 else None
        ema50  = ema_calc(close, 50)  if len(close) >= 50 else None
        ema200 = ema_calc(close, 200) if len(close) >= 200 else None
        precio = float(close.iloc[-1])

        zona = "NEUTRAL"
        if rsi_v:
            if rsi_v > 70:   zona = "SOBRECOMPRA"
            elif rsi_v < 30: zona = "SOBREVENTA"

        vs200 = f"+{(precio/ema200-1)*100:.1f}%" if ema200 else "—"
        vs50  = f"+{(precio/ema50-1)*100:.1f}%"  if ema50  else "—"
        if ema200:
            vs200 = f"+{(precio/ema200-1)*100:.1f}%" if precio > ema200 else f"{(precio/ema200-1)*100:.1f}%"
        if ema50:
            vs50  = f"+{(precio/ema50-1)*100:.1f}%"  if precio > ema50  else f"{(precio/ema50-1)*100:.1f}%"

        tend = "ALCISTA" if (ema50 and ema200 and ema50 > ema200 and precio > ema50) else \
               "BAJISTA" if (ema50 and ema200 and ema50 < ema200 and precio < ema50) else "MIXTA"

        tec_rows.append([
            nombre,
            f"{rsi_v:.1f}" if rsi_v else "—",
            zona, vs200, vs50, tend
        ])

    t_tec = Table(tec_rows, colWidths=[3*cm, 1.8*cm, 2.4*cm, 2.2*cm, 2.2*cm, 2.5*cm])
    ts4 = tabla_style_base(None)
    for r in range(1, len(tec_rows)):
        # Color tendencia
        tend = tec_rows[r][5]
        c_t = ALZA if tend == "ALCISTA" else (BAJA if tend == "BAJISTA" else ORO_OSC)
        ts4.add("TEXTCOLOR", (5,r), (5,r), c_t)
        ts4.add("FONTNAME",  (5,r), (5,r), "Helvetica-Bold")
        # Color RSI zona
        zona = tec_rows[r][2]
        c_z = BAJA if zona == "SOBRECOMPRA" else (ALZA if zona == "SOBREVENTA" else NEGRO)
        ts4.add("TEXTCOLOR", (2,r), (2,r), c_z)
    t_tec.setStyle(ts4)
    story.append(t_tec)
    story.append(Spacer(1, 12))

    # ── SECCIÓN 5: PROYECCIÓN ESTRATÉGICA ────────────────────────
    story.append(Paragraph("5.  PROYECCIÓN ESTRATÉGICA — APERTURA DE MAÑANA", E["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ORO, spaceAfter=8))

    # Estadística histórica
    proyecciones = []
    if df_idx_sp is not None and not df_idx_sp.empty and "Close" in df_idx_sp.columns:
        close_sp = df_idx_sp["Close"].dropna()
        mañana_dow = (hoy + timedelta(days=1)).weekday()
        prob, ret_med = retorno_historico_dia_semana(close_sp, mañana_dow)
        dias_nombres = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
        dia_nombre = dias_nombres[mañana_dow]

        if prob is not None:
            proyecciones.append(
                f"📊 <b>Estadística histórica (5 años):</b> Los {dia_nombre}s el S&P 500 sube "
                f"<b>{prob}%</b> de las veces, con retorno promedio de <b>{ret_med:+.2f}%</b>."
            )

        # Contexto de tendencia
        if len(close_sp) >= 200:
            precio_act = float(close_sp.iloc[-1])
            e200 = float(close_sp.ewm(span=200, adjust=False).mean().iloc[-1])
            e50  = float(close_sp.ewm(span=50,  adjust=False).mean().iloc[-1])
            rsi_act = rsi_calc(close_sp)

            if precio_act > e200 and e50 > e200:
                proyecciones.append(
                    "📈 <b>Tendencia primaria ALCISTA:</b> El S&P 500 cotiza sobre EMA 50 y EMA 200. "
                    "La estructura técnica favorece continuación al alza. "
                    f"Soporte clave: EMA 200 en <b>{e200:,.0f}</b> pts."
                )
            elif precio_act < e200:
                proyecciones.append(
                    "📉 <b>Tendencia primaria BAJISTA:</b> El S&P 500 cotiza bajo su EMA 200. "
                    "Mantener cautela. Resistencia clave: "
                    f"EMA 200 en <b>{e200:,.0f}</b> pts."
                )

            if rsi_act > 65:
                proyecciones.append(
                    f"⚠️ <b>RSI elevado ({rsi_act:.1f}):</b> Mercado en zona de sobrecompra. "
                    "Probabilidad de consolidación o retroceso técnico en el corto plazo."
                )
            elif rsi_act < 35:
                proyecciones.append(
                    f"💡 <b>RSI bajo ({rsi_act:.1f}):</b> Mercado en zona de sobreventa. "
                    "Posible rebote técnico. Vigilar confirmación con volumen."
                )

        # Lectura de tasas
        ust10 = macro_val("UST_10Y", "Último Valor") or macro_val("UST 10Y", "Último Valor")
        if ust10:
            if ust10 > 4.5:
                proyecciones.append(
                    f"🏦 <b>Tasas UST 10Y en {ust10:.2f}%:</b> Nivel elevado que comprime múltiplos. "
                    "Presión sobre growth y tech. Vigilar decisiones Fed."
                )
            elif ust10 < 3.5:
                proyecciones.append(
                    f"🏦 <b>Tasas UST 10Y en {ust10:.2f}%:</b> Tasas bajas — entorno favorable "
                    "para renta variable y activos de riesgo."
                )

    # Niveles a vigilar mañana
    if df_idx_sp is not None and not df_idx_sp.empty and "Close" in df_idx_sp.columns:
        close_sp = df_idx_sp["Close"].dropna()
        high_sp  = df_idx_sp["High"].dropna() if "High" in df_idx_sp.columns else close_sp
        low_sp   = df_idx_sp["Low"].dropna()  if "Low"  in df_idx_sp.columns else close_sp
        if len(close_sp) >= 200:
            precio_act = float(close_sp.iloc[-1])
            e20  = float(close_sp.ewm(span=20,  adjust=False).mean().iloc[-1])
            e50  = float(close_sp.ewm(span=50,  adjust=False).mean().iloc[-1])
            e200 = float(close_sp.ewm(span=200, adjust=False).mean().iloc[-1])

            niveles_data = [
                ["NIVEL A VIGILAR", "VALOR", "SIGNIFICADO"],
                ["Precio actual",   f"{precio_act:,.0f}", "Referencia de cierre"],
                ["EMA 20",          f"{e20:,.0f}",  "Soporte/resistencia corto plazo"],
                ["EMA 50",          f"{e50:,.0f}",  "Tendencia intermedia"],
                ["EMA 200",         f"{e200:,.0f}", "Tendencia primaria — nivel crítico"],
            ]
            t_niv = Table(niveles_data, colWidths=[4*cm, 2.5*cm, 9.1*cm])
            ts5 = tabla_style_base(None, header_bg=colors.HexColor("#2c2200"))
            t_niv.setStyle(ts5)
            proyecciones_text = "<br/><br/>".join(proyecciones) if proyecciones else "Sin datos suficientes."
            story.append(Paragraph(proyecciones_text, E["body"]))
            story.append(Spacer(1, 10))
            story.append(t_niv)
    else:
        story.append(Paragraph("Sin datos históricos suficientes para proyección.", E["body"]))

    story.append(Spacer(1, 14))

    # ── SECCIÓN 6: PLAN DE ACCIÓN ─────────────────────────────────
    story.append(Paragraph("6.  PLAN DE ACCIÓN PARA LA APERTURA", E["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ORO, spaceAfter=8))

    acciones = []
    if sp_dia is not None:
        if sp_dia > 1:
            acciones.append("✅ Sesión positiva: considerar mantener posiciones largas. Trailing stop activo en ganancias abiertas.")
            acciones.append("🔍 Vigilar apertura — si los futuros SP500 abren positivos (+0.3% o más), tendencia con momentum.")
        elif sp_dia < -1:
            acciones.append("🛡️ Sesión negativa: revisar stops de protección. No promediar a la baja sin confirmación técnica.")
            acciones.append("🔍 Si futuros abren negativos, esperar primera media hora para evaluar si es capitulación o continuación.")
        else:
            acciones.append("➡️ Sesión neutral: mercado en pausa. Esperar ruptura de rango para posicionarse.")

    acciones += [
        "📰 Revisar agenda económica del día: datos de empleo, IPC o decisiones Fed mueven el mercado intraday.",
        "📊 Monitorear VIX al abrir: sobre 20 indica volatilidad elevada. Reducir tamaño de posición.",
        "💱 Atención al DXY: dólar fuerte suele presionar commodities y emergentes.",
    ]

    for a in acciones:
        story.append(Paragraph(f"• {a}", E["body"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 14))

    # ── FOOTER ───────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ORO))
    story.append(Spacer(1, 6))
    footer_txt = (
        f"JST ALPHA · Reporte generado el {hoy.strftime('%d/%m/%Y a las %H:%M')} hrs  ·  "
        "Este reporte es de uso interno y educativo. No constituye asesoría financiera."
    )
    story.append(Paragraph(footer_txt, E["centrado"]))

    doc.build(story)
    print(f"\n✓ Reporte generado: {ruta_pdf}")
    print(f"  Tamaño: {os.path.getsize(ruta_pdf)/1024:.1f} KB")
    return ruta_pdf


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  JST ALPHA — GENERANDO REPORTE DIARIO")
    print("="*55)
    ruta = generar_reporte()
    # Abrir automáticamente en macOS
    import subprocess
    subprocess.run(["open", ruta])
