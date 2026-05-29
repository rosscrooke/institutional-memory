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

try:
    from dotenv import load_dotenv

    load_dotenv()  # pick up ANTHROPIC_API_KEY from a local .env if present
except ImportError:
    pass


CURATOR_SYSTEM_PROMPT = """\
You are the Memory Curator. Your only job is memory hygiene.

You have access to another agent's memory store (read/write). On each run:

1. List every entry in the store.
2. Merge any duplicates — keep the most recent version, link the others.
   In this sales context specifically: merge superseded objection answers so
   only our latest best answer per objection survives, and keep only the latest
   competitive intel per competitor (drop older, superseded intel).
3. Flag any unresolved contradictions to the operator with a short summary.
4. Prune anything that is:
   - More than 90 days old AND not referenced in a recent session
   - Ephemeral (one-off support tickets, individual conversation snippets)
   - Subsumed by a more general entry that was added later
5. Produce a one-paragraph summary of what you did.

Do NOT add new knowledge. Do NOT answer domain questions. You only clean.
"""


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    main_agent_id = Path(".agent_id").read_text().strip()

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
    session = client.beta.sessions.create(agent=curator_id)
    client.beta.sessions.events.send(
        session.id,
        events=[
            {
                "type": "user.message",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Curate the memory store of agent {main_agent_id}. "
                            "Follow your standard process. Report back when done."
                        ),
                    }
                ],
            }
        ],
    )

    print("Curator working...")
    text_parts = []
    for event in client.beta.sessions.events.stream(session.id):
        if event.type == "agent.message_delta":
            for block in event.delta.content:
                if block.type == "text_delta":
                    text_parts.append(block.text)
        if event.type == "session.status_idle":
            break

    print("\n=== CURATOR REPORT ===")
    print("".join(text_parts))


if __name__ == "__main__":
    main()
