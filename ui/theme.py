"""
Shared IBM Carbon theme for every Streamlit panel.
See .claude/skills/ibm-streamlit-design/SKILL.md. Change the look here, never in ui/ files.
"""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'IBM Plex Sans', Arial, sans-serif; font-weight: 300; font-size: 14px; color: #161616; }
h1 { color: #0F62FE; font-weight: 700; font-size: 32px; text-align: left; }
h2, h3 { color: #161616; font-weight: 600; text-align: left; }
.subtitle { color: #6F6F6F; font-size: 20px; font-weight: 400; margin-top: -0.5rem; }
.stButton > button { background: #0F62FE; color: #FFFFFF; border: 0; border-radius: 0; font-weight: 600; }
.stButton > button:hover { background: #001D6C; color: #FFFFFF; }
.chip { display: inline-block; background: #E5F6FF; color: #001D6C; padding: 2px 10px; margin: 0 6px 6px 0; font-size: 12px; }
.badge-high { color: #FFFFFF; background: #DA1E28; padding: 2px 8px; font-size: 12px; font-weight: 600; }
.badge-med  { color: #FFFFFF; background: #0F62FE; padding: 2px 8px; font-size: 12px; font-weight: 600; }
.badge-low  { color: #FFFFFF; background: #8D8C8C; padding: 2px 8px; font-size: 12px; font-weight: 600; }
.comments { border-left: 2px solid #0F62FE; padding-left: 16px; }
.comments h4 { font-size: 14px; font-weight: 700; margin: 0 0 8px 0; }
.footer { color: #525252; font-size: 8px; margin-top: 3rem; }
[data-testid="stDataFrame"] thead th { background: #001D6C; color: #FFFFFF; }
</style>
"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title, subtitle=""):
    st.title(title)
    if subtitle:
        st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)


def footer():
    st.markdown('<div class="footer">IBM Consulting | ©2026 IBM Corporation</div>', unsafe_allow_html=True)
