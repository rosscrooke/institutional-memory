"""
Prioritization agent.
Owner: Person 2

Extracts action items and ranks them by priority.
Input: list of items
Output: list of tasks with priority (High|Med|Low)
"""

import json
from core import ask_claude, save_json, load_all, log_event


def prioritize_tasks(items: list[dict]) -> list[dict]:
    """Extract and prioritize tasks from items."""
    if not items:
        return []

    log_event("prioritizer", "prioritize_tasks", "running", f"items={len(items)}")
    try:
        # Prepare item texts for Claude
        item_texts = "\n".join(
            f"- {item.get('title', 'Untitled')} (ID: {item.get('id')}): {item.get('text', '')[:300]}"
            for item in items
        )

        prompt = f"""Extract all action items (tasks, decisions, follow-ups) from the following content.
For each action item, provide: title, priority (High/Med/Low), and the item_id it came from.

Return as JSON array with objects: {{"title": "...", "priority": "High|Med|Low", "item_id": "..."}}

Content:
{item_texts}

Return only valid JSON array."""

        response = ask_claude(prompt)
        # Parse JSON response - extract JSON block if wrapped in markdown
        try:
            # Try direct parse first
            tasks_data = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            if "```json" in response:
                json_block = response.split("```json")[1].split("```")[0].strip()
                tasks_data = json.loads(json_block)
            elif "```" in response:
                json_block = response.split("```")[1].split("```")[0].strip()
                tasks_data = json.loads(json_block)
            else:
                log_event("prioritizer", "prioritize_tasks", "error", f"Failed to parse JSON: {response[:100]}")
                return []

        # Save tasks to data/tasks/, check for duplicates
        existing_tasks = load_all("tasks")
        existing_item_task_pairs = {
            (t.get("item_id"), t.get("title")) for t in existing_tasks
        }

        saved_tasks = []
        for task_data in tasks_data:
            pair = (task_data.get("item_id"), task_data.get("title"))
            if pair not in existing_item_task_pairs:
                task_record = {
                    "item_id": task_data.get("item_id"),
                    "title": task_data.get("title"),
                    "priority": task_data.get("priority", "Med"),
                    "owner": "me",
                    "status": "open",
                    "draft": None,
                }
                task_id = save_json("tasks", task_record)
                saved_tasks.append({**task_record, "id": task_id})

        log_event("prioritizer", "prioritize_tasks", "done", f"saved={len(saved_tasks)}")
        return saved_tasks

    except Exception as e:
        log_event("prioritizer", "prioritize_tasks", "error", str(e))
        raise
