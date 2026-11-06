---
last_reviewed: 2026-01-12
owner: Maya Singh (Head of Security)
source: Production Access Policy, Jan 2026; Onboarding Handbook v4.2
---
# Production access policy

Effective January 2026. Three levels:

| Level | Eligibility | Use |
| --- | --- | --- |
| Read-only | 2 weeks tenure + 30-min pairing session with the SRE on rota | Debugging, logs, observability |
| Read-write | 6 weeks + read-only + tech lead sign-off + SRE sign-off | Config changes, restarts |
| Privileged | On-call certification (~12 weeks) | Incident response, rollback, IAM |

## Requesting read-only access
1. Open a ticket in `#sre-access-requests` (Slack).
2. Tag your direct manager AND the SRE on rota this week (see PagerDuty).
3. The SRE schedules the pairing session within 2 working days.
4. After pairing, the SRE grants access in Okta, usually within 4 hours.

## Urgent exception
For a P1, the on-call SRE can grant temporary 24h read-only access without pairing.
Pairing must follow within 5 working days or access is revoked automatically.
