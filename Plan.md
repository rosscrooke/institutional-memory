# PLAN.md — Institutional Memory Hackathon App

## 1. Context: the original ask

A team of **4 people with no developer background** is building an app for a hackathon. They must start from this scaffold repo:
https://github.com/knag335/institutional-memory.git

The functional requirements come from handwritten notes, transcribed here:

```
UI — Input, Output summary, Agent monitoring

Input:
  - attach files
  - text field
  - slack bot int(egration)
  - tag / categorize → AI generates but is editable

Output summary:
  - chat interface → prompts user w/ suggestions
  - daily digest
  - actions / task list (prioritize)
  - delegate tasks to agent

Agents:
  - Summarization / Analysis agent
  - Categorization agent, scope
  - Summary output — quick snapshot, in-depth
  - Prioritization agent
  - Chat agent — knowledge search + suggestions
  - Task agents → send email, schedule meeting
  - Feedback learning agent
```

**Team decisions made since then:**
- The UI is **two tabs**: **Inputs** and **Summary outputs**. Agent monitoring is a right-hand panel inside Summary outputs.
- The work is split so the **4 people each own separate files and never edit the same file** (no merge conflicts).
- Everyone builds with Claude Code rather than writing code by hand.

## 2. What the scaffold already provides

The repo is Python command-line scripts built on **Claude Managed Agents** with a **memory store**. The memory store is mounted at `/mnt/memory/` inside the agent's session container and persists across sessions.

| File | What it does |
|---|---|
| `create_agent.py` | Creates the Managed Agent (`claude-sonnet-4-6`, `agent_toolset_20260401`), a cloud Environment and a Memory Store. Saves IDs to `.agent_id`, `.environment_id`, `.memory_store_id`. Contains the memory-protocol system prompt. |
| `run_session_1.py` / `run_session_2.py` | Start a session via `client.beta.sessions.create(...)` with the memory store attached as a `resources` entry (`type: memory_store`, `access: read_write`), send docs + a question via `client.beta.sessions.events.send`, and stream `agent.message` / `agent.tool_use` / `session.status_idle` events. **This is the pattern to reuse.** |
| `inspect_memory.py` | Lists memory store contents via `client.beta.memory_stores.memories.list/retrieve`. Reuse for the monitoring panel. |
| `stretch_memory_curator.py` | A second agent that tidies the memory store. Basis for the feedback learning agent. |
| `synthetic-data/round1`, `round2` | Onboarding scenario docs. Round 2 contradicts round 1 (prod-access policy change, team re-org). Use as demo data. |
| `memory_backend.py` | Deprecated. Ignore. |

Requirements: `anthropic>=0.116.0`, `python-dotenv`. The app adds `streamlit`.

The hackathon's core demo idea is: ask the same question before and after new contradictory docs, and show that the agent's answer and memory get sharper. Keep that as the demo climax.

## 3. Target architecture

- **Streamlit** single-page app with `st.tabs(["Inputs", "Summary outputs"])`.
- Two ways to call Claude, both in `core.py`:
  - `ask_claude(prompt)` — fast single Messages API call. Use for categorizing, summarizing, prioritizing, drafting.
  - `run_memory_session(message, title)` — Managed Agent session with the memory store (slow; starts a container). Use only for **ingesting content into memory** and **chat answers**.
- Agents talk to each other through **JSON files in `data/`**, one file per record, so nobody overwrites anybody else's data.

```
app.py                     ← shared, frozen after kickoff (tabs + layout)
core.py                    ← shared, frozen after kickoff (helpers + schemas)
ui/inputs.py               ← Person 1 → render_inputs()
ui/digest_actions.py       ← Person 2 → render_digest(), render_actions()
ui/ask.py                  ← Person 3 → render_ask()
ui/monitor.py              ← Person 4 → render_monitor()
agents/categorizer.py      ← Person 1
agents/summarizer.py       ← Person 2
agents/prioritizer.py      ← Person 2
agents/chat.py             ← Person 3
agents/task_agent.py       ← Person 3
agents/feedback.py         ← Person 4
data/items/   data/tasks/   data/feedback/   data/logs/
```

### UI layout

**Inputs tab** (Person 1)
- File upload area (`st.file_uploader`, .md/.txt/.pdf)
- Text area for pasted notes
- "AI suggested tags": category + tag chips, editable before saving
- "Save to memory" button
- Recent inputs list
- Slack bot: stretch goal only

**Summary outputs tab** — `st.columns([1.6, 1])`
- Left column, top: **Daily digest** with Quick snapshot / In-depth toggle (Person 2)
- Left column, middle: **Actions** — prioritized task list (High/Med/Low) with "Delegate to agent" buttons (Person 2)
- Left column, bottom: **Ask** — chat with 3–4 suggested prompt buttons (Person 3)
- Right column: **Agent monitoring** — status per agent, memory changes (diff), thumbs up/down feedback (Person 4)

## 4. Pre-work (kickoff) — the task to do now

Do this once, on one machine, before the team splits up.

1. Clone the repo. Install deps: `pip install -r requirements.txt streamlit`. Add `streamlit` to `requirements.txt`.
2. Create `.env` with `ANTHROPIC_API_KEY=...` and add `.env` to `.gitignore`. Load it with `python-dotenv` in `core.py`.
3. Run `python create_agent.py` **once**. Commit `.agent_id`, `.environment_id`, `.memory_store_id` so the whole team shares one agent and memory store. Never commit the API key.
4. Write `core.py` containing:
   - Schema docs (as comments or dataclasses):
     - **Item:** `{id, title, source ("upload"|"text"|"slack"), text, tags: [], category, summary_short, summary_long, created_at}`
     - **Task:** `{id, item_id, title, priority ("High"|"Med"|"Low"), owner ("me"|"agent"), status ("open"|"drafting"|"done"), draft, created_at}`
     - **Feedback:** `{id, target ("chat"|"digest"|...), rating (1|-1), comment, created_at}`
     - **Log event:** `{ts, agent, action, status ("running"|"done"|"error"), detail}`
   - `ask_claude(prompt: str, system: str = "") -> str` — Messages API, model `claude-sonnet-4-6`.
   - `run_memory_session(message: str, title: str) -> str` — reuse the session + streaming pattern from `run_session_1.py`; return the final agent text.
   - `save_json(folder: str, record: dict) -> str` — writes `data/<folder>/<id>.json`, generating `id` (uuid) and `created_at` if missing.
   - `load_all(folder: str) -> list[dict]` — reads every JSON in the folder, newest first.
   - `update_json(folder: str, id: str, changes: dict)`.
   - `log_event(agent, action, status, detail="")` — appends to `data/logs/<agent>.jsonl`.
   - `read_logs() -> list[dict]` — all log lines merged, newest first.
   - `list_memory() -> dict[path, content]` — from `inspect_memory.py` logic, for the monitoring panel.
5. Write `app.py`: page config, title "Institutional memory", the two tabs, and the column layout from section 3, calling each `render_*()` function.
6. Create the four `ui/*.py` files with **placeholder** `render_*()` functions that show the panel heading and a mock version of the panel (static sample data) so the app looks complete from the start. Create empty `agents/*.py` stubs with a docstring stating the owner and purpose.
7. Write a seed script `seed_demo.py` that saves the `synthetic-data/round1` docs as Items in `data/items/` (no Claude calls needed), so Persons 2–4 have data immediately.
8. Run `streamlit run app.py`, confirm both tabs render, commit, and push to `main`.
9. Each person then creates their own branch (`p1-inputs`, `p2-digest`, `p3-ask`, `p4-monitor`).

## 5. Per-person work after kickoff

**Person 1 — Inputs + categorization agent**
- Real upload + text area → `agents/categorizer.py` returns `{category, tags}` via `ask_claude` (ask for JSON).
- Editable tags (`st.multiselect` with `accept_new_options` or a text input) and category select.
- On save: `save_json("items", ...)`, then `run_memory_session` to ingest into memory, with a spinner. `log_event` for each step.
- Stretch: Slack bot.

**Person 2 — Digest + Actions (summarization + prioritization agents)**
- `agents/summarizer.py`: snapshot (3 bullets) and in-depth summary over all items; cache results in the item's `summary_short` / `summary_long`.
- `agents/prioritizer.py`: extract action items, rank High/Med/Low, `save_json("tasks", ...)`. Avoid duplicates by checking `item_id`.
- Actions list with "Delegate to agent" → `update_json("tasks", id, {"owner": "agent", "status": "drafting"})`.

**Person 3 — Ask (chat agent + task agent)**
- Chat with `st.chat_message` / `st.chat_input`, answers via `run_memory_session`. Keep history in `st.session_state`.
- 3–4 suggested prompt buttons, e.g. "What changed this week?", "How do I get prod access?", "Who owns payments?".
- `agents/task_agent.py`: for tasks with `owner == "agent"`, draft the email or meeting invite with `ask_claude`, store in the task's `draft`, show it for approval. **Do not actually send email or create calendar events.** Framing: "agent drafts, human approves."

**Person 4 — Agent monitoring + feedback learning agent + demo**
- Status per agent from `read_logs()` (latest event per agent).
- Memory viewer + memory diff: snapshot `list_memory()` to `data/memory_snapshots/<ts>.json`, show added/removed/changed lines between the last two snapshots.
- Thumbs up/down + comment → `save_json("feedback", ...)`.
- `agents/feedback.py`: based on `stretch_memory_curator.py`, reads feedback and updates memory via a memory session.
- Owns the demo script and rehearsal.

## 6. Rules for every Claude Code instance on this project

- **Edit only the files your person owns.** Never modify `app.py` or `core.py` after kickoff; if a change is needed there, stop and say so.
- Use the helpers and schemas in `core.py`; don't invent new data formats.
- Every agent call logs `running` and then `done`/`error` via `log_event`.
- Wrap slow calls in `st.spinner(...)`. Catch exceptions and show `st.error` with a plain message.
- Keep it simple: no databases, no auth, no deployment. Local Streamlit only.
- Commit after each working step.

## 7. Demo story (~2 min)

1. Inputs: upload round 1 docs, show AI-suggested tags, save.
2. Summary outputs: show the digest and prioritized actions; delegate one to the agent.
3. Ask: "I just joined and I need read-only prod access to debug an issue tomorrow. What do I do?"
4. Inputs: upload round 2 docs (policy update + re-org).
5. Ask the same question again — the answer should cite the new policy and flag the change.
6. Monitoring: show the memory diff of what the agent changed.

## 8. Risks

- Managed Agent sessions are slow (container start). Use `ask_claude` everywhere except ingestion and chat; always show a spinner.
- Everyone shares one memory store, so test data leaks into results. Before the demo, re-run `create_agent.py` for a clean store and re-seed.
- Never commit the API key.