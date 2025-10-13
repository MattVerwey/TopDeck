#!/bin/bash
# Validate Azure test infrastructure deployment
# This script checks that all resources were created correctly

set -e

echo "=========================================="
echo "Validate Azure Test Infrastructure"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    exit 1
fi

# Load configuration
if [ -f "azure-setup.env" ]; then
    source azure-setup.env
else
    echo -e "${YELLOW}⚠${NC} azure-setup.env not found"
    echo "Using current Azure context"
fi

# Get Terraform outputs
TERRAFORM_DIR="../../src/topdeck/deployment/terraform/templates/azure"
cd "$(dirname "$0")"
cd "$TERRAFORM_DIR"

if [ ! -f "terraform.tfstate" ]; then
    echo -e "${RED}Error: No Terraform state found${NC}"
    echo "Run ./deploy-test-infrastructure.sh first"
    exit 1
fi

echo "Checking Terraform outputs..."
RG_NAME=$(terraform output -raw resource_group_name)
LOCATION=$(terraform output -raw location)

echo ""
echo "Resource Group: $RG_NAME"
echo "Location: $LOCATION"
echo ""

# Validate resource group exists
echo "1. Validating resource group..."
if az group show --name "$RG_NAME" &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Resource group exists"
else
    echo -e "   ${RED}✗${NC} Resource group not found"
    exit 1
fi

# Validate storage account
echo "2. Validating storage account..."
STORAGE_COUNT=$(az storage account list --resource-group "$RG_NAME" --query "length(@)" -o tsv)
if [ "$STORAGE_COUNT" -gt 0 ]; then
    STORAGE_NAME=$(az storage account list --resource-group "$RG_NAME" --query "[0].name" -o tsv)
    echo -e "   ${GREEN}✓${NC} Storage account exists: $STORAGE_NAME"
else
    echo -e "   ${YELLOW}⚠${NC} No storage account found (may not have been created)"
fi

# Validate virtual network
echo "3. Validating virtual network..."
VNET_COUNT=$(az network vnet list --resource-group "$RG_NAME" --query "length(@)" -o tsv)
if [ "$VNET_COUNT" -gt 0 ]; then
    VNET_NAME=$(az network vnet list --resource-group "$RG_NAME" --query "[0].name" -o tsv)
    echo -e "   ${GREEN}✓${NC} Virtual network exists: $VNET_NAME"
else
    echo -e "   ${YELLOW}⚠${NC} No virtual network found (may not have been created)"
fi

# Validate NSG
echo "4. Validating network security group..."
NSG_COUNT=$(az network nsg list --resource-group "$RG_NAME" --query "length(@)" -o tsv)
if [ "$NSG_COUNT" -gt 0 ]; then
    NSG_NAME=$(az network nsg list --resource-group "$RG_NAME" --query "[0].name" -o tsv)
    echo -e "   ${GREEN}✓${NC} Network security group exists: $NSG_NAME"
else
    echo -e "   ${YELLOW}⚠${NC} No NSG found (may not have been created)"
fi

# Check cost budget
echo "5. Checking cost budget..."
if terraform output budget_id &> /dev/null; then
    BUDGET_AMOUNT=$(terraform output -raw budget_amount)
    echo -e "   ${GREEN}✓${NC} Cost budget configured: \$${BUDGET_AMOUNT}/month"
else
    echo -e "   ${YELLOW}⚠${NC} Cost budget not configured"
fi

# List all resources
echo ""
echo "All resources in group:"
az resource list --resource-group "$RG_NAME" --query "[].{Name:name, Type:type, Location:location}" -o table

# Check costs
echo ""
echo "Estimated monthly cost:"
echo "(Run 'az consumption usage list' for detailed usage)"

echo ""
echo "=========================================="
echo "Validation Complete!"
echo "=========================================="
echo ""
echo "You can now test TopDeck resource discovery against these resources."
echo ""
