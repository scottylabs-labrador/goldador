"""Tests for the validator HTTP server."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from meta.clients.github_client import get_github_client
from meta.loaders.errors import GovernanceLoadError
from meta.loaders.types import LoaderErrorCode, RecordFn
from meta.validator.src import server
from meta.validator.src.github_utils import GitHubRateLimitError, GoldadorGitHubError

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def test_validate_maps_governance_load_error(monkeypatch: MonkeyPatch) -> None:
    """Governance load failures should return validation errors with HTTP 200."""
    file_path = "teams/bad.toml"
    error_message = "parse error"

    def fail(_ref: str) -> dict[str, object]:
        raise GovernanceLoadError(file_path, error_message)

    monkeypatch.setattr(server, "run_validation_for_ref", fail)
    client = TestClient(server.app)

    response = client.post("/validate", json={"ref": "abc123"})

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    errors = payload["validation"]["errors"]
    assert payload["ref"] == "abc123"
    assert payload["loaded"] == {"member_files": 0, "team_files": 0}
    assert file_path in errors
    assert errors[file_path][0]["code"] == "GOVERNANCE_LOAD_ERROR"
    assert error_message in errors[file_path][0]["message"]


def test_run_validation_for_ref_keeps_non_toml_errors(
    monkeypatch: MonkeyPatch,
) -> None:
    """Non-.toml directory entries must be returned as validation errors."""

    def fake_fetch(
        ref: str,
        *,
        record: RecordFn | None = None,
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        assert ref == "abc123"
        assert record is not None
        record(
            "members/faribahnuha",
            LoaderErrorCode.MEMBER_NOT_FILE,
            "Not a .toml file",
        )
        return [], []

    monkeypatch.setattr(server, "fetch_goldador_toml_at_ref", fake_fetch)

    result = server.run_validation_for_ref("abc123")

    errors = result["validation"]["errors"]
    assert errors["members/faribahnuha"] == [
        {"code": "MEMBER_NOT_FILE", "message": "Not a .toml file"},
    ]


def test_validate_maps_ref_not_found_to_404(monkeypatch: MonkeyPatch) -> None:
    """Ref-not-found should remain an HTTP error rather than validation data."""
    error_message = "missing ref"

    def fail(_ref: str) -> dict[str, object]:
        raise GoldadorGitHubError(error_message, status_code=404)

    monkeypatch.setattr(server, "run_validation_for_ref", fail)
    client = TestClient(server.app)

    response = client.post("/validate", json={"ref": "missing"})

    assert response.status_code == HTTPStatus.NOT_FOUND
    detail = response.json()["detail"]
    assert detail["ref"] == "missing"
    assert error_message in detail["error"]


def test_validate_maps_github_rate_limit_to_429(monkeypatch: MonkeyPatch) -> None:
    """GitHub rate limits should be returned to the caller as HTTP 429."""
    error_message = "GitHub API rate limit exceeded. Try again later."

    def fail(_ref: str) -> dict[str, object]:
        raise GitHubRateLimitError

    monkeypatch.setattr(server, "run_validation_for_ref", fail)
    client = TestClient(server.app)

    response = client.post("/validate", json={"ref": "abc123"})

    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    detail = response.json()["detail"]
    assert detail["ref"] == "abc123"
    assert detail["error"] == error_message


def test_github_client_does_not_retry(monkeypatch: MonkeyPatch) -> None:
    """The GitHub client must not sleep through rate-limit windows."""
    created: dict[str, object] = {}

    class FakeGithub:
        def __init__(self, *, auth: object, retry: object) -> None:
            created["auth"] = auth
            created["retry"] = retry

    monkeypatch.setenv("SYNC_GITHUB_TOKEN", "token")
    monkeypatch.setattr("meta.clients.github_client.Github", FakeGithub)
    get_github_client.cache_clear()
    try:
        get_github_client()
    finally:
        get_github_client.cache_clear()

    assert created["retry"] is None


def test_unhandled_exception_returns_500(
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
) -> None:
    """Unexpected server failures should stay opaque while logging stack traces."""

    class UnexpectedError(Exception):
        """Test-only failure type."""

    boom = "boom"

    def fail(_ref: str) -> dict[str, object]:
        raise UnexpectedError(boom)

    monkeypatch.setattr(server, "run_validation_for_ref", fail)
    client = TestClient(server.app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR):
        response = client.post("/validate", json={"ref": "abc123"})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Internal Server Error"
    assert any(
        "Unhandled validator error for /validate" in record.message
        for record in caplog.records
    )
