# Execution Plan — Card D (Sales Engineer for Product X) + All Stretch Goals

## Context

This repo (`institutional-memory-main`) is a **Claude Managed Agents + Memory tool** demo: an agent runs two sessions on the same domain, memory persists between them, session-2 docs contradict session-1, and the agent should reconcile and answer better. The scaffolding (`create_agent.py`, `run_session_1.py`, `run_session_2.py`, `inspect_memory.py`, `stretch_memory_curator.py`) is currently shaped for **Card A — New-Hire Onboarding**, and `synthetic-data/round1`+`round2` hold onboarding docs.

We are switching to **Card D — Sales Engineer for Product X** and **replacing** the onboarding scenario in place. Product X = **Helios**, a fictional real-time data-streaming platform; the prospect being pitched is **Northwind Bank** (fintech). Goal: a working Card-D demo plus **all nine stretch goals (S1–S9)**.

**Card D specifics (from `scenario-cards.md`):**
- Persona: agent supporting a sales engineer pitching Helios; it learns the customer's environment, their objections, and our latest answers.
- Round 1 docs: customer stack overview, list of objections from previous calls, current pitch deck.
- Round 2 docs: a new objection from the latest call, a competitive update from product management.
- Test question (both sessions): **"Tomorrow's call is the final pitch. What's our strategy?"**
- "Better in session 2" = anticipates the new objection, references the latest competitive update, and adjusts the pitch *sequence* rather than repeating the original plan.

**API facts grounded during planning:**
- Managed Agents = `client.beta.agents.create` / `environments.create` / `sessions.create` / `sessions.events.stream`/`send`; memory via `client.beta.memory_stores.create` + `memories.list(store_id, path_prefix=...)` + `memories.retrieve(id, memory_store_id=...)`. Memory is **path-organized** inside a store.
- Compaction is built into the Managed Agents harness; the Messages-API form is `context_management={"edits":[{"type":"compact_20260112"}]}` with beta header `compact-2026-01-12`.
- There is **no documented standalone "Routines" API** (the routines doc 404s). S6 therefore uses a scheduled-wrapper approach (OS scheduler), with a note to prefer a native routines API if one exists in the SDK at execution time.

---

## Part 1 — Core Build (Card D)

### 1a. Replace synthetic data
**Overwrite** `synthetic-data/round1/` (3 docs) and `synthetic-data/round2/` (2 docs). Match the existing markdown style (dated headers, "effective" dates, tables) so contradictions are detectable by date.

`synthetic-data/round1/`:
- `helios-stack-overview.md` — Northwind Bank's current environment: Kafka self-managed on-prem, AWS for analytics, strict data-residency (EU + US), SOC2/PCI, peak ~2M events/sec, Flink for stream processing, a 6-person platform team.
- `objections-log.md` — objections raised in prior calls, each with *our current best answer*: (1) latency SLA vs self-managed Kafka, (2) data residency / on-prem requirement, (3) total cost vs existing Kafka, (4) migration risk, (5) vendor lock-in.
- `pitch-deck.md` — current pitch sequence: problem → Helios architecture → managed-vs-self-managed TCO → security/residency → migration path → pricing → next steps.

`synthetic-data/round2/`:
- `new-objection-2026-05-22.md` — newest call surfaced a **new** objection: Northwind's new CISO mandates *active-active multi-region failover with <5s RPO*, which the current pitch doesn't address.
- `competitive-update-2026-05-25.md` — product management update: competitor **StreamCorp** just cut prices ~20% and announced a managed connector Helios lacks; **but** Helios shipped native active-active multi-region (directly answers the new objection) and a residency-pinning feature.

### 1b. Repoint the agent + sessions
- **`create_agent.py`** — rewrite `SYSTEM_PROMPT` to the Helios Sales-Engineer persona: "You support a sales engineer pitching Helios to a specific prospect. Track the prospect's environment, every objection + our latest best answer, competitive intel, and the current pitch strategy. Get sharper each call." Keep the existing memory-protocol section. Update `name=` and `metadata` to the SE scenario. (Also receives S1 + S3 additions below.)
- **`run_session_1.py`** — set `TEST_QUESTION` to the Card-D question; reword `user_message` from "onboarding and policy documents" to "the prospect's stack overview, objection log, and current pitch deck." `DOCS_DIR` stays `round1`.
- **`run_session_2.py`** — same `TEST_QUESTION`; reword `user_message` to "a new objection from the latest call and a competitive update from product." `DOCS_DIR` stays `round2`.
- `inspect_memory.py` needs no change (store-agnostic).

### 1c. Run + compare
`python create_agent.py` → `run_session_1.py` → `inspect_memory.py` → `run_session_2.py`. Diff `outputs/session1.txt` vs `outputs/session2.txt`: session 2 should anticipate the active-active objection, cite the StreamCorp price cut + Helios's new capability, and resequence the pitch.

---

## Part 2 — Stretch Goals (all nine)

### S1 — Explicit memory policy *(edit `create_agent.py`)*
Add an **ALWAYS remember** list (prospect environment facts; each objection + our best/latest answer; competitive intel with dates; pitch-strategy decisions; key prospect contacts & roles) and a **NEVER remember** list (verbatim deck text — the deck is the source of truth; one-off scheduling/logistics; unconfirmed/speculative pricing; personal data beyond business contact). Recreate the agent and re-run both sessions; memory store should be tighter.

### S2 — Memory Curator sub-agent *(reuse `stretch_memory_curator.py`)*
Already implemented and largely persona-agnostic. Light tweak to `CURATOR_SYSTEM_PROMPT`: add "merge superseded objection answers; keep only the latest competitive intel per competitor." Run `python stretch_memory_curator.py` after session 2, then re-run session 2 to show a sharper answer.

### S3 — Adversarial round *(new `synthetic-data/round3/` + `run_session_3.py`)*
Create `round3/` docs that contradict round1 **with no plausible reason / no effective date** (e.g., `bad-stack-overview.md` claiming Northwind is 100% on-prem with no AWS and only 50k events/sec, and a doc claiming the latency objection "was never raised"). Add `run_session_3.py` (copy of `run_session_2.py`, pointed at `round3`, prompt = "reconcile these against memory"). **Expected correct behaviour: flag + ask, not silent overwrite.** If it silently overwrites, harden `create_agent.py`: add a rule — "If a new document contradicts memory but carries no effective date or stated reason, FLAG the conflict and ASK which to trust; do not overwrite." Re-create + re-test.

### S4 — "What have you learned?" session *(new `run_session_learned.py`)*
Copy session scaffolding but attach **no new docs**; single user message: *"Summarise everything you've learned about this domain across our previous sessions."* Save to `outputs/session_learned.txt`. This is the memory store "talking back."

### S5 — Per-tenant memory via `customer_id` *(modify create + session scripts)*
Run two prospects — **Northwind Bank** and a second prospect **Globex Retail** — with isolated memory. Approach (recommended for guaranteed no-leak): **one memory store per `customer_id`**, recorded in `.memory_store_<customer_id>` files, with `customer_id` also set in `sessions.create(... metadata=...)` and in the store name/description. Add a `--customer` arg to `create_agent.py` (store creation) and the run scripts; load a small per-customer doc set. Run two sessions each for Northwind and Globex, then verify (via `inspect_memory.py` per store + a cross-question) that Northwind facts never appear in Globex answers. *(Lighter alternative if a single store is required: scope by path prefix `/customers/<customer_id>/…` and pass `path_prefix` to `memories.list`.)*

### S6 — Memory + scheduled ingestion ("Routines") *(new `ingest_new_docs.py` + `synthetic-data/inbox/`)*
No native Routines API is documented. Build `ingest_new_docs.py`: scans `synthetic-data/inbox/` for unseen `.md` files, runs a short session that ingests each into memory, then moves processed files to `synthetic-data/processed/`. Schedule it externally — document the **Windows Task Scheduler** command (and an equivalent cron line) to fire daily. Memory then accumulates passively. Note in code/comments: if `client.beta.routines.*` exists in the installed SDK at run time, prefer wrapping the session in that instead.

### S7 — Long-context + compaction *(new `run_session_longcontext.py`)*
Drive **20+ turns in a single session** (a simulated long technical Q&A with Northwind: latency, residency, failover, connectors, pricing, migration, security review…), sending each turn via `sessions.events.send` and streaming the reply. Rely on the harness's built-in compaction for in-session sharpness; **final turn instructs the agent to write a compacted summary of the whole call into `/mnt/memory/`**. Comment the distinction: in-session memory (context window + compaction) vs across-session memory (the memory store). If demonstrating the Messages-API form too, reference `context_management={"edits":[{"type":"compact_20260112"}]}` + beta `compact-2026-01-12`.

### S8 — Memory diff view *(new `memory_snapshot.py` + `memory_diff.py`)*
`memory_snapshot.py <label>` lists every memory (`memories.list` + `memories.retrieve`, reusing `inspect_memory.py`'s pattern) and writes `outputs/memory_snapshot_<label>.json` (path → content). Take a snapshot after session 1 and after session 2. `memory_diff.py before after` prints **added / removed / changed** entries (per-file content diff). This becomes the demo headline: "here's exactly what the agent learned between calls."

### S9 — Topic sub-agents at session level *(new `stretch_topic_subagents.py`)*
Orchestrator that: (1) reads the main agent's memory store and groups entries into topics (customer-environment, objections, competitive-intel, pitch-strategy); (2) creates one **expert sub-agent per topic**, each seeded (read-only) with that topic's memory slice; (3) routes the test question to the relevant expert(s) by memory key and synthesises their answers into the final pitch strategy. Uses `client.beta.agents.create` per topic + sessions; reuses the streaming pattern from `stretch_memory_curator.py`. Most complex — build last.

---

## Critical files

| File | Action |
| --- | --- |
| `create_agent.py` | Rewrite system prompt → Helios SE persona; add S1 ALWAYS/NEVER lists; add S3 flag-and-ask rule; add `--customer` for S5 |
| `run_session_1.py`, `run_session_2.py` | New `TEST_QUESTION` + reworded `user_message`; `--customer` for S5 |
| `synthetic-data/round1/*`, `round2/*` | Replace with Helios/Northwind docs (3 + 2) |
| `stretch_memory_curator.py` | Light prompt tweak for sales context (S2) |
| `synthetic-data/round3/*`, `run_session_3.py` | New (S3) |
| `run_session_learned.py` | New (S4) |
| `ingest_new_docs.py`, `synthetic-data/inbox/` | New (S6) |
| `run_session_longcontext.py` | New (S7) |
| `memory_snapshot.py`, `memory_diff.py` | New (S8) |
| `stretch_topic_subagents.py` | New (S9) |
| `inspect_memory.py` | No change (reused by S5/S8) |

## Verification (end-to-end)

Requires `ANTHROPIC_API_KEY` and network (live Managed Agents calls).

1. **Core:** `pip install -r requirements.txt` → `python create_agent.py` → `run_session_1.py` → `inspect_memory.py` → `run_session_2.py`. Diff `outputs/session1.txt` vs `outputs/session2.txt` — session 2 must anticipate the active-active objection, cite StreamCorp + Helios's new capability, and resequence the pitch.
2. **S1:** re-create + re-run both sessions; `inspect_memory.py` shows tighter, category-aligned memory (no verbatim deck text).
3. **S2:** run curator → re-run session 2 → answer sharper; curator report lists merges/prunes.
4. **S3:** `run_session_3.py` → agent **flags and asks** (does not silently overwrite); if it overwrites, harden prompt and re-test.
5. **S4:** `run_session_learned.py` → coherent recap of environment + objections + competitive intel.
6. **S5:** create + run for `--customer northwind` and `--customer globex`; `inspect_memory.py` per store + a cross-question confirm **no leakage**.
7. **S6:** drop a file in `synthetic-data/inbox/`, run `ingest_new_docs.py`, confirm it lands in memory and moves to `processed/`; verify the scheduled task fires.
8. **S7:** `run_session_longcontext.py` reaches 20+ turns and writes a compacted summary to `/mnt/memory/` (visible via `inspect_memory.py`).
9. **S8:** snapshot before/after session 2; `memory_diff.py` prints added/changed entries.
10. **S9:** `stretch_topic_subagents.py` spawns per-topic experts and produces a routed, synthesised final-pitch strategy.

---

## Part 3 — Team Division (4 engineers)

### Sequencing & dependencies
- **Day-0 sync (15 min):** E1 lands the foundation first — everything depends on a working agent + shaped synthetic data. E1 commits `create_agent.py` (persona, the `--customer` arg signature for S5) and E2 commits `round1`/`round2` docs **early** so E3/E4 can run real sessions.
- After foundation lands, all four streams run in parallel. Shared files: `create_agent.py` + `run_session_1/2.py` are owned by **E1**; **E3** layers the S5 `--customer` arg on top — coordinate via E1's branch, don't fork it.
- Integration checkpoint when all branches merge: run the full Verification list end-to-end.

### Who does what

| Eng | Theme | Scope |
| --- | --- | --- |
| **E1 — Foundation / Lead** | Critical path | `create_agent.py` (Helios SE persona + **S1** ALWAYS/NEVER + **S3** flag-and-ask rule), repoint `run_session_1.py`/`run_session_2.py`, run core build end-to-end, **S2** curator tweak + run. Owns shared scripts; unblocks the team, then floats to help. |
| **E2 — Content / Resilience** | Synthetic data | All docs: `round1/` (3), `round2/` (2), **S3** `round3/` adversarial docs; `run_session_3.py` (S3) and `run_session_learned.py` (S4). |
| **E3 — Production-shape** | Make it real | **S5** per-tenant memory (Northwind + Globex), **S6** `ingest_new_docs.py` + scheduler, **S7** `run_session_longcontext.py` (20+ turns + compaction → memory). |
| **E4 — Demo / Advanced** | Headline + architecture | **S8** `memory_snapshot.py` + `memory_diff.py`, **S9** `stretch_topic_subagents.py` (per-topic expert routing). |

### Ready-to-paste prompts (one per engineer)

Each engineer pastes their block into Claude Code from the repo root. All reference this plan file for full context.

**E1 — Foundation:**
> Read the plan at `C:\Users\tbearly\.claude\plans\scan-this-repo-we-dapper-moore.md`. Implement Part 1b and stretch goals S1, S2, S3-prompt-rule. Rewrite `create_agent.py`'s `SYSTEM_PROMPT` to the Helios Sales-Engineer persona (product = Helios real-time streaming platform, prospect = Northwind Bank); keep the existing memory protocol; add the S1 ALWAYS-remember / NEVER-remember lists and the S3 "flag-and-ask on undated contradictions" rule; update `name`/`metadata`. Add a `--customer <id>` arg that names the memory store per customer (default `northwind`) so E3 can build S5 on it. Repoint `run_session_1.py` and `run_session_2.py`: set `TEST_QUESTION` to "Tomorrow's call is the final pitch. What's our strategy?" and reword each `user_message` for the SE docs. Apply the S2 tweak to `stretch_memory_curator.py`. Do not touch the synthetic-data docs (E2 owns those). Keep style consistent with the existing code.

**E2 — Content / Resilience:**
> Read the plan at `C:\Users\tbearly\.claude\plans\scan-this-repo-we-dapper-moore.md`. Create the Card-D synthetic data and the S3/S4 scripts. Overwrite `synthetic-data/round1/` with `helios-stack-overview.md`, `objections-log.md` (each objection + our current best answer), `pitch-deck.md`; overwrite `synthetic-data/round2/` with `new-objection-2026-05-22.md` (CISO mandates active-active multi-region <5s RPO) and `competitive-update-2026-05-25.md` (StreamCorp -20% price + new connector; Helios ships native active-active + residency pinning). Create `synthetic-data/round3/` with docs that contradict round1 with no effective date or reason (S3 adversarial). Create `run_session_3.py` (copy `run_session_2.py`, point at `round3`, prompt to reconcile) and `run_session_learned.py` (S4 — no docs, single "summarise everything you've learned" message, save to `outputs/session_learned.txt`). Match the existing markdown style (dated headers, tables). Do not modify `create_agent.py` or `run_session_1/2.py` (E1 owns those).

**E3 — Production-shape:**
> Read the plan at `C:\Users\tbearly\.claude\plans\scan-this-repo-we-dapper-moore.md`. Implement S5, S6, S7. S5: build per-tenant memory using E1's `--customer` arg — one memory store per customer (`.memory_store_<id>` files + `customer_id` in `sessions.create` metadata and store name); run two prospects (Northwind, Globex) and prove no leakage via `inspect_memory.py` + a cross-question. S6: write `ingest_new_docs.py` that scans `synthetic-data/inbox/`, ingests unseen `.md` files into memory via a short session, moves them to `synthetic-data/processed/`; document a Windows Task Scheduler command (and cron equivalent) to run it daily; comment to prefer a native `client.beta.routines.*` API if present. S7: write `run_session_longcontext.py` that drives 20+ turns in one session (long Northwind technical Q&A) via `sessions.events.send`, relies on harness compaction, and on the final turn instructs the agent to write a compacted call summary into `/mnt/memory/`. Reuse the streaming pattern from `run_session_2.py`. Coordinate with E1 before editing `create_agent.py`.

**E4 — Demo / Advanced:**
> Read the plan at `C:\Users\tbearly\.claude\plans\scan-this-repo-we-dapper-moore.md`. Implement S8 and S9. S8: write `memory_snapshot.py <label>` (list + retrieve every memory using `inspect_memory.py`'s pattern, dump path→content to `outputs/memory_snapshot_<label>.json`) and `memory_diff.py before after` (print added/removed/changed entries with per-file content diffs). S9: write `stretch_topic_subagents.py` — read the main agent's memory store, group entries into topics (customer-environment, objections, competitive-intel, pitch-strategy), create one expert sub-agent per topic seeded read-only with that topic's slice, route the test question to the relevant expert(s) by memory key, and synthesise a final pitch strategy. Reuse the agent-create + streaming pattern from `stretch_memory_curator.py`. These are all new files — do not modify existing scripts.
