# References
# - https://medium.com/@sauravkumarsct/integrate-keycloak-as-oidc-jwt-provider-with-hashicorp-vault-ae9ebcf8e335
# - https://github.com/ScottyLabs/infrastructure/blob/main/tofu/identity/openbao.tf

# Secrets engine
resource "vault_mount" "kv" {
  path = "labrador"
  type = "kv"
  options = {
    version = "2"
  }
}
