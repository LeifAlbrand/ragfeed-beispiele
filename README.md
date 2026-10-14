# Ragfeed – Beispiele und Token-Messung

Kleine, nachprüfbare Beispiele für [Ragfeed](https://ragfeed.de), eine Firecrawl-kompatible Web-Daten-API aus Deutschland.

> Offenlegung: Dieses Repository gehört zu Ragfeed; ich habe Ragfeed gebaut und betreibe es (Leif Albrand, Einzelunternehmen, Deutschland).

## Inhalt

| Ordner | Was es zeigt |
|---|---|
| [`token-messung/`](token-messung) | Wie viele Tokens eine Webseite ein Sprachmodell kostet: rohes HTML, ganze Seite als Text, Hauptinhalt, llmMarkdown. Skript, Seitenliste und Ergebnis vom 01.10.2026. |
| [`firecrawl-py/`](firecrawl-py) | Bestehender Code mit dem offiziellen Python-SDK von Firecrawl, nur `api_url` und Schlüssel ausgetauscht; dazu die Ragfeed-Formate `llmMarkdown` und `chunks`. |
| [`n8n/`](n8n) | Zwei n8n-Workflows zum Importieren: der offizielle Firecrawl-Baustein mit Ragfeed (nur Base URL und Schlüssel ändern) und Webseite → Chunks für die Vektordatenbank. |

## Token-Messung

Gemessen an 20 öffentlichen, deutschsprachigen Seiten (6 Startseiten, 14 Artikel), Tokenizer `o200k_base` (tiktoken), Median der Ersparnis je Seite. Stand 01.10.2026:

| llmMarkdown im Vergleich zu | alle 20 Seiten | Startseiten | Artikel |
|---|---:|---:|---:|
| rohem HTML | **98 % weniger** | 99 % | 98 % |
| ganzer Seite als Text | **63 % weniger** | 64 % | 59 % |

Ehrlich dazu:
- Den größten Teil der Ersparnis gegenüber der ganzen Seite als Text bringt das Herausschneiden des Hauptinhalts (Median 51 %). Das können auch andere Werkzeuge; llmMarkdown legt im Median rund 9 % drauf.
- Die Spanne ist groß: 18 % bis 90 % gegenüber der ganzen Seite als Text. Schlanke Seiten sparen wenig.
- 20 Seiten sind eine kleine Stichprobe. Seiten ändern sich, ein neuer Lauf liefert etwas andere Zahlen.
- Verglichen werden Darstellungen einer Seite, keine Produkte.

Selbst nachmessen (kostet bei Ragfeed 40 Credits; der kostenlose Plan hat 1.000 im Monat):

```bash
cd token-messung
pip install -r requirements.txt
RAGFEED_API_KEY=sk-IhrSchluessel python messung.py
```

Eine andere Firecrawl-kompatible API lässt sich ohne llmMarkdown genauso messen:
`python messung.py --api https://… --key … --ohne-llm` (verglichen wird dann der Hauptinhalt).

## Firecrawl-SDK mit Ragfeed

```python
from firecrawl import Firecrawl

app = Firecrawl(api_key="sk-IhrSchluessel", api_url="https://api.ragfeed.de")
doc = app.scrape("https://de.wikipedia.org/wiki/Big_Data", formats=["markdown"])
```

Vollständiges Beispiel mit `llmMarkdown` und `chunks`: [`firecrawl-py/beispiel.py`](firecrawl-py/beispiel.py).
Getestet mit `firecrawl-py` 4.17. Nicht unterstützt sind derzeit unter anderem die Formate `branding`, `audio` und `video`.

## Lizenz

MIT, siehe [LICENSE](LICENSE). Ragfeed ist nicht mit Firecrawl verbunden; „Firecrawl“ wird nur genannt, um die Kompatibilität zu beschreiben.
