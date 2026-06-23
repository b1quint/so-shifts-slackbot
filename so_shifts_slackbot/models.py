"""Pure domain types for the Slack bot.

No gspread, no Slack SDK imports here — just data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class ShiftAssignment:
    """Who is assigned to a named shift role on a given date."""

    date: date
    role: str        # e.g. "SupSci", "Day Shift", "Night Shift"
    assignees: tuple[str, ...]  # display names from the sheet


@dataclass(frozen=True)
class GroupUpdate:
    """A pending update: set a Slack user group to a list of member user IDs."""

    group_handle: str          # e.g. "summit-sup-sci"
    group_id: str              # Slack usergroup ID (S...)
    member_ids: tuple[str, ...]  # Slack user IDs (U...)
    display_names: tuple[str, ...]  # for human-readable logging


@dataclass
class SyncResult:
    """Outcome of one sync run."""

    date: date
    updates: list[GroupUpdate] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)   # group handles with no match
    errors: list[str] = field(default_factory=list)
