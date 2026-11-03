---
client: Verdant Ridge Outfitters
type: meeting_transcript
date: 2026-07-14
title: Inventory Forecasting Kickoff
participants: Camille Dubois (VP E-commerce), Raj Patel (Head of Merchandising), Ollie Brandt (Warehouse Operations), Jordan Reyes (our account lead), Kenji Watanabe (our data scientist)
---

# Inventory Forecasting Kickoff — Verdant Ridge Outfitters

**[00:00] Jordan:** Camille, do you want to open with the problem?

**[00:08] Camille:** Sure. We sell outdoor gear online and through 22 retail stores. Last winter we stocked out of insulated jackets two weeks before Christmas, and we were overstocked on trekking poles by about 40,000 units. Together that was a six-figure miss. Our leadership wants better forecasting before this holiday season.

**[00:45] Raj:** I want to add that merchandising currently builds the forecast in spreadsheets, using last year's sales plus gut feel. We don't account for weather, promotions, or social media trends.

**[01:10] Kenji:** What data do you have? Sales history, ideally by SKU and store, at least 2 years back?

**[01:20] Raj:** We have three years of sales in Snowflake. SKU level, store level. Promotions are tracked in a separate sheet that's, honestly, not clean.

**[01:40] Kenji:** The promotions data will matter a lot. Can someone clean it up?

**[01:50] Raj:** I can assign someone. Probably takes two weeks.

**[02:00] Ollie:** From the warehouse side, I care about lead times. Our suppliers range from 3 weeks to 14 weeks. A forecast without lead times is not useful to me.

**[02:20] Kenji:** Agreed. We'd produce a forecast plus a recommended reorder date based on lead time.

**[02:35] Ollie:** Supplier lead times are in our ERP. I'd need to export them. But I should warn you, half of them are out of date.

**[02:50] Camille:** Timeline. Holiday is the target, so we need something running by September 30th, in time for the final orders.

**[03:05] Jordan:** September 30 is tight. We'd propose a first version on top 200 SKUs only, covering the highest revenue items, then expand.

**[03:25] Camille:** Top 200 is fine. That's about 60 percent of revenue.

**[03:35] Raj:** I want to be clear that merchandising needs to stay in control. I don't want a black box overriding my team's judgment. 

**[03:50] Kenji:** The model gives a recommendation and a confidence range. Your team can override and we'll track overrides to see who's right.

**[04:10] Raj:** I can accept that.

**[04:20] Camille:** Security — we're a public company, so the data can't leave our Snowflake environment. Can you work inside it?

**[04:35] Kenji:** We can run in your Snowflake with a read-only role. We'd need a service account.

**[04:50] Camille:** I'll get IT to set that up. Name is Gus Harmon on our data platform team.

**[05:05] Jordan:** Actions: Raj cleans promotion data in two weeks. Ollie exports lead times. Camille gets the Snowflake service account. We'll deliver a plan in a week.
