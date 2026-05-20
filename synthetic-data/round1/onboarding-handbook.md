# BTS-Synthetic Engineering Onboarding Handbook

*Version 4.2 — Effective January 2026*

Welcome to BTS-Synthetic Engineering. This handbook covers everything you need in your first two weeks.

## Day 1 — Equipment and accounts

You'll receive a laptop, a YubiKey, and credentials for the following:
- Email (your firstname.lastname@bts-synthetic.example)
- Slack
- GitHub (organization: `bts-synthetic`)
- Read-only access to staging environments

You will **not** receive prod access on day 1. See "Getting prod access" below.

## Day 2-5 — Your buddy and your team

Your manager will pair you with a buddy for your first two weeks. Spend time with them. They'll walk you through:
- The codebase tour
- Our git workflow (trunk-based, all changes via PR, two approvals to merge)
- The on-call rotation
- The post-mortem culture (blameless, written within 48 hours of any P0 or P1)

## Getting prod access

Prod access at BTS-Synthetic is split into three levels:

1. **Read-only** — for debugging. Available after 2 weeks of tenure and one completed pairing session with an SRE.
2. **Read-write** — for routine ops. Available after 6 weeks and SRE sign-off.
3. **Privileged** — for incident response. Available after on-call certification (12 weeks).

To request read-only access:

1. Open a ticket in the `#sre-access-requests` Slack channel.
2. Tag your manager and an SRE for sign-off.
3. The SRE on rota that week will pair with you to walk through the access tooling.
4. Once paired, the SRE files your access in our IAM tool. Access is granted within 4 working hours.

The SRE on rota changes weekly. Check the on-call schedule in PagerDuty for the current week.

## Key people

| Role | Name | Slack handle |
| --- | --- | --- |
| Head of Engineering | Anika Reddy | @anika |
| Head of SRE | Carlos Mendes | @carlosm |
| Head of Platform | Yuki Tanaka | @yuki |
| Head of Security | Maya Singh | @maya-s |
| Engineering Ops Lead | Tom Bryce | @tomb |

## Service ownership

| Service | Owning team | Tech lead |
| --- | --- | --- |
| payment-service | Payments | Tom Bryce |
| auth-service | Platform | Yuki Tanaka |
| signing-service | Platform | Yuki Tanaka |
| tenant-config-service | Platform | Yuki Tanaka |
| frontend | Web | Priya Shah |

For ownership of any service not listed, run `gh repo view --json owners <service>` in our org.
