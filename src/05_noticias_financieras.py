"""
AGREGADOR DE NOTICIAS FINANCIERAS INTERNACIONALES
50 fuentes: Bloomberg, Reuters, FT, WSJ, CNBC, Seeking Alpha, etc.

Guarda en: data/noticias/noticias_YYYY-MM-DD.csv
           data/noticias/noticias_hoy.csv  (siempre la del día)
"""

import feedparser
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import hashlib

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data", "noticias")
os.makedirs(DATA_DIR, exist_ok=True)

# ─── 50 FUENTES RSS FINANCIERAS INTERNACIONALES ───────────────────
FUENTES = {
    # ── AGENCIAS GLOBALES ──────────────────────────────────────────
    "Reuters - Markets":        "https://feeds.reuters.com/reuters/businessNews",
    "Reuters - Economy":        "https://feeds.reuters.com/news/economy",
    "Reuters - Stocks":         "https://feeds.reuters.com/reuters/companyNews",
    "AP - Business":            "https://feeds.apnews.com/rss/business",
    "AFP - Economy":            "https://www.afp.com/en/afpcom/rss",

    # ── MEDIOS FINANCIEROS USA ─────────────────────────────────────
    "CNBC - Markets":           "https://feeds.nbcnews.com/nbcnews/public/business",
    "CNBC - Economy":           "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "CNBC - Finance":           "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "MarketWatch - Top":        "https://feeds.marketwatch.com/marketwatch/topstories/",
    "MarketWatch - Markets":    "https://feeds.marketwatch.com/marketwatch/marketpulse/",
    "Investopedia":             "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline",
    "Barron's":                 "https://www.barrons.com/xml/rss/3_7167.xml",
    "Kiplinger":                "https://www.kiplinger.com/feeds/rss/investing.rss",
    "TheStreet":                "https://www.thestreet.com/rss/index.xml",
    "Motley Fool":              "https://www.fool.com/feeds/index.aspx",

    # ── BLOOMBERG (vía proxy RSS) ──────────────────────────────────
    "Bloomberg - Markets":      "https://feeds.bloomberg.com/markets/news.rss",
    "Bloomberg - Economy":      "https://feeds.bloomberg.com/economics/news.rss",
    "Bloomberg - Technology":   "https://feeds.bloomberg.com/technology/news.rss",

    # ── FINANCIAL TIMES ───────────────────────────────────────────
    "FT - Markets":             "https://www.ft.com/markets?format=rss",
    "FT - Companies":           "https://www.ft.com/companies?format=rss",
    "FT - Economy":             "https://www.ft.com/global-economy?format=rss",

    # ── WALL STREET JOURNAL ───────────────────────────────────────
    "WSJ - Markets":            "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "WSJ - Economy":            "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "WSJ - Business":           "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",

    # ── ANÁLISIS / RESEARCH ───────────────────────────────────────
    "Seeking Alpha - Wall St":  "https://seekingalpha.com/market_currents.xml",
    "Seeking Alpha - News":     "https://seekingalpha.com/feed.xml",
    "Zero Hedge":               "https://feeds.feedburner.com/zerohedge/feed",
    "Business Insider":         "https://feeds.businessinsider.com/custom/all",

    # ── CRYPTO / DIGITAL ASSETS ───────────────────────────────────
    "CoinDesk":                 "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "CoinTelegraph":            "https://cointelegraph.com/rss",
    "CryptoSlate":              "https://cryptoslate.com/feed/",
    "Decrypt":                  "https://decrypt.co/feed",
    "Bitcoin Magazine":         "https://bitcoinmagazine.com/feed",

    # ── COMMODITIES / ENERGÍA ─────────────────────────────────────
    "OilPrice.com":             "https://oilprice.com/rss/main",
    "Platts - Commodities":     "https://www.spglobal.com/commodityinsights/en/rss-feed/oil",
    "Mining.com":               "https://www.mining.com/feed/",
    "Kitco - Metales":          "https://www.kitco.com/rss/kitco-news.rss",

    # ── LATINOAMÉRICA ─────────────────────────────────────────────
    "El Economista MX":         "https://www.eleconomista.com.mx/rss/mercados_financieros.xml",
    "Infobae - Economía":       "https://www.infobae.com/feeds/rss/economia/",
    "El Mercurio - Negocios":   "https://www.emol.com/rss/_economia.xml",
    "DF - Diario Financiero":   "https://www.df.cl/noticias/rss.xml",
    "Portafolio CO":            "https://www.portafolio.co/rss/portafolio.xml",

    # ── EUROPA / ASIA ─────────────────────────────────────────────
    "ECB - Press Releases":     "https://www.ecb.europa.eu/rss/press.html",
    "Nikkei Asia":              "https://asia.nikkei.com/rss/feed/nar",
    "South China Morning Post": "https://www.scmp.com/rss/5/feed",
    "The Economist - Finance":  "https://www.economist.com/finance-and-economics/rss.xml",
    "Guardian - Business":      "https://www.theguardian.com/business/rss",

    # ── MACRO / BANCOS CENTRALES ──────────────────────────────────
    "Fed Reserve - News":       "https://www.federalreserve.gov/feeds/press_all.xml",
    "IMF - News":               "https://www.imf.org/en/News/rss?language=eng",
    "World Bank - News":        "https://feeds.worldbank.org/worldbank/news",
    "BIS - News":               "https://www.bis.org/rss/press.rss",
}

# Categorías para filtrar
KEYWORDS_RELEVANTES = [
    "fed", "interest rate", "inflation", "gdp", "recession", "earnings",
    "s&p", "nasdaq", "dow", "bitcoin", "crypto", "gold", "oil", "lithium",
    "litio", "copper", "silver", "treasury", "bond", "yield", "dollar",
    "rate hike", "powell", "ecb", "banco central", "mercado", "bolsa",
    "acciones", "commodities", "petróleo", "chile", "latam",
]


def limpiar_texto(texto: str) -> str:
    if not texto:
        return ""
    import re
    texto = re.sub(r"<[^>]+>", "", texto)   # quitar HTML
    return texto.strip()[:500]              # máx 500 chars


def es_relevante(titulo: str, resumen: str) -> bool:
    """Filtra noticias con keywords financieras."""
    texto = (titulo + " " + resumen).lower()
    return any(kw in texto for kw in KEYWORDS_RELEVANTES)


def scrape_fuente(nombre: str, url: str) -> list:
    """Parsea un feed RSS y retorna lista de noticias."""
    try:
        feed = feedparser.parse(url)
        noticias = []
        for entry in feed.entries[:15]:   # máx 15 por fuente
            titulo  = limpiar_texto(entry.get("title", ""))
            resumen = limpiar_texto(entry.get("summary", entry.get("description", "")))
            link    = entry.get("link", "")

            # Fecha
            fecha_raw = entry.get("published_parsed") or entry.get("updated_parsed")
            if fecha_raw:
                try:
                    fecha = datetime(*fecha_raw[:6]).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
            else:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

            if titulo:
                noticias.append({
                    "Fecha":    fecha,
                    "Fuente":   nombre,
                    "Título":   titulo,
                    "Resumen":  resumen,
                    "URL":      link,
                    "Relevante": "SÍ" if es_relevante(titulo, resumen) else "NO",
                    "ID":       hashlib.md5(link.encode()).hexdigest()[:8],
                })
        return noticias
    except Exception as e:
        return []


def descargar_noticias(solo_relevantes: bool = False) -> pd.DataFrame:
    """Descarga noticias de todas las fuentes."""
    print(f"\n{'='*55}")
    print(f"  DESCARGANDO NOTICIAS - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  Fuentes: {len(FUENTES)}")
    print(f"{'='*55}")

    todas = []
    ok = err = 0

    for nombre, url in FUENTES.items():
        noticias = scrape_fuente(nombre, url)
        if noticias:
            todas.extend(noticias)
            ok += 1
        else:
            err += 1
        time.sleep(0.3)

    print(f"\n  ✓ Fuentes OK: {ok}  |  Con error: {err}")
    print(f"  ✓ Total noticias: {len(todas)}")

    if not todas:
        return pd.DataFrame()

    df = pd.DataFrame(todas)
    df = df.drop_duplicates(subset=["ID"])
    df = df.sort_values("Fecha", ascending=False)

    if solo_relevantes:
        df = df[df["Relevante"] == "SÍ"]

    print(f"  ✓ Únicas: {len(df)}  |  Relevantes: {len(df[df['Relevante']=='SÍ'])}")
    return df


def guardar_noticias(df: pd.DataFrame):
    """Guarda CSV del día y sobreescribe noticias_hoy.csv"""
    if df.empty:
        return
    hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_dia  = os.path.join(DATA_DIR, f"noticias_{hoy}.csv")
    ruta_hoy  = os.path.join(DATA_DIR, "noticias_hoy.csv")
    df.to_csv(ruta_dia, index=False, encoding="utf-8-sig")
    df.to_csv(ruta_hoy, index=False, encoding="utf-8-sig")
    print(f"\n  Guardado en: {ruta_dia}")


def exportar_excel_noticias(df: pd.DataFrame):
    """Exporta noticias a Excel con formato."""
    if df.empty:
        return
    hoy   = datetime.now().strftime("%Y-%m-%d")
    ruta  = os.path.join(DATA_DIR, f"noticias_{hoy}.xlsx")

    with pd.ExcelWriter(ruta, engine="xlsxwriter") as writer:
        # Hoja 1: Todas
        df.drop(columns=["ID"]).to_excel(writer, sheet_name="Todas las noticias", index=False)

        # Hoja 2: Solo relevantes
        df_rel = df[df["Relevante"] == "SÍ"].drop(columns=["ID"])
        df_rel.to_excel(writer, sheet_name="Noticias Relevantes", index=False)

        # Hoja 3: Por fuente
        df_res = df.groupby("Fuente").agg(
            Total=("Título", "count"),
            Relevantes=("Relevante", lambda x: (x == "SÍ").sum()),
            Última=("Fecha", "max")
        ).reset_index().sort_values("Relevantes", ascending=False)
        df_res.to_excel(writer, sheet_name="Resumen por Fuente", index=False)

        wb = writer.book
        hdr = wb.add_format({"bold": True, "bg_color": "1F4E79",
                              "font_color": "FFFFFF", "border": 1})
        for sheet in writer.sheets.values():
            sheet.freeze_panes(1, 0)
            sheet.set_column(0, 0, 18)   # Fecha
            sheet.set_column(1, 1, 22)   # Fuente
            sheet.set_column(2, 2, 60)   # Título
            sheet.set_column(3, 3, 80)   # Resumen
            sheet.set_column(4, 4, 50)   # URL

    print(f"  Excel: {ruta}")


if __name__ == "__main__":
    df = descargar_noticias(solo_relevantes=False)
    guardar_noticias(df)
    exportar_excel_noticias(df)
    print(f"\n{'='*55}\n  NOTICIAS DESCARGADAS\n{'='*55}\n")
