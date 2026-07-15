"""
S5 — Per-tenant memory: create one memory store PER CUSTOMER.

The agent and environment are persona-level and shared across all customers
(E1's create_agent.py creates them). Isolation lives at the *memory store*
level: each customer (prospect) gets its own store, so Northwind facts can
never leak into a Globex session and vice versa.

This script is standalone — it does NOT touch create_agent.py. It reuses the
shared .agent_id / .environment_id and creates a fresh memory store named for
the customer, recording its id in `.memory_store_<customer>`.

It also writes `.memory_store_id` = the store it just created, so the
unchanged inspect_memory.py targets whichever customer you last operated on.

Usage:
    python create_customer_store.py --customer northwind
    python create_customer_store.py --customer globex
"""

import argparse
import os
from pathlib import Path

from anthropic import Anthropic


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a per-customer memory store.")
    parser.add_argument(
        "--customer",
        default="northwind",
        help="Customer / prospect id (default: northwind). One store per id.",
    )
    args = parser.parse_args()
    customer = args.customer.strip().lower()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".agent_id", ".environment_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required}. Run create_agent.py (E1) first.")

    client = Anthropic()

    store_path = Path(f".memory_store_{customer}")
    if store_path.exists():
        store_id = store_path.read_text().strip()
        print(f"Reusing existing memory store for '{customer}': {store_id}")
    else:
        memory_store = client.beta.memory_stores.create(
            name=f"Helios SE Memory — {customer}",
            description=(
                f"Per-tenant Helios sales-engineering memory for customer_id="
                f"{customer}. Isolated from every other customer's store. "
                "Contains this prospect's environment, objections + our latest "
                "answers, competitive intel, and pitch strategy."
            ),
        )
        store_id = memory_store.id
        store_path.write_text(store_id)
        print(f"Memory store created for '{customer}': {store_id}")

    # Point the unchanged inspect_memory.py at the customer we just touched.
    Path(".memory_store_id").write_text(store_id)

    print(f"  Recorded in {store_path}")
    print(f"  .memory_store_id now points at '{customer}' (for inspect_memory.py)")
    print(f"\nNext:  python run_customer_session.py --customer {customer}")


if __name__ == "__main__":
    main()
