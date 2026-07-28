"""Client registry — maps a client to their own memory store.

Per-tenant memory is the whole point: each client gets a memory store of their
own, so one client's injuries can never surface in another client's plan.

Backed by a JSON file. That is deliberate for a hackathon build — swapping in
Postgres means replacing this module and nothing else.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import Client

REGISTRY_PATH = Path(".clients.json")


class ClientRegistry:
    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        self._path = path
        self._lock = asyncio.Lock()

    def _read(self) -> dict[str, dict]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def _write(self, data: dict[str, dict]) -> None:
        # Write-then-rename so a crash mid-write can't truncate the registry.
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, default=str))
        tmp.replace(self._path)

    async def add(self, name: str, memory_store_id: str) -> Client:
        async with self._lock:
            data = self._read()
            client = Client(
                client_id=f"cli_{uuid.uuid4().hex[:12]}",
                name=name,
                memory_store_id=memory_store_id,
                created_at=datetime.now(timezone.utc),
            )
            data[client.client_id] = client.model_dump(mode="json")
            self._write(data)
            return client

    async def get(self, client_id: str) -> Client | None:
        async with self._lock:
            raw = self._read().get(client_id)
        return Client(**raw) if raw else None

    async def list(self) -> list[Client]:
        async with self._lock:
            data = self._read()
        clients = [Client(**raw) for raw in data.values()]
        return sorted(clients, key=lambda c: c.created_at)
