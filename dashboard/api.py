"""Thin adapter between the dashboard and the Anthropic API.

Provisioning state lives in `dashboard/.state/` (gitignored):
  ids.json       agent / environment / global store IDs
  users.json     new-hire name -> personal memory store ID   (StoreRegistry)
  sessions.json  session ID -> who started it               (AttributionLog)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from anthropic import Anthropic
from dotenv import load_dotenv

from dashboard.core import (
    AttributionLog,
    Briefing,
    Mode,
    StoreRegistry,
    build_timeline,
    load_json,
    load_seed,
    parse_briefing,
    save_json,
    seed_store,
    slugify,
)

load_dotenv()

STATE = Path(__file__).parent / ".state"
SEED_DIR = Path(__file__).parent / "seed"
MODEL = "claude-sonnet-5-5"

ROLES = [
    "Backend Engineer",
    "Frontend Engineer",
    "SRE / Platform Engineer",
    "Data Engineer",
    "Engineering Manager",
]

SYSTEM_PROMPT = """\
You are the Onboarding Memory Agent for a fast-growing engineering company.

You have up to two memory folders mounted under /mnt/memory/ (see the memory
section of this prompt for their exact paths):

- **Team knowledge (global)** — the company wiki: policies, people, ownership,
  workflows. Curated by experienced colleagues. Newer entries supersede older
  ones. When it is mounted read-only you MUST NOT try to write to it.
- **Personal preferences (user)** — only present for a new hire. Holds that
  person's preferences (answer style, format, their role, things they asked
  you to remember about them). Personal preferences ALWAYS override default
  answer style.

# Protocol

1. At the start of every session, list both folders and read what is relevant.
2. Answer from team knowledge. Cite the memory file you relied on. If a policy
   changed recently, say so and give the effective date.
3. If the user states a personal preference ("answer in bullet points",
   "I'm on the payments team"), save it to the personal folder.
4. When ingesting knowledge into the global folder: one concept per file with a
   descriptive kebab-case name (e.g. `prod-access-policy.md`). If a file on
   the topic exists, UPDATE it in place rather than creating a new one, and note
   the effective date and what changed. Keep files concise and factual — no
   copies of whole documents.
"""

_client: Anthropic | None = None


def client() -> Anthropic:
    global _client
    if _client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("Set ANTHROPIC_API_KEY (env or .env).")
        _client = Anthropic()
    return _client


# --------------------------------------------------------------------------- provisioning


_PROVISIONERS = {
    "agent": lambda c: c.beta.agents.create(
        name="Onboarding Memory Agent",
        model=MODEL,
        system=SYSTEM_PROMPT,
        tools=[{"type": "agent_toolset_20260401"}],
        metadata={"hackathon": "partner-basecamp-2026", "track": "onboarding-dashboard"},
    ).id,
    "environment": lambda c: c.beta.environments.create(
        name="onboarding-dashboard-env",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    ).id,
    "global_store": lambda c: c.beta.memory_stores.create(
        name="team-knowledge",
        description=(
            "Global team knowledge: policies, people, ownership and workflows. "
            "Curated by experienced colleagues; newer entries supersede older ones."
        ),
    ).id,
}


def _ids() -> dict:
    """Agent / environment / global store IDs, provisioning any that are missing."""
    path = STATE / "ids.json"
    ids = load_json(path)
    missing = [k for k in _PROVISIONERS if k not in ids]
    for key in missing:
        ids[key] = _PROVISIONERS[key](client())
    if missing:
        save_json(path, ids)
    return ids


def global_store() -> str:
    """Global store ID. On first use, seeds an empty store from `dashboard/seed/` so every
    persona has something to work with before anyone from the team ingests."""
    ids = _ids()
    if not ids.get("seeded"):
        store_id = ids["global_store"]
        mems = client().beta.memory_stores.memories
        seed_store(
            existing_paths=[m.path for m in list_memories(store_id)],
            seed=load_seed(SEED_DIR),
            create=lambda path, content: mems.create(store_id, path=path, content=content),
        )
        ids["seeded"] = True
        save_json(STATE / "ids.json", ids)
    return ids["global_store"]


def _create_user_store(name: str) -> str:
    return client().beta.memory_stores.create(
        name=f"prefs-{slugify(name)}",
        description=f"Personal preferences and notes for new hire {name}. Overrides default answer style.",
    ).id


registry = StoreRegistry(STATE / "users.json", _create_user_store)
attribution = AttributionLog(STATE / "sessions.json")


# --------------------------------------------------------------------------- reading memory


@dataclass(frozen=True)
class Memory:
    id: str
    path: str
    content: str
    sha256: str
    updated_at: str


def list_memories(store_id: str, prefix: str = "/") -> list[Memory]:
    out: list[Memory] = []
    for item in client().beta.memory_stores.memories.list(store_id, path_prefix=prefix, view="full"):
        if item.type == "memory":
            content = item.content
            if content is None:  # defensive: some list responses omit content
                content = client().beta.memory_stores.memories.retrieve(
                    item.id, memory_store_id=store_id, view="full"
                ).content
            out.append(
                Memory(item.id, item.path, content or "", item.content_sha256, item.updated_at.date().isoformat())
            )
        elif item.path != prefix:
            out.extend(list_memories(store_id, item.path))
    return sorted(out, key=lambda m: m.path)


def timeline(store_id: str, memory_id: str):
    versions = list(
        client().beta.memory_stores.memory_versions.list(store_id, memory_id=memory_id, view="full")
    )
    return build_timeline(versions, attribution.who)


# --------------------------------------------------------------------------- briefing (Messages API)


def briefing(role: str, memories: list[Memory]) -> Briefing:
    corpus = "\n\n".join(f"### {m.path} (updated {m.updated_at})\n{m.content}" for m in memories)
    prompt = f"""A new hire just joined as a **{role}**. Below is our team knowledge base.

{corpus}

Return ONLY a JSON object, no prose:
{{"relevant": [{{"path": "<exact path from above>", "why": "<one sentence: why this matters for a {role} in their first weeks>"}}],
  "questions": ["<3-5 questions this new hire should ask the onboarding agent, specific to our knowledge>"]}}
Order "relevant" most important first. Include only paths that are genuinely relevant to the role."""
    resp = client().messages.create(model=MODEL, max_tokens=2000, messages=[{"role": "user", "content": prompt}])
    text = "".join(b.text for b in resp.content if b.type == "text")
    return parse_briefing(text, {m.path for m in memories})


# --------------------------------------------------------------------------- sessions (Managed Agents)


def _store_resource(store_id: str, access: str, instructions: str) -> Any:
    return {"type": "memory_store", "memory_store_id": store_id, "access": access, "instructions": instructions}


SESSION_END_EVENTS = {"session.status_idle", "session.status_terminated", "session.error"}


def run_session(*, name: str, mode: Mode, message: str, title: str) -> Iterator[str]:
    """Start a Managed Agent session for this person and stream back text (and memory-op notes).

    Mode.EXPERT:   global store read_write.
    Mode.NEW_HIRE: global store read_only + personal store read_write.
    """
    ids = _ids()
    if mode is Mode.EXPERT:
        resources: list[Any] = [
            _store_resource(
                ids["global_store"], "read_write",
                "Global team knowledge. You are ingesting knowledge from an experienced colleague: "
                "create or UPDATE concept files here.",
            )
        ]
    else:
        resources = [
            _store_resource(ids["global_store"], "read_only", "Global team knowledge (read-only). Answer from this."),
            _store_resource(
                registry.user_store(name), "read_write",
                f"Personal preferences for {name}. Read first; apply them to every answer. "
                "Save any new personal preference the user states.",
            ),
        ]

    c = client()
    session = c.beta.sessions.create(
        agent=ids["agent"], environment_id=ids["environment"], title=title, resources=resources
    )
    attribution.record(session.id, name, mode.value)

    with c.beta.sessions.events.stream(session.id) as stream:
        c.beta.sessions.events.send(
            session.id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": message}]}],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        yield getattr(block, "text", "")
            elif event.type == "agent.tool_use":
                inp = getattr(event, "input", {}) or {}
                target = str(inp.get("path") or inp.get("file_path") or inp.get("command") or "")
                if "/mnt/memory" in target:
                    yield f"\n\n`🧠 {getattr(event, 'name', 'tool')}: {target[:120]}`\n\n"
            elif event.type in SESSION_END_EVENTS:
                if event.type != "session.status_idle":
                    yield f"\n\n⚠️ Session ended: `{event.type}`"
                break
