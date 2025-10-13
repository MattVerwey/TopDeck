# Azure Terraform Variables
# Reusable variables for Azure resource deployment

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
}

variable "location" {
  description = "Azure location/region"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Environment name (Dev, Staging, Prod, Test)"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

# Cost Management Variables
variable "enable_cost_budget" {
  description = "Enable cost budget alerts"
  type        = bool
  default     = true
}

variable "monthly_budget_amount" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 50
}

variable "budget_alert_emails" {
  description = "Email addresses to receive budget alerts"
  type        = list(string)
  default     = []
}

# Testing Variables
variable "create_test_resources" {
  description = "Create minimal test resources for validation"
  type        = bool
  default     = false
}
