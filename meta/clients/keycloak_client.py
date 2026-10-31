"""Keycloak client."""

import os
from functools import lru_cache
from typing import cast

from keycloak import KeycloakAdmin

from meta.logger import get_app_logger


@lru_cache(maxsize=1)
def get_keycloak_client() -> KeycloakClient:
    """Get the Keycloak client. Cache the result for reuse across the app."""
    return KeycloakClient()


class KeycloakClient:
    """Keycloak client."""

    def __init__(self) -> None:
        """Create a Keycloak client."""
        self.logger = get_app_logger()

        server_url = os.getenv("KEYCLOAK_SERVER_URL")
        if not server_url:
            msg = "KEYCLOAK_SERVER_URL is not set"
            self.logger.critical(msg)
            raise RuntimeError(msg)

        client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
        if not client_secret:
            msg = "KEYCLOAK_CLIENT_SECRET is not set"
            self.logger.critical(msg)
            raise RuntimeError(msg)

        realm_name = os.getenv("KEYCLOAK_REALM")
        if not realm_name:
            msg = "KEYCLOAK_REALM is not set"
            self.logger.critical(msg)
            raise RuntimeError(msg)

        client_id = os.getenv("KEYCLOAK_CLIENT_ID")
        if not client_id:
            msg = "KEYCLOAK_CLIENT_ID is not set"
            self.logger.critical(msg)
            raise RuntimeError(msg)

        self.keycloak_admin = KeycloakAdmin(
            server_url=server_url,
            realm_name=realm_name,
            client_id=client_id,
            client_secret_key=client_secret,
            verify=True,
        )

    def get_user_id_by_username(self, username: str) -> str | None:
        """Get the Keycloak user ID by username."""
        users = self.keycloak_admin.get_users(
            query={"username": username, "exact": True},
        )

        if not users:
            return None

        # Used `exact` = True, so we should only have one user.
        return cast("str | None", users[0]["id"])

    def get_user_github_username(self, user_id: str) -> str | None:
        """Get the GitHub username by Keycloak user ID."""
        social_logins = self.keycloak_admin.get_user_social_logins(user_id=user_id)
        if not social_logins:
            return None

        for login in social_logins:
            if login["identityProvider"] == "github":
                return cast("str", login["userName"])

        return None

    def get_user_slack_id(self, user_id: str) -> str | None:
        """Get the Slack ID by Keycloak user ID."""
        social_logins = self.keycloak_admin.get_user_social_logins(user_id=user_id)
        if not social_logins:
            return None

        for login in social_logins:
            if login["identityProvider"] == "slack":
                return cast("str", login["userId"])

        return None
