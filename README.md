# Option 2 — Institutional Memory Agent

**Concept landed:** Memory & context engineering
**Tech:** [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) + [memory stores](https://platform.claude.com/docs/en/managed-agents/memory)
**Time:** 60 minutes
**Output:** An agent that visibly gets sharper across multiple sessions on the same domain.

## The pitch

Memory is the concept enterprise clients ask about most and understand least. Most people think it means "a vector database for documents." It doesn't — it means **the agent decides what to remember, what to forget, and what to update when it learns something new.**

You'll build an agent that runs two sessions on the same domain. Between the two sessions, the agent's memory persists. New information in session 2 contradicts session 1. The agent should reconcile, update, and answer better than it did the first time.

That's the demo: same question, two sessions, visibly sharper answer.

## Setup (5 min)

You need a workspace API key on the Console (your hackathon team workspace).

```bash
cd institutional-memory
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
```

That's it. No infrastructure to spin up. Managed Agents handles the runtime.

## Pick a scenario card

Four cards in [`scenario-cards.md`](./scenario-cards.md). Each is a persona that benefits from memory across sessions. Pick one.

## Core build (25 min)

1. **Provision.** Run `python create_agent.py`. This creates three things and saves
   their IDs to `.agent_id`, `.environment_id`, and `.memory_store_id`:
   - A **Managed Agent** with the full agent toolset and a system prompt tuned to your scenario
   - A cloud **environment** (the container the agent's tools run in)
   - A **memory store** — the thing that survives across sessions

2. **Run session 1.** Run `python run_session_1.py`. This:
   - Inlines the docs from `synthetic-data/round1/` into the user message
   - Starts a session with the memory store attached (mounted at `/mnt/memory/`)
   - Asks the agent to read the docs and answer a baseline question
   - Captures the answer in `outputs/session1.txt`

   Between sessions, run `python inspect_memory.py` to see what it chose to remember.

3. **Run session 2.** Run `python run_session_2.py`. This:
   - Inlines `synthetic-data/round2/` (which contradicts or updates round 1)
   - Starts a *new* session against the *same* agent and the *same* memory store
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
institutional-memory/
├── README.md                      (you are here)
├── scenario-cards.md
├── stretch-goals.md
├── requirements.txt
├── create_agent.py                (creates the agent, environment, and memory store)
├── run_session_1.py               (session 1 — uses round1 docs)
├── run_session_2.py               (session 2 — adds round2 docs, asks same question)
├── inspect_memory.py              (demo helper — prints what's in the memory store)
├── stretch_memory_curator.py      (stretch: curator sub-agent)
├── memory_backend.py              (deprecated — the old client-side backend; safe to delete)
└── synthetic-data/
    ├── round1/                    (initial context — onboarding handbook, policies, customer cases)
    └── round2/                    (updates and contradictions)
```
