# Network Graph Demo Summary

## Overview

This feature branch demonstrates TopDeck's network graph capabilities with a comprehensive Azure infrastructure setup, showcasing real-world relationships between cloud resources, identity, and applications.

## What Was Built

### 1. Demo Script (`scripts/demo_network_graph.py`)
A comprehensive Python script that creates a realistic production Azure environment in Neo4j:
- 14 nodes representing various Azure resources
- 16 relationships showing dependencies and connections
- Realistic properties and metadata for each resource

### 2. Test Suite (`scripts/run_demo_tests.py`)
Standalone test runner that validates:
- All resources are created correctly
- All relationships are established
- Properties are set properly
- Network topology paths exist
- Identity access chains work

**Result: 16/16 tests passed (100% success rate)**

### 3. Visualization Tool (`scripts/visualize_demo_graph.py`)
Interactive query tool that displays:
- Complete network topology
- AKS cluster hierarchy
- Identity and access chains
- Service principal roles
- Traffic flow patterns
- Pod dependencies
- Application deployments

### 4. Documentation
- Complete README with setup instructions
- Query examples for Neo4j Browser
- Use case demonstrations
- Architecture diagrams via screenshots

## Azure Resources Demonstrated

### Infrastructure Layer
1. **AKS Cluster** (aks-demo-prod)
   - Kubernetes 1.28.0
   - 3 nodes across 2 pools
   - Azure network plugin

2. **Application Gateway** (appgw-demo)
   - WAF_v2 tier
   - HTTPS on port 443
   - Routes to AKS backend

3. **Storage Account** (stdemoprod001)
   - StorageV2, Standard_LRS
   - Hot tier with 3 containers
   - Used by backend pods

4. **VM Scale Set** (vmss-workers)
   - Standard_D2s_v3 VMs
   - 5 instances
   - Provides compute for AKS

### Identity & Access Layer (Entra ID)
5. **Managed Identity** (id-aks-demo)
   - System-assigned to AKS
   - Storage Blob Data Contributor role
   - Enables AKS to access storage

6. **Service Principal** (sp-demo-deployment)
   - Application type
   - AKS Cluster Admin role
   - VM Contributor role

### Application Layer
7. **Namespaces** (3)
   - frontend - Web tier
   - backend - API tier
   - data - Database tier

8. **Pods** (3)
   - frontend-web-1 (3 replicas)
   - backend-api-1 (5 replicas)
   - backend-worker-1 (2 replicas)

9. **Applications** (2)
   - web-frontend (95.5 health score)
   - api-backend (98.2 health score)

## Relationships Demonstrated

### Network Flow
```
App Gateway --ROUTES_TO--> AKS --CONTAINS--> Namespace --CONTAINS--> Pod
```

### Identity & Access
```
AKS --AUTHENTICATES_WITH--> Managed Identity --ACCESSES--> Storage
Service Principal --HAS_ROLE--> AKS
Service Principal --HAS_ROLE--> VMSS
```

### Dependencies
```
Frontend Pod --DEPENDS_ON--> Backend Pod (HTTP)
Backend Pod --DEPENDS_ON--> Storage (data)
AKS --USES--> VMSS (compute)
```

### Deployments
```
Application --DEPLOYED_TO--> Namespace
```

## Key Features Showcased

1. **Multi-tier Architecture** - Complete infrastructure stack
2. **Identity Integration** - Entra ID with managed identities
3. **Network Topology** - Traffic flow through ingress to pods
4. **Dependency Mapping** - Application and infrastructure dependencies
5. **Kubernetes Hierarchy** - Cluster → Namespace → Pod relationships
6. **RBAC** - Service principal roles on resources
7. **Application Lifecycle** - Deployments to namespaces

## Test Results

All 16 tests passed, validating:
- ✅ AKS cluster exists with correct properties
- ✅ All 3 namespaces created
- ✅ All 3 pods created with replicas
- ✅ Application Gateway configured
- ✅ Storage Account accessible
- ✅ VM Scale Set ready
- ✅ Managed Identity assigned
- ✅ Service Principal has roles
- ✅ Applications deployed
- ✅ Network topology paths complete
- ✅ Identity access chain works
- ✅ All relationships established

## Screenshots

### 1. Full Network Topology
![Full Topology](https://github.com/user-attachments/assets/909f34f1-a766-49ad-9eec-651bb0b8a3b4)

Shows all 14 nodes and 16 relationships in the graph. You can see:
- Orange AKS node at the center
- Blue Application Gateway (appgw-demo)
- Cyan Storage Account (stdemoprod001)
- Yellow Service Principal (sp-demo-deployment)
- Cyan Managed Identity (id-aks-demo)
- Green Namespaces (frontend, backend, data)
- Pink Pods and Applications
- Tan VMSS node

### 2. AKS Node Details
![AKS Details](https://github.com/user-attachments/assets/5b7d6623-1685-4af0-84bc-2808c7bf99cd)

Displays detailed properties of the AKS cluster:
- Cloud provider: azure
- Resource type: aks
- Environment: prod
- Kubernetes version: 1.28.0
- Complete Azure resource ID
- Configuration properties

### 3. AKS Hierarchy
![AKS Hierarchy](https://github.com/user-attachments/assets/3efde3e9-28aa-411d-bbb4-069e27aa8f43)

Shows the hierarchical structure:
- AKS cluster (orange, center)
- 3 Namespaces (tan nodes)
- 3 Pods (green nodes)
- Clear CONTAINS relationships
- One DEPENDS_ON relationship between pods

## How to Run

### Quick Start
```bash
# 1. Start Neo4j
docker compose up -d neo4j

# 2. Wait for Neo4j to be ready (30 seconds)
sleep 30

# 3. Run the demo
python scripts/demo_network_graph.py

# 4. Run tests
python scripts/run_demo_tests.py

# 5. Explore in Neo4j Browser
# Open http://localhost:7474
# Login: neo4j / topdeck123
```

### Explore the Graph
```cypher
-- View everything
MATCH path = (n)-[r]->(m) 
WHERE n.demo = true AND m.demo = true 
RETURN path

-- AKS hierarchy only
MATCH path = (aks:AKS)-[:CONTAINS*]->(child) 
WHERE aks.demo = true 
RETURN path

-- Identity chain
MATCH path = (aks:AKS)-[:AUTHENTICATES_WITH]->(mi:ManagedIdentity)
             -[:ACCESSES]->(storage:StorageAccount)
RETURN path
```

## Use Cases

This demo validates TopDeck can:

1. ✅ **Model Complex Cloud Architectures** - Multi-tier Azure environments
2. ✅ **Track Identity & Access** - Entra ID integration patterns
3. ✅ **Map Dependencies** - Between apps and infrastructure
4. ✅ **Visualize Network Flow** - Traffic routing paths
5. ✅ **Represent Kubernetes** - Hierarchical cluster resources
6. ✅ **Link Apps to Infrastructure** - Deployment relationships
7. ✅ **Support Blast Radius Analysis** - Dependency chains
8. ✅ **Enable Risk Assessment** - Permission and access patterns

## Next Steps

This demo data can be used to:
- Test topology analysis features
- Develop risk scoring algorithms
- Build dependency visualization UI
- Calculate blast radius for incidents
- Generate compliance reports
- Test security posture analysis

## Conclusion

✅ **Demo Complete and Working**

All resources created, all relationships established, all tests passing, and screenshots captured showing the network graph in action. The demo successfully proves TopDeck can model and visualize complex Azure infrastructure with realistic relationships and dependencies.
