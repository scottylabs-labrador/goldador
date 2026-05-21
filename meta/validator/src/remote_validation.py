"""Run member/team rule validation against TOML fetched from GitHub."""

from __future__ import annotations

from typing import Any

from meta.loaders.members import load_members
from meta.loaders.teams import load_teams
from meta.validator.src.github_utils import (
    GOLDADOR_REPO_FULL_NAME,
    fetch_goldador_toml_at_ref,
)
from meta.validator.src.reporter import Reporter, bind_reporter
from meta.validator.src.rules.members import MemberValidator
from meta.validator.src.rules.teams import TeamValidator


def run_remote_validation(ref: str) -> tuple[Reporter, dict[str, Any]]:
    """Load TOML at ``ref`` from GitHub, run validators, return reporter + metadata."""
    reporter = Reporter()
    record = bind_reporter(reporter)
    member_tomls, team_tomls = fetch_goldador_toml_at_ref(ref)
    members = load_members(record, file_contents=member_tomls)
    MemberValidator(members, reporter).validate()

    teams = load_teams(record, file_contents=team_tomls)
    TeamValidator(teams, members, reporter).validate()

    extras: dict[str, Any] = {
        "repository": GOLDADOR_REPO_FULL_NAME,
        "ref": ref,
        "loaded": {
            "member_files": len(member_tomls),
            "team_files": len(team_tomls),
        },
    }
    return reporter, extras
