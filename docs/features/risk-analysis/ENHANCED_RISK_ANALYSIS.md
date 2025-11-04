# Enhanced Risk Analysis - In-Depth Guide

## Overview

TopDeck's enhanced risk analysis provides **genuine, in-depth risk assessment** that goes beyond simple pass/fail scenarios. It analyzes realistic failure modes, searches all dependencies, and provides detailed outcome analysis including:

- **Degraded Performance**: Slow responses, increased latency, resource saturation
- **Intermittent Failures**: Occasional errors, service blips, sporadic issues
- **Partial Outages**: Multi-zone failures, regional issues, capacity loss
- **Dependency Vulnerabilities**: Security issues in package dependencies (npm, pip, etc.)
- **Comprehensive Dependency Analysis**: All relationship types in infrastructure graph

## New Capabilities

### 1. Degraded Performance Analysis

Most production issues aren't complete outages—they're **degraded performance**. This analysis models realistic scenarios:

#### What It Analyzes

- **Database**: Slow queries, connection pool exhaustion, lock contention
- **Cache (Redis)**: Cache miss rate increases, memory pressure, eviction spikes
- **Web Apps**: Increased response times, thread pool exhaustion, memory leaks
- **Load Balancers**: Unhealthy backends, request queuing, SSL delays
- **API Gateways**: Rate limit exhaustion, route lookup delays, auth latency
- **AKS/Kubernetes**: Node pressure, pod evictions, DNS resolution delays

#### Outcomes Analyzed

Each scenario provides multiple **weighted outcomes**:

- **Outcome Type**: `DEGRADED`, `TIMEOUT`, `BLIP`, `ERROR_RATE`, `DOWNTIME`
- **Probability**: Likelihood of this outcome (0-1)
- **Duration**: Expected impact duration in seconds
- **Affected Percentage**: What % of service is impacted
- **User Impact Description**: Human-readable explanation
- **Technical Details**: Root cause information

#### Example API Call

```bash
curl "http://localhost:8000/api/v1/risk/resources/{resource_id}/degraded-performance?current_load=0.8"
```

#### Example Response

```json
{
  "resource_id": "db-prod-001",
  "resource_name": "production-database",
  "failure_type": "degraded_performance",
  "outcomes": [
    {
      "outcome_type": "degraded",
      "probability": 0.72,
      "duration_seconds": 1800,
      "affected_percentage": 68.0,
      "user_impact_description": "Slow response times affecting 68% of requests. Users experience delays but service works.",
      "technical_details": "database slow queries"
    },
    {
      "outcome_type": "timeout",
      "probability": 0.36,
      "duration_seconds": 900,
      "affected_percentage": 34.0,
      "user_impact_description": "Request timeouts affecting 34% of operations. Users need to retry.",
      "technical_details": "database slow queries"
    }
  ],
  "overall_impact": "medium",
  "mitigation_strategies": [
    "Implement connection pooling with proper limits",
    "Add read replicas to distribute load",
    "Set up query timeouts to prevent long-running queries",
    "Enable slow query logging and optimize problematic queries",
    "Consider implementing caching layer (Redis/Memcached)"
  ],
  "monitoring_recommendations": [
    "Monitor key performance indicators (latency, throughput, errors)",
    "Set up alerts on P95/P99 latency thresholds",
    "Track resource utilization (CPU, memory, connections)",
    "Implement health check endpoints",
    "Monitor query execution times and slow query counts"
  ]
}
```

### 2. Intermittent Failure Analysis

Analyzes **service blips** and occasional errors—extremely common in distributed systems.

#### What It Models

- Occasional request failures (e.g., 5% error rate)
- Brief outages that self-recover
- Race conditions and timing issues
- Resource contention causing sporadic failures

#### Key Insights

- **Error Rate Spikes**: How error rates increase under stress
- **User Experience**: Most retries succeed vs. frequent failures
- **Retry Strategy**: Recommendations for retry/backoff logic
- **Circuit Breakers**: When to fail fast vs. keep retrying

#### Example API Call

```bash
curl "http://localhost:8000/api/v1/risk/resources/{resource_id}/intermittent-failure?failure_frequency=0.05"
```

#### Use Cases

- Planning retry logic and timeouts
- Setting up circuit breakers
- Determining acceptable error rates
- Chaos engineering baselines

### 3. Partial Outage Analysis

Analyzes **multi-zone failures** where only some instances/regions fail.

#### What It Analyzes

- Zone-level failures (e.g., zone-a down, zone-b/c healthy)
- Partial capacity loss
- Overload on remaining healthy instances
- Geographic/regional outages

#### Key Metrics

- **Affected Percentage**: What % of capacity is lost
- **Remaining Capacity Stress**: How overloaded are healthy instances
- **User Routing**: Impact of users routed to failed zones
- **Recovery Time**: Time to restore or failover

#### Example API Call

```bash
curl "http://localhost:8000/api/v1/risk/resources/{resource_id}/partial-outage?affected_zones=zone-a,zone-b"
```

#### Example Response

```json
{
  "failure_type": "partial_outage",
  "outcomes": [
    {
      "outcome_type": "partial_outage",
      "probability": 0.8,
      "duration_seconds": 900,
      "affected_percentage": 66.0,
      "user_impact_description": "66% of capacity lost. Service degraded but operational on remaining zones. Some users routed to failed zones experience errors.",
      "technical_details": "load_balancer in zones zone-a, zone-b unavailable"
    },
    {
      "outcome_type": "degraded",
      "probability": 0.2,
      "duration_seconds": 1800,
      "affected_percentage": 34.0,
      "user_impact_description": "Remaining 34% capacity handling 100% of traffic. Increased latency and occasional timeouts.",
      "technical_details": "Overload on healthy load_balancer instances"
    }
  ],
  "overall_impact": "high",
  "mitigation_strategies": [
    "Implement multi-zone redundancy with automatic failover",
    "Configure health checks to remove failed instances",
    "Set up auto-scaling to compensate for lost capacity",
    "Use DNS-based routing to redirect traffic from failed zones"
  ]
}
```

### 4. Dependency Vulnerability Scanning

Scans **package dependencies** for known security vulnerabilities.

#### Supported Ecosystems

- **Python**: `requirements.txt`, `pyproject.toml`
- **Node.js**: `package.json` (dependencies & devDependencies)
- **Future**: Maven, NuGet, Go modules, Ruby gems

#### What It Finds

- CVE identifiers
- Severity levels (critical, high, medium, low)
- Current version vs. fixed version
- Exploit availability
- Affected resources

#### Example Usage

```bash
# Scan as part of comprehensive analysis
curl "http://localhost:8000/api/v1/risk/resources/{resource_id}/comprehensive?project_path=/path/to/project"
```

#### Vulnerability Risk Score

Calculates aggregate risk from all vulnerabilities:

```
risk_score = sum of all (severity_score) + exploit_bonus

Where:
- Critical: 25 points
- High: 15 points
- Medium: 8 points
- Low: 3 points
- Exploit available: +10 points per vulnerability
```

#### Example Output

```json
{
  "dependency_vulnerabilities": [
    {
      "package_name": "django",
      "current_version": "3.2.0",
      "vulnerability_id": "CVE-2023-23969",
      "severity": "high",
      "description": "Potential denial-of-service vulnerability in file uploads",
      "fixed_version": "4.1.7",
      "exploit_available": false,
      "affected_resources": ["web-app-001"]
    }
  ],
  "vulnerability_risk_score": 15.0
}
```

### 5. Enhanced Dependency Analysis

Searches **ALL relationship types** in the Neo4j graph, not just `DEPENDS_ON`.

#### Relationship Types Analyzed

- `DEPENDS_ON`: Direct dependencies
- `USES`: Service usage
- `CONNECTS_TO`: Network connections
- `ROUTES_TO`: Traffic routing
- `ACCESSES`: Data access
- `AUTHENTICATES_WITH`: Authentication dependencies
- `READS_FROM`: Data read dependencies
- `WRITES_TO`: Data write dependencies

#### API Enhancement

New method returns dependencies broken down by type:

```python
# Python SDK
analyzer = RiskAnalyzer(neo4j_client)
deps_by_type = analyzer.dependency_analyzer.get_all_dependency_types(resource_id)

# Returns:
# {
#   "DEPENDS_ON": [...],
#   "AUTHENTICATES_WITH": [...],
#   "ACCESSES": [...]
# }
```

### 6. Comprehensive Risk Analysis

Combines **all analysis types** into a single comprehensive view.

#### What's Included

1. Standard risk assessment (SPOF, blast radius, criticality)
2. Degraded performance scenario
3. Intermittent failure scenario
4. Dependency vulnerabilities (if project path provided)
5. Combined risk score (weighted average)

#### Combined Risk Score Formula

```
combined_risk = (
    infrastructure_risk * 0.5 +
    vulnerability_risk * 0.3 +
    degradation_risk * 0.2
)
```

#### Example API Call

```bash
curl "http://localhost:8000/api/v1/risk/resources/{resource_id}/comprehensive?project_path=/app&current_load=0.8"
```

#### Example Response Structure

```json
{
  "resource_id": "web-app-prod",
  "combined_risk_score": 67.5,
  "standard_assessment": { ... },
  "degraded_performance_scenario": { ... },
  "intermittent_failure_scenario": { ... },
  "dependency_vulnerabilities": [ ... ],
  "vulnerability_risk_score": 15.0,
  "all_recommendations": [
    "🔴 Single Point of Failure: Add redundancy or failover capability",
    "Implement connection pooling with proper limits",
    "Implement retry logic with exponential backoff",
    "🔴 CRITICAL: 1 critical vulnerabilities found - upgrade immediately before deployment",
    "Upgrade django from 3.2.0 to 4.1.7 (CVE-2023-23969)"
  ]
}
```

## API Endpoints

### New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/risk/resources/{id}/degraded-performance` | GET | Analyze degraded performance scenario |
| `/api/v1/risk/resources/{id}/intermittent-failure` | GET | Analyze intermittent failure scenario |
| `/api/v1/risk/resources/{id}/partial-outage` | GET | Analyze partial outage scenario |
| `/api/v1/risk/resources/{id}/comprehensive` | GET | Get comprehensive risk analysis |

### Existing Endpoints (Enhanced)

| Endpoint | Enhancement |
|----------|-------------|
| `/api/v1/risk/resources/{id}` | Now searches all dependency types |
| `/api/v1/risk/blast-radius/{id}` | More accurate with enhanced dependency analysis |
| `/api/v1/risk/spof` | Better detection with comprehensive relationship search |

## Integration Examples

### CI/CD Pipeline Integration

```bash
#!/bin/bash
# Pre-deployment risk check

RESOURCE_ID="web-app-prod"
PROJECT_PATH="/app"

# Get comprehensive analysis
RESPONSE=$(curl -s "http://topdeck:8000/api/v1/risk/resources/$RESOURCE_ID/comprehensive?project_path=$PROJECT_PATH")

# Extract risk scores
COMBINED_RISK=$(echo $RESPONSE | jq -r '.combined_risk_score')
VULN_RISK=$(echo $RESPONSE | jq -r '.vulnerability_risk_score')

# Check thresholds using awk for portability
if [ $(echo "$COMBINED_RISK 75" | awk '{print ($1 > $2)}') -eq 1 ]; then
    echo "❌ Combined risk score too high: $COMBINED_RISK"
    echo "Recommendations:"
    echo $RESPONSE | jq -r '.all_recommendations[]'
    exit 1
fi

if [ $(echo "$VULN_RISK 20" | awk '{print ($1 > $2)}') -eq 1 ]; then
    echo "❌ Critical vulnerabilities found. Risk score: $VULN_RISK"
    echo "Vulnerabilities:"
    echo $RESPONSE | jq -r '.dependency_vulnerabilities[] | "\(.package_name): \(.vulnerability_id) (\(.severity))"'
    exit 1
fi

echo "✅ Risk analysis passed. Combined risk: $COMBINED_RISK"
```

### Python SDK Usage

```python
from topdeck.analysis.risk import RiskAnalyzer
from topdeck.storage.neo4j_client import Neo4jClient

# Initialize
neo4j = Neo4jClient(uri="bolt://localhost:7687", username="neo4j", password="password")
neo4j.connect()
analyzer = RiskAnalyzer(neo4j)

# Get comprehensive analysis
analysis = analyzer.get_comprehensive_risk_analysis(
    resource_id="db-prod-001",
    project_path="/app",
    current_load=0.8
)

# Check results
print(f"Combined Risk Score: {analysis['combined_risk_score']:.1f}/100")

# Show degraded performance outcomes
for outcome in analysis['degraded_performance_scenario'].outcomes:
    print(f"\n{outcome.outcome_type.value.upper()}:")
    print(f"  Probability: {outcome.probability:.0%}")
    print(f"  Duration: {outcome.duration_seconds}s")
    print(f"  Impact: {outcome.user_impact_description}")

# Show vulnerabilities
if analysis['dependency_vulnerabilities']:
    print("\n🔴 VULNERABILITIES FOUND:")
    for vuln in analysis['dependency_vulnerabilities']:
        print(f"  - {vuln.package_name} {vuln.current_version}: {vuln.vulnerability_id} ({vuln.severity})")
        if vuln.fixed_version:
            print(f"    Fix: Upgrade to {vuln.fixed_version}")
```

### Monitoring Integration

```python
# Prometheus metrics example
from prometheus_client import Gauge

risk_score = Gauge('topdeck_risk_score', 'Combined risk score', ['resource_id'])
vuln_count = Gauge('topdeck_vulnerabilities', 'Number of vulnerabilities', ['severity', 'resource_id'])

def update_metrics(resource_id):
    analysis = analyzer.get_comprehensive_risk_analysis(resource_id)
    
    # Update risk score
    risk_score.labels(resource_id=resource_id).set(analysis['combined_risk_score'])
    
    # Update vulnerability counts
    for severity in ['critical', 'high', 'medium', 'low']:
        count = len([v for v in analysis['dependency_vulnerabilities'] if v.severity == severity])
        vuln_count.labels(severity=severity, resource_id=resource_id).set(count)
```

## Best Practices

### 1. Regular Scanning

```bash
# Cron job for daily vulnerability scanning
0 2 * * * /usr/local/bin/scan-topdeck-vulnerabilities.sh
```

### 2. Degradation Testing

Use the degraded performance analysis to:
- Set up load tests with realistic degradation scenarios
- Configure alerting thresholds (P95, P99 latency)
- Plan capacity based on degradation curves

### 3. Multi-Zone Resilience

Use partial outage analysis to:
- Verify failover mechanisms
- Test auto-scaling response
- Plan for zone-level failures

### 4. Dependency Management

- Run vulnerability scans on every commit (CI/CD integration)
- Set up automated dependency updates (Dependabot, Renovate)
- Track vulnerability risk score over time

### 5. Comprehensive Pre-Deployment Checks

```bash
# Full pre-deployment checklist
1. Comprehensive risk analysis
2. Check combined risk score < 75
3. Verify no critical vulnerabilities
4. Review degraded performance outcomes
5. Ensure multi-zone redundancy for high-risk resources
```

## Comparison: Old vs. New

### Old Risk Analysis

- ❌ Only analyzed complete failures
- ❌ Binary outcomes (works/doesn't work)
- ❌ No dependency vulnerability scanning
- ❌ Only checked `DEPENDS_ON` relationships
- ❌ Generic recommendations

### New Enhanced Risk Analysis

- ✅ Analyzes degraded performance, blips, partial outages
- ✅ Multiple weighted outcomes with probabilities
- ✅ Dependency vulnerability scanning (CVEs)
- ✅ Searches all relationship types
- ✅ Specific, actionable recommendations
- ✅ Combined risk scoring
- ✅ Realistic production scenarios

## Conclusion

The enhanced risk analysis provides **genuine, in-depth risk assessment** that reflects real-world production scenarios. It goes beyond simple pass/fail to analyze:

- **How** services fail (degraded, intermittent, partial)
- **What** the actual user impact is
- **Where** vulnerabilities exist in dependencies
- **Why** failures cascade through the system
- **What** to do about it (specific recommendations)

This enables **data-driven deployment decisions** based on realistic risk models.
