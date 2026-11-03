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

IMPLEMENTATION STATUS (first pass)
    Done: each item is summarized once and cached in summary_short /
    summary_long; the quick view is 3 bullets that flag newer-vs-older changes;
    the detailed view groups the cached long summaries by category (no API call).
    Not yet done from this spec: the "What changed" section, source citations
    in parentheses, the digest cache file and Regenerate button, trimming or
    re-asking when the model returns other than 3 bullets, and re-summarizing an
    item that changed after its summary was written.
"""

import json

from core import ask_claude, log_event, update_json

AGENT = "summarizer"


def _oldest_first(items: list[dict]) -> list[dict]:
    """Order by created_at so newer documents come after the ones they may replace."""
    return sorted(items, key=lambda i: i.get("created_at", ""))


def _parse_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply, tolerating code fences."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The model did not return JSON.")
    return json.loads(text[start : end + 1])


def _summarize_item(item: dict) -> dict:
    prompt = (
        "Summarize this document for a team knowledge base. Reply with JSON only, "
        'in the form {"summary_short": "...", "summary_long": "..."}.\n'
        "- summary_short: one sentence, at most 25 words.\n"
        "- summary_long: one paragraph of 3 to 5 sentences covering the key rules, "
        "names, dates and numbers.\n\n"
        f"Title: {item.get('title', 'Untitled')}\n\n{item.get('text', '')[:6000]}"
    )
    data = _parse_json(ask_claude(prompt, system="You write precise, factual summaries."))
    return {
        "summary_short": str(data["summary_short"]).strip(),
        "summary_long": str(data["summary_long"]).strip(),
    }


def summarize_items(items: list[dict]) -> list[dict]:
    """Fill in summary_short / summary_long for items that lack them. Updates items in place."""
    for item in items:
        if item.get("summary_short") and item.get("summary_long"):
            continue
        title = item.get("title", "Untitled")
        log_event(AGENT, f"summarize: {title}", "running")
        try:
            changes = _summarize_item(item)
            update_json("items", item["id"], changes)
            item.update(changes)
            log_event(AGENT, f"summarize: {title}", "done")
        except Exception as e:
            log_event(AGENT, f"summarize: {title}", "error", str(e))
            raise
    return items


def summarize_quick(items: list[dict]) -> str:
    """Generate quick 3-bullet summary."""
    if not items:
        return ""
    items = _oldest_first(summarize_items(items))
    lines = "\n".join(
        f"- {i.get('title', 'Untitled')} (added {i.get('created_at', '')[:10]}): {i['summary_short']}"
        for i in items
    )
    prompt = (
        "Below are one-line summaries of documents in a team's knowledge base, oldest first.\n"
        "Write exactly 3 markdown bullets covering the most important things to know today. "
        "If a newer document changes or contradicts an older one, say what changed, "
        "in the form old -> new. Each bullet is at most 30 words. Output only the bullets.\n\n"
        f"{lines}"
    )
    log_event(AGENT, "quick digest", "running")
    try:
        result = ask_claude(prompt, system="You write a short daily digest for a busy team.").strip()
        log_event(AGENT, "quick digest", "done")
        return result
    except Exception as e:
        log_event(AGENT, "quick digest", "error", str(e))
        raise


def summarize_detailed(items: list[dict], generate: bool = True) -> str:
    """
    Generate in-depth summary: each document's long summary, grouped by category.
    With generate=False, only uses summaries that are already cached (no API calls).
    """
    if generate:
        items = summarize_items(items)
    ready = [i for i in _oldest_first(items) if i.get("summary_long")]

    groups: dict[str, list[dict]] = {}
    for item in ready:
        groups.setdefault(item.get("category") or "Uncategorized", []).append(item)

    blocks = []
    for category, members in groups.items():
        entries = "\n\n".join(f"**{m.get('title', 'Untitled')}**  \n{m['summary_long']}" for m in members)
        blocks.append(f"**{category.upper()}**\n\n{entries}")
    return "\n\n---\n\n".join(blocks)
