"""
Stretch goal S8 (part 1): snapshot the agent's memory store to a JSON file.

Lists every memory in the store (same list+retrieve pattern as inspect_memory.py)
and writes a path -> content map to outputs/memory_snapshot_<label>.json.

Take one snapshot after session 1 and another after session 2, then run
memory_diff.py to see EXACTLY what the agent learned between calls. That diff is
the demo headline: "here is the institutional memory the agent built."

Usage:
    python memory_snapshot.py after_session1
    python memory_snapshot.py after_session2
    python memory_snapshot.py after_session2 --customer globex   # S5 per-tenant store
"""

import argparse
import json
import os
from pathlib import Path

from anthropic import Anthropic

try:
    from dotenv import load_dotenv

    load_dotenv()  # pick up ANTHROPIC_API_KEY from a local .env if present
except ImportError:
    pass


OUTPUT_DIR = Path("outputs")


def resolve_store_id(customer: str | None) -> str:
    """Find the memory store id to snapshot.

    Default: .memory_store_id (the most recently created store, what the
    run_session_* scripts use). With --customer, read the per-tenant
    .memory_store_<customer> file (stretch goal S5).
    """
    if customer:
        store_file = Path(f".memory_store_{customer.strip().lower()}")
        if not store_file.exists():
            raise SystemExit(
                f"Missing {store_file}. Run "
                f"`python create_agent.py --customer {customer}` first."
            )
        return store_file.read_text().strip()

    store_file = Path(".memory_store_id")
    if not store_file.exists():
        raise SystemExit("Missing .memory_store_id. Run create_agent.py first.")
    return store_file.read_text().strip()


def snapshot_store(client: Anthropic, store_id: str) -> dict:
    """Return {path: {id, content, chars}} for every memory in the store."""
    page = client.beta.memory_stores.memories.list(
        store_id,
        path_prefix="/",
        order_by="path",
    )

    memories: dict[str, dict] = {}
    for item in page.data:
        # `item.type` is "memory" for files (or "directory" for nested dirs).
        # We snapshot only files — directories carry no content of their own.
        if item.type != "memory":
            continue

        retrieved = client.beta.memory_stores.memories.retrieve(
            item.id, memory_store_id=store_id
        )
        content = retrieved.content or ""
        memories[item.path] = {
            "id": item.id,
            "content": content,
            "chars": len(content),
        }
    return memories


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Snapshot the agent's memory store to outputs/memory_snapshot_<label>.json"
    )
    parser.add_argument(
        "label",
        help="A name for this snapshot, e.g. after_session1. Used in the filename.",
    )
    parser.add_argument(
        "--customer",
        default=None,
        help="Snapshot a per-customer store (.memory_store_<customer>) instead of "
        "the default .memory_store_id (stretch goal S5).",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    store_id = resolve_store_id(args.customer)
    client = Anthropic()

    print(f"Snapshotting memory store {store_id} ...")
    memories = snapshot_store(client, store_id)

    snapshot = {
        "label": args.label,
        "store_id": store_id,
        "customer": args.customer,
        "memory_count": len(memories),
        # Sorted keys -> stable file -> clean diffs.
        "memories": dict(sorted(memories.items())),
    }

    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / f"memory_snapshot_{args.label}.json"
    out.write_text(json.dumps(snapshot, indent=2, sort_keys=True))

    if not memories:
        print("(memory store is empty - has a session been run yet?)")
    else:
        print(f"Captured {len(memories)} memories:")
        for path, entry in snapshot["memories"].items():
            print(f"  {path}  ({entry['chars']} chars)")

    print(f"\nSaved snapshot to {out}")
    print("Compare two snapshots with:  python memory_diff.py <before> <after>")


if __name__ == "__main__":
    main()
