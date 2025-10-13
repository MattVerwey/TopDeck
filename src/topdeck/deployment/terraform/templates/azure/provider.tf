# Azure Provider Configuration

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  # Backend configuration for state storage
  # Can be customized per deployment
  backend "azurerm" {
    # storage_account_name = "topdeck<environment>"
    # container_name       = "terraform-state"
    # key                  = "azure/<resource-group>.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
