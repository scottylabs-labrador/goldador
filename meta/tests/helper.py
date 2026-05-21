"""Helper functions for tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meta.validator.src.reporter import ErrorCode, Reporter


def no_errors(reporter: Reporter) -> bool:
    """Validate if there are no errors in the reporter."""
    return len(reporter._errors) == 0  # noqa: SLF001


def has_error(reporter: Reporter, error_code: ErrorCode) -> bool:
    """Validate if an error is present in the reporter."""
    return any(
        error_code == error[0]
        for errors in reporter._errors.values()  # noqa: SLF001
        for error in errors
    )
