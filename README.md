# so-shifts-slackbot

Reads the Unified Shift Schedule spreadsheet (`Summary` tab) and updates Slack user groups
with the current shift assignments:

- `@summit-sup-sci` — Support Scientist on shift
- `@os-day-shift` — Operations Specialist day shift
- `@os-night-shift` — Operations Specialist night shift

## Setup

1. Copy `.env.example` to `.env` and fill in `SHIFT_SHEET_ID` and `SLACK_BOT_TOKEN`.
2. Install: `uv sync`
3. Authorize Google Sheets (one-time browser flow): `uv run shifts-slackbot --dry-run`

## Usage

```
shifts-slackbot [--date YYYY-MM-DD] [--dry-run] [-v]
```
