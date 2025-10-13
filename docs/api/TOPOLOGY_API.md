# Topology API Documentation

## Overview

The Topology API provides endpoints for retrieving network topology data, resource dependencies, and data flows. These endpoints enable interactive visualization and drill-down capabilities for the TopDeck platform.

## Base URL

```
/api/v1/topology
```

## Endpoints

### GET /api/v1/topology

Get complete topology graph with optional filtering.

**Parameters:**
- `cloud_provider` (optional, string): Filter by cloud provider (`azure`, `aws`, `gcp`)
- `resource_type` (optional, string): Filter by resource type
- `region` (optional, string): Filter by region

**Response:**
```json
{
  "nodes": [
    {
      "id": "resource-123",
      "resource_type": "pod",
      "name": "web-app-pod",
      "cloud_provider": "azure",
      "region": "eastus",
      "properties": {},
      "metadata": {}
    }
  ],
  "edges": [
    {
      "source_id": "resource-123",
      "target_id": "resource-456",
      "relationship_type": "DEPENDS_ON",
      "flow_type": "https",
      "properties": {}
    }
  ],
  "metadata": {
    "total_nodes": 10,
    "total_edges": 15,
    "filters": {
      "cloud_provider": "azure",
      "resource_type": null,
      "region": null
    }
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/topology?cloud_provider=azure&region=eastus"
```

---

### GET /api/v1/topology/resources/{resource_id}/dependencies

Get dependencies for a specific resource.

**Path Parameters:**
- `resource_id` (required, string): Resource identifier

**Query Parameters:**
- `depth` (optional, integer, 1-10, default=3): Maximum depth to traverse
- `direction` (optional, string, default="both"): Direction to traverse
  - `upstream`: Resources this depends on
  - `downstream`: Resources that depend on this
  - `both`: Both directions

**Response:**
```json
{
  "resource_id": "resource-123",
  "resource_name": "web-app-pod",
  "upstream": [
    {
      "id": "resource-456",
      "resource_type": "database",
      "name": "main-db",
      "cloud_provider": "azure",
      "region": "eastus",
      "properties": {},
      "metadata": {}
    }
  ],
  "downstream": [
    {
      "id": "resource-789",
      "resource_type": "load_balancer",
      "name": "app-lb",
      "cloud_provider": "azure",
      "region": "eastus",
      "properties": {},
      "metadata": {}
    }
  ],
  "depth": 3
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/topology/resources/web-app-pod/dependencies?depth=3&direction=both"
```

---

### GET /api/v1/topology/flows

Get data flow paths through the system.

**Query Parameters:**
- `flow_type` (optional, string): Filter by flow type
  - `http`, `https`, `database`, `storage`, `cache`, `message_queue`, `internal`
- `start_resource_type` (optional, string): Filter by starting resource type
  - e.g., `load_balancer`, `pod`, `gateway`

**Response:**
```json
[
  {
    "id": "flow_0",
    "name": "load_balancer -> gateway -> pod -> database",
    "path": ["lb-123", "gw-456", "pod-789", "db-012"],
    "flow_type": "https",
    "nodes": [
      {
        "id": "lb-123",
        "resource_type": "load_balancer",
        "name": "app-lb",
        "cloud_provider": "azure",
        "region": "eastus",
        "properties": {},
        "metadata": {}
      }
    ],
    "edges": [
      {
        "source_id": "lb-123",
        "target_id": "gw-456",
        "relationship_type": "ROUTES_TO",
        "flow_type": "https",
        "properties": {}
      }
    ],
    "metadata": {
      "pattern": ["load_balancer", "gateway", "pod", "database"]
    }
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/topology/flows?flow_type=https&start_resource_type=load_balancer"
```

---

## Use Cases

### Visualize Full Topology

Get all resources and relationships for a specific cloud provider:

```bash
curl "http://localhost:8000/api/v1/topology?cloud_provider=azure"
```

### Drill Down into Resource

Get all dependencies for a specific resource:

```bash
curl "http://localhost:8000/api/v1/topology/resources/my-app-pod/dependencies?depth=5"
```

### Trace Request Paths

Get HTTP/HTTPS flows starting from load balancers:

```bash
curl "http://localhost:8000/api/v1/topology/flows?flow_type=https&start_resource_type=load_balancer"
```

### Database Connections

Find all database connections in the system:

```bash
curl "http://localhost:8000/api/v1/topology/flows?flow_type=database"
```
