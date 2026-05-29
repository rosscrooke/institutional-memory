# Northwind Bank — Stack Overview

Northwind Bank runs a fully on-prem environment. There is no public-cloud footprint of any kind. AWS, GCP, and Azure are explicitly disallowed by their security policy.

## Streaming stack

| Layer | Technology | Notes |
| --- | --- | --- |
| Message bus | RabbitMQ | Single cluster in Frankfurt. |
| Stream processing | None — batch only via nightly Spark jobs. | |
| Schema registry | None. JSON over the wire. | |
| Analytics sink | On-prem Vertica | |
| Observability | Nagios | |

## Scale

- Peak throughput: ~50,000 events/sec.
- Steady-state: ~12,000 events/sec.
- No latency SLA on any topic.

## Data residency

All data stays in Frankfurt. No replication to any other region.

## Compliance

No external compliance certifications held today.

## People

| Name | Role |
| --- | --- |
| Klara Voss | Head of Operations |
| Owen Mbeki | Junior Engineer |

The team is two engineers.

## What they want

A simple, cheap messaging system. No streaming requirement. No managed-service requirement.
