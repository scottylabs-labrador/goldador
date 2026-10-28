terraform {
  required_providers {
    grouper = {
      source  = "ap-1/grouper"
      version = "~> 0.1"
    }
  }
}

provider "grouper" {
  url       = "https://grouper.andrew.cmu.edu/grouper-ws/servicesRest/v2_6_000"
  username  = "scottylabs-svc"
  password  = var.grouper_password
  time_zone = "America/New_York"
}
