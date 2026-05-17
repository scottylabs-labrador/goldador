output "openbao_oidc_client_secret" {
  description = "OpenBao OIDC client secret"
  value       = keycloak_openid_client.openbao.client_secret
  sensitive   = true
}

output "team_oidc_client_ids" {
  description = "Keycloak team OIDC client_ids"
  value       = [for k, v in keycloak_openid_client.team_oidc_clients : v.client_id]
}

output "team_oidc_client_secrets" {
  description = "Keycloak team OIDC client secrets keyed by client_id"
  value = {
    for k, v in keycloak_openid_client.team_oidc_clients : v.client_id => v.client_secret
  }
  sensitive = true
}
