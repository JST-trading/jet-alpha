"""
SOCIAL MEDIA & PODCASTS AGGREGATOR — JST ALPHA
Fuentes:
  - Podcasts financieros (RSS)
  - Twitter/X via Nitter RSS (sin API de pago)
  - Reddit (API pública RSS)
  - YouTube canales financieros (RSS)

Guarda en: data/social/social_hoy.csv
           data/social/podcasts_hoy.csv
"""

import feedparser
import pandas as pd
import os
import time
import hashlib
from datetime import datetime
import requests

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data", "social")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

# ══════════════════════════════════════════════════════════════════
# PODCASTS FINANCIEROS
# ══════════════════════════════════════════════════════════════════
PODCASTS = {
    # ── MACRO / ECONOMÍA ──────────────────────────────────────────
    "The Indicator (NPR)":           "https://feeds.npr.org/510325/podcast.xml",
    "Planet Money (NPR)":            "https://feeds.npr.org/510289/podcast.xml",
    "Odd Lots (Bloomberg)":          "https://feeds.megaphone.fm/odd-lots",
    "Macro Voices":                  "https://www.macrovoices.com/podcast-feed/feed",
    "We Study Billionaires":         "https://feeds.simplecast.com/ni3s0yT1",
    "Chat With Traders":             "https://chatwithtraders.com/feed/podcast/",
    "Lex Fridman Podcast":           "https://lexfridman.com/feed/podcast/",
    "Masters in Business (BBG)":     "https://feeds.megaphone.fm/masters-in-business",

    # ── INVERSIONES / TRADING ─────────────────────────────────────
    "Invest Like the Best":          "https://feeds.megaphone.fm/investlikethebest",
    "The Meb Faber Show":            "https://mebfaber.com/feed/podcast/",
    "Animal Spirits":                "https://feeds.megaphone.fm/animal-spirits",
    "Acquired Podcast":              "https://acquired.fm/rss",
    "The Knowledge Project":         "https://feeds.simplecast.com/EFjOZVMq",
    "Hidden Forces":                 "https://hiddenforces.io/feed/",
    "Real Vision Finance":           "https://feeds.megaphone.fm/real-vision",
    "Motley Fool Money":             "https://feeds.megaphone.fm/foolmoney",

    # ── CRYPTO / BITCOIN ──────────────────────────────────────────
    "What Bitcoin Did":              "https://www.whatbitcoindid.com/podcast-feed.xml",
    "Bankless":                      "https://feeds.simplecast.com/bOBKMDpH",
    "The Pomp Podcast":              "https://feeds.simplecast.com/LwdHqh0f",
    "Unchained":                     "https://unchainedcrypto.com/feed/podcast/",
    "Crypto 101":                    "https://feeds.soundcloud.com/users/soundcloud:users:212693365/sounds.rss",

    # ── MERCADO USA / WALL STREET ─────────────────────────────────
    "CNBC Squawk Box":               "https://feeds.megaphone.fm/cnbc-squawk-box",
    "Bloomberg Surveillance":        "https://feeds.megaphone.fm/bloomberg-surveillance",
    "Goldman Sachs Exchanges":       "https://feeds.megaphone.fm/goldman-sachs-exchanges",
    "Morgan Stanley Ideas":          "https://feeds.megaphone.fm/morgan-stanley-ideas",
    "JPMorgan Making Sense":         "https://feeds.megaphone.fm/jpmorgan-chase",

    # ── LATAM ─────────────────────────────────────────────────────
    "Entiende Tu Dinero":            "https://entiendetordinero.com/feed/podcast/",
    "El Podcast de Finanzas":        "https://anchor.fm/s/finanzas-para-mortales/podcast/rss",
}

# ══════════════════════════════════════════════════════════════════
# TWITTER/X — VIA NITTER RSS (múltiples instancias fallback)
# ══════════════════════════════════════════════════════════════════

# Instancias Nitter públicas (fallback en orden)
NITTER_INSTANCES = [
    "https://nitter.privacyredirect.com",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
]

# Cuentas por categoría
TWITTER_CUENTAS = {
    # ── POLÍTICOS / GOBIERNO ──────────────────────────────────────
    "🏛 Políticos": [
        ("realDonaldTrump", "Donald Trump — POTUS"),
        ("POTUS",           "White House"),
        ("SecYellen",       "Janet Yellen — Ex Sec. Tesoro"),
        ("SecScottBessent", "Scott Bessent — Sec. Tesoro"),
        ("SenWarren",       "Elizabeth Warren — Senadora"),
    ],

    # ── BANCOS CENTRALES ──────────────────────────────────────────
    "🏦 Bancos Centrales": [
        ("federalreserve",   "Federal Reserve"),
        ("ECB",              "European Central Bank"),
        ("BIS_org",          "Bank for Int'l Settlements"),
        ("IMFNews",          "IMF"),
        ("WorldBank",        "World Bank"),
    ],

    # ── MEGAINVERSORES ────────────────────────────────────────────
    "💰 Inversores Top": [
        ("elonmusk",    "Elon Musk — Tesla/SpaceX/X"),
        ("CathieDWood", "Cathie Wood — ARK Invest"),
        ("chamath",     "Chamath Palihapitiya"),
        ("BillAckman",  "Bill Ackman — Pershing Square"),
        ("carlicahn",   "Carl Icahn"),
        ("naval",       "Naval Ravikant"),
        ("RayDalio",    "Ray Dalio — Bridgewater"),
    ],

    # ── EMPRESAS COTIZADAS ─────────────────────────────────────────
    "🏢 Grandes Empresas": [
        ("Apple",       "Apple Inc."),
        ("nvidia",      "NVIDIA"),
        ("Microsoft",   "Microsoft"),
        ("Meta",        "Meta Platforms"),
        ("Tesla",       "Tesla"),
        ("Amazon",      "Amazon"),
        ("Google",      "Google"),
        ("JPMorgan",    "JPMorgan Chase"),
        ("GoldmanSachs","Goldman Sachs"),
        ("BlackRock",   "BlackRock"),
    ],

    # ── ANALISTAS / MEDIOS FINANCIEROS ────────────────────────────
    "📊 Analistas & Media": [
        ("jimcramer",       "Jim Cramer — CNBC"),
        ("ZeroHedge",       "Zero Hedge"),
        ("ReutersBiz",      "Reuters Business"),
        ("markets",         "Bloomberg Markets"),
        ("WSJmarkets",      "WSJ Markets"),
        ("KobeissiLetter",  "The Kobeissi Letter"),
        ("MacroAlf",        "Alfonso Peccatiello — Macro"),
        ("LynAldenContact", "Lyn Alden — Macro"),
        ("PeterSchiff",     "Peter Schiff — Euro Pacific"),
        ("michael_saylor",  "Michael Saylor — MicroStrategy"),
    ],

    # ── CRYPTO ────────────────────────────────────────────────────
    "₿ Crypto": [
        ("VitalikButerin", "Vitalik Buterin — Ethereum"),
        ("cz_binance",     "CZ — Binance"),
        ("brian_armstrong", "Brian Armstrong — Coinbase"),
        ("WClementeIII",   "Will Clemente — On-chain"),
        ("glassnode",      "Glassnode Analytics"),
    ],
}

# ══════════════════════════════════════════════════════════════════
# REDDIT
# ══════════════════════════════════════════════════════════════════
SUBREDDITS = {
    "r/investing":           "https://www.reddit.com/r/investing/.rss",
    "r/wallstreetbets":      "https://www.reddit.com/r/wallstreetbets/.rss",
    "r/stocks":              "https://www.reddit.com/r/stocks/.rss",
    "r/economics":           "https://www.reddit.com/r/economics/.rss",
    "r/finance":             "https://www.reddit.com/r/finance/.rss",
    "r/options":             "https://www.reddit.com/r/options/.rss",
    "r/SecurityAnalysis":    "https://www.reddit.com/r/SecurityAnalysis/.rss",
    "r/algotrading":         "https://www.reddit.com/r/algotrading/.rss",
    "r/CryptoCurrency":      "https://www.reddit.com/r/CryptoCurrency/.rss",
    "r/Bitcoin":             "https://www.reddit.com/r/Bitcoin/.rss",
    "r/Superstonk":          "https://www.reddit.com/r/Superstonk/.rss",
    "r/quant":               "https://www.reddit.com/r/quant/.rss",
}

# ══════════════════════════════════════════════════════════════════
# YOUTUBE CANALES FINANCIEROS (vía RSS)
# ══════════════════════════════════════════════════════════════════
YOUTUBE_CANALES = {
    "Bloomberg Technology":   "https://www.youtube.com/feeds/videos.xml?channel_id=UCrM7B7SL_g1edFOnmj-SDKg",
    "Bloomberg Markets":      "https://www.youtube.com/feeds/videos.xml?channel_id=UCIALMKvObZNtJ6AmdCLP7Lg",
    "CNBC Television":        "https://www.youtube.com/feeds/videos.xml?channel_id=UCvJJ_dzjViJCoLf5uKUTwoA",
    "Reuters":                "https://www.youtube.com/feeds/videos.xml?channel_id=UCKy1dAqELo0zrOtPkf0eTMw",
    "Wall Street Journal":    "https://www.youtube.com/feeds/videos.xml?channel_id=UCK7tptUDHh-RYDsdxO1-5QQ",
    "Real Vision Finance":    "https://www.youtube.com/feeds/videos.xml?channel_id=UCBH5VZE_Y4F3CMcPIzPEB_A",
    "Andrei Jikh":            "https://www.youtube.com/feeds/videos.xml?channel_id=UCGy7SkBjcIAgTiwkXEtPnYg",
    "Graham Stephan":         "https://www.youtube.com/feeds/videos.xml?channel_id=UCV6KDgJskWaEckne5aPA0aQ",
    "Meet Kevin":             "https://www.youtube.com/feeds/videos.xml?channel_id=UCUvvj5kwbDNs-eLfx8DjHNQ",
    "Patrick Boyle":          "https://www.youtube.com/feeds/videos.xml?channel_id=UCASM3CTGF7KM4-qAkFAE0eg",
    "Joseph Carlson":         "https://www.youtube.com/feeds/videos.xml?channel_id=UCbmNph6atAoGfqLoCL_duAg",
    "Ben Felix":              "https://www.youtube.com/feeds/videos.xml?channel_id=UCDXTQ8nWmx_EhZ2v-kp7QxA",
    "Kitco News":             "https://www.youtube.com/feeds/videos.xml?channel_id=UCeGJHmAlTmQLy0EOFxW1T_g",
    "Coin Bureau":            "https://www.youtube.com/feeds/videos.xml?channel_id=UCqK_GSMbpiV8spgD3ZGloSw",
    "InvestAnswers":          "https://www.youtube.com/feeds/videos.xml?channel_id=UCqAgMCCMtMOwD5wrp-ATa8w",
}


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def parse_feed(url: str, max_items: int = 10) -> list:
    """Parsea un feed RSS y devuelve lista de items."""
    try:
        feed = feedparser.parse(url)
        items = []
        for e in feed.entries[:max_items]:
            fecha_raw = e.get("published_parsed") or e.get("updated_parsed")
            try:
                fecha = datetime(*fecha_raw[:6]).strftime("%Y-%m-%d %H:%M") if fecha_raw else datetime.now().strftime("%Y-%m-%d %H:%M")
            except Exception:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
            items.append({
                "titulo":  (e.get("title", "") or "")[:200],
                "resumen": (e.get("summary", e.get("description", "")) or "")[:300],
                "url":     e.get("link", ""),
                "fecha":   fecha,
                "id":      hashlib.md5((e.get("link", "") + e.get("title", "")).encode()).hexdigest()[:8],
            })
        return items
    except Exception:
        return []


def get_twitter_rss(usuario: str, nombre: str) -> list:
    """Intenta obtener tweets vía Nitter RSS con múltiples instancias."""
    for instancia in NITTER_INSTANCES:
        url = f"{instancia}/{usuario}/rss"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                items = []
                for e in feed.entries[:8]:
                    fecha_raw = e.get("published_parsed")
                    try:
                        fecha = datetime(*fecha_raw[:6]).strftime("%Y-%m-%d %H:%M") if fecha_raw else ""
                    except Exception:
                        fecha = ""
                    items.append({
                        "titulo":  (e.get("title", "") or "")[:280],
                        "resumen": "",
                        "url":     f"https://twitter.com/{usuario}",
                        "fecha":   fecha,
                        "id":      hashlib.md5((usuario + e.get("title", "")).encode()).hexdigest()[:8],
                    })
                if items:
                    return items
        except Exception:
            continue
    return []


# ══════════════════════════════════════════════════════════════════
# SCRAPERS PRINCIPALES
# ══════════════════════════════════════════════════════════════════

def scrape_podcasts() -> pd.DataFrame:
    print("\n[PODCASTS] Descargando episodios recientes...")
    filas = []
    ok = err = 0
    for nombre, url in PODCASTS.items():
        items = parse_feed(url, max_items=3)
        for item in items:
            filas.append({
                "Tipo":     "PODCAST",
                "Fuente":   nombre,
                "Categoría":"Podcasts",
                "Título":   item["titulo"],
                "Resumen":  item["resumen"],
                "URL":      item["url"],
                "Fecha":    item["fecha"],
                "ID":       item["id"],
            })
        if items: ok += 1
        else:     err += 1
        time.sleep(0.2)
    print(f"  ✓ OK: {ok}  |  Error: {err}  |  Episodios: {len(filas)}")
    return pd.DataFrame(filas)


def scrape_twitter() -> pd.DataFrame:
    print("\n[TWITTER/X] Scrapeando cuentas clave...")
    filas = []
    ok = err = 0
    for categoria, cuentas in TWITTER_CUENTAS.items():
        for usuario, nombre in cuentas:
            tweets = get_twitter_rss(usuario, nombre)
            for t in tweets:
                filas.append({
                    "Tipo":     "TWITTER",
                    "Fuente":   f"@{usuario} — {nombre}",
                    "Categoría": categoria,
                    "Título":   t["titulo"],
                    "Resumen":  "",
                    "URL":      t["url"],
                    "Fecha":    t["fecha"],
                    "ID":       t["id"],
                })
            if tweets: ok += 1
            else:      err += 1
            time.sleep(0.5)
    print(f"  ✓ Cuentas OK: {ok}  |  Sin datos: {err}  |  Tweets: {len(filas)}")
    return pd.DataFrame(filas)


def scrape_reddit() -> pd.DataFrame:
    print("\n[REDDIT] Descargando posts...")
    filas = []
    ok = err = 0
    reddit_headers = {**HEADERS, "Accept": "application/json"}
    for nombre, url in SUBREDDITS.items():
        items = parse_feed(url, max_items=10)
        for item in items:
            filas.append({
                "Tipo":     "REDDIT",
                "Fuente":   nombre,
                "Categoría":"Reddit",
                "Título":   item["titulo"],
                "Resumen":  item["resumen"],
                "URL":      item["url"],
                "Fecha":    item["fecha"],
                "ID":       item["id"],
            })
        if items: ok += 1
        else:     err += 1
        time.sleep(0.3)
    print(f"  ✓ Subreddits OK: {ok}  |  Error: {err}  |  Posts: {len(filas)}")
    return pd.DataFrame(filas)


def scrape_youtube() -> pd.DataFrame:
    print("\n[YOUTUBE] Descargando videos recientes...")
    filas = []
    ok = err = 0
    for nombre, url in YOUTUBE_CANALES.items():
        items = parse_feed(url, max_items=5)
        for item in items:
            filas.append({
                "Tipo":     "YOUTUBE",
                "Fuente":   nombre,
                "Categoría":"YouTube",
                "Título":   item["titulo"],
                "Resumen":  item["resumen"],
                "URL":      item["url"],
                "Fecha":    item["fecha"],
                "ID":       item["id"],
            })
        if items: ok += 1
        else:     err += 1
        time.sleep(0.2)
    print(f"  ✓ Canales OK: {ok}  |  Error: {err}  |  Videos: {len(filas)}")
    return pd.DataFrame(filas)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  JST ALPHA — SOCIAL MEDIA AGGREGATOR")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*55)

    dfs = []

    df_pods = scrape_podcasts()
    df_tw   = scrape_twitter()
    df_red  = scrape_reddit()
    df_yt   = scrape_youtube()

    for df in [df_pods, df_tw, df_red, df_yt]:
        if not df.empty:
            dfs.append(df)

    if not dfs:
        print("\n⚠ Sin datos")
    else:
        df_todo = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["ID"])
        df_todo = df_todo.sort_values("Fecha", ascending=False)

        # Guardar CSV
        hoy = datetime.now().strftime("%Y-%m-%d")
        df_todo.to_csv(os.path.join(DATA_DIR, f"social_{hoy}.csv"), index=False, encoding="utf-8-sig")
        df_todo.to_csv(os.path.join(DATA_DIR, "social_hoy.csv"), index=False, encoding="utf-8-sig")

        # Podcasts separado
        df_pods_out = df_todo[df_todo["Tipo"] == "PODCAST"]
        df_pods_out.to_csv(os.path.join(DATA_DIR, "podcasts_hoy.csv"), index=False, encoding="utf-8-sig")

        print(f"\n{'='*55}")
        print(f"  TOTAL: {len(df_todo)} items")
        print(f"  Podcasts: {len(df_pods_out)}")
        print(f"  Twitter:  {len(df_todo[df_todo['Tipo']=='TWITTER'])}")
        print(f"  Reddit:   {len(df_todo[df_todo['Tipo']=='REDDIT'])}")
        print(f"  YouTube:  {len(df_todo[df_todo['Tipo']=='YOUTUBE'])}")
        print(f"{'='*55}\n")
