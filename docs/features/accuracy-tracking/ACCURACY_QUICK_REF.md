# Accuracy Tracking Quick Reference

## Quick Start

### Record a Prediction
```bash
curl -X POST http://localhost:8000/api/v1/accuracy/predictions/record \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "prod-db",
    "failure_probability": 0.85,
    "confidence": "high"
  }'
```

### Validate Outcome
```bash
curl -X POST http://localhost:8000/api/v1/accuracy/predictions/PRED_ID/validate \
  -H "Content-Type: application/json" \
  -d '{"actual_outcome": "failed"}'
```

### Get Accuracy Metrics
```bash
# Last 30 days
curl http://localhost:8000/api/v1/accuracy/predictions/metrics?days=30
```

## Common Tasks

### Check Prediction Accuracy
```bash
# Get precision, recall, F1
curl http://localhost:8000/api/v1/accuracy/predictions/metrics

# Response:
{
  "metrics": {
    "precision": 0.87,  // 87% of alerts are real
    "recall": 0.92,     // Catching 92% of issues
    "f1_score": 0.89    // Balanced metric
  }
}
```

### Find Stale Dependencies
```bash
# Dependencies not seen in 7 days
curl http://localhost:8000/api/v1/accuracy/dependencies/stale?max_age_days=7
```

### Apply Confidence Decay
```bash
# Reduce confidence for old dependencies
curl -X POST http://localhost:8000/api/v1/accuracy/dependencies/decay?decay_rate=0.1&days_threshold=3
```

### Calibrate Thresholds
```bash
# Get recommended threshold adjustments
curl http://localhost:8000/api/v1/accuracy/calibration/thresholds?target_precision=0.85
```

### Get Improvement Report
```bash
# Comprehensive analysis with recommendations
curl http://localhost:8000/api/v1/accuracy/calibration/report
```

## Python Client

```python
import requests

class AccuracyClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base = f"{base_url}/api/v1/accuracy"
    
    def record_prediction(self, resource_id, failure_prob, confidence):
        """Record a prediction."""
        r = requests.post(f"{self.base}/predictions/record", json={
            "resource_id": resource_id,
            "failure_probability": failure_prob,
            "confidence": confidence
        })
        return r.json()["prediction_id"]
    
    def validate_prediction(self, pred_id, outcome):
        """Validate a prediction."""
        r = requests.post(
            f"{self.base}/predictions/{pred_id}/validate",
            json={"actual_outcome": outcome}
        )
        return r.json()
    
    def get_metrics(self, days=30):
        """Get accuracy metrics."""
        r = requests.get(f"{self.base}/predictions/metrics", 
                        params={"days": days})
        return r.json()
    
    def get_improvement_report(self):
        """Get comprehensive improvement report."""
        r = requests.get(f"{self.base}/calibration/report")
        return r.json()

# Usage
client = AccuracyClient()

# 1. Record prediction
pred_id = client.record_prediction("db-1", 0.85, "high")

# 2. Validate later
client.validate_prediction(pred_id, "failed")

# 3. Check metrics
metrics = client.get_metrics()
print(f"Precision: {metrics['metrics']['precision']:.2%}")
```

## Metrics Interpretation

### Precision
**What it means:** What % of your alerts are real?
- **0.9+**: Excellent - very few false alarms
- **0.8-0.9**: Good - some false alarms
- **<0.8**: Needs improvement - too many false alarms

### Recall
**What it means:** What % of real issues do you catch?
- **0.9+**: Excellent - catching almost everything
- **0.8-0.9**: Good - missing some issues
- **<0.8**: Needs improvement - missing too many

### F1 Score
**What it means:** Balanced accuracy metric
- **0.85+**: Excellent
- **0.7-0.85**: Good
- **<0.7**: Needs improvement

## Common Scenarios

### Scenario 1: Too Many False Alarms
**Symptoms:**
- Precision < 0.8
- Alert fatigue

**Actions:**
```bash
# 1. Check current metrics
curl http://localhost:8000/api/v1/accuracy/predictions/metrics

# 2. Get recommended threshold
curl http://localhost:8000/api/v1/accuracy/calibration/thresholds

# 3. Analyze systematic errors
curl http://localhost:8000/api/v1/accuracy/calibration/systematic-errors
```

### Scenario 2: Missing Issues
**Symptoms:**
- Recall < 0.8
- Failures not predicted

**Actions:**
```bash
# 1. Check metrics
curl http://localhost:8000/api/v1/accuracy/predictions/metrics

# 2. Get improvement report
curl http://localhost:8000/api/v1/accuracy/calibration/report

# Look for "decrease threshold" recommendation
```

### Scenario 3: Stale Dependencies
**Symptoms:**
- Old dependencies still showing
- Inaccurate topology

**Actions:**
```bash
# 1. Find stale dependencies
curl http://localhost:8000/api/v1/accuracy/dependencies/stale?max_age_days=7

# 2. Apply confidence decay
curl -X POST http://localhost:8000/api/v1/accuracy/dependencies/decay

# 3. Check metrics
curl http://localhost:8000/api/v1/accuracy/dependencies/metrics
```

## Automated Workflows

### Daily Validation Job
```python
import asyncio
from datetime import datetime, timedelta

async def daily_validation():
    """Run daily to validate predictions."""
    client = AccuracyClient()
    
    # Get pending predictions
    r = requests.get(f"{client.base}/predictions/pending")
    pending = r.json()["predictions"]
    
    for pred in pending:
        # Check if enough time has passed
        pred_time = datetime.fromisoformat(pred["predicted_at"])
        if datetime.now() - pred_time >= timedelta(hours=24):
            # Check actual resource status
            actual_failed = await check_resource(pred["resource_id"])
            outcome = "failed" if actual_failed else "no_failure"
            
            # Validate
            client.validate_prediction(pred["id"], outcome)

# Run daily
asyncio.run(daily_validation())
```

### Weekly Calibration
```python
def weekly_calibration():
    """Run weekly to tune thresholds."""
    client = AccuracyClient()
    
    # Get improvement report
    report = client.get_improvement_report()
    
    # Log current metrics
    print(f"Precision: {report['current_metrics']['precision']:.2%}")
    print(f"Recall: {report['current_metrics']['recall']:.2%}")
    
    # Check for priority actions
    for action in report["priority_actions"]:
        if action["priority"] == "high":
            print(f"⚠️  {action['action']}: {action['details']}")
    
    # Alert if accuracy is declining
    if report['current_metrics']['precision'] < 0.8:
        send_alert("Prediction accuracy declining!")

# Run weekly
weekly_calibration()
```

### Hourly Dependency Maintenance
```python
def hourly_maintenance():
    """Run hourly to maintain dependencies."""
    base = "http://localhost:8000/api/v1/accuracy"
    
    # Apply confidence decay
    r = requests.post(
        f"{base}/dependencies/decay",
        params={"decay_rate": 0.05, "days_threshold": 1}
    )
    print(f"Updated {r.json()['updated_count']} dependencies")
    
    # Check for very stale dependencies
    r = requests.get(f"{base}/dependencies/stale", 
                    params={"max_age_days": 14})
    stale = r.json()["dependencies"]
    
    # Remove low-confidence stale dependencies
    for dep in stale:
        if dep["confidence"] < 0.3:
            # Remove from Neo4j
            remove_dependency(dep["source_id"], dep["target_id"])

# Run hourly
hourly_maintenance()
```

## Troubleshooting

### No Metrics Available
**Problem:** `/predictions/metrics` returns empty
**Solution:** Record predictions first, then validate them

### Low Precision
**Problem:** Too many false positives
**Solution:** 
1. Get threshold recommendation
2. Increase failure_probability threshold
3. Review high-FP resource types

### Low Recall
**Problem:** Missing real failures
**Solution:**
1. Get threshold recommendation
2. Decrease failure_probability threshold
3. Add more sensitive features

### Confidence Not Calibrated
**Problem:** High confidence predictions not more accurate
**Solution:**
1. Check `/calibration/confidence`
2. Review confidence calculation factors
3. Adjust confidence weights

## Best Practices

1. **Always Record Predictions**
   - Record every prediction for tracking
   - Include metadata for analysis

2. **Automate Validation**
   - Set up daily validation job
   - Use monitoring data for validation

3. **Monitor Trends**
   - Weekly accuracy review
   - Alert on degradation

4. **Regular Calibration**
   - Monthly threshold tuning
   - Quarterly model retraining

5. **Maintain Dependencies**
   - Daily confidence decay
   - Weekly cleanup of stale deps

## API Endpoints Summary

### Predictions
- `POST /predictions/record` - Record prediction
- `POST /predictions/{id}/validate` - Validate outcome
- `GET /predictions/metrics` - Get accuracy metrics
- `GET /predictions/pending` - Get pending validations

### Dependencies
- `POST /dependencies/validate` - Cross-validate
- `GET /dependencies/stale` - Find stale deps
- `POST /dependencies/decay` - Apply decay
- `GET /dependencies/metrics` - Get metrics

### Calibration
- `GET /calibration/thresholds` - Threshold recommendations
- `GET /calibration/systematic-errors` - Error analysis
- `GET /calibration/confidence` - Confidence calibration
- `GET /calibration/report` - Full improvement report

### Health
- `GET /health` - Service health check

## Next Steps

1. ✅ Start recording predictions
2. ✅ Set up automated validation
3. ✅ Monitor initial metrics
4. ⏭️ Tune based on calibration
5. ⏭️ Continuous improvement

For detailed documentation, see [ACCURACY_TRACKING_GUIDE.md](ACCURACY_TRACKING_GUIDE.md)
