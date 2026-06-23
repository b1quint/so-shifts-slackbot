"""Google Sheets adapter — read the Summary tab.

This is the only module that imports gspread. It returns plain Python objects
so the rest of the bot never touches the Sheets API.

Auth is OAuth user credentials via gspread.oauth() — authorize once in a
browser, token cached at ~/.config/gspread/. The spreadsheet id comes from
Settings.sheet_id (loaded from SHIFT_SHEET_ID env var).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import gspread
from gspread.utils import ValueRenderOption

from so_shifts_slackbot.config import Settings
from so_shifts_slackbot.models import ShiftAssignment


def authorize(settings: Settings) -> gspread.Client:
    return gspread.oauth()


def _to_date(value: Any) -> date | None:
    """Convert a Sheets cell value to a date.

    The Summary tab may store dates as serial numbers (integer days since
    1899-12-30), as formatted strings, or as ISO strings depending on how
    the sheet is set up. We handle the common cases.
    """
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        # Google Sheets serial: days since 1899-12-30
        from datetime import timedelta
        origin = date(1899, 12, 30)
        return origin + timedelta(days=int(value))
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d, %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def fetch_summary(
    settings: Settings,
    *,
    client: gspread.Client | None = None,
    target_date: date | None = None,
) -> list[ShiftAssignment]:
    """Read the Summary tab and return shift assignments for ``target_date``.

    If ``target_date`` is None, uses today.

    The Summary tab is expected to have dates in one column (or row) and
    shift roles in adjacent columns. The exact layout is adapted in
    ``_parse_summary``; adjust that function once the real layout is known.
    """
    if not settings.sheet_id:
        raise ValueError("SHIFT_SHEET_ID is required.")
    target_date = target_date or date.today()
    client = client or authorize(settings)
    spreadsheet = client.open_by_key(settings.sheet_id)
    worksheet = spreadsheet.worksheet(settings.summary_tab_name)
    raw = worksheet.get_all_values(value_render_option=ValueRenderOption.unformatted)
    return _parse_summary(raw, target_date, settings)


def _parse_summary(
    raw: list[list[Any]],
    target_date: date,
    settings: Settings,
) -> list[ShiftAssignment]:
    """Extract assignments for ``target_date`` from the raw Summary grid.

    IMPORTANT: this function is a STUB. The real Summary tab layout is not
    yet known. Update this once you can inspect the actual sheet structure.

    Current assumption: the first row is a header with role names; the first
    column holds dates. Each data cell holds the assignee name (or names,
    comma-separated).
    """
    if not raw:
        return []

    header = [str(c).strip() for c in raw[0]]
    role_cols = {
        role: header.index(col_label)
        for col_label in settings.summary_columns.values()
        for role in [col_label]
        if col_label in header
    }

    # Invert: col_label -> group_handle
    col_to_group: dict[str, str] = {
        col_label: handle
        for handle, col_label in settings.summary_columns.items()
    }

    assignments: list[ShiftAssignment] = []
    for row in raw[1:]:
        if not row:
            continue
        row_date = _to_date(row[0])
        if row_date != target_date:
            continue
        for col_label, col_idx in role_cols.items():
            if col_idx >= len(row):
                continue
            cell = str(row[col_idx]).strip()
            if not cell:
                continue
            names = tuple(n.strip() for n in cell.split(",") if n.strip())
            group_handle = col_to_group.get(col_label, col_label)
            assignments.append(ShiftAssignment(
                date=target_date,
                role=col_label,
                assignees=names,
            ))
    return assignments
