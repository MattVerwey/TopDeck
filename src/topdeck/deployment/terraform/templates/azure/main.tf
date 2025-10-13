# Azure Main Terraform Configuration
# Example template for deploying Azure resources

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  
  tags = merge(
    var.tags,
    {
      Environment = var.environment
      ManagedBy   = "TopDeck"
    }
  )
}

# Example: Azure Kubernetes Service (AKS)
# module "aks" {
#   source = "./modules/aks"
#   
#   cluster_name       = "${var.environment}-aks"
#   resource_group     = azurerm_resource_group.main.name
#   location           = var.location
#   kubernetes_version = "1.28"
#   
#   tags = var.tags
# }

# Example: Azure App Service
# module "app_service" {
#   source = "./modules/app_service"
#   
#   app_name       = "${var.environment}-app"
#   resource_group = azurerm_resource_group.main.name
#   location       = var.location
#   
#   tags = var.tags
# }
