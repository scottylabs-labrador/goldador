# Goldador

This repository is responsible for the governance of the Labrador committee of the
ScottyLabs organization. It formalizes permission as code. See [Goldador Wiki](
    https://github.com/ScottyLabs-Labrador/goldador/wiki
) on how to use this repository to obtain permissions.

The rest of the documentation is for maintainers of this repository.

## Repository Structure

```py
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
└── teams              # Team TOML files
```

See README.md in each directory for more details.

## Development Setup

[UV](https://docs.astral.sh/uv/) is used to manage the dependencies and run commands.
See [pyproject.toml](pyproject.toml) for more details.

Recommended extensions and settings for development are specified in
[devcontainer.json](.devcontainer/devcontainer.json).
