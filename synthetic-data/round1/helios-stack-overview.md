# Northwind Bank — Stack Overview

*Effective January 2026. Compiled by the Helios pre-sales team from discovery calls held 2025-11 through 2026-01.*

This is the authoritative snapshot of Northwind Bank's current data-streaming environment going into the Helios pitch cycle. Keep this updated as we learn more on each call.

## Business context

Northwind Bank is a top-20 EU/US retail and commercial bank. They are mid-way through a five-year platform modernisation. Streaming is the long pole: their fraud, payments, and risk teams all sit downstream of the same Kafka backbone, and outages there cascade fast.

## Current streaming stack

| Layer | Technology | Notes |
| --- | --- | --- |
| Message bus | Apache Kafka 3.6 (self-managed) | 3 on-prem clusters: Frankfurt (EU primary), Dublin (EU DR), Virginia (US). Cross-cluster mirroring via MirrorMaker 2. |
| Stream processing | Apache Flink 1.18 | ~140 jobs in production. Mostly Java; some PyFlink for analytics. |
| Schema registry | Confluent Schema Registry (OSS) | Avro everywhere; Protobuf on the newer payments topics. |
| Analytics sink | AWS (S3 + Redshift + EMR) | Only place AWS is allowed in the data path today. Read-only from the bank's perspective. |
| Observability | Prometheus + Grafana, Datadog for APM | |
| Identity | Internal LDAP + Okta (for AWS) | |

## Scale and SLAs

- Peak throughput: **~2M events/sec** across all three clusters. Payments alone peaks ~600k events/sec on Black Friday / month-end close.
- Steady-state: ~700k events/sec.
- Internal SLA: **p99 producer→consumer latency under 50ms** on the payments topic. They currently hit ~42ms p99.
- Availability target: 99.95% on the payments path; 99.9% on fraud/risk.

## Data residency

- **Hard constraint:** EU customer data must remain in EU (Frankfurt or Dublin). US customer data must remain in US (Virginia).
- Set by the bank's legal and compliance teams in line with GDPR + state-level US banking law.
- Any cross-region replication must be encrypted in transit, key-pinned to region, and auditable per-record.

## Compliance posture

- **SOC 2 Type II** — renewed annually, last audit 2025-09.
- **PCI DSS Level 1** — payments topics in scope. Quarterly ASV scans.
- Internal data-classification standard requires customer PII to be tokenised before it hits any analytics sink.

## People — Northwind platform team

| Name | Role | Notes |
| --- | --- | --- |
| Klara Voss | Head of Platform Engineering | Economic buyer. Pragmatic, sceptical of "rip-and-replace" pitches. |
| Raghav Iyer | Streaming Tech Lead | Owns the Kafka and Flink estate. Will run the bake-off. |
| Hina Park | SRE Lead | Cares most about incident response and on-call burden. |
| Marcus Lehmann | Security Architect | Reports into the CISO. Owns residency and encryption sign-off. |
| Anya Petrov | Data Engineering Lead | Downstream consumer; cares about Flink job stability. |
| Owen Mbeki | Senior Platform Engineer | Day-to-day operator. Will tell us what actually hurts. |

The team is **six engineers, no headroom**. Klara has been clear that the business case has to include reducing operational load, not just feature parity.

## What they've told us they want

1. Lower operational burden than self-managed Kafka.
2. No regression on the 50ms p99 payments SLA.
3. Residency guarantees they can defend to their regulators.
4. A migration path that does not require a "big bang" cutover.
5. Predictable, capped pricing — they have been burned by usage-based bills before.
