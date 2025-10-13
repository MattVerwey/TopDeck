# Multi-Cloud Configuration Guide

TopDeck supports running Azure, AWS, and GCP integrations simultaneously, allowing clients with multiple cloud instances to discover and manage resources across all three platforms.

## Overview

All three cloud providers can be configured and run concurrently:
- **Azure**: Resource discovery, DevOps integration, Terraform deployment
- **AWS**: Resource discovery, Terraform deployment
- **GCP**: Resource discovery, Terraform deployment

Each cloud provider:
- Has its own discovery module with consistent API
- Formats data properly for Neo4j storage
- Can run independently or alongside other providers
- Maintains separate Terraform state

## Configuration

### Environment Variables

Configure all three cloud providers via environment variables:

```bash
# Azure Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id

# Azure DevOps (optional)
AZURE_DEVOPS_ORGANIZATION=your-org
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_PAT=your-personal-access-token

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# GCP Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id

# Neo4j (shared across all clouds)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Feature Flags (enable/disable per cloud)
ENABLE_AZURE_DISCOVERY=true
ENABLE_AWS_DISCOVERY=true
ENABLE_GCP_DISCOVERY=true
```

### .env File

Create a `.env` file in the project root:

```bash
# Application
APP_ENV=production
APP_PORT=8000

# Azure
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=87654321-4321-4321-4321-210987654321
AZURE_CLIENT_SECRET=your-secret
AZURE_SUBSCRIPTION_ID=11111111-2222-3333-4444-555555555555

# AWS
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# GCP
GOOGLE_APPLICATION_CREDENTIALS=/etc/topdeck/gcp-credentials.json
GCP_PROJECT_ID=my-project-123

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=secure-password

# Enable all clouds
ENABLE_AZURE_DISCOVERY=true
ENABLE_AWS_DISCOVERY=true
ENABLE_GCP_DISCOVERY=true
```

## Running Discovery for All Clouds

### Python API

```python
from topdeck.discovery.azure import AzureDiscoverer
from topdeck.discovery.aws import AWSDiscoverer
from topdeck.discovery.gcp import GCPDiscoverer
from topdeck.storage.neo4j_client import Neo4jClient
from topdeck.common.config import Settings
import asyncio

# Load configuration
settings = Settings()

# Initialize Neo4j client
neo4j = Neo4jClient(
    settings.neo4j_uri,
    settings.neo4j_username,
    settings.neo4j_password
)
neo4j.connect()

async def discover_all_clouds():
    """Discover resources from all enabled cloud providers"""
    
    results = {}
    
    # Azure discovery
    if settings.enable_azure_discovery:
        azure = AzureDiscoverer(
            subscription_id=settings.azure_subscription_id,
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret
        )
        results['azure'] = await azure.discover_all_resources()
        print(f"Azure: Found {len(results['azure'].resources)} resources")
    
    # AWS discovery
    if settings.enable_aws_discovery:
        aws = AWSDiscoverer(
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
            region=settings.aws_region
        )
        results['aws'] = await aws.discover_all_resources()
        print(f"AWS: Found {len(results['aws'].resources)} resources")
    
    # GCP discovery
    if settings.enable_gcp_discovery:
        gcp = GCPDiscoverer(
            project_id=settings.gcp_project_id,
            credentials_path=settings.google_application_credentials
        )
        results['gcp'] = await gcp.discover_all_resources()
        print(f"GCP: Found {len(results['gcp'].resources)} resources")
    
    # Store all resources in Neo4j
    for cloud, result in results.items():
        for resource in result.resources:
            neo4j.upsert_resource(resource.to_neo4j_properties())
        print(f"Stored {len(result.resources)} {cloud} resources in Neo4j")
    
    return results

# Run discovery
asyncio.run(discover_all_clouds())
```

### Parallel Discovery

Run discovery in parallel for faster execution:

```python
async def discover_parallel():
    """Discover from all clouds in parallel"""
    tasks = []
    
    if settings.enable_azure_discovery:
        azure = AzureDiscoverer(...)
        tasks.append(azure.discover_all_resources())
    
    if settings.enable_aws_discovery:
        aws = AWSDiscoverer(...)
        tasks.append(aws.discover_all_resources())
    
    if settings.enable_gcp_discovery:
        gcp = GCPDiscoverer(...)
        tasks.append(gcp.discover_all_resources())
    
    # Run all discoveries in parallel
    results = await asyncio.gather(*tasks)
    return results
```

## Neo4j Data Model

All resources are stored in Neo4j with a consistent schema:

### Resource Node Properties

```cypher
CREATE (r:Resource {
    id: "cloud-specific-id",           // ARN, ARM ID, or GCP resource name
    name: "resource-name",
    resource_type: "normalized-type",   // eks, aks, gke_cluster, etc.
    cloud_provider: "azure|aws|gcp",
    region: "region-name",
    subscription_id: "account-id",      // Subscription ID, Account ID, or Project ID
    status: "running|stopped|error|degraded|unknown",
    environment: "prod|staging|dev",
    tags: {...},                        // Normalized to dict format
    properties: "{...}",                // Cloud-specific props as JSON
    discovered_at: "2024-01-01T12:00:00",
    last_seen: "2024-01-01T12:00:00"
})
```

### Querying Multi-Cloud Resources

```cypher
-- All resources across all clouds
MATCH (r:Resource)
RETURN r.cloud_provider, r.resource_type, count(*) as count
ORDER BY count DESC

-- Resources by cloud provider
MATCH (r:Resource {cloud_provider: "aws"})
RETURN r

-- Resources by environment across all clouds
MATCH (r:Resource {environment: "production"})
RETURN r.cloud_provider, r.name, r.resource_type

-- Compare same resource types across clouds
MATCH (r:Resource)
WHERE r.resource_type IN ["eks", "aks", "gke_cluster"]
RETURN r.cloud_provider, r.name, r.region, r.status
```

## Tag/Label Normalization

Each cloud provider handles metadata differently, but TopDeck normalizes all to a consistent format:

### Azure Tags
```python
# Input (Azure)
tags = {
    "Environment": "production",
    "Application": "web"
}

# Output (Neo4j)
tags = {"Environment": "production", "Application": "web"}  # Dict format
```

### AWS Tags
```python
# Input (AWS)
tags = [
    {"Key": "Environment", "Value": "production"},
    {"Key": "Application", "Value": "web"}
]

# Output (Neo4j)
tags = {"Environment": "production", "Application": "web"}  # Normalized to dict
```

### GCP Labels
```python
# Input (GCP)
labels = {
    "environment": "production",
    "application": "web"
}

# Output (Neo4j)
tags = {"environment": "production", "application": "web"}  # Already dict format
```

## Selective Cloud Discovery

You can selectively enable/disable clouds:

```bash
# Only Azure
ENABLE_AZURE_DISCOVERY=true
ENABLE_AWS_DISCOVERY=false
ENABLE_GCP_DISCOVERY=false

# Azure and AWS only
ENABLE_AZURE_DISCOVERY=true
ENABLE_AWS_DISCOVERY=true
ENABLE_GCP_DISCOVERY=false

# All clouds (default)
ENABLE_AZURE_DISCOVERY=true
ENABLE_AWS_DISCOVERY=true
ENABLE_GCP_DISCOVERY=true
```

## Terraform Multi-Cloud Deployment

Deploy infrastructure to all three clouds using separate Terraform configurations:

```bash
# Set up credentials
export ARM_SUBSCRIPTION_ID="azure-sub-id"
export AWS_ACCESS_KEY_ID="aws-key"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-creds.json"

# Deploy to Azure
cd src/topdeck/deployment/terraform/templates/azure
terraform init
terraform apply -var="subscription_id=$ARM_SUBSCRIPTION_ID"

# Deploy to AWS
cd ../aws
terraform init
terraform apply -var="aws_account_id=123456789012"

# Deploy to GCP
cd ../gcp
terraform init
terraform apply -var="project_id=my-project-123"
```

## Monitoring and Health Checks

Monitor discovery status across all clouds:

```python
from topdeck.discovery.azure import AzureDiscoverer
from topdeck.discovery.aws import AWSDiscoverer
from topdeck.discovery.gcp import GCPDiscoverer

async def health_check():
    """Check health of all cloud integrations"""
    status = {}
    
    if settings.enable_azure_discovery:
        try:
            azure = AzureDiscoverer(...)
            account_id = azure.get_account_id()
            status['azure'] = 'healthy' if account_id else 'unhealthy'
        except Exception as e:
            status['azure'] = f'error: {str(e)}'
    
    if settings.enable_aws_discovery:
        try:
            aws = AWSDiscoverer(...)
            account_id = aws.get_account_id()
            status['aws'] = 'healthy' if account_id else 'unhealthy'
        except Exception as e:
            status['aws'] = f'error: {str(e)}'
    
    if settings.enable_gcp_discovery:
        try:
            gcp = GCPDiscoverer(...)
            project_num = gcp.get_project_number()
            status['gcp'] = 'healthy' if project_num else 'unhealthy'
        except Exception as e:
            status['gcp'] = f'error: {str(e)}'
    
    return status
```

## Best Practices

1. **Credential Management**
   - Use separate credentials for each cloud
   - Store credentials securely (environment variables, secrets manager)
   - Rotate credentials regularly

2. **Resource Tagging**
   - Use consistent tag/label keys across clouds
   - Always include "environment" tag/label
   - Use lowercase keys for consistency

3. **State Management**
   - Use separate Terraform state backends per cloud
   - Enable state locking to prevent conflicts
   - Backup state files regularly

4. **Discovery Scheduling**
   - Run discovery on a schedule (e.g., hourly)
   - Stagger discovery across clouds to reduce load
   - Monitor discovery duration and errors

5. **Neo4j Performance**
   - Create indexes on commonly queried fields
   - Use batch upserts for large datasets
   - Clean up old/stale resources periodically

## Troubleshooting

### Azure Discovery Issues
```bash
# Test Azure credentials
az login
az account show

# Verify permissions
az role assignment list --assignee $AZURE_CLIENT_ID
```

### AWS Discovery Issues
```bash
# Test AWS credentials
aws sts get-caller-identity

# Verify permissions
aws iam get-user
```

### GCP Discovery Issues
```bash
# Test GCP credentials
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS

# Verify project access
gcloud projects describe $GCP_PROJECT_ID
```

## See Also

- [Azure Discovery README](../src/topdeck/discovery/azure/README.md)
- [AWS Discovery README](../src/topdeck/discovery/aws/README.md)
- [GCP Discovery README](../src/topdeck/discovery/gcp/README.md)
- [Terraform Templates README](../src/topdeck/deployment/terraform/templates/README.md)
