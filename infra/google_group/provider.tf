provider "google" {
  credentials           = var.google_credentials_json
  project               = local.google_project_id
  user_project_override = true
  billing_project       = local.google_project_id
}
