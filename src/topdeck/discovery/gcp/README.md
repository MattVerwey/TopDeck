# GCP Resource Discovery

Discover and map Google Cloud Platform resources to TopDeck's unified topology graph.

## Features

- Discover compute resources (GKE, Compute Engine, Cloud Run, Cloud Functions)
- Discover networking resources (VPC, Firewall, Load Balancers)
- Discover data services (Cloud SQL, Spanner, Storage, Memorystore)
- Discover configuration resources (Secret Manager, KMS)
- Map GCP resources to Neo4j-compatible format
- Extract metadata from GCP labels
- Support for multiple projects and regions

## Components

### GCPResourceMapper (`mapper.py`)

Maps GCP resources to TopDeck's normalized model.

**Supported Resource Types**:
- ✅ Compute Engine Instances (`compute.googleapis.com/Instance`)
- ✅ GKE Clusters (`container.googleapis.com/Cluster`)
- ✅ Cloud Run Services (`run.googleapis.com/Service`)
- ✅ Cloud Functions (`cloudfunctions.googleapis.com/CloudFunction`)
- ✅ App Engine Apps (`appengine.googleapis.com/Application`)
- ✅ Cloud SQL Instances (`sqladmin.googleapis.com/Instance`)
- ✅ Spanner Instances (`spanner.googleapis.com/Instance`)
- ✅ Firestore Databases (`firestore.googleapis.com/Database`)
- ✅ Memorystore Redis (`redis.googleapis.com/Instance`)
- ✅ Storage Buckets (`storage.googleapis.com/Bucket`)
- ✅ BigQuery Datasets (`bigquery.googleapis.com/Dataset`)
- ✅ VPC Networks (`compute.googleapis.com/Network`)
- ✅ Subnets (`compute.googleapis.com/Subnetwork`)
- ✅ Firewall Rules (`compute.googleapis.com/Firewall`)
- ✅ Load Balancers (`compute.googleapis.com/ForwardingRule`)
- ✅ Secret Manager (`secretmanager.googleapis.com/Secret`)
- ✅ KMS Keys (`cloudkms.googleapis.com/CryptoKey`)

**Mapping Features**:
- Resource name parsing (project, zone/region extraction)
- State → status mapping
- Environment detection from labels
- Label normalization (already dict format)
- Neo4j-compatible property formatting

### GCPDiscoverer (`discoverer.py`)

Main orchestrator for GCP resource discovery.

**Features**:
- Multi-region discovery
- Multi-project support
- Async/parallel resource scanning
- Credential management (Service Accounts, ADC)
- Resource filtering by labels

## Data Models

### DiscoveredResource

Represents a discovered GCP resource in normalized format.

**Properties**:
- `id`: GCP resource full name (e.g., "projects/my-project/zones/us-central1-a/instances/my-vm")
- `name`: Resource display name
- `resource_type`: TopDeck normalized type
- `cloud_provider`: "gcp"
- `region`: GCP region (extracted from resource name or location)
- `subscription_id`: GCP project ID
- `status`: Resource status (running, stopped, error, etc.)
- `environment`: Environment label (prod, staging, dev)
- `tags`: Resource labels (dict format)
- `properties`: GCP-specific properties (as JSON)
- `discovered_at`: Discovery timestamp
- `last_seen`: Last seen timestamp

## Usage

```python
from topdeck.discovery.gcp import GCPDiscoverer, GCPResourceMapper

# Initialize discoverer
discoverer = GCPDiscoverer(
    project_id="my-project-123",
    credentials_path="/path/to/service-account.json"
)

# Discover all resources
result = await discoverer.discover_all_resources(
    regions=["us-central1", "us-east1"],
    resource_types=["gke_cluster", "compute_instance", "cloud_sql_instance"]
)

# Access discovered resources
for resource in result.resources:
    print(f"Found: {resource.name} ({resource.resource_type})")
```

### Mapping a Single Resource

```python
from topdeck.discovery.gcp import GCPResourceMapper

# Map a Compute Engine instance
resource = GCPResourceMapper.map_gcp_resource(
    resource_name="projects/my-project/zones/us-central1-a/instances/web-server-01",
    display_name="web-server-01",
    resource_type="compute.googleapis.com/Instance",
    region="us-central1",
    labels={
        "environment": "production",
        "application": "web"
    },
    properties={"machineType": "n1-standard-2"},
    state="RUNNING"
)

# Convert to Neo4j properties
neo4j_props = resource.to_neo4j_properties()
```

### Store in Neo4j

```python
from topdeck.storage.neo4j_client import Neo4jClient

client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
client.connect()

# Store resources
for resource in result.resources:
    client.upsert_resource(resource.to_neo4j_properties())
```

## Neo4j Format

Resources are formatted for Neo4j storage with proper data types:

```python
{
    'id': 'projects/my-project/zones/us-central1-a/instances/web-server-01',
    'name': 'web-server-01',
    'resource_type': 'compute_instance',
    'cloud_provider': 'gcp',
    'region': 'us-central1',
    'subscription_id': 'my-project',  # GCP project ID
    'status': 'running',
    'environment': 'production',
    'tags': {'environment': 'production', 'application': 'web'},  # Dict format
    'properties': '{"machineType": "n1-standard-2"}',  # JSON string
    'discovered_at': '2024-01-01T12:00:00',  # ISO format
    'last_seen': '2024-01-01T12:00:00'
}
```

## Configuration

GCP configuration is managed through the main TopDeck settings:

```python
# Environment variables
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=my-project-123
```

Or programmatically:

```python
from topdeck.common.config import Settings

settings = Settings(
    google_application_credentials="/path/to/service-account.json",
    gcp_project_id="my-project-123"
)
```

## Authentication

GCP supports multiple authentication methods:

1. **Service Account** (recommended for production):
   ```python
   discoverer = GCPDiscoverer(
       project_id="my-project",
       credentials_path="/path/to/service-account.json"
   )
   ```

2. **Application Default Credentials** (ADC):
   ```python
   # Set GOOGLE_APPLICATION_CREDENTIALS environment variable
   discoverer = GCPDiscoverer(project_id="my-project")
   ```

3. **Workload Identity** (when running in GKE):
   ```python
   # Automatically uses workload identity
   discoverer = GCPDiscoverer(project_id="my-project")
   ```
