variable "google_group_id" {
  description = "Google group ID (groups/{group_id})"
  type        = string
}

variable "google_credentials_json" {
  description = "Google credentials JSON"
  type        = string
  sensitive   = true
}

locals {
  google_project_id = jsondecode(var.google_credentials_json)["quota_project_id"]
}

variable "andrew_ids" {
  description = "Members' Andrew IDs data"
  type = object({
    admins     = list(string)
    non_admins = list(string)
  })
}
