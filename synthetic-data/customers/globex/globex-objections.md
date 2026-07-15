# Globex Retail — Objections Log

*Effective Q1 2026. Each objection paired with our current best answer.*

## 1. "We're happy with Pub/Sub — why switch?"

Our answer: Helios adds exactly-once processing and a unified connector
catalog (BigQuery, Shopify, Salesforce) that Pub/Sub + Dataflow require glue
code for. Migration is incremental — run side-by-side during one peak season.

## 2. "Cost at idle is our biggest fear."

Our answer: Helios autoscales to near-zero between peaks; you pay for
throughput, not provisioned capacity. We will model their Black-Friday curve
in the POC.

## 3. "We have no EU footprint — don't sell us residency."

Our answer: Understood — residency pinning is available but off by default for
Globex. We focus the pitch on elasticity and connector breadth instead.
