# GCP Main Terraform Configuration
# Example template for deploying GCP resources

# Example: VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.environment}-network"
  auto_create_subnetworks = false
  project                 = var.project_id
}

# Example: Subnet
resource "google_compute_subnetwork" "main" {
  name          = "${var.environment}-subnet"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.region
  network       = google_compute_network.main.id
  project       = var.project_id
}

# Example: GKE Cluster
# module "gke" {
#   source = "./modules/gke"
#   
#   cluster_name       = "${var.environment}-gke"
#   project_id         = var.project_id
#   region             = var.region
#   network            = google_compute_network.main.name
#   subnetwork         = google_compute_subnetwork.main.name
#   kubernetes_version = "1.28"
#   
#   labels = var.labels
# }

# Example: Cloud SQL
# module "cloud_sql" {
#   source = "./modules/cloud_sql"
#   
#   instance_name  = "${var.environment}-db"
#   database_version = "POSTGRES_15"
#   region         = var.region
#   tier           = "db-custom-2-8192"
#   
#   network    = google_compute_network.main.id
#   project_id = var.project_id
#   
#   labels = var.labels
# }
