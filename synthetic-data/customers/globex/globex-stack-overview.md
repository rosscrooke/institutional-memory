# Globex Retail — Stack Overview

*Captured from discovery calls — effective Q1 2026.*

Globex Retail is a national e-commerce and in-store retailer. This is a
**different prospect** from Northwind Bank — nothing here should be conflated
with Northwind's environment.

## Current environment

| Area | Detail |
| --- | --- |
| Cloud | All-in on **Google Cloud Platform (GCP)** — no on-prem footprint |
| Streaming today | **Google Pub/Sub** + Dataflow for clickstream and inventory events |
| Peak volume | ~150k events/sec at holiday peak (Black Friday) |
| Data residency | US-only; no EU residency requirement |
| Compliance | PCI-DSS (card payments); no SOC2 obligation today |
| Platform team | 4 engineers, plus a shared data-platform guild |

## What they care about

- **Holiday-peak elasticity** — spiky traffic, 10x for ~72 hours a year.
- **Connector breadth** — they want turnkey connectors to BigQuery, Shopify,
  and their Salesforce CRM.
- **Cost at idle** — they hate paying peak-sized infrastructure year-round.

## Key contacts

| Role | Name |
| --- | --- |
| VP Engineering | Dana Whitfield |
| Data Platform Lead | Marcus Lee |
