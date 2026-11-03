"""
Agent monitoring panel — status, memory changes, feedback.
Owner: Person 4
"""

import streamlit as st


def render_monitor():
    """Render the Agent monitoring panel."""
    st.header("🔍 Agent monitoring")

    st.subheader("Agent status")
    st.markdown("""
    - **Summarizer**: idle (last run 2m ago)
    - **Categorizer**: idle
    - **Chat**: idle
    - **Task agent**: idle
    - **Feedback**: idle
    """)

    st.divider()
    st.subheader("Memory changes")
    st.caption("Latest snapshot from 5 minutes ago")
    st.info("No memory updates yet")

    st.divider()
    st.subheader("Feedback")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Helpful"):
            st.success("Thanks for the feedback!")
    with col2:
        if st.button("👎 Not helpful"):
            st.warning("We'll learn from this")

    comment = st.text_area("Add a comment (optional)", height=80)
    if st.button("Submit feedback"):
        st.success("Feedback saved")
