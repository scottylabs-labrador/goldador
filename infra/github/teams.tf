# For each team, create a team for all members and a sub-team for admins.
# The admin team has admin permission on the team repositories.
# The member team has write permission on the team repositories.

resource "github_team" "teams" {
  for_each    = var.teams
  name        = each.value.name
  description = each.value.description
  privacy     = "closed" # Visible to all members of the organization
}

resource "github_team" "admin_teams" {
  for_each       = var.teams
  name           = "${each.value.name} Admins"
  privacy        = "closed" # Visible to all members of the organization
  parent_team_id = github_team.teams[each.key].id
}

# Team repositories
locals {
  team_repositories = merge([
    for team_slug, team in var.teams : {
      for repo in team.repos :
      "${team_slug}:${repo}" => {
        team_slug = team_slug
        repo      = repo
      }
    }
  ]...)
}

resource "github_team_repository" "team_repositories" {
  for_each   = local.team_repositories
  team_id    = github_team.teams[each.value.team_slug].id
  repository = each.value.repo
  permission = "push"
}

resource "github_team_repository" "team_admin_repositories" {
  for_each   = local.team_repositories
  team_id    = github_team.admin_teams[each.value.team_slug].id
  repository = each.value.repo
  permission = "admin"
}

# Team memberships
locals {
  team_member_memberships = merge([
    for team_slug, team in var.teams : {
      for username in team.members.github_usernames :
      "${team_slug}:${username}" => {
        team_slug = team_slug
        username  = username
      }
    }
  ]...)

  team_admin_memberships = merge([
    for team_slug, team in var.teams : {
      for username in team.admins.github_usernames :
      "${team_slug}:${username}" => {
        team_slug = team_slug
        username  = username
      }
    }
  ]...)
}

resource "github_team_membership" "team_memberships" {
  for_each = local.team_member_memberships
  team_id  = github_team.teams[each.value.team_slug].id
  username = each.value.username
}

resource "github_team_membership" "team_admins_memberships" {
  for_each = local.team_admin_memberships
  team_id  = github_team.admin_teams[each.value.team_slug].id
  username = each.value.username
}
