#!/bin/bash
# Teardown Azure test infrastructure
# This script destroys all resources created for testing to prevent costs

set -e

echo "=========================================="
echo "Teardown Azure Test Infrastructure"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Change to Terraform directory
TERRAFORM_DIR="../../src/topdeck/deployment/terraform/templates/azure"
cd "$(dirname "$0")"
cd "$TERRAFORM_DIR"

echo ""
echo "Working directory: $(pwd)"
echo ""

# Check if initialized
if [ ! -d ".terraform" ]; then
    echo -e "${RED}Error: Terraform not initialized${NC}"
    echo "Run ./deploy-test-infrastructure.sh first"
    exit 1
fi

# Show what will be destroyed
echo "Planning destruction..."
terraform plan -destroy -var-file="test.tfvars"

echo ""
echo -e "${RED}⚠ WARNING: This will destroy all test resources${NC}"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Teardown cancelled"
    exit 0
fi

# Destroy resources
echo ""
echo "Destroying infrastructure..."
terraform destroy -var-file="test.tfvars" -auto-approve

echo ""
echo "=========================================="
echo "Teardown Complete!"
echo "=========================================="
echo ""
echo "All test resources have been destroyed."
echo ""
