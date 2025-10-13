# Issue #11: Build Unified Multi-Cloud Resource Abstraction Layer

**Labels**: `enhancement`, `architecture`, `priority: high`, `phase-4`

## Description

Create a unified abstraction layer that provides a consistent interface for working with resources across Azure, AWS, and GCP. This abstraction layer will enable TopDeck to treat resources from different cloud providers in a uniform way, simplifying application logic and enabling cross-cloud features like multi-cloud topology visualization and unified risk analysis.

## Scope

### Core Abstractions

**Resource Model**:
- Unified resource schema that works across all cloud providers
- Common metadata fields (id, name, type, region, tags, state)
- Cloud-specific extensions when needed
- Relationship modeling (depends_on, connects_to, deployed_by)

**Compute Abstraction**:
- Kubernetes clusters (AKS, EKS, GKE)
- Virtual machines (Azure VMs, EC2 instances, Compute Engine)
- Serverless functions (Azure Functions, Lambda, Cloud Functions)
- Container services (Azure Container Apps, ECS/Fargate, Cloud Run)

**Networking Abstraction**:
- Virtual networks (VNet, VPC, VPC)
- Load balancers (Application Gateway/Load Balancer, ALB/NLB, Cloud Load Balancing)
- Ingress controllers
- Firewall rules and security groups

**Data Services Abstraction**:
- Relational databases (Azure SQL, RDS, Cloud SQL)
- NoSQL databases (Cosmos DB, DynamoDB, Firestore)
- Object storage (Blob Storage, S3, Cloud Storage)
- Cache services (Azure Cache, ElastiCache, Memorystore)

**Platform Services Abstraction**:
- Secret management (Key Vault, Secrets Manager, Secret Manager)
- Identity and access (Azure AD, IAM, Cloud IAM)
- Monitoring (Application Insights, CloudWatch, Cloud Monitoring)

## Requirements

### Architecture

- **Factory Pattern**: Use factory pattern for creating cloud-specific implementations
- **Adapter Pattern**: Adapt cloud-specific APIs to common interface
- **Plugin Architecture**: Enable extensibility for new cloud providers
- **Dependency Injection**: Allow easy testing and mocking

### Key Features

- **Common Resource Interface**: All resources implement a base Resource interface
- **Type System**: Strong typing for resource types across clouds
- **Relationship Mapping**: Standardized way to represent resource relationships
- **Provider Translation**: Map cloud-specific concepts to unified model
- **Bidirectional Conversion**: Convert between unified model and cloud-specific models

### Data Models

```python
class Resource:
    """Base resource abstraction"""
    id: str
    name: str
    type: ResourceType
    provider: CloudProvider
    region: str
    metadata: Dict[str, Any]
    tags: Dict[str, str]
    state: ResourceState
    relationships: List[Relationship]
    
class ComputeResource(Resource):
    """Compute resource abstraction"""
    compute_type: ComputeType  # k8s, vm, serverless, container
    endpoints: List[Endpoint]
    configuration: ComputeConfig
    
class NetworkResource(Resource):
    """Network resource abstraction"""
    network_type: NetworkType  # vpc, subnet, lb, firewall
    connectivity: NetworkConnectivity
    security: SecurityConfig
    
class DataResource(Resource):
    """Data service abstraction"""
    data_type: DataType  # sql, nosql, storage, cache
    endpoints: List[Endpoint]
    configuration: DataConfig
```

### Design Principles

- **Cloud-Agnostic Core**: Application logic should not depend on cloud-specific details
- **Minimal Mapping Loss**: Preserve important cloud-specific attributes
- **Extensible**: Easy to add new resource types and cloud providers
- **Testable**: Mock cloud providers for testing
- **Performance**: Efficient serialization and query operations

## Technical Design

### Component Structure

```
src/abstraction/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── resource.py          # Base resource models
│   ├── compute.py           # Compute abstractions
│   ├── networking.py        # Network abstractions
│   ├── data.py              # Data service abstractions
│   └── relationships.py     # Relationship models
├── providers/
│   ├── __init__.py
│   ├── base.py              # Base provider interface
│   ├── azure_provider.py    # Azure implementation
│   ├── aws_provider.py      # AWS implementation
│   └── gcp_provider.py      # GCP implementation
├── mappers/
│   ├── __init__.py
│   ├── azure_mapper.py      # Azure to unified mapping
│   ├── aws_mapper.py        # AWS to unified mapping
│   └── gcp_mapper.py        # GCP to unified mapping
└── registry.py              # Resource type registry
```

### Key Interfaces

```python
class CloudProvider(ABC):
    """Base cloud provider interface"""
    
    @abstractmethod
    def get_resource(self, resource_id: str) -> Resource:
        """Retrieve a resource by ID"""
        
    @abstractmethod
    def list_resources(self, resource_type: ResourceType, 
                      region: str = None) -> List[Resource]:
        """List resources of a specific type"""
        
    @abstractmethod
    def get_relationships(self, resource_id: str) -> List[Relationship]:
        """Get relationships for a resource"""

class ResourceMapper(ABC):
    """Base mapper for translating cloud-specific to unified"""
    
    @abstractmethod
    def to_unified(self, cloud_resource: Any) -> Resource:
        """Convert cloud-specific resource to unified model"""
        
    @abstractmethod
    def from_unified(self, resource: Resource) -> Any:
        """Convert unified model to cloud-specific resource"""
```

## Tasks

- [ ] Design unified resource model schema
- [ ] Implement base Resource, ComputeResource, NetworkResource, DataResource classes
- [ ] Create CloudProvider interface and base implementation
- [ ] Implement AzureProvider with mappers for Azure resources
- [ ] Implement AWSProvider with mappers for AWS resources
- [ ] Implement GCPProvider with mappers for GCP resources
- [ ] Build resource type registry system
- [ ] Implement relationship mapping and querying
- [ ] Create resource factory for instantiating cloud-specific implementations
- [ ] Implement caching layer for performance optimization
- [ ] Build query engine for cross-cloud resource queries
- [ ] Create serialization/deserialization for all resource types
- [ ] Write comprehensive unit tests for all abstractions
- [ ] Write integration tests with actual cloud resources
- [ ] Document the abstraction layer architecture
- [ ] Create examples for using the abstraction layer

## Success Criteria

- [ ] Can query resources using unified interface across all three clouds
- [ ] Resource relationships work consistently across clouds
- [ ] Application code doesn't need cloud-specific logic for basic operations
- [ ] Adding a new cloud provider requires minimal changes to core code
- [ ] Performance is acceptable for production use (< 100ms per resource query)
- [ ] All tests pass with high coverage (> 90%)

## Timeline

**Estimated Duration**: 3-4 weeks

**Phase 4 Priority**: High

## Dependencies

- Issue #3: Azure Resource Discovery (completed)
- Issue #8: AWS Resource Discovery (must be completed or in progress)
- Issue #9: GCP Resource Discovery (must be completed or in progress)
- Issue #2: Core Data Models (provides foundation)

## Related Issues

- Issue #5: Risk Analysis Engine (will use this abstraction)
- Issue #6: Topology Visualization (will use this abstraction)
- Issue #12: Infrastructure Deployment Automation (will use this abstraction)

## Notes

- This abstraction layer is critical for all cross-cloud features
- Consider using Protocol Buffers or similar for efficient serialization
- The abstraction should be flexible enough to handle cloud-specific features when needed
- May want to consider implementing a GraphQL layer on top for querying
- Consider implementing a resource cache to improve performance
- Ensure the abstraction supports incremental discovery (delta updates)

## References

- **Multi-Cloud Patterns**: https://www.cloudflare.com/learning/cloud/what-is-multicloud/
- **Terraform Provider Design**: https://www.terraform.io/docs/extend/how-terraform-works.html
- **Cloud Resource Models**: Azure Resource Graph, AWS CloudFormation, GCP Resource Manager
