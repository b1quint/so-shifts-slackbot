# Summary Tab Layout — Unified Shift Schedule Spreadsheet

Layout reference for the **`Summary`** tab of the *Unified Summit Shifts Schedule* spreadsheet.
This tab is the source of truth consumed by `so-shifts-slackbot` to update Slack user groups.
It is also the aggregation view used by humans to check daily coverage across all roles.

**Related documentation:**
- SupSci tab layout → `so-shifts-supsci` repo, `docs/sheet-integration.md`
- OS roster (names/initials) → `OS` tab in the same spreadsheet (described below)
- SupSci roster (names/initials) → `SupSci` tab in the same spreadsheet

---

## Column layout

| Column(s) | Content |
| --- | --- |
| A | Row label (human-readable role or section name) |
| B | *(purpose unclear — see open questions)* |
| C | *(purpose unclear — see open questions)* |
| D → | One column per date, advancing right |

Columns A–C are **static** (no date data). All date-bearing data starts at column D.

---

## Row layout (header rows)

| Row | Content | Use programmatically? |
| --- | --- | --- |
| 1 | Month name — merged cells spanning the month's columns | **No** — merged headers only |
| 2 | Full date (stored as a Google Sheets date serial / full date value) | **Yes** — primary date key |
| 3 | Day-of-week label (e.g. "Mon", "Tue") | No — derived from row 2 |

Row 2 is the **date index**: fetch it with `UNFORMATTED_VALUE` to get the raw date serial,
then convert via the Google Sheets origin (`1899-12-30 + serial days`). Formatted strings
are also acceptable if the sheet is configured that way.

---

## Data rows — roles and Slack group membership

### OS Night Shift (`@os-night-shift`)

Both rows 8 and 9 contribute members to the `@os-night-shift` Slack user group.

| Row | Role label | Cell content | Notes |
| --- | --- | --- | --- |
| 8 | OS Night Shift Manager | Initials of the assigned OS | One person per date |
| 9 | OS Late Shift | Initials of the assigned OS | One person per date |

The **combined** set of assignees from rows 8 and 9 on a given date is synced to
`@os-night-shift`. Either row may be empty on a given date.

### OS Day Shift (`@os-day-shift`)

Both rows 10 and 11 contribute members to the `@os-day-shift` Slack user group.

| Row | Role label | Cell content | Notes |
| --- | --- | --- | --- |
| 10 | OS Day Shift Manager | Initials of the assigned OS | One person per date |
| 11 | OS Day Shift | Initials of the assigned OS | One person per date |

The **combined** set of assignees from rows 10 and 11 is synced to `@os-day-shift`.

### Summit Support Scientist (`@summit-sup-sci`)

| Row | Role label | Cell content | Notes |
| --- | --- | --- | --- |
| 16 | Summit Support Scientist | Initials of the assigned SupSci | One person per date |

A single person per date is synced to `@summit-sup-sci`.

---

## Roster lookups (initials → full name → Slack user)

Cells in the data rows hold **initials**, not full names. The bot resolves initials
to full names using two roster tabs, then matches full names to Slack users.

### OS roster — `OS` tab

| Column | Content | Starting row |
| --- | --- | --- |
| A | Full name | Row 12 |
| B | Initials | Row 12 |

Each person occupies **two rows merged vertically** in column A; the name appears in
the top of the merged pair. Read until the first blank name cell.

Used for: rows 8, 9, 10, 11 in the Summary tab.

### SupSci roster — `SupSci` tab

Initials-to-name mapping for Summit Support Scientists. *(Exact column/row layout
to be confirmed — see open questions below. The SupSci tab layout is also documented
in `so-shifts-supsci/docs/sheet-integration.md`.)*

Used for: row 16 in the Summary tab.

---

## Open questions

The following points were unclear when this document was written and need confirmation
before the corresponding code can be finalized:

1. **Columns B and C in the Summary tab.** What labels or data do they carry?
   Are they used programmatically at all, or purely visual aids?

2. **Rows 4–7 and 12–15.** Are any of these rows relevant to the bot, or are
   they structural / empty / section dividers?

3. **Vertical merging in the Summary tab.** The SupSci tab uses two rows per person
   (availability row + shift row). Do the data rows in the Summary tab (8–11, 16)
   follow any similar vertical-merge convention, or is each role truly a single row?

4. **SupSci initials lookup.** In the `SupSci` tab, which column holds full names
   and which holds initials? What is the starting row? (The SupSci tab layout is
   documented for the availability/assignment grid, but the name↔initials index
   within that tab is not yet confirmed.)

5. **Multiple assignees.** Can a single date cell in rows 8–11 or 16 hold more than
   one set of initials (e.g. a backup or co-assignment)? If so, what is the delimiter?

6. **Empty cells.** When no one is assigned to a role on a given date, is the cell
   blank, or does it hold a placeholder (e.g. `?` or `-`)?
