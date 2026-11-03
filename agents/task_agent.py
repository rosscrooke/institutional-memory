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

from core import ask_claude, update_json, log_event


def draft_task_action(task: dict) -> str:
    """Draft an email or meeting invite for a task. See module SPEC."""
    if not task or not task.get("id"):
        raise ValueError("Task must have an id")

    log_event("task_agent", "draft_action", "running", f"task_id={task.get('id')}")
    try:
        task_id = task.get("id")
        task_title = task.get("title", "Untitled")

        # Load source item for context
        from core import load_all
        source_item = None
        if task.get("item_id"):
            items = load_all("items")
            source_item = next((i for i in items if i["id"] == task["item_id"]), None)

        # Infer email vs meeting: needs discussion/several people -> meeting; single request/approval/info -> email
        is_meeting = any(
            keyword in task_title.lower()
            for keyword in ["meeting", "schedule", "discuss", "sync", "standup", "call", "review", "checkpoint"]
        )

        # Extract context from source item
        source_text = source_item.get("text", "") if source_item else ""
        source_category = source_item.get("category", "TBD") if source_item else "TBD"

        if is_meeting:
            prompt = f"""Draft a concise calendar meeting invite. Keep it ~120 words max.

Task: {task_title}
Source: {source_category}
Context: {source_text[:300]}

Draft as markdown:
**Type:** Meeting invite
**To:** [roles needed, or TBD]
**Subject:** [subject line with clear ask]
**Suggested time:** [TBD if unknown, or infer from context]
**Duration:** 30 min or 1 hour
**Agenda:**
- bullet 1
- bullet 2

At the top, add one line: "Why this draft: [fact used]" so humans can check."""

        else:
            prompt = f"""Draft a professional email. Keep it ~120 words max, clear ask in first two lines.

Task: {task_title}
Source: {source_category}
Context: {source_text[:300]}

Draft as markdown:
**Type:** Email
**To:** [recipient role, or TBD if unknown]
**Subject:** [subject line with clear ask and deadline if applicable]
**Body:**
[concise, fact-based, sign as "[Your name]"]

At the top, add one line: "Why this draft: [fact used]" so humans can check."""

        draft = ask_claude(prompt)

        # Save draft to task record, mark as drafting (awaiting human review/approval)
        update_json("tasks", task_id, {"draft": draft, "status": "drafting", "owner": "agent"})

        log_event("task_agent", "draft_action", "done", f"draft_len={len(draft)}")
        return draft

    except Exception as e:
        log_event("task_agent", "draft_action", "error", str(e))
        raise
