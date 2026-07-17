# Synthetic Personas — Clueless Outfit-Picker Agent

Synthetic users for the outfit-picker agent (inspired by Cher's closet software in *Clueless*).
Each file is one person's clothing taste — the input the agent learns from, suggests outfits against,
gets feedback from, and updates its knowledge with across sessions.

## The set

| Persona | One-liner |
| --- | --- |
| [Carla](./carla.md) | 75, retiree — "coastal grandma," linen and natural colors |
| [Jeff](./jeff.md) | 40, mechanic — durable, functional, doesn't care about fashion |
| [Oscar](./oscar.md) | 15, streetwear — bright colors, Le Fleur brand |
| [Priya](./priya.md) | 32, lawyer — "quiet luxury," neutral capsule wardrobe |
| [Dante](./dante.md) | 28, alt/goth — head-to-toe black, DIY, band tees |
| [Meredith](./meredith.md) | 34, new parent — practical, washable, still wants to feel herself |
| [Rosa](./rosa.md) | 48, plus-size — bold prints, saturated color, maximalist |
| [Kenji](./kenji.md) | 22, techwear/gorpcore — function-forward, muted layers |

The set spans age (15–75), fashion investment (Jeff's indifference → Rosa's joy),
palette (all-black → maximalist color), and constraint type (durability, budget, comfort,
nursing/practicality, plus-size fit, weatherproofing). Gender is stated explicitly on each
profile: Carla, Priya, Meredith, and Rosa are women (she/her); Oscar and Dante are men
(he/him); Jeff and Kenji are nonbinary (they/them).

## File format

Every persona has the same sections, each mapping to a stage of the agent loop:

- **Style identity / Likes / Dislikes** — what the agent *asks about and saves as knowledge*.
- **Lifestyle / occasions / Constraints** — what it needs to *suggest appropriate outfits*
  (budget, climate, comfort, dress codes).
- **Voice** — how the person talks, so simulated conversations sound realistic.
- **Sample outfit reactions** — ✅/⚠️/❌ examples of the *feedback* the user gives, so you can
  script or seed the feedback stage.
- **Taste shift** — a change or new context introduced *later*, for a second session to reconcile.

## The "taste shift" convention (the memory demo)

This repo's core demo is an agent that gets sharper across sessions by *updating* memory when new
info contradicts old (round1 → round2). Each persona's **Taste shift** is that second-session
signal. The bar isn't "did the agent change its answer" — it's "did the agent update the *nuance*
without clobbering the rest of the profile":

- Carla wants one warm accent color → *don't* wipe her "no loud colors" rule.
- Jeff needs one dress-up outfit → *don't* conclude he's "into fashion" now.
- Oscar matures his palette → he still wants a pop, now grounded in neutrals.
- Priya adds a signature burgundy → the capsule expands by one accent, philosophy intact.

A good agent reconciles; a naive one overwrites.
