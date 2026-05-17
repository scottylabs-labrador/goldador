"""Accumulate validation results and emit reports via logging."""

from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, TypedDict

from meta.logger import get_app_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from meta.loaders.types import LoaderErrorCode


class ErrorCode(Enum):
    """Validation error types."""

    MEMBER_NOT_FILE = "Member not a file"
    TEAM_NOT_FILE = "Team not a file"
    MEMBER_KEY_ORDERING = "Member key ordering is invalid"
    TEAM_KEY_ORDERING = "Team key ordering is invalid"
    LEAD_CROSS_REFERENCE = "Lead missing from members in a team"
    MEMBER_CROSS_REFERENCE = "A member in team missing from members/"
    INVALID_GITHUB_USERNAME = "Invalid GitHub username"
    INVALID_KEYCLOAK_USERNAME = "Invalid Keycloak username"
    MISSING_KEYCLOAK_GITHUB = "Missing GitHub username in Keycloak"
    MISMATCHED_KEYCLOAK_GITHUB = "Mismatched GitHub username in Keycloak"
    MISSING_KEYCLOAK_SLACK = "Missing Slack ID in Keycloak"
    GITHUB_REPO_NOT_FOUND = "GitHub repository not found"


class ValidationErrorEntry(TypedDict):
    """One reported error: machine-readable ``code`` plus human ``message``."""

    code: str
    message: str


class ValidationSummary(TypedDict):
    """Counts derived from the per-file error buckets."""

    files_with_errors: int
    error_count: int


class ValidationResult(TypedDict):
    """JSON-serializable validation report returned to API clients and the CLI."""

    valid: bool
    summary: ValidationSummary
    errors: dict[str, list[ValidationErrorEntry]]


class Reporter:
    """Collect validation errors and emit a structured report."""

    def __init__(self) -> None:
        """Initialize an empty per-file error bucket."""
        self.logger = get_app_logger()
        self._errors: defaultdict[str, list[tuple[ErrorCode, str]]] = defaultdict(list)

    def insert_error(self, file_path: str, error: ErrorCode, message: str) -> None:
        """Insert a validation error into the bucket for ``file_path``."""
        self._errors[file_path].append((error, message))

    def as_result(self) -> ValidationResult:
        """Serialize accumulated errors as JSON-friendly structures (no logging)."""
        errors_out: dict[str, list[ValidationErrorEntry]] = {
            file_path: [
                {"code": code.name, "message": message} for code, message in err_list
            ]
            for file_path, err_list in self._errors.items()
            if err_list
        }
        total_errors = sum(len(err_list) for err_list in errors_out.values())

        return {
            "valid": total_errors == 0,
            "summary": {
                "files_with_errors": len(errors_out),
                "error_count": total_errors,
            },
            "errors": errors_out,
        }

    def emit(self) -> None:
        """Log a summary of accumulated errors and exit non-zero if any were seen."""
        result = self.as_result()
        summary = result["summary"]
        invalid_files = summary["files_with_errors"]
        total_errors = summary["error_count"]

        self.logger.info("===== SUMMARY =====")
        self.logger.info("Invalid files: %s", invalid_files)
        self.logger.info("Total errors: %s", total_errors)

        if total_errors == 0:
            self.logger.success("Validation passed!")
            return

        self.logger.error("===== ERRORS =====")
        for file_path, errors in self._errors.items():
            if not errors:
                continue
            self.logger.error(file_path)
            for _, message in errors:
                self.logger.error("  - %s", message)

        self.logger.critical(
            "Validation failed with %s error(s) in %s file(s)",
            total_errors,
            invalid_files,
        )
        raise SystemExit(1)


def bind_reporter(reporter: Reporter) -> Callable[[str, LoaderErrorCode, str], None]:
    """Return a ``RecordFn``-compatible callback that writes into ``reporter``.

    ``LoaderErrorCode`` and ``ErrorCode`` share member names by convention so the
    loader-side codes map onto reporter-side codes by ``.name``.
    """

    def record(
        file_path: str,
        loader_error_code: LoaderErrorCode,
        message: str,
    ) -> None:
        try:
            error_code = ErrorCode[loader_error_code.name]
        except KeyError as e:
            msg = (
                f"No matching reporter ErrorCode for LoaderErrorCode "
                f"{loader_error_code.name!r}"
            )
            raise RuntimeError(msg) from e
        reporter.insert_error(file_path, error_code, message)

    return record
