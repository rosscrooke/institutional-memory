"""
Stretch goal S9: topic sub-agents at session level.

Instead of asking one agent to hold the entire deal in its head, this
orchestrator splits the main agent's memory store into TOPICS and stands up one
expert sub-agent per topic, each seeded (read-only) with just its slice of
memory. The test question is then routed to the relevant expert(s), and a
synthesiser agent fuses their answers into the final pitch strategy.

Pipeline:
  1. Read the main agent's memory store (list + retrieve, like inspect_memory.py).
  2. Bucket each memory into a topic by keyword match on its path + content:
       customer-environment | objections | competitive-intel | pitch-strategy
  3. Create one expert sub-agent per non-empty topic.
  4. Route the test question to the relevant expert(s) and ask each in its own
     session, seeding its memory slice in the opening message (read-only — the
     experts are never given write access to the store).
  5. Hand all expert answers to a synthesiser agent that produces the final,
     re-sequenced pitch strategy.

Reuses the agent-create + streaming pattern from stretch_memory_curator.py.

Usage:
    python stretch_topic_subagents.py
"""

import os
from pathlib import Path

from anthropic import Anthropic

try:
    from dotenv import load_dotenv

    load_dotenv()  # pick up ANTHROPIC_API_KEY from a local .env if present
except ImportError:
    pass


# Same question session 1 / session 2 answer, so the demo lines up.
TEST_QUESTION = "Tomorrow's call is the final pitch. What's our strategy?"

EXPERT_MODEL = "claude-haiku-4-5-20251001"  # one narrow slice each — fast & cheap
SYNTH_MODEL = "claude-sonnet-4-6"  # the fusion step does the real reasoning


# Topic definitions. `keywords` are matched (lowercased) against each memory's
# path + content to bucket it, and against the question to route it.
TOPICS = [
    {
        "key": "customer-environment",
        "title": "Prospect Environment Expert",
        "description": "the prospect's stack, scale, constraints, and compliance posture",
        "keywords": [
            "environment", "stack", "kafka", "aws", "flink", "on-prem", "on prem",
            "residency", "soc2", "pci", "compliance", "scale", "events/sec",
            "platform team", "infrastructure", "architecture",
        ],
    },
    {
        "key": "objections",
        "title": "Objections Expert",
        "description": "every objection the prospect raised and our latest best answer",
        "keywords": [
            "objection", "concern", "latency", "sla", "cost", "tco", "migration",
            "lock-in", "lock in", "risk", "rebuttal", "answer", "failover", "rpo",
            "active-active", "active active", "multi-region",
        ],
    },
    {
        "key": "competitive-intel",
        "title": "Competitive Intelligence Expert",
        "description": "competitor moves, pricing, and feature gaps (dated)",
        "keywords": [
            "competitor", "competitive", "streamcorp", "pricing", "price",
            "discount", "connector", "feature gap", "vs ", "alternative", "rival",
        ],
    },
    {
        "key": "pitch-strategy",
        "title": "Pitch Strategy Expert",
        "description": "the pitch sequence, what to lead with, and what to de-emphasise",
        "keywords": [
            "pitch", "strategy", "deck", "sequence", "lead with", "next steps",
            "narrative", "positioning", "close", "agenda", "demo",
        ],
    },
]
# Memories that match nothing land here so they're never dropped on the floor.
DEFAULT_TOPIC = "pitch-strategy"


def read_memory_store(client: Anthropic, store_id: str) -> list[dict]:
    """Return [{path, content}] for every memory file in the store."""
    page = client.beta.memory_stores.memories.list(
        store_id, path_prefix="/", order_by="path"
    )
    memories = []
    for item in page.data:
        if item.type != "memory":
            continue
        retrieved = client.beta.memory_stores.memories.retrieve(
            item.id, memory_store_id=store_id
        )
        memories.append({"path": item.path, "content": retrieved.content or ""})
    return memories


def score(text: str, keywords: list[str]) -> int:
    text = text.lower()
    return sum(text.count(kw) for kw in keywords)


def bucket_memories(memories: list[dict]) -> dict[str, list[dict]]:
    """Assign each memory to its best-matching topic."""
    buckets: dict[str, list[dict]] = {t["key"]: [] for t in TOPICS}
    for mem in memories:
        haystack = f"{mem['path']} {mem['content']}"
        best_key, best_score = DEFAULT_TOPIC, 0
        for topic in TOPICS:
            s = score(haystack, topic["keywords"])
            if s > best_score:
                best_key, best_score = topic["key"], s
        buckets[best_key].append(mem)
    return buckets


def route_question(question: str, non_empty_keys: set[str]) -> list[str]:
    """Pick which topic experts the question goes to.

    A pitch/strategy question needs the whole picture, so it pulls in every
    expert that has memory. Otherwise route by keyword overlap with the
    question, falling back to all experts if nothing matches.
    """
    q = question.lower()
    if "pitch" in q or "strategy" in q:
        return [t["key"] for t in TOPICS if t["key"] in non_empty_keys]

    matched = [
        t["key"]
        for t in TOPICS
        if t["key"] in non_empty_keys and score(q, t["keywords"]) > 0
    ]
    return matched or [t["key"] for t in TOPICS if t["key"] in non_empty_keys]


def slice_to_text(memories: list[dict]) -> str:
    return "\n\n".join(
        f"----- MEMORY: {m['path']} -----\n{m['content']}" for m in memories
    )


def run_turn(client: Anthropic, agent_id: str, text: str) -> str:
    """Open a fresh session, send one message, stream and return the reply text.

    Mirrors the streaming pattern in run_session_2.py / stretch_memory_curator.py.
    """
    session = client.beta.sessions.create(agent=agent_id)
    parts: list[str] = []
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {"type": "user.message", "content": [{"type": "text", "text": text}]}
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        parts.append(block.text)
            elif event.type == "session.status_idle":
                break
    return "".join(parts)


def get_or_create_agent(
    client: Anthropic, cache_file: Path, name: str, system: str, model: str
) -> str:
    """Create a sub-agent, caching its id so re-runs reuse it.

    The expert agents are deliberately generic — their memory slice is handed in
    per-session (in run_turn) rather than baked into the system prompt, so the
    same agent can be reused as memory grows between runs.
    """
    if cache_file.exists():
        agent_id = cache_file.read_text().strip()
        print(f"  reusing {name}: {agent_id}")
        return agent_id

    agent = client.beta.agents.create(
        name=name,
        model=model,
        system=system,
        tools=[{"type": "agent_toolset_20260401"}],
        metadata={
            "role": "topic-subagent",
            "hackathon": "partner-basecamp-2026",
        },
    )
    cache_file.write_text(agent.id)
    print(f"  created {name}: {agent.id}")
    return agent.id


def expert_system_prompt(topic: dict) -> str:
    return (
        f"You are the {topic['title']} for an active Helios sales deal. You are "
        f"the single source of truth on {topic['description']}.\n\n"
        "You will be given a READ-ONLY slice of the deal's institutional memory "
        "covering only your topic, followed by a question. Answer ONLY from your "
        "slice and your expertise on this topic. Be specific and cite dates where "
        "the memory gives them. If the question touches something outside your "
        "topic, say so briefly rather than guessing. Keep it tight — your answer "
        "is one input the lead strategist will fuse with the other experts."
    )


SYNTHESISER_SYSTEM_PROMPT = """\
You are the lead sales strategist for a Helios deal. You do not have the raw
account memory yourself — instead you receive briefings from topic experts
(prospect environment, objections, competitive intelligence, pitch strategy).

Fuse their briefings into ONE concrete, re-sequenced final-pitch strategy. You
must:
- Open with the single most important move for tomorrow's call.
- Anticipate the prospect's newest / hardest objection and answer it head-on.
- Weave in the latest competitive intelligence (cite dates).
- Give an explicit pitch SEQUENCE (what to lead with, what to de-emphasise),
  not a restatement of the old deck.
Be concise and action-oriented — this is prep for a live call tomorrow.
"""


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    if not Path(".memory_store_id").exists():
        raise SystemExit("Missing .memory_store_id. Run create_agent.py first.")
    store_id = Path(".memory_store_id").read_text().strip()

    client = Anthropic(
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    # 1. Read the main agent's memory.
    print(f"Reading memory store {store_id} ...")
    memories = read_memory_store(client, store_id)
    if not memories:
        raise SystemExit(
            "Memory store is empty. Run run_session_1.py (and ideally "
            "run_session_2.py) first so there's something to route over."
        )
    print(f"  {len(memories)} memories found.\n")

    # 2. Bucket into topics.
    print("Bucketing memories into topics:")
    buckets = bucket_memories(memories)
    for topic in TOPICS:
        mems = buckets[topic["key"]]
        print(f"  {topic['key']:22s} {len(mems)} memory(ies)")
        for m in mems:
            print(f"        - {m['path']}")
    print()

    non_empty = {k for k, v in buckets.items() if v}
    if not non_empty:
        raise SystemExit("No memories could be bucketed — nothing to route.")

    # 3. Route the question.
    routed = route_question(TEST_QUESTION, non_empty)
    print(f"Routing question to {len(routed)} expert(s): {', '.join(routed)}\n")

    # 4. Create + query one expert per routed topic.
    expert_answers: list[dict] = []
    topic_by_key = {t["key"]: t for t in TOPICS}
    for key in routed:
        topic = topic_by_key[key]
        print(f"--- {topic['title']} ---")
        agent_id = get_or_create_agent(
            client,
            Path(f".topic_agent_{key}_id"),
            topic["title"],
            expert_system_prompt(topic),
            EXPERT_MODEL,
        )
        slice_text = slice_to_text(buckets[key])
        question = (
            "Here is your read-only memory slice for this deal:\n\n"
            f"{slice_text}\n\n"
            "==================================================\n"
            f"QUESTION: {TEST_QUESTION}\n\n"
            "Answer only from your topic. Be specific and cite dates."
        )
        answer = run_turn(client, agent_id, question)
        print(answer + "\n")
        expert_answers.append({"topic": topic["title"], "answer": answer})

    # 5. Synthesise.
    print("=== SYNTHESISING FINAL PITCH STRATEGY ===\n")
    synth_id = get_or_create_agent(
        client,
        Path(".topic_synthesiser_id"),
        "Pitch Strategy Synthesiser",
        SYNTHESISER_SYSTEM_PROMPT,
        SYNTH_MODEL,
    )
    briefings = "\n\n".join(
        f"===== BRIEFING FROM {a['topic'].upper()} =====\n{a['answer']}"
        for a in expert_answers
    )
    synth_prompt = (
        "Your topic experts have briefed you below. Fuse them into the final "
        "pitch strategy.\n\n"
        f"{briefings}\n\n"
        "==================================================\n"
        f"QUESTION: {TEST_QUESTION}"
    )
    final = run_turn(client, synth_id, synth_prompt)
    print(final)

    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "session_topic_subagents.txt"
    body = [f"=== TOPIC SUB-AGENTS (S9) ===\nQuestion: {TEST_QUESTION}\n"]
    body.append(f"Routed to: {', '.join(routed)}\n")
    for a in expert_answers:
        body.append(f"\n--- {a['topic']} ---\n{a['answer']}\n")
    body.append(f"\n--- SYNTHESISED FINAL PITCH STRATEGY ---\n{final}\n")
    out.write_text("".join(body), encoding="utf-8")
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
