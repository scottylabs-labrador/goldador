"""Process-lifetime cache of member identities that already passed remote checks."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_verified_github_usernames: set[str] = set()
_verified_keycloak_pairs: set[tuple[str, str]] = set()


def _github_username_key(github_username: str) -> str:
    """Normalize a GitHub username the same way the mismatch check does."""
    return github_username.lower()


def github_username_verified(github_username: str) -> bool:
    """Return whether ``github_username`` already resolved to a GitHub user."""
    with _lock:
        return _github_username_key(github_username) in _verified_github_usernames


def remember_github_username(github_username: str) -> None:
    """Record that ``github_username`` resolved to a GitHub user."""
    with _lock:
        _verified_github_usernames.add(_github_username_key(github_username))


def keycloak_pair_verified(andrew_id: str, github_username: str) -> bool:
    """Return whether this Andrew ID and GitHub username already passed Keycloak."""
    key = (andrew_id, _github_username_key(github_username))
    with _lock:
        return key in _verified_keycloak_pairs


def remember_keycloak_pair(andrew_id: str, github_username: str) -> None:
    """Record a Keycloak check that found a matching GitHub link and a Slack id."""
    key = (andrew_id, _github_username_key(github_username))
    with _lock:
        _verified_keycloak_pairs.add(key)


def clear_verified_identities() -> None:
    """Drop every cached identity."""
    with _lock:
        _verified_github_usernames.clear()
        _verified_keycloak_pairs.clear()
