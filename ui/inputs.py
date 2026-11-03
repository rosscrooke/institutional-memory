"""
Inputs tab — file upload, text input, AI-suggested tags, categorization.
Owner: Person 1
"""

import io
from pathlib import Path

import streamlit as st

from agents.categorizer import CATEGORIES, categorize
from core import load_all, log_event, run_memory_session, save_json

MAX_INGEST_CHARS = 8000  # cap what we send to the memory session


def _read_upload(uploaded_file) -> str:
    """Extract text from an uploaded .md/.txt/.pdf file."""
    if uploaded_file.name.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    return uploaded_file.getvalue().decode("utf-8", errors="replace")


def _guess_title(uploaded_file, text: str) -> str:
    if uploaded_file:
        return Path(uploaded_file.name).stem
    first_line = text.strip().splitlines()[0] if text.strip() else "Untitled"
    return first_line.lstrip("# ").strip()[:80] or "Untitled"


def _ingest_message(item: dict) -> str:
    return (
        "A new item was added to the team's institutional memory. Record the key facts "
        "(people, policies, deadlines, decisions) in /mnt/memory/ so future sessions can "
        "recall them, then reply with a one-line confirmation.\n\n"
        f"Title: {item['title']}\n"
        f"Category: {item['category']}\n"
        f"Tags: {', '.join(item['tags'])}\n"
        f"Source: {item['source']}\n\n"
        f"Content:\n{item['text'][:MAX_INGEST_CHARS]}"
    )


def _save_item(title: str, source: str, text: str, category: str, tags: list[str]) -> None:
    item = {
        "title": title,
        "source": source,
        "text": text,
        "tags": tags,
        "category": category,
        "summary_short": "",
        "summary_long": "",
    }
    with st.spinner("Saving item..."):
        item_id = save_json("items", item)
        log_event("inputs", "save_item", "done", f"{item_id}: {title}")

    try:
        with st.spinner("Ingesting into memory (the agent session can take a minute)..."):
            log_event("inputs", "ingest_memory", "running", item_id)
            reply = run_memory_session(_ingest_message(item), title=f"Ingest: {title}"[:100])
            log_event("inputs", "ingest_memory", "done", reply[:200])
        st.success(f"Saved “{title}” and added it to memory.")
    except Exception as e:
        log_event("inputs", "ingest_memory", "error", str(e))
        st.warning(f"Saved “{title}” locally, but memory ingestion failed: {e}")


def render_inputs():
    """Render the Inputs tab with file upload and text input."""
    st.header("📥 Inputs")

    st.subheader("Upload or paste content")
    uploaded_file = st.file_uploader("Upload a file (.md, .txt, .pdf)", type=["md", "txt", "pdf"])
    text_input = st.text_area(
        "Or paste text directly:", height=150, placeholder="Enter notes, policies, updates..."
    )

    text, source = "", "text"
    if uploaded_file:
        try:
            text, source = _read_upload(uploaded_file), "upload"
        except Exception as e:
            st.error(f"Could not read {uploaded_file.name}: {e}")
    if text_input.strip():
        text = f"{text}\n\n{text_input}".strip() if text else text_input
    if uploaded_file:
        st.caption(f"📄 {uploaded_file.name} — {len(text):,} characters")

    # Reset suggestions when the input content changes
    if st.session_state.get("inputs_src_text") != text:
        st.session_state["inputs_src_text"] = text
        for k in ("inputs_title", "inputs_category", "inputs_tags", "inputs_tag_options"):
            st.session_state.pop(k, None)

    st.subheader("✨ AI suggested tags")
    if st.button("Suggest category & tags", disabled=not text.strip()):
        try:
            with st.spinner("Categorizing..."):
                result = categorize(text)
            st.session_state["inputs_title"] = _guess_title(uploaded_file, text)
            st.session_state["inputs_category"] = result["category"]
            st.session_state["inputs_tags"] = result["tags"]
            st.session_state["inputs_tag_options"] = list(result["tags"])
        except Exception as e:
            st.error(f"Categorization failed: {e}")

    suggested = "inputs_category" in st.session_state
    if not suggested:
        st.info("Add some content, then click “Suggest category & tags”. You can edit the result before saving.")
    else:
        title = st.text_input("Title", key="inputs_title")
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", CATEGORIES, key="inputs_category")
        with col2:
            tags = st.multiselect(
                "Tags (type to add your own)",
                options=st.session_state["inputs_tag_options"],
                key="inputs_tags",
                accept_new_options=True,
            )

        if st.button("💾 Save to memory", type="primary"):
            _save_item(title.strip() or "Untitled", source, text, category, tags)

    st.divider()
    st.subheader("📋 Recent inputs")
    items = sorted(load_all("items"), key=lambda i: i.get("created_at", ""), reverse=True)[:10]
    if not items:
        st.info("No inputs yet. Upload something to get started!")
    for item in items:
        tag_str = ", ".join(item.get("tags", [])) or "no tags"
        st.markdown(f"**{item.get('title', 'Untitled')}** · {item.get('category', '?')} · {tag_str}")
