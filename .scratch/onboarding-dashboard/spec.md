# Onboarding dashboard — spec

Status: ready-for-agent

- Stack: Streamlit app in new `dashboard/`; existing CLI scripts untouched. API key from env/.env.
- Identity: no login; sidebar mode picker (New hire / Experienced colleague) + name.
- Memory layout: one global store (experts read_write, new hires read_only); one personal store per new hire (read_write), created on first use, mapping in users.json. Enforced via API `access`. New agent v2 whose system prompt explains the two mounted folders and that personal prefs override style.
- Expert view: paste note or upload .md -> Managed Agent session (global read_write) decides what to create/update. Log session_id -> name for attribution. Demo seeded by ingesting round-1 docs through same UI.
- New-hire view: fixed role dropdown; one Messages API call returns JSON {relevant memories + one-line why, 3-5 suggested questions}, cached per role, invalidated when global store changes. Each memory card expands into per-file timeline (versions: operation, date, author via session log, difflib diff vs previous). Chat (suggested question clickable) runs Managed Agent session (global read_only + user read_write), streamed. Personal prefs like "bullet points only" saved to user store. "My preferences" panel lists user store.
- Demo: seed round1 -> new hire sees prod-access card -> expert ingests round2 -> new hire refreshes, card changed, timeline v1->v2 + diff -> new hire sets bullet points -> second new hire unaffected.
- Out of scope: auth, LLM-grouped concept timeline, React.
