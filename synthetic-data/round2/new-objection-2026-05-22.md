# New Objection — Northwind Bank — Call 2026-05-22

*Effective 2026-05-22. Filed by the account exec immediately after the call. Supersedes nothing in the existing log — this is a NEW objection.*

## What happened on the call

The 2026-05-22 call was supposed to be the technical close-out before the final pitch. Klara brought a new attendee we have not seen before: **Sven Aaltonen**, who joined Northwind as **CISO** in 2026-04. His mandate from the board is to harden Northwind's resilience posture before the next regulator review in October.

Sven listened for the first 20 minutes, then raised an objection that the current pitch deck does not address.

## The objection

**Sven Aaltonen, CISO, 2026-05-22:**

> "I appreciate the residency story. That's table stakes for us. What I need to see — and what the board is going to ask me about — is **active-active multi-region failover with an RPO of under 5 seconds** on the payments topic. Not active-passive with a 30-minute failover drill. Active-active, both regions taking writes, automatic reconciliation, sub-5-second data-loss window if a region goes dark.
>
> "The last outage cost us €18M in interchange and reputational damage. The board has told me directly that any new core-platform vendor must demonstrate this capability before we sign. If Helios cannot show me this, we'll have to look at building it ourselves on top of self-managed Kafka, or talk to StreamCorp — I'm told they have something."

## Why this is a new objection (not a variant of an old one)

- The existing residency objection (Marcus Lehmann, #2 in the objections log) is about *where data lives*. Sven's objection is about *how the system behaves when a region fails*.
- The existing migration objection (#4) covers gradual cutover, not steady-state resilience.
- The current deck (v3.1) does not mention failover behaviour. Slide 7 covers security and residency; slide 9 covers migration. There is no resilience slide.

## What the current best answer would be (DRAFT — not yet validated with product)

We need product management to confirm before we put this in front of Sven, but the current draft answer is:

- Helios's standard deployment is active-passive with regional failover in 60-90 seconds. That is **not** what Sven asked for.
- Active-active multi-region with sub-5s RPO is on the roadmap but the public timeline has been "H2 2026" — i.e., after Northwind's decision window.
- We need a clear answer from product on (a) whether this can be brought forward for Northwind, (b) whether a controlled GA with Northwind as the first customer is feasible, or (c) whether we need to walk away from this requirement.

## Risk

This is the biggest single risk to the deal we have surfaced. Sven explicitly named StreamCorp on the call. If we do not have a credible answer by the final pitch, we lose.

## Asks

1. Account exec to email Sven a holding response within 24 hours acknowledging the requirement and confirming a product answer at the final pitch.
2. SE to escalate to product (Helios PM for replication, Anders Lundqvist) the same day.
3. Update the pitch sequence — there must now be a resilience slide before the pricing slide.

## Next call

**Final pitch: 2026-06-02.** This objection has to be answered there or the deal moves to StreamCorp.
