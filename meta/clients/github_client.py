"""GitHub client."""

import os
from functools import lru_cache
from http import HTTPStatus
from typing import TYPE_CHECKING

from github import Auth, Github, GithubException

from meta.logger import get_app_logger, log_operation

if TYPE_CHECKING:
    from github.Repository import Repository


REPO_NAME = "scottylabs-labrador/Goldador"


@lru_cache(maxsize=1)
def get_github_client() -> Github:
    """Get the Github client."""
    logger = get_app_logger()

    github_token = os.getenv("SYNC_GITHUB_TOKEN")
    if not github_token:
        msg = "SYNC_GITHUB_TOKEN is not set"
        logger.critical(msg)
        raise RuntimeError(msg)

    return Github(auth=Auth.Token(github_token))


def create_or_update_github_file(
    file_path: str,
    content: str,
    commit_message: str,
) -> None:
    """Create or update a file in the repository.

    Args:
        file_path: The path to the file in the repository.
        content: The content of the file.
        commit_message: The commit message for the file.

    Notes:
        If the file content is the same as the content to be created or updated,
        there is no operation performed.

    """
    logger = get_app_logger()
    repo = get_github_client().get_repo(REPO_NAME)
    current_content, sha = _get_github_file(repo, file_path)
    if current_content == content:
        msg = f"No changes to the {file_path} file. Skipping..."
        logger.debug(msg)
        return

    if sha:
        with log_operation(f"update the {file_path} file"):
            repo.update_file(file_path, commit_message, content, sha)
    else:
        with log_operation(f"create the {file_path} file"):
            repo.create_file(file_path, commit_message, content)


def _get_github_file(
    repo: Repository,
    file_path: str,
) -> tuple[str | None, str | None]:
    """Get the current file from the repository.

    Returns:
        tuple[str | None, str | None]: The current file content
        and the sha of the file. The sha is None if the file does not exist.

    """
    try:
        contents = repo.get_contents(file_path)
    except GithubException as e:
        if e.status == HTTPStatus.NOT_FOUND:
            return None, None
        raise

    if isinstance(contents, list):
        return None, None

    sha = contents.sha
    current_content = contents.decoded_content.decode("utf-8")
    return current_content, sha
