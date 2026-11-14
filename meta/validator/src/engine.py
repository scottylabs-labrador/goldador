"""Shared in-process validation pipeline for local disk and remote TOML."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from meta.loaders.errors import GovernanceLoadError
from meta.loaders.members import load_members
from meta.loaders.teams import load_teams
from meta.validator.src.reporter import ErrorCode, Reporter, bind_reporter
from meta.validator.src.rules.members import MemberValidator
from meta.validator.src.rules.teams import TeamValidator

if TYPE_CHECKING:
    from collections.abc import Iterable


def run_validation(
    *,
    member_tomls: Iterable[tuple[str, str]] | None = None,
    team_tomls: Iterable[tuple[str, str]] | None = None,
    reporter: Reporter,
) -> dict[str, Any]:
    """Load members/teams and return structured validation results.

    When ``member_tomls`` / ``team_tomls`` are ``None``, loaders read
    ``members/*.toml`` and ``teams/*.toml`` from the current working directory.
    Errors already stored on ``reporter`` are included in the result.
    """
    record = bind_reporter(reporter)

    member_rows = list(member_tomls) if member_tomls is not None else None
    team_rows = list(team_tomls) if team_tomls is not None else None

    member_files = len(member_rows) if member_rows is not None else 0
    team_files = len(team_rows) if team_rows is not None else 0

    try:
        members = load_members(record, file_contents=member_rows)
        if member_rows is None:
            member_files = len(members)
        MemberValidator(members, reporter).validate()

        teams = load_teams(record, file_contents=team_rows)
        if team_rows is None:
            team_files = len(teams)
        TeamValidator(teams, members, reporter).validate()
    except GovernanceLoadError as e:
        reporter.insert_error(
            e.file_path,
            ErrorCode.GOVERNANCE_LOAD_ERROR,
            e.message,
        )

    return {
        "loaded": {
            "member_files": member_files,
            "team_files": team_files,
        },
        "validation": {"errors": reporter.as_result()["errors"]},
    }
