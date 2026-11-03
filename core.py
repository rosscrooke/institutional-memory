"""
Core utilities for the Institutional Memory app.

Schemas:
- Item: {id, title, source ("upload"|"text"|"slack"), text, tags: [], category, summary_short, summary_long, created_at}
- Task: {id, item_id, title, priority ("High"|"Med"|"Low"), owner ("me"|"agent"), status ("open"|"drafting"|"done"), draft, created_at}
- Feedback: {id, target ("chat"|"digest"|...), rating (1|-1), comment, created_at}
- Log event: {ts, agent, action, status ("running"|"done"|"error"), detail}
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()


def get_client() -> Anthropic:
    """Return Anthropic client with API key from .env."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in .env")
    return Anthropic(api_key=api_key)


def ask_claude(prompt: str, system: str = "") -> str:
    """
    Fast single Messages API call for categorizing, summarizing, prioritizing, drafting.
    Model: ANTHROPIC_MODEL from .env (default claude-haiku-4-5).
    Returns the final text response.
    """
    client = get_client()
    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5"),
        max_tokens=1024,
        system=system if system else "You are a helpful assistant.",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def run_memory_session(message: str, title: str = "Session") -> str:
    """
    Managed Agent session with memory store attached (slow; starts a container).
    Use only for ingesting content into memory and chat answers.
    Returns the final agent text response.
    """
    client = get_client()

    # Load IDs from files
    agent_id = Path(".agent_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    # Start session with memory store
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title=title,
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is your persistent institutional memory. Mounted at /mnt/memory/. "
                    "Check it before starting. Record what you learn for future sessions."
                ),
            }
        ],
    )

    # Stream the response
    final_text_parts: list[str] = []
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": message}]}],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        final_text_parts.append(block.text)
            elif event.type == "session.status_idle":
                break

    return "".join(final_text_parts)


def save_json(folder: str, record: dict) -> str:
    """
    Save a record to data/<folder>/<id>.json.
    Generates id (uuid) and created_at if missing.
    Returns the id.
    """
    if "id" not in record:
        record["id"] = str(uuid.uuid4())
    if "created_at" not in record:
        record["created_at"] = datetime.now().isoformat()

    path = Path("data") / folder
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{record['id']}.json"
    file_path.write_text(json.dumps(record, indent=2))
    return record["id"]


def load_all(folder: str) -> list[dict]:
    """Read every JSON in data/<folder>/, newest first."""
    path = Path("data") / folder
    if not path.exists():
        return []

    records = []
    for file_path in sorted(path.glob("*.json"), reverse=True):
        try:
            records.append(json.loads(file_path.read_text()))
        except (json.JSONDecodeError, IOError):
            pass
    return records


def update_json(folder: str, id: str, changes: dict) -> None:
    """Update a record by id with the given changes."""
    path = Path("data") / folder / f"{id}.json"
    if not path.exists():
        raise ValueError(f"Record not found: {path}")

    record = json.loads(path.read_text())
    record.update(changes)
    path.write_text(json.dumps(record, indent=2))


def log_event(agent: str, action: str, status: str, detail: str = "") -> None:
    """
    Append a log event to data/logs/<agent>.jsonl.
    Status: "running", "done", "error".
    """
    path = Path("data/logs")
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{agent}.jsonl"

    event = {
        "ts": datetime.now().isoformat(),
        "agent": agent,
        "action": action,
        "status": status,
        "detail": detail,
    }
    with open(file_path, "a") as f:
        f.write(json.dumps(event) + "\n")


def read_logs() -> list[dict]:
    """Read all log lines from data/logs/*.jsonl, merged and sorted newest first."""
    path = Path("data/logs")
    if not path.exists():
        return []

    all_events = []
    for file_path in path.glob("*.jsonl"):
        try:
            for line in file_path.read_text().strip().split("\n"):
                if line:
                    all_events.append(json.loads(line))
        except (json.JSONDecodeError, IOError):
            pass

    # Sort by ts, newest first
    all_events.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return all_events


def list_memory() -> dict[str, str]:
    """
    List memory store contents.
    Returns {path: content} dict for the monitoring panel.
    """
    client = get_client()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    result = {}
    try:
        memories = client.beta.memory_stores.memories.list(memory_store_id)
        for memory in memories.data:
            result[memory.id] = memory.content
    except Exception:
        pass

    return result
