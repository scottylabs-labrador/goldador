"""Load team TOML files from disk or from ``(path, content)`` pairs."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from meta.loaders.types import LoaderErrorCode
from meta.models import Repo, Team

from .key_ordering import KeyOrdering
from .sources import TomlGlobSource, iter_toml_file_sources

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .types import RecordFn

TEAMS_GLOB = "teams/*.toml"
TEAM_SCHEMA_PATH = "meta/schemas/team.schema.json"
_TEAMS_GLOB_SOURCE = TomlGlobSource(
    repo_subdir="teams",
    not_file_code=LoaderErrorCode.TEAM_NOT_FILE,
    not_file_message="not a file",
)


def load_teams(
    record: RecordFn | None = None,
    teams_glob: str = TEAMS_GLOB,
    *,
    file_contents: Iterable[tuple[str, str]] | None = None,
) -> dict[str, Team]:
    """Load all team TOML files from disk or remote ``file_contents``."""
    teams: dict[str, Team] = {}
    key_ordering = KeyOrdering(TEAM_SCHEMA_PATH, record)
    for file_path, content in iter_toml_file_sources(
        record,
        teams_glob,
        glob_source=_TEAMS_GLOB_SOURCE,
        file_contents=file_contents,
    ):
        data: dict[str, Any] = tomllib.loads(content)
        key_ordering.validate(file_path, data, LoaderErrorCode.TEAM_KEY_ORDERING)
        team = _load_team(file_path, data)
        teams[Path(file_path).stem] = Team.model_validate(team)

    return teams


def _load_team(file_path: str, data: dict[str, Any]) -> Team:
    """Parse one team TOML document."""
    # The schema guarantees that there is at least one membership record.
    first = data.get("membership", [])[0]
    payload: dict[str, Any] = {
        "name": data["name"],
        "description": data["description"],
        "website": data.get("website"),
        "server": data.get("server"),
        "create_oidc_clients": data.get("create-oidc-clients", True),
        "repos": [Repo.model_validate(repo) for repo in data.get("repos", [])],
        "leads": [str(x) for x in first["leads"]],
        "members": [str(member["github-username"]) for member in first["members"]],
        "file_path": file_path,
    }
    return Team.model_validate(payload)
