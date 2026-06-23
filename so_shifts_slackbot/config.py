"""Settings for the Slack bot — loaded from environment variables.

All policy and tunables live here; nothing is hard-coded elsewhere.
Load with ``Settings.from_env()`` at startup.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    sheet_id: str = ""
    slack_bot_token: str = ""

    summary_tab_name: str = "Summary"

    # Slack user group handles (without the @)
    group_supsci: str = "summit-sup-sci"
    group_day: str = "os-day-shift"
    group_night: str = "os-night-shift"

    # Map from group handle -> column label in the Summary tab that holds the assignee(s)
    # Adjust once the real Summary tab layout is known.
    summary_columns: dict[str, str] = field(default_factory=lambda: {
        "summit-sup-sci": "SupSci",
        "os-day-shift": "Day Shift",
        "os-night-shift": "Night Shift",
    })

    @classmethod
    def from_env(cls) -> Settings:
        s = cls()
        s.sheet_id = os.environ.get("SHIFT_SHEET_ID", "")
        s.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
        s.group_supsci = os.environ.get("SLACK_GROUP_SUPSCI", s.group_supsci)
        s.group_day = os.environ.get("SLACK_GROUP_DAY", s.group_day)
        s.group_night = os.environ.get("SLACK_GROUP_NIGHT", s.group_night)
        return s

    def validate(self) -> None:
        if not self.sheet_id:
            raise ValueError("SHIFT_SHEET_ID is required.")
        if not self.slack_bot_token:
            raise ValueError("SLACK_BOT_TOKEN is required.")
