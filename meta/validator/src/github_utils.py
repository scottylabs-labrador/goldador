"""Load member and team TOML from the goldador GitHub repository at a ref."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, NoReturn

from github import GithubException

from meta.clients.github_client import get_github_client
from meta.loaders.sources import TomlGlobSource
from meta.loaders.types import LoaderErrorCode

if TYPE_CHECKING:
    from github.Repository import Repository

    from meta.loaders.types import RecordFn

# Canonical org/repo for governance data (must match the public goldador repo URL).
GOLDADOR_REPO_FULL_NAME = "scottylabs-labrador/goldador"

TomlFileRows = list[tuple[str, str]]

_NOT_TOML_MESSAGE = "Not a .toml file"
_MEMBERS_GLOB_SOURCE = TomlGlobSource(
    repo_subdir="members",
    not_file_code=LoaderErrorCode.MEMBER_NOT_FILE,
    not_file_message="Not a file",
)
_TEAMS_GLOB_SOURCE = TomlGlobSource(
    repo_subdir="teams",
    not_file_code=LoaderErrorCode.TEAM_NOT_FILE,
    not_file_message="not a file",
)


class GoldadorGitHubError(Exception):
    """Raised when goldador contents cannot be read from GitHub."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        """Store a message and optional HTTP status for API handlers."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _raise_github_api_error(error: GithubException) -> NoReturn:
    """Wrap a ``GithubException`` as a 502-equivalent ``GoldadorGitHubError``."""
    msg = f"GitHub API error: {error}"
    raise GoldadorGitHubError(msg, status_code=502) from error


def verify_ref(repo: Repository, ref: str) -> None:
    """Ensure ``ref`` resolves to a commit on ``repo``."""
    try:
        repo.get_commit(ref)
    except GithubException as e:
        if e.status == HTTPStatus.NOT_FOUND:
            msg = f"Ref {ref!r} not found in {GOLDADOR_REPO_FULL_NAME}"
            raise GoldadorGitHubError(msg, status_code=404) from e
        _raise_github_api_error(e)


def _record_directory_entry_error(
    record: RecordFn | None,
    glob_source: TomlGlobSource,
    entry_name: str,
    message: str,
) -> None:
    if record is None:
        return
    path = f"{glob_source.repo_subdir}/{entry_name}"
    record(path, glob_source.not_file_code, message)


def _list_toml_paths_and_contents(
    repo: Repository,
    ref: str,
    *,
    glob_source: TomlGlobSource,
    record: RecordFn | None = None,
) -> TomlFileRows:
    """Return sorted ``(path, utf-8 text)`` pairs for ``*.toml`` under ``directory``."""
    directory = glob_source.repo_subdir
    try:
        entries = repo.get_contents(directory, ref=ref)
    except GithubException as e:
        if e.status == HTTPStatus.NOT_FOUND:
            return []
        _raise_github_api_error(e)

    if not isinstance(entries, list):
        entries = [entries]

    pairs: TomlFileRows = []
    for entry in entries:
        if entry.type != "file":
            _record_directory_entry_error(
                record,
                glob_source,
                entry.name,
                glob_source.not_file_message,
            )
            continue
        if not entry.name.endswith(".toml"):
            _record_directory_entry_error(
                record,
                glob_source,
                entry.name,
                _NOT_TOML_MESSAGE,
            )
            continue

        try:
            content_file = repo.get_contents(entry.path, ref=ref)
        except GithubException as e:
            _raise_github_api_error(e)

        if isinstance(content_file, list):
            _record_directory_entry_error(
                record,
                glob_source,
                entry.name,
                glob_source.not_file_message,
            )
            continue

        try:
            text = content_file.decoded_content.decode("utf-8")
        except UnicodeDecodeError as e:
            msg = f"File {entry.path!r} is not valid UTF-8"
            raise GoldadorGitHubError(msg, status_code=502) from e
        pairs.append((content_file.path, text))

    return sorted(pairs, key=lambda pair: pair[0])


def resolve_default_branch_head_sha() -> str:
    """Return the SHA of the latest commit on the repository default branch."""
    try:
        client = get_github_client()
        repo = client.get_repo(GOLDADOR_REPO_FULL_NAME)
        branch = repo.get_branch(repo.default_branch)
    except GithubException as e:
        _raise_github_api_error(e)

    return str(branch.commit.sha)


def fetch_goldador_toml_at_ref(
    ref: str,
    *,
    record: RecordFn | None = None,
) -> tuple[TomlFileRows, TomlFileRows]:
    """Return ``(member_tomls, team_tomls)`` as GitHub path and TOML text pairs."""
    client = get_github_client()
    repo = client.get_repo(GOLDADOR_REPO_FULL_NAME)
    verify_ref(repo, ref)
    member_rows = _list_toml_paths_and_contents(
        repo,
        ref,
        glob_source=_MEMBERS_GLOB_SOURCE,
        record=record,
    )
    team_rows = _list_toml_paths_and_contents(
        repo,
        ref,
        glob_source=_TEAMS_GLOB_SOURCE,
        record=record,
    )
    return member_rows, team_rows
