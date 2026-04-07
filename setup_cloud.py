"""
setup_cloud.py — Descarga y genera todos los datos necesarios en Streamlit Cloud
Se ejecuta automáticamente la primera vez que no hay datos
"""
import os, sys, warnings
warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")

for sub in ["indices","commodities","raw/sp500","raw/nasdaq100","raw/dow30",
            "currencies","rates"]:
    os.makedirs(os.path.join(DATA_DIR, sub), exist_ok=True)

import yfinance as yf
import pandas as pd

# ── Tickers a descargar ─────────────────────────────────────────
INDICES = {
    "^GSPC":"SP500","^IXIC":"NASDAQ_COMP","^DJI":"DOW_JONES",
    "^VIX":"VIX","^RUT":"RUSSELL2000",
}
COMMODITIES = {
    "GC=F":"Oro","CL=F":"Petroleo_WTI","SI=F":"Plata",
    "HG=F":"Cobre","BTC-USD":"Bitcoin","LIT":"Litio_ETF",
    "ALB":"Albemarle_Litio","SQM":"SQM_Litio",
}
CURRENCIES = {
    "EURUSD=X":"EUR_USD","GBPUSD=X":"GBP_USD","JPYUSD=X":"USD_JPY",
    "DX-Y.NYB":"DXY_Dollar_Index","CLP=X":"USD_CLP","AUDUSD=X":"AUD_USD",
    "CNYUSD=X":"USD_CNY",
}
RATES = {
    "^TNX":"US10Y","^FVX":"US5Y","^IRX":"US3M",
}
SP500 = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","JPM","V",
    "MA","UNH","XOM","JNJ","PG","HD","AVGO","CVX","MRK","LLY","ABBV",
    "COST","PEP","KO","ADBE","WMT","CRM","MCD","CSCO","ABT","ACN","TMO",
    "NEE","DHR","NKE","TXN","PM","QCOM","UNP","RTX","HON","INTC","CAT",
    "IBM","GS","BA","GE","MMM","SBUX","AMGN","AMD","NFLX","PYPL","NOW",
    "ISRG","BKNG","ADP","TGT","LOW","DE","LMT","SO","DUK","PLD","AMT",
    "EQIX","SHW","ZTS","GILD","BMY","MO","CL","GD","HCA","CI","CB",
    "ICE","CME","SPGI","BLK","AON","MMC","TRV","AIG","MET","PRU",
]
NASDAQ100 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","COST","NFLX",
    "AMD","ADBE","QCOM","PEP","CSCO","INTC","INTU","CMCSA","TMUS","AMGN",
    "ISRG","AMAT","MU","LRCX","KLAC","PANW","ADI","MELI","REGN","VRTX",
    "CDNS","SNPS","ORLY","ASML","AZN","ABNB","MRNA","KDP","FTNT","PAYX",
]
DOW30 = [
    "AAPL","AMGN","AXP","BA","CAT","CRM","CSCO","CVX","DIS","DOW",
    "GS","HD","HON","IBM","INTC","JNJ","JPM","KO","MCD","MMM",
    "MRK","MSFT","NKE","PG","TRV","UNH","V","VZ","WBA","WMT",
]

def dl(ticker, path, period="5y"):
    """Descarga un ticker y guarda CSV. Silencia errores."""
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return True
    try:
        df = yf.download(ticker, period=period, auto_adjust=False,
                         progress=False, threads=False)
        if not df.empty:
            df.to_csv(path)
            return True
    except Exception:
        pass
    return False

print("⏳ [JST Alpha] Descargando datos de mercado...")

for t, n in INDICES.items():
    dl(t, os.path.join(DATA_DIR, "indices", f"{n}.csv"))

for t, n in COMMODITIES.items():
    dl(t, os.path.join(DATA_DIR, "commodities", f"{n}.csv"))

for t, n in CURRENCIES.items():
    dl(t, os.path.join(DATA_DIR, "currencies", f"{n}.csv"))

for t, n in RATES.items():
    dl(t, os.path.join(DATA_DIR, "rates", f"{n}.csv"))

for t in SP500:
    dl(t, os.path.join(DATA_DIR, "raw", "sp500", f"{t}.csv"))

for t in DOW30:
    dl(t, os.path.join(DATA_DIR, "raw", "dow30", f"{t}.csv"))

for t in NASDAQ100:
    dl(t, os.path.join(DATA_DIR, "raw", "nasdaq100", f"{t}.csv"))

# ── Generar TRADING_DATA.xlsx con datos de mercado ─────────────
print("⏳ [JST Alpha] Generando Excel de mercados...")

def get_info(ticker, nombre, categoria):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if hist.empty:
            return None
        precio = float(hist["Close"].iloc[-1])
        precio_ant = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else precio
        cambio_dia = round((precio / precio_ant - 1) * 100, 2)
        hist_1m = t.history(period="1mo")
        hist_1a = t.history(period="1y")
        cambio_1m = round((precio / float(hist_1m["Close"].iloc[0]) - 1) * 100, 2) if not hist_1m.empty else 0
        cambio_1a = round((precio / float(hist_1a["Close"].iloc[0]) - 1) * 100, 2) if not hist_1a.empty else 0
        return {
            "Activo": nombre, "Ticker": ticker, "Categoría": categoria,
            "Precio": round(precio, 2),
            "Cambio Día %": cambio_dia,
            "Cambio 1M %": cambio_1m,
            "Cambio 1A %": cambio_1a,
        }
    except Exception:
        return None

macro_rows = []
macro_items = [
    ("^GSPC","S&P 500","ÍNDICES"),("^IXIC","Nasdaq","ÍNDICES"),
    ("^DJI","Dow Jones","ÍNDICES"),("^RUT","Russell 2000","ÍNDICES"),
    ("^VIX","VIX","ÍNDICES"),
    ("GC=F","Oro","COMMODITIES"),("CL=F","Petróleo WTI","COMMODITIES"),
    ("SI=F","Plata","COMMODITIES"),("HG=F","Cobre","COMMODITIES"),
    ("BTC-USD","Bitcoin","COMMODITIES"),
    ("EURUSD=X","EUR/USD","MONEDAS"),("GBPUSD=X","GBP/USD","MONEDAS"),
    ("DX-Y.NYB","DXY Index","MONEDAS"),("CLP=X","USD/CLP","MONEDAS"),
    ("^TNX","US 10Y","TASAS UST"),("^FVX","US 5Y","TASAS UST"),
    ("^IRX","US 3M","TASAS UST"),
]

for tkr, nom, cat in macro_items:
    row = get_info(tkr, nom, cat)
    if row:
        macro_rows.append(row)

df_macro = pd.DataFrame(macro_rows) if macro_rows else pd.DataFrame(
    columns=["Activo","Ticker","Categoría","Precio","Cambio Día %","Cambio 1M %","Cambio 1A %"]
)

# SP500 empresas
sp500_rows = []
for t in SP500:
    path = os.path.join(DATA_DIR, "raw", "sp500", f"{t}.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True, skiprows=[1,2])
            if "Close" in df.columns and len(df) >= 2:
                p = float(df["Close"].iloc[-1])
                p1 = float(df["Close"].iloc[-2])
                p1m = float(df["Close"].iloc[-22]) if len(df) >= 22 else p
                p1a = float(df["Close"].iloc[-252]) if len(df) >= 252 else p
                sp500_rows.append({
                    "Ticker": t,
                    "Cambio Día %": round((p/p1-1)*100,2),
                    "Cambio 1M %":  round((p/p1m-1)*100,2),
                    "Cambio 1A %":  round((p/p1a-1)*100,2),
                    "Precio": round(p,2),
                })
        except Exception:
            pass

df_sp500 = pd.DataFrame(sp500_rows) if sp500_rows else pd.DataFrame(
    columns=["Ticker","Cambio Día %","Cambio 1M %","Cambio 1A %","Precio"])

# Dow30 y Nasdaq100 (mismo proceso)
def make_emp_df(tickers, folder):
    rows = []
    for t in tickers:
        path = os.path.join(DATA_DIR, "raw", folder, f"{t}.csv")
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, index_col=0, parse_dates=True, skiprows=[1,2])
                if "Close" in df.columns and len(df) >= 2:
                    p = float(df["Close"].iloc[-1])
                    p1 = float(df["Close"].iloc[-2])
                    p1m = float(df["Close"].iloc[-22]) if len(df) >= 22 else p
                    p1a = float(df["Close"].iloc[-252]) if len(df) >= 252 else p
                    rows.append({
                        "Ticker": t,
                        "Cambio Día %": round((p/p1-1)*100,2),
                        "Cambio 1M %":  round((p/p1m-1)*100,2),
                        "Cambio 1A %":  round((p/p1a-1)*100,2),
                        "Precio": round(p,2),
                    })
            except Exception:
                pass
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Ticker","Cambio Día %","Cambio 1M %","Cambio 1A %","Precio"])

df_dow   = make_emp_df(DOW30,    "dow30")
df_nq    = make_emp_df(NASDAQ100,"nasdaq100")

xlsx_path = os.path.join(DATA_DIR, "TRADING_DATA.xlsx")
try:
    with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
        df_macro.to_excel(writer, sheet_name="Resumen Macro",     index=False)
        df_sp500.to_excel(writer, sheet_name="SP500 Empresas",    index=False)
        df_dow.to_excel(  writer, sheet_name="Dow30 Empresas",    index=False)
        df_nq.to_excel(   writer, sheet_name="Nasdaq100 Empresas",index=False)
    print("✅ [JST Alpha] TRADING_DATA.xlsx generado")
except Exception as e:
    print(f"⚠️ Excel error: {e}")

print("✅ [JST Alpha] Setup completo — datos listos")
