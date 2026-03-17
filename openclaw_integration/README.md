# OpenClaw Integration for Swift Event Intelligence

Bridges Swift API events to OpenClaw for delivery to WhatsApp, Telegram, Discord, Slack, and other messaging channels.

## Architecture

```
Swift API (events)  →  OpenClaw webhook  →  Messaging (Telegram/Slack/etc.)
       ↑                      ↑
Pipeline creates     Bridge polls OR Swift pushes
high-severity        via webhook on new event
events
```

## Setup

### 1. Swift API

Add to `.env`:

```env
# Required for /api/v1/alerts endpoint
OPENCLAW_ALERT_KEY=your-secret-api-key

# Optional: push events to OpenClaw when created (severity >= 3)
OPENCLAW_WEBHOOK_URL=http://127.0.0.1:18789/hooks/agent
OPENCLAW_WEBHOOK_TOKEN=your-openclaw-hooks-token
```

### 2. Install OpenClaw

**Windows (PowerShell):**
```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```

**macOS/Linux:**
```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

Then run onboarding:
```bash
openclaw onboard --install-daemon
```

### 3. Configure OpenClaw Webhooks

In `~/.openclaw/openclaw.json` (or `OPENCLAW_CONFIG_PATH`):

```json5
{
  "hooks": {
    "enabled": true,
    "token": "your-hooks-secret",
    "path": "/hooks",
    "defaultSessionKey": "hook:swift"
  }
}
```

Set `OPENCLAW_WEBHOOK_TOKEN` to the same value as `hooks.token`.

### 4. Bridge (Poll Mode)

Run the bridge on a schedule (cron / Task Scheduler) to fetch events and send to OpenClaw:

```bash
# From swift_project directory
set OPENCLAW_ALERT_KEY=your-secret-api-key
set SWIFT_API_URL=http://127.0.0.1:8000
set OPENCLAW_WEBHOOK_URL=http://127.0.0.1:18789/hooks/agent
set OPENCLAW_WEBHOOK_TOKEN=your-hooks-secret

python -m openclaw_integration.cli --min-severity 3 --limit 10
```

**Direct to Telegram (no OpenClaw):**
```bash
set TELEGRAM_BOT_TOKEN=your-bot-token
set TELEGRAM_CHAT_ID=your-chat-id
python -m openclaw_integration.cli --no-openclaw --telegram
```

**Direct to Discord:**
```bash
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
python -m openclaw_integration.cli --no-openclaw --discord
```

### 5. OpenClaw Cron (Optional)

Add a cron job in OpenClaw to run the bridge every 15 minutes:

```bash
openclaw cron add --schedule "*/15 * * * *" --command "cd C:/Users/ADMIN/Downloads/swift_project && venv/Scripts/python.exe -m openclaw_integration.cli"
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENCLAW_ALERT_KEY` | API key for Swift `/api/v1/alerts` |
| `SWIFT_API_URL` | Swift API base URL (default: http://127.0.0.1:8000) |
| `OPENCLAW_WEBHOOK_URL` | OpenClaw hooks URL (default: http://127.0.0.1:18789/hooks/agent) |
| `OPENCLAW_WEBHOOK_TOKEN` | Bearer token for OpenClaw webhook |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (direct send) |
| `TELEGRAM_CHAT_ID` | Telegram chat/channel ID |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL |

## API

### GET /api/v1/alerts

Returns recent high-severity events. Requires `X-API-Key` header.

Query params: `min_severity` (1-5), `limit` (1-50).
