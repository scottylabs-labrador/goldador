# Adds Labrador's members to its general group in Grouper, leaving out leadership,
# which ScottyLabs governance already adds to Grouper's role groups

locals {
  labrador = "Community:Department:ScottyLabs:ref:committees:labrador"
}

data "grouper_group" "general" {
  name = "${local.labrador}:general"
}

data "grouper_group" "roles" {
  name = "${local.labrador}:roles:all"
}

data "grouper_group_members" "roles" {
  group = data.grouper_group.roles.id
}

resource "grouper_group_members" "general" {
  group = data.grouper_group.general.id
  subjects = {
    ldap = setsubtract(
      concat(var.andrew_ids.admins, var.andrew_ids.non_admins),
      data.grouper_group_members.roles.subjects["ldap"],
    )
  }
}
