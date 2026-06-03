# BTS-Synthetic Data Platform Onboarding Handbook

*Version 4.2 — Effective January 2026*

Welcome to BTS-Synthetic. We build the data platform and the cross-fintech **data exchange** that lets partners share and consume regulated financial data. This handbook covers everything you need in your first two weeks.

## Day 1 — Equipment and accounts

You'll receive a laptop, a YubiKey, and credentials for the following:
- Email (your firstname.lastname@bts-synthetic.example)
- Slack
- GitHub (organization: `bts-synthetic`)
- Dagster (pipeline orchestration)
- Collibra (data catalog and lineage)
- Read-only access to staging environments and the sandbox data exchange

You will **not** receive production data access on day 1. See "Getting production data access" below.

## Day 2-5 — Your buddy and your team

Your manager will pair you with a buddy for your first two weeks. Spend time with them. They'll walk you through:

- The codebase and data-platform tour
- Our git workflow (trunk-based, all changes via PR, two approvals to merge)
- The data on-call rotation
- The post-mortem culture (blameless, written within 48 hours of any P0 or P1 — including data-quality and data-leak incidents)

## Getting production data access

Production data access at BTS-Synthetic is split into three levels:

1. **Read-only** — for debugging and lineage tracing (in Collibra). Available after 2 weeks of tenure and one completed pairing session with a Data Platform Engineer (DPE).
2. **Read-write** — for routine pipeline ops (Dagster runs and config). Available after 6 weeks and DPE sign-off.
3. **Privileged** — for incident response and access-broker changes. Available after on-call certification (12 weeks).

To request read-only access:

1. Open a ticket in the `#data-access-requests` Slack channel.
2. Tag your manager and a DPE for sign-off.
3. The DPE on rota that week will pair with you to walk through the access tooling and our data-handling rules.
4. Once paired, the DPE files your access in our IAM tool. Access is granted within 4 working hours.

The DPE on rota changes weekly. Check the on-call schedule in PagerDuty for the current week.

## Key people

| Role | Name | Slack handle |
| --- | --- | --- |
| Head of Data & AI | Anika Reddy | @anika |
| Head of Data Engineering | Carlos Mendes | @carlosm |
| Data Platform Lead | Yuki Tanaka | @yuki |
| Head of DataSec | Maya Singh | @maya-s |
| Data Developer Experience Lead | Tom Bryce | @tomb |

## Service ownership

| Service | Owning team | Tech lead |
| --- | --- | --- |
| ingestion-pipeline | Data Engineering | Tom Bryce |
| exchange-api | Data Platform | Yuki Tanaka |
| catalog-service | Data Platform | Yuki Tanaka |
| access-broker | Data Platform | Yuki Tanaka |
| exchange-portal | Web | Priya Shah |

For ownership of any service not listed, run `gh repo view --json owners <service>` in our org.
