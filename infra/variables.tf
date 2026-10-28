variable "cmu_ldap_bind_credential" {
  description = "CMU LDAP bind password"
  type        = string
  sensitive   = true
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

variable "vault_token" {
  description = "Vault token"
  type        = string
  sensitive   = true
}

variable "github_token" {
  description = "GitHub token"
  type        = string
  sensitive   = true
}

variable "keycloak_realm_url" {
  description = "Keycloak realm URL"
  type        = string
  default     = "https://idp.scottylabs.org/realms/labrador"
}

variable "openbao_oidc_client_id" {
  description = "OpenBao OIDC client ID"
  type        = string
  default     = "openbao"
}

variable "secrets_url" {
  description = "Secrets URL"
  type        = string
  default     = "https://bao.scottylabs.org"
}

variable "leadership_group_name" {
  description = "Leadership group name"
  type        = string
  default     = "leadership"
}

variable "admin_group_suffix" {
  description = "Admin group suffix"
  type        = string
  default     = "admins"
}

variable "github_client_id" {
  description = "GitHub IDP client ID"
  type        = string
  sensitive   = true
}

variable "github_client_secret" {
  description = "GitHub IDP client secret"
  type        = string
  sensitive   = true
}

variable "slack_client_id" {
  description = "Slack IDP client ID"
  type        = string
  sensitive   = true
}

variable "slack_client_secret" {
  description = "Slack IDP client secret"
  type        = string
  sensitive   = true
}
