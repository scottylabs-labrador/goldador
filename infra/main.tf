module "keycloak" {
  source = "./keycloak"

  # Provider credentials
  keycloak_client_id     = var.keycloak_client_id
  keycloak_client_secret = var.keycloak_client_secret

  # URLs
  keycloak_realm_url = var.keycloak_realm_url
  secrets_url        = var.secrets_url

  # IDs
  openbao_oidc_client_id = var.openbao_oidc_client_id

  # Group names
  admin_group_suffix    = var.admin_group_suffix
  leadership_group_name = var.leadership_group_name

  # LDAP credentials
  cmu_ldap_bind_credential = var.cmu_ldap_bind_credential

  # GitHub IDP credentials
  github_client_id     = var.github_client_id
  github_client_secret = var.github_client_secret

  # Slack IDP credentials
  slack_client_id     = var.slack_client_id
  slack_client_secret = var.slack_client_secret

  # Data
  teams = local.teams
}

module "secrets" {
  source = "./secrets"

  # Credentials
  vault_token = var.vault_token

  # OIDC
  oidc_client_id     = var.openbao_oidc_client_id
  oidc_client_secret = module.keycloak.openbao_oidc_client_secret

  # URLs
  keycloak_realm_url = var.keycloak_realm_url
  secrets_url        = var.secrets_url

  # Group names
  admin_group_suffix    = var.admin_group_suffix
  leadership_group_name = var.leadership_group_name

  # Data
  team_slugs               = toset(keys(local.non_leadership_teams))
  team_oidc_client_ids     = module.keycloak.team_oidc_client_ids
  team_oidc_client_secrets = module.keycloak.team_oidc_client_secrets
}

module "github" {
  source = "./github"

  # Credentials
  github_token = var.github_token

  # Data
  github_usernames = local.github_usernames
  teams            = local.teams
}

module "google_group" {
  source = "./google_group"

  # Credentials
  google_credentials_json = var.google_credentials_json

  # IDs
  google_group_id = var.google_group_id

  # Data
  andrew_ids = local.andrew_ids
}
