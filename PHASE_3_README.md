# Phase 3: Risk Analysis Engine - Quick Start

**Status**: ✅ COMPLETE  
**Date**: 2025-10-13

## What Is This?

The Risk Analysis Engine is TopDeck's **core value proposition**. It enables you to:

- 🎯 **Assess risk** before deployments (0-100 score)
- 💥 **Calculate blast radius** of failures
- 🔍 **Identify single points of failure** (SPOFs)
- 🎬 **Simulate failure scenarios** with recovery steps
- 💡 **Get recommendations** for risk mitigation

## Quick Examples

### 1. Check Risk Before Deployment

```python
from topdeck.analysis.risk import RiskAnalyzer
from topdeck.storage.neo4j_client import Neo4jClient

# Connect to Neo4j
client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
client.connect()

# Create analyzer
analyzer = RiskAnalyzer(client)

# Assess risk
assessment = analyzer.analyze_resource("webapp-prod")

print(f"Risk Score: {assessment.risk_score}/100")
print(f"Risk Level: {assessment.risk_level}")
print(f"SPOFs: {assessment.single_point_of_failure}")
print(f"Blast Radius: {assessment.blast_radius} resources")
print("\nRecommendations:")
for rec in assessment.recommendations:
    print(f"  - {rec}")
```

### 2. Find All Single Points of Failure

```python
# Get all SPOFs
spofs = analyzer.identify_single_points_of_failure()

print(f"Found {len(spofs)} single points of failure:")
for spof in spofs:
    print(f"\n{spof.resource_name} ({spof.resource_type})")
    print(f"  Dependents: {spof.dependents_count}")
    print(f"  Risk Score: {spof.risk_score}/100")
    print(f"  Blast Radius: {spof.blast_radius}")
```

### 3. Calculate Blast Radius

```python
# What happens if database fails?
blast_radius = analyzer.calculate_blast_radius("sql-db-prod")

print(f"Total Affected: {blast_radius.total_affected}")
print(f"Directly: {len(blast_radius.directly_affected)}")
print(f"Indirectly: {len(blast_radius.indirectly_affected)}")
print(f"User Impact: {blast_radius.user_impact}")
print(f"Estimated Downtime: {blast_radius.estimated_downtime_seconds}s")
```

### 4. Simulate Failure Scenario

```python
# Simulate database outage
simulation = analyzer.simulate_failure(
    "sql-db-prod",
    scenario="Database connection pool exhausted"
)

print("Recovery Steps:")
for i, step in enumerate(simulation.recovery_steps, 1):
    print(f"  {i}. {step}")

print("\nMitigation Strategies:")
for strategy in simulation.mitigation_strategies:
    print(f"  - {strategy}")
```

### 5. CI/CD Integration

```bash
#!/bin/bash
# Add to your CI/CD pipeline

SERVICE_ID="webapp-prod"
API_URL="http://topdeck:8000/api/v1/risk"

# Get risk score
RISK_SCORE=$(curl -s "$API_URL/resources/$SERVICE_ID/score" | jq -r '.risk_score')
RISK_LEVEL=$(curl -s "$API_URL/resources/$SERVICE_ID/score" | jq -r '.risk_level')

echo "Risk Assessment for $SERVICE_ID:"
echo "  Score: $RISK_SCORE/100"
echo "  Level: $RISK_LEVEL"

# Block high-risk deployments
if [ "$RISK_SCORE" -gt 75 ]; then
    echo "::error::Risk score too high. Deployment blocked."
    exit 1
fi

echo "✅ Risk check passed. Proceeding with deployment."
```

## REST API Examples

### Get Risk Assessment

```bash
curl -X GET "http://localhost:8000/api/v1/risk/resources/webapp-prod" | jq
```

### Calculate Blast Radius

```bash
curl -X GET "http://localhost:8000/api/v1/risk/blast-radius/sql-db-prod" | jq
```

### List All SPOFs

```bash
curl -X GET "http://localhost:8000/api/v1/risk/spof" | jq
```

### Simulate Failure

```bash
curl -X POST "http://localhost:8000/api/v1/risk/simulate?resource_id=sql-db-prod&scenario=Complete+outage" | jq
```

### Quick Risk Score (for CI/CD)

```bash
curl -X GET "http://localhost:8000/api/v1/risk/resources/webapp-prod/score" | jq
```

## Risk Scoring

### How It Works

Risk score (0-100) is calculated using weighted factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Dependency Count** | 25% | More dependents = higher risk |
| **Criticality** | 30% | Resource type importance |
| **Failure Rate** | 20% | Historical deployment failures |
| **Time Factor** | -10% | Recent changes = higher risk |
| **Redundancy** | -15% | No redundancy = higher risk |

### Risk Levels

| Score | Level | Action |
|-------|-------|--------|
| 0-24 | 🟢 **LOW** | Standard deployment |
| 25-49 | 🟡 **MEDIUM** | Extra caution |
| 50-74 | 🟠 **HIGH** | Maintenance window |
| 75-100 | 🔴 **CRITICAL** | Comprehensive planning |

### Resource Criticality

Different resource types have different base criticality:

- **Key Vault** (40) - Highest
- **Database** (30) - High
- **Cache** (25) - Medium-high
- **Load Balancer** (20) - Medium-high
- **Web App** (15) - Medium
- **Storage** (10) - Lower
- **VNet** (5) - Lowest

## Documentation

- **[API Documentation](docs/api/RISK_ANALYSIS_API.md)** - Complete REST API reference
- **[Completion Summary](PHASE_3_RISK_ANALYSIS_COMPLETION.md)** - Full implementation details
- **[Issue #5](docs/issues/issue-005-risk-analysis-engine.md)** - Original requirements
- **[PROGRESS.md](PROGRESS.md)** - Overall project status

## Architecture

```
src/topdeck/analysis/risk/
├── __init__.py         # Module exports
├── analyzer.py         # Main orchestrator (11KB)
├── dependency.py       # Dependency graph analysis (8.7KB)
├── scoring.py          # Risk scoring algorithms (8.5KB)
├── impact.py           # Blast radius calculation (5.4KB)
├── simulation.py       # Failure simulation (7.1KB)
└── models.py           # Data models (4.5KB)
```

## Testing

Run the comprehensive test suite:

```bash
# Run all risk analysis tests
pytest tests/analysis/test_risk_*.py -v

# Run specific test module
pytest tests/analysis/test_risk_scoring.py -v

# Run with coverage
pytest tests/analysis/test_risk_*.py --cov=topdeck.analysis.risk --cov-report=term-missing
```

**Test Coverage**: 65+ tests, >85% coverage

## Use Cases

### 1. Pre-Deployment Validation

```python
# Before deploying to production
assessment = analyzer.analyze_resource(service_id)
if assessment.risk_level == "critical":
    print("⚠️  Deploy during maintenance window")
    schedule_maintenance_deployment(service_id)
else:
    deploy_immediately(service_id)
```

### 2. Infrastructure Audit

```python
# Weekly SPOF report
spofs = analyzer.identify_single_points_of_failure()
send_report(f"Found {len(spofs)} SPOFs requiring attention", spofs)
```

### 3. Incident Response

```python
# During incident
blast_radius = analyzer.calculate_blast_radius(failed_resource)
notify_teams(blast_radius.directly_affected)
follow_recovery_steps(simulation.recovery_steps)
```

### 4. Capacity Planning

```python
# Identify critical resources
resources = get_all_resources()
critical = [r for r in resources if analyzer.get_change_risk_score(r) > 75]
allocate_redundancy(critical)
```

## Common Patterns

### Pattern 1: Risk-Gated Deployments

```python
def should_deploy(service_id: str) -> bool:
    """Check if deployment is safe."""
    assessment = analyzer.analyze_resource(service_id)
    
    # Block critical risk
    if assessment.risk_level == "critical":
        return False
    
    # Require approval for high risk
    if assessment.risk_level == "high":
        return request_approval(service_id, assessment)
    
    return True
```

### Pattern 2: Automated SPOF Alerting

```python
def check_spofs_daily():
    """Daily SPOF check."""
    spofs = analyzer.identify_single_points_of_failure()
    
    for spof in spofs:
        if spof.risk_score > 75:
            alert_team(
                title=f"Critical SPOF: {spof.resource_name}",
                message=f"Risk: {spof.risk_score}/100, "
                        f"Dependents: {spof.dependents_count}",
                recommendations=spof.recommendations
            )
```

### Pattern 3: Failure Drill Automation

```python
def run_failure_drill(resource_id: str):
    """Run chaos engineering drill."""
    simulation = analyzer.simulate_failure(resource_id)
    
    print(f"Simulating failure of {simulation.resource_name}")
    print(f"Expected impact: {simulation.blast_radius.total_affected} resources")
    print(f"Estimated downtime: {simulation.blast_radius.estimated_downtime_seconds}s")
    
    # Use recovery steps as runbook
    execute_drill_with_runbook(simulation.recovery_steps)
```

## Best Practices

1. **Check risk before every production deployment**
2. **Run weekly SPOF audits**
3. **Simulate failures for disaster recovery planning**
4. **Use risk scores in CI/CD pipelines**
5. **Monitor risk trends over time**
6. **Address SPOFs with highest blast radius first**
7. **Keep deployment failure rates updated**

## Troubleshooting

### Issue: Risk scores seem too high/low

**Solution**: Adjust scoring weights in `RiskScorer`:

```python
from topdeck.analysis.risk import RiskScorer

custom_weights = {
    "dependency_count": 0.30,   # Increase dependency weight
    "criticality": 0.25,
    "failure_rate": 0.20,
    "time_since_change": -0.10,
    "redundancy": -0.15,
}

scorer = RiskScorer(weights=custom_weights)
```

### Issue: SPOF detection not accurate

**Solution**: Ensure redundancy relationships are defined:

```cypher
// In Neo4j, mark redundant resources
MATCH (r1:Resource {id: "webapp-prod-1"})
MATCH (r2:Resource {id: "webapp-prod-2"})
CREATE (r1)-[:REDUNDANT_WITH]->(r2)
CREATE (r2)-[:REDUNDANT_WITH]->(r1)
```

### Issue: Missing historical failure rate

**Solution**: Track deployments and failures:

```python
# After deployment
track_deployment(
    resource_id="webapp-prod",
    success=deployment_succeeded,
    timestamp=datetime.now()
)

# Calculate failure rate
failure_rate = calculate_failure_rate(resource_id, days=30)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new risk factors
- Improving scoring algorithms
- Adding new resource criticality types
- Writing tests

## License

See [LICENSE](LICENSE) for details.

---

**Questions?** Check the [full documentation](docs/api/RISK_ANALYSIS_API.md) or open an issue.

**Phase 3 Status**: ✅ COMPLETE  
**Last Updated**: 2025-10-13
