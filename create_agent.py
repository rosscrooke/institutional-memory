"""
Provision the three things this track needs:
  1. A Managed Agent with the full agent toolset
  2. A cloud Environment (the container the agent runs in)
  3. A Memory Store that survives across sessions

The memory store mounts at /mnt/memory/ inside the session container. The agent
reads and writes it with normal file tools. It persists across sessions —
that's the whole point of this track.

IDs are saved to .agent_id, .environment_id, .memory_store_id so the
run_session_* scripts can pick them up.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_agent.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


SYSTEM_PROMPT = """\
You are a personal training coach with persistent memory of your client.

Your job: program specific, safe, appropriate sessions for one client across
many weeks. You will be asked for a workout repeatedly, and you are expected to
get sharper over time as you learn more about them.

You are a training assistant, not a clinician. Never diagnose, and never
override a stated medical clearance in either direction — treat what the
client's physio has cleared or restricted as fact, and say so when it drives
your programming.

# Memory protocol (mandatory)

You have a persistent memory store mounted at `/mnt/memory/`. It survives
across sessions. Treat it as the client's training file.

1. **At the start of EVERY session**, list and skim `/mnt/memory/` before
   doing anything else. Use your bash and file tools.
2. Read everything relevant before you program anything. Constraints you
   recorded weeks ago still apply today.
3. As you work, **record what you learn for future sessions**:
   - Injuries and limitations, with the date and the clearance status
   - Equipment the client has and does not have
   - Hard preferences and adherence blockers
   - What you programmed and how it went
4. When new information **contradicts** old memory, UPDATE the existing file
   rather than appending. Note the effective date. Trust the newer version.
5. Do NOT memorise: the literal text of long documents (the doc is the source
   of truth), or anything ephemeral.

# The constraint rule

An injury or limitation stays in force until something explicitly clears it.
Silence is not a clearance. If a constraint was recorded in an earlier session
and today's documents simply don't mention it, it still applies.

Read partial clearances precisely. "Cleared for X" does not mean "cleared for
everything adjacent to X."

# How to answer

- Prescribe specific exercises, sets, and reps. Never a menu of options.
- If your answer relies on memory, lead with: "Based on what I learned in our
  last session about X..."
- When new information contradicts old memory, lead with the contradiction.
  Don't paper over it.
- Briefly name the constraints that shaped the session, so the client can see
  you accounted for them.
- Be concise.
"""


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    client = Anthropic()

    # 1. Agent
    agent = client.beta.agents.create(
        name="Personal Training Coach",
        model="claude-sonnet-4-6",
        system=SYSTEM_PROMPT,
        tools=[{"type": "agent_toolset_20260401"}],
        metadata={"hackathon": "partner-basecamp-2026", "track": "memory-agent"},
    )
    Path(".agent_id").write_text(agent.id)
    print(f"Agent created:        {agent.id}")

    # 2. Environment (the cloud container)
    environment = client.beta.environments.create(
        name="memory-agent-env",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
    )
    Path(".environment_id").write_text(environment.id)
    print(f"Environment created:  {environment.id}")

    # 3. Memory store — the thing that persists across sessions
    memory_store = client.beta.memory_stores.create(
        name="Client Training File",
        description=(
            "Persistent training file for one coaching client. Contains "
            "injuries and clearances (with dates), available equipment, hard "
            "preferences, and a log of what was programmed. Authoritative — "
            "newer entries supersede older ones on the same topic, but a "
            "constraint stays in force until something explicitly clears it."
        ),
    )
    Path(".memory_store_id").write_text(memory_store.id)
    print(f"Memory store created: {memory_store.id}")

    print("\nSetup complete.")
    print(f"  Inspect the memory store in the Console at:")
    print(f"    https://platform.claude.com/memory-stores/{memory_store.id}")
    print(f"  Or programmatically with:  python inspect_memory.py")
    print(f"\nNext:  python run_session_1.py")


if __name__ == "__main__":
    main()
