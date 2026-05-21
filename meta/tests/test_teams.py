"""Test the team validator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from meta.loaders.errors import GovernanceLoadError
from meta.loaders.members import load_members
from meta.loaders.teams import load_teams
from meta.validator.src.reporter import ErrorCode, Reporter, bind_reporter
from meta.validator.src.rules.teams import TeamValidationError, TeamValidator

from .helper import has_error, no_errors
from .mock_clients.mock_github_client import (
    MockGithubClientNotFound,
    MockGithubClientRateLimitExceeded,
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
    """Non-404 ``GithubException`` during repo checks should abort validation."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), MEMBERS_FOR_TEAMS)
    teams = load_teams(bind_reporter(reporter), "meta/tests/teams/valid.toml")
    assert no_errors(reporter)
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(MockGithubClientRateLimitExceeded()),
    )
    with pytest.raises(TeamValidationError):
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


INVALID_SYNTAX_FIXTURE = "meta/tests/teams/load_errors/invalid-syntax.toml"


def test_team_invalid_syntax() -> None:
    """Invalid TOML syntax should abort loading with ``GovernanceLoadError``."""
    reporter = Reporter()
    with pytest.raises(GovernanceLoadError) as exc_info:
        load_teams(bind_reporter(reporter), INVALID_SYNTAX_FIXTURE)
    assert exc_info.value.file_path.endswith("invalid-syntax.toml")


def test_team_malformed_structure() -> None:
    """Malformed team documents should abort loading with ``GovernanceLoadError``."""
    reporter = Reporter()
    with pytest.raises(GovernanceLoadError) as exc_info:
        load_teams(
            bind_reporter(reporter),
            "meta/tests/teams/load_errors/malformed-structure.toml",
        )
    assert exc_info.value.file_path.endswith("malformed-structure.toml")
    assert "malformed team structure" in exc_info.value.message
