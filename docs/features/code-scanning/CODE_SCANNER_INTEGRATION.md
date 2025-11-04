# Code Repository Scanner - Integration Summary

## Overview

The **Code Repository Scanner** is a new feature that extends your existing Azure DevOps integration to automatically discover Service Bus dependencies by scanning application source code.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure DevOps Integration                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Existing Features (Already Working):                        │
│  ├── discover_repositories()     - List all repos           │
│  ├── discover_deployments()      - Get deployment history   │
│  └── discover_applications()     - Infer apps from repos    │
│                                                               │
│  NEW Feature:                                                │
│  └── scan_repositories_for_dependencies()                    │
│       └── Uses CodeRepositoryScanner                         │
│            ├── Download config files from repos              │
│            ├── Parse for Service Bus connection strings      │
│            ├── Match to discovered Azure resources           │
│            └── Create dependencies in Neo4j                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Uses Same Credentials from .env:
├── AZURE_DEVOPS_ORGANIZATION
├── AZURE_DEVOPS_PROJECT
└── AZURE_DEVOPS_PAT
```

## How It Works

### 1. Credentials (Shared with Existing ADO Integration)

The scanner uses your **existing** Azure DevOps credentials:

**File**: `.env`
```bash
# These credentials are already configured for ADO integration
AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
AZURE_DEVOPS_PROJECT=YourProjectName
AZURE_DEVOPS_PAT=your-personal-access-token
ENABLE_AZURE_DEVOPS_INTEGRATION=true
```

### 2. API Endpoint (New)

**Endpoint**: `POST /api/v1/discovery/scan-repositories`

**What it does**:
1. Connects to Azure DevOps using your PAT
2. Lists all repositories in your project
3. For each repository:
   - Downloads configuration files (appsettings.json, .env, etc.)
   - Parses them for Service Bus references
   - Extracts namespace, topic, and queue names
4. Matches found resources to your discovered Azure resources
5. Creates strong dependencies in Neo4j

**Response**:
```json
{
  "status": "success",
  "message": "Scanned repositories and created 5 new dependencies",
  "repositories_scanned": 3,
  "dependencies_created": 5,
  "namespaces_found": ["cg-dev-uks-sbns-1"],
  "topics_found": ["fifa-1", "fifa-2", "nba-5", "test-topic", "test-topic-2"]
}
```

### 3. Integration with Discovery Flow

#### Current Flow:
```
1. Discovery runs (scheduled or manual)
   ├── Azure resource discovery
   ├── Store in Neo4j
   └── Done

2. Topology API serves resources
```

#### With Code Scanning:
```
1. Discovery runs (scheduled or manual)
   ├── Azure resource discovery
   ├── Store in Neo4j
   └── Done

2. Code repository scan (NEW - manual trigger)
   ├── Scan ADO repositories
   ├── Parse config files
   ├── Match to discovered resources
   └── Create dependencies in Neo4j

3. Topology API serves resources + dependencies
```

## What Gets Discovered

### Configuration Files Scanned
- ✅ `appsettings.json`
- ✅ `appsettings.Development.json`
- ✅ `appsettings.Production.json`
- ✅ `appsettings.Staging.json`
- ✅ `.env` files
- ✅ `web.config`
- ✅ `app.config`

### Service Bus References Found
From your **appsettings.json**:
```json
{
  "ConnectionStrings": {
    "ServiceBus": "Endpoint=sb://cg-dev-uks-sbns-1.servicebus.windows.net/..."
  },
  "ServiceBus": {
    "TopicName": "fifa-1"
  }
}
```

**Extracts**:
- Namespace: `cg-dev-uks-sbns-1`
- Topic: `fifa-1`

### Matching Logic

```
Found in Code              Your Discovered Resources
───────────────            ─────────────────────────
Namespace:                 Service Bus Namespace
cg-dev-uks-sbns-1     →    ✅ MATCH: cg-dev-uks-sbns-1
                           (from your subscription)

Topic: fifa-1         →    ✅ MATCH: fifa-1
                           (one of your 21 topics)

Topic: fifa-2         →    ✅ MATCH: fifa-2
                           (one of your 21 topics)

Topic: other-topic    →    ❌ NO MATCH
                           (not in your subscription)
```

**Only creates dependencies for resources in your subscription!**

## Setup Required

### Step 1: Verify Azure DevOps Credentials

Run the verification script:
```powershell
python scripts\check_ado_config.py
```

This checks if your ADO credentials are properly configured.

### Step 2: Update .env (If Needed)

If credentials are not set, edit `.env`:
```bash
# Replace these with your actual values:
AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
AZURE_DEVOPS_PROJECT=YourMainProject
AZURE_DEVOPS_PAT=<generate-from-ado>
```

### Step 3: Generate PAT Token

1. Go to: `https://dev.azure.com/CodeGalaxy/_usersSettings/tokens`
2. Click **+ New Token**
3. Name: "TopDeck Code Scanner"
4. Scopes:
   - ✅ **Code**: Read
   - ✅ **Project and Team**: Read
5. Copy token and paste into `.env`

### Step 4: Restart API

```powershell
docker-compose up -d --build api
```

## Usage Example

### 1. Run Discovery (Get Azure Resources)
```powershell
# Discover all Azure resources including Service Bus
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/trigger"
```

**Result**: 624 resources discovered including:
- 1 Service Bus namespace (cg-dev-uks-sbns-1)
- 21 topics (fifa-1 through fifa-9, nba-1 through nba-9, test-topic, etc.)

### 2. Scan Repositories (Find Connections)
```powershell
# Scan ADO repositories for Service Bus references
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/scan-repositories"
```

**Result**:
```json
{
  "status": "success",
  "repositories_scanned": 3,
  "dependencies_created": 5,
  "namespaces_found": ["cg-dev-uks-sbns-1"],
  "topics_found": ["fifa-1", "fifa-2", "nba-5", "test-topic"]
}
```

### 3. View Topology (See Dependencies)
```powershell
# Get topology with new dependencies
$topology = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/topology"

# Find Service Bus dependencies
$topology.edges | Where-Object { 
  $_.relationship_type -eq "DEPENDS_ON" -and 
  $_.properties.discovered_method -eq "code_repository_scan" 
}
```

**Result**: Edges showing App Services depending on Service Bus with:
- `strength`: 0.95 (very strong - found in code)
- `discovered_method`: "code_repository_scan"
- `description`: "Application uses Service Bus cg-dev-uks-sbns-1 (found in repository config)"

## Benefits

### Before Code Scanning
```
App Service → Service Bus
├── Method: heuristic_colocation
├── Strength: 0.3 (weak)
└── Reason: Same resource group
```

❓ **Uncertainty**: "These might be related..."

### After Code Scanning
```
App Service → Service Bus
├── Method: code_repository_scan  
├── Strength: 0.95 (very strong)
└── Reason: Found in appsettings.json
    Topics used: fifa-1, fifa-2, test-topic
```

✅ **Certainty**: "These ARE related, here's proof from source code!"

## Comparison with Existing ADO Features

| Feature | Existing ADO Integration | New Code Scanner |
|---------|-------------------------|------------------|
| **Purpose** | Discover repos, deployments, apps | Find resource dependencies in code |
| **Data Source** | ADO metadata, pipelines | Source code config files |
| **Credentials** | Uses .env AZURE_DEVOPS_* | Same credentials |
| **Output** | Repository objects | ResourceDependency objects |
| **Storage** | Not stored (returned via API) | Stored in Neo4j as edges |
| **Trigger** | Called by discovery flow | Manual API call (POST /scan-repositories) |

## Limitations

### ✅ What It Does
- Scans configuration files (JSON, env, XML)
- Finds Service Bus connection strings
- Matches to your discovered resources
- Creates strong dependencies

### ❌ What It Doesn't Do
- Parse actual C# code (only config files)
- Scan hardcoded values in source code
- Track message flow patterns
- Detect publish vs. subscribe patterns

### 🔮 Future Enhancements
- Parse C# code for Service Bus SDK usage
- Support GitHub repositories
- Real-time scanning on commits
- Cache file contents by commit SHA

## Troubleshooting

### Error: "Azure DevOps credentials not configured"
**Solution**: Update `.env` with your ADO organization, project, and PAT

### Error: "httpx is required"
**Solution**: Already installed in Docker, should work automatically

### No dependencies created
**Possible reasons**:
1. Config files don't contain Service Bus references
2. Service Bus resources not yet discovered (run discovery first)
3. Repository names don't match App Service names (no linking)

### Repositories scanned but no App Services linked
**Solution**: Add repository URL tag to App Services:
```json
{
  "tags": {
    "repository": "https://dev.azure.com/org/project/_git/reponame"
  }
}
```

## Summary

✅ **Yes, this is part of the Azure DevOps integration**  
✅ **Uses same credentials** (AZURE_DEVOPS_ORGANIZATION, PROJECT, PAT)  
✅ **Extends existing ADO features** with code scanning  
✅ **Only creates dependencies for resources in your subscription**  
✅ **Provides strong proof** of Service Bus usage (strength: 0.95)  
✅ **Works with your 21 discovered Service Bus topics**  

The scanner **complements** the existing discovery by finding actual usage patterns in code, giving you complete visibility into which apps use which Service Bus topics!
