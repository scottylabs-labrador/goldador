"""Collect TOML ``(path, utf-8 text)`` rows from disk globs or caller-supplied pairs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .types import LoaderErrorCode, RecordFn


@dataclass(frozen=True, slots=True)
class TomlGlobSource:
    """How to read TOML files from disk when ``file_contents`` is not provided."""

    repo_subdir: str
    not_file_code: LoaderErrorCode
    not_file_message: str


def iter_toml_file_sources(
    record: RecordFn | None,
    path_glob: str,
    *,
    glob_source: TomlGlobSource,
    file_contents: Iterable[tuple[str, str]] | None,
) -> list[tuple[str, str]]:
    """Return sorted ``(file_path, content)`` for a glob or for ``file_contents``."""
    if file_contents is not None:
        return sorted(file_contents, key=lambda t: t[0])

    rows: list[tuple[str, str]] = []
    for path in sorted(Path().glob(path_glob), key=lambda p: p.as_posix()):
        if not path.is_file():
            if record is not None:
                code = glob_source.not_file_code
                msg = glob_source.not_file_message
                record(path.name, code, msg)
            continue
        prefix = glob_source.repo_subdir
        rows.append((f"{prefix}/{path.name}", path.read_text(encoding="utf-8")))
    return rows
