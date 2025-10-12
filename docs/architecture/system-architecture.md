# TopDeck System Architecture

## Overview

TopDeck is designed as a modular, scalable platform for multi-cloud resource discovery, dependency mapping, and risk analysis. The architecture follows microservices principles with clear separation of concerns.

## High-Level Architecture

```
                            ┌─────────────────┐
                            │   Web Browser   │
                            └────────┬────────┘
                                     │ HTTPS
                                     ▼
                            ┌─────────────────┐
                            │  Load Balancer  │
                            │   / API Gateway │
                            └────────┬────────┘
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
                ▼                    ▼                    ▼
        ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
        │  Discovery   │    │ Integration  │    │   Analysis   │
        │   Service    │    │   Service    │    │   Service    │
        └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
               │                   │                    │
               └───────────────────┼────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌──────────┐   ┌──────────┐   ┌──────────┐
            │  Neo4j   │   │  Redis   │   │ Message  │
            │  Graph   │   │  Cache   │   │  Queue   │
            └──────────┘   └──────────┘   └──────────┘
```

## Core Services

### 1. Discovery Service

**Responsibility**: Discover and catalog cloud resources

**Components**:
- Azure Discovery Worker
- AWS Discovery Worker
- GCP Discovery Worker
- Resource Mapper
- Scheduler

**Key Operations**:
1. Authenticate with cloud providers
2. Enumerate resources
3. Extract metadata and configuration
4. Identify resource relationships
5. Store in graph database

**Technology Considerations**:
- Async/concurrent operations for performance
- Rate limiting for API calls
- Caching for frequently accessed data
- Incremental updates (delta sync)

**Data Flow**:
```
Cloud Provider API
    ↓
Discovery Worker (authenticate, fetch)
    ↓
Resource Parser (normalize data)
    ↓
Relationship Detector (identify connections)
    ↓
Graph Mapper (convert to graph model)
    ↓
Neo4j (persist)
```

### 2. Integration Service

**Responsibility**: Integrate with code repositories and CI/CD platforms

**Components**:
- Azure DevOps Integration
- GitHub Integration
- GitLab Integration
- Pipeline Parser
- Deployment Tracker

**Key Operations**:
1. Connect to code repositories
2. Analyze CI/CD pipelines
3. Track deployment history
4. Link code to infrastructure
5. Extract configuration and secrets (masked)

**Data Flow**:
```
Code Repository (GitHub/ADO/GitLab)
    ↓
Repository Analyzer (clone, parse)
    ↓
Pipeline Parser (extract deployment targets)
    ↓
Deployment Tracker (track runs)
    ↓
Linker (connect to cloud resources)
    ↓
Neo4j (persist relationships)
```

### 3. Analysis Service

**Responsibility**: Perform risk analysis and topology analysis

**Components**:
- Dependency Analyzer
- Risk Scoring Engine
- Impact Calculator
- Anomaly Detector
- Report Generator

**Key Operations**:
1. Traverse dependency graph
2. Calculate risk scores
3. Identify single points of failure
4. Simulate failure scenarios
5. Generate recommendations

**Algorithms**:
- Graph traversal (BFS/DFS)
- PageRank for resource importance
- Critical path analysis
- Blast radius calculation
- Time-series anomaly detection

**Data Flow**:
```
Neo4j Graph
    ↓
Dependency Analyzer (traverse graph)
    ↓
Risk Scoring Engine (calculate scores)
    ↓
Impact Calculator (simulate scenarios)
    ↓
Report Generator (create insights)
    ↓
Cache (Redis) + API Response
```

### 4. Monitoring Service

**Responsibility**: Collect and correlate performance metrics

**Components**:
- Metrics Collector
- Error Correlator
- Anomaly Detector
- Alert Processor

**Key Operations**:
1. Collect metrics from monitoring platforms
2. Aggregate and normalize data
3. Detect anomalies
4. Correlate errors to resources
5. Generate alerts

### 5. API Service

**Responsibility**: Provide REST/GraphQL API for clients

**Endpoints**:
- `GET /api/v1/resources` - List resources
- `GET /api/v1/resources/{id}` - Get resource details
- `GET /api/v1/topology` - Get topology graph
- `GET /api/v1/risk/assessment/{id}` - Get risk assessment
- `GET /api/v1/dependencies/{id}` - Get dependencies
- `GET /api/v1/impact/{id}` - Get impact analysis
- `POST /api/v1/discovery/scan` - Trigger scan
- `GET /api/v1/metrics/{id}` - Get performance metrics

**Features**:
- Authentication & Authorization
- Rate limiting
- Caching
- Pagination
- Filtering & Search
- Real-time updates (WebSocket)

## Data Layer

### Neo4j Graph Database

**Purpose**: Store resource topology and relationships

**Node Types**:
- Resource (cloud resources)
- Application (applications)
- Repository (code repos)
- Deployment (deployments)

**Relationship Types**:
- DEPENDS_ON (dependencies)
- CONNECTS_TO (network connections)
- DEPLOYED_TO (deployment relationships)
- BUILT_FROM (code relationships)

**Indexes**:
```cypher
CREATE INDEX resource_id FOR (r:Resource) ON (r.id);
CREATE INDEX resource_type FOR (r:Resource) ON (r.resource_type);
CREATE INDEX cloud_provider FOR (r:Resource) ON (r.cloud_provider);
```

**Example Query**:
```cypher
// Find all dependencies of a resource
MATCH path = (r:Resource {id: $id})-[:DEPENDS_ON*1..5]->(dep:Resource)
RETURN dep, length(path) as depth
ORDER BY depth;
```

### Redis Cache

**Purpose**: Cache frequently accessed data

**Cached Data**:
- Resource lists
- Risk scores
- Topology snapshots
- API responses

**TTL Strategy**:
- Resource data: 5 minutes
- Risk scores: 15 minutes
- Topology: 10 minutes
- API responses: 1 minute

### Message Queue

**Purpose**: Async task processing

**Queues**:
- `discovery.scan` - Resource discovery jobs
- `integration.sync` - Repository sync jobs
- `analysis.risk` - Risk analysis jobs
- `monitoring.collect` - Metrics collection jobs

## Deployment Architecture

### Container-Based Deployment

```
┌─────────────────────────────────────────────┐
│           Kubernetes Cluster                 │
│                                              │
│  ┌────────────┐  ┌────────────┐            │
│  │ Discovery  │  │Integration │            │
│  │   Pods     │  │   Pods     │            │
│  │ (scaled)   │  │ (scaled)   │            │
│  └────────────┘  └────────────┘            │
│                                              │
│  ┌────────────┐  ┌────────────┐            │
│  │ Analysis   │  │    API     │            │
│  │   Pods     │  │   Pods     │            │
│  │ (scaled)   │  │ (scaled)   │            │
│  └────────────┘  └────────────┘            │
│                                              │
│  ┌────────────┐  ┌────────────┐            │
│  │ Monitoring │  │  Frontend  │            │
│  │   Pods     │  │   Pods     │            │
│  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           Managed Services                   │
│                                              │
│  ┌────────────┐  ┌────────────┐            │
│  │   Neo4j    │  │   Redis    │            │
│  │  (AKS or   │  │ (Azure     │            │
│  │   managed) │  │  Cache)    │            │
│  └────────────┘  └────────────┘            │
│                                              │
│  ┌────────────┐  ┌────────────┐            │
│  │  RabbitMQ  │  │  Key Vault │            │
│  │ (or Azure  │  │  (secrets) │            │
│  │ Svc Bus)   │  │            │            │
│  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────┘
```

### Scaling Strategy

**Horizontal Scaling**:
- Discovery workers: Scale based on queue depth
- API pods: Scale based on request rate
- Analysis pods: Scale based on CPU usage

**Vertical Scaling**:
- Neo4j: Scale based on data size and query performance
- Redis: Scale based on memory usage

## Security Architecture

### Authentication & Authorization

**User Authentication**:
- OAuth 2.0 / OpenID Connect
- Azure AD integration
- RBAC (Role-Based Access Control)

**Service Authentication**:
- Managed Identity (for Azure services)
- Service Principal (for cloud access)
- API Keys (for integrations)

**Access Levels**:
- `viewer` - Read-only access
- `operator` - Can trigger scans
- `admin` - Full access

### Data Security

**At Rest**:
- Encrypted databases
- Encrypted cache
- Secrets in Key Vault

**In Transit**:
- TLS/HTTPS for all communication
- mTLS for service-to-service

**Sensitive Data**:
- Mask credentials in logs
- Hash sensitive values
- Audit all access

## Monitoring & Observability

### Application Monitoring

- Application Insights / Prometheus
- Distributed tracing (OpenTelemetry)
- Custom metrics for business logic
- Health checks and readiness probes

### Logging

- Structured logging (JSON)
- Centralized log aggregation (ELK or Azure Log Analytics)
- Log levels (DEBUG, INFO, WARN, ERROR)
- Correlation IDs for request tracing

### Metrics

**System Metrics**:
- CPU, Memory, Disk usage
- Request rate, latency, errors
- Queue depth, processing time

**Business Metrics**:
- Resources discovered
- Risk scores calculated
- Deployments tracked
- API usage

## Performance Considerations

### Optimization Strategies

1. **Caching**: Aggressive caching of computed data
2. **Batch Processing**: Batch operations where possible
3. **Async Processing**: Use message queues for heavy tasks
4. **Database Optimization**: Proper indexing, query optimization
5. **Connection Pooling**: Reuse connections to external services
6. **Rate Limiting**: Protect against abuse

### Expected Performance

- Discovery scan (500 resources): < 5 minutes
- Risk analysis: < 10 seconds
- API response time (p95): < 200ms
- Topology visualization: < 2 seconds to load

## Future Enhancements

1. **Machine Learning**:
   - Predictive failure analysis
   - Anomaly detection improvements
   - Resource optimization recommendations

2. **Multi-Tenancy**:
   - Support multiple organizations
   - Data isolation
   - Usage-based billing

3. **Advanced Visualization**:
   - 3D topology views
   - Time-based playback
   - AR/VR exploration

4. **Compliance & Governance**:
   - Policy engine
   - Compliance reporting
   - Cost optimization

## References

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Azure SDK Documentation](https://docs.microsoft.com/azure/developer/)
- [AWS SDK Documentation](https://aws.amazon.com/sdk-for-python/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)
