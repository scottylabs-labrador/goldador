# Goldador

Goldador is the permission-as-code repository for the Labrador committee of the
ScottyLabs organization. It records members and teams in TOML, validates those
records, and synchronizes the resulting access model to services such as
GitHub, Slack, Keycloak, OpenBao, Google Drive, and Google Groups.

Member-facing permission, setup, and contribution details live on the Goldador
public guide: <https://scottylabs-labrador.github.io/goldador/>.
The rest of this README is for maintainers of this repository.

## Repository Structure

```text
.
├── .github            # CI workflows and validation shell scripts
├── docs               # ADRs and schema documentation
├── infra              # Infrastructure as Code
├── members            # Member TOML files
├── meta
│   ├── schemas        # JSON Schema for member and team TOML
│   ├── models         # Pydantic models for loaded TOML
│   ├── clients        # Python API clients
│   ├── validator      # Validation tools for the TOML files
│   ├── synchronizers  # Permission synchronizers
│   ├── linter         # Python-based linter
│   ├── logger         # Python-based logger
│   └── tests          # Python-based tests
├── teams              # Team TOML files
└── web                # Published member-facing documentation
```

See the README files in nested directories for subsystem-specific details.

## Development Setup

[uv](https://docs.astral.sh/uv/) is used to manage dependencies and run project
commands. The development container in
[`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) contains
the recommended editor setup.

Install dependencies and run local checks with:

```zsh
uv sync --all-groups
uv run lint
uv run --group test --group validator test
```

Validation and synchronization commands that call GitHub, Keycloak, Slack, or
Google APIs require the corresponding environment variables to be present. Those
commands load `.env` automatically when run locally.

## Common Commands

```zsh
# Run Ruff and mypy.
uv run lint

# Run the Python test suite.
uv run --group test --group validator test

# Validate Goldador TOML through the hosted validator API.
uv run validate REF

# Run the validator API locally on port 8000.
uv run --group validator validator-server

# Run synchronizers.
uv run --group codeowners-synchronizer sync-codeowners
uv run --group infra-synchronizer sync-infra
uv run --group slack-synchronizer sync-slack
uv run --group google-synchronizer sync-google-drive
```

`validate` uses `https://validator.goldador.scottylabs.org` by default. Set
`VALIDATOR_SERVER_URL` to use a different validator API.

## Documentation Map

- [`web/index.html`](web/index.html) backs the published member-facing guide at
  <https://scottylabs-labrador.github.io/goldador/>.
- [`docs/adrs/`](docs/adrs/) records architectural decisions.
- [`docs/schemas/`](docs/schemas/) explains how to author member and team TOML.
- [`meta/schemas/README.md`](meta/schemas/README.md) explains the JSON Schemas
  used by Taplo and the loader.
- [`meta/validator/README.md`](meta/validator/README.md) documents validation
  rules and the validator API.
- [`meta/synchronizers/README.md`](meta/synchronizers/README.md) documents the
  service synchronizers.
- [`infra/README.md`](infra/README.md) documents the OpenTofu infrastructure.
