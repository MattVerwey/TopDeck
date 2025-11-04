# Azure Testing Infrastructure Guide

This guide explains how to set up an Azure 30-day trial subscription and deploy test infrastructure for TopDeck with cost controls.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setting Up Azure Trial](#setting-up-azure-trial)
- [Deploying Test Infrastructure](#deploying-test-infrastructure)
- [Cost Management](#cost-management)
- [Testing TopDeck Discovery](#testing-topdeck-discovery)
- [Cleanup](#cleanup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have:

1. **Azure CLI** - [Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Terraform** (>= 1.0) - [Install](https://www.terraform.io/downloads)
3. **An email address** for budget alerts
4. **Credit card** for Azure trial signup (won't be charged within free tier)

## Setting Up Azure Trial

### Step 1: Sign up for Azure Free Trial

1. Go to [https://azure.microsoft.com/free/](https://azure.microsoft.com/free/)
2. Click "Start free"
3. Sign in with your Microsoft account (or create one)
4. Provide your details and credit card information
5. Complete the verification process

**What you get:**
- $200 credit for 30 days
- Free services for 12 months
- Always-free services

### Step 2: Run the Setup Script

The setup script will:
- Verify your Azure login
- Create a resource group for shared resources
- Set up a storage account for Terraform state
- Configure your environment

```bash
cd scripts/azure-testing
./setup-azure-trial.sh
```

Follow the prompts to:
- Enter your email for budget alerts
- Set a monthly budget limit (recommended: $50 or less)

The script will create an `azure-setup.env` file with your configuration.

### Step 3: Load Your Configuration

```bash
source azure-setup.env
```

This sets up environment variables for Azure and Terraform.

## Deploying Test Infrastructure

### What Will Be Created

The test infrastructure includes minimal resources for testing TopDeck:

1. **Resource Group** - Container for all resources
2. **Cost Budget** - $50/month limit with alerts at 80% and 100%
3. **Storage Account** - For testing storage discovery (minimal cost)
4. **Virtual Network** - For testing network discovery (free)
5. **Subnet** - For testing subnet discovery (free)
6. **Network Security Group** - For testing security discovery (free)

**Estimated monthly cost: < $5** (mostly storage, ~$0.15/month)

### Step 1: Configure Variables

Edit the test variables file:

```bash
cd src/topdeck/deployment/terraform/templates/azure
cp test.tfvars.example test.tfvars
nano test.tfvars  # or use your preferred editor
```

Update these values:
```hcl
subscription_id      = "your-subscription-id"
budget_alert_emails  = ["your-email@example.com"]
```

### Step 2: Deploy Infrastructure

```bash
cd scripts/azure-testing
./deploy-test-infrastructure.sh
```

This script will:
1. Initialize Terraform
2. Validate the configuration
3. Show you a plan of what will be created
4. Ask for confirmation
5. Deploy the resources

Review the plan carefully before confirming!

### Step 3: Validate Deployment

```bash
./validate-deployment.sh
```

This will verify that all resources were created correctly.

## Cost Management

### Budget Alerts

The deployment creates a cost budget with two alert thresholds:

- **80%** - Warning alert
- **100%** - Critical alert

You'll receive emails at these thresholds.

### Monitoring Costs

#### Via Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Cost Management + Billing"
3. View your spending and forecasts

#### Via Azure CLI

```bash
# View current costs
az consumption usage list --start-date 2025-10-01

# View budget status
az consumption budget list
```

### Cost-Saving Tips

1. **Destroy resources when not in use**
   ```bash
   cd scripts/azure-testing
   ./teardown-test-infrastructure.sh
   ```

2. **Use the Free Tier**
   - Storage: First 5GB free
   - Bandwidth: First 15GB outbound free
   - Virtual Network: Always free

3. **Set up auto-shutdown** (for VMs if you add them)

4. **Monitor daily** in the first week to catch any unexpected charges

## Testing TopDeck Discovery

Once infrastructure is deployed, you can test TopDeck's Azure discovery:

### 1. Set Up Service Principal

Create a service principal for TopDeck:

```bash
az ad sp create-for-rbac --name "TopDeckTesting" \
  --role "Reader" \
  --scopes "/subscriptions/$ARM_SUBSCRIPTION_ID"
```

Save the output (client_id, client_secret, tenant_id).

### 2. Configure TopDeck

Create a `.env` file:

```bash
cd /home/runner/work/TopDeck/TopDeck
cp .env.example .env
```

Add your Azure credentials:

```ini
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

### 3. Run Discovery

```python
from topdeck.discovery.azure.discoverer import AzureDiscoverer
from azure.identity import ClientSecretCredential
import asyncio

async def test_discovery():
    credential = ClientSecretCredential(
        tenant_id="your-tenant-id",
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    
    discoverer = AzureDiscoverer(
        credential=credential,
        subscription_id="your-subscription-id"
    )
    
    # Discover resources
    resources = await discoverer.discover_all()
    
    print(f"Found {len(resources)} resources:")
    for resource in resources:
        print(f"  - {resource.name} ({resource.resource_type})")
    
    await discoverer.close()

asyncio.run(test_discovery())
```

### 4. Run Integration Tests

```bash
# Set up environment
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

# Run tests
pytest tests/integration/azure/ -v
```

## Cleanup

### Destroy Test Resources

When you're done testing:

```bash
cd scripts/azure-testing
./teardown-test-infrastructure.sh
```

This removes all test resources to stop any charges.

### Delete Service Principal

```bash
az ad sp delete --id your-client-id
```

### Keep or Delete Shared Resources

The shared resource group (`topdeck-shared`) contains the Terraform state storage:

**To keep it** (for future testing):
```bash
# No action needed - minimal cost (~$0.15/month)
```

**To delete it** (complete cleanup):
```bash
az group delete --name topdeck-shared --yes --no-wait
```

## Troubleshooting

### Authentication Issues

**Problem:** `az login` fails

**Solution:**
1. Clear cached credentials: `az account clear`
2. Try again: `az login`
3. Use device code flow: `az login --use-device-code`

### Terraform Errors

**Problem:** Terraform fails with "Storage account name not available"

**Solution:** Storage account names must be globally unique. Edit `test.tfvars` and choose a different name.

**Problem:** "Subscription not found"

**Solution:** 
1. Verify you're logged in: `az account show`
2. List subscriptions: `az account list`
3. Set the correct subscription: `az account set --subscription "your-subscription-id"`

### Budget Alerts Not Received

**Problem:** Not receiving budget alert emails

**Solution:**
1. Check your spam folder
2. Verify email in Azure Portal → Cost Management → Budgets
3. Budget alerts can take up to 24 hours to activate

### Quota Exceeded

**Problem:** "Quota exceeded for resource type"

**Solution:** Trial subscriptions have limited quotas. The test resources are designed to fit within free tier limits. If you hit limits:
1. Choose a different region
2. Reduce the number of resources in `test.tfvars`

### Cost Concerns

**Problem:** Worried about unexpected costs

**Solution:**
1. Set budget to $10-20 (very conservative)
2. Check costs daily: `az consumption usage list`
3. Set up billing alerts in Azure Portal
4. Destroy resources immediately after testing

## Best Practices

### For 30-Day Trial Testing

1. **Set aggressive budgets** - $20-50 max
2. **Destroy resources daily** - Only keep them when actively testing
3. **Monitor the first week closely** - Catch any issues early
4. **Use Free Tier resources** - VNets, NSGs, etc.
5. **Avoid expensive resources** - No VMs, AKS clusters, or databases unless necessary

### For Production Testing

After the trial period, if continuing:

1. **Upgrade to Pay-As-You-Go** for better quotas
2. **Use separate subscriptions** for dev/test/prod
3. **Implement resource tagging** for cost allocation
4. **Set up auto-shutdown** for development resources
5. **Review costs monthly** and optimize

## Additional Resources

- [Azure Free Account FAQ](https://azure.microsoft.com/en-us/free/free-account-faq/)
- [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
- [Azure Cost Management](https://docs.microsoft.com/en-us/azure/cost-management-billing/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review Azure Portal for detailed error messages
3. Check Terraform state: `terraform show`
4. Open an issue on GitHub with details

---

**Remember:** Always destroy test resources when not in use to minimize costs!
