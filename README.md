# Institutional Memory Hackathon App

**Team:** 4 developers (no prior dev experience)
**Tech:** Streamlit + [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) + Memory Store
**Architecture:** Shared core helpers, per-person UI & agent modules in separate files (no conflicts)

## Kickoff checklist ✓ COMPLETE

- [x] Clone repo & install deps: `pip install -r requirements.txt`
- [x] Create `.env` with `ANTHROPIC_API_KEY` (add to `.gitignore`)
- [x] Run `python create_agent.py` — provisioned shared agent, environment, memory store (IDs in `.agent_id`, `.environment_id`, `.memory_store_id`)
- [x] Write `core.py` with schemas & helpers
- [x] Write `app.py` with tabs & layout
- [x] Create UI placeholders (`ui/*.py`)
- [x] Create agent stubs (`agents/*.py`)
- [x] Write `seed_demo.py`
- [ ] **Next: Run `python seed_demo.py` then `streamlit run app.py` to test**

## Setup (once, before team splits)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # Your workspace API key
python create_agent.py                  # Creates agent + memory store (shared by team)
python seed_demo.py                     # Load demo data
streamlit run app.py                    # Test the UI
```

## Architecture

```
app.py                          ← main Streamlit app (frozen after kickoff)
core.py                         ← shared helpers & schemas (frozen)
ui/
  ├── inputs.py                 ← Person 1: file upload, categorization UI
  ├── digest_actions.py         ← Person 2: summaries & task list
  ├── ask.py                    ← Person 3: chat interface
  └── monitor.py                ← Person 4: agent status & memory viewer
agents/
  ├── categorizer.py            ← Person 1: tag & category AI
  ├── summarizer.py             ← Person 2: quick & in-depth summaries
  ├── prioritizer.py            ← Person 2: extract & rank tasks
  ├── chat.py                   ← Person 3: Q&A with memory
  ├── task_agent.py             ← Person 3: draft emails/meetings
  └── feedback.py               ← Person 4: memory curator
data/
  ├── items/                    ← User inputs (JSON files)
  ├── tasks/                    ← Extracted action items
  ├── feedback/                 ← User ratings & comments
  └── logs/                     ← Agent execution logs
synthetic-data/
  ├── round1/                   ← Initial context docs
  └── round2/                   ← Contradictory updates
```

## Each person's work

**Person 1 — Inputs + Categorizer**
- Implement `render_inputs()` — file upload, text area, tag editor
- Implement `agents/categorizer.py` — AI-generated tags & category
- On save: call categorizer, save to `data/items/`, ingest to memory, log

**Person 2 — Digest + Actions + Summarizer + Prioritizer**
- Implement `render_digest()` — quick snapshot / in-depth toggle
- Implement `render_actions()` — prioritized task list with "Delegate to agent" buttons
- Implement `agents/summarizer.py` — cache results in item summaries
- Implement `agents/prioritizer.py` — extract & rank High/Med/Low

**Person 3 — Ask + Chat + Task Agent**
- Implement `render_ask()` — suggested prompts + chat interface
- Implement `agents/chat.py` — Q&A via `run_memory_session`
- Implement `agents/task_agent.py` — draft emails/meetings (don't send)

**Person 4 — Monitor + Feedback + Demo**
- Implement `render_monitor()` — agent status, memory diff, feedback form
- Implement `agents/feedback.py` — learn from feedback (memory curator)
- Prepare & rehearse 2-min demo

## Demo script (~2 min)

1. Upload round1 docs, show AI tags, save
2. Show digest & actions; delegate one task
3. Ask: "I need prod access. What do I do?"
4. Upload round2 docs (policy updated, org changed)
5. Ask same question — answer reflects new policy & flags change
6. Show memory diff in monitoring panel

## Rules for every developer

- **Edit only YOUR files.** Never modify `app.py`, `core.py`, or `.gitignore` after kickoff.
- Use helpers in `core.py`; don't invent new data formats.
- Log all agent calls: `log_event(agent, action, status, detail)`
- Wrap slow calls in `st.spinner(...)`; show errors with `st.error(...)`
- Test locally with `streamlit run app.py` before pushing
- Commit after each working feature
- **No databases, no auth, no deployment.** Local Streamlit only.
