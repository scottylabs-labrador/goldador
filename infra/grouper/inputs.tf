variable "grouper_password" {
  description = "Grouper password of scottylabs-svc"
  type        = string
  sensitive   = true
}

variable "andrew_ids" {
  description = "Members' Andrew IDs data"
  type = object({
    admins     = list(string)
    non_admins = list(string)
  })
}
