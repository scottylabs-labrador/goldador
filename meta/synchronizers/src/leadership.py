"""Set the leadership team's members and leads from Labrador's roles in Grouper."""

from __future__ import annotations

from typing import TYPE_CHECKING

from meta.clients.grouper_client import get_andrew_ids
from meta.logger import get_app_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from meta.models import Member, Team

LABRADOR_ROLES = "Community:Department:ScottyLabs:ref:committees:labrador:roles"

# Roles whose holders are leadership leads, which makes them leadership admins
LEAD_ROLES = ("director", "head-of-onboarding-and-documentation")


def set_leadership_from_grouper(
    leadership: Team,
    members: dict[str, Member],
    get_group_andrew_ids: Callable[[str], set[str]] = get_andrew_ids,
) -> None:
    """Set `leadership`'s members and leads from Labrador's roles in Grouper."""
    logger = get_app_logger()
    github_usernames = {
        member.andrew_id.lower(): username
        for username, member in members.items()
        if member.andrew_id
    }

    def to_github_usernames(andrew_ids: set[str]) -> set[str]:
        usernames = set()
        for andrew_id in sorted(andrew_ids):
            username = github_usernames.get(andrew_id)
            if username is None:
                logger.warning(
                    "%s holds a Labrador role in Grouper but has no member file",
                    andrew_id,
                )
                continue
            usernames.add(username)
        return usernames

    role_holders = get_group_andrew_ids(f"{LABRADOR_ROLES}:all")
    lead_role_holders = set().union(
        *(get_group_andrew_ids(f"{LABRADOR_ROLES}:{role}") for role in LEAD_ROLES),
    )

    leadership.members = sorted(to_github_usernames(role_holders))
    leadership.leads = sorted(to_github_usernames(lead_role_holders))
