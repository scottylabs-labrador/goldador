# GitHub IDP
resource "keycloak_oidc_github_identity_provider" "github_idp" {
  realm         = keycloak_realm.labrador.realm
  alias         = "github"
  display_name  = "GitHub"
  client_id     = var.github_client_id
  client_secret = var.github_client_secret
}

# Slack IDP
resource "keycloak_oidc_identity_provider" "slack_idp" {
  realm              = keycloak_realm.labrador.realm
  alias              = "slack"
  display_name       = "Slack"
  client_id          = var.slack_client_id
  client_secret      = var.slack_client_secret
  authorization_url  = "https://slack.com/openid/connect/authorize"
  token_url          = "https://slack.com/api/openid.connect.token"
  user_info_url      = "https://slack.com/api/openid.connect.userInfo"
  issuer             = "https://slack.com"
  jwks_url           = "https://slack.com/openid/connect/keys"
  hide_on_login_page = true
  validate_signature = true
}
