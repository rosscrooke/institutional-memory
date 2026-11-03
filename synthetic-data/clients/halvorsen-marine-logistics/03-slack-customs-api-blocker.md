---
client: Halvorsen Marine Logistics
type: slack_thread
date: 2026-10-06
title: Customs API sandbox keys delayed
channel: "#halvorsen-tracking-portal"
---

**Sam Okafor** 9:12 AM
heads up, still no sandbox creds from the customs authority. Tom filed the request on Sept 11 so we're at 25 days. I can't test the feed at all without them

**Jordan Reyes** 9:15 AM
ugh. have we escalated?

**Sam Okafor** 9:17 AM
Tom emailed them twice. No reply. He said the contact there is out until the 14th

**Jordan Reyes** 9:20 AM
ok that's a real schedule risk. Priya's final payment is tied to the feed being live. @Sam can you build against a mock in the meantime so we're not fully blocked?

**Sam Okafor** 9:24 AM
yeah I can stub it using their published spec. But the spec is a PDF from 2019 and Tom says the real API has changed since. so there's risk the mock doesn't match

**Mei Lin** 9:31 AM
FWIW I saw something similar with another client, the customs authority has a partner liaison desk, separate from the dev support inbox. They responded in 2 days when we went through them. I can dig up the contact

**Jordan Reyes** 9:33 AM
please do Mei 🙏

**Mei Lin** 9:34 AM
will send it by end of day

**Jordan Reyes** 9:40 AM
Sam: build the mock, flag every assumption in a doc so we know what to verify later. I'll tell Priya on Tuesday's call that go-live is at risk but not changed yet. Don't want to alarm her before we know more

**Sam Okafor** 9:41 AM
👍
