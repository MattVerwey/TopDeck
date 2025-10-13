# Network Graph Demo

This demo showcases TopDeck's network graph capabilities with a comprehensive Azure infrastructure setup.

## Overview

The demo creates a realistic production environment with:

- **AKS Cluster** - Azure Kubernetes Service with 3 node pools
- **Entra ID** - Managed Identity and Service Principal for authentication
- **Application Gateway** - Ingress controller routing HTTPS traffic
- **Storage Account** - Persistent storage for applications
- **VM Scale Set** - Compute nodes for AKS
- **Applications on AKS** - Frontend and backend apps deployed to namespaces
- **Pods** - Running containers with dependencies

## Resources Created

### Infrastructure Components

1. **AKS Cluster** (`aks-demo-prod`)
   - Kubernetes version: 1.28.0
   - Node count: 3
   - Network plugin: Azure
   - Namespaces: frontend, backend, data

2. **Application Gateway** (`appgw-demo`)
   - SKU: WAF_v2
   - Frontend port: 443 (HTTPS)
   - Routes to: AKS cluster

3. **Storage Account** (`stdemoprod001`)
   - SKU: Standard_LRS
   - Kind: StorageV2
   - Containers: uploads, backups, logs

4. **VM Scale Set** (`vmss-workers`)
   - SKU: Standard_D2s_v3
   - Capacity: 5 instances
   - OS: Ubuntu 22.04

### Identity & Access

5. **Managed Identity** (`id-aks-demo`)
   - Type: SystemAssigned
   - Assigned to: AKS cluster
   - Permissions: Storage Blob Data Contributor

6. **Service Principal** (`sp-demo-deployment`)
   - Type: Application
   - Roles:
     - AKS Cluster Admin
     - VM Contributor

### Applications

7. **Namespaces**
   - `frontend` - Web tier
   - `backend` - API tier
   - `data` - Data tier

8. **Pods**
   - `frontend-web-1` (3 replicas) - Web application
   - `backend-api-1` (5 replicas) - API service
   - `backend-worker-1` (2 replicas) - Background workers

9. **Applications**
   - `web-frontend` - Health score: 95.5
   - `api-backend` - Health score: 98.2

## Relationships

The demo creates realistic relationships between resources:

### Network Flow
- **Application Gateway** routes HTTPS traffic to **AKS**
- **AKS** contains **Namespaces**
- **Namespaces** contain **Pods**

### Identity & Access
- **AKS** authenticates with **Managed Identity**
- **Managed Identity** accesses **Storage Account**
- **Service Principal** has roles on **AKS** and **VM Scale Set**

### Dependencies
- **Frontend Pod** depends on **Backend Pod** (HTTP calls)
- **Backend API Pod** depends on **Storage Account** (data storage)
- **AKS** uses **VM Scale Set** (compute nodes)

### Application Deployments
- **web-frontend** app deployed to **frontend namespace**
- **api-backend** app deployed to **backend namespace**

## Running the Demo

### Prerequisites

1. Start Neo4j:
   ```bash
   docker compose up -d neo4j
   ```

2. Wait for Neo4j to be ready (about 30 seconds)

### Execute Demo

Run the demo script:
```bash
python scripts/demo_network_graph.py
```

### Run Tests

Verify the demo data:
```bash
python scripts/run_demo_tests.py
```

### Visualize the Graph

View the network graph relationships:
```bash
python scripts/visualize_demo_graph.py
```

## Neo4j Browser Exploration

1. Open Neo4j Browser: http://localhost:7474
2. Login with:
   - Username: `neo4j`
   - Password: `topdeck123`

### Recommended Queries

#### View Full Topology
```cypher
MATCH path = (n)-[r]->(m) 
WHERE n.demo = true AND m.demo = true 
RETURN path
```

#### View AKS Hierarchy
```cypher
MATCH path = (aks:AKS)-[:CONTAINS*]->(child) 
WHERE aks.demo = true 
RETURN path
```

#### View Identity Access Chain
```cypher
MATCH path = (aks:AKS)-[:AUTHENTICATES_WITH]->(mi:ManagedIdentity)
             -[:ACCESSES]->(storage:StorageAccount)
WHERE aks.demo = true
RETURN path
```

#### View Traffic Flow
```cypher
MATCH path = (appgw:ApplicationGateway)-[:ROUTES_TO]->(aks:AKS)
             -[:CONTAINS*]->(pod:Pod)
WHERE appgw.demo = true
RETURN path
```

#### View Service Principal Roles
```cypher
MATCH (sp:ServicePrincipal)-[r:HAS_ROLE]->(resource)
WHERE sp.demo = true
RETURN sp, r, resource
```

#### View Pod Dependencies
```cypher
MATCH (pod:Pod)-[r:DEPENDS_ON]->(target)
WHERE pod.demo = true
RETURN pod, r, target
```

## Graph Statistics

- **Total Nodes**: 14
  - Resources: 4 (AKS, App Gateway, Storage, VM Scale Set)
  - Namespaces: 3
  - Pods: 3
  - Applications: 2
  - Managed Identity: 1
  - Service Principal: 1

- **Total Relationships**: 16
  - CONTAINS: 6
  - DEPENDS_ON: 2
  - HAS_ROLE: 2
  - DEPLOYED_TO: 2
  - USES: 1
  - AUTHENTICATES_WITH: 1
  - ROUTES_TO: 1
  - ACCESSES: 1

## Screenshots

The demo includes screenshots showing:

1. **Full Network Topology** - Complete graph with all nodes and relationships
2. **AKS Node Details** - Properties and configuration of the AKS cluster
3. **AKS Hierarchy** - Tree view of AKS → Namespaces → Pods

## Cleaning Up

To remove demo data:
```cypher
MATCH (n) WHERE n.demo = true DETACH DELETE n
```

Or rerun the demo script (it clears existing demo data automatically).

## Use Cases Demonstrated

This demo showcases TopDeck's ability to:

1. **Visualize Complex Infrastructure** - Multi-tier Azure architecture
2. **Track Identity & Access** - Entra ID integration with resources
3. **Map Dependencies** - Application and infrastructure dependencies
4. **Show Network Flow** - Traffic routing through ingress to applications
5. **Represent Kubernetes** - Hierarchical structure of AKS resources
6. **Link Applications to Infrastructure** - Apps deployed to namespaces

## Next Steps

This demo data can be used to:

- Test topology analysis queries
- Develop risk analysis features
- Build impact analysis tools
- Create dependency mapping visualizations
- Test blast radius calculations
