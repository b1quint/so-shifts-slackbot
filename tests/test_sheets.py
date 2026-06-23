"""Tests for the Summary tab parser (pure — no network)."""

from datetime import date

from so_shifts_slackbot.config import Settings
from so_shifts_slackbot.io.sheets import _parse_summary, _to_date


def _settings() -> Settings:
    s = Settings()
    s.summary_columns = {
        "summit-sup-sci": "SupSci",
        "os-day-shift": "Day Shift",
        "os-night-shift": "Night Shift",
    }
    return s


def test_to_date_serial():
    # 2026-06-23 is serial 46196 from Google Sheets origin 1899-12-30
    d = _to_date(46196)
    assert d == date(2026, 6, 23)


def test_to_date_iso_string():
    assert _to_date("2026-06-23") == date(2026, 6, 23)


def test_to_date_blank():
    assert _to_date("") is None
    assert _to_date(None) is None


def test_parse_summary_finds_today():
    today = date(2026, 6, 23)
    serial = 46196  # 2026-06-23
    raw = [
        ["Date", "SupSci", "Day Shift", "Night Shift"],
        [serial, "Alice", "Bob", "Carol, Dave"],
        [serial + 1, "Eve", "Frank", "Grace"],
    ]
    assignments = _parse_summary(raw, today, _settings())
    assert len(assignments) == 3
    roles = {a.role for a in assignments}
    assert roles == {"SupSci", "Day Shift", "Night Shift"}
    supsci = next(a for a in assignments if a.role == "SupSci")
    assert supsci.assignees == ("Alice",)
    night = next(a for a in assignments if a.role == "Night Shift")
    assert night.assignees == ("Carol", "Dave")


def test_parse_summary_wrong_date_returns_empty():
    raw = [
        ["Date", "SupSci", "Day Shift", "Night Shift"],
        [46205, "Alice", "Bob", "Carol"],
    ]
    assignments = _parse_summary(raw, date(2026, 6, 24), _settings())
    assert assignments == []


def test_parse_summary_missing_column():
    raw = [
        ["Date", "SupSci"],  # Day Shift and Night Shift columns absent
        [46196, "Alice"],
    ]
    assignments = _parse_summary(raw, date(2026, 6, 23), _settings())
    assert len(assignments) == 1
    assert assignments[0].role == "SupSci"
