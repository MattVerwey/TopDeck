# Issue #9: Implement GCP Resource Discovery

**Labels**: `enhancement`, `cloud: gcp`, `priority: high`, `phase-4`

## Description

Implement the GCP resource discovery module that can scan Google Cloud Platform projects and discover all relevant resources for topology mapping. This implementation should leverage Terraform for infrastructure management and follow the patterns established in Azure and AWS discovery.

## Scope

### Resources to Discover

**Compute Resources**:
- Google Kubernetes Engine (GKE) clusters
  - Node pools
  - Pods and deployments (via kubectl)
  - Ingress controllers
- Compute Engine instances
  - Instance groups (managed and unmanaged)
  - Instance templates
- Cloud Functions
- Cloud Run services
- App Engine applications

**Networking**:
- Virtual Private Cloud (VPC) networks
- Subnets
- Firewall rules
- Cloud Load Balancers (HTTP(S), TCP/UDP, Internal)
- Cloud NAT
- Cloud VPN
- Cloud Interconnect
- VPC Peering

**Data Services**:
- Cloud SQL (PostgreSQL, MySQL, SQL Server)
- Cloud Spanner
- Firestore/Datastore
- Cloud Storage buckets
- Memorystore (Redis, Memcached)
- BigQuery datasets

**Configuration**:
- Secret Manager
- Cloud KMS keys

## Requirements

### Authentication
- Support Service Account authentication
- Support Application Default Credentials (ADC)
- Support Workload Identity (when running in GKE)
- Support user credentials for development
- Support cross-project discovery

### Discovery Strategy
- Parallel discovery across multiple regions
- Support for multi-project discovery via Organization
- Incremental discovery (delta sync)
- Resource label awareness
- Handle GCP API rate limits gracefully

### Terraform Integration
- Use Terraform for infrastructure deployment automation
- Generate Terraform configurations from discovered resources
- Maintain state consistency
- Support import of existing resources

## Technical Design

### Module Structure
```
src/discovery/gcp/
├── __init__.py
├── client.py           # GCP client wrapper (google-cloud-sdk)
├── authenticator.py    # Authentication logic
├── discoverer.py       # Main discovery orchestrator
├── resources/
│   ├── compute.py      # GKE, Compute Engine, Cloud Run discovery
│   ├── networking.py   # VPC, Firewall, LB discovery
│   ├── data.py         # Cloud SQL, Spanner, Storage discovery
│   └── config.py       # Secret Manager discovery
├── mapper.py           # Map GCP resources to graph models
├── terraform/          # Terraform integration
│   ├── generator.py    # Generate TF configs
│   └── importer.py     # Import existing resources
└── config.py           # Configuration management
```

### Key Classes

```python
class GCPDiscoverer:
    def __init__(self, credentials, project_id: str):
        """Initialize GCP discoverer with credentials"""
        
    def discover_all(self, regions: List[str] = None) -> List[Resource]:
        """Discover all resources across specified regions"""
        
    def discover_resource_type(self, resource_type: str, region: str) -> List[Resource]:
        """Discover specific resource type in a region"""
        
    def get_resource_relationships(self, resource_id: str) -> List[Relationship]:
        """Get relationships for a specific resource"""
        
    def generate_terraform(self, resources: List[Resource]) -> str:
        """Generate Terraform configuration for resources"""
```

### Configuration

```yaml
# config/gcp.yaml
gcp:
  authentication:
    method: service_account  # or adc, workload_identity
    project_id: ${GCP_PROJECT_ID}
    credentials_file: ${GCP_CREDENTIALS_FILE}
  
  discovery:
    projects:
      - project_id: "my-project-123"
        regions:
          - us-central1
          - us-east1
          - europe-west1
      - project_id: "my-project-456"
        regions:
          - us-central1
    
    resource_types:
      - gke
      - compute_engine
      - cloud_functions
      - cloud_run
      - cloud_sql
      - cloud_storage
      - vpc
      - load_balancer
    
    excluded_labels:
      - environment: test
      - temporary: true
    
    scan_interval: 3600  # seconds
    parallel_workers: 5
    rate_limit:
      requests_per_second: 10
    
  terraform:
    enabled: true
    output_path: infrastructure/terraform/gcp/
    state_backend: gcs
    state_bucket: topdeck-terraform-state
```

## Tasks

- [ ] Set up GCP SDK (google-cloud-python) client libraries
- [ ] Implement authentication module with multi-method support
- [ ] Implement compute resource discovery (GKE, Compute Engine, Cloud Functions, Cloud Run)
- [ ] Implement networking resource discovery (VPC, Firewall, Load Balancers)
- [ ] Implement data service discovery (Cloud SQL, Spanner, Cloud Storage, Memorystore)
- [ ] Implement configuration discovery (Secret Manager, KMS)
- [ ] Build Terraform integration layer
  - [ ] Generate Terraform configurations from discovered resources
  - [ ] Implement Terraform import functionality
  - [ ] State management integration
- [ ] Create resource-to-graph mapper
- [ ] Implement multi-region discovery
- [ ] Implement multi-project discovery via Organization API
- [ ] Implement rate limiting and quota management
- [ ] Add error handling and retry logic with exponential backoff
- [ ] Write unit tests for all modules
- [ ] Write integration tests
- [ ] Create documentation and examples

## Success Criteria

- [ ] Successfully discovers all major GCP resource types
- [ ] Accurately identifies relationships between resources
- [ ] Generates valid Terraform configurations
- [ ] Can import existing resources into Terraform state
- [ ] Handles multi-region discovery efficiently
- [ ] Supports cross-project discovery
- [ ] Properly handles GCP API rate limits and quotas
- [ ] Stores all data in Neo4j graph database
- [ ] Provides consistent interface with Azure and AWS discovery modules
- [ ] Has >80% test coverage
- [ ] Documentation is complete with examples

## Security Considerations

- Use read-only service accounts for discovery
- Never store credentials in code
- Support Workload Identity over service account keys when possible
- Mask sensitive data in logs
- Encrypt credentials at rest
- Use least privilege principle for IAM permissions
- Follow GCP security best practices

## Dependencies

- Issue #1: Technology Stack Decision (must complete first)
- Issue #2: Core Data Models (must complete first)
- Issue #3: Azure Resource Discovery (reference implementation)
- Issue #8: AWS Resource Discovery (parallel development)
- GCP SDK for Python (google-cloud-python libraries)
- Terraform CLI

## Timeline

**Estimated Duration**: 2-3 weeks

**Phase 2 Priority**: High

## Related Issues

- Issue #2: Core Data Models
- Issue #3: Azure Resource Discovery
- Issue #8: AWS Resource Discovery

## Notes

- Leverage Terraform's existing GCP provider for resource definitions
- Follow the same patterns as Azure and AWS discovery for consistency
- GCP uses projects instead of accounts/subscriptions as the primary organizational unit
- Consider using Cloud Asset Inventory API for comprehensive resource discovery
- GCP APIs have different rate limits per API - implement per-API rate limiting
- Some GCP resources are global (e.g., certain load balancers), others are regional
- Support for both legacy App Engine and newer Cloud Run deployments
