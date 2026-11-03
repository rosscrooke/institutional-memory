"""
Institutional Memory App — Streamlit single-page app.
Two tabs: Inputs and Summary outputs.
"""

import streamlit as st

# Import UI components
from ui.inputs import render_inputs
from ui.digest_actions import render_digest, render_actions
from ui.ask import render_ask
from ui.monitor import render_monitor


def main():
    st.set_page_config(
        page_title="Institutional Memory",
        page_icon="📚",
        layout="wide",
    )
    st.title("📚 Institutional Memory")

    tabs = st.tabs(["Inputs", "Summary outputs"])

    with tabs[0]:
        render_inputs()

    with tabs[1]:
        col_left, col_right = st.columns([1.6, 1])
        with col_left:
            render_digest()
            render_actions()
            render_ask()
        with col_right:
            render_monitor()


if __name__ == "__main__":
    main()
