"""Onboarding dashboard.

    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboard import api
from dashboard.core import Mode, briefing_cache_key

st.set_page_config(page_title="Onboarding Memory", page_icon="🧠", layout="wide")

OP_ICON = {"created": "🟢", "modified": "🟡", "deleted": "🔴"}


# --------------------------------------------------------------------------- cached reads


@st.cache_data(ttl=20, show_spinner=False)
def memories(store_id: str):
    return api.list_memories(store_id)


@st.cache_data(show_spinner="Building your briefing…")
def briefing(cache_key: str, role: str, _mems):  # cache_key invalidates on any memory change
    return api.briefing(role, list(_mems))


@st.cache_data(show_spinner=False)
def timeline(store_id: str, memory_id: str, sha: str):  # sha busts cache when memory changes
    return api.timeline(store_id, memory_id)


def refresh():
    memories.clear()


def stream_into_page(**kwargs) -> str:
    text = st.write_stream(api.run_session(**kwargs))
    refresh()
    return text if isinstance(text, str) else "".join(map(str, text))


def render_memory(mem, history_label: str = "Timeline"):
    tab_now, tab_hist = st.tabs(["Current", history_label])
    tab_now.markdown(mem.content)
    with tab_hist:
        render_timeline(GLOBAL, mem)


def chat_context(history: list[dict], turns: int = 6) -> str:
    """Each chat message is a fresh session, so replay recent turns as context."""
    if not history:
        return ""
    lines = [f"{m['role'].upper()}: {m['content']}" for m in history[-turns:]]
    return "Earlier in this conversation:\n" + "\n".join(lines) + "\n\n"


def strip_tool_notes(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("`🧠")).strip()


def render_timeline(store_id: str, mem):
    entries = timeline(store_id, mem.id, mem.sha256)
    for e in entries:
        st.markdown(f"{OP_ICON.get(e.operation, '•')} **{e.when}** — {e.operation} by _{e.author}_")
        if e.diff:
            st.code(e.diff, language="diff")
    if len(entries) == 1:
        st.caption("No changes since this was first learned.")


# --------------------------------------------------------------------------- sidebar


with st.sidebar:
    st.title("🧠 Onboarding Memory")
    mode = st.radio("I am a…", ["New hire", "Experienced colleague"])
    name = (st.text_input("Your name", value=st.session_state.get("name", "")) or "").strip()
    st.session_state["name"] = name
    if st.button("↻ Refresh memory"):
        refresh()
        st.rerun()

if not name:
    st.info("Enter your name in the sidebar to get started.")
    st.stop()

try:
    GLOBAL = api.global_store()
except Exception as e:  # missing key / provisioning failure — show it, don't crash
    st.error(f"Could not connect to Anthropic: {e}")
    st.stop()


# --------------------------------------------------------------------------- experienced colleague


def expert_view():
    st.header(f"Share knowledge, {name}")
    st.caption("Anything you add here becomes **global** team knowledge for every new hire.")

    note = st.text_area(
        "Note", placeholder="e.g. Prod access now requires a Jira ticket in ACCESS, approved by the on-call SRE.",
        height=140,
    )
    files = st.file_uploader("…or upload docs", type=["md", "txt"], accept_multiple_files=True)

    if st.button("Ingest into team memory", type="primary", disabled=not (note.strip() or files)):
        docs = "\n\n".join(f"===== DOCUMENT: {f.name} =====\n{f.read().decode()}" for f in files or [])
        message = (
            f"{name}, an experienced colleague, is sharing team knowledge. Read the global "
            "team-knowledge folder first, then create or UPDATE concept files so that new hires "
            "get the current truth. Where this contradicts existing memory, update the file and "
            "record the effective date and what changed. Finish with a short bullet summary "
            "of which files you created/updated.\n\n"
            + (f"NOTE FROM {name}:\n{note}\n\n" if note.strip() else "")
            + docs
        )
        with st.container(border=True):
            stream_into_page(name=name, mode=Mode.EXPERT, message=message, title=f"Ingest by {name}")
        st.success("Team memory updated.")

    st.divider()
    st.subheader("Current team memory")
    mems = memories(GLOBAL)
    if not mems:
        st.caption("Empty. Paste a note or upload docs above to add the first team knowledge.")
    for m in mems:
        with st.expander(f"{m.path}  ·  updated {m.updated_at}"):
            render_memory(m, "History")


# --------------------------------------------------------------------------- new hire


def new_hire_view():
    st.header(f"Welcome aboard, {name} 👋")
    role = st.selectbox("Your role", api.ROLES, key="role")

    mems = memories(GLOBAL)
    if not mems:
        st.warning("Team memory is empty. Ask an experienced colleague to ingest the onboarding docs.")
        st.stop()
    by_path = {m.path: m for m in mems}

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader(f"What matters for a {role}")
        key = briefing_cache_key(role, {m.path: m.sha256 for m in mems})
        try:
            brief = briefing(key, role, tuple(mems))
        except ValueError as e:
            st.error(f"Couldn't build briefing: {e}")
            brief = None
        for path, why in (brief.relevant if brief else []):
            m = by_path[path]
            with st.container(border=True):
                st.markdown(f"**{Path(path).stem.replace('-', ' ').title()}**  ·  _updated {m.updated_at}_")
                st.caption(why)
                with st.expander("Read & see how this evolved"):
                    render_memory(m)

    with right:
        st.subheader("Ask the onboarding agent")
        if brief and brief.questions:
            st.caption("Suggested questions")
            for i, q in enumerate(brief.questions):
                if st.button(q, key=f"q{i}", use_container_width=True):
                    st.session_state["pending"] = q

        history = st.session_state.setdefault(f"chat:{name}", [])
        for msg in history:
            st.chat_message(msg["role"]).markdown(msg["content"])

        typed = st.chat_input("Ask anything — or tell me how you like answers (e.g. 'bullet points only')")
        question = typed or st.session_state.pop("pending", None)
        if question:
            context = chat_context(history)
            history.append({"role": "user", "content": question})
            st.chat_message("user").markdown(question)
            with st.chat_message("assistant"):
                answer = stream_into_page(
                    name=name, mode=Mode.NEW_HIRE, title=f"{name} ({role})",
                    message=f"I'm {name}, a new {role}.\n\n{context}{question}",
                )
            history.append({"role": "assistant", "content": strip_tool_notes(answer)})

        with st.expander("🔒 My preferences (only visible to you)"):
            prefs = memories(api.registry.user_store(name))
            if not prefs:
                st.caption("None yet. Tell the agent how you like answers and it will remember.")
            for p in prefs:
                st.markdown(f"**{p.path}**")
                st.markdown(p.content)


if mode == "Experienced colleague":
    expert_view()
else:
    new_hire_view()
