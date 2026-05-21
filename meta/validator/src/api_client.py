"""Lightweight HTTP client for the hosted validator API."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from typing import cast

DEFAULT_VALIDATOR_SERVER_URL = "https://goldador.scottylabs.org"
_VALIDATE_TIMEOUT_SECONDS = 600
_ERROR_BODY_LIMIT = 500
_CONNECT_TIMEOUT_SECONDS = 30
_HTTP_STATUS_MARKER = "\n__GOLDADOR_HTTP_STATUS__:"


class ValidatorApiError(RuntimeError):
    """Raised when the hosted validator API cannot return a usable response."""


def validate_ref_via_api(ref: str) -> Mapping[str, object]:
    """Validate ``ref`` using the hosted validator API."""
    base_url = os.environ.get("VALIDATOR_SERVER_URL", DEFAULT_VALIDATOR_SERVER_URL)
    url = f"{base_url.rstrip('/')}/validate"
    body = json.dumps({"ref": ref}).encode()
    output = _curl_post(url, body)
    response_body, status_code = _split_curl_response(output)
    if status_code != "200":
        msg = f"Validator returned HTTP {status_code}: {_error_detail(response_body)}"
        raise ValidatorApiError(msg)
    return _decode_response(response_body)


def _curl_post(url: str, body: bytes) -> bytes:
    curl = shutil.which("curl")
    if curl is None:
        msg = "curl is required to call the hosted validator API"
        raise ValidatorApiError(msg)

    command = [
        curl,
        "-sS",
        "--connect-timeout",
        str(_CONNECT_TIMEOUT_SECONDS),
        "--max-time",
        str(_VALIDATE_TIMEOUT_SECONDS),
        "-X",
        "POST",
        url,
        "-H",
        "Accept: application/json",
        "-H",
        "Content-Type: application/json",
        "--data-binary",
        "@-",
        "--write-out",
        f"{_HTTP_STATUS_MARKER}%{{http_code}}",
    ]
    result = subprocess.run(  # noqa: S603 - command is built from trusted literals.
        command,
        input=body,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        if not detail:
            detail = f"curl exited {result.returncode}"
        msg = f"Validator API request failed: {detail}"
        raise ValidatorApiError(msg)
    return result.stdout


def _split_curl_response(output: bytes) -> tuple[bytes, str]:
    try:
        body, status = output.rsplit(_HTTP_STATUS_MARKER.encode(), maxsplit=1)
    except ValueError as e:
        msg = "Validator API response is missing HTTP status"
        raise ValidatorApiError(msg) from e

    status_code = status.decode(errors="replace").strip()
    if not status_code.isdigit():
        msg = f"Validator API response has invalid HTTP status {status_code!r}"
        raise ValidatorApiError(msg)
    return body, status_code


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
