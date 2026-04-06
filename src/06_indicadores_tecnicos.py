"""
INDICADORES TÉCNICOS Y FUNDAMENTALES
Para índices y empresas individuales

Técnicos:
  - Medias móviles: SMA 20/50/100/200
  - MACD (12,26,9)
  - RSI (14)
  - Bollinger Bands (20, 2σ)
  - Fibonacci Retracements
  - TD Sequential (T de Mark)

Fundamentales (vía yfinance):
  - P/E, P/B, EV/EBITDA, Market Cap, ROE, ROA, Márgenes, Deuda

Genera: data/INDICADORES_{TICKER}.xlsx
        data/INDICADORES_INDICES.xlsx  (SPX, Nasdaq, Dow juntos)
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
IND_DIR  = os.path.join(DATA_DIR, "indicadores")
os.makedirs(IND_DIR, exist_ok=True)

START = (datetime.today() - timedelta(days=5*365)).strftime("%Y-%m-%d")
END   = datetime.today().strftime("%Y-%m-%d")


# ══════════════════════════════════════════════════════════════════
# INDICADORES TÉCNICOS
# ══════════════════════════════════════════════════════════════════

def sma(serie: pd.Series, periodo: int) -> pd.Series:
    return serie.rolling(window=periodo).mean().round(4)


def ema(serie: pd.Series, periodo: int) -> pd.Series:
    return serie.ewm(span=periodo, adjust=False).mean().round(4)


def calcular_rsi(serie: pd.Series, periodo: int = 14) -> pd.Series:
    delta  = serie.diff()
    ganancia = delta.clip(lower=0)
    perdida  = (-delta).clip(lower=0)
    avg_g = ganancia.ewm(com=periodo - 1, min_periods=periodo).mean()
    avg_p = perdida.ewm(com=periodo - 1, min_periods=periodo).mean()
    rs    = avg_g / avg_p
    return (100 - (100 / (1 + rs))).round(2)


def calcular_macd(serie: pd.Series,
                  rapido: int = 12, lento: int = 26, signal: int = 9
                  ) -> pd.DataFrame:
    ema_r = ema(serie, rapido)
    ema_l = ema(serie, lento)
    macd_line   = (ema_r - ema_l).round(4)
    signal_line = ema(macd_line, signal).round(4)
    histograma  = (macd_line - signal_line).round(4)
    return pd.DataFrame({
        "MACD":          macd_line,
        "MACD_Signal":   signal_line,
        "MACD_Hist":     histograma,
        "MACD_Cruce":    np.where(macd_line > signal_line, "ALCISTA", "BAJISTA"),
    })


def calcular_bollinger(serie: pd.Series, periodo: int = 20, std: float = 2.0
                       ) -> pd.DataFrame:
    media = sma(serie, periodo)
    desv  = serie.rolling(window=periodo).std()
    upper = (media + std * desv).round(4)
    lower = (media - std * desv).round(4)
    ancho = ((upper - lower) / media * 100).round(2)
    posicion = ((serie - lower) / (upper - lower) * 100).round(2)  # %B
    return pd.DataFrame({
        "BB_Upper":   upper,
        "BB_Media":   media,
        "BB_Lower":   lower,
        "BB_Ancho%":  ancho,
        "BB_PosB%":   posicion,   # >80 sobrecompra, <20 sobreventa
    })


def calcular_fibonacci(df: pd.DataFrame, ventana: int = 252) -> pd.DataFrame:
    """Niveles de Fibonacci sobre el rango del último año."""
    if len(df) < ventana:
        ventana = len(df)
    max_p = df["High"].tail(ventana).max()
    min_p = df["Low"].tail(ventana).min()
    rango = max_p - min_p

    niveles = {
        "Fib_100%":  round(max_p, 4),
        "Fib_78.6%": round(max_p - 0.236 * rango, 4),
        "Fib_61.8%": round(max_p - 0.382 * rango, 4),
        "Fib_50.0%": round(max_p - 0.500 * rango, 4),
        "Fib_38.2%": round(max_p - 0.618 * rango, 4),
        "Fib_23.6%": round(max_p - 0.764 * rango, 4),
        "Fib_0%":    round(min_p, 4),
    }
    # Retorna DataFrame con los niveles como columnas constantes
    df_fib = pd.DataFrame(index=df.index)
    for k, v in niveles.items():
        df_fib[k] = v
    return df_fib


def calcular_td_sequential(close: pd.Series) -> pd.DataFrame:
    """
    TD Sequential (Tom DeMark) simplificado:
    - Setup: 9 cierres consecutivos > o < cierre de 4 barras antes
    - Countdown: 13 barras posteriores (simplificado: conteo acumulado)
    - Señal: Setup 9 = posible agotamiento de tendencia
    """
    n = len(close)
    setup_bull  = [0] * n
    setup_bear  = [0] * n
    señal       = [""] * n

    bull_count = 0
    bear_count = 0

    for i in range(4, n):
        if close.iloc[i] < close.iloc[i - 4]:
            bull_count += 1
            bear_count  = 0
        elif close.iloc[i] > close.iloc[i - 4]:
            bear_count += 1
            bull_count  = 0
        else:
            bull_count = 0
            bear_count = 0

        setup_bull[i] = bull_count
        setup_bear[i] = bear_count

        if bull_count == 9:
            señal[i] = "TD BUY SETUP 9"
        elif bear_count == 9:
            señal[i] = "TD SELL SETUP 9"
        elif bull_count == 13:
            señal[i] = "TD BUY COUNTDOWN"
        elif bear_count == 13:
            señal[i] = "TD SELL COUNTDOWN"

    return pd.DataFrame({
        "TD_Setup_Bull":  setup_bull,
        "TD_Setup_Bear":  setup_bear,
        "TD_Señal":       señal,
    }, index=close.index)


def calcular_todos(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula todos los indicadores técnicos sobre un OHLCV DataFrame."""
    close = df["Close"]
    high  = df["High"]
    low   = df["Low"]

    resultado = df.copy()

    # Medias móviles simples
    for p in [20, 50, 100, 200]:
        resultado[f"SMA_{p}"] = sma(close, p)
        resultado[f"EMA_{p}"] = ema(close, p)

    # Posición vs medias (usar .values para evitar problemas de alineación)
    resultado["Sobre_SMA200"] = np.where(close.values > resultado["SMA_200"].values, "SÍ", "NO")
    resultado["Sobre_SMA50"]  = np.where(close.values > resultado["SMA_50"].values,  "SÍ", "NO")

    # RSI
    resultado["RSI_14"] = calcular_rsi(close, 14)
    resultado["RSI_Zona"] = pd.cut(
        resultado["RSI_14"],
        bins=[0, 30, 45, 55, 70, 100],
        labels=["SOBREVENTA", "Débil", "Neutral", "Fuerte", "SOBRECOMPRA"]
    )

    # MACD
    macd_df = calcular_macd(close)
    resultado = pd.concat([resultado, macd_df], axis=1)

    # Bollinger Bands
    bb_df = calcular_bollinger(close)
    resultado = pd.concat([resultado, bb_df], axis=1)

    # Fibonacci (niveles constantes del último año)
    fib_df = calcular_fibonacci(df)
    resultado = pd.concat([resultado, fib_df], axis=1)

    # TD Sequential
    td_df = calcular_td_sequential(close)
    resultado = pd.concat([resultado, td_df], axis=1)

    # ATR (Average True Range) - volatilidad
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    resultado["ATR_14"] = tr.rolling(14).mean().round(4)
    resultado["ATR%_14"] = (resultado["ATR_14"] / close * 100).round(2)

    # Volumen relativo
    if "Volume" in df.columns:
        resultado["Vol_Ratio_20d"] = (
            df["Volume"] / df["Volume"].rolling(20).mean()
        ).round(2)

    return resultado


# ══════════════════════════════════════════════════════════════════
# FUNDAMENTALES
# ══════════════════════════════════════════════════════════════════

METRICAS_FUNDAMENTALES = [
    "shortName", "sector", "industry",
    "marketCap", "enterpriseValue",
    "trailingPE", "forwardPE", "priceToBook",
    "enterpriseToEbitda", "enterpriseToRevenue",
    "returnOnEquity", "returnOnAssets",
    "grossMargins", "operatingMargins", "profitMargins",
    "revenueGrowth", "earningsGrowth",
    "debtToEquity", "currentRatio", "quickRatio",
    "totalCash", "totalDebt",
    "dividendYield", "payoutRatio",
    "beta", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
    "currentPrice", "targetMeanPrice",
    "numberOfAnalystOpinions", "recommendationMean", "recommendationKey",
]


def obtener_fundamentales(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        datos = {"Ticker": ticker}
        for m in METRICAS_FUNDAMENTALES:
            val = info.get(m)
            # Formatear porcentajes
            if m in ["returnOnEquity", "returnOnAssets", "grossMargins",
                     "operatingMargins", "profitMargins", "revenueGrowth",
                     "earningsGrowth", "dividendYield", "payoutRatio"]:
                val = round(val * 100, 2) if val else None
            elif m in ["marketCap", "enterpriseValue", "totalCash", "totalDebt"]:
                val = round(val / 1e9, 3) if val else None   # en miles de millones
            datos[m] = val
        return datos
    except Exception:
        return {"Ticker": ticker}


# ══════════════════════════════════════════════════════════════════
# SEÑALES / RESUMEN
# ══════════════════════════════════════════════════════════════════

def generar_señales(df: pd.DataFrame, ticker: str) -> dict:
    """Genera resumen de señales del último día."""
    if df.empty or len(df) < 5:
        return {}

    ult = df.iloc[-1]
    señales = {"Ticker": ticker, "Fecha": str(df.index[-1])[:10]}

    # Tendencia por medias
    c = ult.get("Close", None)
    if c:
        señales["Precio"]       = round(c, 2)
        señales["vs_SMA20"]     = f"{round((c/ult['SMA_20']-1)*100,1)}%" if pd.notna(ult.get("SMA_20")) else None
        señales["vs_SMA50"]     = f"{round((c/ult['SMA_50']-1)*100,1)}%" if pd.notna(ult.get("SMA_50")) else None
        señales["vs_SMA200"]    = f"{round((c/ult['SMA_200']-1)*100,1)}%" if pd.notna(ult.get("SMA_200")) else None

    señales["RSI"]          = ult.get("RSI_14")
    señales["RSI_Zona"]     = str(ult.get("RSI_Zona", ""))
    señales["MACD_Cruce"]   = ult.get("MACD_Cruce")
    señales["BB_Pos%"]      = ult.get("BB_PosB%")
    señales["TD_Señal"]     = ult.get("TD_Señal") or "-"
    señales["ATR%"]         = ult.get("ATR%_14")

    # Score resumen (simple)
    score = 0
    if pd.notna(ult.get("RSI_14")):
        if ult["RSI_14"] < 30:   score += 2   # sobreventa = oportunidad compra
        elif ult["RSI_14"] > 70: score -= 2
    if ult.get("MACD_Cruce") == "ALCISTA":
        score += 1
    if pd.notna(ult.get("SMA_200")) and c and c > ult["SMA_200"]:
        score += 1
    if pd.notna(ult.get("BB_PosB%")):
        if ult["BB_PosB%"] < 20:  score += 1
        elif ult["BB_PosB%"] > 80: score -= 1

    señales["Score_Técnico"] = score
    señales["Señal_Global"]  = (
        "COMPRA FUERTE" if score >= 3 else
        "COMPRA"        if score >= 1 else
        "NEUTRAL"       if score == 0 else
        "VENTA"         if score >= -1 else
        "VENTA FUERTE"
    )
    return señales


# ══════════════════════════════════════════════════════════════════
# EXCEL CON FORMATO
# ══════════════════════════════════════════════════════════════════

def aplicar_estilo(writer, sheet_name, df, color: str = "1F4E79"):
    ws = writer.sheets[sheet_name]
    wb = writer.book
    hdr = wb.add_format({"bold": True, "font_color": "FFFFFF",
                         "bg_color": color, "border": 1,
                         "align": "center", "font_size": 10})
    for i, col in enumerate(df.columns):
        ws.set_column(i, i, max(len(str(col)) + 2, 12))
        ws.write(0, i, col, hdr)
    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, len(df), len(df.columns) - 1)


# ══════════════════════════════════════════════════════════════════
# MAIN - GENERAR EXCEL DE ÍNDICES
# ══════════════════════════════════════════════════════════════════

INDICES = {
    "^GSPC":  "SP500",
    "^IXIC":  "NASDAQ_COMP",
    "^DJI":   "DOW_JONES",
}

COMMODITIES_EXTRA = {
    "GC=F":    "Oro",
    "CL=F":    "Petroleo_WTI",
    "SI=F":    "Plata",
    "HG=F":    "Cobre",
    "LIT":     "Litio_ETF",
    "ALB":     "Albemarle",
    "SQM":     "SQM",
    "BTC-USD": "Bitcoin",
}


def procesar_ticker(ticker: str, nombre: str) -> tuple:
    """Descarga datos, calcula indicadores y retorna (df_indicadores, señales)."""
    # Primero intentar leer del CSV local
    for subcarpeta in ["indices", "commodities", os.path.join("raw", "sp500"),
                       os.path.join("raw", "nasdaq100"), os.path.join("raw", "dow30")]:
        ruta = os.path.join(DATA_DIR, subcarpeta, f"{nombre}.csv")
        if os.path.exists(ruta):
            df = pd.read_csv(ruta, skiprows=[1, 2], index_col=0, parse_dates=True)
            df.index.name = "Date"
            df = df[pd.to_datetime(df.index, errors="coerce").notna()]
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            break
    else:
        # Descargar directo
        df = yf.download(ticker, start=START, end=END, progress=False, auto_adjust=True)
        # yfinance nuevo devuelve MultiIndex — aplanarlo
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

    # Asegurar que Close sea una Serie (no DataFrame)
    if isinstance(df.get("Close") if hasattr(df, "get") else None, pd.DataFrame):
        df["Close"] = df["Close"].iloc[:, 0]

    if df.empty or "Close" not in df.columns:
        return pd.DataFrame(), {}

    df_ind = calcular_todos(df)
    señales = generar_señales(df_ind, ticker)
    return df_ind, señales


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  CALCULANDO INDICADORES TÉCNICOS")
    print("="*55)

    output = os.path.join(DATA_DIR, "INDICADORES_INDICES.xlsx")

    señales_list = []
    fund_list    = []

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

        # ── ÍNDICES ────────────────────────────────────────────────
        for ticker, nombre in INDICES.items():
            print(f"\n  [{ticker}] Calculando indicadores...")
            df_ind, señal = procesar_ticker(ticker, nombre)
            if df_ind.empty:
                print(f"  ⚠ Sin datos para {ticker}")
                continue

            # Hoja con histórico + todos los indicadores
            df_ind.index.name = "Fecha"
            df_ind.to_excel(writer, sheet_name=f"{nombre}_Indicadores")
            aplicar_estilo(writer, f"{nombre}_Indicadores",
                           df_ind.reset_index(), color="1B5E20")

            # Hoja solo últimos 252 días (más legible)
            df_rec = df_ind.tail(252)
            df_rec.index.name = "Fecha"
            df_rec.to_excel(writer, sheet_name=f"{nombre}_1A")
            aplicar_estilo(writer, f"{nombre}_1A",
                           df_rec.reset_index(), color="2E7D32")

            señales_list.append(señal)

            # Fundamentales
            fund = obtener_fundamentales(ticker)
            fund_list.append(fund)
            print(f"  ✓ RSI: {señal.get('RSI')} | MACD: {señal.get('MACD_Cruce')} | Señal: {señal.get('Señal_Global')}")

        # ── COMMODITIES + LITIO ────────────────────────────────────
        for ticker, nombre in COMMODITIES_EXTRA.items():
            print(f"\n  [{ticker}] Calculando indicadores...")
            df_ind, señal = procesar_ticker(ticker, nombre)
            if df_ind.empty:
                continue
            df_ind.index.name = "Fecha"
            df_ind.to_excel(writer, sheet_name=f"{nombre[:20]}_Ind")
            aplicar_estilo(writer, f"{nombre[:20]}_Ind",
                           df_ind.reset_index(), color="4A148C")
            señales_list.append(señal)

        # ── HOJA RESUMEN DE SEÑALES ────────────────────────────────
        if señales_list:
            df_señ = pd.DataFrame(señales_list)
            df_señ.to_excel(writer, sheet_name="Resumen Señales", index=False)
            aplicar_estilo(writer, "Resumen Señales", df_señ, color="B71C1C")
            print(f"\n  ✓ Hoja 'Resumen Señales' generada")

        # ── HOJA FUNDAMENTALES ─────────────────────────────────────
        if fund_list:
            df_fund = pd.DataFrame(fund_list)
            df_fund.to_excel(writer, sheet_name="Fundamentales", index=False)
            aplicar_estilo(writer, "Fundamentales", df_fund, color="0D47A1")

    print(f"\n{'='*55}")
    print(f"  EXCEL GENERADO: {output}")
    print(f"{'='*55}\n")
