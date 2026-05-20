# Stretch Goals — Option 2

Pick at least one. Memory is the topic most clients ask about — these stretch goals are the talking points you'll repeat back to them.

---

## Tier 1 — Make memory deliberate

### S1. Explicit memory policy in the system prompt
Open `create_agent.py`. Add to the system prompt: a list of categories the agent should ALWAYS remember and a list it should NEVER remember. Re-create the agent. Re-run both sessions.

Compare the new outputs to the originals — the agent's memory store should now be tighter and more useful.

**Why this lands:** "What does my agent remember?" is the question every privacy/security team will ask. Showing you can answer it precisely is the entire game.

### S2. The Memory Curator sub-agent
Run `python stretch_memory_curator.py`. This creates a second agent whose only job is housekeeping on the first agent's memory store. After running it, re-run session 2 and see if the answer is even sharper.

**Why this lands:** Memory hygiene as a *role*, not a feature. Now you've got a multi-agent system whose architecture maps directly to how human teams keep institutional knowledge clean.

---

## Tier 2 — Stress-test memory

### S3. Adversarial round
Create `synthetic-data/round3/` with documents that are deliberately wrong — they contradict round1 with no plausible reason for the contradiction. Run a third session.

Does the agent:
- Flag the contradiction?
- Ask you which to trust?
- Just silently update memory and answer wrong?

The right behaviour is "flag and ask." If the agent silently updates, that's a memory policy bug you've just discovered — fix the system prompt.

**Why this lands:** Shows that you can engineer memory to be robust against bad inputs, which is the only way clients will trust it.

### S4. The "what have you learned?" test
Add a third session where you don't upload any new docs. The only message is:
> "Summarise everything you've learned about this domain across our previous sessions."

The answer is the most direct demo of what's in memory.

**Why this lands:** Lets you literally show the memory store talking back. Hugely demo-able.

---

## Tier 3 — Make memory production-shaped

### S5. Per-tenant memory via metadata
Modify the agent to scope its memory by a `customer_id` metadata key. Run two sessions for "Acme Corp" and two for "Globex Inc." — verify that Acme's facts don't leak into Globex's answers.

**Why this lands:** First question every multi-tenant SaaS will ask: "how do you keep customers' data separated?"

### S6. Memory + Routines combination
Wrap session 1 in a Routine that fires daily, ingesting new docs from a folder. Now memory accumulates passively.

**Why this lands:** Now you've got a fully autonomous learning agent.

### S7. Long-context with compaction
Push the agent to 20+ turns in a single session. Use [context editing / compaction](https://platform.claude.com/docs/en/build-with-claude/compaction) to keep it sharp over long sessions, then commit the compacted summary to memory.

**Why this lands:** Demonstrates the difference between *in-session memory* (the context window) and *across-session memory* (the Memory tool) — a distinction most teams haven't internalised yet.

---

## Tier 4 — For the showoffs

### S8. The "memory diff" view
Build a tiny script that diffs the memory store between session 1 and session 2 and prints what changed. This becomes the headline of your demo.

### S9. Memory + sub-agents at session level
Have the agent spawn a sub-agent per topic in its memory store. Each sub-agent is the canonical expert on that topic. The main agent routes questions to the right sub-agent based on memory keys.

Now you've built an org chart out of memory.

**Why this lands:** This is the architecture that will be in every "AI-native enterprise" pitch deck six months from now.
