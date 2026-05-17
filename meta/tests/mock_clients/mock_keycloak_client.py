"""Mock Keycloak clients for validator tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class MockKeycloakClientValid:
    """Mock Keycloak client; optional per-Andrew GitHub and Slack overrides."""

    def __init__(
        self,
        *,
        github_username_by_andrew_id: dict[str, str] | None = None,
        slack_id_by_andrew_id: dict[str, str] | None = None,
    ) -> None:
        """Create a mock client.

        When lookups are omitted, GitHub login and Slack id default from Andrew ID
        (matches ``valid`` / ``alice`` tests where stem equals ``andrew-id``).
        """
        self._github_username_by_andrew_id = github_username_by_andrew_id
        self._slack_id_by_andrew_id = slack_id_by_andrew_id
        self._andrew_id_by_user_id: dict[str, str] = {}

    def get_user_id_by_username(self, andrew_id: str) -> str:
        """Pretend the user exists in Keycloak."""
        user_id = f"kc-user-{andrew_id}"
        self._andrew_id_by_user_id[user_id] = andrew_id
        return user_id

    def get_user_github_username(self, user_id: str) -> str | None:
        """Return the GitHub username Keycloak would report for federated login."""
        andrew_id = self._andrew_id_by_user_id.get(user_id)
        if andrew_id is None:
            return None
        if self._github_username_by_andrew_id is not None:
            return self._github_username_by_andrew_id.get(andrew_id)
        return andrew_id

    def get_user_slack_id(self, user_id: str) -> str | None:
        """Return a synthetic Slack member id for the Keycloak user."""
        andrew_id = self._andrew_id_by_user_id.get(user_id)
        if andrew_id is None:
            return None
        if self._slack_id_by_andrew_id is not None:
            return self._slack_id_by_andrew_id.get(andrew_id)
        return f"U-{andrew_id}"


class MockKeycloakClientUserNotFound:
    """Mock Keycloak client that reports no matching user."""

    def get_user_id_by_username(self, _username: str) -> str | None:
        """Return no user to emulate an unknown Andrew ID."""
        return None

    def get_user_github_username(self, _user_id: str) -> str | None:
        """Unused when the user does not exist; satisfy the client surface."""
        return None

    def get_user_slack_id(self, _user_id: str) -> str | None:
        """Unused when the user does not exist; satisfy the client surface."""
        return None


class MockKeycloakClientUnexpectedError:
    """Mock Keycloak client that always raises when resolving the user id."""

    def get_user_id_by_username(self, _username: str) -> str | None:
        """Raise a non-Keycloak-specific exception for the generic failure path."""
        msg = "unexpected keycloak client failure"
        raise RuntimeError(msg)

    def get_user_github_username(self, _user_id: str) -> str | None:
        """Unused when user lookup fails first."""
        return None

    def get_user_slack_id(self, _user_id: str) -> str | None:
        """Unused when user lookup fails first."""
        return None


class MockKeycloakClientMissingGithub:
    """User exists in Keycloak but has no GitHub identity provider link."""

    def get_user_id_by_username(self, andrew_id: str) -> str:
        """Pretend the user exists; ``get_user_github_username`` reports no link."""
        return f"kc-user-{andrew_id}"

    def get_user_github_username(self, _user_id: str) -> str | None:
        """Emulate a user with no GitHub federated identity."""
        return None

    def get_user_slack_id(self, _user_id: str) -> str | None:
        """Unused when GitHub validation fails first."""
        return None


class MockKeycloakClientMismatchedGithub:
    """User exists but Keycloak reports a different GitHub login."""

    def get_user_id_by_username(self, andrew_id: str) -> str:
        """Return a synthetic Keycloak user id."""
        return f"kc-user-{andrew_id}"

    def get_user_github_username(self, _user_id: str) -> str | None:
        """Return a login that will not match the member file stem."""
        return "someone-else"

    def get_user_slack_id(self, _user_id: str) -> str | None:
        """Unused when GitHub mismatch is reported first."""
        return None


class MockKeycloakClientMissingSlack:
    """GitHub link matches; Slack id is missing."""

    def __init__(self) -> None:
        """Initialize per-user id mapping for GitHub answers."""
        self._andrew_id_by_user_id: dict[str, str] = {}

    def get_user_id_by_username(self, andrew_id: str) -> str:
        """Return a synthetic Keycloak user id."""
        user_id = f"kc-user-{andrew_id}"
        self._andrew_id_by_user_id[user_id] = andrew_id
        return user_id

    def get_user_github_username(self, user_id: str) -> str | None:
        """Return the Andrew id as GitHub login (same as default fixture layout)."""
        return self._andrew_id_by_user_id.get(user_id)

    def get_user_slack_id(self, _user_id: str) -> str | None:
        """Emulate no Slack federated identity."""
        return None


type MockKeycloakClient = (
    MockKeycloakClientValid
    | MockKeycloakClientUserNotFound
    | MockKeycloakClientUnexpectedError
    | MockKeycloakClientMissingGithub
    | MockKeycloakClientMismatchedGithub
    | MockKeycloakClientMissingSlack
)


def make_get_keycloak_client(
    client: MockKeycloakClient,
) -> Callable[[], MockKeycloakClient]:
    """Return a ``get_keycloak_client``-compatible callable for monkeypatching."""

    def mock_get_keycloak_client() -> MockKeycloakClient:
        """Return the provided mock client."""
        return client

    return mock_get_keycloak_client
