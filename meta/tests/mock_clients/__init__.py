"""Mock client implementations for validator tests."""

from .mock_github_client import (
    MockGithubClientNotFound,
    MockGithubClientRateLimitExceeded,
    MockGithubClientServerError,
    MockGithubClientValid,
    make_get_github_client,
)
from .mock_keycloak_client import (
    MockKeycloakClientMismatchedGithub,
    MockKeycloakClientMissingGithub,
    MockKeycloakClientMissingSlack,
    MockKeycloakClientUnexpectedError,
    MockKeycloakClientUserNotFound,
    MockKeycloakClientValid,
    make_get_keycloak_client,
)

__all__ = [
    "MockGithubClientNotFound",
    "MockGithubClientRateLimitExceeded",
    "MockGithubClientServerError",
    "MockGithubClientValid",
    "MockKeycloakClientMismatchedGithub",
    "MockKeycloakClientMissingGithub",
    "MockKeycloakClientMissingSlack",
    "MockKeycloakClientUnexpectedError",
    "MockKeycloakClientUserNotFound",
    "MockKeycloakClientValid",
    "make_get_github_client",
    "make_get_keycloak_client",
]
