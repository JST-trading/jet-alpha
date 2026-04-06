"""
EXPORTAR DATOS A EXCEL
Genera: data/TRADING_DATA.xlsx

Hojas:
  1. Resumen Macro      - últimos valores de todo
  2. SP500              - precios históricos del índice
  3. Nasdaq             - precios históricos del índice
  4. Dow Jones          - precios históricos del índice
  5. Commodities        - histórico completo
  6. Tasas UST          - histórico completo
  7. Monedas            - histórico completo
  8. SP500 Empresas     - resumen última semana por empresa
  9. Nasdaq100 Empresas - resumen última semana por empresa
 10. Dow30 Empresas     - resumen última semana por empresa
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")
OUTPUT    = os.path.join(DATA_DIR, "TRADING_DATA.xlsx")

# ─── HELPERS ──────────────────────────────────────────────────────

def leer_csv(ruta: str) -> pd.DataFrame:
    """Lee CSV de yfinance que tiene 3 filas de cabecera (Price/Ticker/Date)."""
    try:
        # yfinance guarda: fila0=nombres, fila1=ticker, fila2="Date",,,
        # skiprows=[1,2] salta esas dos filas extra
        df = pd.read_csv(ruta, skiprows=[1, 2], index_col=0, parse_dates=True)
        df.index.name = "Date"
        # Descartar filas que no sean fechas (por si queda algún residuo)
        df = df[pd.to_datetime(df.index, errors="coerce").notna()]
        # Convertir todo a numérico
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def cargar_carpeta(carpeta: str, nombres: dict) -> pd.DataFrame:
    """Carga múltiples CSVs y los combina en un DataFrame (columna = activo, fila = fecha)."""
    frames = {}
    for ticker, nombre in nombres.items():
        ruta = os.path.join(carpeta, f"{nombre}.csv")
        df = leer_csv(ruta)
        if not df.empty and "Close" in df.columns:
            frames[nombre] = df["Close"].rename(nombre)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames.values(), axis=1).sort_index()


def resumen_empresas(carpeta: str, lista_csv: str) -> pd.DataFrame:
    """Genera tabla resumen con datos de cada empresa del índice."""
    lista_path = os.path.join(carpeta, lista_csv)
    if not os.path.exists(lista_path):
        return pd.DataFrame()

    tickers = pd.read_csv(lista_path)["ticker"].tolist()
    filas = []
    for ticker in tqdm(tickers, desc=f"  Leyendo {lista_csv}"):
        ruta = os.path.join(carpeta, f"{ticker}.csv")
        df = leer_csv(ruta)
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if len(close) < 2:
            continue

        ultimo   = close.iloc[-1]
        anterior = close.iloc[-2]
        hace_1m  = close.iloc[-22] if len(close) >= 22 else None
        hace_3m  = close.iloc[-66] if len(close) >= 66 else None
        hace_1y  = close.iloc[-252] if len(close) >= 252 else None
        min_52w  = close.tail(252).min() if len(close) >= 252 else close.min()
        max_52w  = close.tail(252).max() if len(close) >= 252 else close.max()

        fila = {
            "Ticker":        ticker,
            "Último Precio": round(ultimo, 2),
            "Cambio Día %":  round((ultimo / anterior - 1) * 100, 2) if anterior else None,
            "Cambio 1M %":   round((ultimo / hace_1m - 1) * 100, 2) if hace_1m is not None else None,
            "Cambio 3M %":   round((ultimo / hace_3m - 1) * 100, 2) if hace_3m is not None else None,
            "Cambio 1A %":   round((ultimo / hace_1y - 1) * 100, 2) if hace_1y is not None else None,
            "Mín 52 sem":    round(min_52w, 2),
            "Máx 52 sem":    round(max_52w, 2),
            "% vs Mín 52s":  round((ultimo / min_52w - 1) * 100, 2),
            "% vs Máx 52s":  round((ultimo / max_52w - 1) * 100, 2),
            "Vol Prom 20d":  round(df["Volume"].tail(20).mean()) if "Volume" in df.columns else None,
            "Fecha Dato":    close.index[-1].strftime("%Y-%m-%d"),
        }
        filas.append(fila)

    if not filas:
        return pd.DataFrame()
    return pd.DataFrame(filas).sort_values("Cambio Día %", ascending=False)


# ─── ESTILOS EXCEL ────────────────────────────────────────────────

def aplicar_estilo(writer, sheet_name: str, df: pd.DataFrame,
                   freeze_row: bool = True, color_header: str = "1F4E79"):
    ws = writer.sheets[sheet_name]
    workbook = writer.book

    header_fmt = workbook.add_format({
        "bold": True, "font_color": "FFFFFF",
        "bg_color": color_header, "border": 1,
        "align": "center", "valign": "vcenter", "font_size": 10
    })
    num_fmt   = workbook.add_format({"num_format": "#,##0.00", "font_size": 9})
    pct_fmt   = workbook.add_format({"num_format": "#,##0.00%", "font_size": 9})
    int_fmt   = workbook.add_format({"num_format": "#,##0", "font_size": 9})
    date_fmt  = workbook.add_format({"num_format": "dd/mm/yyyy", "font_size": 9})
    pos_fmt   = workbook.add_format({"font_color": "006100", "bg_color": "C6EFCE",
                                     "num_format": "#,##0.00", "font_size": 9})
    neg_fmt   = workbook.add_format({"font_color": "9C0006", "bg_color": "FFC7CE",
                                     "num_format": "#,##0.00", "font_size": 9})

    # Ancho automático de columnas
    for col_num, col_name in enumerate(df.columns):
        ancho = max(len(str(col_name)) + 2, 10)
        ws.set_column(col_num, col_num, ancho)

    # Header
    for col_num, col_name in enumerate(df.columns):
        ws.write(0, col_num, col_name, header_fmt)

    if freeze_row:
        ws.freeze_panes(1, 0)

    ws.autofilter(0, 0, len(df), len(df.columns) - 1)


# ─── MAIN ─────────────────────────────────────────────────────────

INDICES_DICT = {
    "^GSPC": "SP500", "^IXIC": "NASDAQ_COMP", "^DJI": "DOW_JONES"
}
COMMODITIES_DICT = {
    "GC=F": "Oro", "CL=F": "Petroleo_WTI", "BZ=F": "Petroleo_Brent",
    "SI=F": "Plata", "HG=F": "Cobre", "PL=F": "Platino", "BTC-USD": "Bitcoin"
}
TASAS_DICT = {
    "^IRX": "UST_3M", "^FVX": "UST_5Y", "^TNX": "UST_10Y",
    "^TYX": "UST_30Y", "SHY": "UST_2Y_ETF", "IEF": "UST_7_10Y_ETF",
    "TLT": "UST_20_30Y_ETF"
}
MONEDAS_DICT = {
    "EURUSD=X": "EUR_USD", "GBPUSD=X": "GBP_USD", "JPY=X": "USD_JPY",
    "CNY=X": "USD_CNY", "AUDUSD=X": "AUD_USD", "CLP=X": "USD_CLP",
    "DX-Y.NYB": "DXY_Dollar_Index"
}

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  GENERANDO EXCEL: TRADING_DATA.xlsx")
    print("="*55)

    with pd.ExcelWriter(OUTPUT, engine="xlsxwriter",
                        datetime_format="dd/mm/yyyy",
                        date_format="dd/mm/yyyy") as writer:

        # ── 1. RESUMEN MACRO ───────────────────────────────────────
        print("\n[1/10] Resumen Macro...")
        bloques = {
            "ÍNDICES":      (os.path.join(DATA_DIR, "indices"),     INDICES_DICT),
            "COMMODITIES":  (os.path.join(DATA_DIR, "commodities"), COMMODITIES_DICT),
            "TASAS UST":    (os.path.join(DATA_DIR, "rates"),       TASAS_DICT),
            "MONEDAS":      (os.path.join(DATA_DIR, "currencies"),  MONEDAS_DICT),
        }
        filas_macro = []
        for bloque, (carpeta, nombres) in bloques.items():
            for ticker, nombre in nombres.items():
                ruta = os.path.join(carpeta, f"{nombre}.csv")
                df   = leer_csv(ruta)
                if df.empty or "Close" not in df.columns:
                    continue
                close = df["Close"].dropna()
                if len(close) < 2:
                    continue
                ultimo   = close.iloc[-1]
                anterior = close.iloc[-2]
                hace_1m  = close.iloc[-22] if len(close) >= 22 else None
                hace_1y  = close.iloc[-252] if len(close) >= 252 else None
                filas_macro.append({
                    "Categoría":     bloque,
                    "Activo":        nombre.replace("_", " "),
                    "Ticker":        ticker,
                    "Último Valor":  round(ultimo, 4),
                    "Cambio Día %":  round((ultimo / anterior - 1) * 100, 2) if anterior else None,
                    "Cambio 1M %":   round((ultimo / hace_1m - 1) * 100, 2) if hace_1m else None,
                    "Cambio 1A %":   round((ultimo / hace_1y - 1) * 100, 2) if hace_1y else None,
                    "Fecha":         close.index[-1].strftime("%Y-%m-%d"),
                })
        df_macro = pd.DataFrame(filas_macro)
        df_macro.to_excel(writer, sheet_name="Resumen Macro", index=False)
        aplicar_estilo(writer, "Resumen Macro", df_macro, color_header="1F4E79")

        # ── 2-4. ÍNDICES HISTÓRICO ─────────────────────────────────
        for nombre_hoja, nombre_arch in [("SP500 Histórico", "SP500"),
                                          ("Nasdaq Histórico", "NASDAQ_COMP"),
                                          ("Dow Jones Histórico", "DOW_JONES")]:
            print(f"\n[{'2' if 'SP' in nombre_hoja else '3' if 'Nasdaq' in nombre_hoja else '4'}/10] {nombre_hoja}...")
            ruta = os.path.join(DATA_DIR, "indices", f"{nombre_arch}.csv")
            df   = leer_csv(ruta)
            if not df.empty:
                df.index.name = "Fecha"
                df.to_excel(writer, sheet_name=nombre_hoja)
                aplicar_estilo(writer, nombre_hoja, df.reset_index(), color_header="2E7D32")

        # ── 5. COMMODITIES HISTÓRICO ───────────────────────────────
        print("\n[5/10] Commodities histórico...")
        df_comm = cargar_carpeta(os.path.join(DATA_DIR, "commodities"), COMMODITIES_DICT)
        if not df_comm.empty:
            df_comm.index.name = "Fecha"
            df_comm.to_excel(writer, sheet_name="Commodities")
            aplicar_estilo(writer, "Commodities", df_comm.reset_index(), color_header="6A1B9A")

        # ── 6. TASAS UST HISTÓRICO ─────────────────────────────────
        print("\n[6/10] Tasas UST histórico...")
        df_rates = cargar_carpeta(os.path.join(DATA_DIR, "rates"), TASAS_DICT)
        if not df_rates.empty:
            df_rates.index.name = "Fecha"
            df_rates.to_excel(writer, sheet_name="Tasas UST")
            aplicar_estilo(writer, "Tasas UST", df_rates.reset_index(), color_header="BF360C")

        # ── 7. MONEDAS HISTÓRICO ───────────────────────────────────
        print("\n[7/10] Monedas histórico...")
        df_fx = cargar_carpeta(os.path.join(DATA_DIR, "currencies"), MONEDAS_DICT)
        if not df_fx.empty:
            df_fx.index.name = "Fecha"
            df_fx.to_excel(writer, sheet_name="Monedas")
            aplicar_estilo(writer, "Monedas", df_fx.reset_index(), color_header="00695C")

        # ── 8. SP500 EMPRESAS ──────────────────────────────────────
        print("\n[8/10] SP500 Empresas (resumen)...")
        df_sp = resumen_empresas(
            os.path.join(DATA_DIR, "raw", "sp500"), "_lista_SP500.csv"
        )
        if not df_sp.empty:
            df_sp.to_excel(writer, sheet_name="SP500 Empresas", index=False)
            aplicar_estilo(writer, "SP500 Empresas", df_sp, color_header="1565C0")

        # ── 9. NASDAQ100 EMPRESAS ──────────────────────────────────
        print("\n[9/10] Nasdaq100 Empresas (resumen)...")
        df_nq = resumen_empresas(
            os.path.join(DATA_DIR, "raw", "nasdaq100"), "_lista_NASDAQ100.csv"
        )
        if not df_nq.empty:
            df_nq.to_excel(writer, sheet_name="Nasdaq100 Empresas", index=False)
            aplicar_estilo(writer, "Nasdaq100 Empresas", df_nq, color_header="1565C0")

        # ── 10. DOW30 EMPRESAS ─────────────────────────────────────
        print("\n[10/10] Dow30 Empresas (resumen)...")
        df_dw = resumen_empresas(
            os.path.join(DATA_DIR, "raw", "dow30"), "_lista_DOW30.csv"
        )
        if not df_dw.empty:
            df_dw.to_excel(writer, sheet_name="Dow30 Empresas", index=False)
            aplicar_estilo(writer, "Dow30 Empresas", df_dw, color_header="1565C0")

    print(f"\n{'='*55}")
    print(f"  EXCEL GENERADO EXITOSAMENTE")
    print(f"  Archivo: {OUTPUT}")
    print(f"{'='*55}\n")
