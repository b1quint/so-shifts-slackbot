"""Slack adapter — look up user groups and update their members.

Uses the Slack Web API via slack_sdk. Required OAuth scopes for the bot token:
  - usergroups:read  (list groups, get members)
  - usergroups:write (update group membership)
  - users:read       (look up users by display name / email)
  - users:read.email (if matching by email)
"""

from __future__ import annotations

import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from so_shifts_slackbot.config import Settings
from so_shifts_slackbot.models import GroupUpdate, ShiftAssignment, SyncResult

logger = logging.getLogger(__name__)


def make_client(settings: Settings) -> WebClient:
    return WebClient(token=settings.slack_bot_token)


def list_usergroups(client: WebClient) -> dict[str, str]:
    """Return {handle: group_id} for all enabled user groups in the workspace."""
    response = client.usergroups_list(include_disabled=False)
    return {g["handle"]: g["id"] for g in response["usergroups"]}


def list_users(client: WebClient) -> dict[str, str]:
    """Return {display_name_lower: user_id} for all non-bot, non-deleted users."""
    mapping: dict[str, str] = {}
    cursor = None
    while True:
        kwargs: dict = {"limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        response = client.users_list(**kwargs)
        for member in response["members"]:
            if member.get("deleted") or member.get("is_bot"):
                continue
            uid = member["id"]
            profile = member.get("profile", {})
            for key in ("display_name", "real_name", "display_name_normalized", "real_name_normalized"):
                name = profile.get(key, "").strip().lower()
                if name:
                    mapping[name] = uid
        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return mapping


def resolve_names(
    names: tuple[str, ...],
    user_map: dict[str, str],
) -> tuple[list[str], list[str]]:
    """Match display names to Slack user IDs.

    Returns (matched_ids, unmatched_names).
    """
    matched, unmatched = [], []
    for name in names:
        uid = user_map.get(name.lower())
        if uid:
            matched.append(uid)
        else:
            unmatched.append(name)
    return matched, unmatched


def build_updates(
    assignments: list[ShiftAssignment],
    settings: Settings,
    group_map: dict[str, str],
    user_map: dict[str, str],
) -> tuple[list[GroupUpdate], list[str]]:
    """Map ShiftAssignments to GroupUpdates, resolving names to Slack IDs.

    Returns (updates, warnings).
    """
    # col_label -> group_handle
    col_to_handle: dict[str, str] = {
        col_label: handle
        for handle, col_label in settings.summary_columns.items()
    }

    updates: list[GroupUpdate] = []
    warnings: list[str] = []

    for assignment in assignments:
        handle = col_to_handle.get(assignment.role)
        if not handle:
            warnings.append(f"no group handle for role {assignment.role!r}")
            continue
        group_id = group_map.get(handle)
        if not group_id:
            warnings.append(f"Slack group @{handle} not found in workspace")
            continue
        member_ids, unmatched = resolve_names(assignment.assignees, user_map)
        if unmatched:
            warnings.append(
                f"@{handle}: could not resolve Slack user(s): {', '.join(unmatched)}"
            )
        if not member_ids:
            warnings.append(f"@{handle}: no members resolved — skipping update")
            continue
        updates.append(GroupUpdate(
            group_handle=handle,
            group_id=group_id,
            member_ids=tuple(member_ids),
            display_names=assignment.assignees,
        ))
    return updates, warnings


def apply_updates(
    client: WebClient,
    updates: list[GroupUpdate],
    *,
    dry_run: bool = False,
) -> list[str]:
    """Push each GroupUpdate to Slack. Returns list of error strings."""
    errors: list[str] = []
    for update in updates:
        names = ", ".join(update.display_names)
        if dry_run:
            logger.info("[dry-run] @%s → %s", update.group_handle, names)
            continue
        try:
            client.usergroups_users_update(
                usergroup=update.group_id,
                users=list(update.member_ids),
            )
            logger.info("Updated @%s → %s", update.group_handle, names)
        except SlackApiError as exc:
            msg = f"@{update.group_handle}: Slack API error — {exc.response['error']}"
            logger.error(msg)
            errors.append(msg)
    return errors


def sync(
    settings: Settings,
    assignments: list[ShiftAssignment],
    *,
    client: WebClient | None = None,
    dry_run: bool = False,
) -> SyncResult:
    """Top-level: take parsed sheet assignments and sync Slack groups."""
    from datetime import date

    client = client or make_client(settings)
    result = SyncResult(date=date.today())

    group_map = list_usergroups(client)
    user_map = list_users(client)

    updates, warnings = build_updates(assignments, settings, group_map, user_map)
    result.skipped.extend(warnings)

    errors = apply_updates(client, updates, dry_run=dry_run)
    result.errors.extend(errors)
    result.updates.extend(updates)
    return result
