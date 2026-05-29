# Objections Log — Northwind Bank

*Effective January 2026. Maintained by the Helios account team. Updated after every call.*

This log records every objection Northwind has raised across the pitch cycle so far, together with our current best answer. Each entry is dated. If the answer changes, supersede the row and note the date — don't delete history.

## How to read this

- **Objection** — what they said, in their words where possible.
- **Raised by / when** — name + call date.
- **Our current best answer** — what we say today. Replace when product/marketing gives us a better one.
- **Status** — `open` (they aren't convinced yet), `parked` (acknowledged, not blocking), `closed` (they agreed).

## Active objections

### 1. Latency SLA vs self-managed Kafka

- **Raised by:** Raghav Iyer (Streaming Tech Lead)
- **When:** 2025-11-14 technical deep-dive
- **Objection:** "Our self-managed Kafka hits p99 ~42ms on the payments topic. A managed service can't beat that — every benchmark I've seen adds 10-20ms of overhead."
- **Our current best answer:** Helios runs on dedicated single-tenant brokers in the customer's choice of region. In the most recent benchmark (2025-Q4, attached deck slide 14) Helios hit p99 38ms on a payments-shaped workload at 700k events/sec. We offer a 60ms p99 contractual SLA with service credits — well inside their 50ms internal target with headroom.
- **Status:** open — Raghav wants to run his own bake-off before he believes the numbers.

### 2. Data residency / on-prem requirement

- **Raised by:** Marcus Lehmann (Security Architect)
- **When:** 2025-11-21 security review
- **Objection:** "Our regulators expect EU customer data to never leave the EU, and our internal policy requires the actual brokers to be physically in-region. A US-headquartered SaaS vendor running shared infrastructure is a non-starter."
- **Our current best answer:** Helios offers region-pinned dedicated deployments in Frankfurt, Dublin, and Virginia today. Customer data, broker storage, and the control plane for that customer's region all stay in-region. We provide a signed data-residency attestation per region and our SOC 2 + ISO 27001 reports cover all three. We can run the brokers in either our region or theirs (BYOC on AWS, GCP, Azure) — their choice.
- **Status:** open — Marcus is reading the attestation; expected sign-off by end of Q1.

### 3. Total cost vs existing Kafka

- **Raised by:** Klara Voss (Head of Platform Engineering)
- **When:** 2025-12-05 business case review
- **Objection:** "Our existing Kafka costs us ~$3.2M/year all-in including the team. Your ballpark is $4.1M. Why would I pay 28% more for the same thing?"
- **Our current best answer:** Three points. (1) The $3.2M number excludes the on-call cost — Hina's team logs ~40 hours/month of Kafka-related incident work; we cap that at zero. (2) Helios includes Flink-as-a-service in the same envelope, replacing ~$400k of separate Flink infra. (3) Our 3-year TCO model (deck slide 21) shows break-even in month 22 and a $1.8M cumulative saving by year 5. We will share the model with their finance team.
- **Status:** open — Klara wants the model run against her own incident-hours numbers, not ours.

### 4. Migration risk

- **Raised by:** Raghav Iyer
- **When:** 2025-12-12 architecture session
- **Objection:** "We can't do a big-bang cutover. The payments topic is too critical. And we have 140 Flink jobs that all need to keep working."
- **Our current best answer:** Helios supports the Kafka wire protocol natively — existing Flink jobs connect with a connection-string change, no code rewrite. The recommended migration is topic-by-topic, starting with low-criticality (fraud-features, audit-log), then mid (risk), and payments last after a parallel-run period. Typical migrations of this size run 4-6 months. We assign a named Helios SE to embed with their team for the duration at no extra cost.
- **Status:** open — they want a written runbook before committing.

### 5. Vendor lock-in

- **Raised by:** Klara Voss
- **When:** 2025-12-05 business case review
- **Objection:** "If we go all-in on Helios and you raise prices 40% in year 3, we have no leverage."
- **Our current best answer:** Helios speaks vanilla Kafka. Any client, any consumer, any Kafka tool works against Helios with no Helios-specific code. Exit cost = MirrorMaker job to a destination cluster. Contractually we offer a 3-year price lock with annual increases capped at CPI. We will also commit to a documented "exportability test" annually — your team runs a one-day exercise replicating a topic out to a destination cluster and we share the report.
- **Status:** parked — Klara accepted the protocol-compat argument; the price-lock language is in legal review.

## Closed objections

### 6. Open source vs proprietary

- **Raised by:** Owen Mbeki (Senior Platform Engineer)
- **When:** 2025-10-30 first technical chat
- **Objection:** "We've always built on open source. We don't want to be the only bank running a proprietary stack."
- **Our current best answer:** Helios is wire-compatible with Apache Kafka and contributes upstream to Kafka, Flink, and Schema Registry. Three named customers in EU banking are referenceable (one Tier-1).
- **Status:** closed 2025-11-14 — Owen accepted after a reference call with one of the named customers.
