"""
EXCEL DE BALANCES TRIMESTRALES — UNA HOJA POR EMPRESA
Genera 3 archivos (uno por índice):
  data/BALANCES_SP500.xlsx
  data/BALANCES_NASDAQ100.xlsx
  data/BALANCES_DOW30.xlsx

Cada hoja = IS + BS + CF apilados con encabezado de sección
"""

import os
import pandas as pd
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FIN_DIR  = os.path.join(DATA_DIR, "financials")


def leer_estado(ticker: str, tipo: str) -> pd.DataFrame:
    ruta = os.path.join(FIN_DIR, f"{ticker}_{tipo}.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ruta, index_col=0)
        df.index.name = "Trimestre"
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def escribir_hoja_balance(writer, ticker: str):
    """Escribe IS + BS + CF en una misma hoja, apilados."""
    wb  = writer.book
    nombre_hoja = ticker[:31]
    ws  = wb.add_worksheet(nombre_hoja)
    writer.sheets[nombre_hoja] = ws

    # Formatos
    fmt_titulo = wb.add_format({
        "bold": True, "font_size": 12,
        "bg_color": "1F4E79", "font_color": "FFFFFF",
        "border": 1
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
        ("income",   "INCOME STATEMENT (Estado de Resultados)"),
        ("balance",  "BALANCE SHEET (Balance General)"),
        ("cashflow", "CASH FLOW STATEMENT (Flujo de Caja)"),
    ]

    fila = 0
    tiene_datos = False

    for tipo, label in estados:
        df = leer_estado(ticker, tipo)
        if df.empty:
            continue

        tiene_datos = True
        # Título de sección
        ws.merge_range(fila, 0, fila, len(df.columns), f"  {label}  —  {ticker}", fmt_titulo)
        fila += 1

        # Headers (trimestres)
        ws.write(fila, 0, "Métrica", fmt_header)
        ws.set_column(0, 0, 45)
        for j, col in enumerate(df.columns):
            ws.write(fila, j + 1, str(col)[:20], fmt_header)
            ws.set_column(j + 1, j + 1, 18)
        fila += 1

        # Filas de datos
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

        fila += 2  # separación entre estados

    return tiene_datos


def generar_excel_balances(nombre_indice: str, carpeta_raw: str, output: str):
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
        # Hoja resumen primero
        filas_resumen = []
        for ticker in tickers:
            for tipo in ["income", "balance", "cashflow"]:
                ruta = os.path.join(FIN_DIR, f"{ticker}_{tipo}.csv")
                filas_resumen.append({
                    "Ticker": ticker,
                    "Estado": tipo.upper(),
                    "Disponible": "SÍ" if os.path.exists(ruta) else "NO",
                    "Trimestres": len(pd.read_csv(ruta, index_col=0).columns)
                              if os.path.exists(ruta) else 0,
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


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  GENERANDO EXCELS DE BALANCES POR EMPRESA")
    print("="*55)

    generar_excel_balances(
        "SP500",
        os.path.join(DATA_DIR, "raw", "sp500"),
        os.path.join(DATA_DIR, "BALANCES_SP500.xlsx")
    )
    generar_excel_balances(
        "NASDAQ100",
        os.path.join(DATA_DIR, "raw", "nasdaq100"),
        os.path.join(DATA_DIR, "BALANCES_NASDAQ100.xlsx")
    )
    generar_excel_balances(
        "DOW30",
        os.path.join(DATA_DIR, "raw", "dow30"),
        os.path.join(DATA_DIR, "BALANCES_DOW30.xlsx")
    )

    print(f"\n{'='*55}")
    print("  EXCELS DE BALANCES COMPLETADOS")
    print(f"{'='*55}\n")
