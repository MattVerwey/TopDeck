# Enhanced Risk Analysis - Quick Reference

## Quick Commands

### Degraded Performance Analysis
```bash
# Check what happens when a database is under stress
curl "http://localhost:8000/api/v1/risk/resources/db-prod-001/degraded-performance?current_load=0.8"
```

### Intermittent Failure Analysis  
```bash
# Analyze service blips (5% error rate)
curl "http://localhost:8000/api/v1/risk/resources/api-prod/intermittent-failure?failure_frequency=0.05"
```

### Partial Outage Analysis
```bash
# Analyze impact of zone-a and zone-b failures
curl "http://localhost:8000/api/v1/risk/resources/lb-prod/partial-outage?affected_zones=zone-a,zone-b"
```

### Comprehensive Analysis
```bash
# Full analysis including dependency vulnerabilities
curl "http://localhost:8000/api/v1/risk/resources/web-app/comprehensive?project_path=/app&current_load=0.7"
```

## Outcome Types

| Type | Description | Example |
|------|-------------|---------|
| `downtime` | Complete unavailability | Service returns 503 errors |
| `degraded` | Reduced performance | Response time 2x slower |
| `blip` | Brief intermittent issues | Occasional timeouts |
| `timeout` | Increased latency | 30% of requests timeout |
| `error_rate` | Increased errors | 5% error rate spike |
| `partial_outage` | Some zones/instances down | 1 of 3 zones unavailable |

## Risk Score Interpretation

### Combined Risk Score (0-100)

- **0-24**: ✅ **LOW** - Standard deployment procedures
- **25-49**: ⚠️ **MEDIUM** - Extra caution recommended  
- **50-74**: 🔶 **HIGH** - Deploy during maintenance windows
- **75-100**: 🔴 **CRITICAL** - Comprehensive planning required

### Vulnerability Risk Score

- **0**: No vulnerabilities
- **1-10**: Low severity issues
- **11-25**: Medium severity or multiple low
- **26-50**: High severity issues
- **51+**: Critical vulnerabilities or exploits available

## Common Use Cases

### Pre-Deployment Check
```bash
RISK=$(curl -s "http://localhost:8000/api/v1/risk/resources/$ID/comprehensive" | jq -r '.combined_risk_score')
if (( $(echo "$RISK > 75" | bc -l) )); then
    echo "❌ Risk too high: $RISK"
    exit 1
fi
```

### Find Critical Vulnerabilities
```bash
curl -s "http://localhost:8000/api/v1/risk/resources/$ID/comprehensive?project_path=/app" \
  | jq '.dependency_vulnerabilities[] | select(.severity == "critical")'
```

### Check Multi-Zone Resilience
```bash
# Test each zone failure
for zone in zone-a zone-b zone-c; do
    curl "http://localhost:8000/api/v1/risk/resources/$ID/partial-outage?affected_zones=$zone" \
      | jq -r '.overall_impact'
done
```

### Identify Degradation Risks
```bash
# Test at different load levels
for load in 0.5 0.7 0.9; do
    echo "Load: $load"
    curl -s "http://localhost:8000/api/v1/risk/resources/$ID/degraded-performance?current_load=$load" \
      | jq -r '.outcomes[] | "\(.outcome_type): \(.probability)"'
done
```

## Python Examples

### Basic Usage
```python
from topdeck.analysis.risk import RiskAnalyzer
from topdeck.storage.neo4j_client import Neo4jClient

neo4j = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
neo4j.connect()
analyzer = RiskAnalyzer(neo4j)

# Analyze degraded performance
scenario = analyzer.analyze_degraded_performance("db-001", current_load=0.8)
print(f"Impact: {scenario.overall_impact}")
for outcome in scenario.outcomes:
    print(f"- {outcome.outcome_type}: {outcome.probability:.0%} chance")
```

### Scan Dependencies
```python
from topdeck.analysis.risk import DependencyScanner

scanner = DependencyScanner()
vulnerabilities = scanner.scan_all_dependencies("/path/to/project", "web-app-001")

for vuln in vulnerabilities:
    if vuln.severity in ["critical", "high"]:
        print(f"⚠️ {vuln.package_name}: {vuln.vulnerability_id}")
        print(f"   Fix: Upgrade to {vuln.fixed_version}")
```

### Comprehensive Analysis
```python
analysis = analyzer.get_comprehensive_risk_analysis(
    resource_id="web-app-prod",
    project_path="/app",
    current_load=0.7
)

print(f"Combined Risk: {analysis['combined_risk_score']:.1f}/100")
print(f"Vulnerabilities: {len(analysis['dependency_vulnerabilities'])}")
print(f"\nTop Recommendations:")
for rec in analysis['all_recommendations'][:5]:
    print(f"  - {rec}")
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Risk Analysis
  run: |
    RISK=$(curl -s "http://topdeck:8000/api/v1/risk/resources/${{ env.RESOURCE_ID }}/comprehensive?project_path=." | jq -r '.combined_risk_score')
    echo "Risk Score: $RISK"
    if (( $(echo "$RISK > 75" | bc -l) )); then
      echo "::error::Risk score too high"
      exit 1
    fi
```

### GitLab CI
```yaml
risk_check:
  script:
    - RISK=$(curl -s "http://topdeck:8000/api/v1/risk/resources/${RESOURCE_ID}/comprehensive?project_path=." | jq -r '.combined_risk_score')
    - if [ $(echo "$RISK > 75" | bc -l) -eq 1 ]; then exit 1; fi
```

### Jenkins
```groovy
stage('Risk Analysis') {
    steps {
        script {
            def response = sh(
                script: "curl -s http://topdeck:8000/api/v1/risk/resources/${RESOURCE_ID}/comprehensive",
                returnStdout: true
            )
            def risk = readJSON(text: response).combined_risk_score
            if (risk > 75) {
                error("Risk score too high: ${risk}")
            }
        }
    }
}
```

## Monitoring Queries

### Prometheus Metrics
```promql
# Risk score by resource
topdeck_risk_score{resource_id="web-app-prod"}

# Critical vulnerabilities
topdeck_vulnerabilities{severity="critical",resource_id="web-app-prod"}

# Alert on high risk
alert: HighRiskScore
expr: topdeck_risk_score > 75
```

### Grafana Dashboard Variables
```
resource_id: label_values(topdeck_risk_score, resource_id)
severity: ["critical", "high", "medium", "low"]
```

## Troubleshooting

### No Vulnerabilities Found
```bash
# Check if dependency files exist
ls -la requirements.txt package.json pyproject.toml

# Verify project path is correct
curl "http://localhost:8000/api/v1/risk/resources/$ID/comprehensive?project_path=$(pwd)"
```

### Resource Not Found
```bash
# List all resources
curl "http://localhost:8000/api/v1/topology/resources" | jq -r '.[] | .id'

# Check if resource exists in Neo4j
docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 \
  "MATCH (r {id: '$RESOURCE_ID'}) RETURN r.name"
```

### High Risk Score Investigation
```bash
# Get detailed breakdown
curl -s "http://localhost:8000/api/v1/risk/resources/$ID/comprehensive" | jq '{
  combined_risk: .combined_risk_score,
  infrastructure_risk: .standard_assessment.risk_score,
  vulnerability_risk: .vulnerability_risk_score,
  is_spof: .standard_assessment.single_point_of_failure,
  dependents: .standard_assessment.dependents_count
}'
```

## Tips & Best Practices

1. **Run comprehensive analysis before deployments**
2. **Set up automated vulnerability scanning daily**
3. **Test degraded performance scenarios in staging**
4. **Verify multi-zone failover with partial outage analysis**
5. **Track risk scores over time to identify trends**
6. **Automate dependency updates for critical vulnerabilities**
7. **Use degraded performance data to set SLOs**

## Links

- [Full Documentation](./ENHANCED_RISK_ANALYSIS.md)
- [API Reference](../src/topdeck/api/routes/risk.py)
- [Examples](../examples/)
