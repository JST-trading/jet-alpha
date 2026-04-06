"""
DESCARGA DE DATOS HISTÓRICOS - 5 AÑOS
S&P 500 | Nasdaq 100 | Dow Jones 30

Guarda archivos CSV por empresa en data/raw/{indice}/
También descarga los índices completos y macro (tasas, commodities, monedas)
"""

import yfinance as yf
import pandas as pd
import requests
import io
import os
import time
from tqdm import tqdm
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}

# ─── CONFIGURACIÓN ────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")
START_DATE = (datetime.today() - timedelta(days=5*365)).strftime("%Y-%m-%d")
END_DATE   = datetime.today().strftime("%Y-%m-%d")

# ─── TICKERS DE ÍNDICES Y MACRO ───────────────────────────────────
INDICES = {
    "^GSPC":  "SP500",
    "^IXIC":  "NASDAQ_COMP",
    "^DJI":   "DOW_JONES",
}

COMMODITIES = {
    "GC=F":  "Oro",
    "CL=F":  "Petroleo_WTI",
    "BZ=F":  "Petroleo_Brent",
    "SI=F":  "Plata",
    "HG=F":  "Cobre",
    "PL=F":  "Platino",
    "BTC-USD": "Bitcoin",
    "LIT":   "Litio_ETF",       # Global X Lithium & Battery Tech ETF
    "ALB":   "Albemarle_Litio", # mayor productor litio del mundo
    "SQM":   "SQM_Litio",       # Sociedad Química y Minera (Chile)
    "LTHM":  "Livent_Litio",    # productor litio puro
}

TASAS = {
    "^IRX":  "UST_3M",
    "^FVX":  "UST_5Y",
    "^TNX":  "UST_10Y",
    "^TYX":  "UST_30Y",
    "SHY":   "UST_2Y_ETF",   # proxy 2 años
    "IEF":   "UST_7_10Y_ETF",
    "TLT":   "UST_20_30Y_ETF",
}

MONEDAS = {
    "EURUSD=X": "EUR_USD",
    "GBPUSD=X": "GBP_USD",
    "JPY=X":    "USD_JPY",
    "CNY=X":    "USD_CNY",
    "AUDUSD=X": "AUD_USD",
    "CLP=X":    "USD_CLP",   # peso chileno
    "DX-Y.NYB": "DXY_Dollar_Index",
}


# ─── FUNCIONES ────────────────────────────────────────────────────

def descargar_ticker(ticker: str, nombre: str, carpeta: str):
    """Descarga OHLCV de un ticker y lo guarda como CSV."""
    ruta = os.path.join(carpeta, f"{nombre}.csv")
    if os.path.exists(ruta):
        return "ya_existe"
    try:
        df = yf.download(ticker, start=START_DATE, end=END_DATE,
                         progress=False, auto_adjust=True)
        if df.empty:
            return "sin_datos"
        df.to_csv(ruta)
        return "ok"
    except Exception as e:
        return f"error: {e}"


def _leer_html(url: str) -> list:
    """Descarga HTML con headers para evitar bloqueo 403."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return pd.read_html(io.StringIO(resp.text))


def obtener_sp500() -> list:
    """Lee lista S&P 500 desde Wikipedia."""
    tablas = _leer_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    tabla = tablas[0]
    return tabla["Symbol"].str.replace(".", "-", regex=False).tolist()


def obtener_nasdaq100() -> list:
    """Lee lista Nasdaq 100 desde Wikipedia."""
    tablas = _leer_html("https://en.wikipedia.org/wiki/Nasdaq-100")
    for t in tablas:
        if "Ticker" in t.columns:
            return t["Ticker"].str.replace(".", "-", regex=False).tolist()
    return []


def obtener_dow30() -> list:
    """Lee lista Dow Jones 30 desde Wikipedia."""
    try:
        tablas = _leer_html("https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average")
        for t in tablas:
            if "Symbol" in t.columns:
                return t["Symbol"].str.replace(".", "-", regex=False).tolist()
    except Exception:
        pass
    # Fallback hardcoded (componentes actuales)
    return [
        "AAPL","AMGN","AXP","BA","CAT","CRM","CSCO","CVX","DIS","DOW",
        "GS","HD","HON","IBM","JNJ","JPM","KO","MCD","MMM","MRK",
        "MSFT","NKE","PG","SHW","TRV","UNH","V","VZ","WMT","NVDA"
    ]


def descargar_grupo(tickers_dict: dict, carpeta: str, descripcion: str):
    """Descarga un diccionario {ticker: nombre} en una carpeta."""
    os.makedirs(carpeta, exist_ok=True)
    print(f"\n{'='*50}")
    print(f"  {descripcion}")
    print(f"{'='*50}")
    resultados = {"ok": 0, "ya_existe": 0, "sin_datos": 0, "error": 0}
    for ticker, nombre in tqdm(tickers_dict.items(), desc=descripcion):
        estado = descargar_ticker(ticker, nombre, carpeta)
        if estado == "ok":
            resultados["ok"] += 1
        elif estado == "ya_existe":
            resultados["ya_existe"] += 1
        elif estado == "sin_datos":
            resultados["sin_datos"] += 1
        else:
            resultados["error"] += 1
        time.sleep(0.3)   # respetar rate limit de Yahoo Finance
    print(f"  ✓ Descargados: {resultados['ok']}  |  Ya existían: {resultados['ya_existe']}  |  Sin datos: {resultados['sin_datos']}  |  Errores: {resultados['error']}")


def descargar_empresas_indice(nombre_indice: str, tickers: list, carpeta: str):
    """Descarga todas las empresas de un índice."""
    os.makedirs(carpeta, exist_ok=True)
    print(f"\n{'='*50}")
    print(f"  EMPRESAS {nombre_indice} ({len(tickers)} tickers)")
    print(f"{'='*50}")
    ok = ya = sin_datos = err = 0
    for ticker in tqdm(tickers, desc=nombre_indice):
        estado = descargar_ticker(ticker, ticker, carpeta)
        if estado == "ok":       ok += 1
        elif estado == "ya_existe": ya += 1
        elif estado == "sin_datos": sin_datos += 1
        else:                    err += 1
        time.sleep(0.2)
    print(f"  ✓ Descargados: {ok}  |  Ya existían: {ya}  |  Sin datos: {sin_datos}  |  Errores: {err}")

    # Guardar lista de tickers del índice
    pd.Series(tickers).to_csv(
        os.path.join(carpeta, f"_lista_{nombre_indice}.csv"), index=False, header=["ticker"]
    )


# ─── MAIN ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  DESCARGA DE DATOS HISTÓRICOS")
    print(f"  Período: {START_DATE} → {END_DATE}")
    print("="*50)

    # 1. Índices completos (como activo)
    descargar_grupo(INDICES,     os.path.join(DATA_DIR, "indices"),    "ÍNDICES")

    # 2. Commodities + Bitcoin
    descargar_grupo(COMMODITIES, os.path.join(DATA_DIR, "commodities"), "COMMODITIES + BTC")

    # 3. Tasas de interés USA
    descargar_grupo(TASAS,       os.path.join(DATA_DIR, "rates"),      "TASAS UST")

    # 4. Monedas principales
    descargar_grupo(MONEDAS,     os.path.join(DATA_DIR, "currencies"), "MONEDAS")

    # 5. Empresas S&P 500
    print("\nObteniendo lista S&P 500...")
    sp500 = obtener_sp500()
    descargar_empresas_indice("SP500", sp500, os.path.join(DATA_DIR, "raw", "sp500"))

    # 6. Empresas Nasdaq 100
    print("\nObteniendo lista Nasdaq 100...")
    nasdaq100 = obtener_nasdaq100()
    descargar_empresas_indice("NASDAQ100", nasdaq100, os.path.join(DATA_DIR, "raw", "nasdaq100"))

    # 7. Empresas Dow Jones 30
    print("\nObteniendo lista Dow Jones 30...")
    dow30 = obtener_dow30()
    descargar_empresas_indice("DOW30", dow30, os.path.join(DATA_DIR, "raw", "dow30"))

    print("\n" + "="*50)
    print("  DESCARGA COMPLETA")
    print("="*50)
    print(f"\nDatos guardados en: {DATA_DIR}")
