# TopDeck Topology Examples

This document provides visual examples of how cloud resources link together in TopDeck's graph model.

## Example 1: Simple Web Application on Azure

### Architecture Overview
A basic web application deployed to Azure App Service with SQL Database backend and Key Vault for secrets.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ Application  │         │  Repository  │                     │
│  │   "MyAPI"    │─────────│   (GitHub)   │                     │
│  └──────┬───────┘ BUILT_  └──────────────┘                     │
│         │        FROM                                           │
│         │ DEPLOYED_TO                                           │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                          │
│                                                                  │
│  ┌──────────────┐                                               │
│  │  App Service │                                               │
│  │   "myapi"    │                                               │
│  └──────┬───┬───┘                                               │
│         │   │                                                    │
│         │   └─────────────────┐                                 │
│         │ DEPENDS_ON          │ USES_SECRET_FROM                │
│         │ (data)              │                                 │
│         ▼                     ▼                                 │
│  ┌──────────────┐      ┌──────────────┐                        │
│  │ SQL Database │      │  Key Vault   │                        │
│  │ "myapi-db"   │──────│ "myapi-kv"   │                        │
│  └──────────────┘ USES_└──────────────┘                        │
│                   SECRET_FROM                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Graph Structure (Cypher)

```cypher
// Nodes
(app:Application {name: "MyAPI", environment: "prod"})
(repo:Repository {name: "myapi-repo", platform: "github"})
(appservice:Resource:AppService {name: "myapi", region: "eastus"})
(sqldb:Resource:SQLDatabase {name: "myapi-db", region: "eastus"})
(kv:Resource:KeyVault {name: "myapi-kv", region: "eastus"})

// Relationships
(app)-[:BUILT_FROM]->(repo)
(app)-[:DEPLOYED_TO]->(appservice)
(appservice)-[:DEPENDS_ON {category: "data", strength: 0.9}]->(sqldb)
(appservice)-[:USES_SECRET_FROM {secret_names: ["db-connection"]}]->(kv)
(sqldb)-[:USES_SECRET_FROM {secret_names: ["admin-password"]}]->(kv)
```

---

## Example 2: Microservices on AKS

### Architecture Overview
A microservices application deployed to Azure Kubernetes Service with Application Gateway for ingress.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Application Layer                                │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │Application  │  │Application  │  │Application  │  │ Repository  │       │
│  │ "OrderAPI"  │  │ "UserAPI"   │  │ "Frontend"  │  │  (GitHub)   │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────BUILT_FROM              │
└─────────────────────────────────────────────────────────────┬───────────────┘
                                                              │
                     ┌────────────────────────────────────────┘
                     │ DEPLOYED_TO
                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Infrastructure Layer                                │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        AKS Cluster                                  │    │
│  │  ┌─────────────────────────────────────────────────────────┐       │    │
│  │  │            Namespace: "production"                       │       │    │
│  │  │                                                          │       │    │
│  │  │  ┌─────────┐    ┌─────────┐    ┌─────────┐            │       │    │
│  │  │  │  Pod    │    │  Pod    │    │  Pod    │            │       │    │
│  │  │  │ "order" │    │ "user"  │    │"frontend"│            │       │    │
│  │  │  └────┬────┘    └────┬────┘    └────┬────┘            │       │    │
│  │  │       │              │              │                  │       │    │
│  │  └───────┼──────────────┼──────────────┼──────────────────┘       │    │
│  └──────────┼──────────────┼──────────────┼──────────────────────────┘    │
│             │              │              │                                │
│             │CONNECTS_TO   │CONNECTS_TO   │                                │
│             │(SQL)         │(SQL)         │                                │
└─────────────┼──────────────┼──────────────┼────────────────────────────────┘
              │              │              │
              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Layer                                      │
│                                                                              │
│         ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │
│         │SQL Database │   │SQL Database │   │ Key Vault   │                │
│         │ "orders"    │   │  "users"    │   │ "prod-kv"   │                │
│         └─────────────┘   └─────────────┘   └──────▲──────┘                │
│                                                     │                        │
│                                      USES_SECRET_FROM                        │
└─────────────────────────────────────────────────────────────────────────────┘
              ▲
              │
┌─────────────┴───────────────────────────────────────────────────────────────┐
│                          Network Layer                                       │
│                                                                              │
│  ┌────────────────────┐      ┌────────────────────┐                        │
│  │ Application        │      │  Virtual Network   │                        │
│  │ Gateway            │      │   "prod-vnet"      │                        │
│  │ (Public Ingress)   │      │  10.0.0.0/16       │                        │
│  └──────┬─────────────┘      └──────┬─────────────┘                        │
│         │ ROUTES_TO                 │                                       │
│         │                           │ CONTAINS                              │
│         │                           ▼                                       │
│         │                    ┌────────────┐                                 │
│         └───────────────────▶│   Subnet   │                                 │
│                              │"aks-subnet"│                                 │
│                              │10.0.1.0/24 │                                 │
│                              └─────┬──────┘                                 │
│                                    │ PART_OF_NETWORK                        │
│                                    ▼                                        │
│                              [AKS Cluster]                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Graph Structure (Simplified)

```cypher
// Application Nodes
(order_app:Application {name: "OrderAPI"})
(user_app:Application {name: "UserAPI"})
(frontend_app:Application {name: "Frontend"})
(repo:Repository {name: "microservices", platform: "github"})

// Infrastructure Nodes
(aks:Resource:AKS {name: "prod-aks", region: "eastus"})
(ns:Namespace {name: "production", cluster_id: aks.id})
(pod_order:Pod {name: "order-xyz", namespace: "production"})
(pod_user:Pod {name: "user-abc", namespace: "production"})
(pod_frontend:Pod {name: "frontend-def", namespace: "production"})

// Data Nodes
(db_orders:Resource:SQLDatabase {name: "orders"})
(db_users:Resource:SQLDatabase {name: "users"})
(kv:Resource:KeyVault {name: "prod-kv"})

// Network Nodes
(appgw:Resource:ApplicationGateway {name: "prod-appgw"})
(vnet:Resource:VirtualNetwork {name: "prod-vnet"})
(subnet:Resource:Subnet {name: "aks-subnet"})

// Application Relationships
(order_app)-[:BUILT_FROM]->(repo)
(user_app)-[:BUILT_FROM]->(repo)
(frontend_app)-[:BUILT_FROM]->(repo)
(order_app)-[:DEPLOYED_TO]->(aks)
(user_app)-[:DEPLOYED_TO]->(aks)
(frontend_app)-[:DEPLOYED_TO]->(aks)

// Infrastructure Relationships
(aks)-[:CONTAINS]->(ns)
(ns)-[:CONTAINS]->(pod_order)
(ns)-[:CONTAINS]->(pod_user)
(ns)-[:CONTAINS]->(pod_frontend)

// Data Connections
(pod_order)-[:CONNECTS_TO {protocol: "sql", port: 1433}]->(db_orders)
(pod_user)-[:CONNECTS_TO {protocol: "sql", port: 1433}]->(db_users)
(pod_order)-[:USES_SECRET_FROM]->(kv)
(pod_user)-[:USES_SECRET_FROM]->(kv)

// Network Relationships
(appgw)-[:ROUTES_TO {protocol: "https", port: 443}]->(aks)
(vnet)-[:CONTAINS]->(subnet)
(aks)-[:PART_OF_NETWORK]->(subnet)
(aks)-[:DEPENDS_ON {category: "network"}]->(vnet)
```

---

## Example 3: Multi-Region Application

### Architecture Overview
An application deployed across multiple Azure regions with regional databases and shared Key Vault.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         Global Resources                                   │
│                                                                            │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐          │
│  │ Application  │       │  Repository  │       │  Key Vault   │          │
│  │   "WebApp"   │       │   (GitHub)   │       │   (global)   │          │
│  └──────┬───────┘       └──────┬───────┘       └──────┬───────┘          │
│         │ DEPLOYED_TO          │ BUILT_FROM           │                   │
└─────────┼──────────────────────┼──────────────────────┼───────────────────┘
          │                      │                      │
          │                      │                      │ USES_SECRET_FROM
    ┌─────┴──────┐               │          ┌───────────┴───────────┐
    │            │               │          │                       │
    ▼            ▼               │          ▼                       ▼
┌────────────────────────┐   ┌────────────────────────┐   ┌────────────────────────┐
│   Region: East US      │   │   Region: West US      │   │   Region: Europe       │
│                        │   │                        │   │                        │
│ ┌──────────────┐      │   │ ┌──────────────┐      │   │ ┌──────────────┐      │
│ │ App Service  │      │   │ │ App Service  │      │   │ │ App Service  │      │
│ │  "webapp-e"  │      │   │ │  "webapp-w"  │      │   │ │  "webapp-eu" │      │
│ └──────┬───────┘      │   │ └──────┬───────┘      │   │ └──────┬───────┘      │
│        │ DEPENDS_ON   │   │        │ DEPENDS_ON   │   │        │ DEPENDS_ON   │
│        ▼              │   │        ▼              │   │        ▼              │
│ ┌──────────────┐      │   │ ┌──────────────┐      │   │ ┌──────────────┐      │
│ │ SQL Database │      │   │ │ SQL Database │      │   │ │ SQL Database │      │
│ │   "db-east"  │◄─────┼───┼─│   "db-west"  │◄─────┼───┼─│   "db-eu"    │      │
│ └──────────────┘      │   │ └──────────────┘      │   │ └──────────────┘      │
│         ▲             │   │         ▲             │   │         ▲             │
│         │             │   │         │             │   │         │             │
│         └─────────────┼───┼─────────┴─────────────┼───┼─────────┘             │
│           GEO_        │   │         GEO_          │   │                       │
│        REPLICATION    │   │       REPLICATION     │   │                       │
└───────────────────────┘   └───────────────────────┘   └───────────────────────┘
```

### Key Relationships

```cypher
// Global Resources
(app:Application {name: "WebApp", environment: "prod"})
(repo:Repository {name: "webapp", platform: "github"})
(kv:Resource:KeyVault {name: "global-kv", region: "eastus"})

// East US Region
(app_east:Resource:AppService {name: "webapp-e", region: "eastus"})
(db_east:Resource:SQLDatabase {name: "db-east", region: "eastus"})

// West US Region
(app_west:Resource:AppService {name: "webapp-w", region: "westus"})
(db_west:Resource:SQLDatabase {name: "db-west", region: "westus"})

// Europe Region
(app_eu:Resource:AppService {name: "webapp-eu", region: "northeurope"})
(db_eu:Resource:SQLDatabase {name: "db-eu", region: "northeurope"})

// Application Deployment
(app)-[:BUILT_FROM]->(repo)
(app)-[:DEPLOYED_TO]->(app_east)
(app)-[:DEPLOYED_TO]->(app_west)
(app)-[:DEPLOYED_TO]->(app_eu)

// Regional Dependencies
(app_east)-[:DEPENDS_ON {category: "data"}]->(db_east)
(app_west)-[:DEPENDS_ON {category: "data"}]->(db_west)
(app_eu)-[:DEPENDS_ON {category: "data"}]->(db_eu)

// Secrets Management
(app_east)-[:USES_SECRET_FROM]->(kv)
(app_west)-[:USES_SECRET_FROM]->(kv)
(app_eu)-[:USES_SECRET_FROM]->(kv)

// Geo-Replication
(db_east)-[:GEO_REPLICATES_TO]->(db_west)
(db_east)-[:GEO_REPLICATES_TO]->(db_eu)
```

---

## Example 4: Complex Network Topology

### Architecture Overview
Shows how network resources connect: VNet, Subnets, NSGs, Load Balancer, and Application Gateway.

```
                          [Internet]
                              │
                              │ HTTPS
                              ▼
                    ┌────────────────────┐
                    │ Application Gateway│
                    │  (Public IP)       │
                    │  WAF Enabled       │
                    └──────────┬─────────┘
                               │ ROUTES_TO
                               │ (HTTPS:443)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Virtual Network (10.0.0.0/16)                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            Subnet: "aks-subnet" (10.0.1.0/24)           │    │
│  │            SECURED_BY: NSG-1                            │    │
│  │                                                          │    │
│  │   ┌──────────────┐                                      │    │
│  │   │ AKS Cluster  │                                      │    │
│  │   └──────┬───────┘                                      │    │
│  │          │ CONTAINS                                     │    │
│  │          ▼                                               │    │
│  │   ┌──────────────┐   ┌──────────────┐                  │    │
│  │   │  Pod (API)   │   │  Pod (Web)   │                  │    │
│  │   └──────┬───────┘   └──────┬───────┘                  │    │
│  │          │                   │                          │    │
│  └──────────┼───────────────────┼──────────────────────────┘    │
│             │                   │                               │
│  ┌──────────┼───────────────────┼──────────────────────────┐   │
│  │          │  Subnet: "data-subnet" (10.0.2.0/24)        │   │
│  │          │          SECURED_BY: NSG-2                   │   │
│  │          │ CONNECTS_TO (SQL:1433)                       │   │
│  │          ▼                                               │   │
│  │   ┌──────────────┐   ┌──────────────┐                  │   │
│  │   │ SQL Database │   │ Storage Acct │                  │   │
│  │   └──────────────┘   └──────────────┘                  │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐     │
│  │         Subnet: "gateway-subnet" (10.0.0.0/27)        │     │
│  │         (Reserved for App Gateway)                     │     │
│  └───────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    Network Security Groups                        │
│                                                                   │
│  NSG-1 (aks-subnet)             NSG-2 (data-subnet)              │
│  ┌───────────────────┐          ┌───────────────────┐            │
│  │ Allow 443 from    │          │ Allow 1433 from   │            │
│  │ App Gateway       │          │ aks-subnet        │            │
│  │ Allow 80 from     │          │ Deny all other    │            │
│  │ App Gateway       │          │ inbound           │            │
│  └───────────────────┘          └───────────────────┘            │
└──────────────────────────────────────────────────────────────────┘
```

### Graph Structure

```cypher
// Network Resources
(vnet:Resource:VirtualNetwork {
  name: "prod-vnet",
  address_space: ["10.0.0.0/16"]
})

(subnet_aks:Resource:Subnet {
  name: "aks-subnet",
  address_prefix: "10.0.1.0/24"
})

(subnet_data:Resource:Subnet {
  name: "data-subnet",
  address_prefix: "10.0.2.0/24"
})

(subnet_gateway:Resource:Subnet {
  name: "gateway-subnet",
  address_prefix: "10.0.0.0/27"
})

(nsg1:Resource:NSG {
  name: "nsg-aks",
  security_rules: [
    {name: "Allow443", direction: "inbound", protocol: "tcp", port: 443},
    {name: "Allow80", direction: "inbound", protocol: "tcp", port: 80}
  ]
})

(nsg2:Resource:NSG {
  name: "nsg-data",
  security_rules: [
    {name: "Allow1433", direction: "inbound", protocol: "tcp", port: 1433, source: "10.0.1.0/24"},
    {name: "DenyAll", direction: "inbound", protocol: "*", port: "*", action: "deny"}
  ]
})

(appgw:Resource:ApplicationGateway {
  name: "prod-appgw",
  waf_enabled: true
})

// Compute Resources
(aks:Resource:AKS {name: "prod-aks"})
(pod_api:Pod {name: "api-pod"})
(pod_web:Pod {name: "web-pod"})

// Data Resources
(sqldb:Resource:SQLDatabase {name: "prod-db"})
(storage:Resource:StorageAccount {name: "prodstorage"})

// Network Containment
(vnet)-[:CONTAINS]->(subnet_aks)
(vnet)-[:CONTAINS]->(subnet_data)
(vnet)-[:CONTAINS]->(subnet_gateway)

// Security
(subnet_aks)-[:SECURED_BY]->(nsg1)
(subnet_data)-[:SECURED_BY]->(nsg2)

// Network Membership
(aks)-[:PART_OF_NETWORK]->(subnet_aks)
(sqldb)-[:PART_OF_NETWORK]->(subnet_data)
(storage)-[:PART_OF_NETWORK]->(subnet_data)
(appgw)-[:PART_OF_NETWORK]->(subnet_gateway)

// Routing
(appgw)-[:ROUTES_TO {protocol: "https", port: 443}]->(aks)

// Compute Containment
(aks)-[:CONTAINS]->(pod_api)
(aks)-[:CONTAINS]->(pod_web)

// Data Connections
(pod_api)-[:CONNECTS_TO {protocol: "sql", port: 1433}]->(sqldb)
(pod_web)-[:CONNECTS_TO {protocol: "https", port: 443}]->(storage)
```

---

## Query Examples for These Topologies

### Find Complete Application Stack

```cypher
// For Example 1 (Simple Web App)
MATCH path = (app:Application {name: "MyAPI"})-[*]-(related)
RETURN path;
```

### Find All Microservices and Their Dependencies

```cypher
// For Example 2 (Microservices)
MATCH (ns:Namespace {name: "production"})-[:CONTAINS]->(pod:Pod)
OPTIONAL MATCH (pod)-[:CONNECTS_TO]->(resource:Resource)
RETURN pod.name, collect(resource.name) as dependencies;
```

### Find Regional Deployment Topology

```cypher
// For Example 3 (Multi-Region)
MATCH (app:Application {name: "WebApp"})-[:DEPLOYED_TO]->(service:Resource)
OPTIONAL MATCH (service)-[:DEPENDS_ON]->(dep:Resource)
RETURN service.region, service.name, collect(dep.name) as dependencies
ORDER BY service.region;
```

### Analyze Network Security

```cypher
// For Example 4 (Network Topology)
MATCH (subnet:Resource:Subnet)-[:SECURED_BY]->(nsg:Resource:NSG)
RETURN subnet.name, subnet.address_prefix, nsg.name, nsg.security_rules;
```

### Find Network Path Between Resources

```cypher
// Find path from Application Gateway to SQL Database
MATCH path = shortestPath(
  (appgw:Resource:ApplicationGateway)-[*]-(db:Resource:SQLDatabase)
)
RETURN path;
```

---

## Best Practices for Topology Modeling

1. **Use Appropriate Relationship Types**: Choose the relationship that best describes the connection
2. **Set Relationship Properties**: Include metadata like protocols, ports, and discovery timestamps
3. **Model Both Logical and Physical**: Include both containment and network connections
4. **Track Security Boundaries**: Use `SECURED_BY` to show security controls
5. **Include Cost Allocation**: Tag resources with cost centers and environments
6. **Model Deployment History**: Link applications to repositories and deployments
7. **Capture Change Over Time**: Use timestamps to track when relationships were discovered

---

## See Also

- [data-models.md](data-models.md) - Complete data model documentation
- [data-models-quick-reference.md](data-models-quick-reference.md) - Quick reference guide
- [neo4j-schema.cypher](neo4j-schema.cypher) - Database initialization script
