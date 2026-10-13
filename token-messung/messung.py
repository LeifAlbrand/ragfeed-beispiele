"""Token-Messung: Wie viele Tokens kostet eine Webseite ein Sprachmodell?

Ruft 20 öffentliche Seiten über eine Firecrawl-kompatible API ab und zählt mit tiktoken (o200k_base) die Tokens von
    1. rohem HTML,
    2. der ganzen Seite als Text (Markdown mit Menüs und Fußzeile, onlyMainContent=false),
    3. dem Hauptinhalt als Markdown (onlyMainContent=true, Standard),
    4. llmMarkdown (nur bei Ragfeed; mit --ohne-llm weggelassen).
Ausgewertet wird der Median der Ersparnis je Seite, damit wenige riesige Portalseiten das Ergebnis nicht bestimmen.

    pip install -r requirements.txt
    set RAGFEED_API_KEY=sk-...            (PowerShell: $env:RAGFEED_API_KEY="sk-...")
    python messung.py

Andere Firecrawl-kompatible API vergleichen:  python messung.py --api https://... --key ... --ohne-llm
Kosten bei Ragfeed: 2 Credits je Seite, also 40 Credits für alle 20 Seiten (kostenloser Plan: 1.000 im Monat).
Seiten ändern sich: Ein neuer Lauf liefert etwas andere Zahlen als die Momentaufnahme in ergebnis_2026-10-01.json.
"""
import argparse
import json
import os
import statistics
import sys
from datetime import date

import httpx
import tiktoken

START, ARTIKEL = "Startseite", "Artikel"
SEITEN = {
    "https://de.wikipedia.org/wiki/Big_Data": ("Wikipedia: Big Data", ARTIKEL),
    "https://www.gesetze-im-internet.de/urhg/__44b.html": ("Gesetzestext: § 44b UrhG", ARTIKEL),
    "https://developer.mozilla.org/de/docs/Web/HTML": ("MDN-Doku: HTML", ARTIKEL),
    "https://www.umweltbundesamt.de/themen/klima-energie/klimawandel": ("Umweltbundesamt: Klimawandel", ARTIKEL),
    "https://www.tagesschau.de/wirtschaft/": ("tagesschau.de: Wirtschaft", START),
    "https://www.heise.de/": ("heise online: Startseite", START),
    "https://www.siemens.com/de/de.html": ("Siemens: Startseite", START),
    "https://www.dhl.de/de/privatkunden.html": ("DHL: Privatkunden", START),
    "https://www.chefkoch.de/": ("Chefkoch: Startseite", START),
    "https://www.verbraucherzentrale.de/": ("Verbraucherzentrale: Startseite", START),
    "https://www.tagesschau.de/wirtschaft/verbraucher/september-tanken-100.html": ("tagesschau.de: Artikel Tanken", ARTIKEL),
    "https://www.heise.de/news/Tapete-produziert-Strom-mit-Luftfeuchtigkeit-11470666.html": ("heise online: Meldung", ARTIKEL),
    "https://www.verbraucherzentrale.de/wissen/lebensmittel/ernaehrung-fuer-seniorinnen/ernaehrungsberatung-gesucht-so-finden-sie-qualifizierte-hilfe-17735":
        ("Verbraucherzentrale: Ratgeber", ARTIKEL),
    "https://www.chefkoch.de/rezepte/3292561488882374/Preiswerter-einfacher-und-schneller-Bratreis.html": ("Chefkoch: Rezept", ARTIKEL),
    "https://www.umweltbundesamt.de/themen/klima-energie/treibhausgas-emissionen": ("Umweltbundesamt: Treibhausgase", ARTIKEL),
    "https://www.dhl.de/de/privatkunden/pakete-versenden/online-frankieren.html": ("DHL: Online frankieren", ARTIKEL),
    "https://www.t-online.de/heim-garten/aktuelles/id_101097404/waermepumpe-foerderung-neue-grenzwerte-stoppen-zuschuss-vieler-modelle.html":
        ("t-online: Artikel Wärmepumpe", ARTIKEL),
    "https://www.n-tv.de/energieeffizienz/waermepumpe/waermepumpe-kosten-foerderung": ("n-tv: Ratgeber Wärmepumpe", ARTIKEL),
    "https://www.nord24.de/verbraucher/waermepumpe-foerderung-2026-wer-bis-zu-22400-euro-zuschuss-bekommt-414932.html":
        ("nord24: Artikel Wärmepumpe", ARTIKEL),
    "https://www.msn.com/de-de/finanzen/top-stories/w%C3%A4rmepumpe-f%C3%B6rderung-2026-zusch%C3%BCsse-kredite-und-steuerbonus/ar-AA1YIWmf":
        ("MSN: Artikel Wärmepumpe", ARTIKEL),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--api", default="https://api.ragfeed.de", help="Basis-Adresse einer Firecrawl-kompatiblen API")
    ap.add_argument("--key", default=os.environ.get("RAGFEED_API_KEY"), help="API-Schlüssel (sonst RAGFEED_API_KEY)")
    ap.add_argument("--ohne-llm", action="store_true", help="llmMarkdown nicht anfordern (für andere APIs)")
    ap.add_argument("--aus", default=f"ergebnis_{date.today().isoformat()}.json", help="Ergebnisdatei")
    args = ap.parse_args()
    if not args.key:
        sys.exit("Kein API-Schlüssel: --key angeben oder RAGFEED_API_KEY setzen.")

    enc = tiktoken.get_encoding("o200k_base")
    tokens = lambda text: len(enc.encode(text or "", disallowed_special=()))
    client = httpx.Client(base_url=args.api.rstrip("/"), headers={"Authorization": f"Bearer {args.key}"}, timeout=120)

    def scrape(url: str, **body) -> dict:
        r = client.post("/v2/scrape", json={"url": url, "maxAge": 0, **body})
        r.raise_for_status()
        return r.json()["data"]

    formate = ["rawHtml", "markdown"] + ([] if args.ohne_llm else ["llmMarkdown"])
    seiten = []
    for url, (name, art) in SEITEN.items():
        try:
            d = scrape(url, formats=formate)
            ganz = scrape(url, onlyMainContent=False, formats=["markdown"])
        except httpx.HTTPError as e:
            print(f"übersprungen: {name} ({e})")
            continue
        zeile = {"name": name, "art": art, "url": url, "html": tokens(d.get("rawHtml")),
                 "ganzeSeite": tokens(ganz.get("markdown")), "hauptinhalt": tokens(d.get("markdown"))}
        if not args.ohne_llm:
            zeile["llmMarkdown"] = tokens(d.get("llmMarkdown"))
        seiten.append(zeile)
        print(json.dumps(zeile, ensure_ascii=False))
    if not seiten:
        sys.exit("Keine Seite abgerufen.")

    ziel = "hauptinhalt" if args.ohne_llm else "llmMarkdown"

    def median_ersparnis(a: str, b: str, zeilen: list) -> float:
        return round(100 * statistics.median(1 - z[a] / z[b] for z in zeilen if z[b]), 1)

    zusammenfassung = {"seiten": len(seiten), "verglichen": ziel}
    for name, zeilen in (("alle", seiten), ("startseiten", [z for z in seiten if z["art"] == START]),
                         ("artikel", [z for z in seiten if z["art"] == ARTIKEL])):
        if zeilen:
            zusammenfassung[name] = {"gegenHtml": median_ersparnis(ziel, "html", zeilen),
                                     "gegenGanzeSeite": median_ersparnis(ziel, "ganzeSeite", zeilen)}
    zusammenfassung["hauptinhaltGegenGanzeSeite"] = median_ersparnis("hauptinhalt", "ganzeSeite", seiten)
    gegen_ganz = [100 * (1 - z[ziel] / z["ganzeSeite"]) for z in seiten if z["ganzeSeite"]]
    zusammenfassung["spanneGegenGanzeSeite"] = [round(min(gegen_ganz), 1), round(max(gegen_ganz), 1)]

    ergebnis = {"datum": date.today().isoformat(), "api": args.api, "tokenizer": "o200k_base (tiktoken)",
                "zusammenfassung": zusammenfassung, "seiten": seiten}
    with open(args.aus, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ergebnis, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(zusammenfassung, ensure_ascii=False, indent=1))
    print("->", args.aus)


if __name__ == "__main__":
    main()
