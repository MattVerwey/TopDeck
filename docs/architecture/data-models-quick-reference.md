# TopDeck Data Models - Quick Reference

This is a condensed reference for the TopDeck data models. For full documentation, see [data-models.md](data-models.md).

## Core Node Types

| Node Type | Primary Use | Key Properties |
|-----------|-------------|----------------|
| `:Resource` | Cloud infrastructure | `id`, `resource_type`, `cloud_provider`, `region`, `status` |
| `:Application` | Deployed applications | `id`, `name`, `owner_team`, `environment`, `health_score` |
| `:Repository` | Code repositories | `id`, `platform`, `url`, `default_branch` |
| `:Deployment` | Deployment events | `id`, `version`, `deployed_at`, `status` |
| `:Namespace` | K8s namespaces | `id`, `name`, `cluster_id` |
| `:Pod` | K8s pods | `id`, `name`, `namespace`, `phase` |

## Azure Resource Subtypes

| Resource Type | Label | Common Use Case |
|---------------|-------|-----------------|
| AKS Cluster | `:Resource:AKS` | Container orchestration |
| App Service | `:Resource:AppService` | Web apps, APIs, functions |
| Virtual Machine | `:Resource:VirtualMachine` | Traditional compute |
| SQL Database | `:Resource:SQLDatabase` | Relational database |
| Virtual Network | `:Resource:VirtualNetwork` | Network isolation |
| Subnet | `:Resource:Subnet` | Network segmentation |
| Load Balancer | `:Resource:LoadBalancer` | Traffic distribution |
| Application Gateway | `:Resource:ApplicationGateway` | L7 load balancing, WAF |
| NSG | `:Resource:NSG` | Network security rules |
| Storage Account | `:Resource:StorageAccount` | Blob, file, queue storage |
| Key Vault | `:Resource:KeyVault` | Secrets management |

## Core Relationships

| Relationship | Usage | Key Properties |
|--------------|-------|----------------|
| `DEPENDS_ON` | Resource dependencies | `category`, `strength`, `dependency_type` |
| `CONNECTS_TO` | Network connections | `protocol`, `port`, `frequency`, `latency_avg` |
| `CONTAINS` | Parent-child | `containment_type` |
| `DEPLOYED_TO` | App to infrastructure | `deployment_id`, `version` |
| `BUILT_FROM` | App to code | `branch`, `commit_sha` |
| `SECURED_BY` | Security controls | `rule_type` |
| `ROUTES_TO` | Traffic routing | `routing_rule`, `port`, `protocol` |

## Common Query Patterns

### Find Resource by ID
```cypher
MATCH (r:Resource {id: $resource_id})
RETURN r;
```

### Find All Dependencies
```cypher
MATCH path = (r:Resource {id: $resource_id})-[:DEPENDS_ON*1..5]->(dep)
RETURN dep, length(path) as depth
ORDER BY depth;
```

### Find Resources in Environment
```cypher
MATCH (r:Resource {environment: $env})
RETURN r
ORDER BY r.resource_type, r.name;
```

### Find Application Topology
```cypher
MATCH path = (app:Application {name: $app_name})-[:DEPLOYED_TO]->(r:Resource)
OPTIONAL MATCH (r)-[:DEPENDS_ON*0..3]-(dep:Resource)
RETURN app, r, dep;
```

### Find Network Connections
```cypher
MATCH (r:Resource {id: $resource_id})-[conn:CONNECTS_TO]-(other)
RETURN r, conn, other;
```

### Find AKS Pods
```cypher
MATCH (aks:Resource:AKS {id: $aks_id})-[:CONTAINS*]->(pod:Pod)
RETURN pod;
```

### Find Blast Radius
```cypher
MATCH path = (dependent:Resource)-[:DEPENDS_ON*1..5]->(r:Resource {id: $resource_id})
RETURN DISTINCT dependent, length(path) as impact_distance
ORDER BY impact_distance;
```

### Find Security Gaps (Subnets without NSG)
```cypher
MATCH (subnet:Resource:Subnet)
WHERE NOT (subnet)-[:SECURED_BY]->(:Resource:NSG)
RETURN subnet;
```

### Cost Analysis by Environment
```cypher
MATCH (r:Resource)
WHERE r.cost_per_day IS NOT NULL
RETURN r.environment, sum(r.cost_per_day) as daily_cost
ORDER BY daily_cost DESC;
```

## Initialization

To set up the database schema:

```bash
# Connect to Neo4j and run the schema file
cypher-shell -u neo4j -p password -f docs/architecture/neo4j-schema.cypher
```

Or from Neo4j Browser:
1. Open Neo4j Browser
2. Load `docs/architecture/neo4j-schema.cypher`
3. Execute the file

## Working with the Schema

### Adding a New Resource

```cypher
CREATE (r:Resource:AppService {
  id: '/subscriptions/.../providers/Microsoft.Web/sites/myapp',
  cloud_provider: 'azure',
  resource_type: 'app_service',
  name: 'myapp',
  region: 'eastus',
  status: 'running',
  environment: 'prod',
  discovered_at: datetime(),
  last_seen: datetime()
});
```

### Creating a Dependency

```cypher
MATCH (app:Resource {id: $app_id})
MATCH (db:Resource {id: $db_id})
CREATE (app)-[:DEPENDS_ON {
  category: 'data',
  strength: 0.9,
  dependency_type: 'required',
  discovered_at: datetime()
}]->(db);
```

### Creating a Network Connection

```cypher
MATCH (pod:Pod {id: $pod_id})
MATCH (db:Resource:SQLDatabase {id: $db_id})
CREATE (pod)-[:CONNECTS_TO {
  protocol: 'sql',
  port: 1433,
  discovered_at: datetime()
}]->(db);
```

## Property Conventions

- **IDs**: Use cloud provider's resource ID format (Azure: ARM ID, AWS: ARN, GCP: resource URL)
- **Timestamps**: Use Neo4j `datetime()` type
- **Enums**: Use lowercase strings with underscores (e.g., `"app_service"`, not `"AppService"`)
- **Tags**: Store as map (e.g., `{environment: "prod", team: "platform"}`)
- **Status**: Use standardized values: `"running"`, `"stopped"`, `"error"`, `"degraded"`, `"unknown"`

## Performance Tips

1. **Always use indexes**: Filter on `id`, `resource_type`, `cloud_provider`, `environment` first
2. **Limit traversal depth**: Use `*1..5` instead of `*` for relationship patterns
3. **Use OPTIONAL MATCH**: For relationships that may not exist
4. **Filter early**: Apply WHERE clauses before OPTIONAL MATCH
5. **Batch operations**: Use `UNWIND` for bulk creates/updates

## Next Steps

- Review [data-models.md](data-models.md) for complete documentation
- See [system-architecture.md](system-architecture.md) for how models fit into the system
- Check [issue-003-azure-resource-discovery.md](../issues/issue-003-azure-resource-discovery.md) for implementation guidance
