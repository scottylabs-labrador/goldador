# Goldador validator HTTP API (FastAPI + uvicorn).
#
# Required at runtime:
#   SYNC_GITHUB_TOKEN — GitHub API token for fetching governance TOML and org repos.
#   KEYCLOAK_SERVER_URL, KEYCLOAK_PASSWORD, KEYCLOAK_REALM,
#   KEYCLOAK_CLIENT_ID, KEYCLOAK_USER_REALM — Keycloak admin API (member checks).
#
# Optional:
#   VALIDATOR_VALIDATE_RATE_LIMIT (default 60/minute)
#   VALIDATOR_RATE_LIMIT_USE_X_FORWARDED_FOR, VALIDATOR_RATE_LIMIT_DISABLED
#
# No BuildKit cache/bind mounts (Railway rejects many mount ids); Docker layer
# cache still skips dependency sync when pyproject.toml / uv.lock are unchanged.

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:${PATH}"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev --group validator

COPY README.md ./
COPY meta ./meta
RUN uv sync --frozen --no-dev --group validator

RUN useradd --create-home --shell /bin/bash --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["validator-server"]
