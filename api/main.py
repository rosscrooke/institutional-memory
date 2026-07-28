"""FastAPI wrapper around the memory-backed coaching agent.

Run from the repository root:

    uvicorn api.main:app --reload

Interactive docs at http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Path as PathParam
from fastapi.responses import StreamingResponse

from .coach import Coach
from .models import (
    Client,
    CreateClientRequest,
    MemoryList,
    MessageRequest,
)
from .registry import ClientRegistry

coach = Coach()
registry = ClientRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Set ANTHROPIC_API_KEY before starting the API.")
    await coach.ensure_infrastructure()
    yield


app = FastAPI(
    title="Institutional Memory — Coaching API",
    description=(
        "A personal training coach with persistent per-client memory.\n\n"
        "Each client gets their own memory store. Every message runs in a fresh "
        "session with that store mounted, so continuity comes from memory rather "
        "than from a long-lived conversation — and one client's constraints can "
        "never surface in another client's plan."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


async def get_client(
    client_id: str = PathParam(..., examples=["cli_a1b2c3d4e5f6"]),
) -> Client:
    client = await registry.get(client_id)
    if client is None:
        raise HTTPException(404, f"No client with id {client_id!r}")
    return client


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {
        "status": "ok",
        "agent_id": coach.agent_id,
        "environment_id": coach.environment_id,
    }


@app.post("/clients", response_model=Client, status_code=201, tags=["clients"])
async def create_client(body: CreateClientRequest) -> Client:
    """Register a client and provision a memory store for them."""
    store_id = await coach.create_memory_store(body.name)
    return await registry.add(body.name, store_id)


@app.get("/clients", response_model=list[Client], tags=["clients"])
async def list_clients() -> list[Client]:
    return await registry.list()


@app.get("/clients/{client_id}", response_model=Client, tags=["clients"])
async def read_client(client: Client = Depends(get_client)) -> Client:
    return client


@app.post("/clients/{client_id}/messages", tags=["coaching"])
async def send_message(
    body: MessageRequest, client: Client = Depends(get_client)
) -> StreamingResponse:
    """Send a message to the coach and stream the reply as Server-Sent Events.

    A turn takes 30–90 seconds. Events, in order:

    - `status`   — session created, work starting
    - `tool_use` — a tool call; `is_memory` marks reads and writes under `/mnt/memory/`
    - `message`  — a chunk of the coach's reply
    - `error`    — something failed; the stream ends after this
    - `done`     — the full answer plus the memory paths that were written
    """
    return StreamingResponse(
        coach.stream_message(client.memory_store_id, body.text, body.documents),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/clients/{client_id}/memory", response_model=MemoryList, tags=["memory"])
async def read_memory(
    include_content: bool = True, client: Client = Depends(get_client)
) -> MemoryList:
    """What the coach remembers about this client."""
    memories = await coach.list_memories(client.memory_store_id, include_content)
    return MemoryList(memory_store_id=client.memory_store_id, memories=memories)


@app.delete(
    "/clients/{client_id}/memory/{memory_id}", status_code=204, tags=["memory"]
)
async def forget(memory_id: str, client: Client = Depends(get_client)) -> None:
    """Delete one memory — the 'forget that' half of memory management."""
    await coach.delete_memory(client.memory_store_id, memory_id)
