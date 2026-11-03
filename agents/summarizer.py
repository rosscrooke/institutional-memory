"""
Summarization agent.
Owner: Person 2

SPEC (build from this; keep the function signatures)

Purpose
    Give the "President's Brief": a 10-second snapshot and an in-depth briefing
    over the team's items. Memory is the point of the app, so the summary should
    say what CHANGED, not just restate documents.

Input
    items: list of Item dicts (core.py). Typically everything in data/items/,
    possibly filtered to "since yesterday" or one category by the UI. Items span
    several categories and sources (upload, text, slack).

Output
    summarize_quick(items)     -> str  markdown, EXACTLY 3 bullets, each one line
                                       (~20 words max), most important first.
    summarize_detailed(items)  -> str  markdown, grouped under headings by
                                       category (or by theme if one category
                                       dominates), each with short paragraphs
                                       or bullets. Includes a "What changed"
                                       section that calls out contradictions or
                                       updates between older and newer items
                                       (for example round1 vs round2 policy).

Prompt guidance
    - Role: chief of staff briefing an executive. Concrete, no filler, no
      "this document discusses".
    - Include names, numbers, dates and owners from the source. Never invent
      any. If something isn't in the items, don't say it.
    - Cite the source item by title in parentheses, e.g. "(Access Policy)", so
      the user can trace claims.
    - Order by importance/urgency, then recency.
    - When items conflict, prefer the newest created_at and say the old one was
      superseded.

Caching (do this to keep the UI fast)
    - Per-item: if an item has summary_short / summary_long and they were made
      after the item's last change, reuse them. Write new ones back with
      update_json("items", item["id"], {...}).
    - For the multi-item brief: build a cache key from the sorted item ids +
      their created_at values, and store the result in
      data/digest_cache.json via json. If the key matches, return the cache.
    - The UI should offer a "Regenerate" button that bypasses the cache.

Implementation notes
    - Use ask_claude. For many items, summarize each one briefly first
      (map step), then combine (reduce step), so you stay under the context
      limit. Truncate each item to ~4000 chars in the map step.
    - Keep summarize_quick fast: it should use summary_short fields when
      available rather than reading full texts.
    - log_event("summarizer", action, "running"|"done"|"error", detail) around
      every call.

Edge cases
    - No items: return a friendly one-liner ("Nothing to summarize yet. Add
      items on the Inputs tab."), no API call.
    - A single item.
    - Very long items (PDF text): truncate, don't fail.
    - Model returns more or fewer than 3 bullets: trim or re-ask once.
    - API error: log it and raise a readable message for st.error.

Done when
    - Quick view is always exactly 3 bullets with no fabricated facts.
    - Detailed view includes the "What changed" section after seeding round1
      then round2.
    - Calling twice without new items makes no new API calls (cache hit).
"""


def summarize_quick(items: list[dict]) -> str:
    """Generate quick 3-bullet summary. See module SPEC."""
    raise NotImplementedError("Person 2 to implement")


def summarize_detailed(items: list[dict]) -> str:
    """Generate in-depth summary. See module SPEC."""
    raise NotImplementedError("Person 2 to implement")
