"""The Managed Agents layer behind the API.

One agent and one environment are shared by every client; each client gets
their own memory store. A message creates a fresh session with that client's
store attached — continuity comes from memory, not from a long-lived session.
That is the same thing run_session_1 and run_session_2 demonstrate, with the
round boundary replaced by an HTTP request.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncIterator

from anthropic import AsyncAnthropic

# Single source of truth for the coach's behaviour — the same prompt the
# scripts provision with.
from create_agent import SYSTEM_PROMPT

from .models import Document, Memory

AGENT_ID_PATH = Path(".agent_id")
ENVIRONMENT_ID_PATH = Path(".environment_id")

STORE_INSTRUCTIONS = (
    "This is your persistent training file for this client. Check it before "
    "programming anything. Constraints recorded in earlier sessions still "
    "apply unless something explicitly clears them. Record what you learn."
)


def _sse(event: str, payload: dict) -> str:
    """Format a Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


class Coach:
    def __init__(self) -> None:
        self.client = AsyncAnthropic()
        self.agent_id: str | None = None
        self.environment_id: str | None = None

    # --- provisioning -------------------------------------------------------

    async def ensure_infrastructure(self) -> None:
        """Reuse the agent and environment on disk, or provision them once.

        Reusing the dotfiles means the API and the CLI scripts drive the same
        agent, so a store populated by run_session_1.py is readable here.
        """
        if AGENT_ID_PATH.exists():
            self.agent_id = AGENT_ID_PATH.read_text().strip()
        else:
            agent = await self.client.beta.agents.create(
                name="Personal Training Coach",
                model="claude-sonnet-4-6",
                system=SYSTEM_PROMPT,
                tools=[{"type": "agent_toolset_20260401"}],
                metadata={"hackathon": "partner-basecamp-2026", "track": "memory-agent"},
            )
            self.agent_id = agent.id
            AGENT_ID_PATH.write_text(agent.id)

        if ENVIRONMENT_ID_PATH.exists():
            self.environment_id = ENVIRONMENT_ID_PATH.read_text().strip()
        else:
            environment = await self.client.beta.environments.create(
                name="memory-agent-env",
                config={"type": "cloud", "networking": {"type": "unrestricted"}},
            )
            self.environment_id = environment.id
            ENVIRONMENT_ID_PATH.write_text(environment.id)

    async def create_memory_store(self, client_name: str) -> str:
        store = await self.client.beta.memory_stores.create(
            name=f"Training File — {client_name}",
            description=(
                f"Persistent training file for {client_name}. Injuries and "
                "clearances (with dates), available equipment, hard preferences, "
                "and a log of what was programmed. Newer entries supersede older "
                "ones on the same topic, but a constraint stays in force until "
                "something explicitly clears it."
            ),
            metadata={"client_name": client_name},
        )
        return store.id

    # --- memory -------------------------------------------------------------

    async def list_memories(self, store_id: str, include_content: bool) -> list[Memory]:
        items = []
        async for item in self.client.beta.memory_stores.memories.list(
            store_id, path_prefix="/"
        ):
            if item.type != "memory":  # "memory_prefix" — a directory node
                continue
            content = None
            if include_content:
                full = await self.client.beta.memory_stores.memories.retrieve(
                    item.id, memory_store_id=store_id
                )
                content = full.content or ""
            items.append(
                Memory(
                    memory_id=item.id,
                    path=item.path,
                    size_bytes=item.content_size_bytes or 0,
                    content=content,
                )
            )
        return sorted(items, key=lambda m: m.path)

    async def delete_memory(self, store_id: str, memory_id: str) -> None:
        await self.client.beta.memory_stores.memories.delete(
            memory_id, memory_store_id=store_id
        )

    # --- the coaching turn --------------------------------------------------

    def _build_user_message(self, text: str, documents: list[Document]) -> str:
        parts = [
            "Before you answer:\n"
            "1. Check your memory store at /mnt/memory/ to see what you already "
            "know about this client.\n"
            "2. Read any documents below.\n"
            "3. Reconcile conflicts — UPDATE existing memory entries rather than "
            "appending. Note effective dates.\n"
            "4. Answer.\n"
            "5. Before finishing, save anything worth remembering to /mnt/memory/."
        ]
        for doc in documents:
            parts.append(f"=====  DOCUMENT: {doc.name}  =====\n{doc.content}")
        parts.append("=" * 50 + f"\n{text}")
        return "\n\n".join(parts)

    async def stream_message(
        self, memory_store_id: str, text: str, documents: list[Document]
    ) -> AsyncIterator[str]:
        """Run one coaching turn, emitting SSE frames as the agent works."""
        session = await self.client.beta.sessions.create(
            agent=self.agent_id,
            environment_id=self.environment_id,
            title="Coaching turn",
            resources=[
                {
                    "type": "memory_store",
                    "memory_store_id": memory_store_id,
                    "access": "read_write",
                    "instructions": STORE_INSTRUCTIONS,
                }
            ],
        )
        yield _sse("status", {"session_id": session.id, "state": "running"})

        answer_parts: list[str] = []
        memory_writes: list[str] = []

        try:
            # Stream first, then send — the stream only delivers events that
            # occur after it opens.
            stream = await self.client.beta.sessions.events.stream(session.id)
            async with stream:
                await self.client.beta.sessions.events.send(
                    session.id,
                    events=[
                        {
                            "type": "user.message",
                            "content": [
                                {
                                    "type": "text",
                                    "text": self._build_user_message(text, documents),
                                }
                            ],
                        }
                    ],
                )
                async for event in stream:
                    if event.type == "agent.message":
                        for block in event.content:
                            if getattr(block, "type", None) == "text":
                                answer_parts.append(block.text)
                                yield _sse("message", {"text": block.text})

                    elif event.type == "agent.tool_use":
                        name = getattr(event, "name", "?")
                        inp = getattr(event, "input", {}) or {}
                        target = (
                            inp.get("path")
                            or inp.get("file_path")
                            or inp.get("command")
                            or ""
                        )
                        is_memory = "/mnt/memory" in str(target)
                        if is_memory and name in ("write", "edit", "create"):
                            memory_writes.append(str(target))
                        yield _sse(
                            "tool_use",
                            {
                                "tool": name,
                                "target": str(target) or None,
                                "is_memory": is_memory,
                            },
                        )

                    elif event.type == "session.error":
                        detail = getattr(getattr(event, "error", None), "message", None)
                        yield _sse("error", {"detail": detail or "session error"})

                    elif event.type == "session.status_terminated":
                        break

                    elif event.type == "session.status_idle":
                        # Idle is transient while awaiting a tool confirmation;
                        # only a terminal stop reason ends the turn.
                        stop_reason = getattr(event, "stop_reason", None)
                        if getattr(stop_reason, "type", None) == "requires_action":
                            continue
                        break

        except Exception as exc:  # surface failures on the stream, not as a 500
            yield _sse("error", {"detail": f"{type(exc).__name__}: {exc}"})
            return

        yield _sse(
            "done",
            {
                "session_id": session.id,
                "answer": "".join(answer_parts),
                "memory_writes": memory_writes,
            },
        )
