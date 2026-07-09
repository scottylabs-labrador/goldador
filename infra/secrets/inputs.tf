variable "admin_group_suffix" {
  description = "Admin group suffix"
  type        = string
}

variable "leadership_group_name" {
  description = "Leadership group name"
  type        = string
}

variable "keycloak_realm_url" {
  description = "Keycloak realm URL"
  type        = string
  default     = "https://idp.scottylabs.org/realms/labrador"
}

variable "oidc_client_id" {
  description = "OIDC client ID"
  type        = string
}

variable "oidc_client_secret" {
  description = "OIDC client secret"
  type        = string
  sensitive   = true
}

variable "secrets_url" {
  description = "Secrets URL"
  type        = string
}

variable "team_slugs" {
  description = "Team slugs"
  type        = set(string)
}

variable "vault_token" {
  description = "Vault token"
  type        = string
  sensitive   = true
}

variable "team_oidc_clients" {
  description = "Keycloak team OIDC client non-sensitive information keyed by client_id"
  type = map(object({
    slug = string
    env  = string
  }))
}

variable "team_oidc_client_secrets" {
  description = "Keycloak team OIDC client sensitive secrets keyed by client_id"
  type = map(object({
    slug          = string
    env           = string
    client_secret = string
    website       = string
    server        = string
  }))
  sensitive = true
}

