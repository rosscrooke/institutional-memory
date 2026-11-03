"""
Inputs tab — file upload, text input, AI-suggested tags, categorization.
Owner: Person 1
"""

import streamlit as st


def render_inputs():
    """Render the Inputs tab with file upload and text input."""
    st.header("📥 Inputs")

    st.subheader("Upload or paste content")
    uploaded_file = st.file_uploader("Upload a file (.md, .txt, .pdf)", type=["md", "txt", "pdf"])
    if uploaded_file:
        st.caption(f"📄 {uploaded_file.name}")

    text_input = st.text_area("Or paste text directly:", height=150, placeholder="Enter notes, policies, updates...")

    st.subheader("✨ AI suggested tags")
    st.info("Tags will be suggested here after upload/paste")

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Category", ["Development", "Operations", "HR", "Security", "Other"])
    with col2:
        tags = st.multiselect("Tags", ["policy", "urgent", "deadline", "people", "process"])

    if st.button("💾 Save to memory"):
        st.success("Saved to memory (placeholder)")

    st.divider()
    st.subheader("📋 Recent inputs")
    st.info("No inputs yet. Upload something to get started!")
