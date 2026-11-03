# Pre-work Kickoff Summary

## What was completed

This pre-work sets up a complete, conflict-free foundation for a 4-person team to build the Institutional Memory Hackathon App.

### 1. **Dependencies & Environment**
- ✅ Added `streamlit>=1.28.0` to `requirements.txt`
- ✅ Created `.env` template with `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` (**.env is in .gitignore, never pushed**)
- ✅ Created `.gitignore` to protect secrets, cache, and build artifacts

### 2. **Core Helpers — `core.py` (shared, frozen after kickoff)**

All 4 people use these functions. Never edit after kickoff.

| Function | Purpose |
|----------|---------|
| `ask_claude(prompt, system)` | Fast Messages API call for categorizing, summarizing, drafting. Uses claude-sonnet-4-6. |
| `run_memory_session(message, title)` | Managed Agent session with memory store attached. Slow but persistent — use only for ingesting content & chat. |
| `save_json(folder, record)` | Save Item/Task/Feedback to `data/<folder>/<id>.json`. Auto-generates id & created_at. |
| `load_all(folder)` | Load all JSON files from `data/<folder>/`, newest first. |
| `update_json(folder, id, changes)` | Update a record by id. |
| `log_event(agent, action, status, detail)` | Append to `data/logs/<agent>.jsonl`. Tracks agent execution. |
| `read_logs()` | Read all logs, merged and sorted newest first. |
| `list_memory()` | Fetch memory store contents for monitoring panel. |

**Data Schemas** (defined as comments in core.py):
- **Item**: `{id, title, source, text, tags[], category, summary_short, summary_long, created_at}`
- **Task**: `{id, item_id, title, priority, owner, status, draft, created_at}`
- **Feedback**: `{id, target, rating, comment, created_at}`
- **Log**: `{ts, agent, action, status, detail}`

### 3. **Streamlit App — `app.py` (shared, frozen after kickoff)**

Single-page app with two tabs and a 1.6:1 column layout:

```
Inputs Tab                          Summary Outputs Tab
                                    ┌──────────────────┬─────────┐
                                    │ Digest           │ Monitor │
                                    │ Actions          │ (Agent  │
                                    │ Ask              │  Status)│
                                    └──────────────────┴─────────┘
```

Each panel calls a `render_*()` function from the `ui/` module.

### 4. **UI Modules — `ui/*.py` (each person owns one)**

**Person 1 owns `ui/inputs.py`**
- Placeholder showing file uploader, text area, category selector, tag multiselect
- Mock data so the panel looks complete
- Real implementation: file upload → categorizer agent → save to memory

**Person 2 owns `ui/digest_actions.py`**
- Two panels:
  - `render_digest()` — Quick snapshot / In-depth toggle (mock summaries)
  - `render_actions()` — Task list (High/Med/Low) with "Delegate to agent" buttons
- Real implementation: fetch Items/Tasks, call summarizer & prioritizer agents

**Person 3 owns `ui/ask.py`**
- Chat interface with 4 suggested prompt buttons
- Mock response UI
- Real implementation: suggested prompts + `st.chat_input` + `run_memory_session` for answers

**Person 4 owns `ui/monitor.py`**
- Agent status list (from logs)
- Memory changes viewer
- Feedback form (thumbs up/down + comment)
- Real implementation: fetch logs, snapshot memory, show diffs

### 5. **Agent Stubs — `agents/*.py` (each person owns one or two)**

**Person 1:**
- `agents/categorizer.py` — Categorize text & suggest tags via `ask_claude`

**Person 2:**
- `agents/summarizer.py` — Generate quick (3 bullets) & in-depth summaries
- `agents/prioritizer.py` — Extract action items, rank by priority

**Person 3:**
- `agents/chat.py` — Answer questions via `run_memory_session` (memory-aware)
- `agents/task_agent.py` — Draft emails/meeting invites (no send)

**Person 4:**
- `agents/feedback.py` — Process feedback & update memory store (memory curator)

Each file has a docstring stating the owner and purpose. All currently raise `NotImplementedError`.

### 6. **Demo Data — `seed_demo.py`**

One-time script (no Claude calls):
- Loads `synthetic-data/round1/*.md` files
- Saves as Items to `data/items/` with category="Policy"
- Gives Person 2–4 immediate data to work with

Usage: `python seed_demo.py`

### 7. **Documentation — `README.md` (updated)**

Clear architecture diagram, per-person tasks, rules, and demo script.

---

## How this prevents conflicts

**Each person edits only their own files:**
- UI logic in `ui/<name>.py` (not shared)
- Agent logic in `agents/<name>.py` (not shared)
- Data in `data/items/`, `data/tasks/`, `data/feedback/`, `data/logs/` (separate JSON files, not conflicts)

**Shared files are frozen after kickoff:**
- `app.py` — layout & imports only
- `core.py` — helpers only
- `.gitignore`, `requirements.txt`, `README.md` — no changes needed

If anyone needs a change to `core.py` or `app.py`, they flag it (don't edit).

---

## Next steps (after this commit)

1. **Fill in `.env` with your API key** (already in .gitignore)
2. **Run `python create_agent.py`** — creates shared agent, environment, memory store
   - Saves IDs to `.agent_id`, `.environment_id`, `.memory_store_id`
   - **COMMIT these files** — team uses the same agent & memory
3. **Run `python seed_demo.py`** — loads demo Items
4. **Test `streamlit run app.py`** — verify UI renders (should show all 4 panels with mock data)
5. **Each person creates their branch** (`p1-inputs`, `p2-digest`, `p3-ask`, `p4-monitor`)
6. **Each person implements their module** using the patterns & helpers in `core.py`

---

## File structure ready to go

```
institutional-memory/
├── .env                          (secrets, .gitignore'd)
├── .gitignore                    (✓ protects .env, __pycache__, etc.)
├── requirements.txt              (✓ includes streamlit)
├── README.md                     (✓ updated with team architecture)
├── PREWORK_SUMMARY.md            (you are here)
├── Plan.md                       (original spec)
│
├── app.py                        (✓ Streamlit main — frozen)
├── core.py                       (✓ Shared helpers — frozen)
├── seed_demo.py                  (✓ Demo data loader)
│
├── ui/                           (✓ 4 placeholder modules)
│   ├── __init__.py
│   ├── inputs.py                 (Person 1)
│   ├── digest_actions.py         (Person 2)
│   ├── ask.py                    (Person 3)
│   └── monitor.py                (Person 4)
│
├── agents/                       (✓ 6 stub modules)
│   ├── __init__.py
│   ├── categorizer.py            (Person 1)
│   ├── summarizer.py             (Person 2)
│   ├── prioritizer.py            (Person 2)
│   ├── chat.py                   (Person 3)
│   ├── task_agent.py             (Person 3)
│   └── feedback.py               (Person 4)
│
├── data/                         (created at runtime)
│   ├── items/
│   ├── tasks/
│   ├── feedback/
│   ├── logs/
│   └── memory_snapshots/
│
└── synthetic-data/               (✓ demo scenarios)
    ├── round1/                   (initial docs)
    └── round2/                   (contradictory updates)
```

---

## Key decisions made

1. **One shared agent & memory store** (not per-person) → Team learns together
2. **JSON files instead of a database** → No setup, no conflicts, easy to inspect
3. **Separate files per person** → No merge conflicts, clear ownership
4. **Frozen `app.py` & `core.py`** → Changes flagged, not siloed
5. **Mock data from day one** → Devs can build UI in parallel, test immediately
6. **Streamlit (not Flask/React)** → No build step, fast iteration, easy for non-devs

---

## What's ready to commit

- ✅ `requirements.txt` (updated)
- ✅ `.gitignore` (new)
- ✅ `app.py` (new, complete)
- ✅ `core.py` (new, complete)
- ✅ `seed_demo.py` (new, complete)
- ✅ `ui/*.py` (4 new, placeholders complete with mock data)
- ✅ `agents/*.py` (6 new, stubs with docstrings)
- ✅ `README.md` (updated)
- ✅ `PREWORK_SUMMARY.md` (this file)

**Not committed (in .gitignore):**
- `.env` (secrets)
- `data/` (runtime)
- `outputs/` (runtime)

---

This commit completes **Section 4 (Pre-work)** from Plan.md. Team is ready to split up and own their modules.
