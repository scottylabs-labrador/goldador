# Validator

This directory contains the Python-based validator for governance TOML. The
validator loads member and team files from GitHub at a requested ref, applies
project-specific rules, and reports structured validation results for CI.

Schema formatting checks are handled separately by Taplo and EditorConfig.

## Entrypoints

```zsh
# Validate a branch, tag, or commit SHA through the hosted validator API.
uv run validate REF

# Run the FastAPI validator service on port 8000.
uv run --group validator validator-server
```

The CLI posts to the hosted API at `https://goldador.scottylabs.org` by default.
Set `VALIDATOR_SERVER_URL` to point the CLI at another validator server. The API
exposes:

- `GET /` for a health check.
- `POST /validate` with JSON body `{"ref": "branch-or-sha"}`.

## Required Environment

Remote validation requires credentials for the external services it checks:

- `SYNC_GITHUB_TOKEN` for GitHub API calls.
- `KEYCLOAK_SERVER_URL`, `KEYCLOAK_PASSWORD`, `KEYCLOAK_REALM`,
  `KEYCLOAK_CLIENT_ID`, and `KEYCLOAK_USER_REALM` for Keycloak checks.

The API also supports rate-limit configuration:

- `VALIDATOR_VALIDATE_RATE_LIMIT`, defaulting to `60/minute`.
- `VALIDATOR_RATE_LIMIT_USE_X_FORWARDED_FOR`, for deployments behind a proxy.
- `VALIDATOR_RATE_LIMIT_DISABLED`, for trusted local or internal use.

## Validator Checks

### TOML Loading

- The top-level key ordering in each TOML file must match the ordering of
  `properties` in the corresponding JSON Schema.
- Member and team files must be parseable and match the Pydantic models loaded
  from the TOML contents.

### Members

- The member filename must be a valid GitHub username.
- The member's `andrew-id`, when present, must match a Keycloak user.
- The Keycloak user must be linked to a GitHub account.
- The linked GitHub username must match the member filename.
- The Keycloak user must be linked to a Slack account.

### Teams

- All leads in a team must also be listed as members.
- All team members must be listed in the [`members/`](../../members/) directory.
- Each team repository must exist in the
  [ScottyLabs-Labrador](https://github.com/ScottyLabs-Labrador) organization.

## Bash Script Checks

- Pull requests adding a new member must be submitted by the member themselves.
  This self-nomination approach promotes ownership, helps maintain the integrity
  of our member list, and encourages active participation with our governance
  process and the organization. PRs in violation will be automatically rejected.

- When adding a new team, all team members must already exist in the `members/`
  directory. The team creator must be a lead of the team's newest membership record.

- Since you may only add yourself as a member and join only one team per PR,
  any PR that changes more than one file in the `members/` or `teams/`
  directories is automatically rejected.

See bash scripts in the [`.github/scripts/`](../../.github/scripts/) directory
for implementation details.

## Other CI Checks

### EditorConfig

We use [EditorConfig](https://editorconfig.org/) to ensure consistent coding styles.
The VSCode extension [editorconfig.editorconfig](
  https://marketplace.visualstudio.com/items?itemName=editorconfig.editorconfig
) will format files automatically when saving.
You can also run the check locally by installing [editorconfig-checker](
  https://github.com/editorconfig-checker/editorconfig-checker?tab=readme-ov-file#installation
) and running `editorconfig-checker`.

### TOML Schema and Formatting

We use [Taplo](https://taplo.tamasfe.dev/) to validate the TOML files against
the schemas defined in the [`meta/schemas/`](../schemas/) directory. The VSCode extension
[tamasfe.even-better-toml](
  https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml
) will show red squiggles in the editor for errors. You can also run the check
locally by installing [taplo-cli](https://taplo.tamasfe.dev/cli/introduction.html)
and running `taplo fmt --check` and `taplo check`.
