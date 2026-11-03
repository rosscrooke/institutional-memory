---
client: Verdant Ridge Outfitters
type: slack_thread
date: 2026-09-17
title: Backtest results and a weird SKU
channel: "#verdant-forecasting"
---

**Kenji Watanabe** 11:02 AM
backtest on the top 200 is done. MAPE of 18% vs Raj's team's spreadsheet at 31% on the same period. So we're meaningfully better

**Jordan Reyes** 11:04 AM
nice!! that's the headline for Friday's call. Any caveats?

**Kenji Watanabe** 11:07 AM
yes a few. (1) backtest period was Jan-Jun, no holiday season in it. Haven't proven it on peak (2) 14 SKUs are really bad, error over 60%. Almost all are new products with <12 months of history (3) promotions data is still messy so I'm using a rough proxy

**Jordan Reyes** 11:09 AM
how bad is the promo data? Raj said two weeks and that was 9 weeks ago

**Kenji Watanabe** 11:10 AM
about 35% of promo rows have no end date. I've been assuming 7 days. Could be a source of error

**Jordan Reyes** 11:12 AM
ok I'll nudge Raj. what else?

**Kenji Watanabe** 11:15 AM
one weird one. SKU 40871, a down vest, the model says to order 12,000 units but last year's total was 2,200. I looked into it. there's one day in April where it sold 3,100 units, probably a flash sale or a pricing error. The model is treating it as real demand

**Ollie Brandt** 11:20 AM
oh that's the pricing error! It was listed at $9 instead of $90 for about 4 hours. We honored the orders and ate the loss. please exclude it

**Kenji Watanabe** 11:21 AM
perfect, thanks Ollie. I'll add an outlier rule and also a manual exclusion list

**Ollie Brandt** 11:22 AM
and FYI, the lead time export you got from me is stale for maybe 40 suppliers. I'm updating it. Will send by Monday

**Kenji Watanabe** 11:23 AM
👍 that actually matters a lot for reorder dates
