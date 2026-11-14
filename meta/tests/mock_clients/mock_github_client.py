"""Mock GitHub clients for validator tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from github import GithubException, RateLimitExceededException

if TYPE_CHECKING:
    from collections.abc import Callable


class MockGithubClientValid:
    """Mock GitHub client that treats all users and repos as valid."""

    def get_user(self, _github_username: str) -> None:
        """Pretend the looked up GitHub user exists."""
        return

    def get_repo(self, _repo_name: str) -> None:
        """Pretend the looked up repository exists."""
        return


class MockGithubClientNotFound:
    """Mock GitHub client that always raises not-found."""

    def get_user(self, _github_username: str) -> None:
        """Raise a not-found response to emulate invalid users."""
        raise GithubException(status=404, data={"message": "Not Found"})

    def get_repo(self, _repo_name: str) -> None:
        """Raise a not-found response to emulate a missing repository."""
        raise GithubException(status=404, data={"message": "Not Found"})


class MockGithubClientRateLimitExceeded:
    """Mock GitHub client that always raises rate-limit exceeded."""

    def get_user(self, _github_username: str) -> None:
        """Raise a GitHub rate-limit response."""
        raise RateLimitExceededException(
            status=403,
            data={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-remaining": "0"},
        )

    def get_repo(self, _repo_name: str) -> None:
        """Raise a GitHub rate-limit response for repository reads."""
        raise RateLimitExceededException(
            status=403,
            data={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-remaining": "0"},
        )


class MockGithubClientServerError:
    """Mock GitHub client that always raises a non-rate-limit server error."""

    def get_user(self, _github_username: str) -> None:
        """Raise a GitHub server error."""
        raise GithubException(status=500, data={"message": "Server Error"})

    def get_repo(self, _repo_name: str) -> None:
        """Raise a GitHub server error for repository reads."""
        raise GithubException(status=500, data={"message": "Server Error"})


type MockGithubClient = (
    MockGithubClientValid
    | MockGithubClientNotFound
    | MockGithubClientRateLimitExceeded
    | MockGithubClientServerError
)


def make_get_github_client(
    client: MockGithubClient,
) -> Callable[[], MockGithubClient]:
    """Return a ``get_github_client``-compatible callable for monkeypatching."""

    def mock_get_github_client() -> MockGithubClient:
        """Return the provided mock client."""
        return client

    return mock_get_github_client
