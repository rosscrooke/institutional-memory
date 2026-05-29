"""
Session 1 — Baseline (Helios deal, first prep call).

Starts a Managed Agents session with the memory store ATTACHED so the agent
can read and write /mnt/memory/. Inlines the round1 docs (the prospect's stack
overview, objection log, and current pitch deck) in the user message.

After this session, inspect the memory store to see what the agent saved:
    python inspect_memory.py
or in the Console UI under Memory Stores.

Usage:
    python run_session_1.py
"""

import os
from pathlib import Path

from anthropic import Anthropic

try:
    from dotenv import load_dotenv

    load_dotenv()  # pick up ANTHROPIC_API_KEY from a local .env if present
except ImportError:
    pass


TEST_QUESTION = "Tomorrow's call is the final pitch. What's our strategy?"

DOCS_DIR = Path("synthetic-data/round1")
OUTPUT_DIR = Path("outputs")


def load_docs_as_context(docs_dir: Path) -> str:
    blocks = []
    for path in sorted(docs_dir.glob("*.md")):
        print(f"  including {path.name}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    return "\n\n".join(blocks)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".agent_id", ".environment_id", ".memory_store_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required}. Run create_agent.py first.")

    agent_id = Path(".agent_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    client = Anthropic()

    print(f"Loading round1 docs from {DOCS_DIR}/...")
    context = load_docs_as_context(DOCS_DIR)

    print(f"\nStarting session with memory store {memory_store_id} attached...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="Session 1 — baseline",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is your persistent institutional memory. Mounted at "
                    "/mnt/memory/. Check it before starting. Record what you "
                    "learn for future sessions."
                ),
            }
        ],
    )

    user_message = (
        "I'm including the prospect's stack overview, objection log, and current "
        "pitch deck below. Please:\n"
        "1. First, check your memory store at /mnt/memory/ to see what you've "
        "learned in previous sessions.\n"
        "2. Then read the documents below.\n"
        "3. Then answer the question.\n"
        "4. Before you finish, save anything worth remembering to /mnt/memory/.\n\n"
        f"{context}\n\n"
        "==================================================\n"
        f"QUESTION: {TEST_QUESTION}"
    )

    final_text_parts: list[str] = []
    print("\nAgent working...\n")
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": user_message}],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        final_text_parts.append(block.text)
                        print(block.text, end="", flush=True)
            elif event.type == "agent.tool_use":
                # Show file ops on /mnt/memory/ in particular — that's the demo
                name = getattr(event, "name", "?")
                inp = getattr(event, "input", {}) or {}
                target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
                if "/mnt/memory" in str(target):
                    print(f"\n  [memory: {name}  {target}]", flush=True)
                else:
                    print(f"\n  [{name}]", flush=True)
            elif event.type == "session.status_idle":
                print("\n\n[agent finished]")
                break

    final_text = "".join(final_text_parts)
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / "session1.txt"
    out.write_text(
        f"=== SESSION 1 ===\nQuestion: {TEST_QUESTION}\n\n--- ANSWER ---\n{final_text}\n"
    )
    print(f"\nSaved to {out}")
    print(f"\nInspect what the agent remembered:  python inspect_memory.py")
    print(f"Then run run_session_2.py.")


if __name__ == "__main__":
    main()
