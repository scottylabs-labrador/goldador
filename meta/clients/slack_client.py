"""Slack client."""

import os
import ssl
import sys

import certifi
from slack_sdk import WebClient

from meta.logger import get_app_logger


def get_slack_client(env_var_name: str) -> WebClient:
    """Get the Slack client."""
    logger = get_app_logger()

    slack_token = os.getenv(env_var_name)
    if not slack_token:
        msg = f"{env_var_name} is not set"
        logger.critical(msg)
        sys.exit(1)

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    return WebClient(token=slack_token, ssl=ssl_context)
