# AKS Code Repository Scanning

## Overview

The TopDeck code repository scanner fully supports **AKS (Azure Kubernetes Service) clusters** as deployment targets. Since most Infrastructure as Code (IaC) deployments target AKS instead of App Services, the scanner is designed to map code repositories to AKS clusters and discover their dependencies.

## How It Works

### 1. Resource Discovery
The scanner discovers both:
- **App Services** (`resource_type == "app_service"`)
- **AKS Clusters** (`resource_type == "aks"`)

### 2. Repository-to-Cluster Mapping
When scanning Azure DevOps repositories, the scanner matches them to compute resources using:

1. **Tag-based matching**: Checks if resource has `repository` or `repo_url` tag matching the repo URL
2. **Name-based matching**: Matches repository name to resource name patterns
   - Example: Repository `customer-api` matches AKS cluster `prod-customer-api-aks`
   - Example: Repository `payment-service` matches `aks-payment-service-prod`

### 3. Priority Order
The scanner tries to match repositories in this order:
1. **App Services first** - For traditional web apps
2. **AKS Clusters second** - For containerized workloads (most common)

This ensures proper matching even in hybrid environments.

## Scanning Modes

### Single Project Mode
```bash
POST /api/v1/discovery/scan-repositories
```

Scans the configured Azure DevOps project and links repositories to:
- App Services
- AKS clusters

### All Projects Mode
```bash
POST /api/v1/discovery/scan-repositories?scan_all_projects=true
```

Scans **all projects** in your Azure DevOps organization and automatically:
1. Discovers Service Bus references in code
2. Matches repositories to App Services and AKS clusters
3. Creates dependencies in Neo4j

## What Gets Discovered

The scanner finds Service Bus dependencies by parsing:
- `appsettings.json` - Connection strings, topic names
- `.env` files - Environment variables
- `web.config` - Legacy configurations
- Kubernetes YAML manifests (future enhancement)

## Example Scenario

You have:
- **AKS Cluster**: `prod-customer-api-aks`
- **Repository**: `customer-api`
- **Code**: `appsettings.json` contains Service Bus connection string for `fifa-1` topic

### Scanner Process:
1. Scans `customer-api` repository
2. Finds Service Bus namespace and `fifa-1` topic reference
3. Matches `customer-api` repo to `prod-customer-api-aks` cluster
4. Creates dependency: `prod-customer-api-aks` → `DEPENDS_ON` → `fifa-1 topic`

### Result in Neo4j:
```cypher
(aks:Resource {name: "prod-customer-api-aks", resource_type: "aks"})
-[r:DEPENDS_ON {
    strength: 0.95,
    discovered_method: "code_repository_scan",
    category: "messaging",
    dependency_type: "servicebus"
}]->
(topic:Resource {name: "fifa-1", resource_type: "servicebus_topic"})
```

## Dependency Strength

Dependencies discovered through code scanning have:
- **Strength**: `0.95` (very high - found in source code)
- **Method**: `code_repository_scan`
- **Category**: `messaging` (for Service Bus)
- **Type**: `servicebus`

## Naming Conventions

For best results, use consistent naming patterns:

### Good Examples:
- Repo: `customer-api` → AKS: `prod-customer-api-aks` ✅
- Repo: `payment-service` → AKS: `aks-payment-service` ✅
- Repo: `inventory-app` → AKS: `inventory-app-cluster` ✅

### Flexible Matching:
The scanner uses case-insensitive substring matching, so these work too:
- Repo: `CustomerAPI` → AKS: `prod-customer-api-aks` ✅
- Repo: `payment` → AKS: `aks-payment-service-prod` ✅

## Configuration

### Required Environment Variables:
```bash
# Azure DevOps
AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
AZURE_DEVOPS_PAT=<your-pat>
AZURE_DEVOPS_PROJECT=  # Optional - leave empty to scan all projects

# Azure Credentials
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_CLIENT_ID=<service-principal-id>
AZURE_CLIENT_SECRET=<service-principal-secret>
AZURE_TENANT_ID=<tenant-id>
```

### Azure DevOps PAT Permissions:
- **Code**: Read
- **Project and Team**: Read

## Testing

### 1. Discover Azure Resources
```bash
POST /api/v1/discovery/discover-azure
```

Verify you see AKS clusters in the response.

### 2. Scan Repositories
```bash
# Single project
POST /api/v1/discovery/scan-repositories

# All projects (recommended for IaC)
POST /api/v1/discovery/scan-repositories?scan_all_projects=true
```

### 3. View Dependencies in Neo4j
```cypher
// Find all AKS dependencies
MATCH (aks:Resource {resource_type: "aks"})
      -[r:DEPENDS_ON]->
      (target:Resource)
WHERE r.discovered_method = "code_repository_scan"
RETURN aks.name, r.dependency_type, target.name, target.resource_type
```

## Logs

Check API logs for matching details:
```
INFO: Matched repository CodeGalaxy/customer-api to AKS cluster prod-customer-api-aks
INFO: Created 3 dependencies from CodeGalaxy/customer-api to AKS Cluster prod-customer-api-aks
```

Or if no match found:
```
INFO: No matching compute resource (App Service or AKS) found for repository customer-api 
      (found 1 Service Bus namespaces)
```

## Troubleshooting

### No AKS Clusters Discovered
**Problem**: Scanner logs show "No matching compute resource found"

**Solution**:
1. Verify AKS clusters were discovered: `GET /api/v1/resources?type=aks`
2. Check your Azure credentials have permissions to read AKS resources
3. Ensure AKS clusters exist in your subscription

### Repository Not Matching to AKS
**Problem**: Repository scanned but no dependencies created

**Solution**:
1. Check naming patterns - ensure repo name appears in AKS cluster name
2. Add repository tags to your AKS cluster:
   ```bash
   az aks update \
     --resource-group myRG \
     --name prod-customer-api-aks \
     --tags repository=https://dev.azure.com/CodeGalaxy/_git/customer-api
   ```
3. Check logs for "Matched repository" messages

### Dependencies Not Found
**Problem**: Code has Service Bus references but scanner doesn't find them

**Solution**:
1. Verify configuration file format (valid JSON in `appsettings.json`)
2. Check connection string format (must contain `servicebus.windows.net`)
3. Ensure files are in root directory or common config paths
4. Check branch name (scanner tries `main`, `master`, `develop`)

## Future Enhancements

Planned features for AKS support:
- Parse Kubernetes ConfigMaps and Secrets
- Scan Helm values.yaml files
- Detect Dapr components
- Support for Azure Container Apps
- Scan Terraform/Bicep IaC files

## Related Documentation
- [Code Repository Scanner](CODE_REPOSITORY_SCANNER.md)
- [Scanning All Projects](SCANNING_ALL_PROJECTS.md)
- [Code Scanner Integration](CODE_SCANNER_INTEGRATION.md)
