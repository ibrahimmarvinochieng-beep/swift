#!/usr/bin/env python3
"""CLI for OpenClaw bridge. Run via cron or OpenClaw exec."""

import argparse
import sys
from .bridge import run_bridge


def main():
    parser = argparse.ArgumentParser(description="Swift → OpenClaw bridge")
    parser.add_argument("--min-severity", type=int, default=3, help="Min event severity (1-5)")
    parser.add_argument("--limit", type=int, default=10, help="Max events to fetch")
    parser.add_argument("--openclaw", action="store_true", default=True, help="Send to OpenClaw webhook")
    parser.add_argument("--no-openclaw", action="store_true", help="Disable OpenClaw")
    parser.add_argument("--telegram", action="store_true", help="Send to Telegram")
    parser.add_argument("--discord", action="store_true", help="Send to Discord")
    args = parser.parse_args()

    to_openclaw = args.openclaw and not args.no_openclaw
    result = run_bridge(
        min_severity=args.min_severity,
        limit=args.limit,
        to_openclaw=to_openclaw,
        to_telegram=args.telegram,
        to_discord=args.discord,
    )

    print(f"Fetched {result['events']} events, sent to: {list(result['sent'].keys()) or 'none'}")
    if result["events"] > 0 and not result["sent"]:
        print("Warning: No channels configured. Set OPENCLAW_WEBHOOK_* or TELEGRAM_* or DISCORD_*", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
