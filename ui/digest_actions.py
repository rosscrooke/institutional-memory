"""
Digest and Actions panels — summaries and prioritized task list.
Owner: Person 2
"""

import streamlit as st


def render_digest():
    """Render the Daily digest panel."""
    st.header("📊 Daily digest")

    col1, col2 = st.columns(2)
    with col1:
        view = st.radio("View:", ["Quick snapshot", "In-depth"], horizontal=True)

    if view == "Quick snapshot":
        st.markdown("""
        **Today's highlights:**
        - New policy on prod access — requires 2 approvals
        - Team re-org: payments team merged with platform
        - 3 new onboarding docs added
        """)
    else:
        st.markdown("""
        **In-depth summary:**

        The institutional memory has learned:

        1. **Access & Security** — Production access now requires approval from two managers.
           Previous policy allowed single approval.

        2. **Organizational Changes** — Payments team merged with Platform Engineering.
           Contact sarah@company.com for payments questions now.

        3. **Onboarding** — New engineers should complete these steps before day 1:
           - GitHub access request
           - VPN setup
           - Slack workspace join
        """)


def render_actions():
    """Render the Actions (prioritized tasks) panel."""
    st.header("✅ Actions")

    st.subheader("Prioritized task list")

    st.markdown("**High Priority**")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("Request prod access approval from finance lead")
    with col2:
        if st.button("🤖 Delegate", key="task1"):
            st.info("Delegated to agent")

    st.markdown("**Medium Priority**")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("Update team calendar with new meeting schedule")
    with col2:
        if st.button("🤖 Delegate", key="task2"):
            st.info("Delegated to agent")

    st.markdown("**Low Priority**")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("Review and file old policy documents")
    with col2:
        if st.button("🤖 Delegate", key="task3"):
            st.info("Delegated to agent")
