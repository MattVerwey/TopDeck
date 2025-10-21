# Enhanced Topology and Dependency Analysis

## Overview

TopDeck now provides enhanced topology and dependency analysis features that allow you to see which resources are attached to which, and get an in-depth view of your infrastructure connections and dependencies.

## What's New

### 1. Detailed Resource Attachments

Get comprehensive information about how resources are connected, including:
- Relationship types (DEPENDS_ON, CONNECTS_TO, ROUTES_TO, etc.)
- Relationship properties (ports, protocols, connection strings)
- Attachment context (categorization, criticality)
- Bidirectional attachment information

### 2. Dependency Chains

Trace complete paths through your infrastructure to understand:
- How dependencies cascade through the system
- Multi-hop dependency paths
- Upstream and downstream chains
- Relationship types at each hop

### 3. Comprehensive Attachment Analysis

Get a "bigger picture" view with:
- Total attachments and breakdown by type
- Critical attachment identification
- Attachment strength scores
- Impact radius (how many resources are affected)
- Dependency chain analysis

## New API Endpoints

### 1. Get Resource Attachments

**Endpoint:** `GET /api/v1/topology/resources/{resource_id}/attachments`

**Description:** Get detailed attachment information showing which resources are connected and how.

**Parameters:**
- `resource_id` (path, required): The ID of the resource to analyze
- `direction` (query, optional): Direction to get attachments
  - `upstream` - Resources this resource connects to
  - `downstream` - Resources that connect to this resource
  - `both` (default) - Both directions

**Example Request:**
```bash
curl http://localhost:8000/api/v1/topology/resources/my-app-service/attachments?direction=both
```

**Example Response:**
```json
[
  {
    "source_id": "my-app-service",
    "source_name": "MyAppService",
    "source_type": "app_service",
    "target_id": "my-sql-db",
    "target_name": "MySQLDatabase",
    "target_type": "sql_database",
    "relationship_type": "DEPENDS_ON",
    "relationship_properties": {
      "port": 1433,
      "protocol": "tcp",
      "connection_string": "Server=..."
    },
    "attachment_context": {
      "port": 1433,
      "protocol": "tcp",
      "relationship_category": "dependency",
      "is_critical": true
    }
  },
  {
    "source_id": "my-load-balancer",
    "source_name": "MyLoadBalancer",
    "source_type": "load_balancer",
    "target_id": "my-app-service",
    "target_name": "MyAppService",
    "target_type": "app_service",
    "relationship_type": "ROUTES_TO",
    "relationship_properties": {
      "endpoint": "http://myapp.example.com"
    },
    "attachment_context": {
      "endpoint": "http://myapp.example.com",
      "relationship_category": "connectivity",
      "is_critical": true
    }
  }
]
```

### 2. Get Dependency Chains

**Endpoint:** `GET /api/v1/topology/resources/{resource_id}/chains`

**Description:** Get all dependency chains to understand cascading impacts.

**Parameters:**
- `resource_id` (path, required): The ID of the resource to start from
- `max_depth` (query, optional): Maximum chain depth (1-10, default: 5)
- `direction` (query, optional): Direction to trace chains
  - `upstream` - Resources this depends on (recursively)
  - `downstream` (default) - Resources that depend on this (recursively)

**Example Request:**
```bash
curl http://localhost:8000/api/v1/topology/resources/my-database/chains?direction=downstream&max_depth=5
```

**Example Response:**
```json
[
  {
    "chain_id": "chain_0",
    "resource_ids": ["my-database", "my-api", "my-frontend", "my-cdn"],
    "resource_names": ["MySQLDB", "MyAPI", "MyFrontend", "MyCDN"],
    "resource_types": ["sql_database", "app_service", "app_service", "cdn"],
    "relationships": ["DEPENDS_ON", "DEPENDS_ON", "ROUTES_TO"],
    "chain_length": 3,
    "total_risk_score": 0.0,
    "metadata": {
      "direction": "downstream",
      "start_resource": "my-database"
    }
  },
  {
    "chain_id": "chain_1",
    "resource_ids": ["my-database", "my-batch-job"],
    "resource_names": ["MySQLDB", "MyBatchJob"],
    "resource_types": ["sql_database", "app_service"],
    "relationships": ["DEPENDS_ON"],
    "chain_length": 1,
    "total_risk_score": 0.0,
    "metadata": {
      "direction": "downstream",
      "start_resource": "my-database"
    }
  }
]
```

### 3. Get Comprehensive Attachment Analysis

**Endpoint:** `GET /api/v1/topology/resources/{resource_id}/analysis`

**Description:** Get in-depth analysis with comprehensive metrics and the "bigger picture".

**Parameters:**
- `resource_id` (path, required): The ID of the resource to analyze

**Example Request:**
```bash
curl http://localhost:8000/api/v1/topology/resources/my-app-service/analysis
```

**Example Response:**
```json
{
  "resource_id": "my-app-service",
  "resource_name": "MyAppService",
  "resource_type": "app_service",
  "total_attachments": 5,
  "attachment_by_type": {
    "DEPENDS_ON": 2,
    "CONNECTS_TO": 1,
    "ROUTES_TO": 2
  },
  "critical_attachments": [
    {
      "source_id": "my-app-service",
      "source_name": "MyAppService",
      "source_type": "app_service",
      "target_id": "my-sql-db",
      "target_name": "MySQLDatabase",
      "target_type": "sql_database",
      "relationship_type": "DEPENDS_ON",
      "relationship_properties": {
        "port": 1433
      },
      "attachment_context": {
        "port": 1433,
        "relationship_category": "dependency",
        "is_critical": true
      }
    }
  ],
  "attachment_strength": {
    "DEPENDS_ON": 1.0,
    "CONNECTS_TO": 0.7,
    "ROUTES_TO": 1.0
  },
  "dependency_chains": [
    {
      "chain_id": "chain_0",
      "resource_ids": ["my-app-service", "my-sql-db"],
      "resource_names": ["MyAppService", "MySQLDatabase"],
      "resource_types": ["app_service", "sql_database"],
      "relationships": ["DEPENDS_ON"],
      "chain_length": 1,
      "total_risk_score": 0.0,
      "metadata": {
        "direction": "downstream",
        "start_resource": "my-app-service"
      }
    }
  ],
  "impact_radius": 12,
  "metadata": {
    "analysis_depth": 3,
    "max_chain_length": 3,
    "unique_relationship_types": 3
  }
}
```

## Enhanced Existing Endpoints

### Get Resource Dependencies (Enhanced)

**Endpoint:** `GET /api/v1/topology/resources/{resource_id}/dependencies`

**What's New:** Now includes detailed attachment information in addition to basic dependency lists.

**New Response Fields:**
- `upstream_attachments`: Detailed attachment info for upstream dependencies
- `downstream_attachments`: Detailed attachment info for downstream dependencies

**Example Request:**
```bash
curl http://localhost:8000/api/v1/topology/resources/my-app/dependencies?depth=3&direction=both
```

**Enhanced Response:**
```json
{
  "resource_id": "my-app",
  "resource_name": "MyApp",
  "upstream": [
    {
      "id": "my-database",
      "resource_type": "sql_database",
      "name": "MyDatabase",
      "cloud_provider": "azure",
      "region": "eastus",
      "properties": {...}
    }
  ],
  "downstream": [
    {
      "id": "my-frontend",
      "resource_type": "app_service",
      "name": "MyFrontend",
      "cloud_provider": "azure",
      "region": "eastus",
      "properties": {...}
    }
  ],
  "upstream_attachments": [
    {
      "source_id": "my-app",
      "source_name": "MyApp",
      "source_type": "app_service",
      "target_id": "my-database",
      "target_name": "MyDatabase",
      "target_type": "sql_database",
      "relationship_type": "DEPENDS_ON",
      "relationship_properties": {
        "port": 1433,
        "connection_string": "..."
      },
      "attachment_context": {
        "port": 1433,
        "relationship_category": "dependency",
        "is_critical": true
      }
    }
  ],
  "downstream_attachments": [...],
  "depth": 3
}
```

## Understanding the Data

### Relationship Categories

Relationships are automatically categorized into:

- **dependency**: DEPENDS_ON, USES
- **connectivity**: CONNECTS_TO, ROUTES_TO, ACCESSES
- **deployment**: DEPLOYED_TO, BUILT_FROM, CONTAINS
- **security**: AUTHENTICATES_WITH, AUTHORIZES
- **other**: Any other relationship types

### Critical Attachments

Attachments are marked as critical if they use these relationship types:
- DEPENDS_ON
- AUTHENTICATES_WITH
- ROUTES_TO
- CONNECTS_TO

### Attachment Strength

Strength scores (0.0 - 1.0) are calculated based on:
- Base strength: 0.5
- Is critical: +0.3
- Has properties: +0.2

Higher scores indicate more important/impactful connections.

### Impact Radius

The number of unique resources within 3 hops of the analyzed resource. This helps understand the blast radius of potential failures.

## Use Cases

### 1. Understanding Service Dependencies

**Problem:** "What does my application depend on?"

**Solution:**
```bash
# Get all upstream dependencies and their connection details
curl http://localhost:8000/api/v1/topology/resources/my-app/attachments?direction=upstream
```

### 2. Impact Analysis

**Problem:** "If I take down this database, what breaks?"

**Solution:**
```bash
# Get downstream dependency chains
curl http://localhost:8000/api/v1/topology/resources/my-database/chains?direction=downstream

# Or get comprehensive analysis
curl http://localhost:8000/api/v1/topology/resources/my-database/analysis
```

### 3. Security Review

**Problem:** "What are the critical connections in my infrastructure?"

**Solution:**
```bash
# Get comprehensive analysis which highlights critical attachments
curl http://localhost:8000/api/v1/topology/resources/my-app/analysis
```

The `critical_attachments` field shows all security-critical connections.

### 4. Network Architecture Review

**Problem:** "How are my resources connected? What protocols and ports are in use?"

**Solution:**
```bash
# Get all attachments with detailed connection information
curl http://localhost:8000/api/v1/topology/resources/my-app/attachments?direction=both
```

Check `relationship_properties` for ports, protocols, and endpoints.

### 5. Change Impact Planning

**Problem:** "If I update this service, what dependency chains will be affected?"

**Solution:**
```bash
# Get all dependency chains
curl http://localhost:8000/api/v1/topology/resources/my-service/chains?direction=downstream

# Check impact radius
curl http://localhost:8000/api/v1/topology/resources/my-service/analysis
```

The `impact_radius` field shows how many resources are potentially affected.

## Integration with Existing Features

These enhanced features work seamlessly with TopDeck's existing capabilities:

- **Risk Analysis**: Use attachment data to improve risk scoring
- **Topology Visualization**: Enhanced metadata for richer graph displays
- **Monitoring**: Correlate attachment information with performance metrics
- **Change Management**: Better impact assessment for change tickets

## Best Practices

1. **Start with Analysis Endpoint**: For a quick overview, use the `/analysis` endpoint first
2. **Use Appropriate Depth**: For chains, start with depth 3-5 to avoid overly complex results
3. **Filter by Direction**: Use `upstream` or `downstream` when you know what you're looking for
4. **Check Critical Attachments**: Always review critical attachments for security and reliability
5. **Monitor Impact Radius**: Resources with high impact radius need extra attention

## Performance Considerations

- Attachment analysis is optimized for resources with up to 100 connections
- Chain depth is limited to 10 hops maximum
- Impact radius is calculated within 3 hops for performance
- Results are not cached; consider caching at the application level for frequently accessed resources

## Troubleshooting

### Empty Results

If you get empty results:
1. Verify the resource ID exists
2. Check that relationships have been discovered and stored in Neo4j
3. Ensure Neo4j is running and accessible

### Resource Not Found (404)

The analysis endpoint returns 404 if the resource doesn't exist. Verify the resource ID is correct.

### Slow Responses

For resources with many connections:
1. Use direction filters to reduce result size
2. Reduce max_depth for chain queries
3. Consider querying specific attachment types only

## Migration from Legacy Endpoints

If you're using the existing dependencies endpoint:

**Old way:**
```bash
curl http://localhost:8000/api/v1/topology/resources/my-app/dependencies
```

**New way (with more detail):**
```bash
# For basic dependencies (still works, now enhanced)
curl http://localhost:8000/api/v1/topology/resources/my-app/dependencies

# For detailed attachments
curl http://localhost:8000/api/v1/topology/resources/my-app/attachments

# For comprehensive analysis
curl http://localhost:8000/api/v1/topology/resources/my-app/analysis
```

The existing dependencies endpoint now includes attachment details, so it's backward compatible but provides more information.

## Example Workflow

Here's a complete workflow for analyzing a resource:

```bash
# 1. Get high-level analysis
curl http://localhost:8000/api/v1/topology/resources/my-app/analysis

# 2. Check specific attachment details
curl http://localhost:8000/api/v1/topology/resources/my-app/attachments?direction=both

# 3. Trace downstream impact
curl http://localhost:8000/api/v1/topology/resources/my-app/chains?direction=downstream&max_depth=5

# 4. Trace upstream dependencies
curl http://localhost:8000/api/v1/topology/resources/my-app/chains?direction=upstream&max_depth=3
```

## Future Enhancements

Planned improvements:
- Visualization of dependency chains
- Attachment filtering by relationship type
- Real-time attachment monitoring
- Automated critical path detection
- Integration with risk analysis scoring
