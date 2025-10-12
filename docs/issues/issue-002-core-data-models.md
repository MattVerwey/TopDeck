# Issue #2: Design Core Data Models

**Labels**: `enhancement`, `architecture`, `priority: high`, `phase-1`

## Description

Define the core data models that will represent cloud resources, relationships, and metadata in TopDeck. These models will be used throughout the application and stored in Neo4j.

## Requirements

### Resource Model
Need to represent:
- Cloud resources (VMs, containers, databases, networking)
- Common properties (ID, name, region, tags, cost)
- Cloud-specific properties
- Resource state and health

### Relationship Model
Need to represent:
- Dependencies (service A depends on service B)
- Network connections (service A calls service B)
- Deployment relationships (code deployed to resource)
- Ownership (team/project owns resource)

### Metadata Model
Need to capture:
- Discovery timestamp
- Last update time
- Change history
- Risk scores
- Performance metrics

## Proposed Node Types

### Cloud Resources
```
Node: Resource
Properties:
  - id: string (unique identifier)
  - cloud_provider: enum (azure, aws, gcp)
  - resource_type: string (vm, container, database, etc.)
  - name: string
  - region: string
  - status: enum (running, stopped, error)
  - tags: map[string]string
  - created_at: timestamp
  - last_seen: timestamp
  - cost_per_day: float
  - properties: json (cloud-specific properties)
```

### Applications
```
Node: Application
Properties:
  - id: string
  - name: string
  - owner_team: string
  - repository_url: string
  - deployment_method: string (aks, app_service, vm, etc.)
  - health_score: float (0-100)
  - last_deployed: timestamp
```

### Code Repositories
```
Node: Repository
Properties:
  - id: string
  - platform: enum (github, azure_devops, gitlab)
  - url: string
  - branch: string
  - last_commit: string
  - last_commit_date: timestamp
```

### Deployments
```
Node: Deployment
Properties:
  - id: string
  - pipeline_id: string
  - version: string
  - deployed_at: timestamp
  - deployed_by: string
  - status: enum (success, failed, in_progress)
```

## Proposed Relationship Types

### Resource Relationships
```
DEPENDS_ON
Properties:
  - type: enum (network, data, configuration)
  - strength: float (0-1, criticality)
  - discovered_at: timestamp

CONNECTS_TO
Properties:
  - protocol: string (http, tcp, sql, etc.)
  - port: int
  - frequency: int (requests per minute)
  - latency_avg: float (ms)

DEPLOYED_TO
Properties:
  - deployment_id: string
  - deployed_at: timestamp
  - version: string
```

### Code Relationships
```
BUILT_FROM
(Application)-[BUILT_FROM]->(Repository)

DEPLOYS_TO
(Repository)-[DEPLOYS_TO]->(Resource)
```

## Example Graph

```
(Repository:github) -[DEPLOYS_TO]-> (Deployment) -[TARGETS]-> (AKS_Cluster)
                                                                     |
(Application) -[BUILT_FROM]-> (Repository)                          |
      |                                                              |
      +-[DEPLOYED_TO]-> (AKS_Cluster) -[CONTAINS]-> (Pods) -[CONNECTS_TO]-> (LoadBalancer)
                             |                                              |
                             +-[USES]-> (ApplicationGateway) <-------------+
                             |
                             +-[DEPENDS_ON]-> (SQLDatabase)
```

## Tasks

- [ ] Create data model documentation
- [ ] Design Neo4j schema
- [ ] Define required indexes for performance
- [ ] Create Cypher queries for common operations
- [ ] Design API models (DTOs) that map to graph models
- [ ] Consider versioning strategy for model evolution
- [ ] Document model in `docs/architecture/data-models.md`

## Considerations

1. **Extensibility**: Models should be extensible for new cloud providers
2. **Performance**: Indexes on frequently queried properties
3. **Versioning**: Plan for model changes over time
4. **Validation**: Define constraints and validation rules
5. **Relationships**: Balance between flexibility and query performance

## Success Criteria

- [ ] All major cloud resources can be represented
- [ ] Relationships capture critical dependencies
- [ ] Schema is documented
- [ ] Query patterns are defined
- [ ] Team review and approval

## Timeline

Week 1-2

## Dependencies

- Issue #1: Technology Stack Decision (for implementation language)

## Related Issues

- Will create follow-up issues for implementation after design approval
