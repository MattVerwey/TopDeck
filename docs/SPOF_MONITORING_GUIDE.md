# SPOF Monitoring Guide

## Overview

SPOF (Single Point of Failure) Monitoring is a critical feature in TopDeck that continuously monitors your infrastructure for single points of failure. It automatically detects resources that, if they fail, would cause cascading failures across your system, helping you proactively address reliability risks.

## What is a Single Point of Failure?

A Single Point of Failure (SPOF) is a resource in your infrastructure that:
1. Has no redundant alternatives or backups
2. Is depended upon by other resources
3. Would cause cascading failures if it went down

Examples of common SPOFs:
- A single database instance without replicas
- A single authentication service without horizontal scaling
- A single API gateway handling all traffic
- A single load balancer without a backup

## Key Features

### 1. Automated Scanning
- Runs periodic scans every 15 minutes (configurable)
- Scans on startup for immediate visibility
- Can be triggered manually via API

### 2. Change Detection
- Detects new SPOFs as they appear
- Detects when SPOFs are resolved (redundancy added)
- Maintains a history of all SPOF changes
- Logs changes for audit trails

### 3. Risk Scoring
- Each SPOF has a risk score (0-100)
- High-risk SPOFs (score > 80) are flagged
- Risk score considers:
  - Number of dependent resources
  - Blast radius (total affected if failure occurs)
  - Resource criticality
  - Historical failure rates

### 4. Prometheus Metrics
- `topdeck_spof_total`: Total number of SPOFs
- `topdeck_spof_by_type{resource_type}`: SPOFs grouped by resource type
- `topdeck_spof_high_risk`: Count of high-risk SPOFs
- `topdeck_spof_changes_total{change_type}`: SPOF state changes (new/resolved)

### 5. Actionable Recommendations
Each detected SPOF includes specific recommendations:
- Add redundant instances
- Implement automatic failover
- Deploy across availability zones
- Increase monitoring and alerting

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable/disable SPOF monitoring
ENABLE_SPOF_MONITORING=true

# Scan interval in seconds (default: 900 = 15 minutes)
SPOF_SCAN_INTERVAL=900

# High-risk threshold (0-100, default: 80)
SPOF_HIGH_RISK_THRESHOLD=80.0
```

### Customization

**Scan Frequency:**
- Development: `SPOF_SCAN_INTERVAL=300` (5 minutes)
- Production: `SPOF_SCAN_INTERVAL=900` (15 minutes)
- Low-change environments: `SPOF_SCAN_INTERVAL=1800` (30 minutes)

**Risk Threshold:**
- Conservative (more alerts): `SPOF_HIGH_RISK_THRESHOLD=70.0`
- Balanced (recommended): `SPOF_HIGH_RISK_THRESHOLD=80.0`
- Critical only: `SPOF_HIGH_RISK_THRESHOLD=90.0`

## API Endpoints

### Get Current SPOFs

```bash
GET /api/v1/monitoring/spof/current
```

Returns all currently detected SPOFs with details.

**Response:**
```json
[
  {
    "resource_id": "db-primary",
    "resource_name": "Primary Database",
    "resource_type": "database",
    "dependents_count": 10,
    "blast_radius": 15,
    "risk_score": 85.0,
    "recommendations": [
      "⚠️ This is a Single Point of Failure",
      "Add redundant instances across availability zones",
      "Implement automatic failover mechanisms",
      "Increase monitoring and alerting priority"
    ]
  }
]
```

**Example:**
```bash
curl http://localhost:8000/api/v1/monitoring/spof/current
```

### Get SPOF History

```bash
GET /api/v1/monitoring/spof/history?limit=50
```

Returns recent SPOF changes (new SPOFs detected, SPOFs resolved).

**Parameters:**
- `limit` (optional): Maximum number of changes to return (default: 50)

**Response:**
```json
[
  {
    "change_type": "new",
    "resource_id": "auth-service",
    "resource_name": "Authentication Service",
    "resource_type": "web_app",
    "detected_at": "2025-11-03T10:30:00Z",
    "risk_score": 75.0,
    "blast_radius": 8
  },
  {
    "change_type": "resolved",
    "resource_id": "api-gateway",
    "resource_name": "API Gateway",
    "resource_type": "load_balancer",
    "detected_at": "2025-11-03T09:15:00Z",
    "risk_score": 70.0,
    "blast_radius": 12
  }
]
```

**Example:**
```bash
curl http://localhost:8000/api/v1/monitoring/spof/history?limit=20
```

### Get Statistics

```bash
GET /api/v1/monitoring/spof/statistics
```

Returns aggregate statistics about SPOF monitoring.

**Response:**
```json
{
  "status": "active",
  "last_scan": "2025-11-03T10:45:00Z",
  "total_spofs": 5,
  "high_risk_spofs": 2,
  "by_resource_type": {
    "database": 2,
    "web_app": 2,
    "load_balancer": 1
  },
  "total_changes": 15,
  "recent_changes": {
    "new": 3,
    "resolved": 2
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/monitoring/spof/statistics
```

### Trigger Manual Scan

```bash
POST /api/v1/monitoring/spof/scan
```

Triggers an immediate SPOF scan (doesn't wait for the next scheduled scan).

**Response:**
```json
{
  "status": "scheduled",
  "message": "SPOF scan has been scheduled to run",
  "last_scan": "2025-11-03T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/monitoring/spof/scan
```

### Get Metrics

```bash
GET /api/v1/monitoring/spof/metrics
```

Returns metrics in a format suitable for external monitoring systems.

**Response:**
```json
{
  "status": "active",
  "last_scan": "2025-11-03T10:45:00Z",
  "metrics": {
    "spof_total": 5,
    "spof_high_risk": 2,
    "spof_by_type": {
      "database": 2,
      "web_app": 2,
      "load_balancer": 1
    },
    "spof_changes_new": 3,
    "spof_changes_resolved": 2
  }
}
```

## Prometheus Integration

### Setting Up Alerts

Add these alerts to your Prometheus configuration:

```yaml
groups:
  - name: spof_alerts
    rules:
      # Alert on new high-risk SPOFs
      - alert: HighRiskSPOFDetected
        expr: topdeck_spof_high_risk > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High-risk SPOF detected in infrastructure"
          description: "{{ $value }} high-risk single points of failure detected"

      # Alert when total SPOFs increase
      - alert: SPOFCountIncreasing
        expr: delta(topdeck_spof_total[1h]) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "SPOF count increasing"
          description: "SPOF count increased by {{ $value }} in the last hour"

      # Alert on critical database SPOFs
      - alert: DatabaseSPOFDetected
        expr: topdeck_spof_by_type{resource_type="database"} > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database SPOF detected"
          description: "{{ $value }} database SPOFs detected - critical infrastructure risk"
```

### Querying Metrics

Example Prometheus queries:

```promql
# Total SPOFs over time
topdeck_spof_total

# High-risk SPOFs
topdeck_spof_high_risk

# SPOFs by type
topdeck_spof_by_type

# SPOF change rate (new SPOFs per hour)
rate(topdeck_spof_changes_total{change_type="new"}[1h])

# SPOF resolution rate (resolved SPOFs per hour)
rate(topdeck_spof_changes_total{change_type="resolved"}[1h])
```

## Grafana Dashboard

### Key Panels

1. **SPOF Count (Single Stat)**
   - Metric: `topdeck_spof_total`
   - Shows current total SPOFs

2. **High-Risk SPOFs (Single Stat)**
   - Metric: `topdeck_spof_high_risk`
   - Shows count of critical SPOFs

3. **SPOFs by Type (Bar Chart)**
   - Metric: `topdeck_spof_by_type`
   - Groups SPOFs by resource type

4. **SPOF Changes (Graph)**
   - Metric: `rate(topdeck_spof_changes_total[5m])`
   - Shows new and resolved SPOFs over time

## Best Practices

### 1. Set Appropriate Scan Intervals

- **High-change environments**: 5-10 minutes
- **Normal operations**: 15 minutes (default)
- **Stable production**: 30 minutes

### 2. Address High-Risk SPOFs First

Focus on SPOFs with:
- Risk score > 80
- High blast radius (affects many resources)
- Critical resource types (databases, auth services)

### 3. Track Resolution Progress

Use the history endpoint to:
- Monitor SPOF resolution trends
- Verify redundancy implementations
- Track team progress on reliability

### 4. Automate Response

Consider automating responses to SPOF detection:
- Create Jira tickets automatically
- Send Slack notifications
- Trigger runbooks
- Update service catalog

### 5. Regular Reviews

- Weekly review of new SPOFs
- Monthly trending analysis
- Quarterly architecture reviews

## Integration Examples

### Slack Notifications

```python
import requests
from datetime import datetime

def check_and_notify_spofs():
    """Check for new SPOFs and notify Slack."""
    # Get current SPOFs
    response = requests.get("http://localhost:8000/api/v1/monitoring/spof/current")
    spofs = response.json()
    
    high_risk_spofs = [s for s in spofs if s["risk_score"] > 80]
    
    if high_risk_spofs:
        message = f"⚠️ {len(high_risk_spofs)} high-risk SPOFs detected:\n"
        for spof in high_risk_spofs:
            message += f"• {spof['resource_name']} (Risk: {spof['risk_score']:.0f})\n"
        
        # Send to Slack
        requests.post(
            "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
            json={"text": message}
        )

# Run periodically
check_and_notify_spofs()
```

### Jira Ticket Creation

```python
from jira import JIRA

def create_spof_tickets():
    """Create Jira tickets for high-risk SPOFs."""
    # Get current SPOFs
    response = requests.get("http://localhost:8000/api/v1/monitoring/spof/current")
    spofs = response.json()
    
    jira = JIRA(server="https://your-jira.com", basic_auth=("user", "token"))
    
    for spof in spofs:
        if spof["risk_score"] > 80:
            issue = {
                "project": {"key": "INFRA"},
                "summary": f"SPOF: {spof['resource_name']}",
                "description": f"""
                High-risk Single Point of Failure detected:
                
                Resource: {spof['resource_name']}
                Type: {spof['resource_type']}
                Risk Score: {spof['risk_score']}
                Blast Radius: {spof['blast_radius']} affected resources
                
                Recommendations:
                {chr(10).join('- ' + r for r in spof['recommendations'])}
                """,
                "issuetype": {"name": "Task"},
                "priority": {"name": "High"},
                "labels": ["spof", "reliability", "infrastructure"],
            }
            jira.create_issue(fields=issue)
```

## Troubleshooting

### SPOF Monitor Not Running

**Symptom:** No SPOFs detected, statistics show "not_scanned"

**Solutions:**
1. Check scheduler is running:
   ```bash
   curl http://localhost:8000/api/v1/scheduler/status
   ```

2. Check configuration:
   ```bash
   echo $ENABLE_SPOF_MONITORING  # Should be "true"
   ```

3. Check logs:
   ```bash
   grep "SPOF" /var/log/topdeck/app.log
   ```

4. Trigger manual scan:
   ```bash
   curl -X POST http://localhost:8000/api/v1/monitoring/spof/scan
   ```

### Too Many False Positives

**Symptom:** Resources marked as SPOFs but have redundancy

**Solutions:**
1. Check if redundancy relationships are properly set in Neo4j
2. Verify REDUNDANT_WITH relationships exist
3. Update resource discovery to detect redundancy
4. Adjust risk threshold:
   ```bash
   SPOF_HIGH_RISK_THRESHOLD=90.0
   ```

### Performance Issues

**Symptom:** SPOF scans taking too long

**Solutions:**
1. Increase scan interval:
   ```bash
   SPOF_SCAN_INTERVAL=1800  # 30 minutes
   ```

2. Check Neo4j performance and indexes
3. Review number of resources in graph
4. Consider batching for large graphs

## Related Documentation

- [Risk Analysis Guide](ENHANCED_RISK_ANALYSIS.md)
- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Monitoring API](api/MONITORING_API.md)
- [Prometheus Integration](PROMETHEUS_INTEGRATION.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/MattVerwey/TopDeck/issues
- Documentation: https://github.com/MattVerwey/TopDeck/tree/main/docs
