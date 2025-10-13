# Test Resources Module Outputs

output "storage_account_name" {
  description = "Name of the test storage account"
  value       = azurerm_storage_account.test.name
}

output "storage_account_id" {
  description = "ID of the test storage account"
  value       = azurerm_storage_account.test.id
}

output "vnet_id" {
  description = "ID of the test virtual network"
  value       = azurerm_virtual_network.test.id
}

output "vnet_name" {
  description = "Name of the test virtual network"
  value       = azurerm_virtual_network.test.name
}

output "subnet_id" {
  description = "ID of the test subnet"
  value       = azurerm_subnet.test.id
}

output "nsg_id" {
  description = "ID of the test network security group"
  value       = azurerm_network_security_group.test.id
}
