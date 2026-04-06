"""
EXPORTAR BALANCES TRIMESTRALES A EXCEL
Genera: data/BALANCES_TRIMESTRALES.xlsx

Hojas:
  1. Resumen Múltiplos   - P/E, P/B, EV/EBITDA, Market Cap por empresa
  2. Income Statements   - todos los IS consolidados (fila = empresa+trimestre)
  3. Balance Sheets      - todos los BS consolidados
  4. Cash Flows          - todos los CF consolidados
  5-N. Por empresa       - hoja individual con los 3 estados (solo Dow30 por tamaño)
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
from tqdm import tqdm

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")
FIN_DIR   = os.path.join(DATA_DIR, "financials")
OUTPUT    = os.path.join(DATA_DIR, "BALANCES_TRIMESTRALES.xlsx")


def leer_financial(ticker: str, tipo: str) -> pd.DataFrame:
    ruta = os.path.join(FIN_DIR, f"{ticker}_{tipo}.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ruta, index_col=0, parse_dates=True)
        df.index.name = "Trimestre"
        df["Ticker"] = ticker
        for col in df.columns:
            if col != "Ticker":
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def cargar_lista(indice: str) -> list:
    lista_csv = os.path.join(DATA_DIR, "raw", indice.lower(), f"_lista_{indice}.csv")
    if not os.path.exists(lista_csv):
        return []
    return pd.read_csv(lista_csv)["ticker"].tolist()


def obtener_multiplos(tickers: list) -> pd.DataFrame:
    """Obtiene múltiplos fundamentales actuales vía yfinance."""
    filas = []
    for ticker in tqdm(tickers, desc="  Obteniendo múltiplos"):
        try:
            info = yf.Ticker(ticker).info
            filas.append({
                "Ticker":           ticker,
                "Nombre":           info.get("shortName", ""),
                "Sector":           info.get("sector", ""),
                "Industria":        info.get("industry", ""),
                "Market Cap (M)":   round(info.get("marketCap", 0) / 1e6, 1) if info.get("marketCap") else None,
                "P/E (TTM)":        info.get("trailingPE"),
                "P/E Forward":      info.get("forwardPE"),
                "P/B":              info.get("priceToBook"),
                "EV/EBITDA":        info.get("enterpriseToEbitda"),
                "EV/Revenue":       info.get("enterpriseToRevenue"),
                "ROE %":            round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else None,
                "ROA %":            round(info.get("returnOnAssets", 0) * 100, 2) if info.get("returnOnAssets") else None,
                "Margen Bruto %":   round(info.get("grossMargins", 0) * 100, 2) if info.get("grossMargins") else None,
                "Margen Neto %":    round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else None,
                "Deuda/Equity":     info.get("debtToEquity"),
                "Current Ratio":    info.get("currentRatio"),
                "Quick Ratio":      info.get("quickRatio"),
                "Dividend Yield %": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else None,
                "Beta":             info.get("beta"),
                "52W Máx":          info.get("fiftyTwoWeekHigh"),
                "52W Mín":          info.get("fiftyTwoWeekLow"),
                "Precio Actual":    info.get("currentPrice") or info.get("regularMarketPrice"),
            })
        except Exception:
            pass
        import time; time.sleep(0.3)
    if not filas:
        return pd.DataFrame()
    return pd.DataFrame(filas).sort_values("Market Cap (M)", ascending=False)


def consolidar_tipo(tickers: list, tipo: str, descripcion: str) -> pd.DataFrame:
    """Consolida todos los estados financieros de un tipo en un DataFrame."""
    frames = []
    for ticker in tqdm(tickers, desc=f"  Consolidando {descripcion}"):
        df = leer_financial(ticker, tipo)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames).reset_index()


def aplicar_estilo(writer, sheet_name: str, df: pd.DataFrame, color_header: str = "1F4E79"):
    ws = writer.sheets[sheet_name]
    workbook = writer.book
    header_fmt = workbook.add_format({
        "bold": True, "font_color": "FFFFFF", "bg_color": color_header,
        "border": 1, "align": "center", "valign": "vcenter", "font_size": 10
    })
    for col_num, col_name in enumerate(df.columns):
        ancho = max(len(str(col_name)) + 2, 12)
        ws.set_column(col_num, col_num, ancho)
        ws.write(0, col_num, col_name, header_fmt)
    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, len(df), len(df.columns) - 1)


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  GENERANDO EXCEL: BALANCES_TRIMESTRALES.xlsx")
    print("="*55)

    sp500  = cargar_lista("SP500")
    nasdaq = cargar_lista("NASDAQ100")
    dow30  = cargar_lista("DOW30")
    todos  = list(dict.fromkeys(sp500 + nasdaq + dow30))

    print(f"\n  Total empresas únicas: {len(todos)}")

    with pd.ExcelWriter(OUTPUT, engine="xlsxwriter",
                        datetime_format="dd/mm/yyyy") as writer:

        # ── 1. MÚLTIPLOS FUNDAMENTALES ─────────────────────────────
        print("\n[1/5] Obteniendo múltiplos fundamentales (esto tarda ~10 min)...")
        df_mult = obtener_multiplos(todos)
        if not df_mult.empty:
            df_mult.to_excel(writer, sheet_name="Múltiplos Actuales", index=False)
            aplicar_estilo(writer, "Múltiplos Actuales", df_mult, color_header="1F4E79")
        print(f"  ✓ {len(df_mult)} empresas con múltiplos")

        # ── 2. INCOME STATEMENTS CONSOLIDADO ──────────────────────
        print("\n[2/5] Consolidando Income Statements...")
        df_is = consolidar_tipo(todos, "income", "Income Stmt")
        if not df_is.empty:
            df_is.to_excel(writer, sheet_name="Income Statements", index=False)
            aplicar_estilo(writer, "Income Statements", df_is, color_header="2E7D32")
        print(f"  ✓ {len(df_is)} filas")

        # ── 3. BALANCE SHEETS CONSOLIDADO ─────────────────────────
        print("\n[3/5] Consolidando Balance Sheets...")
        df_bs = consolidar_tipo(todos, "balance", "Balance Sheet")
        if not df_bs.empty:
            df_bs.to_excel(writer, sheet_name="Balance Sheets", index=False)
            aplicar_estilo(writer, "Balance Sheets", df_bs, color_header="6A1B9A")
        print(f"  ✓ {len(df_bs)} filas")

        # ── 4. CASH FLOWS CONSOLIDADO ──────────────────────────────
        print("\n[4/5] Consolidando Cash Flows...")
        df_cf = consolidar_tipo(todos, "cashflow", "Cash Flow")
        if not df_cf.empty:
            df_cf.to_excel(writer, sheet_name="Cash Flows", index=False)
            aplicar_estilo(writer, "Cash Flows", df_cf, color_header="BF360C")
        print(f"  ✓ {len(df_cf)} filas")

        # ── 5. DOW30 DETALLE POR EMPRESA ──────────────────────────
        print("\n[5/5] Hojas individuales Dow30...")
        for ticker in tqdm(dow30, desc="  Dow30 detalle"):
            df_i = leer_financial(ticker, "income")
            df_b = leer_financial(ticker, "balance")
            df_c = leer_financial(ticker, "cashflow")

            datos = {}
            if not df_i.empty: datos["IS"] = df_i.drop(columns=["Ticker"], errors="ignore")
            if not df_b.empty: datos["BS"] = df_b.drop(columns=["Ticker"], errors="ignore")
            if not df_c.empty: datos["CF"] = df_c.drop(columns=["Ticker"], errors="ignore")

            if not datos:
                continue

            sheet = f"{ticker}"[:31]   # Excel límite 31 chars
            # Combinar los 3 estados uno debajo del otro con separación
            fila_actual = 0
            ws = writer.book.add_worksheet(sheet)
            writer.sheets[sheet] = ws
            workbook = writer.book
            titulo_fmt = workbook.add_format({"bold": True, "font_size": 12, "bg_color": "1F4E79", "font_color": "FFFFFF"})

            for label, df_t in datos.items():
                ws.write(fila_actual, 0, {"IS": "INCOME STATEMENT", "BS": "BALANCE SHEET", "CF": "CASH FLOW"}[label], titulo_fmt)
                fila_actual += 1
                df_t.reset_index().to_excel(writer, sheet_name=sheet, startrow=fila_actual, index=False)
                fila_actual += len(df_t) + 3

    print(f"\n{'='*55}")
    print(f"  EXCEL GENERADO: {OUTPUT}")
    print(f"{'='*55}\n")
