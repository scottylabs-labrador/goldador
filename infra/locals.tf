locals {
  inputs_data          = jsondecode(file("inputs.json"))
  github_usernames     = local.inputs_data["github_usernames"]
  andrew_ids           = local.inputs_data["andrew_ids"]
  teams                = local.inputs_data["teams"]
  leadership_team      = local.teams["leadership"]
  non_leadership_teams = { for k, v in local.teams : k => v if k != "leadership" }
}
