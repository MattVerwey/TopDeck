# Azure 30-Day Trial Testing Setup - Quick Reference

This is a quick reference guide for setting up Azure testing with a 30-day trial. For detailed information, see [AZURE_TESTING_GUIDE.md](AZURE_TESTING_GUIDE.md).

## Overview

This setup allows you to:
- ✅ Test Azure infrastructure deployment with Terraform
- ✅ Validate TopDeck resource discovery
- ✅ Control costs with budget alerts ($50/month limit)
- ✅ Use Azure's $200 free credit
- ✅ Deploy minimal test resources (< $5/month)

## Prerequisites

```bash
# Install required tools
brew install azure-cli terraform  # macOS
# or
apt-get install azure-cli terraform  # Linux
# or
choco install azure-cli terraform  # Windows
```

## Quick Setup (5 minutes)

### 1. Sign up for Azure Free Trial

Visit: https://azure.microsoft.com/free/

You'll get:
- $200 credit for 30 days
- Free services for 12 months
- Always-free tier services

### 2. Run Setup Scripts

```bash
cd scripts/azure-testing

# Configure Azure subscription and Terraform state
./setup-azure-trial.sh
# Enter your email and budget limit when prompted

# Load environment variables
source azure-setup.env

# Configure test variables
cd ../../src/topdeck/deployment/terraform/templates/azure
cp test.tfvars.example test.tfvars
# Edit test.tfvars with your subscription ID and email

# Deploy test infrastructure
cd -
./deploy-test-infrastructure.sh

# Validate deployment
./validate-deployment.sh
```

### 3. Test TopDeck Discovery

```bash
# Create service principal
az ad sp create-for-rbac --name "TopDeckTesting" \
  --role "Reader" \
  --scopes "/subscriptions/$ARM_SUBSCRIPTION_ID"

# Configure TopDeck
cd /home/runner/work/TopDeck/TopDeck
cp .env.example .env
# Add Azure credentials to .env

# Run integration tests
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

pytest tests/integration/azure/ -v -m integration
```

### 4. Cleanup

```bash
# Destroy test resources
cd scripts/azure-testing
./teardown-test-infrastructure.sh

# (Optional) Delete shared resources
az group delete --name topdeck-shared --yes
```

## What Gets Created

### Infrastructure

1. **Resource Group** (`topdeck-test-rg`)
   - Container for all test resources
   - Tagged with "ManagedBy: TopDeck"

2. **Cost Budget** (Optional, recommended)
   - $50/month limit (configurable)
   - Email alerts at 80% and 100%

3. **Test Resources** (Optional, < $5/month)
   - Storage Account (~$0.15/month)
   - Virtual Network (Free)
   - Subnet (Free)
   - Network Security Group (Free)

### Terraform State

- Storage Account: `topdeckstate[xxx]`
- Container: `terraform-state`
- Resource Group: `topdeck-shared`

## Cost Management

### Budget Settings

Default configuration in `test.tfvars`:
```hcl
enable_cost_budget   = true
monthly_budget_amount = 50  # USD
budget_alert_emails  = ["your-email@example.com"]
```

### Monitor Costs

```bash
# View current spending
az consumption usage list --start-date 2025-10-01

# Check budget status
az consumption budget list

# Via Azure Portal
open https://portal.azure.com/#view/Microsoft_Azure_CostManagement
```

### Cost-Saving Tips

1. **Destroy resources when not in use**
   ```bash
   ./teardown-test-infrastructure.sh
   ```

2. **Enable only what you need**
   ```hcl
   create_test_resources = false  # Don't create storage/networking
   ```

3. **Monitor daily during first week**

4. **Set conservative budget**
   ```hcl
   monthly_budget_amount = 20  # Very safe limit
   ```

## Testing Workflow

### Daily Development Cycle

```bash
# Morning - Deploy resources
cd scripts/azure-testing
./deploy-test-infrastructure.sh

# Test TopDeck features
# ... your development work ...

# Evening - Clean up to save costs
./teardown-test-infrastructure.sh
```

### Integration Testing

```bash
# Set up environment
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."
export AZURE_SUBSCRIPTION_ID="..."
export TEST_RESOURCE_GROUP="topdeck-test-rg"

# Run tests
pytest tests/integration/azure/ -v -m integration

# Expected output:
# test_resource_group_exists ... PASSED
# test_storage_account_discovery ... PASSED
# test_virtual_network_discovery ... PASSED
# test_network_security_group_discovery ... PASSED
# test_all_resources_discovery ... PASSED
```

## Scripts Reference

| Script | Purpose | Runtime |
|--------|---------|---------|
| `setup-azure-trial.sh` | Initial Azure setup | 2-3 min |
| `deploy-test-infrastructure.sh` | Deploy resources | 3-5 min |
| `validate-deployment.sh` | Verify deployment | 30 sec |
| `teardown-test-infrastructure.sh` | Destroy resources | 2-3 min |

## Common Issues

### "Not logged in to Azure"

```bash
az login
az account show
```

### "Quota exceeded"

Trial subscriptions have limited quotas. Use minimal resources:
```hcl
create_test_resources = false
```

### "Storage account name not available"

Choose a unique name in `test.tfvars`:
```hcl
# Storage names must be globally unique
# Default: topdeck{env}test
```

### Budget alerts not received

- Check spam folder
- Verify email in test.tfvars
- Allow 24 hours for activation

## Best Practices

### ✅ Do This

- Set budget to $20-50 for safety
- Destroy resources daily when not testing
- Monitor costs in first week
- Use free tier resources (VNet, NSG)
- Keep credentials secure (never commit)

### ❌ Avoid This

- Creating expensive resources (VMs, AKS)
- Leaving resources running overnight
- Storing state files in git
- Using production credentials for testing
- Ignoring budget alerts

## Support

- **Full Guide:** [AZURE_TESTING_GUIDE.md](AZURE_TESTING_GUIDE.md)
- **Scripts README:** [scripts/azure-testing/README.md](../scripts/azure-testing/README.md)
- **Terraform Docs:** [terraform/templates/README.md](../src/topdeck/deployment/terraform/templates/README.md)

## Security Notes

1. **Service Principal Permissions**
   - Use Reader role for discovery
   - Never use Owner or Contributor for testing

2. **Credential Management**
   - Store in environment variables
   - Use `.env` files (gitignored)
   - Rotate every 90 days

3. **Resource Access**
   - Network security groups restrict access
   - No public endpoints created
   - Resources isolated in test RG

## Architecture

```
Azure Subscription (Trial)
├── topdeck-shared (RG)
│   └── topdeckstate{xxx} (Storage Account)
│       └── terraform-state (Container)
│           └── *.tfstate (Terraform State)
└── topdeck-test-rg (RG)
    ├── Cost Budget ($50/month)
    ├── Storage Account (Test)
    ├── Virtual Network
    │   └── Subnet
    └── Network Security Group
```

## Next Steps

After successful testing:

1. **Explore more resources**
   - Add AKS cluster (for Kubernetes testing)
   - Add App Service (for PaaS testing)
   - Add SQL Database (for data testing)

2. **Integrate with TopDeck**
   - Test resource discovery
   - Test dependency mapping
   - Test risk analysis

3. **Optimize costs**
   - Review actual spending
   - Adjust budget if needed
   - Use auto-shutdown for VMs

4. **Plan for production**
   - Upgrade to Pay-As-You-Go
   - Use separate subscriptions
   - Implement tagging strategy

---

**Remember:** Always destroy resources when not in use to minimize costs!

**Total setup time:** ~10-15 minutes  
**Estimated monthly cost:** < $5 with test resources, $0 without
