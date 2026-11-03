# Slack bot setup (Person 1, stretch goal)

The bot uses **Socket Mode**, so it runs on your laptop with no public URL.

## 1. Create the Slack app
1. https://api.slack.com/apps → **Create New App** → From scratch → pick your workspace.
2. **Socket Mode** → enable → create an **App-Level Token** with scope `connections:write`. Copy it (`xapp-...`).
3. **OAuth & Permissions** → Bot Token Scopes: `channels:history`, `groups:history`, `chat:write`, `files:read`.
4. **Event Subscriptions** → enable → Subscribe to bot events: `message.channels`, `message.groups`, `app_mention`.
5. **Install App** to the workspace. Copy the **Bot User OAuth Token** (`xoxb-...`).

## 2. Add the tokens to `.env`
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

## 3. Run
```
pip install -r requirements.txt
python slack_bot.py
```
Invite the bot to a channel (`/invite @your-bot`) and post a message of 25+ characters,
or upload a `.md` / `.txt` file. The bot replies in a thread with the category and tags.
The item appears in the app's **Inputs → Recent inputs** with source `slack`.

## Behaviour
- Ignores bot messages, edits, and short chatter (under 25 characters).
- Dedupes Slack retries by channel + timestamp.
- Saves the item first, then ingests into memory. If memory fails (for example the agent
  isn't created yet), the item is still saved and the thread reply says so.
- Everything is logged via `log_event("slack_bot", ...)`, so it shows up in the Monitor.

## Limits
- Text files only (`.md`, `.txt`); PDFs in Slack are ignored.
- Only channels the bot is a member of. DMs are not subscribed.
