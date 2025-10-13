# Risk Analysis Demo - Step-by-Step Guide

This guide demonstrates TopDeck's risk analysis working with network graph test data, showing dependency detection in code, portal, and AKS nodes.

## Overview

This demonstration shows:
- ✅ Network graph with Azure resources (AKS, Application Gateway, Storage, etc.)
- ✅ Dependency relationships between resources
- ✅ Risk analysis on resources
- ✅ SPOF (Single Point of Failure) detection
- ✅ Blast radius calculation
- ✅ End-to-end application workflow

## Quick Start (Automated)

Run the complete demo automatically:

```bash
./scripts/e2e_risk_analysis_test.sh
```

This script will:
1. Start infrastructure services (Neo4j, Redis, RabbitMQ)
2. Create network graph demo data
3. Run risk analysis demonstrations
4. Show step-by-step results
5. Provide next steps

## Manual Steps (Detailed Walkthrough)

### Step 1: Start Infrastructure Services

Start Neo4j, Redis, and RabbitMQ:

```bash
docker-compose up -d
```

Verify Neo4j is running:

```bash
# Check Neo4j is accessible
curl http://localhost:7474

# Test Neo4j connection
docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 "RETURN 1 as test;"
```

### Step 2: Create Network Graph Demo Data

The demo creates a realistic network graph with:
- **AKS Cluster** with 3 namespaces (frontend, backend, data)
- **3 Pods** with dependencies between them
- **Application Gateway** routing to AKS
- **Storage Account** for persistent data
- **VM Scale Set** for compute nodes
- **Managed Identity** for authentication
- **Service Principal** for RBAC
- **2 Applications** deployed on AKS

Run the network graph demo:

```bash
python scripts/demo_network_graph.py
```

Expected output:
```
🚀 TOPDECK NETWORK GRAPH DEMO
================================================================================

Creating:
  • AKS Cluster with namespaces and pods
  • Application Gateway (ingress)
  • Storage Account (persistent data)
  • VM Scale Set (compute nodes)
  • Managed Identity (Entra ID)
  • Service Principal (Entra ID)
  • Applications deployed on AKS

🔷 Creating AKS Cluster...
   ✅ Created AKS: aks-demo-prod

📦 Creating Kubernetes Namespaces...
   ✅ Created namespace: frontend
   ✅ Created namespace: backend
   ✅ Created namespace: data

... (more output)

✅ DEMO COMPLETE
```

Verify the data was created:

```bash
docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 \
  "MATCH (n) WHERE n.demo = true RETURN count(n) as count;"
```

### Step 3: View Network Graph in Neo4j Browser

Open Neo4j Browser:
- **URL**: http://localhost:7474
- **Username**: neo4j
- **Password**: topdeck123

#### Query 1: View All Demo Resources

```cypher
MATCH (n) WHERE n.demo = true
RETURN n
LIMIT 50
```

This shows all demo resources: AKS, pods, namespaces, app gateway, storage, etc.

#### Query 2: View Dependency Graph

```cypher
MATCH path = (n)-[r]->(m) 
WHERE n.demo = true AND m.demo = true
RETURN path
```

This visualizes the complete network graph with all relationships.

#### Query 3: View DEPENDS_ON Relationships

```cypher
MATCH (source)-[r:DEPENDS_ON]->(target)
WHERE source.demo = true AND target.demo = true
RETURN source.name as source, 
       target.name as target,
       r.protocol as protocol,
       r.port as port
```

This shows dependency relationships including:
- **Frontend Pod → Backend Pod** (http:8080)
- Pods depending on other resources

#### Query 4: View AKS Hierarchy

```cypher
MATCH path = (aks:AKS)-[:CONTAINS*]->(child)
WHERE aks.demo = true
RETURN path
```

This shows:
- AKS → Namespaces → Pods
- The containment hierarchy

#### Query 5: View Network Flow

```cypher
MATCH (appgw:ApplicationGateway {demo: true})
      -[r1:ROUTES_TO]->(aks:AKS)
      -[r2:CONTAINS]->(ns:Namespace)
      -[r3:CONTAINS]->(pod:Pod)
RETURN appgw, r1, aks, r2, ns, r3, pod
```

This shows the complete network flow:
- Application Gateway → AKS → Namespace → Pods

### Step 4: Run Risk Analysis Demo

Run the risk analysis demonstration:

```bash
python scripts/demo_risk_analysis.py
```

This script demonstrates:

#### 4.1 Demo Data Verification
```
📊 Checking Demo Data
Found X demo resources in Neo4j
```

#### 4.2 Resource Listing
```
📊 Demo Resources
Available resources:
  • Resource             aks-demo-prod
  • ApplicationGateway   appgw-demo
  • StorageAccount       stdemoprod001
  • VMSS                 vmss-demo-nodes
  • Pod                  frontend-pod-abc123
  • Pod                  backend-pod-def456
  • Pod                  data-pod-ghi789
  ...
```

#### 4.3 Dependency Analysis
```
📊 Dependency Analysis

🔗 DEPENDS_ON Relationships:

  1. Pod: frontend-pod-abc123
     └─> Pod: backend-pod-def456
         Protocol: http, Port: 8080

  2. Pod: backend-pod-def456
     └─> Pod: data-pod-ghi789
         Protocol: http, Port: 8080

✅ Found 2 dependency relationships

🔗 Other Relationships:

  1. ApplicationGateway: appgw-demo
     --[ROUTES_TO]--> Resource: aks-demo-prod

  2. Resource: aks-demo-prod
     --[CONTAINS]--> Namespace: frontend

  ...
```

#### 4.4 Risk Analysis on AKS Cluster
```
📊 Risk Analysis: AKS Cluster

Analyzing: aks-demo-prod
ID: /subscriptions/.../aks-demo-prod

📊 Risk Assessment Results:
   Risk Score: 65/100
   Risk Level: high
   Criticality: 85/100
   Single Point of Failure: Yes ⚠️
   Blast Radius: 8 resources
   Dependencies: 3
   Dependents: 5

💡 Recommendations:
   1. This resource is a single point of failure - consider adding redundancy
   2. High blast radius detected - implement circuit breakers
   3. Critical resource type (aks) - increase monitoring
```

#### 4.5 Risk Analysis on Pods
```
📊 Risk Analysis: Pods

Found 3 pods to analyze

🔍 Analyzing: frontend-pod-abc123
   Risk Score: 45/100
   Risk Level: medium
   SPOF: No ✅
   Blast Radius: 0
   Dependencies: 1
   Dependents: 0

🔍 Analyzing: backend-pod-def456
   Risk Score: 55/100
   Risk Level: medium
   SPOF: Yes ⚠️
   Blast Radius: 1
   Dependencies: 1
   Dependents: 1

🔍 Analyzing: data-pod-ghi789
   Risk Score: 65/100
   Risk Level: high
   SPOF: Yes ⚠️
   Blast Radius: 2
   Dependencies: 0
   Dependents: 1
```

#### 4.6 SPOF Detection
```
📊 Single Point of Failure Detection

⚠️  Found 3 Single Points of Failure:

1. aks-demo-prod (aks)
   Risk Score: 65/100
   Dependents: 5
   Blast Radius: 8
   Recommendations:
      • This resource is a single point of failure - consider adding redundancy
      • High blast radius detected - implement circuit breakers

2. backend-pod-def456 (pod)
   Risk Score: 55/100
   Dependents: 1
   Blast Radius: 1
   Recommendations:
      • This resource is a single point of failure - consider adding redundancy
      • Deploy multiple replicas for high availability

3. data-pod-ghi789 (pod)
   Risk Score: 65/100
   Dependents: 1
   Blast Radius: 2
   Recommendations:
      • This resource is a single point of failure - consider adding redundancy
      • Deploy multiple replicas for high availability
```

#### 4.7 Blast Radius Calculation
```
📊 Blast Radius Calculation

Calculating blast radius for: backend-pod-def456

💥 Blast Radius Analysis:
   Total Affected: 1 resources
   Directly Affected: 1
   Indirectly Affected: 0
   Estimated Downtime: 300s
   User Impact: medium

   Directly Affected Resources:
      • frontend-pod-abc123 (pod)

   Affected Services:
      • pod: 1
```

### Step 5: Run Verification Tests

Run the network graph demo tests:

```bash
pytest tests/demo/test_network_graph_demo.py -v
```

Expected output:
```
tests/demo/test_network_graph_demo.py::test_demo_resources_created PASSED
tests/demo/test_network_graph_demo.py::test_aks_cluster_exists PASSED
tests/demo/test_network_graph_demo.py::test_namespaces_exist PASSED
tests/demo/test_network_graph_demo.py::test_pods_exist PASSED
tests/demo/test_network_graph_demo.py::test_application_gateway_exists PASSED
tests/demo/test_network_graph_demo.py::test_storage_account_exists PASSED
tests/demo/test_network_graph_demo.py::test_vmss_exists PASSED
tests/demo/test_network_graph_demo.py::test_managed_identity_exists PASSED
tests/demo/test_network_graph_demo.py::test_service_principal_exists PASSED
tests/demo/test_network_graph_demo.py::test_applications_exist PASSED
tests/demo/test_network_graph_demo.py::test_routes_to_relationship PASSED
tests/demo/test_network_graph_demo.py::test_authenticates_with_relationship PASSED
tests/demo/test_network_graph_demo.py::test_accesses_relationship PASSED
tests/demo/test_network_graph_demo.py::test_has_role_relationship PASSED
tests/demo/test_network_graph_demo.py::test_depends_on_relationship PASSED
tests/demo/test_network_graph_demo.py::test_contains_relationship PASSED
tests/demo/test_network_graph_demo.py::test_deployed_to_relationship PASSED
tests/demo/test_network_graph_demo.py::test_uses_relationship PASSED

==================== 18 passed in X.XXs ====================
```

### Step 6: Test via API (Optional)

Start the TopDeck API server:

```bash
python -m topdeck
```

Test risk analysis endpoints:

#### Get Resource Risk Assessment
```bash
# Replace {resource_id} with actual resource ID from demo
curl http://localhost:8000/api/v1/risk/resources/{resource_id}
```

#### List All SPOFs
```bash
curl http://localhost:8000/api/v1/risk/spof
```

#### Calculate Blast Radius
```bash
curl http://localhost:8000/api/v1/risk/blast-radius/{resource_id}
```

#### Get Quick Risk Score
```bash
curl http://localhost:8000/api/v1/risk/resources/{resource_id}/score
```

### Step 7: Visualize the Graph (Optional)

Run the visualization script:

```bash
python scripts/visualize_demo_graph.py
```

This provides additional queries and visualization examples.

## What the Demo Shows

### 1. Dependencies in Code, Portal, and AKS Nodes

The demo creates realistic dependencies:

**Code Level (Application)**
- Frontend application depends on backend API
- Backend API depends on data service

**Portal Level (Azure Resources)**
- Application Gateway routes to AKS
- AKS uses VM Scale Set for compute
- Pods access Storage Account for data
- Managed Identity authenticates to resources

**AKS Level (Kubernetes)**
- Namespaces contain pods
- Pods have inter-pod dependencies
- Applications are deployed to namespaces

### 2. Risk Analysis Features

**Risk Scoring**
- 0-100 score based on dependencies, type, criticality
- Risk levels: low, medium, high, critical
- Considers SPOF status in scoring

**SPOF Detection**
- Identifies resources with dependents but no redundancy
- Calculates impact of each SPOF
- Provides mitigation recommendations

**Blast Radius**
- Calculates directly and indirectly affected resources
- Estimates downtime and user impact
- Breaks down affected services by type

**Recommendations**
- Specific suggestions for each resource
- Based on risk score, SPOF status, and dependencies
- Actionable mitigation strategies

### 3. End-to-End Application Flow

The complete flow demonstrated:

```
User Request
    ↓
Application Gateway (Portal)
    ↓ [ROUTES_TO]
AKS Cluster (Portal)
    ↓ [CONTAINS]
Namespace (AKS)
    ↓ [CONTAINS]
Frontend Pod (Code)
    ↓ [DEPENDS_ON]
Backend Pod (Code)
    ↓ [DEPENDS_ON]
Data Pod (Code)
    ↓ [ACCESSES]
Storage Account (Portal)
```

Each layer is analyzed for risk:
- Portal resources (Azure resources)
- AKS infrastructure
- Application code (pods/containers)

## Troubleshooting

### Neo4j Connection Error

If you see "Failed to connect to Neo4j":

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs topdeck-neo4j

# Restart Neo4j
docker-compose restart neo4j
```

### No Demo Data Found

If risk analysis shows "No demo data found":

```bash
# Re-run the network graph demo
python scripts/demo_network_graph.py

# Verify data exists
docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 \
  "MATCH (n) WHERE n.demo = true RETURN count(n);"
```

### Python Dependencies Missing

If you see import errors:

```bash
# Install dependencies
pip install -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Next Steps

1. **Explore Neo4j Browser**
   - View the graph visually
   - Try different queries
   - Understand relationships

2. **Use the API**
   - Start API server: `python -m topdeck`
   - Access docs: http://localhost:8000/api/docs
   - Try endpoints with demo data

3. **Run Your Own Data**
   - Configure Azure credentials in `.env`
   - Run discovery: `python scripts/test_discovery.py`
   - Analyze your real infrastructure

4. **Integrate with CI/CD**
   - Add risk checks to deployment pipeline
   - Block deployments with critical risk
   - Generate risk reports

5. **Read Documentation**
   - PHASE_3_README.md - Risk Analysis Quick Start
   - PHASE_3_RISK_ANALYSIS_COMPLETION.md - Complete docs
   - QUICK_START.md - General TopDeck guide

## Summary

This demo shows TopDeck's complete risk analysis capabilities:

✅ **Data Collection**: Network graph with realistic Azure resources  
✅ **Dependency Analysis**: Code, portal, and AKS level dependencies  
✅ **Risk Assessment**: Scoring, classification, and recommendations  
✅ **SPOF Detection**: Identify critical single points of failure  
✅ **Blast Radius**: Calculate cascading failure impact  
✅ **End-to-End Flow**: From user request to data layer  

All working together to provide actionable risk insights! 🎯
