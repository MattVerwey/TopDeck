# Issue #5: Implement Risk Analysis Engine

**Labels**: `enhancement`, `analysis`, `priority: high`, `phase-3`

## Description

Implement the core risk analysis engine that assesses the impact of changes and failures across the infrastructure. This is one of the key value propositions of TopDeck.

## Requirements

### Core Capabilities

1. **Dependency Analysis**
   - Identify all services that depend on a given resource
   - Calculate dependency depth (how many hops)
   - Determine criticality of dependencies

2. **Impact Assessment**
   - "What breaks if this service fails?"
   - Calculate blast radius for failures
   - Identify single points of failure (SPOFs)
   - Assess cascading failure scenarios

3. **Change Risk Scoring**
   - Score risk of updating a service (0-100)
   - Consider number of dependencies
   - Consider service criticality
   - Consider deployment history (past failures)
   - Consider time since last change

4. **Failure Scenario Simulation**
   - Simulate what happens when a service goes down
   - Identify affected services and users
   - Estimate recovery time

## Risk Scoring Algorithm

### Factors to Consider

```python
risk_score = weighted_sum([
    dependency_count * 0.25,      # How many services depend on this
    criticality_score * 0.30,      # How critical is this service
    deployment_failure_rate * 0.20, # Historical failure rate
    time_since_last_change * -0.10, # Longer = less risky
    test_coverage * -0.15,         # More tests = less risky
])

# Normalize to 0-100
risk_score = min(100, max(0, risk_score))
```

### Criticality Score

```python
criticality_factors = {
    'is_database': 30,            # Databases are critical
    'is_authentication': 40,       # Auth is most critical
    'has_external_users': 20,      # User-facing services
    'is_single_instance': 15,      # No redundancy
    'uptime_sla': -10,            # High SLA = less critical in scoring
}
```

## Technical Design

### Module Structure
```
src/analysis/risk/
├── __init__.py
├── analyzer.py         # Main risk analysis orchestrator
├── dependency.py       # Dependency graph analysis
├── impact.py           # Impact assessment
├── scoring.py          # Risk scoring algorithms
├── simulation.py       # Failure simulation
├── metrics.py          # Risk metrics calculation
└── config.py           # Configuration
```

### Key Classes

```python
class RiskAnalyzer:
    def __init__(self, graph_db):
        """Initialize with graph database connection"""
        
    def analyze_resource(self, resource_id: str) -> RiskAssessment:
        """Analyze risk for a specific resource"""
        
    def calculate_blast_radius(self, resource_id: str) -> BlastRadius:
        """Calculate what would be affected if this fails"""
        
    def identify_single_points_of_failure(self) -> List[Resource]:
        """Find all single points of failure"""
        
    def simulate_failure(self, resource_id: str) -> FailureSimulation:
        """Simulate a failure scenario"""
        
    def get_change_risk_score(self, resource_id: str) -> float:
        """Get risk score for changing this resource"""
```

### Data Models

```python
@dataclass
class RiskAssessment:
    resource_id: str
    risk_score: float  # 0-100
    criticality: str   # low, medium, high, critical
    dependencies_count: int
    dependents_count: int
    blast_radius: int  # number of services affected
    single_point_of_failure: bool
    recommendations: List[str]

@dataclass
class BlastRadius:
    resource_id: str
    directly_affected: List[str]      # Immediate dependents
    indirectly_affected: List[str]    # Cascade effects
    user_impact: str                  # low, medium, high
    estimated_downtime: int           # seconds
```

## Analysis Queries

### Find All Dependencies (Cypher)
```cypher
// Find all services that depend on this resource
MATCH path = (dependent:Resource)-[:DEPENDS_ON*1..5]->(resource:Resource {id: $resource_id})
RETURN dependent, length(path) as depth
ORDER BY depth
```

### Find Single Points of Failure
```cypher
// Resources with no redundancy that have dependents
MATCH (r:Resource)<-[:DEPENDS_ON]-(dependent:Resource)
WHERE NOT EXISTS {
    MATCH (r)-[:REDUNDANT_WITH]->(:Resource)
}
WITH r, COUNT(dependent) as dependent_count
WHERE dependent_count > 0
RETURN r, dependent_count
ORDER BY dependent_count DESC
```

### Calculate Blast Radius
```cypher
// All resources affected if this fails
MATCH path = (r:Resource {id: $resource_id})<-[:DEPENDS_ON*0..10]-(affected:Resource)
RETURN DISTINCT affected, MIN(length(path)) as distance
ORDER BY distance
```

## Use Cases

### Use Case 1: Pre-Deployment Risk Check
```python
# Before deploying update to service
risk = analyzer.get_change_risk_score("webapp-prod")
if risk > 75:
    print("⚠️  High risk deployment!")
    print(f"This service has {assessment.dependents_count} dependents")
    print(f"Recommendation: Deploy during maintenance window")
```

### Use Case 2: Identify Critical Services
```python
# Find most critical services
spofs = analyzer.identify_single_points_of_failure()
for resource in spofs:
    assessment = analyzer.analyze_resource(resource.id)
    print(f"{resource.name}: Risk Score {assessment.risk_score}")
    print(f"Recommendations: {', '.join(assessment.recommendations)}")
```

### Use Case 3: Failure Impact
```python
# What happens if database goes down?
simulation = analyzer.simulate_failure("sql-db-prod")
print(f"Services affected: {len(simulation.directly_affected)}")
print(f"Cascade effects: {len(simulation.indirectly_affected)}")
print(f"User impact: {simulation.user_impact}")
```

## Tasks

- [ ] Design risk scoring algorithm
- [ ] Implement dependency graph traversal
- [ ] Implement impact assessment
- [ ] Implement blast radius calculation
- [ ] Implement SPOF detection
- [ ] Implement failure simulation
- [ ] Create risk metrics and reports
- [ ] Add caching for expensive calculations
- [ ] Write comprehensive unit tests
- [ ] Write integration tests
- [ ] Create documentation
- [ ] Build example risk reports

## Success Criteria

- [ ] Accurately identifies dependencies
- [ ] Risk scores are consistent and meaningful
- [ ] Can simulate failure scenarios
- [ ] Identifies single points of failure
- [ ] Performance: Analysis completes in <10 seconds for typical topology
- [ ] Tests pass with >85% coverage
- [ ] Documentation includes examples

## Performance Considerations

- Cache risk scores (recalculate on topology changes)
- Optimize graph queries for large topologies
- Implement depth limits for dependency traversal
- Use parallel processing for batch analysis

## Dependencies

- Issue #2: Core Data Models
- Issue #3: Azure Resource Discovery (for test data)
- Neo4j with populated topology data

## Timeline

Weeks 5-6

## Related Issues

- Issue #6: Visualization Dashboard (will consume this data)
- Issue #7: Change Impact Reports
