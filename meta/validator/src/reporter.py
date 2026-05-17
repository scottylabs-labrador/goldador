"""Accumulate validation results and emit reports via logging."""

from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, cast

from meta.loaders.types import LoaderErrorCode
from meta.logger import get_app_logger

if TYPE_CHECKING:
    from collections.abc import Callable


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


class Reporter:
    """Collects validation errors and emits a report."""

    def __init__(
        self,
    ) -> None:
        """Initialize file buckets for members and teams."""
        self.logger = get_app_logger()
        self._errors: defaultdict[str, list[tuple[ErrorCode, str]]] = defaultdict(
            list,
        )

    def insert_error(self, file_path: str, error: ErrorCode, message: str) -> None:
        """Insert a validation error into the per-file bucket."""
        self._errors[file_path].append((error, message))

    def as_result(self) -> dict[str, object]:
        """Serialize accumulated errors as JSON-friendly structures (no logging)."""
        errors_out: dict[str, list[dict[str, str]]] = {}
        for file_path, err_list in self._errors.items():
            if not err_list:
                continue
            errors_out[file_path] = [
                {"code": code.name, "message": message} for code, message in err_list
            ]

        total_errors = sum(len(errors) for errors in self._errors.values())
        files_with_errors = sum(1 for errors in self._errors.values() if errors)

        return {
            "valid": total_errors == 0,
            "summary": {
                "files_with_errors": files_with_errors,
                "error_count": total_errors,
            },
            "errors": errors_out,
        }

    def emit(self) -> None:
        """Log the report and return whether the run is valid."""
        result = self.as_result()
        summary = cast("dict[str, int]", result["summary"])
        invalid_files = summary["files_with_errors"]
        total_errors = summary["error_count"]

        self.logger.info("===== SUMMARY =====")
        self.logger.info("Invalid files: %s", invalid_files)
        self.logger.info("Total errors: %s", total_errors)

        if total_errors > 0:
            self.logger.error("===== ERRORS =====")
            for file_path, errors in self._errors.items():
                if not errors:
                    continue
                self.logger.error(file_path)
                for error in errors:
                    self.logger.error("  - %s", error[1])

            self.logger.critical(
                "Validation failed with %s error(s) in %s file(s)",
                total_errors,
                invalid_files,
            )
            raise SystemExit(1)

        self.logger.success("Validation passed!")


def bind_reporter(reporter: Reporter) -> Callable[[str, LoaderErrorCode, str], None]:
    """Return a ``RecordFn``-compatible callback backed by ``reporter``."""

    def record(
        file_path: str,
        loader_error_code: LoaderErrorCode,
        message: str,
    ) -> None:
        match loader_error_code:
            case LoaderErrorCode.MEMBER_NOT_FILE:
                error_code = ErrorCode.MEMBER_NOT_FILE
            case LoaderErrorCode.MEMBER_KEY_ORDERING:
                error_code = ErrorCode.MEMBER_KEY_ORDERING
            case LoaderErrorCode.TEAM_NOT_FILE:
                error_code = ErrorCode.TEAM_NOT_FILE
            case LoaderErrorCode.TEAM_KEY_ORDERING:
                error_code = ErrorCode.TEAM_KEY_ORDERING
        reporter.insert_error(file_path, error_code, message)

    return record
