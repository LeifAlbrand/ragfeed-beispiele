# Ragfeed in n8n (English)

Two workflows to import. In n8n: *Workflow → ⋯ → Import from File* (or paste the file content onto the canvas).

| File | What it does | Needs |
|---|---|---|
| [`ragfeed-chunks-vector-db.json`](ragfeed-chunks-vector-db.json) | Web page → ready chunks, one n8n item per chunk, for a vector database | built-in nodes only (HTTP Request) |
| [`ragfeed-firecrawl-node.json`](ragfeed-firecrawl-node.json) | Web page → `llmMarkdown` (main content, cleaned for language models) | Firecrawl community node (self-hosted n8n) |

## Chunks for a vector database

The HTTP Request node calls `POST https://api.ragfeed.de/v2/scrape` with the format `chunks`; **Split Out** makes one item per chunk.

Credential **Header Auth**:
- **Name:** `Authorization`
- **Value:** `Bearer sk-…` (your Ragfeed API key)

Each chunk has:
- `id`: a stable UUID from the normalized URL and position. Re-fetching the same page gives the chunk at the same position the same id, so you overwrite instead of creating duplicates.
- `text`, `embedText` (the text to embed; with the option `context` it starts with title or heading path), `tokens`
- `heading`: the heading path, e.g. `Design › Retrieval`
- `metadata`: URL, title, heading, language, position, fetch time and `hash` (changes only when the content changes)

`maxTokens` (100 to 4,000, default 500) sets the chunk size. Then connect your embeddings and vector store nodes (Qdrant, Pinecone, Supabase, Postgres/pgvector).

## With the Firecrawl node

Ragfeed speaks the Firecrawl API (v1 and v2), so the official Firecrawl node ([`@mendable/n8n-nodes-firecrawl`](https://www.npmjs.com/package/@mendable/n8n-nodes-firecrawl)) works unchanged with a different credential:

1. Install the node on self-hosted n8n via *Settings → Community Nodes*.
2. Create a credential **Firecrawl API**:
   - **Base URL:** `https://api.ragfeed.de/v2`
   - **API Key:** your Ragfeed key (`sk-…`)
3. Done. The node's credential test passes against Ragfeed.

For the Ragfeed formats `llmMarkdown` and `chunks` the workflow uses **Use Custom Body**:

```json
{
  "url": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
  "formats": ["llmMarkdown"],
  "onlyMainContent": true
}
```

## Credits

One page costs 1 credit, `llmMarkdown` and `chunks` cost nothing extra. The free plan has 1,000 credits a month, no card. Sign-up and dashboard are in German; overview in English: [ragfeed.de/en](https://ragfeed.de/en).
