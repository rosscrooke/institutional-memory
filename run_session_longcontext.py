"""
S7 — Long-context + compaction in a single session.

Drives 20+ turns of a simulated Northwind technical Q&A through ONE session.
This exercises two distinct kinds of memory:

  * IN-SESSION memory  = the context window. As the conversation grows, the
    Managed Agents harness COMPACTS it automatically (summarises older turns)
    so the agent stays sharp deep into the call. We rely on that built-in
    behaviour here — nothing to configure on the session.

  * ACROSS-SESSION memory = the memory store at /mnt/memory/. The context
    window evaporates when the session ends; the store persists. So the FINAL
    turn instructs the agent to write a compacted summary of the whole call
    into /mnt/memory/ — that's the bridge from in-session to across-session.

If you want the SAME compaction on the raw Messages API (outside Managed
Agents), the equivalent is:
    context_management={"edits": [{"type": "compact_20260112"}]}
with beta header "compact-2026-01-12". The Managed Agents harness does this
for you, so it is not needed below.

Usage:
    python run_session_longcontext.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


OUTPUT_DIR = Path("outputs")

# 22 technical turns across the full Northwind evaluation surface — well past
# the 20-turn bar, enough to trigger in-session compaction.
TURNS = [
    "Let's do a deep technical review for Northwind. First: what latency SLA can Helios commit to versus their self-managed Kafka at ~2M events/sec?",
    "How does Helios guarantee EU + US data residency given their SOC2/PCI obligations?",
    "Walk me through active-active multi-region failover and the RPO we can promise.",
    "What's the failover behaviour if a whole region goes dark mid-stream?",
    "Their stack uses Flink for stream processing — how does Helios interop with existing Flink jobs?",
    "What connectors ship out of the box, and which ones are we missing versus StreamCorp?",
    "Give me the managed-vs-self-managed TCO story for a 6-person platform team.",
    "How does pricing scale with throughput, and what does idle cost look like?",
    "What's the migration path off self-managed Kafka, and how long does cutover take?",
    "What are the top migration risks and how do we de-risk them?",
    "How does Helios handle exactly-once semantics?",
    "What's the backpressure model when a consumer falls behind?",
    "Describe the schema registry and how schema evolution is handled.",
    "What monitoring and observability hooks do we expose?",
    "Walk through the security review: encryption in transit and at rest, key management.",
    "How do we address the vendor lock-in objection concretely?",
    "What does the disaster-recovery story look like beyond multi-region?",
    "What are the data-retention controls and per-topic retention policies?",
    "How is access control / RBAC structured for their platform team?",
    "What does a 30-day POC plan look like for Northwind?",
    "Summarise the single strongest reason Northwind should choose Helios over StreamCorp.",
    # Final turn — persist the call into across-session memory.
    "We're done. Write a COMPACTED summary of everything from this call into "
    "/mnt/memory/ (a single tidy entry): Northwind's environment, every "
    "objection + our latest answer, competitive intel, and the recommended "
    "final-pitch strategy. This is what future sessions should start from.",
]


def send_and_stream(client: Anthropic, session_id: str, text: str) -> str:
    """Send one turn and drain the stream until the agent goes idle."""
    parts: list[str] = []
    with client.beta.sessions.events.stream(session_id) as stream:
        client.beta.sessions.events.send(
            session_id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": text}]}],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        parts.append(block.text)
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
                break
    return "".join(parts)


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

    print(f"Starting one long session ({len(TURNS)} turns) with store {memory_store_id}...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="Session — long-context technical review (Northwind)",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "Persistent memory at /mnt/memory/. The harness compacts "
                    "this long conversation automatically; on the final turn "
                    "you'll be asked to persist a compacted summary here."
                ),
            }
        ],
    )

    transcript: list[str] = []
    for i, turn in enumerate(TURNS, 1):
        print(f"\n\n===== TURN {i}/{len(TURNS)} =====")
        print(f"USER: {turn}\n")
        answer = send_and_stream(client, session.id, turn)
        transcript.append(f"--- TURN {i} ---\nUSER: {turn}\n\nAGENT: {answer}\n")

    print("\n\n[agent finished]")

    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / "session_longcontext.txt"
    out.write_text(
        f"=== LONG-CONTEXT SESSION ({len(TURNS)} turns) ===\n\n" + "\n".join(transcript)
    )
    print(f"\nSaved transcript to {out}")
    print("The final turn wrote a compacted call summary to /mnt/memory/.")
    print("Inspect it:  python inspect_memory.py")


if __name__ == "__main__":
    main()
