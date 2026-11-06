"""Pure logic for the onboarding dashboard — no network, no Streamlit.

Everything here is testable offline; `dashboard/api.py` wires it to the
Anthropic API and `dashboard/app.py` renders it.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable


class Mode(Enum):
    NEW_HIRE = "new hire"
    EXPERT = "expert"


def slugify(name: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in name.lower()).strip("-") or "user"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


class StoreRegistry:
    """Maps a new hire's name to their personal memory store, creating it on first use."""

    def __init__(self, path: Path, create_store: Callable[[str], str]):
        self._path = Path(path)
        self._create_store = create_store

    def user_store(self, name: str) -> str:
        key = name.strip().lower()
        data = load_json(self._path)
        if key not in data:
            data[key] = self._create_store(name.strip())
            save_json(self._path, data)
        return data[key]


class AttributionLog:
    """Remembers which person started which session, so memory versions can be attributed."""

    def __init__(self, path: Path):
        self._path = Path(path)

    def record(self, session_id: str, name: str, mode: str) -> None:
        data = load_json(self._path)
        data[session_id] = {"name": name, "mode": mode}
        save_json(self._path, data)

    def who(self, session_id: str | None) -> str:
        entry = load_json(self._path).get(session_id or "")
        return f"{entry['name']} ({entry['mode']})" if entry else "agent"


SEED_AUTHOR = "initial knowledge (seed)"


def load_seed(directory: Path) -> dict[str, str]:
    """Read every .md file under `directory` as {store path: content}."""
    directory = Path(directory)
    return {
        "/" + f.relative_to(directory).as_posix(): f.read_text()
        for f in sorted(directory.rglob("*.md"))
    }


def seed_store(existing_paths, seed: dict[str, str], create: Callable[[str, str], object]) -> list[str]:
    """Write the seed into a store, but only if it is still empty — never overwrite team knowledge."""
    if list(existing_paths):
        return []
    for path, content in seed.items():
        create(path, content)
    return list(seed)


@dataclass(frozen=True)
class TimelineEntry:
    when: str  # e.g. "2026-05-15 14:02 UTC" (time matters: demo ingests happen same day)
    operation: str  # created | modified | deleted
    author: str
    content: str
    diff: str | None  # unified diff vs. previous version; None for the first


def build_timeline(versions, who: Callable[[str | None], str]) -> list[TimelineEntry]:
    """Turn memory-store versions (any objects with created_at/operation/content/created_by)
    into an oldest-first timeline with diffs and human attribution."""
    entries: list[TimelineEntry] = []
    previous: str | None = None
    for v in sorted(versions, key=lambda v: v.created_at):
        content = v.content or ""
        actor = v.created_by
        session_id = getattr(actor, "session_id", None) if actor else None
        # Only the seeding step writes through the API directly; people write via sessions.
        author = SEED_AUTHOR if getattr(actor, "type", None) == "api_actor" else who(session_id)
        diff = None
        if previous is not None:
            diff = "".join(
                difflib.unified_diff(
                    previous.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile="before",
                    tofile="after",
                )
            )
        entries.append(
            TimelineEntry(
                when=v.created_at.strftime("%Y-%m-%d %H:%M UTC"),
                operation=str(v.operation),
                author=author,
                content=content,
                diff=diff,
            )
        )
        previous = content
    return entries


@dataclass(frozen=True)
class Briefing:
    relevant: list[tuple[str, str]]  # (memory path, why it matters for this role)
    questions: list[str]


def parse_briefing(raw: str, known_paths: set[str]) -> Briefing:
    """Parse the model's JSON briefing, tolerating prose/code fences and dropping
    any memory path that doesn't exist in the store."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object in briefing response: {raw[:200]!r}")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid briefing JSON: {e}") from e
    relevant = [
        (item["path"], item.get("why", ""))
        for item in data.get("relevant", [])
        if item.get("path") in known_paths
    ]
    questions = [q for q in data.get("questions", []) if isinstance(q, str)]
    return Briefing(relevant=relevant, questions=questions)


def briefing_cache_key(role: str, memory_hashes: dict[str, str]) -> str:
    """Stable key that changes whenever the role or any global memory changes."""
    payload = json.dumps([role, sorted(memory_hashes.items())])
    return hashlib.sha256(payload.encode()).hexdigest()
