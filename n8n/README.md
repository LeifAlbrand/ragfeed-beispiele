# Ragfeed in n8n

Zwei Workflows zum Importieren. In n8n: *Workflow → ⋯ → Import from File* (oder den Inhalt der Datei kopieren und auf der Arbeitsfläche einfügen).

| Datei | Was er macht | Braucht |
|---|---|---|
| [`ragfeed-firecrawl-baustein.json`](ragfeed-firecrawl-baustein.json) | Webseite → `llmMarkdown` (Hauptinhalt, bereinigt für Sprachmodelle) | Firecrawl-Baustein |
| [`ragfeed-chunks-vektordatenbank.json`](ragfeed-chunks-vektordatenbank.json) | Webseite → fertige Chunks, ein n8n-Eintrag pro Chunk, bereit für eine Vektordatenbank | nur Bordmittel (HTTP Request) |

## 1. Mit dem Firecrawl-Baustein

Ragfeed versteht die Firecrawl-API (v1 und v2). Der offizielle Firecrawl-Baustein ([`@mendable/n8n-nodes-firecrawl`](https://www.npmjs.com/package/@mendable/n8n-nodes-firecrawl)) funktioniert deshalb unverändert, nur mit anderen Zugangsdaten:

1. Baustein **Firecrawl** hinzufügen. Bei selbst betriebenem n8n vorher unter *Settings → Community Nodes* installieren.
2. Zugangsdaten **Firecrawl API** anlegen:
   - **Base URL:** `https://api.ragfeed.de/v2`
   - **API Key:** Ihr Ragfeed-Schlüssel (`sk-…`) aus dem Dashboard auf [ragfeed.de](https://ragfeed.de)
3. Fertig. Der Verbindungstest des Bausteins läuft gegen Ragfeed durch.

Bestehende Firecrawl-Workflows stellen Sie so um, indem Sie nur die Zugangsdaten tauschen. Für die Ragfeed-eigenen Formate `llmMarkdown` und `chunks` nutzt der Beispiel-Workflow die Option **Use Custom Body**:

```json
{
  "url": "https://de.wikipedia.org/wiki/Retrieval-Augmented_Generation",
  "formats": ["llmMarkdown"],
  "onlyMainContent": true
}
```

## 2. Chunks für die Vektordatenbank (ohne Zusatz-Baustein)

Der HTTP-Request-Baustein ruft `POST https://api.ragfeed.de/v2/scrape` mit dem Format `chunks` auf, **Split Out** macht aus der Liste einen Eintrag pro Chunk.

Zugangsdaten **Header Auth**:
- **Name:** `Authorization`
- **Value:** `Bearer sk-…` (Ihr Ragfeed-Schlüssel)

Jeder Chunk enthält:
- `id`: feste UUID aus normalisierter Adresse und Position. Bei erneutem Abruf derselben Seite bekommt der Chunk an derselben Position dieselbe ID, Sie überschreiben also, statt Dubletten anzulegen.
- `text` und `embedText` (Text mit Überschriftenpfad, zum Einbetten), `tokens`
- `metadata`: Adresse, Titel, Überschrift, Sprache, Position, Abrufdatum und `hash` (ändert sich nur, wenn sich der Inhalt ändert)

`maxTokens` (100 bis 4000, Standard 500) steuert die Chunk-Größe. Danach verbinden Sie den Ausgang mit Ihrem Embedding- und Vektordatenbank-Baustein (z. B. Qdrant, Pinecone, Postgres/pgvector).

## Getestet

14.10.2026 gegen `api.ragfeed.de` mit der Beispielseite: `llmMarkdown` (ca. 6.400 Tokens) und 14 Chunks bei `maxTokens: 500`. Jeder Abruf kostet 1 Credit, der kostenlose Plan hat 1.000 im Monat.
