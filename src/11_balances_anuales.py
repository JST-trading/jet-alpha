"""
BALANCES ANUALES — DESCARGA Y EXPORTACIÓN A EXCEL
Descarga Income Statement, Balance Sheet y Cash Flow ANUALES de yfinance
y genera un Excel por índice con una hoja por empresa.

Archivos generados:
  data/financials_annual/{ticker}_income.csv
  data/financials_annual/{ticker}_balance.csv
  data/financials_annual/{ticker}_cashflow.csv

  data/BALANCES_ANUALES_SP500.xlsx
  data/BALANCES_ANUALES_NASDAQ100.xlsx
  data/BALANCES_ANUALES_DOW30.xlsx
"""

import os
import time
import yfinance as yf
import pandas as pd
from tqdm import tqdm

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
FIN_DIR     = os.path.join(DATA_DIR, "financials_annual")
os.makedirs(FIN_DIR, exist_ok=True)

ERRORES = []


# ─────────────────────────────────────────────
# DESCARGA
# ─────────────────────────────────────────────

def cargar_lista(indice: str) -> list:
    carpeta   = os.path.join(DATA_DIR, "raw", indice.lower())
    lista_csv = os.path.join(carpeta, f"_lista_{indice}.csv")
    if not os.path.exists(lista_csv):
        print(f"  ⚠ No se encontró lista de {indice}. Ejecuta primero 01_descargar_datos_historicos.py")
        return []
    return pd.read_csv(lista_csv)["ticker"].tolist()


def descargar_anuales(ticker: str) -> dict:
    """Descarga los tres estados financieros ANUALES."""
    try:
        t = yf.Ticker(ticker)
        return {
            "income":   t.income_stmt,
            "balance":  t.balance_sheet,
            "cashflow": t.cashflow,
        }
    except Exception as e:
        return {"error": str(e)}


def guardar_anuales(ticker: str, datos: dict) -> str:
    if "error" in datos:
        return f"error: {datos['error']}"
    guardados = 0
    for tipo, df in datos.items():
        if df is None or df.empty:
            continue
        ruta = os.path.join(FIN_DIR, f"{ticker}_{tipo}.csv")
        df.T.to_csv(ruta)
        guardados += 1
    return "ok" if guardados > 0 else "sin_datos"


def procesar_descarga(tickers: list, descripcion: str):
    print(f"\n{'='*55}")
    print(f"  {descripcion} ({len(tickers)} empresas)")
    print(f"{'='*55}")
    stats = {"ok": 0, "ya_existe": 0, "sin_datos": 0, "error": 0}

    for ticker in tqdm(tickers, desc=descripcion):
        ruta_check = os.path.join(FIN_DIR, f"{ticker}_income.csv")
        if os.path.exists(ruta_check):
            stats["ya_existe"] += 1
            continue

        datos  = descargar_anuales(ticker)
        estado = guardar_anuales(ticker, datos)

        if estado == "ok":
            stats["ok"] += 1
        elif estado == "sin_datos":
            stats["sin_datos"] += 1
        else:
            stats["error"] += 1
            ERRORES.append({"ticker": ticker, "error": estado})

        time.sleep(0.4)

    print(f"  ✓ Descargados: {stats['ok']}  |  Ya existían: {stats['ya_existe']}  |  Sin datos: {stats['sin_datos']}  |  Errores: {stats['error']}")


# ─────────────────────────────────────────────
# GENERACIÓN EXCEL
# ─────────────────────────────────────────────

def leer_estado(ticker: str, tipo: str) -> pd.DataFrame:
    ruta = os.path.join(FIN_DIR, f"{ticker}_{tipo}.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ruta, index_col=0)
        df.index.name = "Año"
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def escribir_hoja_balance(writer, ticker: str):
    """Escribe IS + BS + CF anuales en una misma hoja, apilados."""
    wb  = writer.book
    nombre_hoja = ticker[:31]
    ws  = wb.add_worksheet(nombre_hoja)
    writer.sheets[nombre_hoja] = ws

    fmt_titulo = wb.add_format({
        "bold": True, "font_size": 12,
        "bg_color": "1F4E79", "font_color": "FFFFFF", "border": 1
    })
    fmt_header = wb.add_format({
        "bold": True, "bg_color": "2E4057",
        "font_color": "FFFFFF", "border": 1, "font_size": 9
    })
    fmt_metrica = wb.add_format({
        "bold": True, "bg_color": "1A1F35",
        "font_color": "C8D6E5", "font_size": 9
    })
    fmt_num = wb.add_format({
        "num_format": "#,##0", "font_size": 9,
        "bg_color": "0D1117", "font_color": "E6F1FF"
    })
    fmt_num_neg = wb.add_format({
        "num_format": "#,##0", "font_size": 9,
        "bg_color": "0D1117", "font_color": "FF4757"
    })

    estados = [
        ("income",   "INCOME STATEMENT ANUAL (Estado de Resultados)"),
        ("balance",  "BALANCE SHEET ANUAL (Balance General)"),
        ("cashflow", "CASH FLOW STATEMENT ANUAL (Flujo de Caja)"),
    ]

    fila = 0
    tiene_datos = False

    for tipo, label in estados:
        df = leer_estado(ticker, tipo)
        if df.empty:
            continue

        tiene_datos = True
        ws.merge_range(fila, 0, fila, len(df.columns), f"  {label}  —  {ticker}", fmt_titulo)
        fila += 1

        ws.write(fila, 0, "Métrica", fmt_header)
        ws.set_column(0, 0, 45)
        for j, col in enumerate(df.columns):
            # Mostrar solo el año (primeros 10 chars = YYYY-MM-DD → tomar el año)
            label_col = str(col)[:4] if len(str(col)) >= 4 else str(col)
            ws.write(fila, j + 1, label_col, fmt_header)
            ws.set_column(j + 1, j + 1, 18)
        fila += 1

        for metrica in df.index:
            ws.write(fila, 0, str(metrica), fmt_metrica)
            for j, col in enumerate(df.columns):
                val = df.loc[metrica, col]
                if pd.isna(val):
                    ws.write_blank(fila, j + 1, None, fmt_num)
                elif isinstance(val, (int, float)):
                    fmt = fmt_num_neg if val < 0 else fmt_num
                    ws.write_number(fila, j + 1, val, fmt)
                else:
                    ws.write(fila, j + 1, str(val), fmt_num)
            fila += 1

        fila += 2

    return tiene_datos


def generar_excel_anuales(nombre_indice: str, carpeta_raw: str, output: str):
    lista_csv = os.path.join(carpeta_raw, f"_lista_{nombre_indice}.csv")
    if not os.path.exists(lista_csv):
        print(f"  ⚠ No se encontró lista de {nombre_indice}")
        return

    tickers = pd.read_csv(lista_csv)["ticker"].tolist()
    print(f"\n{'='*55}")
    print(f"  {nombre_indice} — {len(tickers)} empresas → {os.path.basename(output)}")
    print(f"{'='*55}")

    ok = sin_datos = 0
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Hoja índice
        filas_resumen = []
        for ticker in tickers:
            for tipo in ["income", "balance", "cashflow"]:
                ruta = os.path.join(FIN_DIR, f"{ticker}_{tipo}.csv")
                anos = 0
                if os.path.exists(ruta):
                    try:
                        anos = len(pd.read_csv(ruta, index_col=0).columns)
                    except Exception:
                        pass
                filas_resumen.append({
                    "Ticker":     ticker,
                    "Estado":     tipo.upper(),
                    "Disponible": "SÍ" if os.path.exists(ruta) else "NO",
                    "Años":       anos,
                })
        df_res = pd.DataFrame(filas_resumen)
        df_res.to_excel(writer, sheet_name="_ÍNDICE", index=False)
        ws_idx = writer.sheets["_ÍNDICE"]
        wb = writer.book
        fmt_h = wb.add_format({"bold": True, "bg_color": "1F4E79",
                                "font_color": "FFFFFF", "border": 1})
        for i, col in enumerate(df_res.columns):
            ws_idx.write(0, i, col, fmt_h)
            ws_idx.set_column(i, i, 15)
        ws_idx.freeze_panes(1, 0)

        # Una hoja por empresa
        for ticker in tqdm(tickers, desc=f"  {nombre_indice}"):
            tiene = escribir_hoja_balance(writer, ticker)
            if tiene:
                ok += 1
            else:
                sin_datos += 1

    print(f"  ✓ Empresas con datos: {ok}  |  Sin datos: {sin_datos}")
    size = os.path.getsize(output) / 1e6
    print(f"  ✓ Archivo: {output} ({size:.1f} MB)")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  BALANCES ANUALES — DESCARGA Y EXCEL")
    print("="*55)

    sp500  = cargar_lista("SP500")
    nasdaq = cargar_lista("NASDAQ100")
    dow    = cargar_lista("DOW30")

    # ── Descarga ──────────────────────────────
    print("\n[ FASE 1: DESCARGA DE DATOS ANUALES ]")

    if sp500:
        procesar_descarga(sp500, "SP500 - Anuales")

    nq_nuevos = [t for t in nasdaq if t not in set(sp500)]
    if nq_nuevos:
        procesar_descarga(nq_nuevos, "NASDAQ100 exclusivos - Anuales")

    dow_nuevos = [t for t in dow if t not in set(sp500 + nasdaq)]
    if dow_nuevos:
        procesar_descarga(dow_nuevos, "DOW30 exclusivos - Anuales")

    if ERRORES:
        pd.DataFrame(ERRORES).to_csv(
            os.path.join(FIN_DIR, "_errores_descarga.csv"), index=False
        )
        print(f"\n  ⚠ Errores guardados en: financials_annual/_errores_descarga.csv")

    # ── Generación Excel ──────────────────────
    print("\n[ FASE 2: GENERACIÓN DE EXCELS ]")

    if sp500:
        generar_excel_anuales(
            "SP500",
            os.path.join(DATA_DIR, "raw", "sp500"),
            os.path.join(DATA_DIR, "BALANCES_ANUALES_SP500.xlsx")
        )
    if nasdaq:
        generar_excel_anuales(
            "NASDAQ100",
            os.path.join(DATA_DIR, "raw", "nasdaq100"),
            os.path.join(DATA_DIR, "BALANCES_ANUALES_NASDAQ100.xlsx")
        )
    if dow:
        generar_excel_anuales(
            "DOW30",
            os.path.join(DATA_DIR, "raw", "dow30"),
            os.path.join(DATA_DIR, "BALANCES_ANUALES_DOW30.xlsx")
        )

    print(f"\n{'='*55}")
    print("  BALANCES ANUALES COMPLETADOS")
    print(f"  Carpeta datos: {FIN_DIR}")
    print(f"  Excels en:     {DATA_DIR}")
    print(f"{'='*55}\n")
