# Option 2 — Institutional Memory Agent

**Concept landed:** Memory & context engineering
**Tech:** [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) + the [Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
**Time:** 60 minutes
**Output:** An agent that visibly gets sharper across multiple sessions on the same domain.

## The pitch

Memory is the concept enterprise clients ask about most and understand least. Most people think it means "a vector database for documents." It doesn't — it means **the agent decides what to remember, what to forget, and what to update when it learns something new.**

You'll build an agent that runs two sessions on the same domain. Between the two sessions, the agent's memory persists. New information in session 2 contradicts session 1. The agent should reconcile, update, and answer better than it did the first time.

That's the demo: same question, two sessions, visibly sharper answer.

## Setup (5 min)

You need a workspace API key on the Console (your hackathon team workspace).

```bash
cd 02-institutional-memory-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
```

That's it. No infrastructure to spin up. Managed Agents handles the runtime.

## Pick a scenario card

Four cards in [`scenario-cards.md`](./scenario-cards.md). Each is a persona that benefits from memory across sessions. Pick one.

## Core build (25 min)

1. **Create the agent.** Run `python create_agent.py`. This creates a Managed Agent with the Memory tool enabled, a system prompt tuned to your scenario, and saves the agent ID to `.agent_id`.

2. **Run session 1.** Run `python run_session_1.py`. This:
   - Uploads the docs from `synthetic-data/round1/` via the Files API
   - Starts a session that asks the agent to read them and answer a baseline question
   - Captures the answer in `outputs/session1.txt`

3. **Run session 2.** Run `python run_session_2.py`. This:
   - Uploads `synthetic-data/round2/` (which contradicts or updates round 1)
   - Starts a *new* session against the *same* agent
   - Asks the same question
   - Captures the answer in `outputs/session2.txt`

4. **Compare.** Open both outputs. The session 2 answer should:
   - Acknowledge the conflict
   - Reflect the newer information
   - Reference what it learned in session 1 via its memory store

By minute 30 you have two sessions to compare and a clear "the agent learned something" moment.

## Stretch goals (20 min — pick at least one)

See [`stretch-goals.md`](./stretch-goals.md).

**Tier 1 — Make memory deliberate:**
- Add explicit memory instructions to the system prompt. Tell the agent what kinds of things to remember and what to ignore.
- Add a sub-agent that curates the memory store (the "memory curator" pattern).

**Tier 2 — Make memory resilient:**
- Adversarial test: feed it deliberately wrong information in session 2 and see if it spots the contradiction.
- Add a third session where you ask: "What have you learned?" and see what the agent says.

**Tier 3 — Make memory production-shaped:**
- Tie memory to a customer ID via metadata so the agent has per-tenant memory.
- Use Files API to attach growing document sets across multiple sessions and watch context grow.

## Two-minute demo

Side-by-side terminal windows:
- Left: session 1 answer
- Right: session 2 answer (same question, after memory + new context)

Read both out loud. Let the room see the agent's answer sharpen. Then open the memory store on the third terminal — show what the agent chose to remember.

## What's in this folder

```
02-institutional-memory-agent/
├── README.md                      (you are here)
├── scenario-cards.md
├── stretch-goals.md
├── requirements.txt
├── create_agent.py                (creates the Managed Agent with Memory tool)
├── run_session_1.py               (session 1 — uses round1 docs)
├── run_session_2.py               (session 2 — adds round2 docs, asks same question)
├── stretch_memory_curator.py      (stretch: curator sub-agent)
└── synthetic-data/
    ├── round1/                    (initial context — onboarding handbook, policies, customer cases)
    └── round2/                    (updates and contradictions)
```
sebas