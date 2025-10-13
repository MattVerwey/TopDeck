# Risk Analysis Demo - Complete Guide

## 🎯 What Has Been Accomplished

This implementation demonstrates TopDeck's complete risk analysis capabilities using test data from network graphs, showing dependency detection in **code**, **portal**, and **AKS nodes**.

### ✅ All Requirements Met

1. ✅ **Used test data from network graphs** - 14 nodes, 16 relationships
2. ✅ **Dependency detection working** - Code (Pods), Portal (Azure), AKS (K8s) levels
3. ✅ **SPOF detection** - Found 2 single points of failure
4. ✅ **Blast radius calculation** - Cascade effects analyzed
5. ✅ **End-to-end testing** - Complete application flow validated
6. ✅ **Step-by-step documentation** - Multiple guides provided

## 🚀 Quick Start

### Option 1: Automated (Recommended)

Run the complete end-to-end test with one command:

```bash
./scripts/e2e_risk_analysis_test.sh
```

This will:
1. ✅ Check prerequisites
2. ✅ Start infrastructure (Neo4j, Redis, RabbitMQ)
3. ✅ Create network graph demo data
4. ✅ Run risk analysis demonstrations
5. ✅ Show all results
6. ✅ Provide next steps

### Option 2: Manual Steps

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Wait for Neo4j to be ready (10-15 seconds)
sleep 15

# 3. Create demo data
python scripts/demo_network_graph.py

# 4. Run risk analysis
python scripts/demo_risk_analysis.py
```

## 📊 What Gets Demonstrated

### 1. Network Graph Demo Data

Creates a realistic Azure infrastructure graph:

**Resources Created (14 nodes)**:
- 1 AKS Cluster (aks-demo-prod)
- 3 Kubernetes Namespaces (frontend, backend, data)
- 3 Kubernetes Pods (frontend-web-1, backend-api-1, backend-worker-1)
- 1 Application Gateway (appgw-demo)
- 1 Storage Account (stdemoprod001)
- 1 VM Scale Set (vmss-workers)
- 1 Managed Identity (id-aks-demo)
- 1 Service Principal (sp-demo-deployment)
- 2 Applications (web-frontend, api-backend)

**Relationships Created (16 relationships)**:
- 6 CONTAINS (AKS hierarchy)
- 2 DEPENDS_ON (pod dependencies)
- 2 HAS_ROLE (RBAC)
- 2 DEPLOYED_TO (apps to namespaces)
- 1 ROUTES_TO (App Gateway → AKS)
- 1 AUTHENTICATES_WITH (AKS → Managed Identity)
- 1 ACCESSES (Managed Identity → Storage)
- 1 USES (AKS → VMSS)

### 2. Dependency Detection

Shows three levels of dependencies:

#### Code Level (Application/Pod Dependencies)
```
Frontend Pod (frontend-web-1)
    └─ DEPENDS_ON → Backend Pod (backend-api-1) [http:8080]
        └─ DEPENDS_ON → Storage Account (stdemoprod001)
```

#### Portal Level (Azure Infrastructure)
```
Application Gateway (appgw-demo)
    └─ ROUTES_TO → AKS Cluster (aks-demo-prod)
        ├─ USES → VM Scale Set (vmss-workers)
        └─ AUTHENTICATES_WITH → Managed Identity (id-aks-demo)
            └─ ACCESSES → Storage Account (stdemoprod001)
```

#### AKS Level (Kubernetes Hierarchy)
```
AKS Cluster (aks-demo-prod)
    ├─ CONTAINS → Namespace (frontend)
    │   └─ CONTAINS → Pod (frontend-web-1)
    ├─ CONTAINS → Namespace (backend)
    │   ├─ CONTAINS → Pod (backend-api-1)
    │   └─ CONTAINS → Pod (backend-worker-1)
    └─ CONTAINS → Namespace (data)
```

### 3. Risk Analysis Results

#### Single Points of Failure (SPOF)

**2 SPOFs Detected:**

1. **backend-api-1** (Pod)
   - Has 1 dependent: frontend-web-1
   - Blast radius: 1 resource
   - No redundancy configured
   - Recommendation: Deploy multiple replicas

2. **stdemoprod001** (Storage Account)
   - Has 1 dependent: backend-api-1
   - Blast radius: 2 resources (direct + indirect)
   - No redundancy configured
   - Recommendation: Enable geo-redundancy

#### Blast Radius Analysis

**Example: Storage Account Failure**
```
Storage Account (stdemoprod001) FAILS
    ↓
Directly Affected:
    • backend-api-1 (Pod) - Cannot access data
    ↓
Indirectly Affected (Cascade):
    • frontend-web-1 (Pod) - Backend unavailable

Total Impact:
    • 2 resources affected
    • Estimated downtime: 600s (10 minutes)
    • User impact: Low
```

#### Risk Scores

- **AKS Cluster**: 50-65/100 (High risk)
  - Critical resource type
  - Multiple dependents
  - No redundancy
  
- **Backend API Pod**: 1/100 (Low risk, but SPOF)
  - Single point of failure
  - 1 dependent
  
- **Frontend Pod**: 0/100 (Low risk)
  - Has redundancy potential
  - Not a SPOF

### 4. End-to-End Flow

Complete request flow through the system:

```
User Request
    ↓
[Portal] Application Gateway (appgw-demo)
    ↓ [ROUTES_TO]
[Portal] AKS Cluster (aks-demo-prod)
    ↓ [CONTAINS]
[AKS] Namespace (frontend)
    ↓ [CONTAINS]
[Code] Frontend Pod (frontend-web-1)
    ↓ [DEPENDS_ON via http:8080]
[Code] Backend Pod (backend-api-1)
    ↓ [DEPENDS_ON]
[Portal] Storage Account (stdemoprod001)
```

Each layer analyzed for:
- ✅ Risk score
- ✅ Dependencies
- ✅ SPOF status
- ✅ Blast radius
- ✅ Recommendations

## 📚 Documentation Files

### For Running the Demo

1. **`scripts/e2e_risk_analysis_test.sh`**
   - Automated end-to-end test
   - Checks prerequisites
   - Sets up everything
   - Runs all demonstrations

2. **`scripts/demo_risk_analysis.py`**
   - Main demonstration script
   - Shows all risk analysis features
   - Detailed output with formatting

3. **`scripts/demo_network_graph.py`**
   - Creates test data
   - 14 nodes, 16 relationships
   - Realistic Azure infrastructure

### For Understanding

4. **`RISK_ANALYSIS_DEMO_STEPS.md`** (540 lines)
   - Complete step-by-step guide
   - Manual walkthrough
   - Neo4j query examples
   - Troubleshooting section

5. **`RISK_ANALYSIS_DEMO_SUMMARY.md`** (359 lines)
   - Complete achievement summary
   - Technical details
   - Results breakdown
   - Success metrics

6. **`DEMO_COMPLETE_README.md`** (this file)
   - Overview and quick start
   - What's demonstrated
   - How to use it

### For Reference

7. **`PHASE_3_README.md`**
   - Risk analysis API guide
   - Code examples
   - Integration patterns

8. **`PHASE_3_RISK_ANALYSIS_COMPLETION.md`**
   - Complete implementation docs
   - Test coverage details
   - API endpoints

## 🎨 Visual Exploration

### Neo4j Browser Queries

Open http://localhost:7474 (neo4j/topdeck123) and try:

#### 1. View All Demo Resources
```cypher
MATCH (n) WHERE n.demo = true
RETURN n
LIMIT 50
```

#### 2. View Dependency Graph
```cypher
MATCH path = (n)-[r]->(m) 
WHERE n.demo = true AND m.demo = true
RETURN path
```

#### 3. View Dependency Chain
```cypher
MATCH path = (frontend:Pod {name: 'frontend-web-1'})
    -[:DEPENDS_ON*1..5]->(resource)
WHERE frontend.demo = true
RETURN path
```

#### 4. Find Single Points of Failure
```cypher
MATCH (r)<-[:DEPENDS_ON]-(dependent)
WHERE r.demo = true
AND NOT EXISTS {
    MATCH (r)-[:REDUNDANT_WITH]->()
}
WITH r, count(dependent) as dep_count
WHERE dep_count > 0
RETURN r.name, labels(r)[0] as type, dep_count
ORDER BY dep_count DESC
```

#### 5. View AKS Hierarchy
```cypher
MATCH path = (aks:Resource {name: 'aks-demo-prod'})
    -[:CONTAINS*]->(child)
RETURN path
```

#### 6. View Complete Flow
```cypher
MATCH path = (appgw:Resource {name: 'appgw-demo'})
    -[*1..10]->(resource)
WHERE appgw.demo = true
RETURN path
```

## 🔧 Technical Details

### Code Fixes Applied

1. **Fixed `get_dependency_counts()`**
   - Bug: Called `single()` twice, returned None
   - Fix: Store result in variable first

2. **Updated All Queries for Any Node Type**
   - Before: Only matched `Resource` label
   - After: Matches any node with `id` property
   - Used `COALESCE` for type fallback

3. **Improved Error Handling**
   - Better null checks
   - Clearer error messages
   - Graceful degradation

### Files Modified

- `src/topdeck/analysis/risk/analyzer.py`
  - `_get_resource_details()` - Match any node
  - `_check_redundancy()` - Match any node
  - SPOF detection query - Match any node

- `src/topdeck/analysis/risk/dependency.py`
  - `get_dependency_counts()` - Fixed bug
  - `find_critical_path()` - Match any node
  - `get_dependency_tree()` - Match any node
  - `is_single_point_of_failure()` - Match any node
  - `get_affected_resources()` - Match any node

## ✅ Validation

### Test Results

```bash
# Data verification
docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 \
  "MATCH (n) WHERE n.demo = true RETURN labels(n)[0] as type, count(*) as count"

# Results:
# Application: 2
# ManagedIdentity: 1
# Namespace: 3
# Pod: 3
# Resource: 4
# ServicePrincipal: 1
# Total: 14 nodes ✅

# Relationship verification
docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 \
  "MATCH ()-[r]->() WHERE r.demo = true RETURN type(r) as type, count(*) as count"

# Results: 16 relationships ✅
```

### Risk Analysis Validation

- ✅ Dependencies detected: 2 DEPENDS_ON relationships
- ✅ SPOFs identified: 2 (backend-api-1, stdemoprod001)
- ✅ Blast radius: 2 resources affected by storage failure
- ✅ Risk scores: Calculated for all resources
- ✅ Recommendations: Generated for each assessment

## 🎯 Next Steps

### 1. Explore the Demo

```bash
# View the graph visually
open http://localhost:7474

# Try different queries
# See RISK_ANALYSIS_DEMO_STEPS.md for examples
```

### 2. Start the API

```bash
# Start TopDeck API server
python -m topdeck

# Access documentation
open http://localhost:8000/api/docs

# Try risk endpoints
curl http://localhost:8000/api/v1/risk/spof
```

### 3. Run Your Own Data

```bash
# Configure Azure credentials
cp .env.example .env
# Edit .env with your credentials

# Run discovery
python scripts/test_discovery.py

# Analyze your infrastructure
python scripts/demo_risk_analysis.py
```

### 4. Integrate with CI/CD

```bash
# Add to deployment pipeline
SERVICE_ID="your-service-id"
RISK_SCORE=$(curl -s "http://topdeck:8000/api/v1/risk/resources/$SERVICE_ID/score" \
  | jq -r '.risk_score')

if [ "$RISK_SCORE" -gt 70 ]; then
    echo "⚠️ High risk - schedule maintenance window"
    exit 1
fi
```

### 5. Read More Documentation

- `RISK_ANALYSIS_DEMO_STEPS.md` - Detailed walkthrough
- `RISK_ANALYSIS_DEMO_SUMMARY.md` - Technical summary
- `PHASE_3_README.md` - API usage guide
- `PHASE_3_RISK_ANALYSIS_COMPLETION.md` - Full implementation

## 🏆 Success!

All requirements have been met:

✅ **Test data from network graphs** - Created and loaded  
✅ **Dependency detection** - Working at code, portal, AKS levels  
✅ **SPOF detection** - Identified 2 SPOFs  
✅ **Blast radius** - Calculated cascade effects  
✅ **End-to-end testing** - Complete flow validated  
✅ **Step-by-step documentation** - Multiple guides provided  

The system is fully functional and ready to analyze real infrastructure! 🎉

## 📞 Support

If you encounter issues:

1. Check `RISK_ANALYSIS_DEMO_STEPS.md` for troubleshooting
2. Verify Neo4j is running: `docker ps | grep neo4j`
3. Check logs: `docker logs topdeck-neo4j`
4. Restart services: `docker compose restart`

## 📄 License

See LICENSE file in repository root.
