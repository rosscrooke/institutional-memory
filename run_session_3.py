"""
Session 3 — Adversarial round (S3).

Same agent, same memory store, fresh session. Round3 docs contradict round1 —
but unlike round2, they carry NO effective date, NO author, and NO stated
reason. The expected correct behaviour is for the agent to FLAG the conflict
and ASK which to trust, not silently overwrite memory.

If the agent overwrites without challenge, harden create_agent.py's
flag-and-ask rule (S3) and re-run.

Usage:
    python run_session_3.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


TEST_QUESTION = (
    "Tomorrow's call is the final pitch. What's our strategy?"
)

DOCS_DIR = Path("synthetic-data/round3")
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

    print(f"Loading round3 (adversarial) docs from {DOCS_DIR}/...")
    context = load_docs_as_context(DOCS_DIR)

    print(f"\nStarting fresh session with same memory store {memory_store_id}...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="Session 3 — adversarial / undated contradictions",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is your persistent institutional memory. The documents "
                    "in this session contradict prior memory but carry no "
                    "effective date and no stated reason. Do NOT silently "
                    "overwrite memory — flag the conflict and ask which to "
                    "trust."
                ),
            }
        ],
    )

    user_message = (
        "I'm including some new documents below. They contradict things you "
        "learned in our previous sessions.\n\n"
        "Important: these documents carry no effective date, no author, and "
        "no stated reason for the change.\n\n"
        "Please:\n"
        "1. First, check your memory store at /mnt/memory/ to see what you "
        "already know about this prospect.\n"
        "2. Read the new documents below.\n"
        "3. RECONCILE these against memory. Where a new document contradicts "
        "memory but offers no effective date and no reason, FLAG the conflict "
        "explicitly and ASK which to trust. Do not overwrite memory silently.\n"
        "4. Once you have flagged the conflicts, answer the question using "
        "whichever source you judge most reliable, and say which you chose "
        "and why.\n\n"
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
    out = OUTPUT_DIR / "session3.txt"
    out.write_text(
        f"=== SESSION 3 (adversarial) ===\nQuestion: {TEST_QUESTION}\n\n--- ANSWER ---\n{final_text}\n"
    )
    print(f"\nSaved to {out}")
    print(
        "\nExpected: the agent flagged the undated contradictions and asked "
        "which to trust, rather than silently overwriting memory."
    )
    print("Inspect memory:  python inspect_memory.py")


if __name__ == "__main__":
    main()
