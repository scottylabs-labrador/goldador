resource "github_membership" "membership_for_admins" {
  for_each = toset(var.github_usernames.admins)
  username = each.value
  role     = "admin"
}

resource "github_membership" "membership_for_non_admins" {
  for_each = toset(var.github_usernames.non_admins)
  username = each.value
  role     = "member"
}
