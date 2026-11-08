"""Call Ragfeed as an A2A agent with the official a2a-sdk, the way another agent would.

Three calls:
  1. fetch_clean_webdata: fetch one page (no stream), result as llmMarkdown.
  2. crawl_site: crawl a few pages and follow progress live over a stream (SSE).
  3. The same fetch with the eu-web-data extension: Ragfeed attaches how the result came about.

    pip install -r requirements.txt
    export RAGFEED_API_KEY=sk-...     (PowerShell: $env:RAGFEED_API_KEY="sk-..."; cmd: set RAGFEED_API_KEY=sk-...)
    python example.py

Costs about 5 credits. Prints no page content and never the key.
Get the key from the dashboard at https://ragfeed.de
"""
import asyncio
import os
import sys
import time
import uuid

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest, TaskState
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Value

# The Agent Card lives at <AGENT>/.well-known/agent-card.json and describes skills, endpoint and auth.
AGENT = "https://ragfeed.de"
PAGE = "https://example.com/"      # the page to fetch
SITE = "https://ragfeed.de/en"     # start page for the small crawl
# Data-only extension from the Agent Card: where data is processed and which site rules apply.
EU_WEB_DATA = "https://ragfeed.de/a2a/extensions/eu-web-data/v1"


def request(part: Part) -> SendMessageRequest:
    # Every A2A message needs its own message_id; the role here is the calling user/agent.
    return SendMessageRequest(message=Message(message_id=str(uuid.uuid4()), role=Role.ROLE_USER, parts=[part]))


async def fetch(http: httpx.AsyncClient, card) -> None:
    # streaming=False: a single task, we wait for the finished result.
    client = await create_client(card, ClientConfig(httpx_client=http, streaming=False))
    # A plain text part triggers the default skill fetch_clean_webdata, with the URL as its text.
    events = [event async for event in client.send_message(request(Part(text=PAGE)))]
    await client.close()
    task = events[-1].task
    chars = sum(len(p.text) for a in task.artifacts for p in a.parts)
    print(f"Fetch: {TaskState.Name(task.status.state)}, artifacts: {[a.name for a in task.artifacts]}, "
          f"chars: {chars}, credits: {task.metadata['creditsUsed']:.0f}")


async def stream(http: httpx.AsyncClient, card) -> None:
    # streaming=True: the server sends interim states (SUBMITTED -> WORKING -> artifacts -> COMPLETED) over SSE.
    client = await create_client(card, ClientConfig(httpx_client=http, streaming=True))
    started = time.monotonic()
    # You call a specific skill through a data part with "skill" and its parameters.
    part = Part(data=ParseDict({"skill": "crawl_site", "url": SITE, "limit": 3, "formats": ["links"]}, Value()))
    async for event in client.send_message(request(part)):
        kind = event.WhichOneof("payload")
        if kind == "status_update":
            detail = TaskState.Name(event.status_update.status.state)
        elif kind == "artifact_update":
            detail = event.artifact_update.artifact.name
        else:
            detail = TaskState.Name(event.task.status.state)
        # If all lines arrive only at the very end, something between you and the server buffers the stream.
        print(f"Stream {time.monotonic() - started:6.1f} s  {kind}: {detail}")
    await client.close()


async def provenance(key: str, card) -> None:
    # Send the A2A-Extensions header with the URI and every result carries provenance: live or from the cache, when
    # fetched, robots.txt checked, where processed. Without the header nothing changes.
    headers = {"Authorization": f"Bearer {key}", "A2A-Extensions": EU_WEB_DATA}
    async with httpx.AsyncClient(headers=headers, timeout=90) as http:
        client = await create_client(card, ClientConfig(httpx_client=http, streaming=False))
        events = [event async for event in client.send_message(request(Part(text=PAGE)))]
        await client.close()
    artifact = events[-1].task.artifacts[0]
    print(f"Provenance: {MessageToDict(artifact.metadata).get(EU_WEB_DATA)}")


async def main() -> int:
    key = os.environ.get("RAGFEED_API_KEY", "").strip()
    if not key:
        print("RAGFEED_API_KEY missing - set a key from the dashboard at ragfeed.de")
        return 2
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {key}"}, timeout=90) as http:
        card = await A2ACardResolver(http, AGENT).get_agent_card()
        interface = card.supported_interfaces[0]
        print(f"Card: {card.name} {card.version}, {interface.url}, A2A {interface.protocol_version}, "
              f"skills: {[s.id for s in card.skills]}")
        await fetch(http, card)
        await stream(http, card)
    await provenance(key, card)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
