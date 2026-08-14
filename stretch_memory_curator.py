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


CURATOR_SYSTEM_PROMPT = """\
You are the Memory Curator. Your only job is memory hygiene.

You have access to another agent's memory store (read/write). On each run:

1. List every entry in the store.
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
    #
    # The session needs an environment to run in, and — less obviously — the memory
    # store has to be attached as a resource. The user message asks the curator to
    # curate "the memory store of agent X", but nothing mounts it, so there would be
    # nothing at /mnt/memory/ to read. Fixing only the missing environment_id gives a
    # curator that runs, reports success, and has read nothing.
    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()
    session = client.beta.sessions.create(
        agent=curator_id,
        environment_id=environment_id,
        title="Memory curation pass",
        resources=[{
            "type": "memory_store",
            "memory_store_id": memory_store_id,
            "access": "read_write",
            "instructions": (
                "The memory store you are curating. Merge duplicates, flag "
                "unresolved contradictions, prune what is no longer load-bearing."
            ),
        }],
    )
    print("Curator working...")
    text_parts, memory_ops = [], []

    # Open the stream before sending, as run_session_1.py and run_session_2.py do.
    # Sending first and then iterating `stream(...)` directly loses the reply, and the
    # report prints empty — which reads exactly like a curator that found nothing to
    # do. Handles agent.message as well as agent.message_delta, since the delta event
    # did not fire here.
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": (
                    f"Curate the memory store of agent {main_agent_id}. "
                    "Follow your standard process. Report back when done."
                )}],
            }],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        text_parts.append(block.text)
            elif event.type == "agent.message_delta":
                for block in event.delta.content:
                    if block.type == "text_delta":
                        text_parts.append(block.text)
            elif event.type == "agent.tool_use":
                inp = getattr(event, "input", {}) or {}
                target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
                if "/mnt/memory" in str(target):
                    memory_ops.append(f"{getattr(event, 'name', '?')} {target}")
                    print(f"  [memory: {getattr(event, 'name', '?')}  {target}]", flush=True)
            elif event.type == "session.status_idle":
                break

    print("\n=== CURATOR REPORT ===")
    print("".join(text_parts) or "(the curator returned no text)")
    print(f"\nMemory operations: {len(memory_ops)}")


if __name__ == "__main__":
    main()
