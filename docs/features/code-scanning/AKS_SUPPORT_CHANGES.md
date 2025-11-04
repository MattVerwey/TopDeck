# AKS Support Enhancement Summary

## Changes Made

### 1. API Endpoint Updates (`src/topdeck/api/routes/discovery.py`)

#### Added AKS Cluster Discovery
- Now discovers both `app_service` and `aks` resource types
- Creates separate lists: `app_services` and `aks_clusters`

#### Updated All-Projects Mode Matching Logic
- **Before**: Only matched repositories to App Services
- **After**: Matches repositories to both App Services AND AKS clusters
- **Priority**: App Services first, then AKS clusters
- **Logs**: Shows resource type matched (App Service vs AKS Cluster)

#### Updated Single-Project Mode
- **Before**: Only passed App Services to scanner
- **After**: Combines App Services + AKS clusters into `compute_resources`
- Scanner now links repositories to both types

### 2. DevOps Discoverer Updates (`src/topdeck/discovery/azure/devops.py`)

#### Renamed Methods for Clarity
- `_find_app_service_for_repo()` → `_find_compute_resource_for_repo()`
- Updated parameter name from `app_service_resources` to accept any compute resource
- Updated docstrings to reflect support for both App Services and AKS

#### Enhanced Matching Logic
- Works with both App Service and AKS cluster resources
- Tag-based matching checks repository URL in resource tags
- Name-based matching works for both types
- Examples:
  - `customer-api` repo → `prod-customer-api-aks` cluster ✅
  - `payment-service` repo → `aks-payment-service` cluster ✅

### 3. Documentation

#### Created New Guide
- **File**: `docs/AKS_CODE_SCANNING.md`
- **Content**:
  - Overview of AKS support
  - How repository-to-cluster mapping works
  - Priority order (App Services first, AKS second)
  - Example scenarios
  - Configuration requirements
  - Testing procedures
  - Troubleshooting guide

## What This Enables

### Discovery Flow
```
Azure DevOps Repository (code)
    ↓
Scan appsettings.json, .env files
    ↓
Find Service Bus connection strings & topic names
    ↓
Match repository to AKS cluster (by name or tags)
    ↓
Create DEPENDS_ON relationships in Neo4j
    ↓
Visualize: AKS Cluster → Service Bus Topic
```

### Example Use Case

**Your Setup:**
- AKS Cluster: `prod-customer-api-aks`
- Repository: `customer-api` (in Azure DevOps)
- Code: Uses Service Bus topics `fifa-1`, `nba-5`

**Scanner Process:**
1. Scans `customer-api` repository
2. Finds Service Bus references in `appsettings.json`
3. Matches `customer-api` to `prod-customer-api-aks` (name similarity)
4. Creates dependencies:
   - `prod-customer-api-aks` → `DEPENDS_ON` → `fifa-1 topic`
   - `prod-customer-api-aks` → `DEPENDS_ON` → `nba-5 topic`

**Result:**
You can now visualize which AKS clusters depend on which Service Bus topics!

## API Usage

### Scan All Projects (Recommended for IaC)
```bash
POST /api/v1/discovery/scan-repositories?scan_all_projects=true
```

**Response:**
```json
{
  "success": true,
  "projects_scanned": ["Project1", "Project2"],
  "repositories_scanned": 15,
  "dependencies_created": 42,
  "message": "Successfully scanned all projects..."
}
```

### Scan Single Project
```bash
POST /api/v1/discovery/scan-repositories
```

## Logging

The scanner now provides detailed logs:

```
INFO: Matched repository CodeGalaxy/customer-api to AKS cluster prod-customer-api-aks
INFO: Created 3 dependencies from CodeGalaxy/customer-api to AKS Cluster prod-customer-api-aks

INFO: Matched repository CodeGalaxy/payment-service to App Service prod-payment-api
INFO: Created 2 dependencies from CodeGalaxy/payment-service to App Service prod-payment-api

INFO: No matching compute resource (App Service or AKS) found for repository legacy-app 
      (found 1 Service Bus namespaces)
```

## Neo4j Relationships

Dependencies created have these properties:

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

## Naming Best Practices

For automatic matching to work, use consistent naming:

### Good Patterns:
- Repo: `customer-api` → AKS: `prod-customer-api-aks` ✅
- Repo: `payment-service` → AKS: `aks-payment-service-prod` ✅
- Repo: `inventory` → AKS: `inventory-cluster` ✅

### Alternative: Use Tags
If naming doesn't match, add repository tags to your AKS cluster:

```bash
az aks update \
  --resource-group myRG \
  --name my-aks-cluster \
  --tags repository=https://dev.azure.com/CodeGalaxy/_git/customer-api
```

## Testing Steps

1. **Discover Azure Resources** (includes AKS):
   ```bash
   POST /api/v1/discovery/discover-azure
   ```

2. **Verify AKS Clusters Discovered**:
   ```bash
   GET /api/v1/resources?type=aks
   ```

3. **Scan All Projects**:
   ```bash
   POST /api/v1/discovery/scan-repositories?scan_all_projects=true
   ```

4. **Check Dependencies in Neo4j**:
   ```cypher
   MATCH (aks:Resource {resource_type: "aks"})
         -[r:DEPENDS_ON]->
         (target:Resource)
   WHERE r.discovered_method = "code_repository_scan"
   RETURN aks.name, target.name, target.resource_type
   ```

## Backward Compatibility

✅ **100% Backward Compatible**
- Existing App Service scanning still works
- Can handle mixed environments (App Services + AKS)
- Single-project mode unchanged for existing users
- All existing dependencies preserved

## Next Steps

1. **Rebuild API Container**:
   ```bash
   docker-compose up -d --build api
   ```

2. **Test with Your Environment**:
   - You have 21 Service Bus topics already discovered
   - Scanner will now map your IaC repositories to AKS clusters
   - Create dependencies automatically

3. **Visualize**:
   - View topology graph showing AKS → Service Bus relationships
   - See which clusters depend on which topics

## Summary

The code repository scanner now **fully supports AKS clusters** alongside App Services. Since most of your Infrastructure as Code deploys to AKS, the scanner will:

✅ Discover AKS clusters in your subscription
✅ Scan your Azure DevOps repositories for Service Bus references
✅ Match repositories to AKS clusters by name or tags
✅ Create dependencies showing which clusters use which topics
✅ Store everything in Neo4j for topology visualization

**This gives you complete visibility into your AKS-based microservices and their Service Bus dependencies!**
