"""Tests for the validator HTTP server."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from meta.loaders.errors import GovernanceLoadError
from meta.validator.src import server

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def test_validate_maps_governance_load_error(monkeypatch: MonkeyPatch) -> None:
    """Governance load failures should return structured HTTP 502 responses."""
    file_path = "teams/bad.toml"
    error_message = "parse error"

    def fail(_ref: str) -> dict[str, object]:
        raise GovernanceLoadError(file_path, error_message)

    monkeypatch.setattr(server, "run_validation_for_ref", fail)
    client = TestClient(server.app)

    response = client.post("/validate", json={"ref": "abc123"})

    assert response.status_code == HTTPStatus.BAD_GATEWAY
    detail = response.json()["detail"]
    assert detail["file"] == file_path
    assert error_message in detail["error"]
    assert detail["ref"] == "abc123"


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
