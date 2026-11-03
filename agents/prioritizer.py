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
"""


def prioritize_tasks(items: list[dict]) -> list[dict]:
    """Extract and prioritize tasks. See module SPEC."""
    raise NotImplementedError("Person 2 to implement")
