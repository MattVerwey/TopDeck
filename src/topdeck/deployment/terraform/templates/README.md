# Terraform Templates for Multi-Cloud Deployment

This directory contains reusable Terraform templates for deploying infrastructure across Azure, AWS, and GCP. The templates are designed to support multiple cloud instances running simultaneously, allowing clients to manage resources across all three cloud providers.

## Directory Structure

```
templates/
├── azure/          # Azure-specific Terraform templates
│   ├── provider.tf # Azure provider configuration
│   ├── variables.tf # Reusable variables
│   └── main.tf     # Main resource definitions
├── aws/            # AWS-specific Terraform templates
│   ├── provider.tf # AWS provider configuration
│   ├── variables.tf # Reusable variables
│   └── main.tf     # Main resource definitions
└── gcp/            # GCP-specific Terraform templates
    ├── provider.tf # GCP provider configuration
    ├── variables.tf # Reusable variables
    └── main.tf     # Main resource definitions
```

## Features

### Multi-Cloud Support

All three cloud integrations can run simultaneously:
- **Azure**: Uses AzureRM provider with separate state backend
- **AWS**: Uses AWS provider with S3 backend
- **GCP**: Uses Google provider with GCS backend

### Separate State Management

Each cloud provider uses its own state backend:
- **Azure**: Azure Storage Account (`azurerm` backend)
- **AWS**: Amazon S3 with DynamoDB locking (`s3` backend)
- **GCP**: Google Cloud Storage (`gcs` backend)

### Consistent Variable Structure

All templates follow a consistent variable pattern:
- `environment`: Environment name (dev, staging, prod)
- `region/location`: Cloud-specific region
- `tags/labels`: Resource metadata
- Provider-specific ID (subscription_id, aws_account_id, project_id)

## Usage

### Azure Deployment

```bash
cd templates/azure

# Initialize Terraform
terraform init \
  -backend-config="storage_account_name=topdeckstate" \
  -backend-config="container_name=terraform-state" \
  -backend-config="key=azure/production.tfstate"

# Plan deployment
terraform plan \
  -var="subscription_id=your-subscription-id" \
  -var="resource_group_name=topdeck-prod" \
  -var="location=eastus" \
  -var="environment=prod"

# Apply deployment
terraform apply
```

### AWS Deployment

```bash
cd templates/aws

# Initialize Terraform
terraform init \
  -backend-config="bucket=topdeck-terraform-state-123456789012" \
  -backend-config="key=aws/production.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=topdeck-terraform-locks"

# Plan deployment
terraform plan \
  -var="aws_account_id=123456789012" \
  -var="region=us-east-1" \
  -var="environment=prod"

# Apply deployment
terraform apply
```

### GCP Deployment

```bash
cd templates/gcp

# Initialize Terraform
terraform init \
  -backend-config="bucket=topdeck-terraform-state-my-project" \
  -backend-config="prefix=gcp/production"

# Plan deployment
terraform plan \
  -var="project_id=my-project-123" \
  -var="region=us-central1" \
  -var="environment=prod"

# Apply deployment
terraform apply
```

## Running Multiple Cloud Instances

To manage infrastructure across all three clouds simultaneously:

1. **Set up separate state backends** for each cloud provider
2. **Use different working directories** for each cloud
3. **Configure credentials** for each provider:

```bash
# Azure
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"

# AWS
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# GCP
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export GCP_PROJECT_ID="my-project-123"
```

4. **Run Terraform in parallel** (optional):

```bash
# In separate terminals or CI/CD jobs
cd templates/azure && terraform apply -auto-approve &
cd templates/aws && terraform apply -auto-approve &
cd templates/gcp && terraform apply -auto-approve &
```

## Neo4j Integration

Resources deployed via these templates are automatically formatted for Neo4j storage:

### Resource Properties Format

All discovered resources include:
- `id`: Cloud-specific resource identifier (ARM ID, ARN, or GCP resource name)
- `name`: Human-readable name
- `resource_type`: Normalized type (e.g., "aks", "eks", "gke_cluster")
- `cloud_provider`: "azure", "aws", or "gcp"
- `region`: Cloud region
- `subscription_id`: Account/Project identifier
- `status`: Resource status (running, stopped, error, degraded, unknown)
- `environment`: Environment tag/label (prod, staging, dev)
- `tags`: Metadata as dictionary (normalized from cloud-specific formats)
- `properties`: Cloud-specific details as JSON string
- `discovered_at`: ISO timestamp
- `last_seen`: ISO timestamp

### Tag/Label Normalization

Each cloud provider handles metadata differently:
- **Azure**: Tags as `{key: value}` dict
- **AWS**: Tags as `[{Key: k, Value: v}]` list → normalized to dict
- **GCP**: Labels as `{key: value}` dict

All are converted to a consistent `{key: value}` dictionary format for Neo4j.

## State Backend Setup

### Azure Storage Backend

```bash
# Create storage account for Terraform state
az storage account create \
  --name topdeckstate \
  --resource-group topdeck-shared \
  --location eastus \
  --sku Standard_LRS

az storage container create \
  --name terraform-state \
  --account-name topdeckstate
```

### AWS S3 Backend

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket topdeck-terraform-state-123456789012 \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket topdeck-terraform-state-123456789012 \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name topdeck-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### GCP GCS Backend

```bash
# Create GCS bucket for Terraform state
gsutil mb -p my-project-123 \
  -l us-central1 \
  gs://topdeck-terraform-state-my-project

# Enable versioning
gsutil versioning set on gs://topdeck-terraform-state-my-project
```

## Testing with Azure 30-Day Trial

We provide comprehensive testing infrastructure for Azure with cost controls:

### Quick Start

```bash
# 1. Set up Azure trial
cd scripts/azure-testing
./setup-azure-trial.sh

# 2. Deploy test infrastructure
./deploy-test-infrastructure.sh

# 3. Validate deployment
./validate-deployment.sh

# 4. Run integration tests
pytest tests/integration/azure/ -v

# 5. Clean up
./teardown-test-infrastructure.sh
```

### Features

- **Cost Budget**: $50/month limit with email alerts
- **Minimal Resources**: < $5/month estimated cost
- **Test Resources**: Storage, VNet, Subnet, NSG
- **Integration Tests**: Comprehensive validation suite

See [docs/AZURE_TESTING_GUIDE.md](../../../../docs/AZURE_TESTING_GUIDE.md) for detailed instructions.

## Best Practices

1. **Separate State Files**: Use different state files for each environment and cloud
2. **State Locking**: Enable state locking to prevent concurrent modifications
3. **State Encryption**: Enable encryption at rest for all state backends
4. **Workspaces**: Use Terraform workspaces for environment isolation
5. **Variable Files**: Use `.tfvars` files for environment-specific values
6. **Modules**: Create reusable modules for common patterns
7. **Version Pinning**: Pin provider versions for consistency
8. **Cost Management**: Always enable budgets for test/dev environments
9. **Resource Cleanup**: Destroy test resources when not in use

## Extending Templates

To add new resource types:

1. Create a module in `modules/<resource-type>/`
2. Define variables, resources, and outputs
3. Reference the module in `main.tf`
4. Ensure Neo4j formatting in the resource discovery mapper

Example module structure:
```
modules/
└── aks/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    └── README.md
```

## Security Considerations

- Never commit `.tfstate` files to version control
- Use encrypted state backends
- Implement least-privilege IAM policies
- Use service principals/roles for CI/CD
- Rotate credentials regularly
- Enable audit logging for all Terraform operations
