# Accuracy Tracking and Validation Guide

## Overview

TopDeck includes a comprehensive accuracy tracking system that monitors and improves the accuracy of:

1. **Prediction Accuracy**: How accurate are failure predictions and performance forecasts?
2. **Dependency Detection Accuracy**: How accurate is dependency discovery?

This guide explains how to use the accuracy tracking features to understand and improve TopDeck's predictions.

## Why Track Accuracy?

### The Problem

Without accuracy tracking:
- ❌ You don't know if predictions are reliable
- ❌ False positives cause alert fatigue
- ❌ False negatives miss real issues
- ❌ No way to improve over time
- ❌ Can't tune confidence thresholds

### The Solution

With accuracy tracking:
- ✅ Know your prediction reliability (precision, recall, F1)
- ✅ Validate dependencies with multiple evidence sources
- ✅ Automatic confidence decay for stale data
- ✅ Historical tracking shows improvement trends
- ✅ Data-driven threshold tuning

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Accuracy Tracking System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐    ┌──────────────────────┐       │
│  │  Prediction Tracker  │    │ Dependency Validator │       │
│  │                      │    │                      │       │
│  │  • Record predictions│    │  • Cross-validate    │       │
│  │  • Validate outcomes │    │  • Check staleness   │       │
│  │  • Calculate metrics │    │  • Apply decay       │       │
│  └──────────────────────┘    └──────────────────────┘       │
│            │                           │                     │
│            └───────────┬───────────────┘                     │
│                        ▼                                     │
│            ┌─────────────────────┐                          │
│            │   Neo4j Storage     │                          │
│            │                     │                          │
│            │  • Predictions      │                          │
│            │  • Validations      │                          │
│            │  • Metrics          │                          │
│            └─────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Prediction Accuracy Tracking

### Recording Predictions

When making a prediction, record it for later validation:

```bash
# Record a failure prediction
curl -X POST http://localhost:8000/api/v1/accuracy/predictions/record \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "prod-database-01",
    "failure_probability": 0.85,
    "time_to_failure_hours": 24,
    "confidence": "high",
    "metadata": {
      "model_version": "1.0",
      "features_used": 27
    }
  }'

# Response:
{
  "prediction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "recorded"
}
```

### Validating Predictions

When the outcome is known, validate the prediction:

```bash
# Validate that a predicted failure actually occurred
curl -X POST http://localhost:8000/api/v1/accuracy/predictions/550e8400-e29b-41d4-a716-446655440000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "actual_outcome": "failed",
    "notes": "Database CPU hit 100% and became unresponsive"
  }'

# Response:
{
  "prediction_id": "550e8400-e29b-41d4-a716-446655440000",
  "resource_id": "prod-database-01",
  "outcome_type": "true_positive",
  "actual_outcome": "failed",
  "validated_at": "2024-11-15T14:30:00Z"
}
```

**Outcome Types:**
- `true_positive`: Predicted failure, actually failed ✅
- `true_negative`: Predicted no failure, didn't fail ✅
- `false_positive`: Predicted failure, didn't fail ❌
- `false_negative`: Predicted no failure, but failed ❌

### Getting Accuracy Metrics

```bash
# Get accuracy metrics for last 30 days
curl http://localhost:8000/api/v1/accuracy/predictions/metrics?days=30

# Response:
{
  "metrics": {
    "precision": 0.87,      # 87% of predicted failures were real
    "recall": 0.92,         # 92% of actual failures were predicted
    "f1_score": 0.89,       # Harmonic mean of precision and recall
    "accuracy": 0.88,       # Overall correctness
    "true_positives": 23,
    "true_negatives": 45,
    "false_positives": 3,
    "false_negatives": 2,
    "total_predictions": 73
  },
  "validated_count": 73,
  "pending_count": 12,
  "time_range": {
    "start": "2024-10-15T00:00:00Z",
    "end": "2024-11-15T00:00:00Z"
  }
}
```

### Pending Predictions

See which predictions need validation:

```bash
# Get predictions made in last 72 hours awaiting validation
curl http://localhost:8000/api/v1/accuracy/predictions/pending?max_age_hours=72

# Response:
{
  "pending_count": 12,
  "predictions": [
    {
      "prediction_id": "...",
      "resource_id": "prod-api-gateway",
      "failure_probability": 0.75,
      "predicted_at": "2024-11-14T08:00:00Z",
      "time_to_failure_hours": 24
    }
  ]
}
```

## Dependency Detection Accuracy

### Cross-Validation

Validate a dependency using multiple evidence sources:

```bash
# Check if dependency is validated by multiple sources
curl -X POST "http://localhost:8000/api/v1/accuracy/dependencies/validate?source_id=api-gateway&target_id=database"

# Response:
{
  "source_id": "api-gateway",
  "target_id": "database",
  "detected_confidence": 0.92,
  "evidence_sources": [
    "connection_string",
    "loki_logs",
    "prometheus_metrics"
  ],
  "validation_status": "validated",
  "is_correct": true,
  "validation_method": "cross_validation"
}
```

**Validation Status:**
- `validated`: Multiple evidence sources confirm (high confidence)
- `pending`: Single source, needs more evidence
- `expired`: Not seen recently, may be stale

### Stale Dependencies

Find dependencies that haven't been confirmed recently:

```bash
# Get dependencies not seen in 7 days
curl "http://localhost:8000/api/v1/accuracy/dependencies/stale?max_age_days=7"

# Response:
{
  "stale_count": 5,
  "dependencies": [
    {
      "source_id": "old-service",
      "target_id": "deprecated-cache",
      "confidence": 0.45,
      "evidence_sources": ["logs"],
      "notes": "Not seen since 2024-11-01T00:00:00Z"
    }
  ]
}
```

### Confidence Decay

Apply time-based confidence decay to unconfirmed dependencies:

```bash
# Reduce confidence for dependencies not seen in 3+ days
curl -X POST "http://localhost:8000/api/v1/accuracy/dependencies/decay?decay_rate=0.1&days_threshold=3"

# Response:
{
  "updated_count": 8,
  "decay_rate": 0.1,
  "days_threshold": 3
}
```

**How It Works:**
- Dependencies not seen in `days_threshold` days have confidence reduced
- Confidence multiplied by `(1 - decay_rate)`
- Example: 0.8 confidence with 0.1 decay → 0.72 confidence
- Repeated decay eventually marks low-confidence dependencies for removal

### Dependency Accuracy Metrics

```bash
# Get dependency detection accuracy for last 30 days
curl "http://localhost:8000/api/v1/accuracy/dependencies/metrics?days=30"

# Response:
{
  "metrics": {
    "precision": 0.94,      # 94% of detected dependencies are valid
    "recall": 0.0,          # Hard to measure (unknown dependencies)
    "f1_score": 0.0,
    "accuracy": 0.94,
    "true_positives": 142,  # Validated dependencies (2+ sources)
    "false_positives": 9,   # Stale dependencies
    "total_predictions": 151
  },
  "validated_count": 142,
  "pending_count": 34,
  "time_range": {
    "start": "2024-10-15T00:00:00Z",
    "end": "2024-11-15T00:00:00Z"
  },
  "details": {
    "stale_count": 9,
    "total_dependencies": 185
  }
}
```

## Integration Examples

### Python Client

```python
import requests

class TopDeckAccuracy:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def record_prediction(self, resource_id, failure_probability, confidence):
        """Record a prediction."""
        response = requests.post(
            f"{self.base_url}/api/v1/accuracy/predictions/record",
            json={
                "resource_id": resource_id,
                "failure_probability": failure_probability,
                "confidence": confidence
            }
        )
        return response.json()["prediction_id"]
    
    def validate_prediction(self, prediction_id, actual_outcome):
        """Validate a prediction."""
        response = requests.post(
            f"{self.base_url}/api/v1/accuracy/predictions/{prediction_id}/validate",
            json={"actual_outcome": actual_outcome}
        )
        return response.json()
    
    def get_accuracy_metrics(self, days=30):
        """Get accuracy metrics."""
        response = requests.get(
            f"{self.base_url}/api/v1/accuracy/predictions/metrics",
            params={"days": days}
        )
        return response.json()

# Usage
client = TopDeckAccuracy()

# 1. Make and record prediction
pred_id = client.record_prediction(
    resource_id="prod-db",
    failure_probability=0.85,
    confidence="high"
)

# 2. Later, validate outcome
client.validate_prediction(pred_id, "failed")

# 3. Check accuracy
metrics = client.get_accuracy_metrics(days=30)
print(f"Precision: {metrics['metrics']['precision']:.2%}")
print(f"Recall: {metrics['metrics']['recall']:.2%}")
```

### Automated Validation

```python
import asyncio
from datetime import datetime, timedelta

async def auto_validate_predictions():
    """Automatically validate predictions based on monitoring data."""
    client = TopDeckAccuracy()
    
    # Get pending predictions
    pending = requests.get(
        f"{client.base_url}/api/v1/accuracy/predictions/pending"
    ).json()
    
    for pred in pending["predictions"]:
        # Check if enough time has passed
        predicted_at = datetime.fromisoformat(pred["predicted_at"])
        time_to_validate = predicted_at + timedelta(
            hours=pred.get("time_to_failure_hours", 24)
        )
        
        if datetime.now() >= time_to_validate:
            # Check actual resource status
            actual_failed = check_resource_status(pred["resource_id"])
            
            outcome = "failed" if actual_failed else "no_failure"
            client.validate_prediction(pred["prediction_id"], outcome)
            
            print(f"Validated {pred['prediction_id']}: {outcome}")

# Run daily
asyncio.run(auto_validate_predictions())
```

## Best Practices

### 1. Always Record Predictions

```python
# ✅ Good: Record prediction for tracking
prediction = await predictor.predict_failure(resource_id, resource_name, resource_type)
prediction_id = await tracker.record_prediction(
    resource_id=resource_id,
    failure_probability=prediction.failure_probability,
    time_to_failure_hours=prediction.time_to_failure_hours,
    confidence=prediction.confidence.value
)

# ❌ Bad: Make prediction without tracking
prediction = await predictor.predict_failure(resource_id, resource_name, resource_type)
# No record for validation!
```

### 2. Validate Promptly

```python
# ✅ Good: Set up automated validation
async def check_predictions():
    # Check every hour
    while True:
        await validate_due_predictions()
        await asyncio.sleep(3600)

# ❌ Bad: Manual validation only
# Predictions pile up without validation
```

### 3. Monitor Accuracy Trends

```python
# ✅ Good: Track accuracy over time
metrics_30d = client.get_accuracy_metrics(days=30)
metrics_7d = client.get_accuracy_metrics(days=7)

if metrics_7d["metrics"]["precision"] < metrics_30d["metrics"]["precision"]:
    alert("Prediction accuracy declining!")

# ❌ Bad: Ignore accuracy metrics
# Don't know if predictions are getting better or worse
```

### 4. Use Confidence Appropriately

```python
# ✅ Good: Act based on accuracy and confidence
metrics = client.get_accuracy_metrics()

if metrics["metrics"]["precision"] > 0.9:
    # High accuracy: can auto-act on high confidence predictions
    if prediction.confidence == "high" and prediction.failure_probability > 0.7:
        await auto_scale_resource(resource_id)
else:
    # Lower accuracy: require manual review
    await alert_ops_team(prediction)

# ❌ Bad: Ignore accuracy when making decisions
if prediction.failure_probability > 0.7:
    # Auto-act without checking if predictions are accurate!
    await auto_scale_resource(resource_id)
```

### 5. Clean Up Stale Dependencies

```python
# ✅ Good: Regular maintenance
# Run daily
await validator.apply_confidence_decay(decay_rate=0.1, days_threshold=3)

stale = await validator.validate_stale_dependencies(max_age_days=7)
for dep in stale:
    if dep.detected_confidence < 0.3:
        await remove_dependency(dep.source_id, dep.target_id)

# ❌ Bad: Never clean up
# Stale dependencies accumulate, reducing accuracy
```

## Metrics Interpretation

### Precision vs Recall

**Precision** = What % of alerts are real?
- High precision (>0.9): Few false alarms, safe to auto-act
- Low precision (<0.6): Many false alarms, needs tuning

**Recall** = What % of real issues are caught?
- High recall (>0.9): Catching most issues
- Low recall (<0.6): Missing issues, increase sensitivity

**F1 Score** = Balance of precision and recall
- >0.8: Good balance
- 0.6-0.8: Acceptable, room for improvement
- <0.6: Needs significant tuning

### Example Scenarios

**Scenario 1: High Precision, Low Recall**
```json
{
  "precision": 0.95,  // 95% of alerts are real
  "recall": 0.60      // Only catching 60% of issues
}
```
**Action**: Increase sensitivity, lower thresholds

**Scenario 2: Low Precision, High Recall**
```json
{
  "precision": 0.55,  // Too many false alarms
  "recall": 0.95      // Catching almost everything
}
```
**Action**: Reduce sensitivity, raise thresholds

**Scenario 3: Good Balance**
```json
{
  "precision": 0.88,
  "recall": 0.92,
  "f1_score": 0.90
}
```
**Action**: Monitor and maintain

## Troubleshooting

### Low Prediction Accuracy

**Symptoms:**
- Precision < 0.7
- Many false positives

**Solutions:**
1. Check feature quality: `GET /api/v1/prediction/resources/{id}/failure-risk`
2. Verify monitoring data is current
3. Increase confidence threshold
4. Retrain models with more recent data

### Low Dependency Detection Accuracy

**Symptoms:**
- Many stale dependencies
- Low confidence scores

**Solutions:**
1. Verify monitoring platforms are connected (Loki, Prometheus)
2. Check log retention (need recent data)
3. Apply confidence decay regularly
4. Increase evidence source requirements

### Missing Validations

**Symptoms:**
- High pending_count
- Old predictions not validated

**Solutions:**
1. Set up automated validation job
2. Integrate with monitoring alerts
3. Check validation time windows

## Summary

✅ **Record all predictions** for accuracy tracking  
✅ **Validate outcomes** promptly and automatically  
✅ **Monitor metrics** to understand reliability  
✅ **Apply confidence decay** to keep dependencies current  
✅ **Use accuracy data** to tune thresholds and improve models  

The accuracy tracking system provides the feedback loop needed to continuously improve TopDeck's predictions and dependency detection.
