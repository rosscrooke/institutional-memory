"""
Summarization agent.
Owner: Person 2

Generates quick (3 bullets) and in-depth summaries of content.
Input: list of items
Output: {summary_short, summary_long}

Each item is summarized once by ask_claude and cached in the item's
summary_short / summary_long, so later digests cost one small call at most.
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
