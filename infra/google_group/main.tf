# One resource per member, so when a member changes role, the resource is updated
# instead of creating a new one to prevent Google API 409 error (existing membership).

locals {
  admin_set = toset(var.andrew_ids.admins)

  andrew_id_is_admin = {
    for id in concat(var.andrew_ids.admins, var.andrew_ids.non_admins) : id => contains(local.admin_set, id)
  }
}

resource "google_cloud_identity_group_membership" "membership" {
  for_each = local.andrew_id_is_admin

  group = var.google_group_id

  preferred_member_key {
    id = "${each.key}@andrew.cmu.edu"
  }

  dynamic "roles" {
    for_each = each.value ? ["MANAGER", "MEMBER"] : ["MEMBER"]
    content {
      name = roles.value
    }
  }
}
