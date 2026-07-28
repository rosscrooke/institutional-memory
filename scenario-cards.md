# Scenario Cards — Option 2

Each team picks ONE persona. The synthetic data folder under `synthetic-data/round1/` and `round2/` is shaped for the **New-Hire Onboarding** persona by default — for the other personas you can tweak the docs lightly to fit.

---

## Card A — New-Hire Onboarding Agent

**Persona:** An agent that helps new engineering hires answer onboarding questions ("How do I get prod access?", "Who owns the payments service?", "What's our git workflow?").

**Round 1 docs (already in folder):** Onboarding handbook, team directory, sample policy doc.

**Round 2 docs (already in folder):** A policy update that changes the prod access workflow, an updated team directory after a re-org.

**The test question (use this in both sessions):**
> "I just joined and I need read-only prod access to debug an issue tomorrow. What do I do?"

**What "better answer in session 2" looks like:** It cites the new policy, doesn't recommend the old workflow, and notes that the prod-access flow was updated last week.

---

## Card B — Customer Success Specialist Agent

**Persona:** An agent that supports a CSM looking after a specific enterprise customer ("Acme Corp"). It remembers Acme's history, their open issues, their contract terms, their key contacts.

**Round 1 docs:** Acme's account history, contract summary, recent support ticket log.

**Round 2 docs:** A new ticket from Acme, a contract amendment, a leadership change at Acme.

**The test question:**
> "Acme's CTO Sarah just emailed asking for a renewal proposal. What should we know going in?"

**What "better answer in session 2" looks like:** It references the new ticket and the leadership change, doesn't recommend Sarah as the contact (she's not the CTO any more), and suggests adjusting renewal terms to reflect the amendment.

---

## Card C — M&A Diligence Analyst

**Persona:** An agent supporting an M&A team diligencing a target company. It tracks what we've learned across multiple data-room reviews.

**Round 1 docs:** Target's financial summary, org chart, IP portfolio.

**Round 2 docs:** Newly disclosed liabilities, a contradicting financial restatement, updated IP claims.

**The test question:**
> "Give me your current risk assessment of this acquisition."

**What "better answer in session 2" looks like:** It flags the contradiction in the financials as a red flag, raises the risk rating, and explicitly says "this contradicts what I assessed last session."

---

## Card D — Sales Engineer for Product X

**Persona:** An agent that supports a sales engineer pitching a specific technical product. It learns the customer's environment, their objections, and our latest answers.

**Round 1 docs:** Customer's stack overview, list of objections raised in previous calls, current pitch deck.

**Round 2 docs:** A new objection from the latest call, a competitive update from product management.

**The test question:**
> "Tomorrow's call is the final pitch. What's our strategy?"

**What "better answer in session 2" looks like:** It anticipates the new objection, references the latest competitive update, and adjusts the pitch sequence rather than repeating the original plan.

---

## Card E — Personal Training Coach ← **the scenario in this repo**

**Persona:** A coach programming sessions for one client over many weeks. It
remembers their injuries, their equipment, and what they'll actually do.

**Round 1 docs:** Client intake, injuries and limitations, preferences and history.

**Round 2 docs:** A physio update (partial wrist clearance + a brand-new knee
restriction), an equipment update (bar and kettlebell added, bench broken).

**The test question (use this in both sessions):**
> "Give me my workout for tomorrow morning. 30 minutes, at home. Be specific about exercises, sets, and reps."

**What "better answer in session 2" looks like:** it reintroduces neutral-grip
pressing at the higher load and says why, keeps flat-palm loading out, avoids
deep knee flexion, substitutes off the broken bench — and still avoids burpees
and loaded spinal flexion, neither of which round 2 mentions at all.

### Why this card is the sharpest memory test

The other four cards put the answer in the round-2 documents: a stateless agent
reading only round 2 would answer the prod-access question largely correctly, and
memory shows up only as the phrase *"this changed last week."*

Here the question mentions no constraints, and round 2 restates only some of them.
That splits the memory behaviour into four separately observable outcomes:

| Constraint | Where it appears | What it tests |
| --- | --- | --- |
| Burpees, loaded spinal flexion | **Round 1 only** | **Persistence** — silence is not a clearance |
| Left knee | Round 2 only | Picking up a new constraint |
| Bench | Round 1, invalidated by round 2 | Full supersession |
| Right wrist | Both, partially changed | **Nuance** — "cleared for neutral grip" ≠ "wrist is fine" |

Row 1 is the demo. If burpees or a weighted sit-up appear in the session-2 plan,
memory failed, and nobody has to squint at the output to see it. Row 4 is the one
that separates a good answer from a lazy one: an agent that overwrites the whole
wrist entry on seeing "cleared" will wrongly allow push-ups.

---

## Picking guidance

| If your team is... | Pick |
| --- | --- |
| Most familiar enterprise scenario | A (Onboarding) |
| Best for client demo | B (Customer Success) |
| Most "executive interest" | C (M&A) |
| Most relatable to sales-led orgs | D (Sales Engineer) |
