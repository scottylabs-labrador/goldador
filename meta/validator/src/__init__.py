"""Validator package."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from meta.logger import get_app_logger
from meta.validator.src.reporter import Reporter

if TYPE_CHECKING:
    import logging

DEFAULT_VALIDATOR_SERVER_URL = "https://validator.goldador.scottylabs.org"
_VALIDATE_TIMEOUT_SECONDS = 600
_ERROR_BODY_LIMIT = 500
_CONNECT_TIMEOUT_SECONDS = 30


class ValidatorApiError(RuntimeError):
    """Raised when the hosted validator API cannot return a usable response."""


class _LoadedSummary(BaseModel):
    member_files: int
    team_files: int


class _ValidationLogContext(BaseModel):
    repository: str
    ref: str
    loaded: _LoadedSummary


def validate_ref_via_api(ref: str) -> Mapping[str, object]:
    """Validate ``ref`` using the hosted validator API."""
    base_url = os.environ.get("VALIDATOR_SERVER_URL", DEFAULT_VALIDATOR_SERVER_URL)
    url = f"{base_url.rstrip('/')}/validate"
    try:
        response = requests.post(
            url,
            json={"ref": ref},
            headers={"Accept": "application/json"},
            timeout=(_CONNECT_TIMEOUT_SECONDS, _VALIDATE_TIMEOUT_SECONDS),
        )
    except requests.RequestException as e:
        msg = f"Validator API request failed: {e}"
        raise ValidatorApiError(msg) from e

    if response.status_code != HTTPStatus.OK:
        msg = (
            f"Validator returned HTTP {response.status_code}: "
            f"{_error_detail(response.content)}"
        )
        raise ValidatorApiError(msg)
    return _decode_response(response.content)


def _decode_response(data: bytes) -> Mapping[str, object]:
    try:
        payload: object = json.loads(data.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        msg = "Validator API returned invalid JSON"
        raise ValidatorApiError(msg) from e

    if not isinstance(payload, Mapping):
        msg = "Validator API returned a non-object JSON response"
        raise ValidatorApiError(msg)
    return cast("Mapping[str, object]", payload)


def _error_detail(data: bytes) -> str:
    text = data.decode(errors="replace").strip()
    if not text:
        return "empty response body"
    try:
        payload: object = json.loads(text)
    except json.JSONDecodeError:
        return text[:_ERROR_BODY_LIMIT]

    if isinstance(payload, Mapping):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
        if isinstance(detail, Mapping):
            error = detail.get("error")
            if isinstance(error, str):
                return error
    return text[:_ERROR_BODY_LIMIT]


def main() -> None:
    """Validate governance TOML through the hosted validator API."""
    load_dotenv()
    logger = get_app_logger()
    ref = _cli_ref(sys.argv)

    try:
        payload = validate_ref_via_api(ref)
        validation = _validation_from_payload(payload)
        reporter = Reporter.from_result(validation)
        _log_validation_context(logger, payload)
    except (TypeError, ValidatorApiError, ValidationError, ValueError) as e:
        logger.critical("%s", e)
        raise SystemExit(1) from e

    reporter.emit()


def _cli_ref(argv: list[str]) -> str:
    """Parse the required Git ref argument from ``argv``."""
    # ``argv`` layout: script name, required Git ref.
    expected_argc = 2
    argc = len(argv)
    if argc == expected_argc:
        return argv[1]
    prog = argv[0] if argv else "validate"
    msg = f"usage: {prog} REF"
    raise SystemExit(msg)


def _validation_from_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    validation = payload.get("validation")
    if not isinstance(validation, Mapping):
        msg = "Validator API response is missing object 'validation'"
        raise TypeError(msg)
    return validation


def _log_validation_context(
    logger: logging.Logger,
    payload: Mapping[str, object],
) -> None:
    context = _ValidationLogContext.model_validate(payload)

    logger.info(
        "Validating %s @ %s (%s member files, %s team files)",
        context.repository,
        context.ref,
        context.loaded.member_files,
        context.loaded.team_files,
    )
