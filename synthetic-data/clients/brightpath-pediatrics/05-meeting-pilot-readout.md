---
client: Brightpath Pediatrics
type: meeting_transcript
date: 2026-11-04
title: Eastside Pilot Readout and Rollout Decision
participants: Dr. Anita Folau, Marcus Webb, Elena Cortez, Gwen Tsai, Jordan Reyes, Dana Whitfield
---

# Pilot Readout — Nov 4

**[00:00] Dana:** Six weeks complete. Headline: Eastside no-shows went from 17 percent to 10.8 percent. That's a 36 percent reduction. The goal was 50 percent over six months, so we're on pace.

**[00:30] Marcus:** That's roughly 15,000 dollars a month recovered across one clinic's volume. Extrapolating to all four, that's real money.

**[00:50] Dr. Folau:** And the vaccine catch-up numbers?

**[00:58] Dana:** Well-child visit completion at Eastside is up 9 points. I can break that out.

**[01:10] Dr. Folau:** Wonderful.

**[01:15] Elena:** I need to raise the double-booking problem. Five incidents total. Every one costs my team time and annoys a family. If we roll out to all four clinics that scales to maybe twenty incidents a month.

**[01:40] Marcus:** That's a fair concern. What is the fix?

**[01:45] Dana:** Either the paid API at 1,800 a month, which allows near real-time sync, or we keep CSV and add a rule that holds cancelled slots for 24 hours before releasing them. The hold rule is free but loses some fill rate.

**[02:10] Marcus:** I'd take the API if it removes the double-booking. 1,800 a month versus 15,000 recovered, it's easy math.

**[02:25] Elena:** But does it let us write back confirmations?

**[02:30] Dana:** I need to verify. The rep said read-only. I'll go back and ask whether a newer tier supports write.

**[02:45] Gwen:** Before we go further. The Spanish template issue. I've re-approved the fixed version, but I want to flag that we sent about 140 messages with the wrong gendered title before it was caught. It's not a privacy violation, but it's a quality-of-care and trust issue. I want a template change process with sign-off in the future.

**[03:10] Jordan:** Agreed. We'll set up a review checklist and you'll have final approval.

**[03:25] Gwen:** Also, the opt-out rate. 3 percent is high. If it climbs, there are regulatory implications under TCPA. I'd like us to drop the 2-hour reminder.

**[03:45] Dr. Folau:** I agree with Gwen. Fewer messages.

**[03:55] Dana:** We can do that. We'll test 48-hour only for the next two weeks.

**[04:10] Marcus:** So decision on rollout. Do we expand to the other three clinics?

**[04:20] Dr. Folau:** I'm in favor, but conditional on the double-booking fix. Let's say we expand to Northgate first, in January, after the API question is settled. Then Harbor and Central in February.

**[04:45] Marcus:** I can live with that. Let's not do it in December, holiday volume is chaos.

**[05:00] Elena:** Thank you. I appreciate that.

**[05:05] Jordan:** Actions: Dana confirms API write support by Nov 11. Jordan sends the template review process doc. We drop the 2-hour reminder starting Monday. Marcus decides on the API budget once Dana reports back. Rollout dates tentatively Northgate in January.
