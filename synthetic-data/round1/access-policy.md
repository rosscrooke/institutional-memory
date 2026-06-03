# Production Data Access Policy

*Effective January 2026. Owned by Maya Singh (Head of DataSec).*

This is the authoritative source for how production data access is granted at BTS-Synthetic.

## Three levels

1. **Read-only** — Eligibility: 2 weeks of tenure + completed pairing session with a Data Platform Engineer (DPE). Use: debugging, lineage tracing in Collibra, observability, log access.
2. **Read-write** — Eligibility: 6 weeks of tenure + read-only level + tech lead sign-off + DPE sign-off. Use: Dagster pipeline configuration changes, restart commands.
3. **Privileged** — Eligibility: on-call certification (typically 12 weeks). Use: incident response, emergency rollback, access-broker and IAM changes.

## Standard read-only access request

1. Engineer opens a ticket in `#data-access-requests`.
2. Engineer tags their direct manager AND the DPE on rota for that week.
3. DPE on rota schedules a 30-minute pairing session within 2 working days.
4. After pairing, DPE files the access via Okta. Provisioning typically completes within 4 hours.

## Exception: urgent access requests

If an engineer needs urgent read-only access (e.g., to debug a P1 data-quality incident), the on-call DPE may grant temporary 24-hour access without a pairing session. The pairing session must happen within 5 working days of the grant or the access is revoked automatically.

## Review cadence

This policy is reviewed quarterly by DataSec and Data Engineering leads. Last review: 2025-12-15.
