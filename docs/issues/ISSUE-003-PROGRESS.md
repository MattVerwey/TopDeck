# Issue #3: Azure Resource Discovery - Progress Report

**Status**: 🚧 In Progress (Foundation Complete)  
**Started**: 2025-10-12  
**Related Issues**: #1 (Technology Stack), #2 (Core Data Models)

## Overview

Implementation of Azure resource discovery module for TopDeck, enabling automated discovery and cataloging of Azure resources across subscriptions.

## Completed Work

### ✅ Schema Validation (Prerequisites)

Before beginning Azure discovery implementation, validated that the Neo4j schema from Issue #2 works correctly with POC data:

**Deliverables**:
- `scripts/validate_schema.py` - Automated schema validation script
- `docs/architecture/SCHEMA_VALIDATION_RESULTS.md` - Complete validation report

**Results**:
- ✅ 6 uniqueness constraints verified working
- ✅ 34 indexes created and confirmed active
- ✅ POC resources successfully stored in Neo4j
- ✅ POC relationships created correctly
- ✅ All query patterns validated
- ⚠️ Existence constraints require Enterprise Edition (will enforce in code)

### ✅ Core Data Models

**File**: `src/topdeck/discovery/models.py`

Implemented cloud-agnostic data models for discovery:

1. **DiscoveredResource**
   - Normalized resource representation
   - Cloud-agnostic properties
   - Extensible for all cloud providers
   - Converts to Neo4j properties

2. **ResourceDependency**
   - Dependency relationships
   - Category and strength tracking
   - Discovery method metadata
   - Converts to Neo4j relationships

3. **DiscoveryResult**
   - Discovery operation results
   - Resource and dependency lists
   - Error tracking
   - Timing and metrics

### ✅ Azure Resource Mapper

**File**: `src/topdeck/discovery/azure/mapper.py`

Implemented mapping from Azure SDK resources to TopDeck model:

**Features**:
- Maps 14+ Azure resource types to normalized types
- Extracts resource group from ARM ID
- Extracts subscription ID from ARM ID
- Maps provisioning state to TopDeck status
- Extracts environment from tags (multiple tag key patterns)
- Handles missing/optional properties gracefully

**Supported Resource Types**:
- ✅ Microsoft.Compute/virtualMachines → virtual_machine
- ✅ Microsoft.Web/sites → app_service
- ✅ Microsoft.ContainerService/managedClusters → aks
- ✅ Microsoft.Sql/servers/databases → sql_database
- ✅ Microsoft.Storage/storageAccounts → storage_account
- ✅ Microsoft.Network/loadBalancers → load_balancer
- ✅ Microsoft.Network/applicationGateways → application_gateway
- ✅ Microsoft.Network/virtualNetworks → virtual_network
- ✅ Microsoft.Network/networkSecurityGroups → network_security_group
- ✅ Microsoft.KeyVault/vaults → key_vault
- ✅ Microsoft.Cache/redis → redis_cache
- ✅ Plus PostgreSQL, MySQL, Cosmos DB, and more

### ✅ Azure Discoverer

**File**: `src/topdeck/discovery/azure/discoverer.py`

Implemented main orchestrator for Azure discovery:

**Features**:
- Azure SDK integration (ResourceManagementClient)
- Multiple authentication methods:
  - DefaultAzureCredential (Azure CLI, Managed Identity)
  - Service Principal (tenant ID, client ID, client secret)
  - Custom credential objects
- Discover all resources in subscription
- Filter by resource groups
- Async/await support for future concurrency
- Basic dependency detection (heuristic-based)
- Error handling and reporting

**Usage**:
```python
discoverer = AzureDiscoverer(subscription_id="...")
result = await discoverer.discover_all_resources()
```

### ✅ Neo4j Client

**File**: `src/topdeck/storage/neo4j_client.py`

Implemented Neo4j database client for resource storage:

**Features**:
- Connection management
- Resource CRUD operations:
  - Create resource
  - Upsert resource (create or update)
  - Get resource by ID
  - Get resources by type
- Dependency operations:
  - Create DEPENDS_ON relationships
  - Get dependencies for resource
- Query helpers
- Context manager support
- Bulk operations support

### ✅ Tests

**File**: `tests/discovery/azure/test_mapper.py`

Implemented comprehensive test suite for Azure mapper:

**Test Coverage**:
- Resource type mapping (known and unknown types)
- Resource ID parsing (resource group, subscription)
- Provisioning state mapping
- Environment tag extraction
- Complete resource mapping (minimal and full)
- Edge cases and error handling

**Test Count**: 20+ test cases covering all mapper functionality

### ✅ Documentation

**Files**:
- `src/topdeck/discovery/README.md` - Discovery module overview
- `src/topdeck/discovery/azure/README.md` - Comprehensive Azure discovery guide

**Documentation Includes**:
- Architecture overview
- Usage examples
- Authentication patterns
- Data model reference
- Testing guide
- Future enhancements roadmap
- Contributing guidelines

## Remaining Work

### 🚧 Specialized Resource Discovery

**File**: `src/topdeck/discovery/azure/resources.py` (placeholder)

Need to implement detailed discovery for each resource category:

1. **Compute Resources**
   - Virtual Machines (detailed configuration)
   - VM Scale Sets
   - App Services (connection strings, app settings)
   - AKS clusters (node pools, configurations)

2. **Networking Resources**
   - Virtual Networks (subnets, peering)
   - Load Balancers (backend pools, rules)
   - Application Gateways (routing rules)
   - NSGs (security rules)
   - Private Endpoints

3. **Data Resources**
   - SQL Databases (server properties, firewall rules)
   - Cosmos DB (accounts, databases)
   - Storage Accounts (containers, file shares)
   - Redis Cache

4. **Configuration Resources**
   - Key Vaults (secrets, certificates)
   - App Configuration stores

### 🚧 Advanced Dependency Detection

Current implementation uses simple heuristics. Need to implement:

1. **Configuration Parsing**
   - Parse App Service connection strings
   - Parse environment variables
   - Detect database connection configurations

2. **Network Analysis**
   - Parse VNet peering relationships
   - Analyze subnet associations
   - Detect private endpoint connections
   - Parse load balancer backend pools

3. **Azure Resource Graph**
   - Query built-in relationships
   - Get resource dependencies from Azure
   - Cross-subscription relationships

4. **Kubernetes Integration**
   - Connect to AKS clusters via kubectl
   - Discover pods, services, deployments
   - Parse service dependencies
   - Map to infrastructure resources

### 🚧 Integration Testing

Need to test with live Azure resources:

1. **Test Subscription Setup**
   - Create test subscription with sample resources
   - Verify authentication methods
   - Test different resource types

2. **End-to-End Testing**
   - Discovery → Mapping → Storage pipeline
   - Verify all resource types discovered
   - Validate relationships in Neo4j
   - Test incremental updates

3. **Performance Testing**
   - Test with large subscriptions (100+ resources)
   - Measure discovery time
   - Identify bottlenecks
   - Test rate limiting

### 🚧 Performance Optimization

1. **Parallel Discovery**
   - Implement worker pools
   - Concurrent resource group scanning
   - Parallel API calls with rate limiting

2. **Incremental Updates**
   - Track last discovery time
   - Only update changed resources
   - Delta sync support
   - Change detection

3. **Caching**
   - Cache frequently accessed resources
   - Cache SDK clients
   - Reduce API calls

### 🚧 Error Handling & Resilience

1. **Robust Error Handling**
   - Handle Azure API errors gracefully
   - Retry with exponential backoff
   - Continue on partial failures
   - Detailed error reporting

2. **Rate Limiting**
   - Respect Azure API rate limits
   - Implement throttling
   - Queue requests when needed

3. **Monitoring & Logging**
   - Structured logging
   - Metrics collection
   - Discovery progress tracking

## Architecture Decisions

### 1. Cloud-Agnostic Data Model

**Decision**: Create normalized `DiscoveredResource` model instead of using Azure SDK objects directly.

**Rationale**:
- Enables multi-cloud support (AWS, GCP)
- Simplifies Neo4j storage layer
- Provides consistent interface for all cloud providers
- Allows cloud-specific properties via flexible `properties` field

**Trade-off**: Extra mapping layer, but worth it for flexibility.

### 2. Mapper Pattern

**Decision**: Separate mapper class (`AzureResourceMapper`) from discoverer.

**Rationale**:
- Single Responsibility Principle
- Easier to test mapping logic
- Can be used independently
- Easier to extend with new resource types

### 3. Heuristic-Based Dependencies

**Decision**: Start with simple heuristics for dependency detection.

**Rationale**:
- Provides immediate value
- Low risk of false positives
- Simple to understand and maintain
- Can be enhanced incrementally

**Future**: Will add configuration parsing and Azure Resource Graph queries.

### 4. Properties as JSON

**Decision**: Store cloud-specific properties as JSON string in Neo4j.

**Rationale**:
- Flexible schema (different properties per resource type)
- No need to update schema for new resource types
- Can store arbitrary Azure properties
- Easy to query and parse when needed

**Alternative Considered**: Dynamic node properties - rejected due to schema complexity.

## Testing Strategy

### Unit Tests ✅
- Azure mapper (20+ test cases)
- Resource type mapping
- ID parsing
- Status mapping
- Complete resource mapping

### Integration Tests 🚧
- End-to-end discovery flow
- Neo4j storage integration
- Azure SDK integration (with mocks)

### Manual Tests 🚧
- Test with live Azure subscription
- Verify all resource types
- Validate relationships
- Performance testing

## Performance Considerations

### Current Implementation
- Single-pass discovery (all resources at once)
- Synchronous API calls
- Simple heuristic dependencies

### Expected Performance
- Small subscription (10-50 resources): ~10-30 seconds
- Medium subscription (50-200 resources): ~30-90 seconds
- Large subscription (200+ resources): ~90-180 seconds

### Bottlenecks
- Azure API rate limits
- Network latency
- Sequential API calls

### Future Optimizations
- Parallel resource discovery
- Batch Neo4j operations
- Caching and incremental updates

## Dependencies

### Required
- ✅ azure-identity - Azure authentication
- ✅ azure-mgmt-resource - Resource management
- ✅ neo4j - Graph database client
- ✅ pydantic - Data validation

### Optional (for detailed discovery)
- 🚧 azure-mgmt-compute - VM details
- 🚧 azure-mgmt-network - Network details
- 🚧 azure-mgmt-containerservice - AKS details
- 🚧 kubernetes - Kubernetes integration

## Success Criteria

### Phase 1: Foundation ✅
- [x] Core data models implemented
- [x] Azure mapper implemented
- [x] Basic discoverer implemented
- [x] Neo4j client implemented
- [x] Unit tests passing
- [x] Documentation complete

### Phase 2: Enhanced Discovery 🚧
- [ ] Specialized resource discovery functions
- [ ] Detailed property extraction
- [ ] Advanced dependency detection
- [ ] Integration tests passing

### Phase 3: Production Ready 🚧
- [ ] Performance optimization
- [ ] Error handling and resilience
- [ ] Rate limiting and throttling
- [ ] Monitoring and logging
- [ ] End-to-end tests with live Azure
- [ ] Performance tests passing

### Phase 4: Advanced Features 🚧
- [ ] Kubernetes integration
- [ ] Azure Resource Graph integration
- [ ] Multi-subscription support
- [ ] Incremental discovery
- [ ] Change detection

## Timeline

- **Week 1** (Current): Foundation complete ✅
- **Week 2**: Enhanced discovery and testing 🚧
- **Week 3**: Production readiness 🚧
- **Week 4**: Advanced features 🚧

## Next Steps

1. **Implement Specialized Discovery Functions**
   - Create detailed discovery for compute resources
   - Add network resource details
   - Implement data resource discovery

2. **Integration Testing**
   - Set up test Azure subscription
   - Test end-to-end flow
   - Validate with real resources

3. **Enhance Dependency Detection**
   - Parse App Service connection strings
   - Analyze network configurations
   - Implement Azure Resource Graph queries

4. **Performance Optimization**
   - Implement parallel discovery
   - Add rate limiting
   - Optimize Neo4j operations

## References

- [Azure SDK for Python](https://docs.microsoft.com/en-us/azure/developer/python/)
- [Azure Resource Manager](https://docs.microsoft.com/en-us/azure/azure-resource-manager/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Issue #3 Requirements](issue-003-azure-resource-discovery.md)

---

**Last Updated**: 2025-10-12  
**Next Review**: End of Week 2
