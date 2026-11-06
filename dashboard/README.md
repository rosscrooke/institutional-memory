# Onboarding Dashboard

Streamlit app on top of the Managed Agents memory stores.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # or put it in .env
streamlit run dashboard/app.py
python -m pytest -q                      # offline tests for dashboard/core.py
```

First load provisions an agent, environment and the global `team-knowledge`
store (IDs cached in `dashboard/.state/`, gitignored). If that store is empty it is
seeded once from `dashboard/seed/`, so every role gets a briefing before anyone has
ingested anything. The seed is the January 2026 knowledge (round 1) written as concept
files. Seeded versions show up as *initial knowledge (seed)* in timelines.
A non-empty store is never touched. To re-seed, delete `dashboard/.state/ids.json`.

Every seed file has `last_reviewed` frontmatter. `data/analytics-warehouse.md` is
deliberately stale (`last_reviewed: 2024-06-03`, still mentions a planned "2025" migration).
It is there for a future "mark as stale" feature. That feature has to read `last_reviewed`:
the API `updated_at` of every seeded file is the seeding date.

| Who | Global store | Personal store |
| --- | --- | --- |
| Experienced colleague | `read_write` | — |
| New hire | `read_only` | `read_write` (created on first use, per name) |

Access is enforced by the API, not by the prompt.

## Demo script

1. (Automatic) the global store is seeded with the round-1 knowledge on first load.
2. **New hire** "Alice", role *Backend Engineer*: see role briefing + suggested questions.
   Click *"How do I get read-only prod access?"*.
3. Switch to **Tom**: upload `synthetic-data/round2/*.md` → Ingest.
4. Back to **Alice** → ↻ Refresh: prod-access card shows a new date; *Timeline* tab
   shows created → modified with a diff, attributed to Tom.
5. Alice: *"From now on answer only in bullet points."* → appears under *My preferences*.
6. New hire "Bob" asks the same question → prose answer (Alice's preference is hers only).

## Layout

- `core.py`: pure logic (store registry, attribution, timeline+diffs, briefing parsing/cache key). Tested.
- `api.py`: Anthropic adapter (provisioning, memory reads, version history, briefing call, sessions).
- `app.py`: Streamlit UI.
