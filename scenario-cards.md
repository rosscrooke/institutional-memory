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

## Picking guidance

| If your team is... | Pick |
| --- | --- |
| Most familiar enterprise scenario | A (Onboarding) |
| Best for client demo | B (Customer Success) |
| Most "executive interest" | C (M&A) |
| Most relatable to sales-led orgs | D (Sales Engineer) |
