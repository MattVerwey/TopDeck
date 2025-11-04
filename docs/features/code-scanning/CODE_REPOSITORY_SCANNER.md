# Code Repository Scanner for Service Bus Dependencies

## Overview

The Code Repository Scanner automatically discovers Service Bus and other resource dependencies by scanning application source code from Azure DevOps repositories. It parses configuration files to find connection strings and resource references, then creates dependency relationships in the topology graph.

## 🎯 What It Does

### Scans Configuration Files
- `appsettings.json` (all variants: Development, Staging, Production)
- `.env` files
- `web.config` / `app.config`
- Other JSON/XML configuration files

### Discovers Service Bus References
- **Connection Strings**: `Endpoint=sb://namespace.servicebus.windows.net/...`
- **Topic Names**: References to specific topics like `fifa-1`, `nba-5`, `test-topic`
- **Queue Names**: References to queues
- **Namespace Names**: Service Bus namespace identifiers

### Creates Strong Dependencies
- **Strength**: 0.95 (very high confidence - found in actual source code)
- **Discovery Method**: `code_repository_scan`
- **Category**: Data dependencies
- **Type**: Required (since code references them)

## 📋 How It Works

### 1. Repository Discovery
```
Azure DevOps API
      ↓
Get all repositories in project
      ↓
For each repository:
  - Try main branch
  - Fallback to master
  - Fallback to develop
```

### 2. File Scanning
```
For each repository:
  ↓
Get file list (recursively)
  ↓
Filter for config files:
  - appsettings*.json
  - .env*
  - *.config
  ↓
Download file contents
  ↓
Parse based on file type
```

### 3. Parsing Logic

#### JSON Files (appsettings.json)
```json
{
  "ConnectionStrings": {
    "ServiceBus": "Endpoint=sb://cg-dev-uks-sbns-1.servicebus.windows.net/..."
  },
  "ServiceBus": {
    "TopicName": "fifa-1",
    "Namespace": "cg-dev-uks-sbns-1"
  },
  "Messaging": {
    "Topics": ["fifa-1", "fifa-2", "test-topic"]
  }
}
```

**Extracts**:
- Namespace: `cg-dev-uks-sbns-1`
- Topics: `fifa-1`, `fifa-2`, `test-topic`

#### Environment Files (.env)
```bash
AZURE_SERVICEBUS_CONNECTION=Endpoint=sb://namespace.servicebus.windows.net/...
SERVICEBUS_TOPIC_NAME=test-topic-2
TOPIC_NAME=nba-5
```

**Extracts**:
- Connection strings with Service Bus endpoints
- Environment variables containing "SERVICEBUS", "TOPIC", "QUEUE"

### 4. Resource Matching

```
Found in Code              Discovered Azure Resources
─────────────────          ───────────────────────────
Namespace: cg-dev-uks-     →  MATCH: ServiceBus namespace
sbns-1                         /subscriptions/.../cg-dev-uks-sbns-1

Topic: fifa-1              →  MATCH: Topic in namespace.topics[]
                               Name: fifa-1, Status: Active

Topic: other-service-bus   →  NO MATCH: Not in subscription
                               (Filtered out - no dependency created)
```

**Only creates dependencies for resources in your subscription!**

### 5. App Service Linking

Links repositories to App Services by:
1. **Repository URL in tags**: App Service has `repository` tag matching repo URL
2. **Name matching**: Repository name appears in App Service name
   - Repo: `myapp` → App Service: `prod-myapp-api` ✅
   - Repo: `customer-service` → App Service: `cust-service-web` ✅

### 6. Dependency Creation

```cypher
MATCH (app:Resource {id: "app-service-id"})
MATCH (sb:Resource {id: "servicebus-namespace-id"})
MERGE (app)-[r:DEPENDS_ON]->(sb)
SET r.category = 'DATA',
    r.dependency_type = 'REQUIRED',
    r.strength = 0.95,
    r.discovered_method = 'code_repository_scan',
    r.description = 'Application uses Service Bus namespace (found in repository config)',
    r.discovered_at = datetime()
```

## 🚀 Usage

### Prerequisites

1. **Azure DevOps Credentials**
   ```bash
   export AZURE_DEVOPS_ORGANIZATION="your-org"
   export AZURE_DEVOPS_PROJECT="your-project"
   export AZURE_DEVOPS_PAT="your-personal-access-token"
   ```

2. **PAT Permissions Required**
   - Code: Read
   - Project and Team: Read

3. **Azure Resources Already Discovered**
   - Run normal discovery first to get Service Bus resources
   - Scanner only creates dependencies for known resources

### API Endpoint

#### POST /api/v1/discovery/scan-repositories

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/discovery/scan-repositories
```

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

### Command Line Test

```bash
# Test the scanner logic
python scripts/test_code_scanner.py
```

## 📊 Example Scenario

### Before Code Scanning

**Topology**:
```
App Service (prod-myapp)
    ↓ (heuristic, strength: 0.3)
Service Bus Namespace (cg-dev-uks-sbns-1)
    ├── Topic: fifa-1
    ├── Topic: fifa-2
    └── Topic: test-topic
```

Dependency exists but **weak** (heuristic - same resource group).

### After Code Scanning

**Topology**:
```
App Service (prod-myapp)
    ↓ (code_repository_scan, strength: 0.95) 
Service Bus Namespace (cg-dev-uks-sbns-1)
    ├── Topic: fifa-1 ← Used in code
    ├── Topic: fifa-2 ← Used in code
    └── Topic: test-topic ← Used in code
```

Dependency is now **strong** with proof from source code!

**Details in dependency**:
```json
{
  "source": "/subscriptions/.../providers/Microsoft.Web/sites/prod-myapp",
  "target": "/subscriptions/.../providers/Microsoft.ServiceBus/namespaces/cg-dev-uks-sbns-1",
  "category": "DATA",
  "type": "REQUIRED",
  "strength": 0.95,
  "method": "code_repository_scan",
  "description": "Application uses Service Bus cg-dev-uks-sbns-1 (found in repository config)"
}
```

## 🔍 What Gets Scanned

### Configuration File Patterns

| Pattern | Examples | Parsed As |
|---------|----------|-----------|
| `appsettings.json` | appsettings.json | JSON |
| `appsettings.*.json` | appsettings.Production.json | JSON |
| `.env` | .env, .env.production | Key-Value |
| `*.config` | web.config, app.config | XML |

### Service Bus Patterns Detected

| Pattern | Example | Extracts |
|---------|---------|----------|
| Connection String | `Endpoint=sb://namespace.servicebus.windows.net/` | Namespace |
| Topic Reference | `"TopicName": "fifa-1"` | Topic name |
| Queue Reference | `"QueueName": "orders"` | Queue name |
| Namespace Reference | `"Namespace": "cg-dev-uks-sbns-1"` | Namespace |

## ⚠️ Limitations

### Only Scans Configuration Files
- Does **NOT** parse C# code, Python code, etc.
- Only reads config files: appsettings.json, .env
- Hardcoded values in source code are not detected

### Only Matches Discovered Resources
- Scanner **only** creates dependencies for resources already in Neo4j
- If code references a Service Bus in another subscription → No dependency
- If code references a resource not yet discovered → No dependency

### Branch Detection
- Tries `main` → `master` → `develop` in order
- Stops at first successful branch
- Other branches are not scanned

### Repository-to-App Linking
- Best effort matching by name or tags
- May not link repositories without clear App Service association
- Unlinked repos still report findings but don't create dependencies

## 🔄 Integration with Discovery Flow

### Option 1: Manual Scanning
```bash
# 1. Run normal discovery
POST /api/v1/discovery/trigger

# 2. Wait for completion
GET /api/v1/discovery/status

# 3. Scan repositories
POST /api/v1/discovery/scan-repositories

# 4. View updated topology
GET /api/v1/topology
```

### Option 2: Scheduled Scanning
Modify `scheduler.py` to run repository scanning after resource discovery:

```python
async def _discover_azure(self):
    # Normal discovery
    result = await self.discoverer.discover_all_resources()
    
    # Store in Neo4j
    await self._store_resources(result)
    
    # Scan repositories (if configured)
    if settings.azure_devops_organization:
        await self._scan_repositories()
```

## 📈 Performance

### Scan Time
- ~2-5 seconds per repository
- Depends on number of files
- API timeout: 30 seconds per file

### Caching
- No caching currently implemented
- Each scan re-downloads all files
- Future: Cache file contents by commit SHA

### Rate Limiting
- Azure DevOps API: 200 requests/minute
- Built-in rate limiter handles this automatically

## 🧪 Testing

### Unit Test
```python
from topdeck.discovery.azure.code_scanner import CodeRepositoryScanner

scanner = CodeRepositoryScanner("org", "project", "pat")

# Test JSON parsing
results = scanner._parse_file_content(
    '{"ServiceBus": {"Namespace": "test-ns"}}',
    "appsettings.json",
    None
)

assert "test-ns" in results["namespaces"]
```

### Integration Test
```bash
# Set up test repository with sample config
# Run scanner
# Verify dependencies created in Neo4j

pytest tests/discovery/azure/test_code_scanner.py
```

## 🎯 Use Cases

### 1. Complete Dependency Mapping
**Problem**: Heuristic discovery only gives weak signals  
**Solution**: Code scanning provides strong proof of actual usage

### 2. Multi-Subscription Filtering  
**Problem**: Code might reference resources in other subscriptions  
**Solution**: Scanner only creates dependencies for resources in your subscription

### 3. Topic-Level Visibility
**Problem**: Don't know which specific topics each app uses  
**Solution**: Scanner finds exact topic names in configuration

### 4. Risk Analysis Enhancement
**Problem**: Can't assess impact of Service Bus changes  
**Solution**: Strong dependencies enable accurate impact analysis

## 🔮 Future Enhancements

### Phase 1 (Current) ✅
- [x] Scan configuration files
- [x] Parse Service Bus connection strings
- [x] Match to discovered resources
- [x] Create dependencies in Neo4j

### Phase 2 (Planned)
- [ ] Parse actual C# code for Service Bus SDK usage
- [ ] Detect publish vs. subscribe patterns
- [ ] Cache file contents by commit SHA
- [ ] Support GitHub repositories (not just Azure DevOps)

### Phase 3 (Future)
- [ ] Real-time scanning on code commits
- [ ] Webhook integration with Azure DevOps
- [ ] Track which topics are publishers vs. subscribers
- [ ] Analyze message schemas from code

## 📚 Related Documentation

- [Service Bus Enhancement](./SERVICE_BUS_ENHANCEMENT.md)
- [Dependency Mapping Architecture](./dependency_mapping_architecture.md)
- [Enhanced Dependency Mapping](./ENHANCED_DEPENDENCY_MAPPING.md)
