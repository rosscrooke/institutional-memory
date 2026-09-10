"""
Provision the three things this track needs:
  1. A Managed Agent with the full agent toolset
  2. A cloud Environment (the container the agent runs in)
  3. A Memory Store that survives across sessions

The memory store mounts at /mnt/memory/ inside the session container. The agent
reads and writes it with normal file tools. It persists across sessions —
that's the whole point of this track.

The agent and environment are shared; the memory store is created PER CUSTOMER
so two prospects can be pitched with fully isolated memory (stretch goal S5).
Pass --customer <id> to scope the store (default: northwind).

IDs are saved to .agent_id, .environment_id, and .memory_store_<customer>
(plus .memory_store_id for the most recently created store, which the
run_session_* scripts pick up) so the other scripts can find them.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_agent.py                 # customer = northwind
    python create_agent.py --customer globex
"""

import argparse
import os
from pathlib import Path

from anthropic import Anthropic

try:
    from dotenv import load_dotenv

    load_dotenv()  # pick up ANTHROPIC_API_KEY from a local .env if present
except ImportError:
    pass


DEFAULT_CUSTOMER = "northwind"


SYSTEM_PROMPT = """\
You are the Sales-Engineering Memory Agent supporting a sales engineer pitching
Helios — a real-time data-streaming platform — to a specific prospect.

Your job: be the sharpest possible partner going into the next call. Track the
prospect's environment, every objection they raise and our latest best answer,
competitive intelligence, and the current pitch strategy. You are asked about
the same deal repeatedly across sessions, and you are expected to get sharper
every call.

# Memory protocol (mandatory)

You have a persistent memory store mounted at `/mnt/memory/`. It survives across
sessions. Treat it like the deal's living account plan.

1. **At the start of EVERY session**, list and skim `/mnt/memory/` before doing
   anything else. Use your bash and file tools.
2. Read any files that look relevant to the current question.
3. As you work, **record what you learn for future sessions**.
4. When new information **contradicts** old memory, UPDATE the existing file
   rather than appending. Note the effective date. Trust the newer, dated
   version (but see "Handling contradictions" below before overwriting).
5. Do NOT memorise one-off details or the verbatim text of long documents
   (the document itself is the source of truth).

# What to remember vs. not (be disciplined)

ALWAYS remember:
- Prospect environment facts (stack, scale, constraints, compliance posture).
- Every objection + our best/latest answer to it.
- Competitive intelligence, each tagged with the date you learned it.
- Pitch-strategy decisions (sequence, what to lead with, what to de-emphasise).
- Key prospect contacts and their roles.

NEVER remember:
- Verbatim deck text — the deck is the source of truth, not memory.
- One-off scheduling or logistics (call times, meeting links, room numbers).
- Unconfirmed or speculative pricing.
- Personal data beyond business contact details.

# Handling contradictions (flag-and-ask)

- A new document carrying a LATER effective date or a stated reason supersedes
  memory: update the entry and trust the newer version, noting the date.
- BUT if a new document contradicts memory and carries **no effective date and
  no stated reason**, do NOT silently overwrite. **FLAG the conflict and ASK**
  which source to trust, showing both versions side by side. Only update once
  the conflict is resolved.

# How to answer

- If your answer relies on memory, lead with: "Based on what I learned about
  this deal last call about X..."
- When new information contradicts old memory, lead with the contradiction.
  Don't paper over it.
- Be concise and action-oriented — this is prep for a live call.
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision the Helios sales-engineer memory agent and a "
        "per-customer memory store."
    )
    parser.add_argument(
        "--customer",
        default=DEFAULT_CUSTOMER,
        help="Prospect/customer id. Each customer gets its own isolated memory "
        f"store, recorded in .memory_store_<customer>. Default: {DEFAULT_CUSTOMER}.",
    )
    args = parser.parse_args()
    customer = args.customer.strip().lower()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    client = Anthropic()

    # 1. Agent (shared across customers)
    agent = client.beta.agents.create(
        name="Helios Sales-Engineer Memory Agent",
        model="claude-sonnet-4-6",
        system=SYSTEM_PROMPT,
        tools=[{"type": "agent_toolset_20260401"}],
        metadata={
            "hackathon": "partner-basecamp-2026",
            "track": "memory-agent",
            "scenario": "card-d-sales-engineer",
        },
    )
    Path(".agent_id").write_text(agent.id)
    print(f"Agent created:        {agent.id}")

    # 2. Environment (the cloud container, shared across customers)
    environment = client.beta.environments.create(
        name="helios-se-env",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
    )
    Path(".environment_id").write_text(environment.id)
    print(f"Environment created:  {environment.id}")

    # 3. Memory store — created per customer so two prospects never share
    #    memory (S5). The customer_id is baked into the store name/description
    #    so it's traceable in the Console and at session-attach time.
    memory_store = client.beta.memory_stores.create(
        name=f"Helios SE Memory — {customer}",
        description=(
            f"Persistent sales-engineering memory for the Helios deal with "
            f"'{customer}'. Contains the prospect's environment, objections + "
            f"our latest answers, dated competitive intel, pitch strategy, and "
            f"key contacts. Authoritative account plan — newer dated entries "
            f"supersede older ones on the same topic. customer_id={customer}."
        ),
    )
    # Per-customer file (S5 isolation) + the default file the run scripts read.
    Path(f".memory_store_{customer}").write_text(memory_store.id)
    Path(".memory_store_id").write_text(memory_store.id)
    print(f"Memory store created: {memory_store.id}  (customer={customer})")

    print("\nSetup complete.")
    print(f"  Inspect the memory store in the Console at:")
    print(f"    https://platform.claude.com/memory-stores/{memory_store.id}")
    print(f"  Or programmatically with:  python inspect_memory.py")
    print(f"\nNext:  python run_session_1.py")


if __name__ == "__main__":
    main()
