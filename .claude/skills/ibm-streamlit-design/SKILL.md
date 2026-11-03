---
name: ibm-streamlit-design
description: IBM Carbon look for the Daily Digest Streamlit app. Use whenever you build or change any Streamlit UI in this repo (app.py, ui/), including layout, colors, fonts, buttons, tables, tag chips, priority badges, charts, or page headers. Keeps every tab and panel looking like one product.
---

# IBM Streamlit Design

Adapted from the IBM Consulting deck standard (`ibm-deck-design`) for a web app.
The three things that matter most, in order: **color, type size, alignment.**

## One-time setup (whoever touches the UI first)

`.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#0F62FE"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F4F4F4"
textColor = "#161616"
font = "sans serif"
```

Put the CSS below in one shared place (e.g. `ui/theme.py` with `apply_theme()`), call it first in `app.py` and every `ui/` render function, and **never copy-paste it into a `ui/` file or hard-code colors there**.

```python
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
```

## Palette (IBM Carbon, use only these)

| Role | Hex |
|---|---|
| Titles, links, primary buttons, key data | `#0F62FE` |
| Table headers, dark bars, button hover | `#001D6C` |
| Alerts, negatives, High priority | `#DA1E28` |
| Body text | `#161616` |
| Subtitles, muted labels | `#6F6F6F` |
| Footer text | `#525252` |
| Borders, rules | `#D9D9D9` / `#E0E0E0` |
| Light panels, zebra rows | `#F4F4F4` |
| Tag chips, light-blue panels | `#E5F6FF` |
| Total / highlighted table row | `#D6EFFF` |
| Low priority, secondary gray | `#8D8C8C` |
| Chart series, in order | `#0F62FE`, `#001D6C`, `#A56EFE`, `#33B1FF`, `#009D99` |

## Type ladder

Page title 32px bold blue → subtitle 20px gray → section header 14px bold → body 14px → small labels 10–12px → footer 8px gray.
Keep the contrast between steps; don't invent in-between sizes.

## Alignment

- **Left-align everything**: titles, subtitles, body, captions. Only badges and table header text may be centered.
- Tables: row labels left, numbers right.
- Repeated rows (task lists, memory entries) use even spacing.
- Don't center body content or use `st.markdown` with `<center>`.

## Component recipes

- **Page header**: `apply_theme()` then `page_header("Daily Digest", "Today's priorities")` first in `app.py`; each `ui/` render function starts with `st.subheader`. Footer last.
- **Quick vs In-depth view**: use `st.tabs(["Quick", "In-depth"])` or `st.radio(horizontal=True)`; the Quick view shows only `summary_short`.
- **Comments panel**: main content in the left column, a `.comments` div in the right column (`st.columns([7, 3])`) with a bold "Comments" header. Use it for agent notes and feedback.
- **Tag chips**: `<span class="chip">tag</span>`. Tags are editable, so pair them with `st.multiselect` or `st.text_input` for edits.
- **Priority**: render with `.badge-high`, `.badge-med`, `.badge-low`. Never use green/yellow traffic-light colors.
- **Tables**: `st.dataframe` / `st.table` with the navy header from the CSS; highlight the total or "today" row with `#D6EFFF`; negatives in red `#DA1E28`.
- **Charts**: series colors from the palette in order; minimal gridlines; small gray axis labels. Pass colors explicitly (e.g. `color=["#0F62FE", "#001D6C"]`).
- **Slow agent calls**: wrap in `st.spinner("Agent working...")`; show errors with `st.error` (the red is already on-palette).
- **Not for the web app**: the 16x9 canvas, IBM logo, DRAFT tag, and slide page numbers from the deck skill.

## QA checklist (run before you open a PR)

- [ ] `apply_theme()` runs once at the top of `app.py`; no hard-coded hex colors or `<style>` blocks in `ui/` files.
- [ ] Page title (the one `st.title` in `app.py`) is blue 32px, subtitle gray, nothing centered.
- [ ] Only palette colors; priorities use the badges; negatives and alerts in red.
- [ ] Tables have navy headers, numbers right-aligned, total row highlighted.
- [ ] Charts use the series order above.
- [ ] Footer present: `IBM Consulting | ©2026 IBM Corporation`.
- [ ] No leftover "TODO" or placeholder text on a finished page.

Fonts load from Google at runtime, so an offline laptop falls back to Arial; that is fine for the demo.
