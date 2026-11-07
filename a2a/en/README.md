# Ragfeed as an A2A agent

Ragfeed is also an [A2A](https://a2a-protocol.org) agent: other agents – or their developers – can ask Ragfeed over the Agent2Agent protocol to fetch a web page cleanly, crawl it, search, or monitor it, using the same API key as everywhere else.

The **Agent Card** is public at [`/.well-known/agent-card.json`](https://ragfeed.de/.well-known/agent-card.json). It lists the endpoint, protocol version (A2A 1.0) and the skills `fetch_clean_webdata`, `search_web`, `crawl_site`, `monitor_page`. The data-only extension `eu-web-data` describes, machine-readably, where data is processed and which site rules apply ([specification](https://ragfeed.de/a2a/extensions/eu-web-data/v1)).

## Example

[`example.py`](example.py) calls Ragfeed with the official `a2a-sdk`, the way another agent would: first a page fetch (`fetch_clean_webdata`), then a small crawl over a stream that prints each interim state with a timestamp.

```bash
pip install -r requirements.txt
export RAGFEED_API_KEY=sk-yourkey   # PowerShell: $env:RAGFEED_API_KEY="sk-..."
python example.py
```

Expected output (shortened):

```
Card: Ragfeed 1.1.0, https://api.ragfeed.de/a2a/v1, A2A 1.0, skills: ['fetch_clean_webdata', 'search_web', 'crawl_site', 'monitor_page']
Fetch: TASK_STATE_COMPLETED, artifacts: ['llmMarkdown'], chars: 1095, credits: 1
Stream    0.1 s  task: TASK_STATE_SUBMITTED
Stream    0.3 s  status_update: TASK_STATE_WORKING
Stream    1.3 s  artifact_update: pages
Stream    1.3 s  status_update: TASK_STATE_COMPLETED
```

Costs about 4 credits; the free plan has 1,000 per month.

## Good to know

- **Default skill:** a plain text part counts as `fetch_clean_webdata` with the URL as its text. You call a specific skill through a `data` part with `{"skill": "…", …}`.
- **Protocol 1.0:** without an `A2A-Version` header the server assumes 0.3 per spec and rejects. The SDK sets the header itself.
- **API key only**, as a Bearer token – the same one as for the REST and MCP interface.
- **Fair to the target site:** on crawl and monitoring Ragfeed honours robots.txt and bypasses no bot protection; rejected tasks cost nothing.

Tested 2026-11-07 against `api.ragfeed.de` with `a2a-sdk` 1.3.0.
