resource "vault_kv_secret_v2" "team_oidc_clients" {
  for_each = toset(var.team_oidc_client_ids)
  mount    = vault_mount.kv.path
  name     = "${split("-", each.key)[0]}/auth/${split("-", each.key)[1]}"
  data_json = jsonencode(
    {
      client_id     = each.key
      client_secret = var.team_oidc_client_secrets[each.key]
    }
  )
}
