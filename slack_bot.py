"""
Slack bot — stretch goal.
Owner: Person 1

Listens (Socket Mode, so no public URL is needed) in every channel the bot is
invited to, and turns messages and .md/.txt file uploads into Items with
source="slack". Each one is categorized, saved to data/items/ (so it appears in
the Streamlit app), and ingested into the memory store.

Run:   python slack_bot.py
Setup: see SLACK_SETUP.md
Env:   SLACK_BOT_TOKEN (xoxb-...), SLACK_APP_TOKEN (xapp-...)  — both in .env
"""

import os
import threading

from agents.categorizer import categorize
from core import log_event, run_memory_session, save_json

MIN_CHARS = 25          # skip "ok", "thanks", emoji-only chatter
MAX_FILE_BYTES = 1_000_000
MAX_INGEST_CHARS = 8000
TEXT_FILE_TYPES = {"md", "txt", "markdown", "text"}

_seen: set[str] = set()  # Slack retries events; don't ingest the same one twice
_seen_lock = threading.Lock()


def already_seen(key: str) -> bool:
    with _seen_lock:
        if key in _seen:
            return True
        _seen.add(key)
        if len(_seen) > 5000:
            _seen.clear()
        return False


def should_ingest(event: dict) -> bool:
    """Decide whether a Slack message event is worth turning into an Item."""
    if event.get("bot_id") or event.get("subtype") not in (None, "file_share", "thread_broadcast"):
        return False
    has_file = any(f.get("filetype") in TEXT_FILE_TYPES for f in event.get("files", []))
    return has_file or len((event.get("text") or "").strip()) >= MIN_CHARS


def ingest_text(text: str, title: str, slack_meta: dict | None = None, to_memory: bool = True) -> dict:
    """
    categorize -> save_json("items") -> run_memory_session.
    Returns {"item": dict, "memory": "ok"|"failed: ..."|"skipped"}.
    Same pipeline as the Inputs tab, with source="slack".
    """
    result = categorize(text)
    item = {
        "title": title,
        "source": "slack",
        "text": text,
        "tags": result["tags"],
        "category": result["category"],
        "summary_short": "",
        "summary_long": "",
        **(slack_meta or {}),
    }
    item_id = save_json("items", item)
    log_event("slack_bot", "save_item", "done", f"{item_id}: {title}")

    memory = "skipped"
    if to_memory:
        message = (
            "A new item arrived from Slack. Record the key facts (people, policies, "
            "deadlines, decisions) in /mnt/memory/ for future sessions, then reply with a "
            "one-line confirmation.\n\n"
            f"Title: {title}\nCategory: {item['category']}\nTags: {', '.join(item['tags'])}\n\n"
            f"Content:\n{text[:MAX_INGEST_CHARS]}"
        )
        try:
            log_event("slack_bot", "ingest_memory", "running", item_id)
            reply = run_memory_session(message, title=f"Slack: {title}"[:100])
            log_event("slack_bot", "ingest_memory", "done", reply[:200])
            memory = "ok"
        except Exception as e:  # saved locally either way
            log_event("slack_bot", "ingest_memory", "error", str(e))
            memory = f"failed: {e}"
    return {"item": item, "memory": memory}


def make_title(text: str, fallback: str = "Slack message") -> str:
    first = text.strip().splitlines()[0].lstrip("# ").strip() if text.strip() else ""
    return (first[:80] or fallback)


def _download_text_file(token: str, file_obj: dict) -> str | None:
    import urllib.request

    url = file_obj.get("url_private_download") or file_obj.get("url_private")
    if not url or file_obj.get("size", 0) > MAX_FILE_BYTES:
        return None
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> None:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not bot_token or not app_token:
        raise SystemExit("Set SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env (see SLACK_SETUP.md).")

    app = App(token=bot_token)

    def process(event: dict, client) -> None:
        channel, ts = event["channel"], event.get("thread_ts") or event["ts"]
        try:
            parts = []
            if (event.get("text") or "").strip():
                parts.append(event["text"].strip())
            for f in event.get("files", []):
                if f.get("filetype") in TEXT_FILE_TYPES:
                    body = _download_text_file(bot_token, f)
                    if body:
                        parts.append(f"[file: {f.get('name')}]\n{body}")
            text = "\n\n".join(parts)
            if not text.strip():
                return
            name = event["files"][0].get("name") if event.get("files") else None
            out = ingest_text(
                text,
                title=make_title(text, fallback=name or "Slack message"),
                slack_meta={"slack_channel": event["channel"], "slack_ts": event["ts"], "slack_user": event.get("user")},
            )
            item = out["item"]
            note = "" if out["memory"] == "ok" else f"\n_(memory ingestion: {out['memory']})_"
            client.chat_postMessage(
                channel=channel,
                thread_ts=ts,
                text=f":brain: Saved *{item['title']}* — {item['category']} · {', '.join(item['tags'])}{note}",
            )
        except Exception as e:
            log_event("slack_bot", "process_message", "error", str(e))
            client.chat_postMessage(channel=channel, thread_ts=ts, text=f":warning: Couldn't ingest that: {e}")

    @app.event("message")
    def on_message(event, client):
        if not should_ingest(event) or already_seen(f"{event['channel']}:{event['ts']}"):
            return
        log_event("slack_bot", "receive", "running", f"{event['channel']}:{event['ts']}")
        # Bolt acks the event right away; do the slow work off the listener thread.
        threading.Thread(target=process, args=(event, client), daemon=True).start()

    @app.event("app_mention")
    def on_mention(event):
        pass  # handled via the message event in channels the bot is in

    log_event("slack_bot", "start", "done", "Socket Mode connected")
    print("Slack bot running. Invite it to a channel and post something.")
    SocketModeHandler(app, app_token).start()


if __name__ == "__main__":
    main()
