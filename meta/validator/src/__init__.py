"""Validator package."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from http import HTTPStatus
from typing import cast

import requests
from dotenv import load_dotenv
from pydantic import ValidationError

from meta.logger import get_app_logger
from meta.validator.src.reporter import Reporter

DEFAULT_VALIDATOR_SERVER_URL = "https://validator.goldador.scottylabs.org"
_VALIDATE_TIMEOUT_SECONDS = 600
_ERROR_BODY_LIMIT = 500
_CONNECT_TIMEOUT_SECONDS = 30


class ValidatorApiError(RuntimeError):
    """Raised when the hosted validator API cannot return a usable response."""


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
    """Validate governance TOML locally or through the hosted validator API.

    With no arguments, validates ``members/`` and ``teams/`` on disk. With a
    Git ref argument, posts to the hosted validator API.
    """
    parser = argparse.ArgumentParser(
        prog="validate",
        description=(
            "Validate governance TOML locally (no REF) or via the hosted "
            "validator API (with REF)."
        ),
    )
    parser.add_argument(
        "ref",
        nargs="?",
        help="Git ref to validate via the hosted API; omit to validate local disk",
    )
    args = parser.parse_args()
    ref: str | None = args.ref

    load_dotenv()
    logger = get_app_logger()

    try:
        if ref is None:
            # Local mode needs validator extras (PyGithub, Keycloak); keep these
            # imports lazy so ``validate REF`` stays usable with base deps only.
            from meta.validator.src.engine import (  # noqa: PLC0415
                run_validation,
            )
            from meta.validator.src.github_utils import (  # noqa: PLC0415
                GitHubRateLimitError,
            )
            from meta.validator.src.rules.members import (  # noqa: PLC0415
                MemberValidationError,
            )
            from meta.validator.src.rules.teams import (  # noqa: PLC0415
                TeamValidationError,
            )

            try:
                payload: Mapping[str, object] = run_validation(reporter=Reporter())
            except (
                GitHubRateLimitError,
                MemberValidationError,
                TeamValidationError,
            ) as e:
                logger.critical("%s", e)
                raise SystemExit(1) from e
        else:
            payload = validate_ref_via_api(ref)

        validation = payload.get("validation")
        if not isinstance(validation, Mapping):
            logger.critical(
                "Validator API response is missing object 'validation'",
            )
            raise SystemExit(1)

        reporter = Reporter.from_result(validation)
        loaded = payload.get("loaded")
        if not isinstance(loaded, Mapping):
            logger.critical("Validation response is missing object 'loaded'")
            raise SystemExit(1)
        if ref is None:
            target = "local disk"
        else:
            target = f"{payload['repository']} @ {payload['ref']}"
        logger.info(
            "Validating %s (%s member files, %s team files)",
            target,
            loaded.get("member_files"),
            loaded.get("team_files"),
        )
    except (
        TypeError,
        ValidatorApiError,
        ValidationError,
        ValueError,
    ) as e:
        logger.critical("%s", e)
        raise SystemExit(1) from e

    reporter.emit()
