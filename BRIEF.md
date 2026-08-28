# BRIEF — Two-Tier Agent Memory

> **Why this is not `CLAUDE.md`.** `CLAUDE.md` is loaded into context automatically at the
> start of every session, and anything it `@imports` is loaded with it. That budget is for
> instructions that must apply to *every* turn. This file is the opposite: a long, one-time
> read for a human (or an agent) about to work on the memory layer. It should be read
> deliberately, once, not paid for on every prompt.
>
> `CLAUDE.md` carries a **plain-text mention** of this file — not an `@import` — so it stays
> discoverable without being auto-loaded.
>
> **Read this if:** you are picking up the project, joining mid-build, or about to change
> how memory is written. **Skip it if:** you are fixing a typo.

---

## 1. What we are building

An institutional-memory agent with **two memories that have different lifetimes**, and an
explicit, visible policy for promoting facts from one to the other.

| Tier | Scope | Lives in | Dies when |
|---|---|---|---|
| **Short-term** | one conversation | the Managed Agents session (turn history + `/workspace`) | the session ends |
| **Long-term** | one user, forever | a memory store, mounted at `/mnt/memory/<store-name>/` | never (every write is versioned) |

Plus a **curator deployed on a cron schedule** that keeps long-term memory from rotting.

### The one-sentence pitch
> An agent that remembers is a demo. An institution that maintains its own memory on a
> schedule, with an auditable run history, is a system.

### Why this and not "the agent remembers things"
The upstream repo already demos memory surviving between two sessions. Every other team on
this track will demo that. Our differentiator is not *more* memory — it is **two memories
with different lifetimes**, which buys three things the base demo cannot show:

1. **A visible promotion moment.** The audience watches the agent decide what from this
   conversation is worth keeping forever, and what gets thrown away with the session.
2. **Per-user isolation by construction.** Switch user, ask the identical question, get a
   different answer — because sessions mount a different store, not because we wrote
   filtering code.
3. **Memory that maintains itself.** A scheduled curator with a run history.

---

## 2. The context that is easy to get wrong

**Short-term memory is not something we build.** A Managed Agents session is already
stateful across turns, already prompt-cached, and already compacts itself when it
approaches the context limit. Any hand-rolled conversation buffer, Redis, or LangChain
memory is rebuilding — worse — something the platform hands us for free.

**Long-term memory is a filesystem, not a database.** A memory store is a set of small text
files mounted into the session container. The agent reads and writes it with `ls`, `grep`,
`read`, `write`. There is no retrieval layer to build, and at our scale (tens of short
facts) there is no retrieval problem to solve.

**Multiple stores per session is the architecture.** Up to 8 stores attach to one session,
each with its own access level. We use two:

```
user:<name>   read_write   ← this user's private long-term memory
org:shared    read_only    ← company policies, directory, handbook (source of truth)
```

Tenant isolation stops being a feature we implement and becomes a property of how we
create the session. This is the upstream repo's Tier-3 stretch goal (S5), and we get it
essentially free.

**Nothing is written to long-term memory mid-conversation.** Facts are promoted only during
an explicit consolidation turn, triggered by a button in the UI — not typed by the user.
Mid-turn writes would work, but they scatter the exact moment we want the audience to see.

---

## 3. Platform objects, and their ID prefixes

Useful when reading logs or the Console. All of these live under `client.beta.*` and carry
the `managed-agents-2026-04-01` beta header, which the SDK sets automatically.

| Object | Prefix | What it is |
|---|---|---|
| Agent | `agent_` | Persisted, versioned config: model, system prompt, tools. Created once, referenced forever. |
| Environment | `env_` | Template for provisioning the container. |
| Session | — | One stateful interaction. References an agent + environment. **This is our short-term memory.** |
| Memory store | `memstore_` | Workspace-scoped collection of text files. **This is our long-term memory.** |
| Memory | `mem_` | One file in a store, addressed by `path`. Max 100KB — prefer many small files. |
| Memory version | `memver_` | Immutable snapshot per mutation. This is what makes a diff view possible. |
| Deployment | `depl_` | A cron schedule that fires sessions autonomously. |
| Deployment run | `drun_` | One firing, recorded whether it succeeded or failed. |

Session lifecycle: `rescheduling → running ⇄ idle → terminated`.

---

## 4. What we found reading the upstream repo

Real findings, verified against the code. Fix these rather than rediscovering them.

**1. The idle break is wrong for a chat UI.**
`run_session_1.py` and `run_session_2.py` break the event loop on a bare
`session.status_idle`. Sessions go idle *transiently* — between parallel tool calls, or
while waiting on a tool confirmation. Correct gate:

```python
if event.type == "session.status_terminated":
    break
if event.type == "session.status_idle":
    if event.stop_reason.type == "requires_action":
        continue          # it is waiting on us — handle it
    break                 # end_turn, retries_exhausted, budget_reached
```

Harmless in the one-shot scripts. In a multi-turn chat it truncates replies mid-answer.

**2. The curator cannot see the memory store.**
`stretch_memory_curator.py` calls `sessions.create(agent=curator_id)` with no
`environment_id` and no `resources`, then asks the agent to curate a store it was never
given. It needs the same `memory_store` resource block as any other session.

**3. Stores mount under their own name.**
With two stores attached the mount is `/mnt/memory/<store-name>/`, not a flat
`/mnt/memory/`. Tell the agent to `ls -R /mnt/memory/` first rather than hard-coding paths
in the system prompt.

**4. No `.gitignore`.**
The scripts write `.agent_id`, `.environment_id`, `.memory_store_id`, `.curator_agent_id`
and `outputs/` into the repo root. Without a `.gitignore`, those — and any `.env` someone
creates — get committed. Fixed in the same commit as this file.

**5. The pinned model is old.**
`create_agent.py` pins `claude-sonnet-4-6`. See the decision log below.

---

## 5. Decision log

Each of these was a real fork in the road. The reason matters more than the choice.

| Decision | Why |
|---|---|
| **Memory stores, not a vector DB** | The whole store is a few dozen short files. The agent greps it faster than we could stand up Chroma, and embeddings buy nothing at this scale. Costs ~40 minutes we do not have. |
| **The session *is* short-term memory** | Stateful, cached and auto-compacting out of the box. Building a buffer is strictly worse and strictly slower. |
| **Two stores per session** | Gives per-user isolation and a shared source of truth as a property of session creation rather than as code. Also directly answers the first question any enterprise reviewer asks. |
| **Promote only at consolidation** | Makes the interesting decision happen at one observable moment instead of scattered across turns. |
| **`claude-opus-5` for the main agent** | Consolidation quality *is* the product — deciding what deserves to be remembered is a judgment task. `claude-sonnet-5` is the fallback if on-stage latency becomes a problem; that is a deliberate call, not a default. |
| **`claude-haiku-4-5` for the curator** | Housekeeping needs speed and low cost, not judgment. Matches what the upstream repo already does. |
| **Streamlit for the UI** | `st.chat_message` + `st.chat_input` is a working chat in ~15 lines; `st.columns` puts the memory panel beside it; the sidebar is the user switcher. Free, no build step. |
| **A JSON file for local state** | All we persist locally is `user → memstore_id` plus the agent/env IDs. There is no query here worth a schema. |
| **The curator as a scheduled deployment** | Memory hygiene is cadence work — nobody triggers it. This is what a deployment is *for*, and it is the piece that makes the project read as a system. |
| **Provision once, commit the IDs** | Three people running `create_agent.py` means three agents, three environments, and an afternoon wondering why memory is empty. |

---

## 6. Constraints

- **Two hours, hard stop.** Every choice above is optimized for minutes-to-working-demo.
- **Shared workspace API key.** Cap deployment spend with `budget.max_list_cost` — an
  uncapped cron job is the classic way to drain a hackathon key overnight.
- **Max 8 memory stores per session.** One deployment covers up to 8 demo users.
- **Memory stores attach at session-create time only.** `sessions.resources.add()` does not
  accept `memory_store`.
- **`anthropic>=0.116.0`**, already pinned by the repo's `requirements.txt`.

### Hard rule: never write a secret to long-term memory

Memory persists across sessions and is replayed **verbatim** into every future context. A
key written once is in every later session that mounts the store. There is no unsee — the
recovery path is deleting the memory *and* redacting the affected versions. The system
prompt carries an explicit NEVER clause for this; do not remove it.

---

## 7. Explicitly out of scope

Refuse these out loud when someone suggests them:

- Embeddings or a vector database
- Real authentication (a dropdown of three names is the user model)
- A database of any kind
- Multi-agent routing (impressive on a diagram, invisible in a two-minute demo)
- Hosting the UI on Managed Agents — **it deploys agents, not web apps**. Streamlit runs on
  the demo laptop.
- A second deployment, or a webhook receiver
- Tests, Docker, type hints, a polished README

---

## 8. Where things are

- **`PLAN.md`** — the 120-minute schedule, function contracts, system prompt, and the code
  blocks to copy. That is the operational doc; this one is the reasoning behind it.
- **Upstream** — `rosscrooke/institutional-memory`. Add the remote if you want to pull
  organizer fixes mid-hackathon:
  `git remote add upstream https://github.com/rosscrooke/institutional-memory.git`
- **Console** — every session has a live trace view. Keep that tab open while building.
