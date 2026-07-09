output "openbao_oidc_client_secret" {
  description = "OpenBao OIDC client secret"
  value       = keycloak_openid_client.openbao.client_secret
  sensitive   = true
}

output "team_oidc_clients" {
  description = "Keycloak team OIDC client non-sensitive information keyed by client_id"
  value = {
    for client_id, _ in keycloak_openid_client.team_oidc_clients : client_id => {
      slug = split("-", client_id)[0]
      env  = split("-", client_id)[1]
    }
  }
}

output "team_oidc_client_secrets" {
  description = "Keycloak team OIDC client sensitive secrets keyed by client_id"
  value = {
    for _, v in keycloak_openid_client.team_oidc_clients : v.client_id => {
      slug          = split("-", v.client_id)[0]
      env           = split("-", v.client_id)[1]
      client_secret = v.client_secret
      website       = v.root_url
      server        = tolist(v.web_origins)[0]
    }
  }
  sensitive = true
}
