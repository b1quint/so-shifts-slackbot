# Handoff — so-shifts-slackbot

Current branch: `minimum-valuable-product`

## What works

End-to-end sheet reading is verified against the live spreadsheet:

```
❯ uv run shifts-slackbot --sheet-only --date 2026-06-23

Reading Summary tab for 2026-06-23 …

Assignments read from sheet:
  [os-night-shift] OS Night Shift Manager: <name>
  [os-night-shift] OS Late Shift: <name>
  [os-day-shift] OS Day Shift Manager: <name>
  [os-day-shift] OS Day Shift: <name>
  [summit-sup-sci] Summit Support Scientist: <name>
```

- `--sheet-only` reads Summary + OS + SupSci tabs and resolves initials → full names. No Slack API calls.
- `--dry-run` additionally resolves full names → Slack user IDs and plans the group updates, but does not write.
- Running without flags does the live sync.

## Environment setup

```bash
cp .env.example .env
# Fill in:
#   SHIFT_SHEET_ID=<spreadsheet id from the URL>
#   SLACK_BOT_TOKEN=xoxb-...
```

Google Sheets OAuth token is cached at `~/.config/gspread/authorized_user.json` (shared with
`so-shifts-supsci` — no re-auth needed if that project has already been authorized).

The Slack app needs these bot token scopes: `usergroups:read`, `usergroups:write`, `users:read`.
`usergroups:write` requires a paid Slack workspace.

## Immediate next steps

### 1. Normalize OS name format (easy, do first)

OS names come out of the roster as `"Surname, Name"` (e.g. `"<name>"`).
SupSci names are `"Name Surname"` (e.g. `"<name>"`).

Fix in `io/sheets.py` — add a `_normalize_name(name: str) -> str` helper that detects
the comma pattern and flips it:

```python
def _normalize_name(name: str) -> str:
    if "," in name:
        surname, given = name.split(",", 1)
        return f"{given.strip()} {surname.strip()}"
    return name
```

Call it in `parse_roster` when building the `{initials: name}` dict.

### 2. Run `--dry-run` to test Slack name resolution

```bash
uv run shifts-slackbot --dry-run --date 2026-06-23
```

This will paginate through all Slack workspace users and try to match the resolved full
names. Expect warnings for any name that does not match a Slack profile exactly — those
will need manual mapping or profile corrections.

### 3. Open a PR and merge to `main`

Once the dry-run output looks correct, open a PR from `minimum-valuable-product` → `main`.

### 4. Schedule the bot (future)

Run daily (e.g. 07:00 Chile time) via a GitHub Actions cron workflow or a local cron job.
The command for a scheduled live run is simply:

```bash
uv run shifts-slackbot
```

(no flags — defaults to today's date, live sync).

## Known issues / open items

| # | Issue | Where to fix |
|---|---|---|
| 1 | OS names stored as `"Surname, Name"` — needs normalization before Slack matching | `io/sheets.py::parse_roster` |
| 2 | Slack `users_list` paginates the entire workspace — slow for large workspaces | `io/slack.py::list_users` (could filter or cache) |
| 3 | Column C role codes (for OS rows) not yet documented | `docs/summary-tab-layout.md` |

## Architecture in one paragraph

`cli.py` loads `.env`, reads `Settings`, calls `io/sheets.fetch_summary` (opens 3 tabs,
parses initials → full names), then calls `io/slack.sync` (resolves full names → Slack
user IDs, updates user groups). All parsing logic (`parse_roster`, `parse_date_row`,
`parse_summary_grid`) is pure Python with no network calls — fully unit-tested. The only
network calls are in `io/sheets.py` (gspread) and `io/slack.py` (slack_sdk).

## File map

```
so_shifts_slackbot/
├── cli.py          # entrypoint — flags: --date, --dry-run, --sheet-only, -v
├── config.py       # Settings, SummaryLayout, RosterLayout (all row/col indices here)
├── models.py       # ShiftAssignment, GroupUpdate, SyncResult
└── io/
    ├── sheets.py   # gspread adapter + pure parsers (parse_roster, parse_summary_grid)
    └── slack.py    # slack_sdk adapter (list_usergroups, list_users, build_updates, sync)
docs/
└── summary-tab-layout.md   # authoritative layout reference for the Summary tab
```
