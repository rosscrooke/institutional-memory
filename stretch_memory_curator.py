"""
Stretch goal: the Memory Curator sub-agent.

After multiple sessions, the main agent's memory store can become messy —
duplicates, stale facts, contradictions that were never resolved.

This script creates a SECOND agent whose only job is to curate memory:
- Read the main agent's memory store
- Merge duplicates
- Flag unresolved contradictions
- Prune anything that's no longer load-bearing

In a real system, you'd run this on a schedule (a Routine!).

Usage:
    python stretch_memory_curator.py
"""

import os
from pathlib import Path

from anthropic import Anthropic

from prompts import CURATOR_SYSTEM_PROMPT, CURATOR_TASK_MESSAGE


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".agent_id", ".environment_id", ".memory_store_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required}. Run create_agent.py first.")

    main_agent_id = Path(".agent_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    client = Anthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    # Create the curator agent if it doesn't exist
    curator_path = Path(".curator_agent_id")
    if curator_path.exists():
        curator_id = curator_path.read_text().strip()
        print(f"Reusing curator agent {curator_id}")
    else:
        curator = client.beta.agents.create(
            name="Memory Curator",
            model="claude-haiku-4-5-20251001",  # Fast, cheap, sufficient for housekeeping
            system=CURATOR_SYSTEM_PROMPT,
            tools=[
                {"type": "agent_toolset_20260401"},
            ],
            metadata={
                "role": "memory-curator",
                "for_agent": main_agent_id,
                "hackathon": "partner-basecamp-2026",
            },
        )
        curator_id = curator.id
        curator_path.write_text(curator_id)
        print(f"Curator agent created: {curator_id}")

    # Run a curation session. In production this would be a scheduled Routine.
    # The memory store must be attached, otherwise /mnt/memory/ doesn't exist.
    session = client.beta.sessions.create(
        agent=curator_id,
        environment_id=environment_id,
        title="Memory curation",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": "The memory store you are curating.",
            }
        ],
    )

    print("Curator working...")
    text_parts = []
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": CURATOR_TASK_MESSAGE}],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        text_parts.append(block.text)
            elif event.type == "agent.tool_use":
                inp = getattr(event, "input", {}) or {}
                target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
                print(f"  [{getattr(event, 'name', '?')}  {target}]", flush=True)
            elif event.type == "session.status_idle":
                break

    print("\n=== CURATOR REPORT ===")
    print("".join(text_parts))


if __name__ == "__main__":
    main()
