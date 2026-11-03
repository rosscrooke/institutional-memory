"""
Prioritization agent.
Owner: Person 2

SPEC (build from this; keep the function signature)

Purpose
    Turn the team's items into a ranked action list: what needs a human decision
    or a deadline met, and what an agent could take on.

Input
    items: list of Item dicts (see core.py): {id, title, source, text, tags,
    category, summary_short, summary_long, created_at}. May be 1 item or the
    whole data/items folder. Items vary a lot: policy docs, meeting notes, Slack
    messages, team directories, handbooks. Many contain NO action items.

Output
    list of Task dicts (core.py): {id, item_id, title, priority, owner, status,
    draft, created_at}, already saved with save_json("tasks", task).
      - title:    imperative, specific, under ~100 chars ("Get a second approver
                  for prod access before 15 May", not "Access")
      - priority: "High" | "Med" | "Low"
      - owner:    "me" by default; "agent" only if the user delegates it later
                  (the Delegate button uses update_json, not this function)
      - status:   "open"
      - item_id:  the item the task came from (required, used for dedupe)

How to decide priority (put this rubric in the prompt)
    High: hard deadline within ~7 days, security/compliance/access changes,
          something blocking other people, explicit "urgent"/"required"/"must".
    Med:  has a soft deadline or affects the team's workflow, no immediate risk.
    Low:  housekeeping, FYI follow-ups, nice-to-have clean-up.
    Never invent deadlines. If the text has no date, do not call it High
    because of "soon".

Approach
    1. Skip items that already have tasks: load_all("tasks") and compare
       item_id. Re-running must NOT create duplicates.
    2. One ask_claude call per item (or batch up to ~5 short items), asking for
       JSON only: [{"title": ..., "priority": ..., "reason": ...}]. Return an
       empty list for an item with no actions. That is a valid answer.
    3. Parse defensively (code fences, prose around the JSON; see
       agents/categorizer.py:_parse_json for a pattern). Clamp unknown priority
       values to "Med". Drop empty titles. De-duplicate near-identical titles.
    4. Truncate item text (~6000 chars) before sending; use summary_short if
       present for long items.
    5. Sort the returned list High, Med, Low, then by created_at.
    6. log_event("prioritizer", action, "running"|"done"|"error", detail) for
       every step. Never swallow errors: log them and continue with the next
       item, so one bad item doesn't kill the run.

Edge cases to handle
    - Empty list in -> empty list out (no API call).
    - Item with empty text.
    - Model returns nothing parseable: log an error, skip that item.
    - Two items describing the same action (a policy and its update): keep one
      task, tied to the newer item.
    - Contradictory info (old vs new policy): prefer the newer item by
      created_at, and mention the supersession in the task title.

Done when
    - Seeded data (synthetic-data/round1 + round2) produces a sensible,
      non-duplicated list with at least one High and one Low.
    - Running twice creates no new files in data/tasks/.
    - Errors show up in the Monitor tab through log_event.

IMPLEMENTATION STATUS (first pass)
    Done: one ask_claude call per item, tasks saved with save_json, items that
    already have tasks are skipped (no duplicates on re-run), priorities clamped
    to High/Med/Low, every step logged with log_event.
    Not yet done from this spec: the full priority rubric and the "never invent
    deadlines" rule in the prompt, replacing an old item's task when a newer item
    supersedes it, dropping near-identical titles, sorting the returned list,
    using summary_short for long items, and continuing to the next item after an
    error (today the first failing item stops the run and the error is shown).
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
