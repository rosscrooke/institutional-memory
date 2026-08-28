# PLAN — 120 minutes

Operational doc: what to do, in what order, with the code to copy.
The reasoning behind every choice here lives in [`BRIEF.md`](./BRIEF.md). Read that once
before you start; come back to this one while building.

Roles: **A** memory · **B** UI · **C** agent + deployment.
With four people, the fourth owns `DEMO.md` and rehearsals from minute 20 and writes no code.

> It is tight, because the deployment is a hard requirement, not a stretch goal.
> **If you fall behind, cut the user-isolation beat at 01:28 first.** It is the most
> impressive thing you can afford to lose; everything before it still tells a whole story.

---

## Schedule

### `00:00` — Prove the pipe (12 min) · everyone
Clone, `pip install -r requirements.txt`, export the key, run `create_agent.py` then
`run_session_1.py` **unchanged**. Do not read the code first. Do not improve anything.

Nominate one laptop as the demo machine now.

**If this is not green at minute 12, stop and switch to the Messages API fallback**
(`client.messages.create` + the `memory_20250818` memory tool with a local directory
backend — same two-tier story, ~30 minutes more code, no Console view). That decision gets
harder every minute you delay it.

### `00:12` — Freeze the demo, then the interfaces (8 min) · everyone
Write the exact three turns you will type on stage into `DEMO.md`, **before any code**.
Use Card A (onboarding) — the synthetic data already fits it.

Then write the function signatures below as empty stubs. Nobody changes a signature after
this point without saying so out loud.

**C also, here:** run `create_agent.py` once and commit the IDs so everyone points at the
same objects. `.gitignore` is already in the repo — keep it that way.

### `00:20` — Three tracks, no integration (35 min)

**A — `memory.py`**
Get-or-create a store named `user:<name>`; list its memories with `view="full"`; list
versions filtered by `created_at_gte` so we can show what changed. Seed the shared store
from `synthetic-data/round1/`.

**B — `app.py`**
Sidebar user picker, chat column, memory panel column, a **Consolidate & end session**
button. Wire it to hard-coded fake data first — it should *look* finished before it works.

**C — `agent.py`, then `deploy.py`**
Recreate the agent with the new system prompt on `claude-opus-5`. `start_session` attaching
both stores. `ask()` that sends a message, streams to idle, returns text. Then the curator
agent on Haiku plus the scheduled deployment, verified with one `deployments.run()`.

> C has the widest track. **If C is behind at 00:45, B takes `deploy.py`** — it is thirty
> lines and independent of everything else.

### `00:55` — Integrate, chat first, panel second (20 min) · B + C
Replace fake chat responses with real ones. Cache the client with `@st.cache_resource` and
keep `session_id` in `st.session_state`, or every Streamlit rerun starts a new session and
the demo makes no sense.

**A meanwhile:** swap the panel's fake data for real store contents.

Target for this block: one working end-to-end conversation, panel included.

### `01:15` — The promotion moment (13 min) · everyone
Wire the consolidate button: send `CONSOLIDATE`, stream the agent's report into the chat,
refresh the panel, and **mark files created or changed in the last minute**. That highlight
is the single most valuable pixel on the screen. Make it obvious.

### `01:28` — User isolation (10 min) · A + B · ⚠️ cut this first
Switch the sidebar to a second user, start a fresh session, ask the identical question.
Different memory, different answer, same agent, same shared docs.

### `01:38` — Put the deployment in the demo (7 min) · C
The deployment already exists. This is only about making it visible: a button or a terminal
calling `deployments.run()`, and a printed list of past `drun_` records beside it.

Confirm `schedule.upcoming_runs_at` reads the way you will describe it on stage — that is
the field proving the cron parsed as intended.

### `01:45` — Rehearse twice, on the demo machine (8 min) · everyone
Full timed run-throughs, out loud, from `DEMO.md`. Fix only what breaks the run.
Two clean passes beats one more feature, every time.

### `01:53` — Freeze (7 min) · everyone
No more commits. **Pre-warm one session** so the first container boot does not happen on
stage. Screenshot the chat and the memory panel into a slide as the network-died fallback.
Close every other tab.

---

## Function contracts

Agreed at 00:12. Do not change silently.

| File | Surface |
|---|---|
| `memory.py` | `store_for_user(user) -> str` · `list_memories(store_id) -> list` · `changed_since(store_id, ts) -> list` |
| `agent.py` | `start_session(user) -> str` · `ask(session_id, text) -> str` · `consolidate(session_id) -> str` |
| `deploy.py` | `create_curator() -> str` · `run_now(deployment_id) -> str` |
| `app.py` | — Streamlit entry point |
| `seed.py` | — one-off, pushes `round1/` into the shared store |

---

## The session call — this is the whole architecture

```python
session = client.beta.sessions.create(
    agent=AGENT_ID,
    environment_id=ENV_ID,
    title=f"chat · {user}",
    resources=[
        {   # long-term, private to this user
            "type": "memory_store",
            "memory_store_id": store_for_user(user),
            "access": "read_write",
            "instructions": (
                f"Long-term memory for {user}. Read it before answering "
                "anything. Update it only when asked to consolidate."
            ),
        },
        {   # long-term, shared, never written
            "type": "memory_store",
            "memory_store_id": SHARED_STORE_ID,
            "access": "read_only",
            "instructions": "Company policies and directory. Source of truth.",
        },
    ],
)
# short-term memory: nothing to do — the session is it
```

## The event loop — get this gate right

```python
with client.beta.sessions.events.stream(session_id) as stream:
    client.beta.sessions.events.send(session_id, events=[
        {"type": "user.message", "content": [{"type": "text", "text": text}]},
    ])
    for event in stream:
        if event.type == "agent.message":
            for block in event.content:
                if getattr(block, "type", None) == "text":
                    parts.append(block.text)

        if event.type == "session.status_terminated":
            break
        if event.type == "session.status_idle":
            if event.stop_reason.type == "requires_action":
                continue          # waiting on us
            break                 # actually done
```

The upstream scripts break on a bare `status_idle`. That truncates replies in a multi-turn
chat. See `BRIEF.md` §4.

## The scheduled deployment

```python
curator = client.beta.deployments.create(
    name="Nightly memory curator",
    agent=CURATOR_AGENT_ID,          # claude-haiku-4-5
    environment_id=ENV_ID,
    resources=[                      # the block the upstream script is missing
        {"type": "memory_store", "memory_store_id": sid, "access": "read_write"}
        for sid in all_user_store_ids()          # max 8 per session
    ],
    initial_events=[{
        "type": "user.message",
        "content": [{"type": "text", "text":
            "Run memory hygiene across every mounted store: merge duplicates, "
            "flag unresolved contradictions, prune anything ephemeral. "
            "Do not add new knowledge."}],
    }],
    schedule={"type": "cron", "expression": "0 3 * * *",
              "timezone": "America/Bogota"},
    budget={"type": "limit",
            "max_list_cost": {"amount": "200", "currency": "USD"}},   # $2.00 per run
)

# On stage, don't wait for 3AM:
client.beta.deployments.run(curator.id)     # fires now, records a drun_…
```

Notes that bite:
- Execution is **jittered** up to 15% of the interval (capped at 9 min). Never promise an
  exact fire time in the pitch.
- Cron is wall-clock matched: a 2AM schedule is skipped on spring-forward and fires twice on
  fall-back. 3AM is fine.
- **Archiving or deleting the agent auto-archives the deployment, permanently.** Create new
  agent versions; never delete agents mid-build.
- `deployment_runs.list(has_error=True)` is the failure log.

---

## The system prompt

Replaces `SYSTEM_PROMPT` in `create_agent.py`. This is the actual product — the upstream
prompt says *remember things*; this one says which tier a fact belongs in and when
promotion is allowed.

```
You have two kinds of memory, and they are not interchangeable.

SHORT-TERM — this conversation. Everything said in this session, plus any
scratch files you write under /workspace. It disappears when the session
ends. Use it freely. Think out loud here.

LONG-TERM — the mounts under /mnt/memory/. These survive forever and are
replayed into every future conversation with this user.

# Protocol

1. FIRST ACTION, EVERY SESSION: `ls -R /mnt/memory/` and read anything that
   looks relevant. Never answer before you have done this.
2. During the conversation, do NOT write to /mnt/memory/. Keep working notes
   in /workspace instead.
3. When the user asks you to consolidate, promote to long-term memory ONLY:
     - stable preferences and constraints ("I own the payments service")
     - decisions, and the reason behind them
     - corrections the user made to something you said
     - questions this user asks repeatedly, and the best current answer
4. NEVER promote: the transcript, one-off questions, anything already in the
   shared read-only store, anything derivable, and above all no credentials,
   keys, or tokens — long-term memory is replayed verbatim into every future
   session.
5. When a new fact contradicts an existing one, EDIT the existing file in
   place. Do not append. Record the date. The newer fact wins unless the
   older one is explicitly dated later.
6. The shared store is read-only. It is the source of truth for policy. If
   your memory disagrees with it, the shared store is right.

# Answering

- If you used long-term memory, say so in the first sentence:
  "From what you told me before about X..."
- If a fact changed since last time, lead with what changed and why.
- Be concise.
```

The consolidation turn is sent by the **app**, not typed by the user — that is what makes
it a button rather than a prompt-engineering trick:

```python
CONSOLIDATE = (
    "End of session. Review this conversation and promote anything durable "
    "to my long-term memory under /mnt/memory/, following your protocol. "
    "Then list exactly which files you created or changed and why, in one "
    "line each."
)
```

---

## Pre-flight checklist

Run through this before the demo, not during it.

- [ ] `session_id` lives in `st.session_state`; client cached with `@st.cache_resource`
- [ ] Idle gate checks `stop_reason.type`, not bare `status_idle`
- [ ] One session pre-warmed — the first container boot is slow
- [ ] `schedule.upcoming_runs_at` reads as expected
- [ ] Deployment has a `budget`
- [ ] Agent and store IDs committed; everyone on the same ones
- [ ] `.gitignore` in place; no `.env` or `.agent_id` staged
- [ ] Screenshots of chat + memory panel pasted into a slide
- [ ] `outputs/session1.txt` and `session2.txt` kept as a backup narrative

## If a stretch goal fits, ranked by demo value per minute

1. **The version diff** (~15 min) — `memory_versions.list()` gives before/after content for
   every change. One red/green diff of a fact the agent revised is the strongest single
   image in the deck.
2. **"What have you learned about me?"** (~5 min) — a button, no documents attached. Makes
   long-term memory talk back.
3. **A store messy enough to curate** (~10 min) — the curator has nothing to clean unless
   memory is genuinely duplicated and contradictory. Seed deliberate mess so the nightly run
   lands instead of returning "nothing to do".
4. **Adversarial round** — feed a document that contradicts memory for no good reason; see
   whether it flags or silently updates. Genuinely interesting, risky live.

## Refuse these

Embeddings or a vector DB · real auth · any database · multi-agent routing · hosting the UI
on Managed Agents (it deploys agents, not web apps) · a second deployment or a webhook
receiver · tests, Docker, type hints, a polished README.
