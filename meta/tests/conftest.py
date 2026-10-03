"""Shared test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from meta.validator.src.rules.verified_identities import clear_verified_identities

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def verified_identities_cache() -> Iterator[None]:
    """Clear cached GitHub usernames and Keycloak pairs around each test."""
    clear_verified_identities()
    yield
    clear_verified_identities()
