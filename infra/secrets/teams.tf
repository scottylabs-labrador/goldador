# Web Secrets
locals {
  web_secrets = {
    for client_id, client in var.team_oidc_client_secrets : client_id => {
      VITE_SERVER_URL = client.env == "local" ? "http://localhost" : "$${{@${client.slug}/server.SERVER_URL}}"
    }
  }
}

resource "vault_kv_secret_v2" "team_web_secrets" {
  for_each  = var.team_oidc_clients
  mount     = vault_mount.kv.path
  name      = "${each.value.slug}/generated/${each.value.env}/web"
  data_json = jsonencode(local.web_secrets[each.key])
}

# Server Secrets
locals {
  server_secrets = {
    for client_id, client in var.team_oidc_client_secrets : client_id => {
      ADMIN_GROUP           = "${client.slug}-members"
      ALLOWED_ORIGINS_REGEX = client.env == "local" ? "^https?://localhost:3000$" : "^${client.website}$"
      AUTH_CLIENT_ID        = client_id
      AUTH_CLIENT_SECRET    = client.client_secret
      AUTH_ISSUER           = var.keycloak_realm_url
      AUTH_JWKS_URI         = "${var.keycloak_realm_url}/protocol/openid-connect/certs"
      BETTER_AUTH_URL       = client.env == "local" ? "http://localhost:3000" : "${client.website}"
      DATABASE_URL          = client.env == "local" ? "postgresql://postgres:donotuseinprod@postgres:5432/${client.slug}" : "$${{Postgres.DATABASE_URL}}"
      SERVER_URL            = client.env == "local" ? "http://localhost" : "${client.server}"
    }
  }
}
resource "vault_kv_secret_v2" "team_server_secrets" {
  for_each  = var.team_oidc_clients
  mount     = vault_mount.kv.path
  name      = "${each.value.slug}/generated/${each.value.env}/server"
  data_json = jsonencode(local.server_secrets[each.key])
}
