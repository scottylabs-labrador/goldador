"""Google Drive synchronizer.

All Labrador members are added to the Google Drive as contributors and
Labrador leadership are added to the Google Drive as content managers.

We make sure that each member has AT LEAST the permission they should have but
we don't demote them to a lower permission if they have a higher permission.
This is because some Labrador leadership are Content Managers while others are Managers,
"""

import os
from typing import ClassVar, Literal, override

from dotenv import load_dotenv
from google.oauth2 import service_account

# The type checking performance after installing the stubs is so bad it is faster to
# develope without them...
# https://github.com/henribru/google-api-python-client-stubs?tab=readme-ov-file#performance
from googleapiclient.discovery import build  # type: ignore[import-untyped]

from meta.logger import log_operation, print_section

from ._constants import LEADERSHIP
from .abstract import AbstractSynchronizer


class GoogleDriveSynchronizer(AbstractSynchronizer):
    """Google Drive synchronizer."""

    DRIVE_ROLE = Literal["writer", "fileOrganizer"]

    # Maps the Google API role to the Google Drive display name for logging.
    DRIVE_ROLE_TO_ROLE_NAME: ClassVar[dict[DRIVE_ROLE, str]] = {
        "writer": "contributor",
        "fileOrganizer": "content manager",
    }

    GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"  # noqa: S105

    def __init__(
        self,
    ) -> None:
        """Initialize the Google Drive synchronizer."""
        super().__init__()

        # Validate environment variables
        for env_var in [
            "GOOGLE_CLIENT_EMAIL",
            "GOOGLE_PRIVATE_KEY",
            "SCOTTYLABS_GOOGLE_DRIVE_ID",
        ]:
            if env_var not in os.environ:
                msg = f"Environment variable {env_var} is not set"
                self.logger.critical(msg)
                raise RuntimeError(msg)

        # Set the Google Drive ID
        self.google_drive_id = os.getenv("SCOTTYLABS_GOOGLE_DRIVE_ID")

        # Initialize the Google credentials
        creds = service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
            info={
                "private_key": os.getenv("GOOGLE_PRIVATE_KEY"),
                "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
                "token_uri": self.GOOGLE_TOKEN_URI,
            },
        )

        # Initialize the Google Drive service client
        self.service = build("drive", "v3", credentials=creds)

    @override
    def sync(self) -> None:
        print_section("Google Drive")
        permissions = self.get_all_permissions(self.service)
        new_member_email_addresses = self.get_new_member_email_addresses(permissions)
        new_admin_email_addresses = self.get_new_admin_email_addresses(permissions)
        new_non_admin_email_addresses = set(new_member_email_addresses) - set(
            new_admin_email_addresses,
        )
        self.add_permissions(list(new_non_admin_email_addresses), "writer")
        self.add_permissions(new_admin_email_addresses, "fileOrganizer")

    def get_all_permissions(self, service: build) -> dict[str, str]:
        """Return a email to role mapping for the ScottyLabs Google Drive."""
        permissions = {}
        page_token = None

        while True:
            response = (
                service.permissions()
                .list(
                    fileId=self.google_drive_id,
                    fields="nextPageToken, permissions(emailAddress,role)",
                    supportsAllDrives=True,
                    pageToken=page_token,
                )
                .execute()
            )

            for permission in response.get("permissions", []):
                email_address = permission["emailAddress"]
                role = permission["role"]
                permissions[email_address] = role

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return permissions

    def get_new_member_email_addresses(
        self,
        permissions: dict[str, str],
    ) -> list[str]:
        """Get the new member email addresses.

        The members are any members of the Labrador team.
        """
        new_email_addresses = []
        for contributor in self.members.values():
            if contributor.andrew_id is None:
                continue

            email_address = contributor.andrew_id + "@andrew.cmu.edu"
            if email_address not in permissions:
                new_email_addresses.append(email_address)

        return new_email_addresses

    def get_new_admin_email_addresses(
        self,
        permissions: dict[str, str],
    ) -> list[str]:
        """Get the new admin email addresses.

        The admins are the members of the Leadership team.
        """
        new_email_addresses = []
        for github_username in self.teams[LEADERSHIP].members:
            admin = self.members[github_username]
            if admin.andrew_id is None:
                continue

            email_address = admin.andrew_id + "@andrew.cmu.edu"

            # Permission of a maintainer needs to be at least File Organizer.
            # If an admin has "organizer" role, itmaps to Manager and has more
            # permissions and we will not demote them to a lower permission.
            if email_address not in permissions or (
                permissions[email_address] != "fileOrganizer"
                and permissions[email_address] != "organizer"
            ):
                new_email_addresses.append(email_address)

        return new_email_addresses

    def add_permissions(self, email_addresses: list[str], role: DRIVE_ROLE) -> None:
        """Create permissions for the given email addresses with the given role."""
        role_name = self.DRIVE_ROLE_TO_ROLE_NAME[role]

        # Log messages
        if len(email_addresses) == 0:
            self.logger.debug("Detected no new %s.\n", role_name)
            return

        self.logger.info("Detected %d new %s.\n", len(email_addresses), role_name)

        # Add permissions
        for email_address in email_addresses:
            with log_operation(
                f"add/update {email_address} as a ScottyLabs Google Drive {role_name}",
            ):
                self.service.permissions().create(
                    fileId=self.google_drive_id,
                    body={"type": "user", "role": role, "emailAddress": email_address},
                    supportsAllDrives=True,
                ).execute()


def main() -> None:
    """CLI entry point."""
    load_dotenv()
    google_drive_synchronizer = GoogleDriveSynchronizer()
    google_drive_synchronizer.sync()
