"""Load member and team TOML from the goldador GitHub repository at a ref."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, NoReturn

from github import GithubException, RateLimitExceededException

from meta.clients.github_client import get_github_client
from meta.loaders.sources import TomlGlobSource
from meta.loaders.types import LoaderErrorCode

if TYPE_CHECKING:
    from github.ContentFile import ContentFile
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


class GitHubRateLimitError(GoldadorGitHubError):
    """Raised when GitHub rejects a request because a rate limit was exceeded."""

    def __init__(self) -> None:
        """Report a GitHub rate limit with HTTP 429 for API callers."""
        msg = "GitHub API rate limit exceeded. Try again later."
        super().__init__(msg, status_code=HTTPStatus.TOO_MANY_REQUESTS)


def _raise_github_api_error(error: GithubException) -> NoReturn:
    """Wrap a ``GithubException`` as a 502-equivalent ``GoldadorGitHubError``."""
    msg = f"GitHub API error: {error}"
    raise GoldadorGitHubError(msg, status_code=502) from error


def verify_ref(repo: Repository, ref: str) -> None:
    """Ensure ``ref`` resolves to a commit on ``repo``."""
    try:
        repo.get_commit(ref)
    except RateLimitExceededException as e:
        raise GitHubRateLimitError from e
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


def _toml_row_for_entry(
    repo: Repository,
    ref: str,
    entry: ContentFile,
    glob_source: TomlGlobSource,
    record: RecordFn | None,
) -> tuple[str, str] | None:
    """Return one TOML row, or ``None`` when ``entry`` is not a TOML file."""
    if entry.type != "file":
        _record_directory_entry_error(
            record,
            glob_source,
            entry.name,
            glob_source.not_file_message,
        )
        return None
    if not entry.name.endswith(".toml"):
        _record_directory_entry_error(
            record,
            glob_source,
            entry.name,
            _NOT_TOML_MESSAGE,
        )
        return None

    try:
        content_file = repo.get_contents(entry.path, ref=ref)
    except RateLimitExceededException as e:
        raise GitHubRateLimitError from e
    except GithubException as e:
        _raise_github_api_error(e)

    if isinstance(content_file, list):
        _record_directory_entry_error(
            record,
            glob_source,
            entry.name,
            glob_source.not_file_message,
        )
        return None

    try:
        text = content_file.decoded_content.decode("utf-8")
    except UnicodeDecodeError as e:
        msg = f"File {entry.path!r} is not valid UTF-8"
        raise GoldadorGitHubError(msg, status_code=502) from e
    return content_file.path, text


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
    except RateLimitExceededException as e:
        raise GitHubRateLimitError from e
    except GithubException as e:
        if e.status == HTTPStatus.NOT_FOUND:
            return []
        _raise_github_api_error(e)

    if not isinstance(entries, list):
        entries = [entries]

    pairs: TomlFileRows = []
    for entry in entries:
        row = _toml_row_for_entry(repo, ref, entry, glob_source, record)
        if row is not None:
            pairs.append(row)

    return sorted(pairs, key=lambda pair: pair[0])


def resolve_default_branch_head_sha() -> str:
    """Return the SHA of the latest commit on the repository default branch."""
    try:
        client = get_github_client()
        repo = client.get_repo(GOLDADOR_REPO_FULL_NAME)
        branch = repo.get_branch(repo.default_branch)
    except RateLimitExceededException as e:
        raise GitHubRateLimitError from e
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
    try:
        repo = client.get_repo(GOLDADOR_REPO_FULL_NAME)
    except RateLimitExceededException as e:
        raise GitHubRateLimitError from e
    except GithubException as e:
        _raise_github_api_error(e)
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
