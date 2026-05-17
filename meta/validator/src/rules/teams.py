"""Team validation runner."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
from github import GithubException

from meta.clients.github_client import get_github_client
from meta.logger import get_app_logger
from meta.validator.src.reporter import ErrorCode

if TYPE_CHECKING:
    from meta.models import Member, Team
    from meta.validator.src.reporter import Reporter


GITHUB_ORG_NAME = "ScottyLabs-Labrador"


class TeamValidationError(Exception):
    """Raised when validation fails in a way that should abort the run."""

    message: str

    def __init__(self, message: str) -> None:
        """Initialize a validation error."""
        self.message = message


class TeamValidator:
    """Run team validation and record results."""

    def __init__(
        self,
        teams: dict[str, Team],
        members: dict[str, Member],
        reporter: Reporter,
    ) -> None:
        """Create a team validator."""
        self.teams = teams
        self.members = members
        self.reporter = reporter
        self.logger = get_app_logger()

    def validate(self) -> None:
        """Validate all teams (checks ordered per team; teams run in parallel)."""
        try:
            asyncio.run(self._validate_async())
        except TeamValidationError as e:
            self.logger.exception(e.message)
            raise

    async def _validate_async(self) -> None:
        """Validate each team concurrently using a shared async HTTP client scope."""
        async with httpx.AsyncClient() as _:
            await asyncio.gather(
                *[self._validate_team(team) for team in self.teams.values()],
            )

    async def _validate_team(self, team: Team) -> None:
        """Run all checks for a single team."""
        await asyncio.to_thread(self.validate_leads_are_members, team)
        await asyncio.to_thread(self.validate_cross_references, team)
        await asyncio.to_thread(self.validate_github_repos_exist, team)

    def validate_leads_are_members(self, team: Team) -> None:
        """Ensure every lead is also listed as a member."""
        member_set = set(team.members)
        for lead in team.leads:
            if lead not in member_set:
                self.reporter.insert_error(
                    team.file_path,
                    ErrorCode.LEAD_CROSS_REFERENCE,
                    f"Lead {lead!r} missing from members",
                )

    def validate_cross_references(self, team: Team) -> None:
        """Check that all team contributors exist in contributors."""
        for member in team.members:
            if member not in self.members:
                self.reporter.insert_error(
                    team.file_path,
                    ErrorCode.MEMBER_CROSS_REFERENCE,
                    f"Unknown member: {member}",
                )

    def validate_github_repos_exist(self, team: Team) -> None:
        """Ensure that all GitHub repositories for this team exist."""
        github_client = get_github_client()
        for repo in team.repos:
            try:
                repo_name = f"{GITHUB_ORG_NAME}/{repo.name}"
                github_client.get_repo(repo_name)
            except GithubException as e:
                if e.status == HTTPStatus.NOT_FOUND:
                    self.reporter.insert_error(
                        team.file_path,
                        ErrorCode.GITHUB_REPO_NOT_FOUND,
                        f"GitHub repository {repo_name} not found",
                    )
                    continue

                error_message = f"Unexpected GitHub API error: {e}"
                raise TeamValidationError(error_message) from e
