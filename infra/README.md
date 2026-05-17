# Infrastructure

This directory implements the Infrastructure as Code (IaC) for the Labrador Governance.

## Keycloak

The Keycloak module

- `main.tf`: defines the Labrador realm (imported)

- `saml.tf`: creates the SAML identity provider for login

- `ldap.tf`: creates the LDAP to automatically sync user info when user logs in

- `user_profile.tf`: creates the user profile attributes

- `idps.tf`: creates the identity providers for linked accounts

- `openbao.tf`: creates the OpenBao client for OIDC login in OpenBao

- `leadership.tf`: creates the leadership permissions

- `teams.tf`: creates the teams for the Labrador governance

- `outputs.tf`: outputs the secrets to be stored in OpenBao

## Secrets

The Secrets module

- `main.tf`: defines the secrets engine (imported)

- `oidc.tf`: creates the OIDC auth backend for login

- `leadership.tf`: creates the leadership permissions

- `policies.tf`: creates the policies for each team

- `teams.tf`: stores the OIDC client secrets for each team

## GitHub

The GitHub module

- `main.tf`: defines the GitHub organization (imported)

- `members.tf`: add members to the GitHub organization

- `teams.tf`: creates the GitHub teams, including members and permission to repos
