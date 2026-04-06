"""
DESCARGA DE BALANCES TRIMESTRALES - ÚLTIMOS 5 AÑOS
S&P 500 | Nasdaq 100 | Dow Jones 30

Por cada empresa descarga:
  - Income Statement (Estado de Resultados) - trimestral
  - Balance Sheet (Balance General) - trimestral
  - Cash Flow Statement (Flujo de Caja) - trimestral

Guarda en: data/financials/{ticker}_income.csv
                            {ticker}_balance.csv
                            {ticker}_cashflow.csv
"""

import yfinance as yf
import pandas as pd
import os
import time
from tqdm import tqdm

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
FIN_DIR     = os.path.join(DATA_DIR, "financials")
os.makedirs(FIN_DIR, exist_ok=True)

ERRORES     = []


def cargar_lista(indice: str) -> list:
    carpeta   = os.path.join(DATA_DIR, "raw", indice.lower())
    lista_csv = os.path.join(carpeta, f"_lista_{indice}.csv")
    if not os.path.exists(lista_csv):
        print(f"  ⚠ No se encontró lista de {indice}. Ejecuta primero 01_descargar_datos_historicos.py")
        return []
    return pd.read_csv(lista_csv)["ticker"].tolist()


def descargar_financials(ticker: str) -> dict:
    """Descarga income, balance y cashflow trimestrales de un ticker."""
    try:
        t = yf.Ticker(ticker)
        return {
            "income":   t.quarterly_income_stmt,
            "balance":  t.quarterly_balance_sheet,
            "cashflow": t.quarterly_cashflow,
        }
    except Exception as e:
        return {"error": str(e)}


def guardar_financials(ticker: str, datos: dict) -> str:
    """Guarda los tres estados financieros en CSV. Retorna estado."""
    if "error" in datos:
        return f"error: {datos['error']}"

    guardados = 0
    for tipo, df in datos.items():
        if df is None or df.empty:
            continue
        ruta = os.path.join(FIN_DIR, f"{ticker}_{tipo}.csv")
        # Transponer: filas = trimestres, columnas = métricas
        df.T.to_csv(ruta)
        guardados += 1

    return "ok" if guardados > 0 else "sin_datos"


def procesar_lista(tickers: list, descripcion: str):
    """Descarga y guarda financials para una lista de tickers."""
    print(f"\n{'='*55}")
    print(f"  {descripcion} ({len(tickers)} empresas)")
    print(f"{'='*55}")
    stats = {"ok": 0, "ya_existe": 0, "sin_datos": 0, "error": 0}

    for ticker in tqdm(tickers, desc=descripcion):
        # Verificar si ya fue descargado (al menos el income statement)
        ruta_check = os.path.join(FIN_DIR, f"{ticker}_income.csv")
        if os.path.exists(ruta_check):
            stats["ya_existe"] += 1
            continue

        datos  = descargar_financials(ticker)
        estado = guardar_financials(ticker, datos)

        if estado == "ok":
            stats["ok"] += 1
        elif estado == "ya_existe":
            stats["ya_existe"] += 1
        elif estado == "sin_datos":
            stats["sin_datos"] += 1
        else:
            stats["error"] += 1
            ERRORES.append({"ticker": ticker, "error": estado})

        time.sleep(0.4)   # respetar rate limit

    print(f"  ✓ Descargados: {stats['ok']}  |  Ya existían: {stats['ya_existe']}  |  Sin datos: {stats['sin_datos']}  |  Errores: {stats['error']}")


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  DESCARGA DE BALANCES TRIMESTRALES")
    print("="*55)

    # Unir todos los tickers sin duplicados
    sp500    = cargar_lista("SP500")
    nasdaq   = cargar_lista("NASDAQ100")
    dow      = cargar_lista("DOW30")

    todos = list(dict.fromkeys(sp500 + nasdaq + dow))   # deduplicar preservando orden
    print(f"\n  Total empresas únicas: {len(todos)}")

    # SP500
    if sp500:
        procesar_lista(sp500, "SP500 - Balances")

    # Nasdaq100 (solo los que no están en SP500)
    nq_nuevos = [t for t in nasdaq if t not in set(sp500)]
    if nq_nuevos:
        procesar_lista(nq_nuevos, "NASDAQ100 exclusivos - Balances")

    # Dow30 (solo los que no están ya descargados)
    dow_nuevos = [t for t in dow if t not in set(sp500 + nasdaq)]
    if dow_nuevos:
        procesar_lista(dow_nuevos, "DOW30 exclusivos - Balances")

    # Guardar log de errores
    if ERRORES:
        pd.DataFrame(ERRORES).to_csv(
            os.path.join(FIN_DIR, "_errores_descarga.csv"), index=False
        )
        print(f"\n  ⚠ Errores guardados en: financials/_errores_descarga.csv")

    print(f"\n{'='*55}")
    print(f"  BALANCES DESCARGADOS")
    print(f"  Carpeta: {FIN_DIR}")
    print(f"{'='*55}\n")
