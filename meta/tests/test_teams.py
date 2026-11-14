"""Test the team validator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from github import GithubException

from meta.loaders.members import load_members
from meta.loaders.teams import load_teams
from meta.models import Repo, Team
from meta.validator.src.github_utils import GitHubRateLimitError
from meta.validator.src.reporter import ErrorCode, Reporter, bind_reporter
from meta.validator.src.rules.teams import TeamValidationError, TeamValidator

from .helper import has_error, no_errors
from .mock_clients.mock_github_client import (
    MockGithubClientNotFound,
    MockGithubClientRateLimitExceeded,
    MockGithubClientServerError,
    MockGithubClientValid,
    make_get_github_client,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

MEMBERS_FOR_TEAMS = "meta/tests/members/for_teams/*.toml"
GITHUB_CLIENT_FUNCTION_PATH = "meta.validator.src.rules.teams.get_github_client"


def test_team_valid(monkeypatch: MonkeyPatch) -> None:
    """A well-formed team and matching members produce no errors."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), MEMBERS_FOR_TEAMS)
    teams = load_teams(bind_reporter(reporter), "meta/tests/teams/valid.toml")
    assert no_errors(reporter)
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(MockGithubClientValid()),
    )
    TeamValidator(teams, members, reporter).validate()
    assert no_errors(reporter)


def test_team_wrong_key_ordering() -> None:
    """Top-level TOML keys must follow ``team.schema.json`` property order."""
    reporter = Reporter()
    load_teams(bind_reporter(reporter), "meta/tests/teams/wrong-key-ordering.toml")
    assert has_error(reporter, ErrorCode.TEAM_KEY_ORDERING)


def test_team_filename_not_lowercase() -> None:
    """Team file names must be fully lowercase."""
    reporter = Reporter()
    content = Path("meta/tests/teams/valid.toml").read_text(encoding="utf-8")
    load_teams(
        bind_reporter(reporter),
        file_contents=[("teams/MixedCase.toml", content)],
    )
    assert has_error(reporter, ErrorCode.TEAM_FILENAME_NOT_LOWERCASE)


def test_team_unknown_member_cross_reference(monkeypatch: MonkeyPatch) -> None:
    """Every team member github username must exist in the members index."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), MEMBERS_FOR_TEAMS)
    teams = load_teams(bind_reporter(reporter), "meta/tests/teams/unknown-member.toml")
    assert no_errors(reporter)
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(MockGithubClientValid()),
    )
    TeamValidator(teams, members, reporter).validate()
    assert has_error(reporter, ErrorCode.MEMBER_CROSS_REFERENCE)


def test_team_lead_not_in_members(monkeypatch: MonkeyPatch) -> None:
    """Every lead must also appear under membership members."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), MEMBERS_FOR_TEAMS)
    teams = load_teams(bind_reporter(reporter), "meta/tests/teams/lead-not-member.toml")
    assert no_errors(reporter)
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(MockGithubClientValid()),
    )
    TeamValidator(teams, members, reporter).validate()
    assert has_error(reporter, ErrorCode.LEAD_CROSS_REFERENCE)


def test_rate_limited_github_team_repo_raises(monkeypatch: MonkeyPatch) -> None:
    """A GitHub rate-limit response during repo checks should abort validation."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), MEMBERS_FOR_TEAMS)
    teams = load_teams(bind_reporter(reporter), "meta/tests/teams/valid.toml")
    assert no_errors(reporter)
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(MockGithubClientRateLimitExceeded()),
    )
    with pytest.raises(GitHubRateLimitError, match="GitHub API rate limit exceeded"):
        TeamValidator(teams, members, reporter).validate()


def test_unexpected_github_error_aborts_team_validation(
    monkeypatch: MonkeyPatch,
) -> None:
    """A non-rate-limit GitHub failure should abort team validation."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), MEMBERS_FOR_TEAMS)
    teams = load_teams(bind_reporter(reporter), "meta/tests/teams/valid.toml")
    assert no_errors(reporter)
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(MockGithubClientServerError()),
    )
    with pytest.raises(TeamValidationError, match="Unexpected GitHub API error"):
        TeamValidator(teams, members, reporter).validate()


def test_team_github_repo_not_found(monkeypatch: MonkeyPatch) -> None:
    """A missing GitHub repo should be reported as ``GITHUB_REPO_NOT_FOUND``."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), MEMBERS_FOR_TEAMS)
    teams = load_teams(bind_reporter(reporter), "meta/tests/teams/valid.toml")
    assert no_errors(reporter)
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(MockGithubClientNotFound()),
    )
    TeamValidator(teams, members, reporter).validate()
    assert has_error(reporter, ErrorCode.GITHUB_REPO_NOT_FOUND)


def test_team_not_file() -> None:
    """Teams must be a file."""
    reporter = Reporter()
    load_teams(bind_reporter(reporter), "meta/tests/teams/*")
    assert has_error(reporter, ErrorCode.TEAM_NOT_FILE)


class _CountingGithubRepoClient(MockGithubClientValid):
    """Count repository lookups."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.get_repo_calls: list[str] = []

    def get_repo(self, repo_name: str) -> None:
        """Record the lookup, then pretend the repository exists."""
        self.get_repo_calls.append(repo_name)
        super().get_repo(repo_name)


class _CountingGithubRepoNotFound(MockGithubClientNotFound):
    """Count repository lookups that 404."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.get_repo_calls: list[str] = []

    def get_repo(self, repo_name: str) -> None:
        """Record the lookup, then raise not-found."""
        self.get_repo_calls.append(repo_name)
        super().get_repo(repo_name)


class _SelectiveRepoClient(MockGithubClientValid):
    """404 selected repositories and count every lookup."""

    def __init__(self, missing: set[str]) -> None:
        """Treat names in ``missing`` as absent."""
        self.missing = missing
        self.get_repo_calls: list[str] = []

    def get_repo(self, repo_name: str) -> None:
        """Record the lookup, then 404 when ``repo_name`` is missing."""
        self.get_repo_calls.append(repo_name)
        if repo_name in self.missing:
            raise GithubException(status=404, data={"message": "Not Found"})


def _teams(*repo_names: str) -> dict[str, Team]:
    """Build a one-team index whose only remote check is repository existence."""
    team = Team(
        file_path="teams/fixture.toml",
        name="Fixture",
        description="Repository cache fixture.",
        create_oidc_clients=False,
        repos=[
            Repo(name=name, description="Fixture repository.") for name in repo_names
        ],
        leads=[],
        members=[],
    )
    return {"fixture": team}


def test_cached_repo_skips_github(monkeypatch: MonkeyPatch) -> None:
    """A repository that already exists is not looked up again."""
    github = _CountingGithubRepoClient()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )

    first = Reporter()
    TeamValidator(_teams("fixture-repo"), {}, first).validate()
    assert no_errors(first)
    assert github.get_repo_calls == ["ScottyLabs-Labrador/fixture-repo"]

    TeamValidator(_teams("fixture-repo"), {}, Reporter()).validate()
    assert github.get_repo_calls == ["ScottyLabs-Labrador/fixture-repo"]


def test_existing_repo_stays_cached_when_another_is_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    """A verified repository stays cached when a sibling lookup 404s."""
    github = _SelectiveRepoClient({"ScottyLabs-Labrador/missing-repo"})
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )

    first = Reporter()
    TeamValidator(_teams("fixture-repo", "missing-repo"), {}, first).validate()
    assert has_error(first, ErrorCode.GITHUB_REPO_NOT_FOUND)
    assert github.get_repo_calls == [
        "ScottyLabs-Labrador/fixture-repo",
        "ScottyLabs-Labrador/missing-repo",
    ]

    second = Reporter()
    TeamValidator(_teams("fixture-repo", "missing-repo"), {}, second).validate()
    assert github.get_repo_calls == [
        "ScottyLabs-Labrador/fixture-repo",
        "ScottyLabs-Labrador/missing-repo",
        "ScottyLabs-Labrador/missing-repo",
    ]
    assert has_error(second, ErrorCode.GITHUB_REPO_NOT_FOUND)


def test_github_repo_cache_is_case_insensitive(monkeypatch: MonkeyPatch) -> None:
    """Repository names that differ only by case share one cache entry."""
    github = _CountingGithubRepoClient()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )

    first = Reporter()
    TeamValidator(_teams("Fixture-Repo"), {}, first).validate()
    assert no_errors(first)
    assert github.get_repo_calls == ["ScottyLabs-Labrador/Fixture-Repo"]

    TeamValidator(_teams("fixture-repo"), {}, Reporter()).validate()
    assert github.get_repo_calls == ["ScottyLabs-Labrador/Fixture-Repo"]


def test_github_repo_not_found_is_not_cached(monkeypatch: MonkeyPatch) -> None:
    """A repository 404 is looked up again on the next run."""
    github = _CountingGithubRepoNotFound()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )

    first = Reporter()
    TeamValidator(_teams("missing-repo"), {}, first).validate()
    assert has_error(first, ErrorCode.GITHUB_REPO_NOT_FOUND)
    assert github.get_repo_calls == ["ScottyLabs-Labrador/missing-repo"]

    TeamValidator(_teams("missing-repo"), {}, Reporter()).validate()
    assert github.get_repo_calls == [
        "ScottyLabs-Labrador/missing-repo",
        "ScottyLabs-Labrador/missing-repo",
    ]
