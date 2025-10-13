# Test Resources Module
# Minimal Azure resources for testing and validation
# These resources are designed to be cost-effective and suitable for testing

# Storage Account - For testing storage discovery
resource "azurerm_storage_account" "test" {
  name                     = "topdeck${var.environment}test"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  # Cost optimization
  access_tier = "Cool"
  
  # Security
  min_tls_version           = "TLS1_2"
  enable_https_traffic_only = true
  
  tags = merge(
    var.tags,
    {
      Purpose = "Testing"
      Type    = "Storage"
    }
  )
}

# Virtual Network - For testing network discovery
resource "azurerm_virtual_network" "test" {
  name                = "topdeck-${var.environment}-test-vnet"
  resource_group_name = var.resource_group_name
  location            = var.location
  address_space       = ["10.0.0.0/16"]
  
  tags = merge(
    var.tags,
    {
      Purpose = "Testing"
      Type    = "Network"
    }
  )
}

# Subnet - For testing subnet discovery
resource "azurerm_subnet" "test" {
  name                 = "test-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.test.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Network Security Group - For testing security discovery
resource "azurerm_network_security_group" "test" {
  name                = "topdeck-${var.environment}-test-nsg"
  resource_group_name = var.resource_group_name
  location            = var.location
  
  # Basic security rule for testing
  security_rule {
    name                       = "allow-https"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  
  tags = merge(
    var.tags,
    {
      Purpose = "Testing"
      Type    = "Security"
    }
  )
}

# Associate NSG with subnet
resource "azurerm_subnet_network_security_group_association" "test" {
  subnet_id                 = azurerm_subnet.test.id
  network_security_group_id = azurerm_network_security_group.test.id
}
