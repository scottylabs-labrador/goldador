"""Load team TOML files from disk or from ``(path, content)`` pairs."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from meta.loaders.errors import GovernanceLoadError
from meta.loaders.types import LoaderErrorCode
from meta.logger import get_app_logger
from meta.models import Repo, Team

from .key_ordering import KeyOrdering
from .sources import TomlGlobSource, iter_toml_file_sources

logger = get_app_logger()

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
        try:
            data: dict[str, Any] = tomllib.loads(content)
        except tomllib.TOMLDecodeError as e:
            message = str(e)
            logger.exception("Failed to parse TOML in %s", file_path)
            raise GovernanceLoadError(file_path, message) from e

        key_ordering.validate(file_path, data, LoaderErrorCode.TEAM_KEY_ORDERING)
        try:
            teams[Path(file_path).stem] = _load_team(file_path, data)
        except GovernanceLoadError:
            raise
        except ValidationError as e:
            message = str(e)
            logger.exception("Failed to validate team model in %s", file_path)
            raise GovernanceLoadError(file_path, message) from e

    return teams


def _load_team(file_path: str, data: dict[str, Any]) -> Team:
    """Parse one team TOML document."""
    try:
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
            "members": [
                str(member["github-username"]) for member in first["members"]
            ],
            "file_path": file_path,
        }
    except (IndexError, KeyError, TypeError) as e:
        message = f"malformed team structure: {e}"
        logger.exception("Failed to load team structure in %s", file_path)
        raise GovernanceLoadError(file_path, message) from e

    return Team.model_validate(payload)
