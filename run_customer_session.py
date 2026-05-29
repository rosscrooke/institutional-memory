"""
S5 — Per-tenant session runner.

Runs the Helios SE agent against ONE customer's isolated memory store. The
agent + environment are shared (E1's create_agent.py); only the memory store
differs per customer, so facts learned about one prospect can never surface in
another's session.

This is standalone — it does NOT modify run_session_1/2.py. It mirrors their
session + streaming pattern.

Two turns run per invocation:
  1. The Card-D question ("Tomorrow's call is the final pitch. What's our
     strategy?") — answered from THIS customer's memory + docs.
  2. A cross-tenant probe asking about Northwind's environment — proves no
     leakage (a Globex session must answer "I have no such information").

`customer_id` is set in sessions.create(metadata=...) and baked into the store
name/description by create_customer_store.py.

Usage:
    python create_customer_store.py --customer northwind
    python run_customer_session.py --customer northwind
    python create_customer_store.py --customer globex
    python run_customer_session.py --customer globex   # cross-probe shows no leak
"""

import argparse
import os
from pathlib import Path

from anthropic import Anthropic


TEST_QUESTION = "Tomorrow's call is the final pitch. What's our strategy?"

CROSS_TENANT_PROBE = (
    "Separately: what is Northwind Bank's peak event rate, and who is their "
    "CISO? If this customer is not Northwind and you have no Northwind facts "
    "in your memory, say so explicitly — do not guess."
)

OUTPUT_DIR = Path("outputs")


def docs_dir_for(customer: str) -> Path:
    """Resolve a customer's doc set.

    Prefer synthetic-data/customers/<customer>/; Northwind falls back to the
    shared round1 Helios docs (E2's content).
    """
    per_customer = Path("synthetic-data/customers") / customer
    if per_customer.is_dir():
        return per_customer
    if customer == "northwind":
        return Path("synthetic-data/round1")
    raise SystemExit(
        f"No docs found for '{customer}'. Expected {per_customer}/ "
        "(or round1/ for northwind)."
    )


def load_docs_as_context(docs_dir: Path) -> str:
    blocks = []
    for path in sorted(docs_dir.glob("*.md")):
        print(f"  including {path.name}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    return "\n\n".join(blocks)


def send_and_stream(client: Anthropic, session_id: str, text: str) -> str:
    """Send one user turn and drain the stream until the agent goes idle."""
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
    parser = argparse.ArgumentParser(description="Run a per-customer Helios SE session.")
    parser.add_argument("--customer", default="northwind", help="Customer id (default: northwind).")
    args = parser.parse_args()
    customer = args.customer.strip().lower()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".agent_id", ".environment_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required}. Run create_agent.py (E1) first.")

    store_path = Path(f".memory_store_{customer}")
    if not store_path.exists():
        raise SystemExit(
            f"Missing {store_path}. Run: python create_customer_store.py "
            f"--customer {customer}"
        )

    agent_id = Path(".agent_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = store_path.read_text().strip()

    # Keep the unchanged inspect_memory.py pointed at the customer in play.
    Path(".memory_store_id").write_text(memory_store_id)

    client = Anthropic()

    docs_dir = docs_dir_for(customer)
    print(f"Loading docs for '{customer}' from {docs_dir}/...")
    context = load_docs_as_context(docs_dir)

    print(f"\nStarting session for '{customer}' with store {memory_store_id}...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title=f"Helios SE — {customer}",
        metadata={"customer_id": customer},
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    f"This is your persistent memory for customer_id={customer} "
                    "ONLY. Mounted at /mnt/memory/. Check it before answering. "
                    "Record what you learn about THIS customer. Never assume "
                    "facts about other customers."
                ),
            }
        ],
    )

    primary_message = (
        f"You are supporting the Helios pitch to customer '{customer}'.\n"
        "1. First, check your memory store at /mnt/memory/ for what you already "
        "know about this customer.\n"
        "2. Read the documents below.\n"
        "3. Save anything worth remembering about this customer to /mnt/memory/.\n"
        "4. Answer the question.\n\n"
        f"{context}\n\n"
        "==================================================\n"
        f"QUESTION: {TEST_QUESTION}"
    )

    print("\nAgent working (turn 1 — pitch strategy)...\n")
    answer = send_and_stream(client, session.id, primary_message)

    print("\n\nAgent working (turn 2 — cross-tenant leakage probe)...\n")
    cross_answer = send_and_stream(client, session.id, CROSS_TENANT_PROBE)
    print("\n\n[agent finished]")

    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / f"session_{customer}.txt"
    out.write_text(
        f"=== SESSION ({customer}) ===\n"
        f"customer_id: {customer}\n"
        f"memory_store: {memory_store_id}\n\n"
        f"Question: {TEST_QUESTION}\n\n--- ANSWER ---\n{answer}\n\n"
        f"Cross-tenant probe: {CROSS_TENANT_PROBE}\n\n--- ANSWER ---\n{cross_answer}\n"
    )
    print(f"\nSaved to {out}")
    print(f"Inspect this customer's memory:  python inspect_memory.py")
    print(
        "No-leak check: run this for both northwind and globex, then read each "
        "session_<customer>.txt — the Globex cross-probe must report NO Northwind facts."
    )


if __name__ == "__main__":
    main()
