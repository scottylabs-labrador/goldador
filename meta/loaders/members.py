"""Load contributor TOML files from disk or from ``(path, content)`` pairs."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from meta.loaders.errors import GovernanceLoadError
from meta.loaders.types import LoaderErrorCode
from meta.logger import get_app_logger
from meta.models import Member

from .key_ordering import KeyOrdering
from .sources import TomlGlobSource, iter_toml_file_sources

logger = get_app_logger()

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .types import RecordFn

MEMBERS_GLOB = "members/*.toml"
MEMBER_SCHEMA_PATH = "meta/schemas/member.schema.json"
_MEMBERS_GLOB_SOURCE = TomlGlobSource(
    repo_subdir="members",
    not_file_code=LoaderErrorCode.MEMBER_NOT_FILE,
    not_file_message="Not a file",
)


def load_members(
    record: RecordFn | None = None,
    members_glob: str = MEMBERS_GLOB,
    *,
    file_contents: Iterable[tuple[str, str]] | None = None,
) -> dict[str, Member]:
    """Load all member TOML files from disk or remote ``file_contents``."""
    members: dict[str, Member] = {}
    key_ordering = KeyOrdering(MEMBER_SCHEMA_PATH, record)
    for file_path, content in iter_toml_file_sources(
        record,
        members_glob,
        glob_source=_MEMBERS_GLOB_SOURCE,
        file_contents=file_contents,
    ):
        try:
            data: dict[str, Any] = tomllib.loads(content)
        except tomllib.TOMLDecodeError as e:
            message = str(e)
            logger.exception("Failed to parse TOML in %s", file_path)
            raise GovernanceLoadError(file_path, message) from e

        key_ordering.validate(file_path, data, LoaderErrorCode.MEMBER_KEY_ORDERING)
        data["file_path"] = file_path
        try:
            members[Path(file_path).stem] = Member.model_validate(data)
        except ValidationError as e:
            message = str(e)
            logger.exception("Failed to validate member model in %s", file_path)
            raise GovernanceLoadError(file_path, message) from e

    return members
