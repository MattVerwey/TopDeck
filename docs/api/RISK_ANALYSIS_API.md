# Risk Analysis API Documentation

## Overview

The Risk Analysis API provides comprehensive risk assessment capabilities for infrastructure resources, including:

- **Risk Assessment**: Calculate risk scores based on dependencies, criticality, and historical data
- **Blast Radius**: Determine impact of resource failures
- **Failure Simulation**: Predict outcomes of failure scenarios
- **SPOF Detection**: Identify single points of failure

## Base URL

```
/api/v1/risk
```

## Endpoints

### 1. Get Risk Assessment

Get complete risk assessment for a resource.

**Endpoint**: `GET /api/v1/risk/resources/{resource_id}`

**Parameters**:
- `resource_id` (path): Resource identifier

**Response**: `RiskAssessmentResponse`

```json
{
  "resource_id": "string",
  "resource_name": "string",
  "resource_type": "string",
  "risk_score": 0-100,
  "risk_level": "low|medium|high|critical",
  "criticality_score": 0-100,
  "dependencies_count": 0,
  "dependents_count": 0,
  "blast_radius": 0,
  "single_point_of_failure": false,
  "deployment_failure_rate": 0.0-1.0,
  "time_since_last_change": null,
  "recommendations": [
    "string"
  ],
  "factors": {
    "dependencies_count": 0,
    "dependents_count": 0,
    "is_spof": false,
    "has_redundancy": false,
    "blast_radius_size": 0,
    "user_impact": "minimal|low|medium|high|severe"
  },
  "assessed_at": "2024-01-01T12:00:00"
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/v1/risk/resources/sql-db-prod"
```

**Use Cases**:
- Pre-deployment risk checks
- Continuous monitoring of critical resources
- Audit and compliance reporting
- Capacity planning

---

### 2. Calculate Blast Radius

Calculate the blast radius (impact) if a resource fails.

**Endpoint**: `GET /api/v1/risk/blast-radius/{resource_id}`

**Parameters**:
- `resource_id` (path): Resource identifier

**Response**: `BlastRadiusResponse`

```json
{
  "resource_id": "string",
  "resource_name": "string",
  "directly_affected": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "cloud_provider": "string"
    }
  ],
  "indirectly_affected": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "cloud_provider": "string",
      "distance": 2
    }
  ],
  "total_affected": 0,
  "user_impact": "minimal|low|medium|high|severe",
  "estimated_downtime_seconds": 0,
  "critical_path": ["resource-1", "resource-2", "resource-3"],
  "affected_services": {
    "web_app": 5,
    "database": 2,
    "storage": 1
  }
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/v1/risk/blast-radius/sql-db-prod"
```

**Use Cases**:
- Impact analysis before maintenance
- Disaster recovery planning
- SLA assessment
- Capacity planning

---

### 3. Simulate Failure

Simulate a failure scenario and get recovery recommendations.

**Endpoint**: `POST /api/v1/risk/simulate`

**Query Parameters**:
- `resource_id` (required): Resource to simulate failure for
- `scenario` (optional): Failure scenario description (default: "Complete service outage")

**Response**: `FailureSimulationResponse`

```json
{
  "resource_id": "string",
  "resource_name": "string",
  "scenario": "Complete service outage",
  "blast_radius": {
    "resource_id": "string",
    "resource_name": "string",
    "directly_affected": [],
    "indirectly_affected": [],
    "total_affected": 0,
    "user_impact": "high",
    "estimated_downtime_seconds": 1800,
    "critical_path": [],
    "affected_services": {}
  },
  "cascade_depth": 3,
  "recovery_steps": [
    "1. Confirm the failure and impact scope",
    "2. Activate incident response team",
    "3. Notify stakeholders and affected users",
    "..."
  ],
  "mitigation_strategies": [
    "Implement circuit breakers to prevent cascade failures",
    "Configure automatic failover to standby database",
    "..."
  ],
  "similar_past_incidents": []
}
```

**Example**:

```bash
curl -X POST "http://localhost:8000/api/v1/risk/simulate?resource_id=sql-db-prod&scenario=Database+connection+timeout"
```

**Use Cases**:
- Disaster recovery planning
- Incident response preparation
- Team training and drills
- Infrastructure design validation

---

### 4. Identify Single Points of Failure

Get all resources that are single points of failure.

**Endpoint**: `GET /api/v1/risk/spof`

**Response**: `List[SinglePointOfFailureResponse]`

```json
[
  {
    "resource_id": "string",
    "resource_name": "string",
    "resource_type": "string",
    "dependents_count": 15,
    "blast_radius": 25,
    "risk_score": 75.0,
    "recommendations": [
      "⚠️ This is a Single Point of Failure",
      "Add redundant instances across availability zones",
      "Implement automatic failover mechanisms",
      "Increase monitoring and alerting priority"
    ]
  }
]
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/v1/risk/spof"
```

**Use Cases**:
- Infrastructure audit
- Disaster recovery planning
- High availability improvements
- Risk reduction initiatives

---

### 5. Get Change Risk Score

Get quick risk score for deploying changes (useful for CI/CD).

**Endpoint**: `GET /api/v1/risk/resources/{resource_id}/score`

**Parameters**:
- `resource_id` (path): Resource identifier

**Response**:

```json
{
  "resource_id": "string",
  "risk_score": 65.0,
  "risk_level": "high"
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/v1/risk/resources/webapp-prod/score"
```

**Use Cases**:
- CI/CD pipeline integration
- Deployment gating
- Quick pre-deployment checks
- Automated alerts

---

## Risk Scoring Algorithm

The risk score (0-100) is calculated using weighted factors:

### Factors and Weights

| Factor | Weight | Description |
|--------|--------|-------------|
| Dependency Count | 0.25 | Number of services depending on this resource |
| Criticality | 0.30 | Resource type criticality (database=30, key_vault=40, etc.) |
| Failure Rate | 0.20 | Historical deployment failure rate |
| Time Since Change | -0.10 | Longer time = lower risk (negative weight) |
| Redundancy | -0.15 | Has redundancy = lower risk (negative weight) |

### Formula

```
risk_score = (
    dependency_count * 0.25 +
    criticality * 0.30 +
    failure_rate * 0.20 +
    time_factor * -0.10 +
    redundancy_factor * -0.15
)
```

### Risk Levels

| Score Range | Level | Description |
|------------|-------|-------------|
| 0-24 | LOW | Low risk, standard deployment procedures |
| 25-49 | MEDIUM | Moderate risk, extra caution recommended |
| 50-74 | HIGH | High risk, deploy during maintenance windows |
| 75-100 | CRITICAL | Critical risk, comprehensive planning required |

---

## Criticality Factors

Resource types have different base criticality scores:

### High Criticality (30-40)
- **Databases** (30): sql_database, cosmos_db, postgresql
- **Authentication** (40): key_vault, authentication services
- **Caching** (25): redis_cache, memcache

### Medium-High Criticality (20-25)
- **Load Balancers** (20): load_balancer, app_gateway
- **API Gateways** (20): api_gateway

### Medium Criticality (15)
- **Compute** (15): web_app, function_app, pod, aks, eks, gke

### Lower Criticality (5-10)
- **Storage** (10): storage_account, blob_storage
- **VMs** (10): vm, compute instances
- **Networking** (5): vnet, subnets

---

## User Impact Levels

| Level | Description | Affected Resources | User Facing |
|-------|-------------|-------------------|-------------|
| MINIMAL | No impact | 0 | No |
| LOW | Minor impact | 1-2 | No |
| MEDIUM | Moderate impact | 3-9 or 1-4 user-facing | Possibly |
| HIGH | Major impact | 10-19 or 5+ user-facing | Yes |
| SEVERE | Critical impact | 20+ | Yes |

---

## Error Responses

### 404 Not Found

```json
{
  "detail": "Resource {resource_id} not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Failed to analyze resource: {error_message}"
}
```

---

## Integration Examples

### Python

```python
import requests

# Get risk assessment
response = requests.get(
    "http://localhost:8000/api/v1/risk/resources/sql-db-prod"
)
assessment = response.json()

print(f"Risk Score: {assessment['risk_score']}")
print(f"Risk Level: {assessment['risk_level']}")
print(f"Recommendations:")
for rec in assessment['recommendations']:
    print(f"  - {rec}")
```

### CI/CD Pipeline (GitHub Actions)

```yaml
- name: Check Deployment Risk
  run: |
    RISK_SCORE=$(curl -s "http://topdeck:8000/api/v1/risk/resources/$SERVICE_ID/score" | jq -r '.risk_score')
    if [ "$RISK_SCORE" -gt 75 ]; then
      echo "::error::Risk score too high ($RISK_SCORE). Deployment blocked."
      exit 1
    fi
```

### Bash Script

```bash
#!/bin/bash

RESOURCE_ID="webapp-prod"
API_URL="http://localhost:8000/api/v1/risk"

# Get risk assessment
ASSESSMENT=$(curl -s "$API_URL/resources/$RESOURCE_ID")
RISK_SCORE=$(echo $ASSESSMENT | jq -r '.risk_score')
RISK_LEVEL=$(echo $ASSESSMENT | jq -r '.risk_level')

echo "Risk Assessment for $RESOURCE_ID:"
echo "  Score: $RISK_SCORE"
echo "  Level: $RISK_LEVEL"

# Check if SPOF
IS_SPOF=$(echo $ASSESSMENT | jq -r '.single_point_of_failure')
if [ "$IS_SPOF" = "true" ]; then
    echo "  ⚠️  WARNING: This is a Single Point of Failure!"
fi
```

---

## Best Practices

### 1. Pre-Deployment Checks

Always check risk scores before deploying to production:

```bash
# Get risk score
SCORE=$(curl -s "http://localhost:8000/api/v1/risk/resources/$RESOURCE/score" | jq -r '.risk_score')

# Gate deployments based on score
if [ "$SCORE" -gt 75 ]; then
    echo "High risk deployment - require approval"
fi
```

### 2. Regular SPOF Audits

Schedule regular checks for single points of failure:

```bash
# Weekly SPOF report
curl -s "http://localhost:8000/api/v1/risk/spof" | \
    jq -r '.[] | "\(.resource_name): \(.dependents_count) dependents, Risk: \(.risk_score)"'
```

### 3. Failure Simulation

Test disaster recovery procedures with simulations:

```bash
# Simulate database failure
curl -X POST "http://localhost:8000/api/v1/risk/simulate?resource_id=sql-db-prod" | \
    jq -r '.recovery_steps[]'
```

### 4. Continuous Monitoring

Monitor risk scores over time to track improvements:

```python
# Daily risk check
resources = ["sql-db-prod", "webapp-prod", "api-gateway"]
for resource_id in resources:
    assessment = get_risk_assessment(resource_id)
    if assessment['risk_level'] == 'critical':
        send_alert(f"Critical risk: {resource_id}")
```

---

## Related Documentation

- [Topology API](TOPOLOGY_API.md) - Resource topology and dependencies
- [Monitoring API](MONITORING_API.md) - Performance metrics and monitoring
- [Risk Analysis Guide](../guides/RISK_ANALYSIS.md) - Detailed usage guide
- [Issue #5: Risk Analysis Engine](../issues/issue-005-risk-analysis-engine.md) - Original requirements
