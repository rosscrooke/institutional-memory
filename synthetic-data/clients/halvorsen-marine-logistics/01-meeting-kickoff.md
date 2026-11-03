---
client: Halvorsen Marine Logistics
type: meeting_transcript
date: 2026-09-08
title: Tracking Portal Kickoff Call
participants: Priya Raman (Halvorsen COO), Tom Beckett (Halvorsen IT Director), Jordan Reyes (our account lead), Sam Okafor (our engineer)
---

# Tracking Portal Kickoff Call — Halvorsen Marine Logistics

**[00:00] Jordan:** Thanks everyone for making time. Quick goal for today: agree on scope, the timeline, and who owns what for the new container tracking portal.

**[00:42] Priya:** From my side, the pain is simple. Customers call us forty times a day asking where their container is. Our current system is a 2011 Access database with a web front end bolted on. I want customers to self-serve.

**[01:30] Tom:** And I'll add, the old system can't talk to the customs authority's API. Everything is re-keyed by hand by two clerks. That's the real cost.

**[02:10] Jordan:** Understood. So the three pillars are: one, a customer-facing tracking page; two, an internal dashboard for the ops team; three, an automated feed from the customs API so the clerks stop re-keying.

**[03:05] Priya:** Yes. And I need to be clear that the customs feed is the part I'm paying for. The pretty page is nice but the feed saves headcount.

**[03:40] Sam:** For the feed we'll need sandbox credentials from the customs authority. Tom, who requests those?

**[03:55] Tom:** I can. It usually takes about a week. I'll file it this Friday.

**[04:20] Jordan:** Great. On timeline, we're proposing go-live on November 17th. That gives us about ten weeks including testing.

**[04:48] Priya:** November 17th works. I want it live before the peak season crunch, that's non-negotiable for me.

**[05:15] Tom:** One concern, my team is only two people. We can't do a big data migration and also do user acceptance testing in the same month.

**[05:50] Sam:** Then let's split it. We'll handle the migration of historical shipment records ourselves. Tom, your team just needs to give us an export of the old database. Can you get us that by September 25th?

**[06:15] Tom:** Should be fine. I'll have Dev, one of my guys, run it.

**[06:40] Priya:** Budget. We talked about 180 thousand. I still need to get final sign-off from our CFO, Lars. I'll have an answer next week.

**[07:05] Jordan:** Perfect. We'll send a written scope summary tomorrow so you can send it to Lars.

**[07:30] Priya:** Also — random question — can the portal be in Norwegian too? A few of our biggest customers are out of Bergen.

**[07:50] Jordan:** We hadn't scoped that. Let me think about the effort and come back to you. Probably a small add.

**[08:15] Priya:** Okay, no rush, just flagging it.

**[08:30] Jordan:** Last thing, weekly status calls Tuesdays at 10. Anything else?

**[08:42] Tom:** No, all good.

**[08:44] Jordan:** Thanks all. Talk next week.
