"""HTTP API for running goldador validation against a remote Git ref."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request  # noqa: TC002
from starlette.responses import JSONResponse, Response

from meta.loaders.errors import GovernanceLoadError
from meta.loaders.members import load_members
from meta.loaders.teams import load_teams
from meta.logger import get_app_logger
from meta.validator.src.github_utils import (
    GOLDADOR_REPO_FULL_NAME,
    GoldadorGitHubError,
    fetch_goldador_toml_at_ref,
)
from meta.validator.src.reporter import ErrorCode, Reporter, bind_reporter
from meta.validator.src.rules.members import MemberValidationError, MemberValidator
from meta.validator.src.rules.teams import TeamValidationError, TeamValidator

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Mapping
else:
    from collections.abc import Mapping

# Load environment up-front so the module-level rate-limit reads below see
# values from ``.env``. ``lifespan`` re-loads at request time for ``--reload``
# scenarios where the file may have changed since import.
load_dotenv()

# Git ref names are bounded well below this in practice; the cap exists to
# defend against accidental or malicious payloads pinned to the request body.
_REF_MAX_LENGTH = 260
_DEFAULT_VALIDATE_RATE_LIMIT = "60/minute"
# Maps validation/environment failures to the HTTP status used in the response
# body. ``GoldadorGitHubError`` carries its own status when available.
_FALLBACK_STATUS_CODE = 502
_STATUS_CODE_BY_EXCEPTION: dict[type[Exception], int] = {
    MemberValidationError: 502,
    TeamValidationError: 502,
}

logger = get_app_logger()


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


_RATE_LIMIT_VALIDATE = (
    os.environ.get(
        "VALIDATOR_VALIDATE_RATE_LIMIT",
        _DEFAULT_VALIDATE_RATE_LIMIT,
    ).strip()
    or _DEFAULT_VALIDATE_RATE_LIMIT
)
_RATE_LIMIT_USE_X_FORWARDED_FOR = _truthy_env(
    "VALIDATOR_RATE_LIMIT_USE_X_FORWARDED_FOR",
)
_RATE_LIMIT_DISABLED = _truthy_env("VALIDATOR_RATE_LIMIT_DISABLED")


def rate_limit_client_id(request: Request) -> str:
    """Client id for rate limits (optional X-Forwarded-For via env toggle)."""
    if _RATE_LIMIT_USE_X_FORWARDED_FOR:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            first = forwarded.split(",")[0].strip()
            if first:
                return first
    return get_remote_address(request)


limiter = Limiter(
    key_func=rate_limit_client_id,
    headers_enabled=True,
    enabled=not _RATE_LIMIT_DISABLED,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Load environment before handling requests."""
    load_dotenv()
    yield


app = FastAPI(title="Goldador validator", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)


class ValidateRequest(BaseModel):
    """Request body for ``POST /validate``."""

    ref: str = Field(
        ...,
        min_length=1,
        max_length=_REF_MAX_LENGTH,
        description="Git ref (branch, tag, or SHA)",
    )


def run_validation_for_ref(ref: str) -> dict[str, Any]:
    """Fetch TOML from GitHub at ``ref`` and return structured validation results."""
    reporter = Reporter()
    record = bind_reporter(reporter)
    member_tomls, team_tomls = fetch_goldador_toml_at_ref(ref, record=record)
    try:
        members = load_members(record, file_contents=member_tomls)
        MemberValidator(members, reporter).validate()

        teams = load_teams(record, file_contents=team_tomls)
        TeamValidator(teams, members, reporter).validate()
    except GovernanceLoadError as e:
        reporter.insert_error(
            e.file_path,
            ErrorCode.GOVERNANCE_LOAD_ERROR,
            e.message,
        )

    return {
        "repository": GOLDADOR_REPO_FULL_NAME,
        "ref": ref,
        "loaded": {
            "member_files": len(member_tomls),
            "team_files": len(team_tomls),
        },
        "validation": {"errors": reporter.as_result()["errors"]},
    }


def _status_for(exc: Exception) -> int:
    """Map a known validator exception to the HTTP status used in the response."""
    if isinstance(exc, GoldadorGitHubError):
        return exc.status_code or _FALLBACK_STATUS_CODE
    return _STATUS_CODE_BY_EXCEPTION.get(type(exc), _FALLBACK_STATUS_CODE)


def _error_detail(ref: str, exc: Exception) -> dict[str, str]:
    """Return the JSON ``detail`` payload for a validator-side ``HTTPException``."""
    detail = {
        "repository": GOLDADOR_REPO_FULL_NAME,
        "ref": ref,
        "error": str(exc),
    }
    if isinstance(exc, GovernanceLoadError):
        detail["file"] = exc.file_path
    return detail


def _governance_load_result(ref: str, exc: GovernanceLoadError) -> dict[str, Any]:
    """Serialize a load failure as a validation result payload."""
    reporter = Reporter()
    reporter.insert_error(
        exc.file_path,
        ErrorCode.GOVERNANCE_LOAD_ERROR,
        exc.message,
    )
    return {
        "repository": GOLDADOR_REPO_FULL_NAME,
        "ref": ref,
        "loaded": {"member_files": 0, "team_files": 0},
        "validation": {"errors": reporter.as_result()["errors"]},
    }


def _log_mapped_error(ref: str, exc: Exception) -> None:
    """Log a mapped validator failure before it is returned as an HTTP error."""
    if isinstance(exc, GovernanceLoadError):
        logger.error(
            "Validation request failed for ref %s (%s): %s",
            ref,
            exc.file_path,
            exc.message,
        )
        return

    logger.error(
        "Validation request failed for ref %s (%s): %s",
        ref,
        type(exc).__name__,
        exc,
    )


def _log_validation_success(ref: str, result: dict[str, Any]) -> None:
    """Log a completed validation response summary."""
    loaded = result.get("loaded")
    validation = result.get("validation")
    if not isinstance(loaded, Mapping) or not isinstance(validation, Mapping):
        logger.info("Validation completed for ref %s", ref)
        return

    errors = validation.get("errors")
    if not isinstance(errors, Mapping):
        logger.info("Validation completed for ref %s", ref)
        return

    error_count = 0
    files_with_errors = 0
    for entries in errors.values():
        if not isinstance(entries, list):
            logger.info("Validation completed for ref %s", ref)
            return
        if entries:
            files_with_errors += 1
        error_count += len(entries)

    logger.info(
        "Validation completed for ref %s (%s member files, %s team files, "
        "%s error(s) in %s file(s))",
        ref,
        loaded.get("member_files"),
        loaded.get("team_files"),
        error_count,
        files_with_errors,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    _exc: Exception,
) -> JSONResponse:
    """Log unexpected failures while keeping client responses opaque."""
    logger.exception("Unhandled validator error for %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


@app.get("/")
async def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.post("/validate")
@limiter.limit(_RATE_LIMIT_VALIDATE)
async def validate_remote(
    request: Request,  # noqa: ARG001
    response: Response,  # noqa: ARG001
    body: ValidateRequest,
) -> dict[str, Any]:
    """Validate governance TOML at ``ref`` using the same rules as the CLI."""
    logger.info("Validation request started for ref %s", body.ref)
    try:
        result = await asyncio.to_thread(run_validation_for_ref, body.ref)
    except GovernanceLoadError as e:
        logger.info(
            "Validation request for ref %s returned governance load errors",
            body.ref,
        )
        result = _governance_load_result(body.ref, e)
        _log_validation_success(body.ref, result)
        return result
    except (
        GoldadorGitHubError,
        MemberValidationError,
        TeamValidationError,
    ) as e:
        _log_mapped_error(body.ref, e)
        raise HTTPException(
            status_code=_status_for(e),
            detail=_error_detail(body.ref, e),
        ) from e

    _log_validation_success(body.ref, result)
    return result


def main() -> None:
    """Run the API with uvicorn (dev-friendly defaults)."""
    uvicorn.run(
        "meta.validator.src.server:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=False,
    )
