"""CLI entrypoint for the Shifts Slack bot.

Usage:
    shifts-slackbot [--date YYYY-MM-DD] [--dry-run]

Reads the Summary tab of the Unified Shift Schedule for the given date
(default: today) and updates the configured Slack user groups.

Required environment variables:
    SHIFT_SHEET_ID    — Google Sheets spreadsheet id
    SLACK_BOT_TOKEN   — Slack bot token (xoxb-...)
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from so_shifts_slackbot.config import Settings
from so_shifts_slackbot.io.sheets import fetch_summary
from so_shifts_slackbot.io.slack import sync


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="shifts-slackbot",
        description="Sync today's shift assignments from the spreadsheet to Slack user groups.",
    )
    p.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Date to sync (default: today).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without calling the Slack API.",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    settings = Settings.from_env()
    try:
        settings.validate()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    target_date: date | None = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"error: invalid date {args.date!r} — use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    print(f"Reading Summary tab for {target_date or date.today()} …")
    assignments = fetch_summary(settings, target_date=target_date)

    if not assignments:
        print("No assignments found for that date.")
        sys.exit(0)

    for a in assignments:
        names = ", ".join(a.assignees) or "(none)"
        print(f"  {a.role}: {names}")

    result = sync(settings, assignments, dry_run=args.dry_run)

    if args.dry_run:
        print("\n[dry-run] no changes written to Slack.")

    for w in result.skipped:
        print(f"warning: {w}")
    for e in result.errors:
        print(f"error: {e}", file=sys.stderr)

    if result.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
