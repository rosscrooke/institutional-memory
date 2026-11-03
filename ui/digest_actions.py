"""
Digest and Actions panels — summaries and prioritized task list.
Owner: Person 2
"""

import streamlit as st

from agents.prioritizer import prioritize_tasks
from agents.summarizer import summarize_detailed, summarize_quick
from core import load_all, update_json
from ui.theme import apply_theme

PRIORITIES = ["High", "Med", "Low"]
BADGE = {"High": "badge-high", "Med": "badge-med", "Low": "badge-low"}


def _error_text(e: Exception) -> str:
    if "ANTHROPIC_API_KEY" in str(e):
        return "No API key found. Add ANTHROPIC_API_KEY to your .env file and try again."
    return f"The agent could not finish this step: {e}"


def render_digest():
    """Render the Daily digest panel."""
    apply_theme()
    st.subheader("Daily digest")

    items = load_all("items")
    if not items:
        st.info("Nothing to summarize yet. Add a document in the Inputs tab, then come back.")
        return

    pending = [i for i in items if not (i.get("summary_short") and i.get("summary_long"))]
    ids = {i["id"] for i in items}

    col_view, col_action = st.columns([3, 1])
    with col_view:
        view = st.radio(
            "View", ["Quick snapshot", "In-depth"], horizontal=True,
            label_visibility="collapsed", key="digest_view",
        )
    with col_action:
        if st.button("Update digest", key="digest_update"):
            with st.spinner("Agent working..."):
                try:
                    st.session_state["digest_quick"] = summarize_quick(items)
                    st.session_state["digest_quick_ids"] = ids
                    pending = []
                except Exception as e:
                    st.error(_error_text(e))

    if view == "Quick snapshot":
        bullets = st.session_state.get("digest_quick")
        if bullets:
            st.markdown(bullets)
            if st.session_state.get("digest_quick_ids") != ids:
                st.caption("New documents have arrived since this was written. Select Update digest.")
            else:
                st.caption(f"Based on {len(items)} documents.")
        else:
            st.caption(f"{len(items)} documents are waiting. Select Update digest to have the agent summarize them.")
    else:
        detail = summarize_detailed(items, generate=False)
        if detail:
            st.markdown(detail)
        if pending:
            st.caption(f"{len(pending)} of {len(items)} documents are not summarized yet. Select Update digest.")


def _task_row(task: dict, titles: dict[str, str]):
    col_title, col_status, col_act = st.columns([5, 2, 2])
    with col_title:
        st.markdown(task.get("title", "Untitled task"))
        st.caption(f"From: {titles.get(task.get('item_id'), 'Unknown document')}")
        if task.get("draft"):
            with st.expander("Agent draft"):
                st.markdown(task["draft"])
    with col_status:
        if task.get("owner") == "agent":
            st.caption(f"With agent ({task.get('status', 'drafting')})")
        else:
            st.caption("Yours")
    with col_act:
        if task.get("owner") != "agent":
            if st.button("Delegate to agent", key=f"delegate_{task['id']}"):
                update_json("tasks", task["id"], {"owner": "agent", "status": "drafting"})
                st.rerun()
        if st.button("Mark done", key=f"done_{task['id']}"):
            update_json("tasks", task["id"], {"status": "done"})
            st.rerun()


def render_actions():
    """Render the Actions (prioritized tasks) panel."""
    apply_theme()
    st.subheader("Actions")

    items = load_all("items")
    if items and st.button("Find tasks in documents", key="actions_find"):
        with st.spinner("Agent working..."):
            try:
                created = prioritize_tasks(items)
                st.success(f"Added {len(created)} tasks." if created else "No new tasks found.")
            except Exception as e:
                st.error(_error_text(e))

    tasks = load_all("tasks")
    if not tasks:
        st.info("No tasks yet. Select Find tasks in documents to have the agent pull them out.")
        return

    titles = {i["id"]: i.get("title", "Untitled") for i in items}
    open_tasks = [t for t in tasks if t.get("status") != "done"]

    for priority in PRIORITIES:
        group = [t for t in open_tasks if t.get("priority") == priority]
        if not group:
            continue
        st.markdown(f'<span class="{BADGE[priority]}">{priority}</span>', unsafe_allow_html=True)
        for task in group:
            _task_row(task, titles)

    finished = [t for t in tasks if t.get("status") == "done"]
    if finished:
        with st.expander(f"Done ({len(finished)})"):
            for task in finished:
                st.markdown(f"~~{task.get('title', 'Untitled task')}~~")
