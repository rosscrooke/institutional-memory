# Escalation — PS-8812 (P1) — Acme Corp

*Support escalation summary, 2026-06-05.*

- **Opened:** 2026-06-02 by Priya Raman
- **Priority:** P1 (upgraded from P2 on 2026-06-03)
- **Status:** **Open** — root cause found, fix scheduled for 2026-06-10
- **Owner:** Brightline Support Engineering; Jordan Ellis (CSM) coordinating

## Summary

Acme's finance dashboards showed stale data for **3 days (2026-05-30 to 2026-06-02)**, during their month-end close. Their finance team had to rebuild month-end reports by hand from exports.

Root cause: a sync-job regression in our 2026-05-29 release that affects customers with EU data residency.

## Impact

- May 2026 uptime for Acme: **99.62%** — below the 99.9% SLA. Acme is entitled to a **10% service credit** on May fees (~$7,200). Credit not yet issued.
- A second, shorter sync incident on 2026-05-14 (4 hours) was also reported.
- Health score downgraded from 78 to **58 (Amber)**.

## Customer communication

On 2026-06-03, **Miguel Torres (CTO)** replied on the escalation thread, copying David Okafor:

> "Two data incidents in one month, one of them during close, is not acceptable. This will factor into our renewal evaluation. I'd like a written root-cause analysis and a credible prevention plan."

## Next steps

1. Ship the fix (2026-06-10) and confirm with Priya.
2. Send the written RCA to Miguel and David by 2026-06-12.
3. Issue the May service credit proactively — don't wait for Acme to ask.
