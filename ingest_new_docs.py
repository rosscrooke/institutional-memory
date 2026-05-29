"""
S6 — Memory + scheduled ingestion ("Routines").

Passive memory growth: drop new docs into synthetic-data/inbox/, and on each
run this script ingests every unseen .md into the agent's memory store, then
moves the file to synthetic-data/processed/. The move IS the "seen" marker —
only files still in inbox/ are unprocessed, so re-runs are idempotent.

There is no documented standalone Routines API at the time of writing (the
routines doc 404s). If client.beta.routines.* exists in your installed SDK at
run time, PREFER wrapping the ingestion session in that native primitive
instead of the OS scheduler — see the guard in main().

# SCHEDULING (run daily, externally)
#
# Windows Task Scheduler (one line; adjust paths):
#   schtasks /create /tn "helios-ingest" ^
#     /tr "python C:\path\to\repo\ingest_new_docs.py" ^
#     /sc daily /st 07:00
#
# cron (Linux/macOS) — daily at 07:00:
#   0 7 * * * cd /path/to/repo && /usr/bin/python ingest_new_docs.py >> ingest.log 2>&1

Usage:
    python ingest_new_docs.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


INBOX = Path("synthetic-data/inbox")
PROCESSED = Path("synthetic-data/processed")


def ingest_one(client: Anthropic, agent_id: str, environment_id: str,
               memory_store_id: str, doc_path: Path) -> None:
    """Run a short session that folds one doc into /mnt/memory/."""
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title=f"Ingest — {doc_path.name}",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is your persistent institutional memory at "
                    "/mnt/memory/. Fold the document below into it following "
                    "your memory protocol — update existing entries on conflict, "
                    "note dates, don't store verbatim doc text."
                ),
            }
        ],
    )

    message = (
        "A new document has arrived for ingestion. Check /mnt/memory/, then "
        "record anything worth remembering from this document. Be concise; "
        "reply with a one-line summary of what you saved.\n\n"
        f"=====  DOCUMENT: {doc_path.name}  =====\n{doc_path.read_text()}"
    )

    print(f"  ingesting {doc_path.name} ...", flush=True)
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": message}]}],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        print(block.text, end="", flush=True)
            elif event.type == "session.status_idle":
                break
    print()


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".agent_id", ".environment_id", ".memory_store_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required}. Run create_agent.py first.")

    agent_id = Path(".agent_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    INBOX.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    pending = sorted(INBOX.glob("*.md"))
    if not pending:
        print(f"Inbox {INBOX}/ is empty — nothing to ingest. (no-op)")
        return

    client = Anthropic()

    # If a native Routines API ever ships, prefer it over the OS scheduler.
    if hasattr(client.beta, "routines"):
        print(
            "NOTE: client.beta.routines is available in this SDK — consider "
            "wrapping ingestion in the native Routines API instead of cron/"
            "Task Scheduler. Proceeding with the manual session for now."
        )

    print(f"Found {len(pending)} doc(s) in {INBOX}/")
    for doc_path in pending:
        ingest_one(client, agent_id, environment_id, memory_store_id, doc_path)
        dest = PROCESSED / doc_path.name
        doc_path.rename(dest)
        print(f"  moved -> {dest}")

    print("\nDone. Inspect what was learned:  python inspect_memory.py")


if __name__ == "__main__":
    main()
