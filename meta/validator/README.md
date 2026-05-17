# Validator

This directory contains the Python-based validator of the project.
This README describes the checks performed by the validator, as well as other checks.

## Validator Checks

### TOML Files

- The field orderings in a TOML file must match the the ordering of `properties`
  in the corresponding JSON schema file.

### Members

- The member's filename must be a valid GitHub username.

- The member's `andrew-id` field must match the username of a user in Keycloak.

- The member's Keycloak user must be linked to a GitHub account and a Slack account,
  and the GitHub username must match the member's filename.

### Teams

- All leads in a team must also be listed as members.

- All team members must be listed in the `members/` directory.

- Each team repository must exist as a GitHub repository in the
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

_Note: See bash scripts in the [.github/scripts/](../../.github/scripts/)_
_directory for more details._

## Check EditorConfig Compliance

We use [EditorConfig](https://editorconfig.org/) to ensure consistent coding styles.
The VSCode extension [editorconfig.editorconfig](
  https://marketplace.visualstudio.com/items?itemName=editorconfig.editorconfig
) will format files automatically when saving.
You can also run the check locally by installing [editorconfig-checker](
  https://github.com/editorconfig-checker/editorconfig-checker?tab=readme-ov-file#installation
) and running `editorconfig-checker`.

## Validate TOML Files

We use [Taplo](https://taplo.tamasfe.dev/) to validate the TOML files against
the schemas defined in the `__meta/schemas/` directory. The VSCode extension
[tamasfe.even-better-toml](
  https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml
) will show red squiggles in the editor for errors. You can also run the check
locally by installing [taplo-cli](https://taplo.tamasfe.dev/cli/introduction.html)
and running `taplo fmt --check` and `taplo check`.
