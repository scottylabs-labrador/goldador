"""Validator package."""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from meta.logger import get_app_logger
from meta.validator.src.github_utils import (
    GoldadorGitHubError,
    resolve_default_branch_head_sha,
)
from meta.validator.src.remote_validation import run_remote_validation
from meta.validator.src.rules.members import MemberValidationError
from meta.validator.src.rules.teams import TeamValidationError

# Exceptions that should be reported and turned into a non-zero exit instead of
# bubbling up as a traceback. Wider environment problems (``RuntimeError``) are
# included alongside per-domain validation failures.
_FATAL_ERRORS: tuple[type[Exception], ...] = (
    GoldadorGitHubError,
    MemberValidationError,
    TeamValidationError,
    RuntimeError,
)


def main() -> None:
    """Validate governance TOML from GitHub.

    With no arguments, validates the tip of the repository default branch.
    With one argument, validates that Git ref (branch name, tag, or commit SHA).
    """
    load_dotenv()
    logger = get_app_logger()
    ref = _cli_ref(sys.argv)

    try:
        reporter, extras = run_remote_validation(ref)
    except _FATAL_ERRORS as e:
        logger.critical("%s", e)
        raise SystemExit(1) from e

    logger.info(
        "Validating %s @ %s (%s member files, %s team files)",
        extras["repository"],
        extras["ref"],
        extras["loaded"]["member_files"],
        extras["loaded"]["team_files"],
    )
    reporter.emit()


def _cli_ref(argv: list[str]) -> str:
    """Parse the optional ref argument from ``argv``; default to the branch head."""
    # ``argv`` layout: script name, optional Git ref.
    expected_max_argc = 2
    argc = len(argv)
    if argc < expected_max_argc:
        return resolve_default_branch_head_sha()
    if argc == expected_max_argc:
        return argv[1]
    prog = argv[0] if argv else "validate"
    msg = f"usage: {prog} [REF]"
    raise SystemExit(msg)
