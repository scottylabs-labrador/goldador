"""Slack synchronizer.

Creates a Slack channel for each team and invites the team members to the channel.
"""

import sys
from typing import TYPE_CHECKING, cast, override

from dotenv import load_dotenv

from meta.clients.keycloak_client import get_keycloak_client
from meta.clients.slack_client import get_slack_client
from meta.logger import (
    log_operation,
    log_team_sync,
    print_section,
)

from ._constants import LEADERSHIP
from .abstract import AbstractSynchronizer

if TYPE_CHECKING:
    from meta.models import Team


class SlackSynchronizer(AbstractSynchronizer):
    """Slack synchronizer."""

    def __init__(
        self,
    ) -> None:
        """Initialize the slack synchronizer."""
        super().__init__()

        # Initialize the Keycloak client
        self.keycloak_client = get_keycloak_client()

        # Initialize the Slack user and bot clients
        # The user client is used to create channels since the bot don't
        # have permission to do so.
        # The bot client is used to invite users to channels since a user can't
        # invite themselves to a channel.
        self.user_client = get_slack_client(env_var_name="SLACK_USER_TOKEN")
        self.bot_client = get_slack_client(env_var_name="SLACK_BOT_TOKEN")

    @override
    def sync(self) -> None:
        print_section("Syncing Slack")

        with log_operation("get all Slack channels"):
            self.channels = self.get_all_channels()
        self.logger.debug("Found %d Slack channels\n", len(self.channels))

        for team_slug, team in self.teams.items():
            # Leadership Slack channel is private and not managed by Goldador
            if team_slug == LEADERSHIP:
                continue
            self.sync_team(team_slug, team)

    def get_all_channels(self) -> list[dict[str, str]]:
        """Get all channels channels and their IDs."""
        channels: list[dict[str, str]] = []
        cursor: str | None = None
        while True:
            response = self.bot_client.conversations_list(
                types="public_channel",
                cursor=cursor,
            )

            channels.extend(
                {"id": channel["id"], "name": channel["name"]}
                for channel in response["channels"]
            )

            metadata = cast(
                "dict[str, object]",
                response.get("response_metadata"),
            )
            cursor = cast("str | None", metadata.get("next_cursor"))
            if not cursor:
                break

        return channels

    @log_team_sync()
    def sync_team(self, team_slug: str, team: Team) -> None:
        """Sync a team."""
        channel_id = self.get_or_create_channel(team_slug)

        # Get the desired members' Slack IDs for the team
        desired_members = set()
        for member_id in team.members:
            member = self.members[member_id]
            andrew_id = member.andrew_id
            if andrew_id is None:
                continue
            user_id = self.keycloak_client.get_user_id_by_username(andrew_id)

            # User not found in Keycloak would be caught by the validator
            if user_id is None:
                continue

            # User not linked to a Slack account would be caught by the validator
            member_slack_id = self.keycloak_client.get_user_slack_id(user_id)
            if member_slack_id is None:
                continue

            desired_members.add(member_slack_id)

        # Sync the channel
        self.sync_channel(team, channel_id, desired_members)

    def get_or_create_channel(self, team_slug: str) -> str:
        """Get or create a Slack channel for a team."""
        channel_name = f"labrador-{team_slug}"
        channel = next(
            (channel for channel in self.channels if channel["name"] == channel_name),
            None,
        )
        if channel is not None:
            return channel["id"]

        with log_operation(f"create Slack channel: {channel_name}"):
            response = self.user_client.conversations_create(name=channel_name)
            return cast("str", response["channel"]["id"])

    def sync_channel(
        self,
        team: Team,
        channel_id: str,
        desired_members: set[str],
    ) -> None:
        """Invite members of a team to a Slack channel."""
        try:
            info = self.bot_client.conversations_info(channel=channel_id)
        except Exception:
            self.logger.exception(
                "Error getting info of %s Slack channel",
                team.name,
            )
            sys.exit(1)

        if not info["channel"]["is_member"]:
            with log_operation(f"join Slack channel: {channel_id}"):
                self.bot_client.conversations_join(channel=channel_id)

        # Get the current members of the channel
        try:
            response = self.bot_client.conversations_members(channel=channel_id)
        except Exception:
            self.logger.exception(
                "Error getting members of %s Slack channel",
                team.name,
            )
            sys.exit(1)

        # Get the users to invite
        current_members = set(response["members"])
        users = list(desired_members - current_members)
        if not users:
            self.logger.debug(
                "No users to invite to %s Slack channel.",
                team.name,
            )
            return

        # Invite the users to the channel
        log_message = f"invite users to {team.name} Slack channel: {users}"
        with log_operation(log_message):
            self.bot_client.conversations_invite(channel=channel_id, users=users)


def main() -> None:
    """CLI entry point."""
    load_dotenv()
    slack_synchronizer = SlackSynchronizer()
    slack_synchronizer.sync()
