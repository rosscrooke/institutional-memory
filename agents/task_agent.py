"""
Task agent.
Owner: Person 3

Drafts emails or meeting invites for delegated tasks.
Does NOT send — agent drafts, human approves.
"""

from core import ask_claude, update_json, log_event


def draft_task_action(task: dict) -> str:
    """Draft an email or meeting invite for a delegated task.

    Infers whether the task requires an email or meeting based on title keywords.
    Uses ask_claude to generate professional drafts. Saves draft to task record
    with status 'drafting' for human review. Does NOT send emails or create
    calendar events.

    Args:
        task: Task dict with keys: id, title, priority, owner, status

    Returns:
        Draft text (email or meeting invite)

    Raises:
        ValueError: If task has no id
        Exception: If draft generation fails
    """
    if not task or not task.get("id"):
        raise ValueError("Task must have an id")

    log_event("task_agent", "draft_action", "running", f"task_id={task.get('id')}")
    try:
        task_title = task.get("title", "Untitled task")
        task_id = task.get("id")

        # Infer whether task is for a meeting or email based on title keywords
        is_meeting = any(
            keyword in task_title.lower()
            for keyword in ["meeting", "schedule", "discuss", "sync", "standup", "call", "review", "checkpoint"]
        )

        if is_meeting:
            prompt = f"""Draft a concise calendar meeting invite for the following task:

Task: {task_title}

Include:
- Subject line
- Suggested attendees (generic roles based on context)
- Duration (30 min or 1 hour)
- Brief agenda/purpose

Format as:
MEETING INVITE
Subject: [...]
Attendees: [...]
Duration: [...]
Agenda:
[...]"""
        else:
            prompt = f"""Draft a professional email for the following task:

Task: {task_title}

Include:
- Subject line
- Concise body (2-3 paragraphs)
- Clear call to action or next steps

Format as:
EMAIL DRAFT
To: [recipient role]
Subject: [...]
Body:
[...]"""

        draft = ask_claude(prompt)

        # Save draft to task record and mark as awaiting human review/approval
        update_json("tasks", task_id, {"draft": draft, "status": "drafting"})

        log_event("task_agent", "draft_action", "done", f"draft_len={len(draft)}")
        return draft

    except Exception as e:
        log_event("task_agent", "draft_action", "error", str(e))
        raise
