"""Bridge: fetch Swift events and send to OpenClaw webhook or messaging channels."""

import os
import json
import httpx
from typing import Optional

SWIFT_API_URL = os.environ.get("SWIFT_API_URL", "http://127.0.0.1:8000")
SWIFT_ALERT_KEY = os.environ.get("OPENCLAW_ALERT_KEY", "")
OPENCLAW_WEBHOOK_URL = os.environ.get("OPENCLAW_WEBHOOK_URL", "http://127.0.0.1:18789/hooks/agent")
OPENCLAW_WEBHOOK_TOKEN = os.environ.get("OPENCLAW_WEBHOOK_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")


def fetch_swift_alerts(min_severity: int = 3, limit: int = 10) -> list[dict]:
    """Fetch recent high-severity events from Swift API."""
    if not SWIFT_ALERT_KEY:
        return []
    url = f"{SWIFT_API_URL.rstrip('/')}/api/v1/alerts"
    with httpx.Client(timeout=15.0) as client:
        r = client.get(
            url,
            headers={"X-API-Key": SWIFT_ALERT_KEY},
            params={"min_severity": min_severity, "limit": limit},
        )
        r.raise_for_status()
        data = r.json()
        return data.get("events", [])


def format_event_message(event: dict) -> str:
    """Format a single event for messaging."""
    title = event.get("title", "Untitled")
    etype = event.get("event_type", "unknown")
    severity = event.get("severity", 0)
    location = event.get("location", "")
    desc = (event.get("description") or "")[:200]
    if desc and len((event.get("description") or "")) > 200:
        desc += "..."
    parts = [f"🚨 **{title}**", f"Type: {etype} | Severity: {severity}"]
    if location:
        parts.append(f"Location: {location}")
    if desc:
        parts.append(desc)
    return "\n".join(parts)


def send_to_openclaw(events: list[dict], message: Optional[str] = None) -> bool:
    """POST events to OpenClaw webhook. Agent will process and optionally deliver to channels."""
    if not OPENCLAW_WEBHOOK_URL or not OPENCLAW_WEBHOOK_TOKEN:
        return False
    text = message or "\n\n".join(format_event_message(e) for e in events)
    if not text.strip():
        return False
    payload = {
        "message": f"[Swift Events]\n\n{text}",
        "name": "Swift",
        "wakeMode": "now",
        "deliver": True,
    }
    headers = {
        "Authorization": f"Bearer {OPENCLAW_WEBHOOK_TOKEN}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(OPENCLAW_WEBHOOK_URL, json=payload, headers=headers)
        return r.status_code == 200


def send_to_telegram(text: str) -> bool:
    """Send message to Telegram via Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
        )
        return r.status_code == 200


def send_to_discord(text: str) -> bool:
    """Send message to Discord webhook."""
    if not DISCORD_WEBHOOK_URL:
        return False
    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            DISCORD_WEBHOOK_URL,
            json={"content": text[:2000]},
        )
        return r.status_code in (200, 204)


def run_bridge(
    min_severity: int = 3,
    limit: int = 10,
    to_openclaw: bool = True,
    to_telegram: bool = False,
    to_discord: bool = False,
) -> dict:
    """Fetch Swift alerts and send to configured channels. Returns stats."""
    events = fetch_swift_alerts(min_severity=min_severity, limit=limit)
    if not events:
        return {"events": 0, "sent": {}}

    formatted = "\n\n".join(format_event_message(e) for e in events)
    sent = {}

    if to_openclaw and send_to_openclaw(events):
        sent["openclaw"] = True
    if to_telegram and send_to_telegram(formatted):
        sent["telegram"] = True
    if to_discord and send_to_discord(formatted):
        sent["discord"] = True

    return {"events": len(events), "sent": sent}
