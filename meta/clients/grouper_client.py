"""Grouper client."""

import os

import requests

from meta.logger import get_app_logger

GROUPER_URL = "https://grouper.andrew.cmu.edu/grouper-ws/servicesRest/v2_6_000"
GROUPER_USERNAME = "scottylabs-svc"
TIMEOUT_SECONDS = 30


def get_andrew_ids(group_name: str) -> set[str]:
    """Get the Andrew IDs of a group's members, including those of nested groups."""
    logger = get_app_logger()

    password = os.getenv("GROUPER_PASSWORD")
    if not password:
        msg = "GROUPER_PASSWORD is not set"
        logger.critical(msg)
        raise RuntimeError(msg)

    response = requests.post(
        f"{GROUPER_URL}/groups",
        auth=(GROUPER_USERNAME, password),
        json={
            "WsRestGetMembersRequest": {
                "wsGroupLookups": [{"groupName": group_name}],
                "memberFilter": "All",
            },
        },
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    result = response.json()["WsGetMembersResults"]["results"][0]
    if result["resultMetadata"]["success"] != "T":
        code = result["resultMetadata"]["resultCode"]
        msg = f"Failed to get the members of {group_name}: {code}"
        logger.critical(msg)
        raise RuntimeError(msg)

    # Nested groups are listed as members too, under the g:gsa source
    return {
        subject["id"].lower()
        for subject in result.get("wsSubjects", [])
        if subject["sourceId"] == "ldap"
    }
