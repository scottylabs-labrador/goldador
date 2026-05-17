"""Lightweight HTTP client for the hosted validator API."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_VALIDATOR_SERVER_URL = "https://goldador.scottylabs.org"
_VALIDATE_TIMEOUT_SECONDS = 600
_ERROR_BODY_LIMIT = 500


class ValidatorApiError(RuntimeError):
    """Raised when the hosted validator API cannot return a usable response."""


def validate_ref_via_api(ref: str) -> Mapping[str, object]:
    """Validate ``ref`` using the hosted validator API."""
    base_url = os.environ.get("VALIDATOR_SERVER_URL", DEFAULT_VALIDATOR_SERVER_URL)
    url = f"{base_url.rstrip('/')}/validate"
    body = json.dumps({"ref": ref}).encode()
    request = Request(  # noqa: S310 - URL is project-controlled or env-configured.
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=_VALIDATE_TIMEOUT_SECONDS) as response:  # noqa: S310
            return _decode_response(response.read())
    except HTTPError as e:
        detail = _error_detail(e.read())
        msg = f"Validator returned HTTP {e.code}: {detail}"
        raise ValidatorApiError(msg) from e
    except (OSError, URLError) as e:
        msg = f"Validator API request failed: {e}"
        raise ValidatorApiError(msg) from e


def _decode_response(data: bytes) -> Mapping[str, object]:
    try:
        payload: object = json.loads(data.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        msg = "Validator API returned invalid JSON"
        raise ValidatorApiError(msg) from e

    if not isinstance(payload, Mapping):
        msg = "Validator API returned a non-object JSON response"
        raise ValidatorApiError(msg)
    return cast("Mapping[str, object]", payload)


def _error_detail(data: bytes) -> str:
    text = data.decode(errors="replace").strip()
    if not text:
        return "empty response body"
    try:
        payload: object = json.loads(text)
    except json.JSONDecodeError:
        return text[:_ERROR_BODY_LIMIT]

    if isinstance(payload, Mapping):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
        if isinstance(detail, Mapping):
            error = detail.get("error")
            if isinstance(error, str):
                return error
    return text[:_ERROR_BODY_LIMIT]
