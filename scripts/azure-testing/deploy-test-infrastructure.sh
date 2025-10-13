#!/bin/bash
# Deploy Azure test infrastructure using Terraform
# This script deploys minimal resources for testing TopDeck discovery

set -e

echo "=========================================="
echo "Deploy Azure Test Infrastructure"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    echo "Install from: https://www.terraform.io/downloads"
    exit 1
fi

echo -e "${GREEN}✓${NC} Terraform is installed"

# Load environment variables if they exist
if [ -f "azure-setup.env" ]; then
    source azure-setup.env
    echo -e "${GREEN}✓${NC} Loaded Azure configuration from azure-setup.env"
else
    echo -e "${YELLOW}⚠${NC} azure-setup.env not found. Make sure you've run setup-azure-trial.sh"
fi

# Change to Terraform directory
TERRAFORM_DIR="../../src/topdeck/deployment/terraform/templates/azure"
cd "$(dirname "$0")"
cd "$TERRAFORM_DIR"

echo ""
echo "Working directory: $(pwd)"
echo ""

# Check if tfvars file exists
if [ ! -f "test.tfvars" ]; then
    echo -e "${YELLOW}⚠${NC} test.tfvars not found"
    echo "Creating from example..."
    cp test.tfvars.example test.tfvars
    echo ""
    echo -e "${RED}Please edit test.tfvars with your values before continuing${NC}"
    echo "File location: $(pwd)/test.tfvars"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found test.tfvars"

# Initialize Terraform
echo ""
echo "Initializing Terraform..."
terraform init

echo -e "${GREEN}✓${NC} Terraform initialized"

# Validate configuration
echo ""
echo "Validating Terraform configuration..."
terraform validate

echo -e "${GREEN}✓${NC} Configuration is valid"

# Plan deployment
echo ""
echo "Planning deployment..."
terraform plan -var-file="test.tfvars" -out=tfplan

echo ""
echo -e "${YELLOW}Review the plan above${NC}"
read -p "Do you want to apply this plan? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    rm tfplan
    exit 0
fi

# Apply deployment
echo ""
echo "Deploying infrastructure..."
terraform apply tfplan

rm tfplan

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

# Show outputs
echo "Resources created:"
terraform output

echo ""
echo "To destroy these resources later, run:"
echo "  ./teardown-test-infrastructure.sh"
echo ""
