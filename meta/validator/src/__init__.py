"""Validator package."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from meta.logger import get_app_logger
from meta.validator.src.api_client import ValidatorApiError, validate_ref_via_api
from meta.validator.src.reporter import Reporter

if TYPE_CHECKING:
    import logging


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
    except (TypeError, ValidatorApiError, ValueError) as e:
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
    loaded = payload.get("loaded")
    if not isinstance(loaded, Mapping):
        msg = "Validator API response is missing object 'loaded'"
        raise TypeError(msg)

    logger.info(
        "Validating %s @ %s (%s member files, %s team files)",
        _string_field(payload, "repository"),
        _string_field(payload, "ref"),
        _int_field(loaded, "member_files"),
        _int_field(loaded, "team_files"),
    )


def _string_field(payload: Mapping[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str):
        msg = f"Validator API response field {field!r} must be a string"
        raise TypeError(msg)
    return value


def _int_field(payload: Mapping[str, object], field: str) -> int:
    value = payload.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        msg = f"Validator API response field {field!r} must be an integer"
        raise TypeError(msg)
    return value
