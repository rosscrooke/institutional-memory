# Production Access Policy — UPDATED

*Effective 2026-05-15. Supersedes the January 2026 version.*
*Owned by Maya Singh (Head of Security) and Carlos Mendes (Head of SRE).*

## What changed and why

Following the April incident review (PROD-INC-04-2026), we are tightening production access. The new policy:

- Eliminates the SRE pairing session as the access trigger (it was a bottleneck — backlog grew to 3 weeks).
- Replaces it with an **online certification** + **just-in-time access** model.
- Centralises access requests in our IAM platform, not Slack.

## New process for read-only access

1. Engineer completes the **Prod Access Foundations** course in the BTS Learning portal (90 minutes, self-paced).
2. After passing the assessment, engineer requests access through the IAM platform (link in the learning portal completion email).
3. Access is granted **just-in-time**, scoped to a 4-hour window per request. Engineers re-request as needed.
4. Engineer's manager is notified of each request. No manager sign-off required for individual requests — only for the initial certification.

**No SRE pairing session required.** No Slack ticket required.

## Tenure requirement reduced

The 2-week tenure requirement is reduced to **3 working days**. Engineers can complete the certification and request access from day 4.

## Migration

Engineers who already have read-only access under the old policy retain it through 2026-06-30, after which they must complete the new certification or lose access.

## What hasn't changed

- Read-write and privileged access requirements are unchanged.
- The on-call rotation continues to manage P0/P1 escalations.

## Why the change matters

The old policy was created when we had 40 engineers. We're now 280. The pairing-session model didn't scale. The new model is auditable, faster, and aligns with our SOC2 controls.
