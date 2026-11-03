"""
Categorization agent.
Owner: Person 1

Categorizes incoming content and suggests tags.
Input: raw text from file or paste
Output: {category, tags: [...]}
"""

import json
import re

from core import ask_claude, log_event

CATEGORIES = ["Development", "Operations", "HR", "Security", "Other"]

SYSTEM = (
    "You classify internal company documents for an institutional-memory system. "
    "Reply with a single JSON object and nothing else (no prose, no code fences)."
)

PROMPT = """Classify the document below.

Return JSON exactly like: {{"category": "<one of {cats}>", "tags": ["tag1", "tag2"]}}

Rules:
- category must be exactly one of: {cats}
- 3 to 6 tags, lowercase, short (1-2 words), most specific first
- Tags should capture topics, people/teams, deadlines, or policies worth recalling later

Document:
\"\"\"
{text}
\"\"\"
"""

MAX_CHARS = 6000  # enough to classify; keeps the call fast


def _parse_json(raw: str) -> dict:
    """Parse model output as JSON, tolerating code fences or surrounding prose."""
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"Categorizer returned non-JSON output: {raw[:200]}")
        return json.loads(match.group(0))


def categorize(text: str) -> dict:
    """Categorize text and suggest tags. Returns {"category": str, "tags": [str]}."""
    if not text.strip():
        raise ValueError("Nothing to categorize: text is empty.")

    log_event("categorizer", "categorize", "running", f"{len(text)} chars")
    try:
        raw = ask_claude(
            PROMPT.format(cats=", ".join(CATEGORIES), text=text[:MAX_CHARS]),
            system=SYSTEM,
        )
        data = _parse_json(raw)
    except Exception as e:
        log_event("categorizer", "categorize", "error", str(e))
        raise

    category = data.get("category")
    if category not in CATEGORIES:
        category = "Other"
    tags: list[str] = []
    for t in data.get("tags", []):
        t = str(t).strip().lower()
        if t and t not in tags:
            tags.append(t)

    log_event("categorizer", "categorize", "done", f"{category}: {', '.join(tags)}")
    return {"category": category, "tags": tags}
