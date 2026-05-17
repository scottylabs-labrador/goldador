# Infrastructure

This directory contains the OpenTofu infrastructure for Labrador governance.
It consumes generated data from [`inputs.json`](inputs.json), plus sensitive
runtime variables supplied by CI, and applies the resulting access model to
identity, secret, GitHub, and Google Group systems.

## Layout

```text
infra/
├── main.tf            # Composes the infrastructure modules
├── backend.tf         # Remote state backend configuration
├── locals.tf          # Decodes inputs.json into local values
├── variables.tf       # Runtime variables and secrets
├── inputs.json        # Generated member and team data
├── github/            # GitHub organization membership and teams
├── google_group/      # Google Group membership
├── keycloak/          # Labrador realm, groups, clients, and identity providers
└── secrets/           # OpenBao auth, policies, and team secrets
```

Do not edit [`inputs.json`](inputs.json) by hand unless you are intentionally
debugging generated data. It is produced by the infrastructure synchronizer from
the TOML files in [`members/`](../members/) and [`teams/`](../teams/).

## Modules

### `keycloak`

Manages the Labrador Keycloak realm and related access structures:

- `main.tf` imports and configures the Labrador realm.
- `saml.tf` configures the SAML identity provider for login.
- `ldap.tf` configures LDAP-backed user lookup.
- `user_profile.tf` configures user profile attributes.
- `idps.tf` configures linked identity providers.
- `openbao.tf` creates the OpenBao OIDC client.
- `leadership.tf` creates leadership access.
- `teams.tf` creates team groups and team OIDC clients.
- `outputs.tf` emits generated secrets consumed by the OpenBao module.

### `secrets`

Manages OpenBao configuration:

- `main.tf` imports and configures the secrets engine.
- `oidc.tf` configures OIDC login.
- `leadership.tf` creates leadership permissions.
- `policies.tf` creates team policies.
- `teams.tf` stores generated OIDC client secrets for teams.

### `github`

Manages GitHub organization state:

- `main.tf` imports the GitHub organization.
- `membership.tf` manages organization membership.
- `teams.tf` creates teams, team membership, and repository permissions.

### `google_group`

Manages Google Group membership from the generated Andrew ID lists.

## Applying Changes

Infrastructure changes are applied by the `Sync` GitHub Actions workflow when
files under [`infra/`](.) change on `main`. The workflow runs:

```zsh
tofu init
tofu validate
tofu fmt -check -diff
tofu apply -auto-approve
```

Local plans or applies require the same backend credentials and `TF_VAR_*`
secrets configured in CI. Prefer running `tofu fmt` before opening changes that
touch Terraform/OpenTofu files.

## Data Flow

1. Maintainers update TOML in [`members/`](../members/) and
   [`teams/`](../teams/).
2. The infra synchronizer generates [`inputs.json`](inputs.json).
3. OpenTofu reads `inputs.json` through [`locals.tf`](locals.tf).
4. Modules apply the desired access model to external services.
