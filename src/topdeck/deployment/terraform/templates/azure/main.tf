# Azure Main Terraform Configuration
# Template for deploying Azure test resources with cost management

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  
  tags = merge(
    var.tags,
    {
      Environment = var.environment
      ManagedBy   = "TopDeck"
      Purpose     = "Testing"
    }
  )
}

# Cost Management Budget
resource "azurerm_consumption_budget_resource_group" "main" {
  count = var.enable_cost_budget ? 1 : 0

  name              = "${var.resource_group_name}-budget"
  resource_group_id = azurerm_resource_group.main.id

  amount     = var.monthly_budget_amount
  time_grain = "Monthly"

  time_period {
    start_date = formatdate("YYYY-MM-01'T'00:00:00'Z'", timestamp())
  }

  notification {
    enabled   = true
    threshold = 80.0
    operator  = "GreaterThan"

    contact_emails = var.budget_alert_emails
  }

  notification {
    enabled   = true
    threshold = 100.0
    operator  = "GreaterThan"

    contact_emails = var.budget_alert_emails
  }
}

# Test Resources - Minimal infrastructure for validation
module "test_resources" {
  count  = var.create_test_resources ? 1 : 0
  source = "./modules/test_resources"
  
  resource_group_name = azurerm_resource_group.main.name
  location           = var.location
  environment        = var.environment
  tags               = var.tags
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
