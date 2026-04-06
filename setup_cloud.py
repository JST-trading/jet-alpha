"""
setup_cloud.py — Descarga datos mínimos para Streamlit Community Cloud
Se ejecuta automáticamente al iniciar la app en la nube
"""
import os, sys
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
for sub in ["indices", "commodities", "raw/sp500", "raw/nasdaq100", "raw/dow30"]:
    os.makedirs(os.path.join(DATA_DIR, sub), exist_ok=True)

# Solo descargar si los archivos no existen
import yfinance as yf

INDICES = {
    "^GSPC": "SP500", "^IXIC": "NASDAQ_COMP", "^DJI": "DOW_JONES",
}
COMMODITIES = {
    "GC=F": "Oro", "CL=F": "Petroleo_WTI", "SI=F": "Plata",
    "HG=F": "Cobre", "BTC-USD": "Bitcoin", "LIT": "Litio_ETF",
    "ALB": "Albemarle_Litio", "SQM": "SQM_Litio",
}
SP500_SAMPLE = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","JPM","V",
    "MA","UNH","XOM","JNJ","PG","HD","AVGO","CVX","MRK","LLY",
    "ABBV","COST","PEP","KO","ADBE","WMT","CRM","MCD","CSCO","ABT",
    "ACN","TMO","NEE","DHR","NKE","TXN","PM","QCOM","UNP","RTX",
    "HON","INTC","CAT","IBM","GS","BA","GE","MMM","SBUX","AMGN",
]
DOW30 = [
    "AAPL","AMGN","AXP","BA","CAT","CRM","CSCO","CVX","DIS","DOW",
    "GS","HD","HON","IBM","INTC","JNJ","JPM","KO","MCD","MMM",
    "MRK","MSFT","NKE","PG","TRV","UNH","V","VZ","WBA","WMT",
]
NASDAQ100_SAMPLE = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","COST","NFLX",
    "AMD","ADBE","QCOM","PEP","CSCO","INTC","INTU","CMCSA","TMUS","AMGN",
    "ISRG","AMAT","MU","LRCX","KLAC","PANW","ADI","MELI","REGN","VRTX",
]

def dl(ticker, path):
    if os.path.exists(path):
        return
    try:
        df = yf.download(ticker, period="5y", auto_adjust=False, progress=False)
        if not df.empty:
            df.to_csv(path)
    except Exception:
        pass

print("⏳ Descargando datos esenciales...")
for t, n in INDICES.items():
    dl(t, os.path.join(DATA_DIR, "indices", f"{n}.csv"))
for t, n in COMMODITIES.items():
    dl(t, os.path.join(DATA_DIR, "commodities", f"{n}.csv"))
for t in SP500_SAMPLE:
    dl(t, os.path.join(DATA_DIR, "raw", "sp500", f"{t}.csv"))
for t in DOW30:
    dl(t, os.path.join(DATA_DIR, "raw", "dow30", f"{t}.csv"))
for t in NASDAQ100_SAMPLE:
    dl(t, os.path.join(DATA_DIR, "raw", "nasdaq100", f"{t}.csv"))
print("✅ Setup completo")
