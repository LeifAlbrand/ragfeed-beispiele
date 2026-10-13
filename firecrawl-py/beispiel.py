"""Bestehender Firecrawl-Code mit Ragfeed: nur api_url und Schlüssel ändern sich.

    pip install firecrawl-py httpx
    set RAGFEED_API_KEY=fc-...            (PowerShell: $env:RAGFEED_API_KEY="fc-...")
    python beispiel.py
"""
import os

import httpx
from firecrawl import Firecrawl

API_URL = "https://api.ragfeed.de"  # vorher: https://api.firecrawl.dev
KEY = os.environ["RAGFEED_API_KEY"]
URL = "https://de.wikipedia.org/wiki/Big_Data"

# 1. Unveränderter SDK-Code: Markdown einer Seite.
app = Firecrawl(api_key=KEY, api_url=API_URL)
doc = app.scrape(URL, formats=["markdown"])
print(doc.markdown[:500], "\n...")

# 2. Ragfeed-Formate: llmMarkdown und fertige Chunks für eine Vektordatenbank (ohne Aufpreis, 1 Credit je Seite).
#    Direkt über die REST-API, weil das SDK nur die Firecrawl-Formate kennt.
r = httpx.post(f"{API_URL}/v2/scrape", headers={"Authorization": f"Bearer {KEY}"}, timeout=120,
               json={"url": URL, "formats": ["llmMarkdown", {"type": "chunks", "maxTokens": 500}]})
r.raise_for_status()
data = r.json()["data"]
print(f"llmMarkdown: {len(data['llmMarkdown'])} Zeichen, {len(data['chunks'])} Chunks")
for chunk in data["chunks"][:3]:
    # id ist stabil je Abschnitt (gut als Schlüssel in der Vektordatenbank), heading der Überschriftenpfad.
    print(f"- {chunk['id']}  {chunk['heading']}: {chunk['text'][:80]!r}")
