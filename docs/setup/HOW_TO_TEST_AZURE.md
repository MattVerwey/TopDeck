# How to Test Azure with TopDeck

**Quick guide for testing TopDeck's Azure discovery features using a 30-day trial**

## Why This Approach?

As discussed, we want to:
- ✅ Use Terraform/ARM templates for infrastructure
- ✅ Create a 30-day trial subscription
- ✅ Ensure we don't spend money with cost budgets
- ✅ Deploy infrastructure and test TopDeck

This implementation delivers exactly that!

## What You Get

1. **Terraform Templates** - Infrastructure as code for Azure
2. **Cost Budget** - $50/month limit with email alerts
3. **Test Resources** - Minimal infrastructure (< $5/month)
4. **Deployment Scripts** - Automated setup and teardown
5. **Integration Tests** - Validate everything works

## Setup Time

- **Initial setup**: 10-15 minutes
- **Daily deploy**: 3-5 minutes
- **Daily teardown**: 2-3 minutes

## Step-by-Step Guide

### 1. Prerequisites

Install required tools:

```bash
# macOS
brew install azure-cli terraform

# Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Windows (with Chocolatey)
choco install azure-cli terraform
```

### 2. Get Azure 30-Day Trial

1. Go to https://azure.microsoft.com/free/
2. Click "Start free"
3. Sign in with Microsoft account
4. Complete verification (credit card required but won't be charged)

**You get**:
- $200 credit for 30 days
- Free services for 12 months
- Always-free services

### 3. Run Setup Script

```bash
cd scripts/azure-testing
./setup-azure-trial.sh
```

**What it does**:
- Verifies Azure login
- Creates resource group for Terraform state
- Sets up storage account
- Configures environment

**You'll be prompted for**:
- Email for budget alerts
- Monthly budget limit (recommend: $50)

**Output**:
- Creates `azure-setup.env` with your configuration

### 4. Configure Test Variables

```bash
cd ../../src/topdeck/deployment/terraform/templates/azure
cp test.tfvars.example test.tfvars
nano test.tfvars  # or use your preferred editor
```

**Update these values**:
```hcl
subscription_id = "your-subscription-id-from-setup"
budget_alert_emails = ["your-email@example.com"]
```

**Optional settings**:
```hcl
monthly_budget_amount = 50  # Adjust if needed
create_test_resources = true  # Set false to skip test resources
```

### 5. Deploy Test Infrastructure

```bash
cd scripts/azure-testing
source azure-setup.env  # Load configuration
./deploy-test-infrastructure.sh
```

**What gets created**:
- Resource Group: `topdeck-test-rg`
- Cost Budget: $50/month with alerts
- Storage Account: For testing discovery (~$0.15/month)
- Virtual Network: For testing networking (free)
- Subnet: For testing subnets (free)
- Network Security Group: For testing security (free)

**Runtime**: 3-5 minutes

### 6. Validate Deployment

```bash
./validate-deployment.sh
```

**This checks**:
- ✓ Resource group exists
- ✓ Storage account created
- ✓ Virtual network configured
- ✓ Network security group active
- ✓ Cost budget enabled
- ✓ All resources properly tagged

### 7. Set Up Service Principal for TopDeck

```bash
az ad sp create-for-rbac --name "TopDeckTesting" \
  --role "Reader" \
  --scopes "/subscriptions/$ARM_SUBSCRIPTION_ID"
```

**Save the output**:
```json
{
  "appId": "your-client-id",
  "password": "your-client-secret",
  "tenant": "your-tenant-id"
}
```

### 8. Configure TopDeck

```bash
cd /home/runner/work/TopDeck/TopDeck
cp .env.example .env
```

**Edit .env**:
```ini
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

### 9. Run Integration Tests

```bash
# Set environment variables
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export TEST_RESOURCE_GROUP="topdeck-test-rg"

# Run tests
pytest tests/integration/azure/ -v -m integration
```

**Expected results**:
```
tests/integration/azure/test_infrastructure.py::test_resource_group_exists PASSED
tests/integration/azure/test_infrastructure.py::test_storage_account_discovery PASSED
tests/integration/azure/test_infrastructure.py::test_virtual_network_discovery PASSED
tests/integration/azure/test_infrastructure.py::test_network_security_group_discovery PASSED
tests/integration/azure/test_infrastructure.py::test_all_resources_discovery PASSED
tests/integration/azure/test_infrastructure.py::test_resource_tags PASSED
tests/integration/azure/test_infrastructure.py::test_resource_permissions PASSED

======= 7 passed in 10.23s =======
```

### 10. Test TopDeck Discovery

```python
from topdeck.discovery.azure.discoverer import AzureDiscoverer
from azure.identity import ClientSecretCredential
import asyncio
import os

async def test_discovery():
    credential = ClientSecretCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET")
    )
    
    discoverer = AzureDiscoverer(
        credential=credential,
        subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID")
    )
    
    print("Discovering Azure resources...")
    resources = await discoverer.discover_all()
    
    print(f"\nFound {len(resources)} resources:")
    for resource in resources:
        print(f"  - {resource.name} ({resource.resource_type})")
    
    await discoverer.close()

asyncio.run(test_discovery())
```

### 11. Clean Up (IMPORTANT!)

When done testing, **always clean up** to avoid charges:

```bash
cd scripts/azure-testing
./teardown-test-infrastructure.sh
```

**This destroys**:
- All test resources
- Resource group
- Stops all costs

**Keeps**:
- Shared resource group (for state)
- Storage account (minimal cost ~$0.15/month)

**To completely clean up**:
```bash
# Delete service principal
az ad sp delete --id your-client-id

# (Optional) Delete shared resources
az group delete --name topdeck-shared --yes
```

## Cost Management

### How Cost Budget Works

The Terraform templates automatically create a budget with:

- **Limit**: $50/month (configurable)
- **Alerts**:
  - 80% threshold → Warning email
  - 100% threshold → Critical email

**Budget settings in test.tfvars**:
```hcl
enable_cost_budget = true
monthly_budget_amount = 50
budget_alert_emails = ["your-email@example.com"]
```

### Monitor Costs

#### Via Azure Portal
1. Go to https://portal.azure.com
2. Navigate to "Cost Management + Billing"
3. View spending and forecasts

#### Via Azure CLI
```bash
# Current spending
az consumption usage list --start-date 2025-10-01

# Budget status
az consumption budget list

# By resource group
az consumption usage list --resource-group topdeck-test-rg
```

### Estimated Costs

| Scenario | Daily Cost | Monthly Cost |
|----------|-----------|--------------|
| No test resources | $0.00 | $0.00 |
| Test resources running 24/7 | ~$0.15 | ~$4.50 |
| Test resources 8 hours/day | ~$0.05 | ~$1.50 |

**Recommendation**: Deploy only when testing, destroy after.

## Daily Workflow

### Morning - Deploy

```bash
cd scripts/azure-testing
source azure-setup.env
./deploy-test-infrastructure.sh
```

### During Day - Test

```bash
# Run TopDeck discovery
python your_test_script.py

# Run integration tests
pytest tests/integration/azure/ -v

# Make changes to TopDeck
# Test again
```

### Evening - Clean Up

```bash
cd scripts/azure-testing
./teardown-test-infrastructure.sh
```

**Result**: Minimal costs (hours instead of days)

## Troubleshooting

### "Not logged in to Azure"

```bash
az login
az account show
```

### "Terraform not initialized"

```bash
cd src/topdeck/deployment/terraform/templates/azure
terraform init
```

### "Storage account name not available"

Storage names must be globally unique. Edit `test.tfvars`:
```hcl
# Change the resource group name to make storage name unique
resource_group_name = "topdeck-test-yourname-rg"
```

### Budget alerts not received

- Check spam folder
- Verify email in test.tfvars
- Allow up to 24 hours for activation
- Check Azure Portal → Cost Management → Budgets

### Tests failing

```bash
# Check Azure credentials
az account show

# Verify resources exist
az resource list --resource-group topdeck-test-rg

# Check service principal permissions
az role assignment list --assignee your-client-id
```

## Tips for Success

### Cost Control
1. **Set conservative budget** - Start with $20-30 if worried
2. **Destroy daily** - Only keep resources when testing
3. **Monitor weekly** - Check costs in Azure Portal
4. **Disable test resources** - Set `create_test_resources = false` if not needed

### Testing
1. **Start minimal** - Basic resources first
2. **Test incrementally** - Add complexity gradually
3. **Validate changes** - Run validate script after each change
4. **Use integration tests** - Automate validation

### Security
1. **Reader role only** - Service principal doesn't need more
2. **Rotate credentials** - Change every 90 days
3. **Use environment variables** - Never commit credentials
4. **Delete when done** - Remove service principal after testing

## What's Next?

After successful testing, you can:

1. **Add more resources** - VMs, AKS, App Services, etc.
2. **Test different scenarios** - Multi-region, multiple RGs
3. **Integrate with CI/CD** - Automate testing
4. **Expand to other clouds** - AWS and GCP templates available

## Additional Resources

- **Full Guide**: [AZURE_TESTING_GUIDE.md](AZURE_TESTING_GUIDE.md)
- **Quick Reference**: [AZURE_TRIAL_SETUP.md](AZURE_TRIAL_SETUP.md)
- **Implementation Details**: [AZURE_TESTING_SUMMARY.md](archive/AZURE_TESTING_SUMMARY.md)
- **Scripts Documentation**: [scripts/azure-testing/README.md](../scripts/azure-testing/README.md)

## Support

If you have issues:

1. Check the troubleshooting section above
2. Review detailed guides in `docs/`
3. Check Azure Portal for error details
4. Open a GitHub issue with logs

## Summary

This testing approach gives you:

✅ **Safe Testing** - Budget alerts prevent overspending  
✅ **Quick Setup** - 10-15 minutes to get started  
✅ **Minimal Cost** - < $5/month with daily teardown  
✅ **Automated** - Scripts handle deployment/cleanup  
✅ **Validated** - Integration tests confirm everything works  
✅ **Documented** - Comprehensive guides for all scenarios  

**Remember**: Always run `./teardown-test-infrastructure.sh` when done testing!

---

**Total time to test**: Setup once (15 min) + Deploy/Test/Teardown daily (15 min/day)  
**Cost per month**: < $5 with test resources, < $1 with daily teardown  
**Safety**: Budget alerts at 80% and 100%, email notifications
