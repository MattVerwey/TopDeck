# Azure Terraform Outputs
# Export important resource information

output "resource_group_name" {
  description = "Name of the created resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_id" {
  description = "ID of the created resource group"
  value       = azurerm_resource_group.main.id
}

output "location" {
  description = "Azure location where resources are deployed"
  value       = azurerm_resource_group.main.location
}

output "budget_id" {
  description = "ID of the cost budget (if enabled)"
  value       = var.enable_cost_budget ? azurerm_consumption_budget_resource_group.main[0].id : null
}

output "budget_amount" {
  description = "Monthly budget amount in USD"
  value       = var.enable_cost_budget ? var.monthly_budget_amount : null
}

output "test_resources" {
  description = "Details of created test resources"
  value = var.create_test_resources ? {
    storage_account_name = module.test_resources[0].storage_account_name
    vnet_id             = module.test_resources[0].vnet_id
    subnet_id           = module.test_resources[0].subnet_id
  } : null
}
