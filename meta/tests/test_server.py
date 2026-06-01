"""Tests for the validator HTTP server."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from meta.loaders.errors import GovernanceLoadError
from meta.validator.src import server
from meta.validator.src.github_utils import GoldadorGitHubError

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
