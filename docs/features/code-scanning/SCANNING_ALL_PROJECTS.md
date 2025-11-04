# Scanning All Azure DevOps Projects

## Overview

The Code Repository Scanner can now scan **all projects** in your Azure DevOps organization, not just a single project. This is useful when you have multiple projects and want to discover Service Bus dependencies across your entire organization.

## Configuration

### Option 1: Scan All Projects (Recommended)

**Set only organization and PAT in `.env`:**
```bash
AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
AZURE_DEVOPS_PROJECT=  # Leave empty or omit this line
AZURE_DEVOPS_PAT=your-personal-access-token
```

**API Call:**
```powershell
# Scan all projects in the organization
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/scan-repositories?scan_all_projects=true"
```

### Option 2: Scan Single Project

**Set organization, project, and PAT in `.env`:**
```bash
AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
AZURE_DEVOPS_PROJECT=MySpecificProject
AZURE_DEVOPS_PAT=your-personal-access-token
```

**API Call:**
```powershell
# Scan only the configured project
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/scan-repositories"

# OR explicitly set scan_all_projects=false
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/scan-repositories?scan_all_projects=false"
```

## API Usage

### Endpoint

```
POST /api/v1/discovery/scan-repositories?scan_all_projects={true|false}
```

**Query Parameters:**
- `scan_all_projects` (optional, default: `false`)
  - `true`: Scans all projects in the organization
  - `false`: Scans only the configured project

### Response

#### Single Project Scan
```json
{
  "status": "success",
  "message": "Scanned 1 project(s) and created 5 new dependencies",
  "projects_scanned": null,
  "repositories_scanned": 3,
  "dependencies_created": 5,
  "namespaces_found": ["cg-dev-uks-sbns-1"],
  "topics_found": ["fifa-1", "fifa-2", "nba-5"]
}
```

#### All Projects Scan
```json
{
  "status": "success",
  "message": "Scanned 5 project(s) and created 0 new dependencies",
  "projects_scanned": ["Project1", "Project2", "Project3", "Project4", "Project5"],
  "repositories_scanned": 15,
  "dependencies_created": 0,
  "namespaces_found": ["cg-dev-uks-sbns-1", "prod-servicebus"],
  "topics_found": ["fifa-1", "fifa-2", "orders", "events"]
}
```

## How It Works

### All Projects Mode

```
1. Get all projects in organization
   ├── Project1
   ├── Project2
   ├── Project3
   └── Project4

2. For each project:
   ├── Get all repositories
   ├── For each repository:
   │   ├── Try main branch
   │   ├── Fallback to master
   │   └── Fallback to develop
   │
   └── Parse config files:
       ├── appsettings.json
       ├── .env
       └── web.config

3. Aggregate results across all projects

4. Report findings:
   ├── Projects scanned: ["Project1", "Project2", ...]
   ├── Repositories scanned: 15
   ├── Namespaces found: ["cg-dev-uks-sbns-1", ...]
   └── Topics found: ["fifa-1", "fifa-2", ...]
```

### Single Project Mode (Original)

```
1. Use configured project

2. Get all repositories in project

3. For each repository:
   ├── Scan config files
   ├── Match to App Services (by name/tags)
   └── Create dependencies in Neo4j

4. Report findings:
   ├── Repositories scanned: 3
   ├── Dependencies created: 5
   └── Namespaces/topics found
```

## Benefits of All-Projects Scanning

### 1. **Organization-Wide Discovery**
Find Service Bus usage across **all** your projects, not just one.

**Example:**
```
Organization: CodeGalaxy
├── Project: CustomerPortal
│   └── Repos: portal-api, portal-web
│       └── Uses: cg-dev-uks-sbns-1 (topics: fifa-1, fifa-2)
│
├── Project: InternalTools  
│   └── Repos: admin-dashboard, reporting-service
│       └── Uses: cg-dev-uks-sbns-1 (topics: nba-5, test-topic)
│
└── Project: MobileApps
    └── Repos: ios-app, android-app
        └── No Service Bus usage found
```

### 2. **No Configuration Required Per Project**
Set credentials once, scan everything.

### 3. **Complete Dependency Mapping**
Discover ALL applications using your Service Bus resources.

## Limitations

### Features
- ✅ Scans all projects and repositories
- ✅ Finds Service Bus references
- ✅ Reports aggregated results  
- ✅ **Creates dependencies automatically** by matching repository names to App Services

The all-projects mode scans across all projects and **automatically creates dependencies** when it can match repositories to App Services by name similarity.

**Matching Logic:**
- Repository name contains App Service name → ✅ Match
- App Service name contains repository name → ✅ Match
- Example: Repo `customer-api` matches App Service `prod-customer-api`

### Future Enhancements (Phase 2)
- [ ] Match using repository tags in App Service resources
- [ ] Support cross-subscription resource dependencies
- [ ] Track publisher vs subscriber patterns

## Use Cases

### Use Case 1: Initial Discovery
**Scenario**: New TopDeck installation, want to see what's using Service Bus

```powershell
# Step 1: Discover Azure resources
POST /api/v1/discovery/trigger

# Step 2: Scan ALL projects to find usage
POST /api/v1/discovery/scan-repositories?scan_all_projects=true
```

**Output**: Complete picture of Service Bus usage across entire organization

### Use Case 2: Specific Project Deep Dive
**Scenario**: Know which project to focus on, want dependency graph

```powershell
# Configure specific project in .env
AZURE_DEVOPS_PROJECT=CustomerPortal

# Scan just this project
POST /api/v1/discovery/scan-repositories
```

**Output**: Dependencies created in Neo4j for topology visualization

### Use Case 3: Multi-Project Report
**Scenario**: Need report of Service Bus usage for compliance

```powershell
# Scan all projects
POST /api/v1/discovery/scan-repositories?scan_all_projects=true
```

**Output**:
```json
{
  "projects_scanned": ["Project1", "Project2", "Project3"],
  "repositories_scanned": 12,
  "namespaces_found": ["cg-dev-uks-sbns-1"],
  "topics_found": ["fifa-1", "fifa-2", "nba-5", "test-topic"]
}
```

## PAT Permissions

### Required Scopes
- ✅ **Code**: Read (access repositories)
- ✅ **Project and Team**: Read (list projects)

### Verify Permissions
```powershell
# Test if PAT can access projects API
$headers = @{
    Authorization = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$PAT"))
}

Invoke-RestMethod -Uri "https://dev.azure.com/CodeGalaxy/_apis/projects?api-version=7.0" -Headers $headers
```

Should return list of projects if PAT is valid.

## Performance

### Single Project
- **Time**: ~2-5 seconds per repository
- **API Calls**: ~10-20 per repository
- **Rate Limit**: 200 requests/minute (ADO API)

### All Projects (5 projects, 15 repos total)
- **Time**: ~30-75 seconds total
- **API Calls**: ~150-300 total
- **Rate Limit**: Handled automatically by rate limiter

## Examples

### PowerShell Examples

```powershell
# Example 1: Scan all projects
$result = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/scan-repositories?scan_all_projects=true"

Write-Host "Projects scanned: $($result.projects_scanned -join ', ')"
Write-Host "Repositories scanned: $($result.repositories_scanned)"
Write-Host "Namespaces found: $($result.namespaces_found -join ', ')"
Write-Host "Topics found: $($result.topics_found -join ', ')"

# Example 2: Scan single project
$result = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/scan-repositories"

Write-Host "Dependencies created: $($result.dependencies_created)"
Write-Host "Namespaces: $($result.namespaces_found -join ', ')"

# Example 3: Compare scan modes
# All projects (discovery mode)
$all = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/scan-repositories?scan_all_projects=true"
Write-Host "All projects: Found $($all.namespaces_found.Count) namespaces in $($all.projects_scanned.Count) projects"

# Single project (dependency creation mode)
$single = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/discovery/scan-repositories"
Write-Host "Single project: Created $($single.dependencies_created) dependencies"
```

### curl Examples

```bash
# Scan all projects
curl -X POST "http://localhost:8000/api/v1/discovery/scan-repositories?scan_all_projects=true"

# Scan single project
curl -X POST "http://localhost:8000/api/v1/discovery/scan-repositories"
```

## Troubleshooting

### Error: "Azure DevOps organization not configured"
**Solution**: Set `AZURE_DEVOPS_ORGANIZATION` in `.env`

### Error: "Azure DevOps PAT not configured"
**Solution**: Set `AZURE_DEVOPS_PAT` in `.env`

### No projects found
**Possible causes:**
1. PAT doesn't have "Project and Team: Read" permission
2. Organization name is incorrect
3. No projects exist in organization

**Verify:**
```powershell
# Check if org URL is correct
https://dev.azure.com/CodeGalaxy  # Should open in browser
```

### Scan finds namespaces but no dependencies created
**Possible causes:**
1. No App Services matched the repository names
2. App Services don't exist in your discovered resources
3. Repository-to-App Service name matching failed

**Check the logs for:**
```
No matching App Service found for repository Project/RepoName
```

**Solutions:**
- Ensure App Services are discovered (run discovery first)
- Use naming conventions: repo `myapp` → app `prod-myapp-api`
- Add repository tags to App Services for better matching

## Migration Guide

### From Single Project to All Projects

**Before:**
```bash
# .env
AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
AZURE_DEVOPS_PROJECT=MainProject
AZURE_DEVOPS_PAT=xxx
```

```powershell
# API Call
POST /api/v1/discovery/scan-repositories
```

**After:**
```bash
# .env (remove or leave empty PROJECT)
AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
AZURE_DEVOPS_PROJECT=
AZURE_DEVOPS_PAT=xxx
```

```powershell
# API Call (add query parameter)
POST /api/v1/discovery/scan-repositories?scan_all_projects=true
```

## Summary

| Feature | Single Project | All Projects |
|---------|---------------|--------------|
| **Configuration** | Requires PROJECT set | Only requires ORGANIZATION |
| **API Parameter** | `scan_all_projects=false` (default) | `scan_all_projects=true` |
| **What It Scans** | 1 project | All projects in org |
| **Dependency Creation** | ✅ Yes (by repo-app linking) | ✅ Yes (by name matching) |
| **Output** | Dependencies in Neo4j | Dependencies in Neo4j + aggregated report |
| **Use Case** | Detailed analysis of one project | Discovery across entire organization |
| **Performance** | Fast (~5-15 sec) | Slower (~30-120 sec) |

**Recommendation**: Use all-projects mode for initial discovery, then scan specific projects for detailed dependency mapping!
