locals {
  team_oidc_client_ids = {
    for client_id, parts in {
      for id, _ in keycloak_openid_client.team_oidc_clients : id => split("-", id)
    } : client_id => {
      slug = join("-", slice(parts, 0, length(parts) - 1))
      env  = parts[length(parts) - 1]
    }
  }
}

output "openbao_oidc_client_secret" {
  description = "OpenBao OIDC client secret"
  value       = keycloak_openid_client.openbao.client_secret
  sensitive   = true
}

output "team_oidc_clients" {
  description = "Keycloak team OIDC client non-sensitive information keyed by client_id"
  value       = local.team_oidc_client_ids
}

output "team_oidc_client_secrets" {
  description = "Keycloak team OIDC client sensitive secrets keyed by client_id"
  value = {
    for client_id, v in keycloak_openid_client.team_oidc_clients : client_id => {
      slug          = local.team_oidc_client_ids[client_id].slug
      env           = local.team_oidc_client_ids[client_id].env
      client_secret = v.client_secret
      website       = v.root_url
      server        = tolist(v.web_origins)[0]
    }
  }
  sensitive = true
}
