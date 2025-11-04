# Change Management Guide

## Overview

TopDeck's Change Management features help organizations track, analyze, and manage changes across their cloud infrastructure. This guide covers how to use the change management capabilities including change request tracking, impact assessment, and integration with external systems.

## Features

### 1. Change Request Tracking

Track change requests throughout their lifecycle:

- **Create change requests** for planned changes
- **Track status** from draft to completion
- **Link to affected resources** to understand impact
- **Schedule changes** with maintenance windows
- **Integrate with external systems** (ServiceNow, Jira)

### 2. Impact Assessment ✨ Enhanced

Automatically analyze the impact of proposed changes with **resource-specific intelligence**:

- **Blast radius calculation** - identify directly and indirectly affected resources
- **Smart risk scoring** - adjusts based on change type AND resource characteristics
- **Performance impact** - non-linear estimation based on actual risk levels
- **Context-aware downtime estimation** - considers:
  - Resource type (databases take longer than function apps)
  - Resource risk score and criticality
  - Number of dependent resources
  - Whether resource is on critical path
  - Specific change type + resource type combinations
- **Intelligent approval routing** - determines approvals based on actual impact

**Key Improvement**: Impact now varies based on actual resource characteristics, not just change type. A database deployment will show significantly different impact than a function app deployment, even though both are "deployments".

### 3. Change Calendar

Visualize upcoming changes across your infrastructure:

- **Timeline view** of scheduled changes
- **Conflict detection** - identify overlapping changes
- **Resource availability** - ensure resources are available
- **Maintenance windows** - plan changes during optimal times

### 4. External System Integration

Connect TopDeck with your existing change management tools:

- **ServiceNow integration** via webhooks
- **Jira integration** via webhooks
- **Automatic sync** of change requests
- **Bi-directional updates** (planned)

## API Reference

### Create Change Request

Create a new change request:

```bash
POST /api/v1/changes
Content-Type: application/json

{
  "title": "Deploy new version of API service",
  "description": "Deploying v2.1.0 of the customer API service",
  "change_type": "deployment",
  "affected_resources": ["resource-id-1", "resource-id-2"],
  "scheduled_start": "2024-11-15T02:00:00Z",
  "scheduled_end": "2024-11-15T03:00:00Z",
  "requester": "john.doe@company.com"
}
```

Response:
```json
{
  "id": "change-123",
  "title": "Deploy new version of API service",
  "change_type": "deployment",
  "status": "draft",
  "risk_level": "medium",
  "affected_resources": ["resource-id-1", "resource-id-2"],
  "affected_services_count": 5,
  "estimated_downtime_seconds": 900,
  "created_at": "2024-11-01T10:30:00Z"
}
```

### Assess Change Impact

Analyze the impact of a proposed change:

```bash
POST /api/v1/changes/{change_id}/assess?resource_id=resource-123
```

Response:
```json
{
  "change_id": "change-123",
  "directly_affected_resources": [
    {
      "resource_id": "resource-123",
      "name": "api-service",
      "type": "app_service",
      "risk_score": 65.5,
      "blast_radius": 8
    }
  ],
  "indirectly_affected_resources": [
    {
      "resource_id": "resource-456",
      "name": "web-frontend",
      "type": "app_service"
    }
  ],
  "total_affected_count": 12,
  "overall_risk_score": 62.3,
  "performance_degradation_pct": 15.5,
  "estimated_downtime_seconds": 900,
  "user_impact_level": "medium",
  "critical_path_affected": true,
  "recommended_window": "maintenance",
  "rollback_plan_required": true,
  "approval_required": true,
  "breakdown": {
    "direct_dependents": 5,
    "indirect_dependents": 7,
    "critical_path": true
  },
  "recommendations": [
    "This change affects critical infrastructure. Ensure rollback plan is in place.",
    "High risk change. Recommend additional approval and testing before execution.",
    "Schedule during low-traffic maintenance window if possible.",
    "Monitor all affected services during and after the change."
  ]
}
```

### Get Change Calendar

View scheduled changes:

```bash
GET /api/v1/changes/calendar?start_date=2024-11-01T00:00:00Z&end_date=2024-11-30T23:59:59Z
```

Response:
```json
[
  {
    "id": "change-123",
    "title": "Deploy API service v2.1.0",
    "change_type": "deployment",
    "status": "scheduled",
    "risk_level": "medium",
    "scheduled_start": "2024-11-15T02:00:00Z",
    "scheduled_end": "2024-11-15T03:00:00Z",
    "requester": "john.doe@company.com"
  }
]
```

### Get Available Change Types

Get list of supported change types:

```bash
GET /api/v1/changes/types
```

Response:
```json
[
  "deployment",
  "configuration",
  "scaling",
  "restart",
  "update",
  "patch",
  "infrastructure",
  "emergency"
]
```

## Webhook Integration

### ServiceNow Webhook

Configure ServiceNow to send change request notifications to TopDeck:

1. In ServiceNow, navigate to **System Web Services > Outbound > REST Message**
2. Create a new REST Message:
   - Name: `TopDeck Change Notification`
   - Endpoint: `https://your-topdeck-instance.com/api/v1/webhooks/servicenow`
   - HTTP Method: `POST`
3. Configure the message body to include change request data
4. Set up a Business Rule to trigger the webhook on change request creation/update

Webhook endpoint:
```
POST /api/v1/webhooks/servicenow
Content-Type: application/json
X-ServiceNow-Signature: <signature>

{
  "number": "CHG0001234",
  "short_description": "Deploy new application version",
  "description": "Detailed description...",
  "state": "scheduled",
  "risk": "medium",
  "type": "normal",
  "start_date": "2024-11-15 02:00:00",
  "end_date": "2024-11-15 03:00:00",
  "cmdb_ci": "resource-id-123",
  "requested_by": {
    "name": "John Doe"
  }
}
```

### Jira Webhook

Configure Jira to send issue notifications to TopDeck:

1. In Jira, navigate to **Settings > System > WebHooks**
2. Create a new webhook:
   - URL: `https://your-topdeck-instance.com/api/v1/webhooks/jira`
   - Events: Issue Created, Issue Updated
   - JQL Filter: `project = CHANGE AND type = Change`
3. Save the webhook

Webhook endpoint:
```
POST /api/v1/webhooks/jira
Content-Type: application/json
X-Hub-Signature: <signature>

{
  "issue": {
    "key": "CHANGE-123",
    "fields": {
      "summary": "Deploy new application version",
      "description": "Detailed description...",
      "status": {
        "name": "In Progress"
      },
      "priority": {
        "name": "Medium"
      },
      "issuetype": {
        "name": "Change"
      },
      "labels": ["resource:resource-id-123"],
      "reporter": {
        "displayName": "John Doe"
      }
    }
  }
}
```

## Usage Examples

### Example 1: Manual Change Request

Create and assess a manual change request for a deployment:

```bash
# Step 1: Create the change request
curl -X POST http://localhost:8000/api/v1/changes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Update customer API to v2.1.0",
    "description": "Rolling update with new features and bug fixes",
    "change_type": "deployment",
    "affected_resources": ["api-service-prod"],
    "scheduled_start": "2024-11-15T02:00:00Z",
    "scheduled_end": "2024-11-15T03:00:00Z",
    "requester": "devops@company.com"
  }'

# Step 2: Assess the impact
curl -X POST "http://localhost:8000/api/v1/changes/change-123/assess?resource_id=api-service-prod"

# Step 3: Review recommendations and proceed with change
```

### Example 2: ServiceNow Integration

Automatically receive and analyze changes from ServiceNow:

1. Configure ServiceNow webhook (see above)
2. When a change request is created in ServiceNow, it's automatically:
   - Imported into TopDeck
   - Impact assessment is triggered
   - Risk level is calculated
   - Recommendations are generated
3. View the change in TopDeck dashboard

### Example 3: Change Calendar View

View upcoming changes for the next 30 days:

```bash
# Get changes for November 2024
curl "http://localhost:8000/api/v1/changes/calendar?start_date=2024-11-01T00:00:00Z&end_date=2024-11-30T23:59:59Z"
```

View in the web UI:
1. Navigate to the Change Impact page
2. Click on "View Calendar" (planned feature)
3. See all scheduled changes in a timeline view

## Best Practices

### 1. Change Planning

- **Create change requests early** - give time for review and approval
- **Link all affected resources** - ensure complete impact assessment
- **Schedule during maintenance windows** - minimize user impact
- **Prepare rollback plans** - especially for high-risk changes

### 2. Impact Assessment

- **Run assessments before approval** - understand risks early
- **Review all recommendations** - don't ignore the guidance
- **Check blast radius** - understand the full scope of impact
- **Verify dependencies** - ensure all dependent services are considered

### 3. Risk Management

- **High-risk changes need extra approval** - don't bypass the process
- **Test rollback procedures** - ensure you can recover
- **Monitor during changes** - watch for unexpected issues
- **Document lessons learned** - improve future changes

### 4. Integration

- **Use webhook authentication** - secure your endpoints
- **Map fields correctly** - ensure data integrity
- **Handle failures gracefully** - don't lose change data
- **Sync bidirectionally** (when available) - keep systems in sync

## Troubleshooting

### Issue: Change Impact Assessment Returns Empty Results

**Cause**: No resources linked or topology not discovered

**Solution**:
1. Ensure resources are discovered: `python -m topdeck.discovery.azure.discoverer`
2. Verify resource IDs are correct
3. Check that dependencies are mapped in Neo4j

### Issue: Webhook Not Receiving Data

**Cause**: Network connectivity or authentication issues

**Solution**:
1. Verify webhook URL is accessible from external system
2. Check firewall rules
3. Verify authentication headers
4. Check application logs: `docker-compose logs -f`

### Issue: Risk Score Seems Incorrect

**Cause**: Incomplete topology data or missing metrics

**Solution**:
1. Ensure complete discovery has run
2. Verify all dependencies are mapped
3. Check that monitoring data is being collected
4. Review risk scoring configuration

## Enhanced Impact Analysis Details

### Resource-Aware Impact Calculation

The impact analysis system now considers multiple factors to provide accurate, resource-specific impact estimates:

#### 1. Resource Type Multipliers

Different resource types have different change complexity:

| Resource Type | Multiplier | Reason |
|---------------|------------|--------|
| Database (SQL, PostgreSQL, etc.) | 2.0x | Requires careful handling, backups, validation |
| Virtual Machines | 1.5x | Moderate complexity, longer boot times |
| Kubernetes Clusters | 1.8x | Complex orchestration, many moving parts |
| Storage Accounts | 1.5x | Data integrity concerns |
| Web Apps | 1.0x | Standard complexity |
| Function Apps | 0.8x | Fast deployments, minimal downtime |
| Logic Apps | 0.7x | Lightweight, quick to change |

#### 2. Risk Score Factor

Higher risk resources get longer estimated downtime (1.0x to 2.0x multiplier):
- Risk score 0: 1.0x multiplier
- Risk score 50: 1.5x multiplier  
- Risk score 100: 2.0x multiplier

#### 3. Dependency Consideration

More dependent resources means more coordination:
- Every 5 dependents adds 10% to downtime estimate
- Ensures time for proper communication and coordination

#### 4. Critical Path Multiplier

Single points of failure get extra care:
- Critical resources: 1.5x multiplier
- Non-critical resources: 1.0x multiplier

#### 5. Change Type Risk

Different change types have inherent risk levels:

| Change Type | Risk Multiplier | Notes |
|-------------|-----------------|-------|
| Emergency | 1.4x | Rushed, higher risk |
| Infrastructure | 1.3x | Complex, affects many resources |
| Update | 1.2x | Version compatibility risks |
| Deployment | 1.1x | New code always carries risk |
| Patch | 1.0x | Standard risk baseline |
| Configuration | 1.1x | Can have unexpected impacts |
| Scaling | 0.9x | Well-tested, lower risk |
| Restart | 0.8x | Lowest risk, well-understood |

### Example Impact Differences

For a **DEPLOYMENT** change (base: 15 minutes):

```
Critical Database:     102 minutes (6.8x base)
  - Database: 2.0x
  - High risk (75): 1.75x
  - Many dependencies (15): 1.3x
  - Critical: 1.5x
  - Deployment type: 1.1x
  = 6.8x total

Standard Web App:      29 minutes (1.9x base)
  - Web app: 1.0x
  - Medium risk (60): 1.6x
  - Moderate dependencies (10): 1.2x
  - Non-critical: 1.0x
  - Deployment type: 1.1x
  = 1.9x total

Low-Risk Function App: 16 minutes (1.2x base)
  - Function app: 0.8x
  - Low risk (40): 1.4x
  - Few dependencies (3): 1.06x
  - Non-critical: 1.0x
  - Deployment type: 1.1x
  = 1.2x total
```

### Performance Impact Estimation

Non-linear performance degradation based on risk:
- **Low risk (0-40)**: 0-5% degradation (minimal impact)
- **Medium risk (40-70)**: 5-15% degradation (moderate impact)
- **High risk (70-100)**: 15-30% degradation (significant impact)

### Demonstration

Run the demonstration script to see the improvements:

```bash
python examples/change_impact_comparison_standalone.py
```

## Future Enhancements

Planned features for future releases:

- **Automated approval workflows** - route changes based on risk level
- **Change templates** - pre-defined change types with defaults
- **Change success/failure tracking** - learn from past changes
- **Historical learning** - refine estimates based on actual downtime data
- **Change conflict detection** - prevent overlapping changes
- **Automated rollback** - trigger rollback on failure detection
- **Change metrics dashboard** - track change management KPIs
- **Bi-directional sync** - update external systems with TopDeck data

## Support

For issues or questions:
- GitHub Issues: https://github.com/MattVerwey/TopDeck/issues
- Documentation: https://github.com/MattVerwey/TopDeck/tree/main/docs
- API Docs: http://localhost:8000/api/docs
