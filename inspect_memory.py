"""
List every memory in the agent's memory store, with content previews.

This is your demo helper — run it between sessions to see what the agent has
chosen to remember. Great for the live demo (three terminals: session 1
output, session 2 output, this).

Usage:
    python inspect_memory.py              # list with previews
    python inspect_memory.py --full       # full content of every memory
"""

import os
import sys
from pathlib import Path

from anthropic import Anthropic


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    store_id_path = Path(".memory_store_id")
    if not store_id_path.exists():
        raise SystemExit("Missing .memory_store_id. Run create_agent.py first.")
    store_id = store_id_path.read_text().strip()

    full = "--full" in sys.argv

    client = Anthropic()

    print(f"Memory store: {store_id}\n" + "=" * 60)

    page = client.beta.memory_stores.memories.list(
        store_id,
        path_prefix="/",
        order_by="path",
    )

    items = list(page.data)
    if not items:
        print("(memory store is empty — has run_session_1.py been run?)")
        return

    for item in items:
        # `item.type` is "memory" for files (or "directory" for nested dirs)
        if item.type != "memory":
            print(f"\n[dir] {item.path}")
            continue

        retrieved = client.beta.memory_stores.memories.retrieve(
            item.id, memory_store_id=store_id
        )
        content = retrieved.content or ""

        print(f"\n--- {item.path}  ({len(content)} chars) ---")
        if full:
            print(content)
        else:
            preview = content[:400]
            print(preview + ("..." if len(content) > 400 else ""))


if __name__ == "__main__":
    main()
