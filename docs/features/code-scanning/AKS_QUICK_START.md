# Quick Reference: AKS + Code Scanning

## What Changed

The code repository scanner now maps your **Azure DevOps repositories** to **AKS clusters** (not just App Services) and discovers Service Bus dependencies.

## Why This Matters for Your Setup

You mentioned:
> "Most of my IaC in ADO will be deploying to AKS not App Services"

**Before**: Scanner only linked repos to App Services ❌
**After**: Scanner links repos to both App Services AND AKS clusters ✅

## How It Works

1. **Discovers AKS Clusters** from your Azure subscription
2. **Scans ADO Repositories** for Service Bus connection strings
3. **Matches Repos to Clusters** by name similarity
4. **Creates Dependencies** in Neo4j showing: AKS → Service Bus

## Matching Examples

| Repository Name | AKS Cluster Name | Match? |
|----------------|------------------|--------|
| `customer-api` | `prod-customer-api-aks` | ✅ Yes |
| `payment-service` | `aks-payment-service` | ✅ Yes |
| `inventory` | `inventory-cluster` | ✅ Yes |
| `CustomerAPI` | `prod-customer-api-aks` | ✅ Yes (case-insensitive) |
| `old-app` | `new-customer-api-aks` | ❌ No (use tags instead) |

## Priority Order

When matching, the scanner checks:
1. **App Services first** - For traditional web apps
2. **AKS Clusters second** - For containerized workloads (your case)

## Quick Test

### 1. Rebuild API
```powershell
cd "c:\Code\Custom Repos\TopDeck"
docker-compose up -d --build api
```

### 2. Scan All Projects
```powershell
Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/api/v1/discovery/scan-repositories?scan_all_projects=true'
```

### 3. Check Logs
```powershell
docker-compose logs api | Select-String "Matched repository"
```

You should see:
```
INFO: Matched repository CodeGalaxy/customer-api to AKS cluster prod-customer-api-aks
INFO: Created 3 dependencies from CodeGalaxy/customer-api to AKS Cluster prod-customer-api-aks
```

## What You'll Get

### Dependencies Created:
```
AKS Cluster (prod-customer-api-aks)
    ├─ DEPENDS_ON → fifa-1 topic
    ├─ DEPENDS_ON → fifa-2 topic
    └─ DEPENDS_ON → nba-5 topic
```

### Topology View:
- Visual graph showing which AKS clusters use which Service Bus topics
- Strength: 0.95 (very high - found in code)
- Method: "code_repository_scan"

## If Repos Don't Match

### Option 1: Fix Naming
Ensure repo name appears in cluster name:
- Repo: `my-service` → Cluster: `prod-my-service-aks` ✅

### Option 2: Add Tags
```bash
az aks update \
  --resource-group myRG \
  --name my-aks-cluster \
  --tags repository=https://dev.azure.com/CodeGalaxy/_git/my-repo
```

## View Dependencies

### In Neo4j Browser:
```cypher
MATCH (aks:Resource {resource_type: "aks"})
      -[r:DEPENDS_ON]->
      (sb:Resource)
WHERE r.discovered_method = "code_repository_scan"
RETURN aks.name, sb.name, sb.resource_type
```

### Via API:
```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/resources?type=aks'
```

## Configuration

Your existing `.env` already has what you need:
```bash
AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
AZURE_DEVOPS_PAT=<your-pat>
AZURE_DEVOPS_PROJECT=  # Leave empty to scan all

# Azure credentials (for discovering AKS)
AZURE_SUBSCRIPTION_ID=<your-sub-id>
AZURE_CLIENT_ID=<sp-id>
AZURE_CLIENT_SECRET=<sp-secret>
AZURE_TENANT_ID=<tenant-id>
```

## Summary

✅ **AKS clusters now fully supported**
✅ **Scans all projects in your ADO organization**
✅ **Automatically creates dependencies**
✅ **Works with your existing Service Bus topics (21 discovered)**
✅ **Supports name-based and tag-based matching**

**You're all set for IaC + AKS deployments!** 🚀
