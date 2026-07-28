"""
Stretch goal: the Memory Curator sub-agent.

After multiple sessions, the main agent's memory store can become messy —
duplicates, stale facts, contradictions that were never resolved.

This script creates a SECOND agent whose only job is to curate memory:
- Read the main agent's memory store
- Merge duplicates
- Flag unresolved contradictions
- Prune anything that's no longer load-bearing

The curator gets the SAME memory store attached as a read_write resource, so it
operates on /mnt/memory/ exactly like the main agent does. It reuses the
environment created by create_agent.py.

In a real system, you'd run this on a schedule (a Routine!).

Usage:
    python stretch_memory_curator.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


CURATOR_SYSTEM_PROMPT = """\
You are the Memory Curator. Your only job is memory hygiene.

You have read/write access to another agent's memory store, mounted inside your
session container under `/mnt/memory/`. On each run:

1. List every entry under `/mnt/memory/` using your bash and file tools.
2. Merge any duplicates — keep the most recent version, link the others.
3. Flag any unresolved contradictions to the operator with a short summary.
4. Prune anything that is:
   - More than 90 days old AND not referenced in a recent session
   - Ephemeral (one-off support tickets, individual conversation snippets)
   - Subsumed by a more general entry that was added later
5. Produce a one-paragraph summary of what you did.

Do NOT add new knowledge. Do NOT answer domain questions. You only clean.
"""


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".agent_id", ".environment_id", ".memory_store_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required}. Run create_agent.py first.")

    main_agent_id = Path(".agent_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    client = Anthropic()

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

    # Run a curation session against the SAME memory store the main agent uses.
    # In production this would be a scheduled Routine.
    print(f"\nStarting curation session on memory store {memory_store_id}...")
    session = client.beta.sessions.create(
        agent=curator_id,
        environment_id=environment_id,
        title="Memory curation pass",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is the Institutional Memory Agent's store. Curate it: "
                    "merge duplicates, flag unresolved contradictions, prune "
                    "anything stale or ephemeral. Do not add new knowledge."
                ),
            }
        ],
    )

    print("\nCurator working...\n")
    text_parts: list[str] = []
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Curate the memory store mounted at /mnt/memory/. "
                                "Follow your standard process. Report back when done."
                            ),
                        }
                    ],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        text_parts.append(block.text)
                        print(block.text, end="", flush=True)
            elif event.type == "agent.tool_use":
                name = getattr(event, "name", "?")
                inp = getattr(event, "input", {}) or {}
                target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
                if "/mnt/memory" in str(target):
                    print(f"\n  [memory: {name}  {target}]", flush=True)
                else:
                    print(f"\n  [{name}]", flush=True)
            elif event.type == "session.status_terminated":
                break
            elif event.type == "session.status_idle":
                # The session goes idle transiently; only a non-"requires_action"
                # stop reason means the curator is actually done.
                stop_reason = getattr(event, "stop_reason", None)
                if getattr(stop_reason, "type", None) == "requires_action":
                    continue
                break

    print("\n\n=== CURATOR REPORT ===")
    print("".join(text_parts))
    print(f"\nInspect the curated store:  python inspect_memory.py")


if __name__ == "__main__":
    main()
