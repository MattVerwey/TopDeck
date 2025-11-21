# Enhanced Risk Analysis - "What Will Happen" Analysis

## Overview

The enhanced risk analysis provides comprehensive answers to critical questions:
- **"What services and clients will be brought down if this fails?"**
- **"What does this app depend on and what are the risks?"**
- **"What will happen if this resource fails or is changed?"**

This enhancement addresses the need for clearer impact analysis that categorizes affected resources and provides actionable insights for change planning.

## New API Endpoints

### 1. Downstream Impact Analysis

**Endpoint:** `GET /api/v1/risk/resources/{resource_id}/downstream-impact`

**Purpose:** Answers "What services and clients will be affected if this resource fails?"

#### Response Structure

```json
{
  "resource_id": "api-gateway-prod",
  "resource_name": "Production API Gateway",
  "total_affected": 12,
  "affected_by_category": {
    "user_facing": [
      {
        "resource_id": "web-app-1",
        "resource_name": "Customer Portal",
        "resource_type": "web_app",
        "category": "user_facing",
        "relationship_type": "DEPENDS_ON",
        "impact_severity": "high",
        "is_critical": true
      }
    ],
    "backend_service": [...],
    "data_store": [...],
    "client_app": [...]
  },
  "critical_services_affected": [...],
  "client_apps_affected": [...],
  "user_facing_impact": "5 user-facing services affected (3 critical): Users will experience service outages or severe degradation",
  "backend_impact": "4 backend services affected: Internal service functionality will be impaired",
  "data_impact": "3 data stores affected (2 critical): Data access will be blocked",
  "estimated_users_affected": 5000,
  "business_impact_summary": "3 critical services will fail; 2 client applications will be impacted"
}
```

#### Usage Example

```bash
# Analyze what will be affected if API gateway fails
curl http://localhost:8000/api/v1/risk/resources/api-gateway-prod/downstream-impact

# Example output interpretation:
# - 12 total resources will be affected
# - 5 user-facing services (customers will see outages)
# - 4 backend services (internal systems impaired)
# - 3 data stores affected (data access blocked)
# - Estimated 5,000 users impacted
```

#### Resource Categories

Resources are automatically categorized based on their type:

- **`user_facing`**: Web apps, APIs, gateways that users interact with directly
- **`backend_service`**: Internal services, microservices, workers
- **`data_store`**: Databases, caches, storage systems
- **`infrastructure`**: Load balancers, networks, clusters
- **`integration`**: External integrations, webhooks
- **`client_app`**: Client applications consuming services

### 2. Upstream Dependency Health

**Endpoint:** `GET /api/v1/risk/resources/{resource_id}/upstream-dependencies`

**Purpose:** Answers "What does this app depend on and what are the risks?"

#### Response Structure

```json
{
  "resource_id": "web-app-1",
  "resource_name": "Customer Portal",
  "total_dependencies": 5,
  "dependencies_by_category": {
    "data_store": [
      {
        "resource_id": "sql-db-prod",
        "resource_name": "Customer Database",
        "resource_type": "database",
        "category": "data_store",
        "relationship_type": "DEPENDS_ON",
        "impact_severity": "high",
        "is_critical": true
      }
    ],
    "backend_service": [...],
    "integration": [...]
  },
  "unhealthy_dependencies": [...],
  "single_points_of_failure": [
    {
      "resource_id": "sql-db-prod",
      "resource_name": "Customer Database",
      "resource_type": "database",
      "category": "data_store",
      "relationship_type": "DEPENDS_ON",
      "impact_severity": "high",
      "is_critical": true
    }
  ],
  "high_risk_dependencies": [...],
  "dependency_health_score": 65.0,
  "recommendations": [
    "⚠️ 1 single point(s) of failure detected in dependencies. Add redundancy or failover capabilities.",
    "🔧 2 unhealthy dependencies detected. Review and remediate issues in dependent services.",
    "📊 1 high-risk dependencies detected. Consider alternatives or add circuit breakers."
  ]
}
```

#### Usage Example

```bash
# Check what a web app depends on
curl http://localhost:8000/api/v1/risk/resources/web-app-1/upstream-dependencies

# Example output interpretation:
# - Web app depends on 5 resources
# - 1 dependency is a single point of failure (database)
# - 2 dependencies are unhealthy
# - Overall dependency health score: 65/100 (needs improvement)
# - Recommendations provided for each issue
```

#### Dependency Health Score

The health score (0-100) considers:
- **Unhealthy dependencies** (deduct up to 30 points)
- **Single points of failure** (deduct up to 40 points)
- **High-risk dependencies** (deduct up to 20 points)

**Score Interpretation:**
- 90-100: Excellent - healthy dependencies
- 70-89: Good - minor concerns
- 50-69: Fair - action recommended
- Below 50: Poor - immediate action required

### 3. What-If Scenario Analysis

**Endpoint:** `GET /api/v1/risk/resources/{resource_id}/what-if?scenario_type={type}`

**Purpose:** Comprehensive "what will happen" analysis for different scenarios

#### Scenario Types

- **`failure`**: Resource fails completely (default)
- **`maintenance`**: Planned maintenance window
- **`update`**: Deploying an update/change
- **`degraded`**: Resource running in degraded state

#### Response Structure

```json
{
  "resource_id": "api-gateway-prod",
  "resource_name": "Production API Gateway",
  "scenario_type": "failure",
  "downstream_impact": {
    // Full DownstreamImpactAnalysis (see above)
  },
  "upstream_dependencies": {
    // Full UpstreamDependencyHealth (see above)
  },
  "timeline_minutes": 0,
  "severity": "severe",
  "mitigation_available": true,
  "mitigation_steps": [
    "Enable maintenance mode for affected critical services",
    "Notify stakeholders and users of planned impact",
    "Scale up redundant instances before making changes",
    "Enable circuit breakers to prevent cascade failures"
  ],
  "rollback_possible": false,
  "rollback_steps": []
}
```

#### Usage Examples

```bash
# Analyze a complete failure scenario
curl "http://localhost:8000/api/v1/risk/resources/api-gateway-prod/what-if?scenario_type=failure"

# Analyze planned maintenance impact
curl "http://localhost:8000/api/v1/risk/resources/database-prod/what-if?scenario_type=maintenance"

# Analyze deployment update impact
curl "http://localhost:8000/api/v1/risk/resources/web-app/what-if?scenario_type=update"
```

#### Timeline Estimation

- **Failure**: 0 minutes (immediate impact)
- **Maintenance**: 60 minutes (planned, can schedule)
- **Update**: 30 minutes (gradual rollout)

#### Severity Levels

- **`minimal`**: 0 affected resources
- **`low`**: 1-5 affected resources, no critical services
- **`medium`**: 6-10 affected resources
- **`high`**: 10+ affected resources
- **`severe`**: Critical services affected

## Use Cases

### Use Case 1: Pre-Deployment Risk Assessment

**Scenario:** You need to deploy an update to the API gateway

```bash
# Step 1: Analyze what-if scenario for the update
curl "http://localhost:8000/api/v1/risk/resources/api-gateway/what-if?scenario_type=update"

# Result: 
# - 12 services will be affected
# - 3 critical services including customer portal
# - Estimated 5,000 users impacted
# - Mitigation steps provided
# - Rollback is possible

# Step 2: Check downstream impact details
curl http://localhost:8000/api/v1/risk/resources/api-gateway/downstream-impact

# Result:
# - 5 user-facing services (need maintenance mode)
# - 4 backend services (internal notification required)
# - 3 data stores affected

# Decision: Schedule during low-traffic window with maintenance page
```

### Use Case 2: Dependency Health Check

**Scenario:** Check if a web app has risky dependencies

```bash
# Check upstream dependencies
curl http://localhost:8000/api/v1/risk/resources/web-app/upstream-dependencies

# Result:
# - Dependency health score: 55/100 (Fair)
# - 1 SPOF detected: Primary database (no replica)
# - 2 high-risk dependencies
# - Recommendations: Add database replica, implement circuit breakers

# Action: Plan to add database read replica
```

### Use Case 3: Incident Impact Assessment

**Scenario:** Database is experiencing issues

```bash
# Check what will be affected if database fails
curl http://localhost:8000/api/v1/risk/resources/sql-db-prod/downstream-impact

# Result:
# - 8 services will fail
# - 6 user-facing services affected
# - Estimated 10,000 users impacted
# - Critical services: Customer Portal, API, Mobile App

# Action: Trigger incident response plan
```

### Use Case 4: Change Advisory Board Review

**Scenario:** Need to present change impact to CAB

```bash
# Get comprehensive what-if analysis
curl "http://localhost:8000/api/v1/risk/resources/payment-service/what-if?scenario_type=update"

# Use the response to populate CAB documentation:
# - Business Impact: "Payment service update affects 4 critical services"
# - User Impact: "Estimated 3,000 users affected during deployment"
# - Timeline: "30-minute gradual rollout"
# - Mitigation: "Enable circuit breakers, scale redundant instances"
# - Rollback Plan: "Available, 5-minute rollback time"
```

## Best Practices

### 1. Regular Dependency Health Monitoring

```bash
# Create a script to monitor dependency health for critical services
for service in api-gateway web-app payment-service; do
  health=$(curl -s "http://localhost:8000/api/v1/risk/resources/$service/upstream-dependencies" | jq .dependency_health_score)
  if [ $(echo "$health < 70" | bc) -eq 1 ]; then
    echo "WARNING: $service dependency health score: $health"
  fi
done
```

### 2. Pre-Deployment Checklist

Before any deployment:
1. Run what-if analysis for the update scenario
2. Check downstream impact to identify affected services
3. Review mitigation steps
4. Verify rollback capability
5. Schedule based on timeline and user impact

### 3. Incident Response

During an incident:
1. Run downstream impact analysis to understand scope
2. Check what-if scenario for failure to see full impact
3. Use the affected services list to notify stakeholders
4. Follow recommended recovery steps

### 4. Architecture Review

During architecture reviews:
1. Check upstream dependencies for all critical services
2. Identify single points of failure
3. Verify dependency health scores
4. Address low-scoring dependencies with redundancy

## Integration with Existing Features

### With Standard Risk Assessment

```bash
# Get standard risk assessment
risk_score=$(curl -s "http://localhost:8000/api/v1/risk/resources/api-gateway" | jq .risk_score)

# If risk score is high, get detailed impact analysis
if [ $(echo "$risk_score > 70" | bc) -eq 1 ]; then
  curl "http://localhost:8000/api/v1/risk/resources/api-gateway/downstream-impact"
  curl "http://localhost:8000/api/v1/risk/resources/api-gateway/upstream-dependencies"
fi
```

### With Blast Radius

The new downstream impact analysis enhances blast radius with:
- **Categorization** of affected resources
- **Business impact** summaries
- **User impact** estimation
- **Critical service** identification

```bash
# Standard blast radius
curl "http://localhost:8000/api/v1/risk/blast-radius/api-gateway"

# Enhanced downstream impact (includes categorization)
curl "http://localhost:8000/api/v1/risk/resources/api-gateway/downstream-impact"
```

## Comparison: Before vs After

### Before: Basic Question

**Q:** "What will happen if the API gateway fails?"

**Basic Answer:**
- Blast radius: 12 affected resources
- Risk score: 85/100
- Recommendation: High risk, add redundancy

### After: Enhanced Analysis

**Q:** "What will happen if the API gateway fails?"

**Detailed Answer:**
- **User-Facing Impact:** 5 services affected (3 critical) - Users will experience outages
- **Backend Impact:** 4 backend services affected - Internal systems impaired
- **Data Impact:** 3 data stores affected (2 critical) - Data access blocked
- **Client Apps:** 2 mobile/web clients impacted
- **Estimated Users:** 5,000 affected
- **Business Impact:** "3 critical services will fail; 2 client applications impacted"
- **Critical Services:** Customer Portal, Mobile API, Payment Gateway
- **Timeline:** Immediate (0 minutes)
- **Severity:** Severe
- **Mitigation Available:** Yes
  - Enable maintenance mode for critical services
  - Notify stakeholders and users
  - Enable circuit breakers
  - Scale up redundant instances

## Summary

The enhanced risk analysis provides:

1. **Clearer Impact Understanding** - Resources categorized by type and criticality
2. **Dependency Health Visibility** - Know what you depend on and the risks
3. **Actionable Insights** - Specific mitigation and rollback steps
4. **User Impact Estimation** - Understand business consequences
5. **Comprehensive Scenarios** - Analyze different "what if" situations

These enhancements enable better decision-making for:
- Deployment planning
- Incident response
- Architecture reviews
- Change management
- Risk mitigation
