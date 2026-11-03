"""
Summarization agent.
Owner: Person 2

Generates quick (3 bullets) and in-depth summaries of content.
Input: list of items
Output: {summary_short, summary_long}
"""

import json
from core import ask_claude, log_event


def summarize_quick(items: list[dict]) -> str:
    """Generate quick 3-bullet summary."""
    if not items:
        return "No items to summarize."

    log_event("summarizer", "summarize_quick", "running", f"items={len(items)}")
    try:
        # Prepare item texts
        item_texts = "\n".join(
            f"- {item.get('title', 'Untitled')}: {item.get('text', '')[:200]}"
            for item in items
        )

        prompt = f"""Summarize the following items in exactly 3 bullet points. Be concise and actionable.

{item_texts}

Return only the 3 bullets, one per line, starting with "- "."""

        result = ask_claude(prompt)
        log_event("summarizer", "summarize_quick", "done")
        return result
    except Exception as e:
        log_event("summarizer", "summarize_quick", "error", str(e))
        raise


def summarize_detailed(items: list[dict]) -> str:
    """Generate in-depth summary."""
    if not items:
        return "No items to summarize."

    log_event("summarizer", "summarize_detailed", "running", f"items={len(items)}")
    try:
        # Prepare full item texts
        item_texts = "\n".join(
            f"**{item.get('title', 'Untitled')}** ({item.get('category', 'uncategorized')})\n{item.get('text', '')}"
            for item in items
        )

        prompt = f"""Provide a comprehensive summary of the following items. Include key points, themes, and connections.

{item_texts}

Return a well-structured summary with sections as needed."""

        result = ask_claude(prompt)
        log_event("summarizer", "summarize_detailed", "done")
        return result
    except Exception as e:
        log_event("summarizer", "summarize_detailed", "error", str(e))
        raise
