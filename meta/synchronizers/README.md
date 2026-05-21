# Synchronizer

This directory contains Python-based synchronizers that project the desired
Labrador access model from [`members/`](../../members/) and
[`teams/`](../../teams/) into external systems or generated repository files.

Each synchronizer loads the same member and team models, then performs one
targeted side effect.

## Entrypoints

```zsh
uv run --group codeowners-synchronizer sync-codeowners
uv run --group infra-synchronizer sync-infra
uv run --group slack-synchronizer sync-slack
uv run --group google-synchronizer sync-google-drive
```

All synchronizers load `.env` when run locally.

## CODEOWNERS

The CODEOWNERS synchronizer updates
[`../../.github/CODEOWNERS`](../../.github/CODEOWNERS).

- The default owners are Goldador team leads.
- The owners for the `teams/` directory are leadership leads.
- Each `teams/<slug>.toml` file is owned by that team's leads.
- It commits changes through the GitHub API with
  `chore: auto-update CODEOWNERS`.

Required environment:

- `SYNC_GITHUB_TOKEN`

## Infra

The infra synchronizer updates [`../../infra/inputs.json`](../../infra/inputs.json).

- It writes GitHub usernames split into leadership admins and non-admins.
- It writes Andrew IDs split into leadership admins and non-admins.
- It writes team metadata, members, leads, repositories, and OIDC settings.
- It includes legacy team entries that are still required by infrastructure.
- It commits changes through the GitHub API with
  `chore: auto-update infra/inputs.json`.

Required environment:

- `SYNC_GITHUB_TOKEN`

## Slack

The Slack synchronizer creates and maintains public Slack channels for teams.

- It creates channels named `labrador-<team-slug>` when missing.
- It skips the leadership team because that channel is private and unmanaged by
  Goldador.
- It resolves Slack IDs through Keycloak social login links.
- It invites team members who are not already in the channel.

Required environment:

- `SLACK_USER_TOKEN`
- `SLACK_BOT_TOKEN`
- `KEYCLOAK_SERVER_URL`
- `KEYCLOAK_PASSWORD`
- `KEYCLOAK_REALM`
- `KEYCLOAK_CLIENT_ID`
- `KEYCLOAK_USER_REALM`

## Google Drive

The Google Drive synchronizer grants baseline access to the ScottyLabs Google
Drive.

- Labrador members receive contributor access.
- Leadership leads receive at least content manager access.
- Existing higher Google Drive permissions are preserved.

Required environment:

- `GOOGLE_CLIENT_EMAIL`
- `GOOGLE_PRIVATE_KEY`
- `SCOTTYLABS_GOOGLE_DRIVE_ID`

## CI Behavior

Synchronizers run from the `Sync` GitHub Actions workflow on pushes to `main`.
Jobs are path-filtered so only relevant synchronizers run for a given change.

The file-writing synchronizers update repository files through the GitHub API.
The service synchronizers update their target services directly.

## Adding a Synchronizer

New synchronizers should subclass `AbstractSynchronizer`, implement `sync()`,
load credentials from environment variables, and expose a console script in
[`../../pyproject.toml`](../../pyproject.toml). Keep each synchronizer focused
on one external system or generated artifact.
