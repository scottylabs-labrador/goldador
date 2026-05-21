"""Types shared by loaders."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum


class LoaderErrorCode(Enum):
    """Error code names."""

    MEMBER_NOT_FILE = "MEMBER_NOT_FILE"
    MEMBER_KEY_ORDERING = "MEMBER_KEY_ORDERING"
    TEAM_NOT_FILE = "TEAM_NOT_FILE"
    TEAM_KEY_ORDERING = "TEAM_KEY_ORDERING"


# (file_path, error_code_name, message). ``error_code_name`` must match an
# ``ErrorCode`` enum member name (e.g. ``"MEMBER_KEY_ORDERING"``).
RecordFn = Callable[[str, LoaderErrorCode, str], None]
