"""
Prioritization agent.
Owner: Person 2

Extracts action items and ranks them by priority.
Input: list of items
Output: list of tasks with priority (High|Med|Low)

Tasks are saved to data/tasks/. An item that already has tasks is skipped,
so running this twice does not create duplicates.
"""

import json

from core import ask_claude, load_all, log_event, save_json

AGENT = "prioritizer"
VALID = {"high": "High", "med": "Med", "medium": "Med", "low": "Low"}


def _parse_list(text: str) -> list[dict]:
    """Pull the first JSON array out of a model reply, tolerating code fences."""
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("The model did not return a JSON list.")
    return json.loads(text[start : end + 1])


def _extract(item: dict) -> list[dict]:
    prompt = (
        "List the action items a team member must do after reading this document. "
        "Reply with a JSON array only, at most 5 entries, each in the form "
        '{"title": "...", "priority": "High"|"Med"|"Low"}.\n'
        "- title: starts with a verb, under 12 words.\n"
        "- High: blocks work, involves access or security, or has a deadline within a week.\n"
        "- Low: nice to have.\n"
        "If there is nothing to do, reply [].\n\n"
        f"Title: {item.get('title', 'Untitled')}\n\n{item.get('text', '')[:6000]}"
    )
    return _parse_list(ask_claude(prompt, system="You turn documents into clear, ranked to-do lists."))


def prioritize_tasks(items: list[dict]) -> list[dict]:
    """Extract and prioritize tasks. Returns only the tasks created by this call."""
    done_items = {t.get("item_id") for t in load_all("tasks")}
    created: list[dict] = []

    for item in sorted(items, key=lambda i: i.get("created_at", "")):
        if item["id"] in done_items:
            continue
        title = item.get("title", "Untitled")
        log_event(AGENT, f"extract tasks: {title}", "running")
        try:
            for entry in _extract(item):
                task = {
                    "item_id": item["id"],
                    "title": str(entry["title"]).strip()[:200],
                    "priority": VALID.get(str(entry.get("priority", "")).strip().lower(), "Med"),
                    "owner": "me",
                    "status": "open",
                    "draft": None,
                }
                save_json("tasks", task)
                created.append(task)
            log_event(AGENT, f"extract tasks: {title}", "done")
        except Exception as e:
            log_event(AGENT, f"extract tasks: {title}", "error", str(e))
            raise
    return created
