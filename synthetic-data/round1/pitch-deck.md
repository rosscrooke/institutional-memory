# Helios → Northwind Bank — Pitch Deck

*Version 3.1 — Effective January 2026. Owned by the Helios account team.*

The deck has gone through three revisions since the first meeting in October 2025. This is the version we are walking in with for the next call. The deck itself lives in the shared drive; this document describes the **sequence, the message of each slide, and the speaker notes** so the on-call SE can pick it up cold.

## Audience for this version

Mixed room: Klara Voss (economic buyer), Raghav Iyer (technical), Marcus Lehmann (security), with Hina Park and Owen Mbeki joining for the technical sections. 90 minutes, deck-driven, with two demo cut-aways.

## Sequence

| # | Slide | Owner on the call | Notes |
| --- | --- | --- | --- |
| 1 | Title + agenda | Account exec | Set the 90-minute frame. State the three things we want them to leave with. |
| 2 | The problem we keep hearing | Account exec | Self-managed Kafka at this scale is six FTE of toil. Frame their pain in their words from the last call. |
| 3 | Helios architecture overview | SE | Single-tenant brokers, region-pinned. Show the same diagram they've seen, but with Northwind's three regions filled in. |
| 4 | Where Helios sits in their stack | SE | Side-by-side: their current architecture vs target architecture. MirrorMaker → Helios cross-region. Flink stays. Schema Registry stays. |
| 5 | Managed vs self-managed — what we take off your team | SE | Klara's slide. List the operational toil categories with hours/month numbers from her own team's incident reports. |
| 6 | TCO model | Account exec | Walk slide 21 numbers: $3.2M baseline vs $4.1M Helios but with $400k Flink savings + $700k incident-hours savings → net $200k/yr cheaper from year 2. Break-even month 22. |
| 7 | Security and residency | SE | Marcus's slide. Region-pinned brokers, signed attestations, SOC 2 / ISO 27001 / PCI DSS Level 1 in scope. BYOC option. |
| 8 | Demo cut-away #1 — provisioning a region-pinned cluster | SE | 5 minutes live. Frankfurt cluster, show the residency lock in the console. |
| 9 | Migration path | SE | Topic-by-topic. Low-criticality → mid → payments last. Named Helios SE embedded. 4-6 months target. Runbook attached as appendix. |
| 10 | Demo cut-away #2 — Flink job switching backends with a connection-string change | SE | 5 minutes live. Reuse one of Anya's job shapes if possible. |
| 11 | Pricing | Account exec | $4.1M year 1, CPI-capped increases, 3-year term, documented exportability test. Address the lock-in concern here before they raise it. |
| 12 | Next steps | Account exec | Three asks: (a) Raghav's bake-off — we'll provide a target cluster within 7 days. (b) Marcus's residency attestation review by end of Q1. (c) Klara's finance team reviews the TCO model against their own numbers. |
| 13 | Q&A backstop | — | Held slides covering: Kafka version compatibility, MirrorMaker handoff, Flink-as-a-service detail, exit/exportability test, support SLA. |

## Speaker notes — key points to land

- **Open with their pain, not our features.** Slide 2 must come from their words. Quote Hina from the 2025-12 call: *"Every weekend on-call is at least one Kafka page."*
- **The TCO slide is the hinge.** If we lose Klara on TCO we lose the deal. The break-even-at-month-22 chart is the one slide she will photograph.
- **Marcus's slide is gated by paperwork, not persuasion.** Don't oversell — point at the attestation and the audit reports and move on.
- **The migration slide is the slide Raghav cares about most.** Show, don't tell. The runbook appendix is more important than the deck slide.
- **Do not get pulled into a Kafka feature-comparison.** If Raghav goes there, take the question to the technical session next week.

## What we are NOT pitching in this deck

- Helios's analytics layer. Northwind has Redshift + EMR working; we're not going to dislodge it this cycle.
- AI / ML features. Northwind has no internal ML use case for streaming today.
- Multi-cloud portability beyond BYOC. They are AWS-only for cloud and want to stay that way.

## Open issues going into the call

1. Raghav's bake-off has not been scheduled. We are blocked on him picking a workload shape.
2. The TCO model has Klara's incident-hours number plugged at our estimate, not hers. She will push on this.
3. The migration runbook is at v0.4 — usable but needs a final review by our delivery team before we let it leave the room.
