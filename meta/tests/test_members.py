"""Test the member validator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from meta.loaders.members import load_members
from meta.models import Member
from meta.validator.src.github_utils import GitHubRateLimitError
from meta.validator.src.reporter import ErrorCode, Reporter, bind_reporter
from meta.validator.src.rules.members import MemberValidationError, MemberValidator

from .helper import has_error, no_errors
from .mock_clients.mock_github_client import (
    MockGithubClientNotFound,
    MockGithubClientRateLimitExceeded,
    MockGithubClientServerError,
    MockGithubClientValid,
    make_get_github_client,
)
from .mock_clients.mock_keycloak_client import (
    MockKeycloakClientMismatchedGithub,
    MockKeycloakClientMissingGithub,
    MockKeycloakClientMissingSlack,
    MockKeycloakClientUnexpectedError,
    MockKeycloakClientUserNotFound,
    MockKeycloakClientValid,
    make_get_keycloak_client,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

GITHUB_CLIENT_FUNCTION_PATH = "meta.validator.src.rules.members.get_github_client"
KEYCLOAK_CLIENT_FUNCTION_PATH = "meta.validator.src.rules.members.get_keycloak_client"


def test_member_valid(monkeypatch: MonkeyPatch) -> None:
    """Members must be valid."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), "meta/tests/members/valid.toml")
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientValid()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(mock_keycloak),
    )
    MemberValidator(members, reporter).validate()
    assert no_errors(reporter)


def test_member_key_ordering() -> None:
    """Members key ordering must be validated."""
    reporter = Reporter()
    load_members(bind_reporter(reporter), "meta/tests/members/wrong-key-ordering.toml")
    assert has_error(reporter, ErrorCode.MEMBER_KEY_ORDERING)


def test_member_not_file() -> None:
    """Members must be a file."""
    reporter = Reporter()
    load_members(bind_reporter(reporter), "meta/tests/members/*")
    assert has_error(reporter, ErrorCode.MEMBER_NOT_FILE)


def test_not_found_github_username(
    monkeypatch: MonkeyPatch,
) -> None:
    """A GitHub 404 should be reported as ``INVALID_GITHUB_USERNAME``."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientNotFound()
    mock_keycloak = MockKeycloakClientValid()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(mock_keycloak),
    )

    MemberValidator(members, reporter).validate()

    assert has_error(reporter, ErrorCode.INVALID_GITHUB_USERNAME)


def test_rate_limited_github_username(
    monkeypatch: MonkeyPatch,
) -> None:
    """A GitHub rate-limit response should abort validation early."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientRateLimitExceeded()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )

    with pytest.raises(GitHubRateLimitError, match="GitHub API rate limit exceeded"):
        MemberValidator(members, reporter).validate()


def test_unexpected_github_error_aborts_member_validation(
    monkeypatch: MonkeyPatch,
) -> None:
    """A non-rate-limit GitHub failure should abort member validation."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(MockGithubClientServerError()),
    )

    with pytest.raises(MemberValidationError, match="Unexpected GitHub API error"):
        MemberValidator(members, reporter).validate()


def test_not_found_keycloak_username(monkeypatch: MonkeyPatch) -> None:
    """A missing Keycloak user should be reported as ``INVALID_KEYCLOAK_USERNAME``."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientUserNotFound()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(mock_keycloak),
    )

    MemberValidator(members, reporter).validate()

    assert has_error(reporter, ErrorCode.INVALID_KEYCLOAK_USERNAME)


def test_missing_keycloak_github(monkeypatch: MonkeyPatch) -> None:
    """A Keycloak user without GitHub federation is an error."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientMissingGithub()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(mock_keycloak),
    )

    MemberValidator(members, reporter).validate()

    assert has_error(reporter, ErrorCode.MISSING_KEYCLOAK_GITHUB)


def test_mismatched_keycloak_github(monkeypatch: MonkeyPatch) -> None:
    """Keycloak GitHub login must match the member file stem."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientMismatchedGithub()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(mock_keycloak),
    )

    MemberValidator(members, reporter).validate()

    assert has_error(reporter, ErrorCode.MISMATCHED_KEYCLOAK_GITHUB)


def test_unexpected_keycloak_client_error_raises(
    monkeypatch: MonkeyPatch,
) -> None:
    """Unexpected Keycloak errors should hit generic ``except Exception`` and raise."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientUnexpectedError()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(mock_keycloak),
    )

    with pytest.raises(MemberValidationError):
        MemberValidator(members, reporter).validate()


def test_missing_keycloak_slack(monkeypatch: MonkeyPatch) -> None:
    """A Keycloak user without Slack federation is an error."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientMissingSlack()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(mock_keycloak),
    )

    MemberValidator(members, reporter).validate()

    assert has_error(reporter, ErrorCode.MISSING_KEYCLOAK_SLACK)


def test_skips_keycloak_when_no_andrew_id(monkeypatch: MonkeyPatch) -> None:
    """Members without ``andrew-id`` should not trigger Keycloak username checks."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/no-andrew-id.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientUnexpectedError()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(mock_github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(mock_keycloak),
    )

    MemberValidator(members, reporter).validate()
    assert no_errors(reporter)


class _CountingGithubClient(MockGithubClientValid):
    """Count GitHub user lookups."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.get_user_calls = 0

    def get_user(self, github_username: str) -> None:
        """Record the lookup, then pretend the user exists."""
        self.get_user_calls += 1
        super().get_user(github_username)


class _CountingGithubNotFound(MockGithubClientNotFound):
    """Count GitHub user lookups that 404."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.get_user_calls = 0

    def get_user(self, github_username: str) -> None:
        """Record the lookup, then raise not-found."""
        self.get_user_calls += 1
        super().get_user(github_username)


class _CountingKeycloakClient(MockKeycloakClientValid):
    """Count every Keycloak read."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        super().__init__()
        self.calls = 0

    def get_user_id_by_username(self, andrew_id: str) -> str:
        """Record the lookup, then pretend the user exists."""
        self.calls += 1
        return super().get_user_id_by_username(andrew_id)

    def get_user_github_username(self, user_id: str) -> str | None:
        """Record the lookup, then return the linked GitHub username."""
        self.calls += 1
        return super().get_user_github_username(user_id)

    def get_user_slack_id(self, user_id: str) -> str | None:
        """Record the lookup, then return the linked Slack id."""
        self.calls += 1
        return super().get_user_slack_id(user_id)


class _CountingMissingSlack(MockKeycloakClientMissingSlack):
    """Count Keycloak reads for a user with no Slack link."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        super().__init__()
        self.calls = 0

    def get_user_id_by_username(self, andrew_id: str) -> str:
        """Record the lookup, then return a synthetic user id."""
        self.calls += 1
        return super().get_user_id_by_username(andrew_id)

    def get_user_github_username(self, user_id: str) -> str | None:
        """Record the lookup, then return the linked GitHub username."""
        self.calls += 1
        return super().get_user_github_username(user_id)

    def get_user_slack_id(self, user_id: str) -> str | None:
        """Record the lookup, then report no Slack link."""
        self.calls += 1
        return super().get_user_slack_id(user_id)


def _member(github_username: str, andrew_id: str) -> dict[str, Member]:
    """Build a one-member index keyed by ``github_username``."""
    member = Member.model_validate(
        {
            "full-name": "Cache Member",
            "andrew-id": andrew_id,
            "file_path": f"members/{github_username}.toml",
        },
    )
    return {github_username: member}


def test_cached_member_skips_github_and_keycloak(monkeypatch: MonkeyPatch) -> None:
    """A member that already passed is not looked up again."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), "meta/tests/members/valid.toml")
    assert no_errors(reporter)

    github = _CountingGithubClient()
    keycloak = _CountingKeycloakClient()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(keycloak),
    )

    MemberValidator(members, reporter).validate()
    assert no_errors(reporter)
    github_calls = github.get_user_calls
    keycloak_calls = keycloak.calls
    assert github_calls
    assert keycloak_calls

    MemberValidator(members, Reporter()).validate()
    assert github.get_user_calls == github_calls
    assert keycloak.calls == keycloak_calls


def test_github_cache_retries_failed_keycloak(monkeypatch: MonkeyPatch) -> None:
    """A verified GitHub user is cached even when the Keycloak link check fails."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    github = _CountingGithubClient()
    keycloak = _CountingMissingSlack()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(keycloak),
    )

    MemberValidator(members, reporter).validate()
    assert has_error(reporter, ErrorCode.MISSING_KEYCLOAK_SLACK)
    github_calls = github.get_user_calls
    keycloak_calls = keycloak.calls
    assert github_calls
    assert keycloak_calls

    second = Reporter()
    MemberValidator(members, second).validate()
    assert github.get_user_calls == github_calls
    assert keycloak.calls != keycloak_calls
    assert has_error(second, ErrorCode.MISSING_KEYCLOAK_SLACK)


def test_github_username_cache_is_case_insensitive(monkeypatch: MonkeyPatch) -> None:
    """GitHub usernames that differ only by case share one cache entry."""
    github = _CountingGithubClient()
    keycloak = _CountingKeycloakClient()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(keycloak),
    )

    first = Reporter()
    MemberValidator(_member("Alice", "alice"), first).validate()
    assert no_errors(first)
    github_calls = github.get_user_calls
    assert github_calls

    MemberValidator(_member("alice", "alice"), Reporter()).validate()
    assert github.get_user_calls == github_calls


def test_keycloak_cache_includes_github_username(monkeypatch: MonkeyPatch) -> None:
    """The same Andrew ID with a different GitHub username is checked again."""
    github = _CountingGithubClient()
    keycloak = _CountingKeycloakClient()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(keycloak),
    )

    first = Reporter()
    MemberValidator(_member("alice", "alice"), first).validate()
    assert no_errors(first)
    keycloak_calls = keycloak.calls
    assert keycloak_calls

    second = Reporter()
    MemberValidator(_member("bob", "alice"), second).validate()
    assert keycloak.calls != keycloak_calls
    assert has_error(second, ErrorCode.MISMATCHED_KEYCLOAK_GITHUB)


def test_github_not_found_is_not_cached(monkeypatch: MonkeyPatch) -> None:
    """A GitHub 404 is looked up again on the next run."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    github = _CountingGithubNotFound()
    monkeypatch.setattr(
        GITHUB_CLIENT_FUNCTION_PATH,
        make_get_github_client(github),
    )
    monkeypatch.setattr(
        KEYCLOAK_CLIENT_FUNCTION_PATH,
        make_get_keycloak_client(MockKeycloakClientValid()),
    )

    MemberValidator(members, reporter).validate()
    assert has_error(reporter, ErrorCode.INVALID_GITHUB_USERNAME)
    github_calls = github.get_user_calls
    assert github_calls

    MemberValidator(members, Reporter()).validate()
    assert github.get_user_calls != github_calls
