# AWS Provider Configuration

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for state storage
  # Can be customized per deployment
  backend "s3" {
    # bucket         = "topdeck-terraform-state-<account-id>"
    # key            = "aws/<environment>.tfstate"
    # region         = "us-east-1"
    # encrypt        = true
    # dynamodb_table = "topdeck-terraform-locks"
  }
}

provider "aws" {
  region = var.region
  
  default_tags {
    tags = merge(
      var.tags,
      {
        Environment = var.environment
        ManagedBy   = "TopDeck"
      }
    )
  }
}
