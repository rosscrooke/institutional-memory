---
client: Verdant Ridge Outfitters
type: email
date: 2026-08-11
title: Snowflake access - security review
from: Gus Harmon <gus.harmon@verdantridge.example>
to: Kenji Watanabe
cc: Camille Dubois, Jordan Reyes
---

Subject: Snowflake access - security review

Kenji,

I got Camille's request for a service account. Status and some bad news.

Our security team requires a vendor risk assessment for any external party touching production data. That questionnaire takes them 3-4 weeks once submitted. I submitted it on Aug 4th, so earliest is around Aug 25 - Sept 1.

In the meantime I can give you access to a **sanitized sample**: 6 months of sales for the top 200 SKUs, with store IDs hashed. It won't have promotions data or customer info. It's enough to build and test the pipeline, not to make real forecasts.

I'll need from you:
- Your IP range for allowlisting
- The names of everyone who will use the account (max 3, named individuals, no shared logins)
- A SOC 2 report or equivalent. Camille said you have one?

Also: the read-only role will be limited to the `FORECAST_SANDBOX` schema. If you need other tables later, we need a request through the data governance board, which meets monthly. Next meeting is Sept 9.

Let me know if this works.

Gus
