# Onboarding Dashboard

Streamlit app on top of the Managed Agents memory stores.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # or put it in .env
streamlit run dashboard/app.py
python -m pytest -q                      # offline tests for dashboard/core.py
```

First load provisions an agent, environment and the global `team-knowledge`
store (IDs cached in `dashboard/.state/`, gitignored).

| Who | Global store | Personal store |
| --- | --- | --- |
| Experienced colleague | `read_write` | — |
| New hire | `read_only` | `read_write` (created on first use, per name) |

Access is enforced by the API, not by the prompt.

## Demo script

1. **Experienced colleague** "Tom": upload `synthetic-data/round1/*.md` → Ingest.
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
