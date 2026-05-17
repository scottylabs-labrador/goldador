"""Test the member validator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from meta.loaders.members import load_members
from meta.validator.src.reporter import ErrorCode, Reporter, bind_reporter
from meta.validator.src.rules.members import MemberValidationError, MemberValidator

from .helper import has_error, no_errors
from .mock_clients.mock_github_client import (
    MockGithubClientNotFound,
    MockGithubClientRateLimitExceeded,
    MockGithubClientValid,
    make_get_github_client,
)
from .mock_clients.mock_keycloak_client import (
    MockKeycloakClientGithubUnexpectedError,
    MockKeycloakClientMismatchedGithub,
    MockKeycloakClientMissingGithub,
    MockKeycloakClientMissingSlack,
    MockKeycloakClientSlackUnexpectedError,
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


def test_member_github_username_match_is_case_insensitive(
    monkeypatch: MonkeyPatch,
) -> None:
    """Keycloak GitHub login may differ in case from the members file stem."""
    reporter = Reporter()
    members = load_members(bind_reporter(reporter), "meta/tests/members/valid.toml")
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientValid(
        github_username_by_andrew_id={"valid": "VaLiD"},
    )
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

    with pytest.raises(MemberValidationError):
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


def test_unexpected_keycloak_github_link_error_raises(
    monkeypatch: MonkeyPatch,
) -> None:
    """Errors while reading GitHub from Keycloak should abort validation."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientGithubUnexpectedError()
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


def test_unexpected_keycloak_slack_link_error_raises(
    monkeypatch: MonkeyPatch,
) -> None:
    """Errors while reading Slack from Keycloak should abort validation."""
    reporter = Reporter()
    members = load_members(
        bind_reporter(reporter),
        "meta/tests/members/for_teams/alice.toml",
    )
    assert no_errors(reporter)

    mock_github = MockGithubClientValid()
    mock_keycloak = MockKeycloakClientSlackUnexpectedError()
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
