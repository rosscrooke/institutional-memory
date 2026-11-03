"""
Load the synthetic client records into the persistent memory store.

Each file in synthetic-data/clients/<client>/ becomes one memory at
    /clients/<client>/<filename>.md
plus a top-level index at /clients/INDEX.md so agents can orient quickly.

Agents attached to the store (read_write, mounted at /mnt/memory/) will see
these as ordinary files and can search/read them to produce insights.

Safe to re-run: existing paths are updated in place, new ones are created.

Usage:
    python seed_memory_clients.py --dry-run   # show what would be written
    python seed_memory_clients.py             # write to the memory store

Requires ANTHROPIC_API_KEY (env or .env) and a .memory_store_id file.
"""

import argparse
import os
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

CLIENTS_DIR = Path("synthetic-data/clients")
MEMORY_ROOT = "/clients"


def parse_front_matter(text: str) -> dict:
    """Minimal parser for the simple `key: value` header used in the records."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    meta = {}
    if match:
        for line in match.group(1).splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip().strip('"')
    return meta


def collect_records() -> list[dict]:
    records = []
    for client_dir in sorted(p for p in CLIENTS_DIR.iterdir() if p.is_dir()):
        for path in sorted(client_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta = parse_front_matter(text)
            records.append(
                {
                    "path": f"{MEMORY_ROOT}/{client_dir.name}/{path.name}",
                    "client_slug": client_dir.name,
                    "client": meta.get("client", client_dir.name),
                    "type": meta.get("type", "unknown"),
                    "date": meta.get("date", ""),
                    "title": meta.get("title", path.stem),
                    "content": text,
                }
            )
    return records


def build_index(records: list[dict]) -> str:
    lines = [
        "# Client records index",
        "",
        "Synthetic client history (meeting transcripts, emails, Slack threads, notes).",
        "Each record is a file under /mnt/memory/clients/<client>/ with a front-matter",
        "header (client, type, date, title). Records are raw source material, ordered",
        "by filename number within each client. Later records may supersede earlier ones",
        "(dates, budgets, scope), so read in date order and trust the newest.",
        "",
    ]
    by_client: dict[str, list[dict]] = {}
    for r in records:
        by_client.setdefault(r["client"], []).append(r)
    for client, items in by_client.items():
        lines.append(f"## {client}")
        for r in sorted(items, key=lambda x: x["date"]):
            lines.append(f"- {r['date']}  [{r['type']}]  {r['title']}  ->  {r['path']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print plan, write nothing")
    args = parser.parse_args()

    load_dotenv()

    if not CLIENTS_DIR.exists():
        raise SystemExit(f"{CLIENTS_DIR} not found. Run from the repo root.")

    records = collect_records()
    payload = [(r["path"], r["content"]) for r in records]
    payload.append((f"{MEMORY_ROOT}/INDEX.md", build_index(records)))

    if args.dry_run:
        print(f"[dry run] {len(payload)} memories would be written:")
        for path, content in payload:
            print(f"  {path}  ({len(content)} chars)")
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")
    store_id_path = Path(".memory_store_id")
    if not store_id_path.exists():
        raise SystemExit("Missing .memory_store_id (get it from the team, or see create_agent.py).")
    store_id = store_id_path.read_text().strip()

    client = Anthropic()
    print(f"Memory store: {store_id}")

    existing = {}
    for item in client.beta.memory_stores.memories.list(store_id, path_prefix=f"{MEMORY_ROOT}/"):
        if item.type == "memory":
            existing[item.path] = item.id

    created = updated = 0
    for path, content in payload:
        if path in existing:
            client.beta.memory_stores.memories.update(
                existing[path], memory_store_id=store_id, content=content
            )
            updated += 1
            print(f"  updated  {path}")
        else:
            client.beta.memory_stores.memories.create(store_id, path=path, content=content)
            created += 1
            print(f"  created  {path}")

    print(f"\nDone: {created} created, {updated} updated.")
    print("Verify with:  python inspect_memory.py")


if __name__ == "__main__":
    main()
