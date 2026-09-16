# Production Access Policy

*Effective January 2026. Owned by Maya Singh (Head of Security).*

This is the authoritative source for how production access is granted at BTS-Synthetic.

## Three levels

1. **Read-only** — Eligibility: 2 weeks of tenure + completed pairing session with SRE. Use: debugging, observability, log access.
2. **Read-write** — Eligibility: 6 weeks of tenure + read-only level + tech lead sign-off + SRE sign-off. Use: configuration changes, restart commands.
3. **Privileged** — Eligibility: on-call certification (typically 12 weeks). Use: incident response, emergency rollback, IAM changes.

## Standard read-only access request

1. Engineer opens a ticket in `#sre-access-requests`.
2. Engineer tags their direct manager AND the SRE on rota for that week.
3. SRE on rota schedules a 30-minute pairing session within 2 working days.
4. After pairing, SRE files the access via Okta. Provisioning typically completes within 4 hours.

## Exception: urgent access requests

If an engineer needs urgent read-only access (e.g., to debug a P1 incident), the on-call SRE may grant temporary 24-hour access without a pairing session. The pairing session must happen within 5 working days of the grant or the access is revoked automatically.

## Review cadence

This policy is reviewed quarterly by Security and SRE leads. Last review: 2025-12-15.
