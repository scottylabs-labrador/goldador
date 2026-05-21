# A team member is allowed to read and list secrets in the local file/folder.

resource "vault_identity_group" "team_members_groups" {
  for_each = var.team_slugs
  name     = each.key
  type     = "external"
  policies = [vault_policy.team_members_policies[each.key].name]
}

resource "vault_identity_group_alias" "team_members_groups" {
  for_each       = var.team_slugs
  name           = each.key
  canonical_id   = vault_identity_group.team_members_groups[each.key].id
  mount_accessor = vault_jwt_auth_backend.oidc.accessor
}

resource "vault_policy" "team_members_policies" {
  for_each = var.team_slugs
  name     = each.key
  policy   = <<-EOT
    path "${vault_mount.kv.path}/data/${each.key}/local" {
        capabilities = ["read", "list"]
    }

    path "${vault_mount.kv.path}/data/${each.key}/local/*" {
        capabilities = ["read", "list"]
    }
  EOT
}

# A team admin is allowed have all permissions on the team's folder.

locals {
  # A map from team slug to its admin group name
  team_admin_group_names = {
    for team in var.team_slugs :
    team => {
      name = "${team}-${var.admin_group_suffix}"
    }
  }
}

resource "vault_identity_group" "team_admins_groups" {
  for_each = local.team_admin_group_names
  name     = each.value.name
  type     = "external"
  policies = [vault_policy.team_admins_policies[each.key].name]
}

resource "vault_identity_group_alias" "team_admins_groups" {
  for_each       = local.team_admin_group_names
  name           = each.value.name
  canonical_id   = vault_identity_group.team_admins_groups[each.key].id
  mount_accessor = vault_jwt_auth_backend.oidc.accessor
}

resource "vault_policy" "team_admins_policies" {
  for_each = local.team_admin_group_names
  name     = each.value.name
  policy   = <<-EOT
    path "${vault_mount.kv.path}/data/${each.key}/*" {
        capabilities = ["create", "read", "update", "delete", "list", "sudo"]
    }

    path "${vault_mount.kv.path}/metadata/${each.key}/*" {
        capabilities = ["create", "read", "update", "delete", "list", "sudo"]
    }
  EOT
}

