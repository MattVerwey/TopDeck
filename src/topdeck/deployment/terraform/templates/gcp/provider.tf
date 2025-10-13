# GCP Provider Configuration

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for state storage
  # Can be customized per deployment
  backend "gcs" {
    # bucket  = "topdeck-terraform-state-<project-id>"
    # prefix  = "gcp/<environment>"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  
  default_labels = merge(
    var.labels,
    {
      environment = var.environment
      managed_by  = "topdeck"
    }
  )
}
