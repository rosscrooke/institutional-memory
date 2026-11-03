"""
Task agent.
Owner: Person 3

SPEC (build from this; keep the function signature)

Purpose
    When the user clicks "Delegate to agent" on a task, produce a ready-to-send
    DRAFT (email or meeting invite). The agent never sends anything: it drafts,
    a human approves. This is a deliberate safety boundary; keep it.

Input
    task: Task dict (core.py): {id, item_id, title, priority, owner, status,
    draft, created_at}. Look up the source item with
    next(i for i in load_all("items") if i["id"] == task["item_id"]) for
    context (text, tags, category).

Output
    str: the draft, markdown, in this shape so the UI can render it:
        **Type:** Email | Meeting invite
        **To:** names/roles taken from the source item (or "TBD" if unknown)
        **Subject:** ...
        **Body:** ...
        For a meeting invite also: **Suggested time:** ..., **Duration:** ...,
        **Agenda:** bullets.
    Persist it: update_json("tasks", task["id"],
        {"draft": draft, "status": "drafting", "owner": "agent"}).
    The UI sets status to "done" only after the human approves.

Drafting guidance
    - Decide email vs meeting: needs discussion/several people -> meeting;
      single request, approval, or info -> email.
    - Professional, concise, ~120 words max; clear ask and deadline in the first
      two lines. Use only facts from the item (names, dates, policies). Use
      "TBD" instead of inventing a recipient, date or number.
    - Optionally call run_memory_session to look up the right owner/contact in
      memory ("Who owns payments?"). It is slow: do this only if the item
      lacks a contact, and show a spinner.
    - Add a one-line "Why this draft" note before the draft listing the facts
      used, so the human can check them.
    - No links, attachments or fake signatures. Sign as "[Your name]".

Edge cases
    - Task with no item_id or a missing item: draft from the task title alone
      and flag "(no source item found)".
    - Task already has a draft: return it unless the caller wants a regenerate
      (add an optional regenerate: bool = False parameter if you need it).
    - Vague task title: draft a clarifying question instead of guessing.
    - API error: log_event "error", raise a readable message.
    - NEVER call any send-email, calendar or Slack API.

Done when
    - A High task from seeded data produces a draft with a real recipient from
      the team directory (or TBD), a clear ask, and a deadline.
    - The task record shows status "drafting" and the draft text afterwards.
    - log_event("task_agent", ...) lines appear in the Monitor.
"""


def draft_task_action(task: dict) -> str:
    """Draft an email or meeting invite for a task. See module SPEC."""
    raise NotImplementedError("Person 3 to implement")
