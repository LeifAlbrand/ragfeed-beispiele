# Ragfeed als A2A-Agent

Ragfeed ist auch ein [A2A](https://a2a-protocol.org)-Agent: andere Agenten – oder deren Entwickler – können Ragfeed über das Agent2Agent-Protokoll beauftragen, eine Webseite sauber abzurufen, zu crawlen, zu durchsuchen oder zu überwachen, mit demselben API-Schlüssel wie sonst.

Die **Agent Card** liegt offen unter [`/.well-known/agent-card.json`](https://ragfeed.de/.well-known/agent-card.json). Sie nennt Endpunkt, Protokollversion (A2A 1.0) und die Fähigkeiten `fetch_clean_webdata`, `search_web`, `crawl_site`, `monitor_page`. Die data-only Extension `eu-web-data` beschreibt maschinenlesbar, wo Daten verarbeitet werden und welche Seiten-Regeln gelten ([Spezifikation](https://ragfeed.de/a2a/extensions/eu-web-data/v1)).

## Beispiel

[`beispiel.py`](beispiel.py) spricht Ragfeed mit dem offiziellen `a2a-sdk` an, so wie es ein anderer Agent täte: erst ein Seitenabruf (`fetch_clean_webdata`), dann ein kleiner Crawl über einen Stream, bei dem jeder Zwischenstand mit Zeitstempel ausgegeben wird. Zum Schluss derselbe Abruf mit der Extension `eu-web-data`: Das Ergebnis trägt dann Herkunftsangaben, die sich für die eigene Dokumentation festhalten lassen.

```bash
pip install -r requirements.txt
export RAGFEED_API_KEY=sk-IhrSchluessel   # PowerShell: $env:RAGFEED_API_KEY="sk-..."
python beispiel.py
```

Erwartete Ausgabe (gekürzt):

```
Card: Ragfeed 1.1.0, https://api.ragfeed.de/a2a/v1, A2A 1.0, Skills: ['fetch_clean_webdata', 'search_web', 'crawl_site', 'monitor_page']
Abruf: TASK_STATE_COMPLETED, Artifacts: ['llmMarkdown'], Zeichen: 1095, Credits: 1
Stream    0.1 s  task: TASK_STATE_SUBMITTED
Stream    0.3 s  status_update: TASK_STATE_WORKING
Stream    1.3 s  artifact_update: pages
Stream    1.3 s  status_update: TASK_STATE_COMPLETED
Herkunft: {'fetchedFrom': 'cache', 'fetchedAt': '…', 'processedIn': 'DE', 'robotsChecked': True}
```

`cache` heißt hier: eine frische Kopie vom ersten Abruf, nie ein Archiv. Kostet rund 5 Credits; der kostenlose Plan hat 1.000 im Monat.

## Herkunftsangaben (Extension `eu-web-data`)

Wer den Header `A2A-Extensions: https://ragfeed.de/a2a/extensions/eu-web-data/v1` mitschickt, bekommt sie im `metadata` jedes Artifacts unter genau dieser URI; beim Crawl je Seite. Ragfeed bestätigt die Aktivierung im selben Antwort-Header. Ohne den Header ändert sich nichts. Es ist eine Selbstauskunft, kein Prüfbericht; was die Felder bedeuten, steht in der [Spezifikation](https://ragfeed.de/a2a/extensions/eu-web-data/v1).

## Gut zu wissen

- **Standard-Skill:** Eine reine Text-Part gilt als `fetch_clean_webdata` mit der URL als Text. Einen bestimmten Skill ruft man über eine `data`-Part mit `{"skill": "…", …}` auf.
- **Protokoll 1.0:** Ohne Header `A2A-Version` nimmt der Server nach Spezifikation 0.3 an und lehnt ab. Das SDK setzt den Header selbst.
- **Nur API-Schlüssel** als Bearer-Token, derselbe wie für die REST- und MCP-Schnittstelle.
- **Fair zur Zielseite:** Bei jeder A2A-Aufgabe, auch beim einzelnen Abruf, beachtet Ragfeed robots.txt und Opt-outs der Seite, liefert keine Archivkopien und umgeht keinen Bot-Schutz; abgelehnte Aufgaben kosten nichts.

Englische Fassung: [`en/`](en). Getestet mit `a2a-sdk` 1.3.0, zuletzt am 08.11.2026.
