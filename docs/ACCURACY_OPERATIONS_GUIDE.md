# Accuracy Tracking Operations Guide

## Overview

This guide covers the operational aspects of the accuracy tracking system, including automated maintenance tasks, monitoring, and alerting.

## Automated Maintenance

The accuracy tracking system includes automated background tasks to maintain data quality and provide continuous monitoring.

### Scheduler Components

The `AccuracyMaintenanceScheduler` handles three automated tasks:

1. **Prediction Validation** (Hourly)
   - Validates pending predictions based on actual outcomes
   - Checks resource health/status
   - Updates accuracy metrics

2. **Confidence Decay** (Daily at 2 AM)
   - Reduces confidence in unconfirmed dependencies
   - Prevents stale data accumulation
   - Maintains dependency graph accuracy

3. **Calibration Analysis** (Weekly on Sunday at 3 AM)
   - Analyzes prediction accuracy trends
   - Generates threshold recommendations
   - Identifies systematic errors

### Starting the Scheduler

```python
from topdeck.analysis.accuracy.scheduler import AccuracyMaintenanceScheduler
from topdeck.storage.neo4j_client import Neo4jClient

# Initialize
neo4j_client = Neo4jClient(uri=..., username=..., password=...)
scheduler = AccuracyMaintenanceScheduler(neo4j_client)

# Start automated tasks
scheduler.start()

# Check status
status = scheduler.get_status()
print(f"Scheduler running: {status['scheduler_running']}")
print(f"Jobs: {status['jobs']}")
```

### Configuration

Customize the scheduler behavior:

```python
scheduler = AccuracyMaintenanceScheduler(
    neo4j_client=neo4j_client,
    validation_interval_hours=2,      # Run validation every 2 hours
    decay_schedule="0 3 * * *",       # 3 AM daily
    calibration_schedule="0 4 * * 0", # 4 AM Sunday
)
```

## Monitoring Endpoints

### Dashboard

Get comprehensive accuracy metrics and status:

```bash
# Get 7-day dashboard
curl http://localhost:8000/api/v1/accuracy/monitoring/dashboard

# Get 30-day dashboard
curl http://localhost:8000/api/v1/accuracy/monitoring/dashboard?days=30
```

**Response:**
```json
{
  "prediction_accuracy": {
    "precision": 0.87,
    "recall": 0.92,
    "f1_score": 0.89,
    "total_predictions": 150
  },
  "dependency_accuracy": {
    "validated_count": 180,
    "stale_count": 5,
    "total_dependencies": 195
  },
  "pending_work": {
    "predictions_to_validate": 12,
    "stale_dependencies": 5
  },
  "time_range": {
    "days": 7,
    "from": "2024-11-17T00:00:00Z",
    "to": "2024-11-24T00:00:00Z"
  }
}
```

### Alerts

Check for accuracy degradation:

```bash
# Check with default thresholds
curl http://localhost:8000/api/v1/accuracy/monitoring/alerts

# Custom thresholds
curl "http://localhost:8000/api/v1/accuracy/monitoring/alerts?precision_threshold=0.90&recall_threshold=0.95"
```

**Response (with alerts):**
```json
{
  "status": "alert",
  "alert_count": 1,
  "alerts": [
    {
      "severity": "warning",
      "metric": "precision",
      "current": 0.82,
      "threshold": 0.85,
      "message": "Precision (82.00%) below threshold (85.00%)"
    }
  ],
  "metrics": {
    "precision": 0.82,
    "recall": 0.91,
    "f1_score": 0.86,
    "accuracy": 0.88
  },
  "thresholds": {
    "precision": 0.85,
    "recall": 0.90,
    "f1_score": 0.85
  }
}
```

### Trends

Monitor accuracy over time:

```bash
# Get accuracy trends
curl http://localhost:8000/api/v1/accuracy/monitoring/trends
```

**Response:**
```json
{
  "weeks_analyzed": 1,
  "trends": [
    {
      "week": 1,
      "start_date": "2024-11-17T00:00:00Z",
      "end_date": "2024-11-24T00:00:00Z",
      "precision": 0.87,
      "recall": 0.92,
      "f1_score": 0.89,
      "prediction_count": 45
    }
  ],
  "note": "Currently showing most recent week only. Full historical trends require database schema extension for weekly aggregation."
}
```

## Manual Maintenance

### Trigger Validation

Manually trigger prediction validation:

```bash
# Validate predictions older than 24 hours
curl -X POST http://localhost:8000/api/v1/accuracy/maintenance/run-validation

# Custom age threshold
curl -X POST "http://localhost:8000/api/v1/accuracy/maintenance/run-validation?max_age_hours=48"
```

**Note:** This endpoint requires integration with monitoring systems to automatically determine actual outcomes. Currently returns pending predictions count.

### Trigger Decay

Manually apply confidence decay:

```bash
# Apply decay with default settings
curl -X POST http://localhost:8000/api/v1/accuracy/maintenance/run-decay

# Custom decay parameters
curl -X POST "http://localhost:8000/api/v1/accuracy/maintenance/run-decay?decay_rate=0.15&days_threshold=5"
```

**Response:**
```json
{
  "status": "success",
  "dependencies_updated": 23,
  "decay_rate": 0.1,
  "days_threshold": 3,
  "timestamp": "2024-11-24T12:00:00Z"
}
```

## Alerting Integration

### Using the Alerts Endpoint

The accuracy tracking system provides a JSON-based alerts endpoint for integration with monitoring systems. Since the endpoint returns JSON (not Prometheus exposition format), you can use it with custom scrapers or the approach below.

**Direct Monitoring:**

Use the `/monitoring/alerts` endpoint for threshold-based alerting:

```bash
# Check current alert status
curl http://localhost:8000/api/v1/accuracy/monitoring/alerts
```

**Custom Prometheus Exporter:**

To expose metrics in Prometheus format, create a custom exporter that reads from the dashboard endpoint:

```python
# prometheus_exporter.py
from prometheus_client import Gauge, start_http_server
import requests
import time

# Define metrics
precision_gauge = Gauge('topdeck_accuracy_precision', 'Prediction precision')
recall_gauge = Gauge('topdeck_accuracy_recall', 'Prediction recall')
f1_gauge = Gauge('topdeck_accuracy_f1_score', 'Prediction F1 score')
stale_deps_gauge = Gauge('topdeck_dependency_stale_count', 'Stale dependencies')

def update_metrics():
    """Fetch metrics from TopDeck and update Prometheus gauges."""
    try:
        resp = requests.get("http://localhost:8000/api/v1/accuracy/monitoring/dashboard")
        data = resp.json()
        
        pred = data.get("prediction_accuracy", {})
        precision_gauge.set(pred.get("precision", 0))
        recall_gauge.set(pred.get("recall", 0))
        f1_gauge.set(pred.get("f1_score", 0))
        
        deps = data.get("dependency_accuracy", {})
        stale_deps_gauge.set(deps.get("stale_count", 0))
    except Exception as e:
        print(f"Failed to update metrics: {e}")

if __name__ == "__main__":
    start_http_server(9090)  # Prometheus scrapes this port
    while True:
        update_metrics()
        time.sleep(60)
```

Then configure Prometheus to scrape the exporter:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'topdeck_accuracy'
    static_configs:
      - targets: ['localhost:9090']  # The exporter port
```

### Alert Rules

Example Prometheus alert rules (requires the custom exporter above):

```yaml
groups:
  - name: accuracy_alerts
    rules:
      - alert: LowPredictionPrecision
        expr: topdeck_accuracy_precision < 0.85
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Prediction precision below threshold"
          description: "Precision is {{ $value | humanizePercentage }}, below 85%"

      - alert: LowPredictionRecall
        expr: topdeck_accuracy_recall < 0.90
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Prediction recall below threshold"
          description: "Recall is {{ $value | humanizePercentage }}, below 90%"

      - alert: HighStaleDependencyCount
        expr: topdeck_dependency_stale_count > 10
        for: 2h
        labels:
          severity: warning
        annotations:
          summary: "High number of stale dependencies"
          description: "{{ $value }} dependencies are stale"
```

### Slack/PagerDuty Integration

Use the alerts endpoint to integrate with notification systems:

```python
import requests
import json

def check_accuracy_alerts():
    """Check accuracy and send alerts if needed."""
    response = requests.get(
        "http://localhost:8000/api/v1/accuracy/monitoring/alerts"
    )
    data = response.json()
    
    if data["status"] == "alert":
        # Send to Slack
        slack_message = {
            "text": f"🚨 Accuracy Alert ({data['alert_count']} issues)",
            "attachments": [
                {
                    "color": "warning",
                    "fields": [
                        {
                            "title": alert["metric"],
                            "value": alert["message"],
                            "short": False
                        }
                        for alert in data["alerts"]
                    ]
                }
            ]
        }
        
        requests.post(
            "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
            json=slack_message
        )

# Run periodically
if __name__ == "__main__":
    import schedule
    import time
    
    schedule.every(1).hour.do(check_accuracy_alerts)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

## Operational Procedures

### Daily Tasks

1. **Morning Check** (Automated via scheduler)
   - Review dashboard metrics
   - Check for new alerts
   - Verify scheduler is running

2. **Confidence Decay** (Automated at 2 AM)
   - Applied automatically
   - Review logs for any issues

### Weekly Tasks

1. **Calibration Review** (Automated Sunday 3 AM)
   - Review calibration report
   - Apply recommended threshold adjustments
   - Monitor systematic errors

2. **Trend Analysis**
   - Review weekly trends
   - Identify accuracy improvements/degradations
   - Adjust alert thresholds if needed

### Monthly Tasks

1. **Comprehensive Review**
   - Analyze 30-day trends
   - Review false positive/negative patterns
   - Update prediction models if needed

2. **Dependency Cleanup**
   - Review stale dependencies
   - Remove very low confidence dependencies
   - Verify critical dependencies

## Troubleshooting

### Scheduler Not Running

Check scheduler status:

```python
status = scheduler.get_status()
if not status["scheduler_running"]:
    scheduler.start()
```

Check logs:
```bash
grep "accuracy maintenance" /var/log/topdeck/app.log
```

### Low Accuracy Metrics

1. **Check Recent Changes**
   - Review calibration report
   - Identify systematic errors
   - Check for data quality issues

2. **Adjust Thresholds**
   - Use calibration recommendations
   - Test new thresholds in staging
   - Monitor impact

3. **Validate Data Sources**
   - Ensure monitoring integrations are working
   - Check dependency discovery accuracy
   - Verify prediction inputs

### High Stale Dependency Rate

1. **Increase Validation Frequency**
   - Run validation more often
   - Enable more verification sources

2. **Adjust Decay Parameters**
   - Increase decay rate
   - Reduce days threshold
   - Clean up very low confidence dependencies

## Best Practices

### Alert Thresholds

- **Precision**: 0.85+ (85% of alerts should be real)
- **Recall**: 0.90+ (catching 90% of issues)
- **F1 Score**: 0.85+ (balanced accuracy)

### Maintenance Schedule

- **Validation**: Every 1-2 hours during business hours
- **Decay**: Daily at low-traffic time (2-3 AM)
- **Calibration**: Weekly for review and adjustments

### Data Retention

- **Predictions**: Keep validated predictions for 90 days
- **Dependencies**: Clean up <0.3 confidence after 14 days
- **Metrics**: Aggregate and archive monthly

## See Also

- [Accuracy Tracking Guide](features/accuracy-tracking/ACCURACY_TRACKING_GUIDE.md)
- [Accuracy Quick Reference](features/accuracy-tracking/ACCURACY_QUICK_REF.md)
- [Calibration Documentation](features/accuracy-tracking/accuracy-system-diagram.md)
