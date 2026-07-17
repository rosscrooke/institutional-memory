# Clueless

An agent that learns your taste in clothes and dresses you.

**Tech:** [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) + memory stores (mounts at `/mnt/memory/`, persists across sessions).

The loop *is* the product:

```
interview -> knowledge -> suggest -> discuss -> revise
```

## The doctrine: taste accumulates, it does not supersede

This is the whole point. Read it twice.

"I hated the beige one" does **not** overturn "loves neutrals." It's one noisy data point.

When feedback contradicts an existing belief, the agent must **not** simply trust the newer thing. It must notice the contradiction and **ask**. That conversation is the feature, not a fallback — it's where the agent finds out whether beige was the problem, or the cut was, or the occasion was, or nothing was and they were just tired.

This is the opposite of a policy wiki. In a wiki, a newer dated policy genuinely voids the old one — newest wins, overwrite, move on. Taste doesn't work that way. A single reaction is evidence, not a verdict. Beliefs shift by weight of accumulated evidence, and contradictions get surfaced rather than silently resolved.

A naive agent overwrites. A good agent gets curious.

## Why it has to be personal

No fashion dataset contains human taste judgments. Not one.

Every one of them is *curated outfits vs. random junk*. Polyvore's compatibility task is literally `1 = human-curated, 0 = negative`. That teaches a model what a coherent outfit looks like in general. It teaches it exactly nothing about **you**.

Your reactions are the only real labels that exist. The loop is what generates them.

## Architecture

### The datasets give generic priors, not taste

| Dataset | Contents | What it's for |
| --- | --- | --- |
| `samples/sanzo-wada/` | 157 colors, 348 curated combination groups | color harmony ground truth |
| `samples/fashionpedia/` | 294 attributes, 46 categories | silhouette / pattern vocabulary |
| `samples/polyvore/` | items + images + outfits | the catalog to suggest **from**, plus a generic compatibility prior |

See [`samples/README.md`](./samples/README.md) for shapes and provenance.

The memory store is the **only** place personal taste lives. The datasets never learn anything about the user.

The interesting moments are where generic priors and personal memory **disagree** — Wada says those two colors clash, but they've worn them together three times and loved it. Wada isn't wrong. He just isn't them.

### Five reasoning dimensions

The agent explains its suggestions in these terms, and attributes feedback back to them:

- **color harmony**
- **formality match**
- **silhouette balance**
- **pattern load**
- **genre coherence**

Attribution is what makes feedback usable. "I hated it" is noise. "I hated it, and the agent's best guess is that pattern load was too high" is a data point that can accumulate.

### Memory layout

```
/mnt/memory/
  taste/beliefs.md          - derived beliefs, each with confidence + evidence count
                              + optional `contested` flag
  taste/observations.jsonl  - APPEND-ONLY raw reactions. Never edited.
                              These are the only real labels.
  taste/open-questions.md   - contested beliefs awaiting the user's answer
  outfits/log.md            - what was suggested, why, and how it landed
```

**Why observations are append-only but beliefs are freely rewritable:**

Observations are **data**. They're the only labels in the entire system — no dataset supplies them, they exist only because someone reacted to something. Destroy an observation and it's gone; you cannot reconstruct it from anything else. So: append, never edit.

Beliefs are a **reading** of that data. If a belief is wrong, re-derive it from the observations and it comes back correct. Rewriting a belief costs nothing, because the thing it was derived from is still intact. So: rewrite freely.

That asymmetry is the whole design. Cheap-to-rebuild layer on top of an immutable one.

### Scripts

| Script | Does |
| --- | --- |
| `create_agent.py` | one-time setup — creates the agent + environment + memory store, writes `.agent_id` / `.environment_id` / `.memory_store_id` |
| `clueless.py` | the multi-turn agent — interactive REPL |
| `inspect_memory.py` | shows what the agent chose to remember (`--full` for complete content) |
| `stretch_memory_curator.py` | stretch: a second, cheaper agent that does memory hygiene on the first one's store — merges duplicates, flags unresolved contradictions |

### Closet contract

A teammate is building this. Closets land at `closets/<persona>.json`, items carrying:

```
id, name, category, color, color_family, value, formality (1-5),
silhouette, pattern, pattern_load (0-3), genre, fabric, image
```

Until it lands, fall back to `samples/polyvore/`.

## Personas

Eight synthetic users in [`personas/`](./personas/README.md) — ages 15–75, all-black to maximalist, Jeff's total indifference to Rosa's joy. Each has a **taste shift**: a later change that a second session has to reconcile *without clobbering the rest of the profile*. That's the doctrine, in test form.

## Setup

```bash
pip install -r requirements.txt
```

Put your key in `.env` (git-ignored; the scripts load it via `python-dotenv`):

```
ANTHROPIC_API_KEY=sk-ant-...
```

Then:

```bash
python create_agent.py     # one-time
python clueless.py         # talk to it
```

Between sessions, `python inspect_memory.py` to see what stuck.
