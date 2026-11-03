---
client: Halvorsen Marine Logistics
type: meeting_transcript
date: 2026-10-27
title: Weekly Status Call
participants: Priya Raman, Tom Beckett, Jordan Reyes, Sam Okafor, Mei Lin
---

# Weekly Status Call — Oct 27

**[00:00] Jordan:** Let's get started. Sam, where are we technically?

**[00:12] Sam:** Customer tracking page is done and in staging. Ops dashboard is about 80 percent. The customs feed works end to end against the sandbox now, we got the keys on the 16th. The good news is the real API matched the mock about 90 percent. The bad news is the other ten percent was the container status codes, which is the core of the thing. I've had to rework the mapping.

**[01:05] Priya:** How much rework?

**[01:10] Sam:** About a week and a half. And honestly there are still some status codes I can't verify because the sandbox only returns test data for three of the fourteen codes.

**[01:40] Priya:** So what does that do to November 17th?

**[01:48] Jordan:** I want to be honest with you. Realistically November 17th is not safe. And there's something I need to raise. Tom, I understand Halvorsen has an IT change freeze from November 20th?

**[02:10] Tom:** Yes. That's right. Twentieth through thirtieth.

**[02:15] Priya:** I didn't know that. Wait. So if we miss the 19th we're in December?

**[02:22] Tom:** Basically, yes. Sorry, I assumed you knew.

**[02:30] Priya:** I did not. Okay. That changes things. Jordan, what are my options?

**[02:42] Jordan:** Option one: we hold November 17th, ship with the customs feed in a limited mode covering only the three verified status codes, and finish the rest after the freeze. Option two: move go-live to December 8th, everything complete.

**[03:10] Priya:** Option one means the clerks are still re-keying for some containers. Lars will not release the last payment on that.

**[03:25] Jordan:** Correct, the final milestone would shift.

**[03:35] Priya:** I'm going to say December 8th, but I need to explain that to Lars and the CEO and they won't be happy. Can you give me something in writing by Thursday that explains why?

**[03:52] Jordan:** Yes. I'll write it.

**[04:05] Tom:** One more thing. For UAT in November, we'll need a test script my engineer can follow. Dev will be out.

**[04:15] Sam:** I have a draft. I'll send it Wednesday.

**[04:25] Priya:** Also, because of the status code rework, are we over budget?

**[04:32] Jordan:** We'll absorb the rework. No change request. But I'd flag that the Norwegian translation is definitely out of scope.

**[04:45] Priya:** Agreed, phase 2.

**[04:50] Mei:** One thing from me — we should ask the customs authority to enable test data for the other eleven status codes. Otherwise we're guessing at go-live.

**[05:00] Jordan:** Good call. Mei, can you own that?

**[05:04] Mei:** Yes, I'll reach out to the liaison desk tomorrow.

**[05:10] Jordan:** Great. Summary of actions: I write the delay memo by Thursday, Sam sends the UAT script Wednesday, Mei contacts the liaison desk tomorrow, Priya briefs Lars and the CEO. Thanks all.
