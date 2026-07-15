"""Illustrative *expected output* for the Card-D (Helios Sales Engineer) demo.

Card D has not been run live yet, so the session answers and memory snapshots
below are illustrative — grounded in the behaviour described in
``execution-plan-card-d.md`` (section 1a) and ``stretch-goals.md``. The deck
(``build_deck.py``) reads from this module; rendering is kept separate from
content so this file can later be replaced with parsed real output
(``outputs/session1.txt`` / ``session2.txt`` / memory-snapshot JSON) without
touching the layout code.
"""

# --- Brand / styling -------------------------------------------------------
# Colours are (R, G, B) tuples; build_deck.py converts them to pptx RGBColor.
BRAND = {
    "ink": (23, 23, 33),            # near-black body text
    "muted": (107, 114, 128),       # secondary text
    "accent": (217, 119, 6),        # Helios amber — titles / accents
    "accent_dark": (146, 64, 14),
    "session1": (37, 99, 235),      # blue — "before"
    "session2": (5, 150, 105),      # green — "after / sharper"
    "added": (5, 150, 105),         # green — memory added
    "changed": (217, 119, 6),       # amber — memory changed
    "unchanged": (107, 114, 128),   # grey — memory unchanged
    "surface": (245, 245, 247),     # light panel background
    "white": (255, 255, 255),
    "title_font": "Calibri",
    "body_font": "Calibri",
}

TEST_QUESTION = "Tomorrow's call is the final pitch. What's our strategy?"

SCENARIO = {
    "product": "Helios — a real-time data-streaming platform",
    "prospect": "Northwind Bank (fintech; SOC2 / PCI; EU + US data residency)",
    "persona": (
        "An agent supporting a sales engineer pitching Helios. It tracks the "
        "prospect's environment, every objection + our latest best answer, "
        "competitive intel, and the current pitch strategy — and gets sharper "
        "each call."
    ),
    "round1_docs": [
        ("helios-stack-overview.md",
         "Northwind's environment: self-managed Kafka on-prem, AWS for "
         "analytics, EU+US residency, SOC2/PCI, ~2M events/sec peak, Flink, "
         "6-person platform team."),
        ("objections-log.md",
         "Five prior objections + our current best answer each: latency SLA, "
         "data residency, total cost vs Kafka, migration risk, vendor lock-in."),
        ("pitch-deck.md",
         "Current sequence: problem -> architecture -> managed-vs-self TCO -> "
         "security/residency -> migration path -> pricing -> next steps."),
    ],
    "round2_docs": [
        ("new-objection-2026-05-22.md",
         "Northwind's new CISO mandates active-active multi-region failover "
         "with <5s RPO — the current pitch does not address it."),
        ("competitive-update-2026-05-25.md",
         "StreamCorp cut prices ~20% and shipped a managed connector Helios "
         "lacks — but Helios just shipped native active-active multi-region "
         "(answers the new objection) and residency pinning."),
    ],
}

# --- Session answers (illustrative) ---------------------------------------
SESSION_1_ANSWER = {
    "preface": "Memory store is empty — this is a fresh start. Answering from the round-1 docs.",
    "headline": "Run the standard deck in its current order.",
    "bullets": [
        "Open on the problem, then Helios architecture.",
        "Lead the value case with managed-vs-self-managed TCO vs their Kafka.",
        "Cover security & EU/US data residency (SOC2/PCI).",
        "Walk the migration path to de-risk the switch from self-managed Kafka.",
        "Close on pricing, then next steps.",
        "Have answers ready for the five known objections: latency SLA, "
        "residency, cost, migration risk, lock-in.",
    ],
    "gap": "No failover / multi-region story — it has not come up yet.",
}

SESSION_2_ANSWER = {
    "preface": (
        "Memory recalls the round-1 strategy and the five objections. Two new "
        "round-2 inputs change the plan — reconciling, then resequencing."
    ),
    "headline": "Resequence: open on resilience, reframe on value, pre-empt the new objection.",
    "bullets": [
        "OPEN on active-active multi-region failover with <5s RPO — Helios just "
        "shipped it natively; this directly answers the CISO's new mandate.",
        "Pair it with residency pinning — closes the EU/US residency objection "
        "in the same breath.",
        "Pre-empt the new CISO objection rather than waiting for it to be raised.",
        "Reframe pricing against StreamCorp's ~20% cut: lead with TCO + native "
        "failover (no bolt-on), don't compete on sticker price.",
        "Get ahead of StreamCorp's managed connector gap — name it, give the "
        "roadmap/workaround before they do.",
        "Then run architecture -> TCO -> migration -> next steps as before.",
    ],
    "gap": "Resilience + competitive reframing moved to the front; pricing demoted.",
}

# --- Memory snapshots (path-organized, illustrative) -----------------------
# Each entry: path -> short content summary the agent chose to remember.
MEMORY_SNAPSHOT_AFTER_S1 = {
    "/customers/northwind/environment.md":
        "Self-managed Kafka on-prem; AWS analytics; EU+US residency; SOC2/PCI; "
        "~2M events/sec; Flink; 6-person platform team.",
    "/objections/latency.md": "Latency SLA vs self-managed Kafka — best answer: <X>.",
    "/objections/residency.md": "Data residency / on-prem requirement — best answer: <X>.",
    "/objections/cost.md": "Total cost vs existing Kafka — best answer: <X>.",
    "/objections/migration.md": "Migration risk — best answer: phased cutover.",
    "/objections/lock-in.md": "Vendor lock-in — best answer: open protocols.",
    "/pitch/strategy.md":
        "Sequence: problem -> architecture -> TCO -> security/residency -> "
        "migration -> pricing -> next steps.",
}

MEMORY_SNAPSHOT_AFTER_S2 = {
    "/customers/northwind/environment.md":
        "Self-managed Kafka on-prem; AWS analytics; EU+US residency; SOC2/PCI; "
        "~2M events/sec; Flink; 6-person platform team.",
    "/customers/northwind/contacts.md":
        "New CISO (joined ~May 2026) — mandates active-active multi-region, <5s RPO.",
    "/objections/latency.md": "Latency SLA vs self-managed Kafka — best answer: <X>.",
    "/objections/residency.md":
        "Data residency — UPDATED: now answered by Helios residency pinning.",
    "/objections/cost.md":
        "Total cost — UPDATED: reframe vs StreamCorp -20%; lead on TCO + native failover.",
    "/objections/migration.md": "Migration risk — best answer: phased cutover.",
    "/objections/lock-in.md": "Vendor lock-in — best answer: open protocols.",
    "/objections/failover.md":
        "NEW objection: active-active multi-region failover, <5s RPO "
        "(CISO mandate) — answered by Helios native active-active.",
    "/competitive/streamcorp.md":
        "StreamCorp cut prices ~20%; shipped a managed connector Helios lacks. "
        "Counter: native active-active + residency pinning; reframe on TCO.",
    "/pitch/strategy.md":
        "RESEQUENCED: open on failover + residency -> reframe pricing vs "
        "StreamCorp -> architecture -> TCO -> migration -> next steps.",
}


def _compute_diff(before, after):
    """Return (added, changed, unchanged) path lists between two snapshots."""
    added = [p for p in after if p not in before]
    changed = [p for p in after if p in before and after[p] != before[p]]
    unchanged = [p for p in after if p in before and after[p] == before[p]]
    return added, changed, unchanged


_added, _changed, _unchanged = _compute_diff(
    MEMORY_SNAPSHOT_AFTER_S1, MEMORY_SNAPSHOT_AFTER_S2
)

MEMORY_DIFF = {
    "added": [(p, MEMORY_SNAPSHOT_AFTER_S2[p]) for p in _added],
    "changed": [(p, MEMORY_SNAPSHOT_AFTER_S2[p]) for p in _changed],
    "unchanged": [p for p in _unchanged],
}

# Facts-per-category for the memory-growth bar chart: (category, after_s1, after_s2)
MEMORY_GROWTH = [
    ("Environment", 1, 2),
    ("Objections", 5, 6),
    ("Competitive", 0, 1),
    ("Pitch strategy", 1, 1),
]

# --- Stretch goals S1-S9 ---------------------------------------------------
# (id, title, what, why_it_lands)
STRETCH_TIERS = [
    ("Tier 1 — Make memory deliberate", [
        ("S1", "Explicit memory policy",
         "ALWAYS/NEVER lists in the system prompt (remember environment, "
         "objections+answers, dated competitive intel, pitch decisions; never "
         "verbatim deck text or speculative pricing).",
         "'What does my agent remember?' is the first question every "
         "privacy/security team asks."),
        ("S2", "Memory Curator sub-agent",
         "A second agent does housekeeping on the main store — merges "
         "superseded objection answers, keeps only the latest intel per competitor.",
         "Memory hygiene as a role, not a feature — maps to how human teams "
         "keep institutional knowledge clean."),
    ]),
    ("Tier 2 — Stress-test memory", [
        ("S3", "Adversarial round",
         "Feed undated docs that contradict memory with no reason. Correct "
         "behaviour: flag the conflict and ask which to trust — never silently "
         "overwrite.",
         "Shows memory can be engineered to resist bad inputs — the only way "
         "clients will trust it."),
        ("S4", "'What have you learned?'",
         "A session with no new docs; one prompt asks the agent to summarise "
         "everything it has learned across calls.",
         "The memory store talking back — the most direct, demo-able proof of "
         "what's retained."),
    ]),
    ("Tier 3 — Make memory production-shaped", [
        ("S5", "Per-tenant memory",
         "One memory store per customer_id (Northwind vs Globex). Prove "
         "Northwind facts never leak into Globex answers.",
         "First question every multi-tenant SaaS asks: how do you separate "
         "customers' data?"),
        ("S6", "Scheduled ingestion",
         "A watcher ingests new docs from an inbox folder on a schedule and "
         "moves them to processed — memory accumulates passively.",
         "A fully autonomous, continuously-learning agent."),
        ("S7", "Long-context + compaction",
         "20+ turns in one session; rely on built-in compaction, then commit a "
         "compacted call summary to the memory store.",
         "Distinguishes in-session memory (context window) from across-session "
         "memory (the store) — a gap most teams haven't internalised."),
    ]),
    ("Tier 4 — For the showoffs", [
        ("S8", "Memory diff view",
         "Snapshot the store after each session and diff them — print exactly "
         "what was added / changed / removed between calls.",
         "This is the demo headline: 'here's precisely what the agent learned.'"),
        ("S9", "Topic sub-agents",
         "Group memory into topics, spawn one expert sub-agent per topic seeded "
         "with its slice, route the question to the right expert(s) and synthesise.",
         "An org chart built out of memory — the architecture in every "
         "'AI-native enterprise' pitch six months out."),
    ]),
]

BUSINESS_VALUE = [
    ("\"What does it remember?\"",
     "An explicit ALWAYS/NEVER policy (S1) — answer it precisely, on demand."),
    ("\"How is it kept clean?\"",
     "A curator sub-agent (S2) merges superseded facts and prunes stale intel."),
    ("\"How do you isolate customers?\"",
     "Per-tenant memory stores by customer_id (S5) — provable no-leak."),
    ("\"Can I see what changed?\"",
     "Memory diff between sessions (S8) — an audit trail of what was learned."),
    ("\"Won't it just trust bad data?\"",
     "Adversarial flag-and-ask behaviour (S3) — contradictions surface, not silently overwrite."),
]

HOW_TO_RUN = [
    "pip install -r requirements.txt   (now includes python-pptx)",
    "python create_agent.py            — Managed Agent + path-organized memory store",
    "python run_session_1.py           — round-1 docs; baseline answer -> outputs/session1.txt",
    "python inspect_memory.py          — show what the agent chose to remember",
    "python run_session_2.py           — round-2 docs; sharper answer -> outputs/session2.txt",
    "diff the two outputs              — session 2 anticipates failover, cites StreamCorp, resequences",
    "python build_deck.py              — regenerate this deck from deck_content.py",
]
