variable "admin_group_suffix" {
  description = "Admin group suffix"
  type        = string
}

variable "cmu_ldap_bind_credential" {
  description = "CMU LDAP bind password"
  type        = string
  sensitive   = true
}

variable "leadership_group_name" {
  description = "Leadership group name"
  type        = string
}

variable "teams" {
  description = "Teams data"
  type = map(object({
    members = object({
      andrew_ids       = list(string)
      github_usernames = list(string)
    })
    admins = object({
      andrew_ids       = list(string)
      github_usernames = list(string)
    })
    website             = optional(string, "")
    server              = optional(string, "")
    create_oidc_clients = bool
  }))
}

variable "keycloak_client_id" {
  description = "Keycloak client ID"
  type        = string
  sensitive   = true
}

variable "keycloak_client_secret" {
  description = "Keycloak client secret"
  type        = string
  sensitive   = true
}

variable "keycloak_realm" {
  description = "Keycloak realm"
  type        = string
  default     = "labrador"
}

variable "keycloak_realm_url" {
  description = "Keycloak realm URL"
  type        = string
}

variable "keycloak_url" {
  description = "Keycloak URL"
  type        = string
  default     = "https://idp.scottylabs.org"
}

variable "openbao_oidc_client_id" {
  description = "OIDC client ID"
  type        = string
}

variable "secrets_url" {
  description = "Secrets URL"
  type        = string
}

variable "github_client_id" {
  description = "GitHub client ID"
  type        = string
  sensitive   = true
}

variable "github_client_secret" {
  description = "GitHub client secret"
  type        = string
  sensitive   = true
}

variable "slack_client_id" {
  description = "Slack client ID"
  type        = string
  sensitive   = true
}

variable "slack_client_secret" {
  description = "Slack client secret"
  type        = string
  sensitive   = true
}
