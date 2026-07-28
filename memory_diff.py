"""
Show what the agent actually changed in memory between session 1 and session 2.

Session 1 and session 2 both write to the same memory store, so "the agent
learned something" is otherwise just a claim you have to take on faith from
reading two separate answers. This script makes it literal: for every memory
file, it pairs the version as it stood at the end of session 1 against the
version as it stood at the end of session 2, and prints a real diff.

Uses `memory_stores.memory_versions.list(..., session_id=...)` to pull the
version history scoped to each session — no extra model calls.

Requires .session1_id and .session2_id, which run_session_1.py / run_session_2.py
write out after creating their sessions.

Usage:
    python memory_diff.py
"""

import difflib
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


def _read_required(path: str, hint: str) -> str:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Missing {path}. {hint}")
    return p.read_text().strip()


def _latest_content(client: Anthropic, store_id: str, memory_id: str, session_id: str) -> str | None:
    """Newest version of `memory_id` written during `session_id`, or None if none exists."""
    versions = client.beta.memory_stores.memory_versions.list(
        store_id,
        memory_id=memory_id,
        session_id=session_id,
        view="full",
    )
    for version in versions.data:
        if version.operation == "deleted":
            return None
        return version.content or ""
    return None


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    store_id = _read_required(".memory_store_id", "Run create_agent.py first.")
    session1_id = _read_required(".session1_id", "Run run_session_1.py first.")
    session2_id = _read_required(".session2_id", "Run run_session_2.py first.")

    client = Anthropic()

    page = client.beta.memory_stores.memories.list(store_id, path_prefix="/")
    memories = sorted(
        (item for item in page.data if item.type == "memory"),
        key=lambda item: item.path,
    )
    if not memories:
        print("(memory store is empty — has run_session_1.py been run?)")
        return

    changed_any = False
    for item in memories:
        before = _latest_content(client, store_id, item.id, session1_id)
        after = _latest_content(client, store_id, item.id, session2_id)

        if after is None:
            continue  # session 2 didn't touch this memory — nothing to show
        if before == after:
            continue  # session 2 wrote it but content didn't actually change

        changed_any = True
        diff = difflib.unified_diff(
            (before or "").splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{item.path} (after session 1)",
            tofile=f"{item.path} (after session 2)",
        )
        print(f"\n{'=' * 60}\n{item.path}\n{'=' * 60}")
        print("".join(diff) or "(no line-level diff — only whitespace changed)")

    if not changed_any:
        print("No memory files changed between session 1 and session 2.")


if __name__ == "__main__":
    main()
