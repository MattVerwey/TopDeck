# Change Management Quick Reference

Quick reference for TopDeck change management features.

## Quick Start

### 1. Create a Change Request

```bash
curl -X POST http://localhost:8000/api/v1/changes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy API v2.0",
    "description": "Production deployment",
    "change_type": "deployment",
    "scheduled_start": "2024-11-15T02:00:00Z",
    "requester": "devops@company.com"
  }'
```

### 2. Assess Impact

```bash
curl -X POST "http://localhost:8000/api/v1/changes/{change-id}/assess?resource_id=resource-123"
```

### 3. View Scheduled Changes

```bash
curl "http://localhost:8000/api/v1/changes/calendar?start_date=2024-11-01T00:00:00Z"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/changes` | POST | Create change request |
| `/api/v1/changes/{id}/assess` | POST | Assess change impact |
| `/api/v1/changes/calendar` | GET | View scheduled changes |
| `/api/v1/changes/types` | GET | Get change types |
| `/api/v1/changes/metrics` | GET | Get change metrics |
| `/api/v1/changes/{id}/approve` | POST | Approve change |
| `/api/v1/changes/{id}/reject` | POST | Reject change |
| `/api/v1/webhooks/servicenow` | POST | ServiceNow webhook |
| `/api/v1/webhooks/jira` | POST | Jira webhook |

## Change Types

- `deployment` - Application deployments
- `configuration` - Configuration changes
- `scaling` - Resource scaling
- `restart` - Service restarts
- `update` - Version updates
- `patch` - Security/bug patches
- `infrastructure` - Infrastructure changes
- `emergency` - Emergency changes

## Risk Levels

- `low` - Low risk, minimal impact
- `medium` - Moderate risk, some services affected
- `high` - High risk, significant impact
- `critical` - Critical risk, major infrastructure affected

## Change Status Lifecycle

```
draft → pending_approval → approved → scheduled → in_progress → completed
                                                            ↓
                                                    failed / rolled_back
```

## Impact Assessment Fields

```json
{
  "total_affected_count": 12,
  "overall_risk_score": 65.5,
  "performance_degradation_pct": 15.0,
  "estimated_downtime_seconds": 900,
  "user_impact_level": "medium",
  "critical_path_affected": true,
  "recommended_window": "maintenance",
  "rollback_plan_required": true,
  "approval_required": true
}
```

## Metrics

View change management metrics:

```bash
curl "http://localhost:8000/api/v1/changes/metrics?days=30"
```

Returns:
- Success rate
- Emergency change rate
- Rollback rate
- Average lead time
- Risk distribution
- Weekly trends
- Recommendations

## Integration Setup

### ServiceNow

1. Create REST Message in ServiceNow
2. Point to: `/api/v1/webhooks/servicenow`
3. Map change request fields
4. Set up Business Rule trigger

### Jira

1. Create webhook in Jira settings
2. Point to: `/api/v1/webhooks/jira`
3. Filter: `project = CHANGE`
4. Events: Issue Created, Issue Updated

## Best Practices

### Planning
✅ Create changes at least 24 hours in advance  
✅ Link all affected resources  
✅ Schedule during maintenance windows  
✅ Prepare rollback plans for high-risk changes  

### Assessment
✅ Run impact assessment before approval  
✅ Review all recommendations  
✅ Check blast radius and dependencies  
✅ Verify critical path services  

### Execution
✅ Monitor services during changes  
✅ Follow rollback plan if issues occur  
✅ Update change status promptly  
✅ Document lessons learned  

### Risk Management
✅ High-risk changes require additional approval  
✅ Emergency changes need justification  
✅ Test changes in non-prod first  
✅ Have rollback plan ready  

## Common Workflows

### Standard Change

1. Create change request (draft)
2. Assess impact
3. Request approvals (auto-routed by risk)
4. Schedule during maintenance window
5. Execute change
6. Mark as completed

### Emergency Change

1. Create with type="emergency"
2. Get emergency approver approval
3. Execute immediately
4. Post-change review required

### High-Risk Change

1. Create change request
2. Impact shows critical_path_affected=true
3. Requires multiple approvers:
   - Change Manager
   - Technical Lead
   - Security Reviewer
   - Business Owner
4. Schedule during major maintenance window
5. Extra monitoring during execution

## Troubleshooting

### Issue: Impact assessment returns empty

**Fix**: Ensure resources are discovered and mapped in topology

```bash
# Run discovery
python -m topdeck.discovery.azure.discoverer --subscription-id <id>
```

### Issue: Webhook not receiving data

**Fix**: Check URL, authentication, and firewall rules

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/api/v1/webhooks/servicenow/health
```

### Issue: Metrics show no data

**Fix**: Ensure changes have been created and are in Neo4j

```bash
# Check Neo4j
docker exec -it topdeck-neo4j cypher-shell \
  "MATCH (c:ChangeRequest) RETURN count(c)"
```

## Web UI

Access change management in the web interface:

1. Navigate to **Change Impact** page
2. Select a service
3. Choose change type
4. Click **Analyze**
5. Review impact assessment and recommendations

## Further Reading

- [Complete Change Management Guide](CHANGE_MANAGEMENT_GUIDE.md)
- [API Documentation](http://localhost:8000/api/docs)
- [Risk Analysis Guide](ENHANCED_RISK_ANALYSIS.md)
