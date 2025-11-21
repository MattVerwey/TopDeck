# Enhanced Impact Analysis - Quick Reference

Quick reference for the enhanced "what will happen" risk analysis endpoints.

## Quick Commands

### Downstream Impact (What Will Break?)

```bash
# What services and clients will be affected if this resource fails?
curl http://localhost:8000/api/v1/risk/resources/{resource-id}/downstream-impact
```

**Returns:**
- Resources affected by category (user-facing, backend, data, etc.)
- Critical services that will fail
- Client apps that will be impacted
- Estimated users affected
- Business impact summary

### Upstream Dependencies (What Do I Depend On?)

```bash
# What does this resource depend on and what are the risks?
curl http://localhost:8000/api/v1/risk/resources/{resource-id}/upstream-dependencies
```

**Returns:**
- Dependencies by category
- Unhealthy dependencies
- Single points of failure in dependencies
- High-risk dependencies
- Dependency health score (0-100)
- Recommendations

### What-If Analysis (What Will Happen?)

```bash
# Comprehensive scenario analysis
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/what-if?scenario_type={type}"

# Scenarios: failure (default), maintenance, update, degraded
```

**Returns:**
- Complete downstream impact analysis
- Complete upstream dependency analysis
- Timeline estimation
- Severity assessment
- Mitigation steps
- Rollback capability

## Common Use Cases

### Pre-Deployment Check

```bash
# Before deploying an update
curl "http://localhost:8000/api/v1/risk/resources/api-gateway/what-if?scenario_type=update"

# Check: severity, affected services, mitigation steps, rollback capability
```

### Dependency Health Check

```bash
# Check dependency health for a service
curl http://localhost:8000/api/v1/risk/resources/web-app/upstream-dependencies | \
  jq '{score: .dependency_health_score, spofs: .single_points_of_failure | length, recommendations: .recommendations}'
```

### Incident Impact Assessment

```bash
# During incident - what's affected?
curl http://localhost:8000/api/v1/risk/resources/database/downstream-impact | \
  jq '{
    total_affected: .total_affected,
    critical_services: .critical_services_affected | length,
    estimated_users: .estimated_users_affected,
    business_impact: .business_impact_summary
  }'
```

### Identify Critical Services

```bash
# Find critical services that will be affected
curl http://localhost:8000/api/v1/risk/resources/database/downstream-impact | \
  jq '.critical_services_affected[] | {id: .resource_id, name: .resource_name, category: .category}'
```

## Resource Categories

Resources are automatically categorized:

| Category | Description | Examples |
|----------|-------------|----------|
| `user_facing` | Services users interact with | Web apps, API gateways, app gateways |
| `backend_service` | Internal services | Microservices, workers, processors |
| `data_store` | Data storage systems | Databases, caches, storage |
| `infrastructure` | Infrastructure components | Load balancers, clusters, networks |
| `integration` | External integrations | Webhooks, external APIs |
| `client_app` | Client applications | Mobile apps, desktop clients |

## Severity Levels

| Severity | Description |
|----------|-------------|
| `minimal` | No affected resources |
| `low` | 1-5 affected, no critical services |
| `medium` | 6-10 affected |
| `high` | 10+ affected |
| `severe` | Critical services affected |

## Dependency Health Score

| Score | Interpretation | Action |
|-------|----------------|--------|
| 90-100 | Excellent | No action needed |
| 70-89 | Good | Monitor for changes |
| 50-69 | Fair | Action recommended |
| 0-49 | Poor | Immediate action required |

## Quick Scripts

### Monitor Dependency Health

```bash
#!/bin/bash
# Check dependency health for critical services

CRITICAL_SERVICES="api-gateway web-app payment-service database"

for service in $CRITICAL_SERVICES; do
  health=$(curl -s "http://localhost:8000/api/v1/risk/resources/$service/upstream-dependencies" | jq -r .dependency_health_score)
  spofs=$(curl -s "http://localhost:8000/api/v1/risk/resources/$service/upstream-dependencies" | jq -r '.single_points_of_failure | length')
  
  echo "Service: $service"
  echo "  Health Score: $health"
  echo "  SPOFs: $spofs"
  
  if (( $(echo "$health < 70" | bc -l) )); then
    echo "  ⚠️  WARNING: Low dependency health!"
  fi
  echo ""
done
```

### Pre-Deployment Check

```bash
#!/bin/bash
# Pre-deployment impact check

SERVICE_ID=$1

if [ -z "$SERVICE_ID" ]; then
  echo "Usage: $0 <resource-id>"
  exit 1
fi

echo "Analyzing deployment impact for: $SERVICE_ID"
echo "============================================="

# Get what-if analysis
ANALYSIS=$(curl -s "http://localhost:8000/api/v1/risk/resources/$SERVICE_ID/what-if?scenario_type=update")

SEVERITY=$(echo $ANALYSIS | jq -r .severity)
AFFECTED=$(echo $ANALYSIS | jq -r .downstream_impact.total_affected)
USERS=$(echo $ANALYSIS | jq -r .downstream_impact.estimated_users_affected)
ROLLBACK=$(echo $ANALYSIS | jq -r .rollback_possible)

echo "Severity: $SEVERITY"
echo "Affected Services: $AFFECTED"
echo "Estimated Users: $USERS"
echo "Rollback Available: $ROLLBACK"
echo ""

if [ "$SEVERITY" = "severe" ] || [ "$SEVERITY" = "high" ]; then
  echo "⚠️  HIGH IMPACT DEPLOYMENT - Review required"
  echo ""
  echo "Mitigation Steps:"
  echo $ANALYSIS | jq -r '.mitigation_steps[]' | sed 's/^/  - /'
fi
```

### Find Services Depending on Resource

```bash
# Find all services that depend on a database
curl http://localhost:8000/api/v1/risk/resources/sql-db-prod/downstream-impact | \
  jq -r '.affected_by_category | to_entries[] | 
    "Category: \(.key)\n" + 
    (.value[] | "  - \(.resource_name) (\(.resource_id))")'
```

### Check for Single Points of Failure

```bash
# Check if any dependencies are SPOFs
curl http://localhost:8000/api/v1/risk/resources/web-app/upstream-dependencies | \
  jq -r 'if (.single_points_of_failure | length) > 0 then 
    "⚠️  SPOFs found:\n" + 
    (.single_points_of_failure[] | "  - \(.resource_name) (\(.resource_type))") 
  else 
    "✅ No single points of failure"
  end'
```

## Integration Examples

### With CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- name: Check Deployment Impact
  run: |
    IMPACT=$(curl -s "http://topdeckapi/api/v1/risk/resources/${{ env.SERVICE_ID }}/what-if?scenario_type=update")
    SEVERITY=$(echo $IMPACT | jq -r .severity)
    
    if [ "$SEVERITY" = "severe" ]; then
      echo "❌ Deployment blocked - severe impact detected"
      exit 1
    fi
```

### With Monitoring Alert

```bash
# When alert fires, check impact
RESOURCE_ID="database-prod"

curl http://localhost:8000/api/v1/risk/resources/$RESOURCE_ID/downstream-impact | \
  jq '{
    alert: "Database Issue Detected",
    services_affected: .total_affected,
    critical_services: (.critical_services_affected | map(.resource_name)),
    users_impacted: .estimated_users_affected,
    business_impact: .business_impact_summary
  }' | \
  # Send to incident management system
  curl -X POST https://incidents.company.com/api/create -d @-
```

## API Response Fields

### Downstream Impact

| Field | Type | Description |
|-------|------|-------------|
| `total_affected` | int | Total number of affected resources |
| `affected_by_category` | dict | Resources grouped by category |
| `critical_services_affected` | array | List of critical services |
| `client_apps_affected` | array | List of client applications |
| `user_facing_impact` | string | Summary of user impact |
| `backend_impact` | string | Summary of backend impact |
| `data_impact` | string | Summary of data access impact |
| `estimated_users_affected` | int | Estimated number of users |
| `business_impact_summary` | string | High-level business impact |

### Upstream Dependencies

| Field | Type | Description |
|-------|------|-------------|
| `total_dependencies` | int | Total number of dependencies |
| `dependencies_by_category` | dict | Dependencies grouped by category |
| `unhealthy_dependencies` | array | Dependencies with issues |
| `single_points_of_failure` | array | SPOF dependencies |
| `high_risk_dependencies` | array | High-risk dependencies |
| `dependency_health_score` | float | Health score (0-100) |
| `recommendations` | array | Actionable recommendations |

### What-If Analysis

| Field | Type | Description |
|-------|------|-------------|
| `scenario_type` | string | Type of scenario analyzed |
| `downstream_impact` | object | Full downstream analysis |
| `upstream_dependencies` | object | Full upstream analysis |
| `timeline_minutes` | int | Estimated timeline |
| `severity` | string | Overall severity level |
| `mitigation_available` | bool | Whether mitigation is possible |
| `mitigation_steps` | array | Steps to mitigate impact |
| `rollback_possible` | bool | Whether rollback is possible |
| `rollback_steps` | array | Steps to rollback |

## Tips

1. **Run what-if before changes** - Always check impact before deployments
2. **Monitor dependency health** - Track health scores over time
3. **Address SPOFs** - Prioritize fixing single points of failure
4. **Use categories** - Filter by category to focus on specific impacts
5. **Check rollback** - Ensure rollback is possible before risky changes
6. **Estimate users** - Use user impact for communication planning
7. **Review mitigation** - Follow recommended mitigation steps
8. **Track health trends** - Dependency health should improve over time

## Need More Details?

See [Enhanced Impact Analysis Guide](./ENHANCED_IMPACT_ANALYSIS.md) for:
- Complete endpoint documentation
- Detailed use cases
- Integration examples
- Best practices
- Field descriptions
