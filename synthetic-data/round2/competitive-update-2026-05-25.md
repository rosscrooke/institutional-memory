# Competitive Update — 2026-05-25

*Effective 2026-05-25. Issued by Helios Product Management (Anders Lundqvist) and Competitive Intelligence (Priya Naidu). Distribute to all live deals.*

Two things changed this week. Both matter for the Northwind deal.

## 1. StreamCorp price cut and connector launch

On 2026-05-23 StreamCorp announced:

| Change | Detail |
| --- | --- |
| **List-price cut** | **~20% across all managed tiers**, effective 2026-06-01. Their "Enterprise" tier drops from $1.10 to $0.88 per GB ingested. |
| **New connector** | A **native managed Salesforce CDC connector**, GA today. Helios does not have a first-party equivalent; we recommend Debezium today. |
| **Positioning** | Their press release explicitly targets "EU financial-services customers re-evaluating their Kafka spend." That is Northwind, by name in all but the headline. |

**Impact on Northwind:** Klara will see the price cut. She is comparing total cost line-by-line. Our $4.1M number now looks materially worse next to a StreamCorp comparable; expect her to push hard on TCO at the final pitch.

**Impact across the book:** Account teams should expect the price-cut question on every active deal this quarter. Holding line on list price is endorsed by leadership — discount only through the standard approval flow.

## 2. Helios ships two features that directly help us here

Effective today (2026-05-25), the following are **GA**:

### a. Native active-active multi-region replication

| Capability | Detail |
| --- | --- |
| **Topology** | Both regions take writes simultaneously. Conflict resolution via per-record vector clocks. |
| **RPO** | **Sub-5-second** under documented network conditions (cross-region p99 latency under 80ms). Northwind's Frankfurt ↔ Dublin path is ~12ms — well inside spec. |
| **Failover** | Automatic. No operator action required. Failover demonstrated under load in our internal chaos tests at 1.2M events/sec. |
| **Available regions** | Frankfurt, Dublin, Virginia (and 8 others). All three Northwind regions are covered today. |
| **Pricing** | Included in Enterprise tier — no additional line item. |

**This directly answers Sven Aaltonen's 2026-05-22 objection.** It also pre-empts the StreamCorp comparison: StreamCorp's equivalent is active-passive only and they have no announced timeline for active-active.

### b. Residency pinning

| Capability | Detail |
| --- | --- |
| **What it does** | Per-record region tagging enforced at write time. A record tagged `eu` cannot be replicated, mirrored, or read from a non-EU broker — enforced at the broker level, not at the application level. |
| **Auditability** | Per-record residency events streamed to a customer-controlled audit topic. |
| **Pricing** | Included in Enterprise tier. |

This strengthens our answer to Marcus Lehmann's residency objection (#2 in the log). The signed attestation we already provide is now backed by a broker-level enforcement, not just a deployment guarantee.

## Recommended message changes for the Northwind final pitch

1. **Lead with the active-active capability.** Sven raised this as a deal-breaker. Walking in without it on slide 1 of the resilience section is a miss.
2. **Use the StreamCorp price cut as the *entry point* for the TCO conversation,** not as a defensive response. Acknowledge it, then point at the operational savings and the active-active inclusion — StreamCorp's $0.88/GB does not include active-active, and a self-build on top of StreamCorp wipes out their price advantage.
3. **Position residency pinning alongside the attestation** to convert Marcus's "open" objection into "closed."
4. **Do not engage on the Salesforce CDC connector unless asked.** Northwind has not raised it. If they do, the answer is: Debezium today, first-party connector on the roadmap for 2026-Q4.

## What is still not addressed

- Helios does not have a first-party Salesforce CDC connector. If Northwind asks, see above.
- Active-active is GA today but Northwind would be one of the earliest production deployments at their scale. We should offer a named TAM and weekly check-ins for the first 90 days post-cutover. Get sign-off from delivery before promising this.

## Next steps for the Northwind account team

- Update the pitch deck (v3.1 → v3.2) to insert a resilience slide before pricing.
- Brief the SE on the active-active failover demo — there is a canned demo cluster available, ask Anders.
- Final pitch is 2026-06-02. Internal dry-run on 2026-05-29.
