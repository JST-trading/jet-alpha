"""
EXCEL DE PRECIOS HISTÓRICOS — UNA HOJA POR EMPRESA
Genera 3 archivos (uno por índice):
  data/PRECIOS_SP500.xlsx
  data/PRECIOS_NASDAQ100.xlsx
  data/PRECIOS_DOW30.xlsx

Cada hoja = ticker, columnas OHLCV 5 años
"""

import os
import pandas as pd
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def leer_precio(ruta: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(ruta, skiprows=[1, 2], index_col=0, parse_dates=True)
        df.index.name = "Fecha"
        df = df[pd.to_datetime(df.index, errors="coerce").notna()]
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.round(4)
    except Exception:
        return pd.DataFrame()


def header_fmt(wb):
    return wb.add_format({
        "bold": True, "font_color": "FFFFFF",
        "bg_color": "1F4E79", "border": 1,
        "align": "center", "font_size": 10
    })


def escribir_hoja(writer, ticker: str, df: pd.DataFrame):
    nombre_hoja = ticker[:31]   # Excel límite 31 chars
    df.reset_index().to_excel(writer, sheet_name=nombre_hoja, index=False)
    ws = writer.sheets[nombre_hoja]
    wb = writer.book
    fmt = header_fmt(wb)
    cols = ["Fecha"] + list(df.columns)
    for i, col in enumerate(cols):
        ws.set_column(i, i, 14)
        ws.write(0, i, col, fmt)
    ws.freeze_panes(1, 0)


def generar_excel_indice(nombre_indice: str, carpeta_raw: str, output: str):
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
        for ticker in tqdm(tickers, desc=f"  {nombre_indice}"):
            ruta = os.path.join(carpeta_raw, f"{ticker}.csv")
            df = leer_precio(ruta)
            if df.empty:
                sin_datos += 1
                continue
            escribir_hoja(writer, ticker, df)
            ok += 1

    print(f"  ✓ Hojas escritas: {ok}  |  Sin datos: {sin_datos}")
    size = os.path.getsize(output) / 1e6
    print(f"  ✓ Archivo: {output} ({size:.1f} MB)")


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  GENERANDO EXCELS DE PRECIOS POR EMPRESA")
    print("="*55)

    generar_excel_indice(
        "SP500",
        os.path.join(DATA_DIR, "raw", "sp500"),
        os.path.join(DATA_DIR, "PRECIOS_SP500.xlsx")
    )
    generar_excel_indice(
        "NASDAQ100",
        os.path.join(DATA_DIR, "raw", "nasdaq100"),
        os.path.join(DATA_DIR, "PRECIOS_NASDAQ100.xlsx")
    )
    generar_excel_indice(
        "DOW30",
        os.path.join(DATA_DIR, "raw", "dow30"),
        os.path.join(DATA_DIR, "PRECIOS_DOW30.xlsx")
    )

    print(f"\n{'='*55}")
    print("  EXCELS DE PRECIOS COMPLETADOS")
    print(f"{'='*55}\n")
