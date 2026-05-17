"""Load member and team TOML from the goldador GitHub repository at a ref."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from github import GithubException

from meta.clients.github_client import get_github_client

if TYPE_CHECKING:
    from github.Repository import Repository

# Canonical org/repo for governance data (must match the public goldador repo URL).
GOLDADOR_REPO_FULL_NAME = "scottylabs-labrador/goldador"

TomlFileRows = list[tuple[str, str]]


class GoldadorGitHubError(Exception):
    """Raised when goldador contents cannot be read from GitHub."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        """Store a message and optional HTTP status for API handlers."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def verify_ref(repo: Repository, ref: str) -> None:
    """Ensure ``ref`` resolves to a commit on ``repo``."""
    try:
        repo.get_commit(ref)
    except GithubException as e:
        if e.status == HTTPStatus.NOT_FOUND:
            msg = f"Ref {ref!r} not found in {GOLDADOR_REPO_FULL_NAME}"
            raise GoldadorGitHubError(msg, status_code=400) from e
        msg = f"GitHub API error: {e}"
        raise GoldadorGitHubError(msg, status_code=502) from e


def _list_toml_paths_and_contents(
    repo: Repository,
    directory: str,
    ref: str,
) -> list[tuple[str, str]]:
    """Return sorted ``(path, utf-8 text)`` pairs for ``*.toml`` under ``directory``."""
    try:
        entries = repo.get_contents(directory, ref=ref)
    except GithubException as e:
        if e.status == HTTPStatus.NOT_FOUND:
            return []
        msg = f"GitHub API error: {e}"
        raise GoldadorGitHubError(msg, status_code=502) from e

    if not isinstance(entries, list):
        entries = [entries]

    out: list[tuple[str, str]] = []
    for entry in entries:
        if entry.type != "file" or not str(entry.name).endswith(".toml"):
            continue
        cf = repo.get_contents(entry.path, ref=ref)
        if isinstance(cf, list):
            continue
        text = cf.decoded_content.decode("utf-8")
        out.append((cf.path, text))
    return sorted(out, key=lambda t: t[0])


def resolve_default_branch_head_sha() -> str:
    """Return the SHA of the latest commit on the repository default branch."""
    try:
        client = get_github_client()
        repo = client.get_repo(GOLDADOR_REPO_FULL_NAME)
        branch = repo.get_branch(repo.default_branch)
    except GithubException as e:
        msg = f"GitHub API error: {e}"
        raise GoldadorGitHubError(msg, status_code=502) from e

    return str(branch.commit.sha)


def fetch_goldador_toml_at_ref(ref: str) -> tuple[TomlFileRows, TomlFileRows]:
    """Return ``(member_tomls, team_tomls)`` as GitHub path and TOML text pairs."""
    client = get_github_client()
    repo = client.get_repo(GOLDADOR_REPO_FULL_NAME)
    verify_ref(repo, ref)
    member_rows = _list_toml_paths_and_contents(repo, "members", ref)
    team_rows = _list_toml_paths_and_contents(repo, "teams", ref)
    return member_rows, team_rows
