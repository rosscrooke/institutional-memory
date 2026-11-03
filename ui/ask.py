"""
Ask panel — chat interface with suggested prompts.
Owner: Person 3
"""

import streamlit as st


def render_ask():
    """Render the Ask (chat) panel."""
    st.header("💬 Ask the agent")

    st.subheader("Suggested prompts")
    suggested = [
        "What changed this week?",
        "How do I get prod access?",
        "Who owns payments?",
        "What's the team structure?",
    ]
    for prompt in suggested:
        if st.button(prompt, key=f"prompt_{prompt}"):
            st.info(f"Agent would answer: {prompt} (placeholder)")

    st.divider()
    st.subheader("Chat")
    user_input = st.chat_input("Ask anything about our company...")
    if user_input:
        st.info(f"Agent response to: {user_input} (placeholder)")
