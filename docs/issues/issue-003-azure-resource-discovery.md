# Issue #3: Implement Azure Resource Discovery

**Labels**: `enhancement`, `cloud: azure`, `priority: high`, `phase-1`

## Description

Implement the Azure resource discovery module that can scan an Azure subscription and discover all relevant resources for topology mapping.

## Scope

### Resources to Discover

**Compute Resources**:
- Azure Kubernetes Service (AKS) clusters
  - Node pools
  - Pods and deployments (via kubectl)
  - Ingress controllers
- App Services
  - Web Apps
  - Function Apps
  - App Service Plans
- Virtual Machines
  - VM Scale Sets
  - Availability Sets

**Networking**:
- Virtual Networks (VNets)
- Subnets
- Network Security Groups (NSGs)
- Load Balancers
- Application Gateways
- Public IP Addresses
- Private Endpoints

**Data Services**:
- Azure SQL Databases
- Cosmos DB accounts
- Storage Accounts
- Redis Cache
- MySQL/PostgreSQL servers

**Configuration**:
- Key Vaults
- App Configuration stores

## Requirements

### Authentication
- Support Service Principal authentication
- Support Managed Identity
- Support Azure CLI authentication (for development)
- Securely store and manage credentials

### Discovery Process
1. **Enumerate Subscriptions**: List all accessible subscriptions
2. **Discover Resources**: Scan each subscription for resources
3. **Extract Metadata**: Get detailed configuration for each resource
4. **Identify Relationships**: Determine connections between resources
5. **Store in Graph**: Save to Neo4j with proper relationships

### Data to Extract

For each resource:
- Basic properties (ID, name, location, tags, resource group)
- Configuration (SKU, pricing tier, settings)
- Network configuration (IP addresses, DNS, ports)
- Connection strings and dependencies
- Cost information
- Health/status

### Performance Considerations
- Parallel resource discovery across resource groups
- Rate limiting to respect Azure API limits
- Caching of resource data
- Incremental updates (only update changed resources)

## Technical Design

### Module Structure
```
src/discovery/azure/
├── __init__.py
├── client.py           # Azure client wrapper
├── authenticator.py    # Authentication logic
├── discoverer.py       # Main discovery orchestrator
├── resources/
│   ├── compute.py      # AKS, App Service, VM discovery
│   ├── networking.py   # VNet, NSG, LB, AppGW discovery
│   ├── data.py         # SQL, Cosmos, Storage discovery
│   └── config.py       # Key Vault, App Config discovery
├── mapper.py           # Map Azure resources to graph models
└── config.py           # Configuration management
```

### Key Classes

```python
class AzureDiscoverer:
    def __init__(self, credentials, subscription_id):
        """Initialize Azure discoverer with credentials"""
        
    def discover_all(self) -> List[Resource]:
        """Discover all resources in subscription"""
        
    def discover_resource_type(self, resource_type: str) -> List[Resource]:
        """Discover specific resource type"""
        
    def get_resource_relationships(self, resource_id: str) -> List[Relationship]:
        """Get relationships for a specific resource"""
```

### Configuration

```yaml
# config/azure.yaml
azure:
  authentication:
    method: service_principal  # or managed_identity, azure_cli
    tenant_id: ${AZURE_TENANT_ID}
    client_id: ${AZURE_CLIENT_ID}
    client_secret: ${AZURE_CLIENT_SECRET}
  
  discovery:
    subscriptions:
      - subscription_id_1
      - subscription_id_2
    
    resource_types:
      - aks
      - app_service
      - virtual_machine
      - sql_database
      - load_balancer
      - application_gateway
    
    excluded_resource_groups:
      - test-*
      - temp-*
    
    scan_interval: 3600  # seconds
    parallel_workers: 5
```

## Tasks

- [ ] Set up Azure SDK dependencies
- [ ] Implement authentication module
- [ ] Implement AKS discovery
- [ ] Implement App Service discovery
- [ ] Implement VM discovery
- [ ] Implement networking resource discovery
- [ ] Implement database resource discovery
- [ ] Implement resource relationship detection
- [ ] Implement graph storage integration
- [ ] Add comprehensive error handling
- [ ] Add logging and monitoring
- [ ] Write unit tests
- [ ] Write integration tests (with mock Azure APIs)
- [ ] Create documentation
- [ ] Add configuration examples

## Testing Strategy

### Unit Tests
- Mock Azure SDK responses
- Test individual resource discovery functions
- Test error handling

### Integration Tests
- Use Azure SDK mocks/test doubles
- Test full discovery flow
- Test graph storage integration

### Manual Testing
- Test against real Azure subscription (dev environment)
- Verify all resource types discovered
- Verify relationships are correct
- Check performance with large subscriptions

## Success Criteria

- [ ] Can authenticate with Azure
- [ ] Discovers all specified resource types
- [ ] Correctly identifies relationships
- [ ] Stores data in Neo4j graph
- [ ] Handles errors gracefully
- [ ] Performance: Can scan subscription with 100+ resources in <5 minutes
- [ ] Tests pass with >80% coverage
- [ ] Documentation complete

## Security Considerations

- Never log credentials or secrets
- Use Azure Key Vault for sensitive configuration
- Follow principle of least privilege for permissions
- Encrypt credentials at rest

## Dependencies

- Issue #1: Technology Stack Decision
- Issue #2: Core Data Models
- Neo4j running and accessible
- Azure subscription for testing

## Timeline

Weeks 2-3

## Related Issues

- Issue #4: AWS Resource Discovery (similar pattern)
- Issue #5: GCP Resource Discovery (similar pattern)
