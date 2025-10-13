#!/bin/bash
# Setup script for Azure 30-day trial testing
# This script helps you set up an Azure trial subscription with cost controls

set -e

echo "=========================================="
echo "Azure 30-Day Trial Setup for TopDeck"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    echo "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

echo -e "${GREEN}✓${NC} Azure CLI is installed"

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}You are not logged in to Azure${NC}"
    echo "Opening browser for login..."
    az login
fi

echo -e "${GREEN}✓${NC} Logged in to Azure"

# Get current subscription
SUBSCRIPTION=$(az account show --query "name" -o tsv)
SUBSCRIPTION_ID=$(az account show --query "id" -o tsv)

echo ""
echo "Current Subscription: $SUBSCRIPTION"
echo "Subscription ID: $SUBSCRIPTION_ID"
echo ""

# Check if it's a trial subscription
SUBSCRIPTION_TYPE=$(az account show --query "subscriptionPolicies.quotaId" -o tsv)
if [[ "$SUBSCRIPTION_TYPE" == *"Free"* ]] || [[ "$SUBSCRIPTION_TYPE" == *"Trial"* ]]; then
    echo -e "${GREEN}✓${NC} This appears to be a trial/free subscription"
else
    echo -e "${YELLOW}⚠${NC} This may not be a trial subscription. Be careful with costs!"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set up cost budget
echo ""
echo "Setting up cost controls..."
echo ""

read -p "Enter your email for budget alerts: " EMAIL
read -p "Enter monthly budget limit in USD (default: 50): " BUDGET
BUDGET=${BUDGET:-50}

# Create a resource group for shared resources
RG_NAME="topdeck-shared"
LOCATION="eastus"

echo ""
echo "Creating shared resource group: $RG_NAME in $LOCATION..."
az group create --name "$RG_NAME" --location "$LOCATION" --tags "Project=TopDeck" "Purpose=Shared"

echo -e "${GREEN}✓${NC} Resource group created"

# Create storage account for Terraform state
STORAGE_ACCOUNT_NAME="topdeckstate$(echo $SUBSCRIPTION_ID | cut -c1-8)"

echo ""
echo "Creating storage account for Terraform state: $STORAGE_ACCOUNT_NAME..."
az storage account create \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RG_NAME" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --encryption-services blob \
  --tags "Project=TopDeck" "Purpose=TerraformState"

echo -e "${GREEN}✓${NC} Storage account created"

# Create container for Terraform state
echo ""
echo "Creating container for Terraform state..."
az storage container create \
  --name "terraform-state" \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --auth-mode login

echo -e "${GREEN}✓${NC} Container created"

# Output setup information
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Subscription ID: $SUBSCRIPTION_ID"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Resource Group: $RG_NAME"
echo ""
echo "Next steps:"
echo "1. Copy test.tfvars.example to test.tfvars"
echo "2. Update test.tfvars with your subscription ID and email"
echo "3. Run ./deploy-test-infrastructure.sh to deploy test resources"
echo ""
echo "Important files have been saved to: azure-setup.env"

# Save configuration to file
cat > azure-setup.env << EOF
export ARM_SUBSCRIPTION_ID="$SUBSCRIPTION_ID"
export AZURE_STORAGE_ACCOUNT="$STORAGE_ACCOUNT_NAME"
export AZURE_RESOURCE_GROUP="$RG_NAME"
export AZURE_LOCATION="$LOCATION"
export BUDGET_EMAIL="$EMAIL"
export MONTHLY_BUDGET="$BUDGET"
EOF

echo ""
echo "To use these settings in your shell, run:"
echo "  source azure-setup.env"
echo ""
