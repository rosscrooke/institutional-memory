"""
Session "what have you learned?" (S4).

Same agent, same memory store, fresh session — but no new documents are
attached. The single user message asks the agent to summarise everything
it has learned about this domain across previous sessions. This is the
memory store "talking back."

Output: outputs/session_learned.txt

Usage:
    python run_session_learned.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


USER_MESSAGE = (
    "No new documents this session. Please read your memory store at "
    "/mnt/memory/ and summarise everything you have learned about this "
    "domain across our previous sessions.\n\n"
    "Cover at minimum:\n"
    "- The prospect: who they are, their environment, scale, constraints.\n"
    "- The people on the prospect side and what each cares about.\n"
    "- Every objection on record and the latest best answer for each.\n"
    "- The competitive landscape and the latest intel.\n"
    "- The current pitch strategy and the most recent revisions to it.\n"
    "- Anything else worth knowing for the next call.\n\n"
    "Be specific. Cite dates where you have them. Flag anything in memory "
    "that looks stale or contradictory."
)

OUTPUT_DIR = Path("outputs")


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

    print(f"Starting 'what have you learned?' session with memory store {memory_store_id}...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="Session learned — memory recap, no new docs",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is your persistent institutional memory. No new "
                    "documents are attached this session. Read memory and "
                    "summarise what you have learned across prior sessions."
                ),
            }
        ],
    )

    final_text_parts: list[str] = []
    print("\nAgent working...\n")
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": USER_MESSAGE}],
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
    out = OUTPUT_DIR / "session_learned.txt"
    out.write_text(
        f"=== SESSION LEARNED ===\nPrompt: summarise everything you've learned.\n\n--- ANSWER ---\n{final_text}\n"
    )
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
