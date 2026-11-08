"""Ragfeed als A2A-Agent ansprechen – mit dem offiziellen a2a-sdk, so wie es ein anderer Agent täte.

Drei Aufrufe:
  1. fetch_clean_webdata: eine Seite abrufen (ohne Stream), Ergebnis als llmMarkdown.
  2. crawl_site: wenige Seiten crawlen und den Fortschritt live über einen Stream (SSE) verfolgen.
  3. Derselbe Abruf mit der Extension eu-web-data: Ragfeed legt dem Ergebnis bei, wie es zustande kam.

    pip install -r requirements.txt
    set RAGFEED_API_KEY=sk-...        (PowerShell: $env:RAGFEED_API_KEY="sk-..."; Bash: export RAGFEED_API_KEY=sk-...)
    python beispiel.py

Kostet rund 5 Credits. Gibt keinen Seiteninhalt und nie den Schlüssel aus.
Den Schlüssel gibt es im Dashboard auf https://ragfeed.de
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

# Die Agent Card liegt unter <AGENT>/.well-known/agent-card.json und beschreibt Fähigkeiten, Endpunkt und Auth.
AGENT = "https://ragfeed.de"
PAGE = "https://example.com/"      # die abzurufende Seite
SITE = "https://ragfeed.de/en"     # Startseite für den kleinen Crawl
# Data-only Extension aus der Agent Card: wo Daten verarbeitet werden und welche Seiten-Regeln gelten.
EU_WEB_DATA = "https://ragfeed.de/a2a/extensions/eu-web-data/v1"


def request(part: Part) -> SendMessageRequest:
    # Jede A2A-Nachricht braucht eine eigene message_id; die Rolle ist hier der aufrufende Nutzer/Agent.
    return SendMessageRequest(message=Message(message_id=str(uuid.uuid4()), role=Role.ROLE_USER, parts=[part]))


async def fetch(http: httpx.AsyncClient, card) -> None:
    # streaming=False: ein einzelner Task, wir warten auf das fertige Ergebnis.
    client = await create_client(card, ClientConfig(httpx_client=http, streaming=False))
    # Eine reine Text-Part löst den Standard-Skill fetch_clean_webdata aus, die URL steht als Text drin.
    events = [event async for event in client.send_message(request(Part(text=PAGE)))]
    await client.close()
    task = events[-1].task
    chars = sum(len(p.text) for a in task.artifacts for p in a.parts)
    print(f"Abruf: {TaskState.Name(task.status.state)}, Artifacts: {[a.name for a in task.artifacts]}, "
          f"Zeichen: {chars}, Credits: {task.metadata['creditsUsed']:.0f}")


async def stream(http: httpx.AsyncClient, card) -> None:
    # streaming=True: der Server schickt Zwischenstände (SUBMITTED -> WORKING -> Artifacts -> COMPLETED) über SSE.
    client = await create_client(card, ClientConfig(httpx_client=http, streaming=True))
    started = time.monotonic()
    # Einen bestimmten Skill ruft man über eine data-Part mit "skill" und seinen Parametern auf.
    part = Part(data=ParseDict({"skill": "crawl_site", "url": SITE, "limit": 3, "formats": ["links"]}, Value()))
    async for event in client.send_message(request(part)):
        kind = event.WhichOneof("payload")
        if kind == "status_update":
            detail = TaskState.Name(event.status_update.status.state)
        elif kind == "artifact_update":
            detail = event.artifact_update.artifact.name
        else:
            detail = TaskState.Name(event.task.status.state)
        # Kommen alle Zeilen erst ganz am Ende, puffert etwas zwischen Ihnen und dem Server den Stream.
        print(f"Stream {time.monotonic() - started:6.1f} s  {kind}: {detail}")
    await client.close()


async def provenance(key: str, card) -> None:
    # Wer den Header A2A-Extensions mit der URI schickt, bekommt zu jedem Ergebnis Herkunftsangaben: live oder aus dem
    # Cache, wann abgerufen, robots.txt geprüft, wo verarbeitet. Ohne den Header ändert sich nichts.
    headers = {"Authorization": f"Bearer {key}", "A2A-Extensions": EU_WEB_DATA}
    async with httpx.AsyncClient(headers=headers, timeout=90) as http:
        client = await create_client(card, ClientConfig(httpx_client=http, streaming=False))
        events = [event async for event in client.send_message(request(Part(text=PAGE)))]
        await client.close()
    artifact = events[-1].task.artifacts[0]
    print(f"Herkunft: {MessageToDict(artifact.metadata).get(EU_WEB_DATA)}")


async def main() -> int:
    key = os.environ.get("RAGFEED_API_KEY", "").strip()
    if not key:
        print("RAGFEED_API_KEY fehlt – Schlüssel aus dem Dashboard auf ragfeed.de setzen.")
        return 2
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {key}"}, timeout=90) as http:
        card = await A2ACardResolver(http, AGENT).get_agent_card()
        interface = card.supported_interfaces[0]
        print(f"Card: {card.name} {card.version}, {interface.url}, A2A {interface.protocol_version}, "
              f"Skills: {[s.id for s in card.skills]}")
        await fetch(http, card)
        await stream(http, card)
    await provenance(key, card)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
