# ML-Based Prediction Usage Guide

## Overview

TopDeck's ML-based prediction system helps you:
- **Predict failures** before they occur
- **Forecast performance** degradation
- **Detect anomalies** in real-time
- **Plan capacity** proactively

This guide shows you how to use these capabilities.

## Quick Start

### 1. Start TopDeck API Server

```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Start the API server
python -m topdeck
```

The prediction API will be available at `http://localhost:8000/api/v1/prediction`

### 2. Check Prediction Service Health

```bash
curl http://localhost:8000/api/v1/prediction/health
```

**Response:**
```json
{
  "status": "healthy",
  "models": {
    "failure_prediction": {
      "status": "active",
      "version": "1.0.0-rule-based",
      "algorithm": "rule-based"
    },
    "performance_prediction": {
      "status": "active",
      "version": "1.0.0-rule-based",
      "algorithm": "rule-based"
    },
    "anomaly_detection": {
      "status": "active",
      "version": "1.0.0-rule-based",
      "algorithm": "rule-based"
    }
  }
}
```

## Use Cases

### Use Case 1: Predict Resource Failure

**Scenario**: You want to know if your production database is at risk of failing.

```bash
curl "http://localhost:8000/api/v1/prediction/resources/sql-db-prod/failure-risk?resource_name=Production%20Database&resource_type=database"
```

**Response:**
```json
{
  "resource_id": "sql-db-prod",
  "resource_name": "Production Database",
  "resource_type": "database",
  "failure_probability": 0.73,
  "time_to_failure_hours": 48,
  "risk_level": "high",
  "confidence": "high",
  "contributing_factors": [
    {
      "factor": "cpu_usage",
      "importance": 0.35,
      "current_value": 0.85,
      "threshold": 0.8,
      "description": "CPU usage is consistently high"
    },
    {
      "factor": "error_rate",
      "importance": 0.30,
      "current_value": 0.06,
      "threshold": 0.05,
      "description": "Error rate is elevated"
    },
    {
      "factor": "memory_trend",
      "importance": 0.25,
      "current_value": 0.08,
      "threshold": 0.1,
      "description": "Memory usage is increasing over time"
    }
  ],
  "recommendations": [
    "Immediate attention required - high failure risk",
    "Scale up CPU allocation or add horizontal scaling",
    "Increase memory allocation or investigate memory leaks",
    "Investigate error spike - check logs and dependencies",
    "Consider read replicas or database optimization"
  ],
  "predicted_at": "2025-10-21T19:30:00Z",
  "model_version": "1.0.0-rule-based"
}
```

**Interpretation:**
- **73% chance of failure** within the next 48 hours
- **High risk level** - immediate action needed
- Main issues: High CPU (85%), elevated errors (6%), increasing memory
- Follow the recommendations to prevent failure

### Use Case 2: Forecast Performance Degradation

**Scenario**: You want to predict if your API gateway will experience latency issues.

```bash
curl "http://localhost:8000/api/v1/prediction/resources/api-gateway/performance?resource_name=API%20Gateway&metric_name=latency_p95&horizon_hours=24"
```

**Response:**
```json
{
  "resource_id": "api-gateway",
  "resource_name": "API Gateway",
  "metric_name": "latency_p95",
  "current_value": 250.0,
  "baseline_value": 200.0,
  "predictions": [
    {
      "timestamp": "2025-10-21T20:00:00Z",
      "predicted_value": 250.0,
      "confidence_lower": 225.0,
      "confidence_upper": 275.0
    },
    {
      "timestamp": "2025-10-21T21:00:00Z",
      "predicted_value": 255.0,
      "confidence_lower": 229.5,
      "confidence_upper": 280.5
    },
    // ... more predictions
  ],
  "degradation_risk": "medium",
  "confidence": "medium",
  "trend": "increasing",
  "seasonality_detected": false,
  "anomalies_detected": 0,
  "recommendations": [
    "Performance degrading - monitor closely",
    "Consider scaling or optimization"
  ],
  "predicted_at": "2025-10-21T19:30:00Z",
  "prediction_horizon_hours": 24,
  "model_version": "1.0.0-rule-based"
}
```

**Interpretation:**
- Current latency (250ms) is **25% above baseline** (200ms)
- **Increasing trend** - latency will continue to rise
- **Medium risk** of degradation
- Take action now before it impacts users

### Use Case 3: Detect Anomalies

**Scenario**: You want to identify unusual behavior in your production web app.

```bash
curl "http://localhost:8000/api/v1/prediction/resources/webapp-prod/anomalies?resource_name=Production%20Web%20App&window_hours=24"
```

**Response:**
```json
{
  "resource_id": "webapp-prod",
  "resource_name": "Production Web App",
  "anomalies": [
    {
      "timestamp": "2025-10-21T15:30:00Z",
      "metric_name": "memory_usage",
      "actual_value": 0.92,
      "expected_value": 0.65,
      "anomaly_score": 0.88,
      "deviation_percentage": 41.5
    }
  ],
  "overall_anomaly_score": 0.88,
  "risk_level": "high",
  "affected_metrics": ["memory_usage"],
  "potential_causes": [
    "Memory leak",
    "Traffic spike",
    "Inefficient code deployment"
  ],
  "similar_historical_incidents": [],
  "correlated_resources": ["cache-redis"],
  "recommendations": [
    "Investigate memory leak",
    "Check recent deployments",
    "Review application logs"
  ],
  "detected_at": "2025-10-21T19:30:00Z",
  "detection_window_hours": 24,
  "model_version": "1.0.0-rule-based"
}
```

**Interpretation:**
- **High anomaly** detected in memory usage (88% score)
- Memory is **41.5% higher than expected** (92% vs 65%)
- Likely causes: Memory leak, traffic spike, or recent deployment
- Follow recommendations to investigate

### Use Case 4: List All Recent Anomalies

**Scenario**: You want to see all anomalies across your infrastructure.

```bash
curl "http://localhost:8000/api/v1/prediction/anomalies?time_range_hours=24&risk_level=high"
```

## API Reference

### Predict Failure Risk

**Endpoint:** `GET /api/v1/prediction/resources/{resource_id}/failure-risk`

**Query Parameters:**
- `resource_name` (optional): Human-readable resource name
- `resource_type` (optional): Type of resource (database, web_app, etc.)

**Response Fields:**
- `failure_probability`: 0.0 to 1.0 (0% to 100%)
- `time_to_failure_hours`: Estimated hours until failure (null if low risk)
- `risk_level`: low, medium, high, critical
- `confidence`: low, medium, high
- `contributing_factors`: List of factors contributing to risk
- `recommendations`: Actions to prevent failure

### Predict Performance

**Endpoint:** `GET /api/v1/prediction/resources/{resource_id}/performance`

**Query Parameters:**
- `resource_name` (optional): Human-readable resource name
- `metric_name` (default: latency_p95): Metric to predict
- `horizon_hours` (default: 24, max: 168): How far ahead to predict

**Supported Metrics:**
- `latency_p95`: 95th percentile latency
- `error_rate`: Error rate
- `throughput`: Request rate
- `response_time`: Average response time

**Response Fields:**
- `predictions`: Time-series forecast with confidence intervals
- `degradation_risk`: low, medium, high, critical
- `trend`: increasing, decreasing, stable
- `seasonality_detected`: Boolean indicating if daily/weekly patterns found

### Detect Anomalies

**Endpoint:** `GET /api/v1/prediction/resources/{resource_id}/anomalies`

**Query Parameters:**
- `resource_name` (optional): Human-readable resource name
- `window_hours` (default: 24, max: 168): Time window to analyze

**Response Fields:**
- `anomalies`: List of detected anomalous points
- `overall_anomaly_score`: 0.0 to 1.0 (higher = more anomalous)
- `risk_level`: low, medium, high, critical
- `affected_metrics`: Which metrics show anomalies
- `potential_causes`: Possible explanations

### List All Anomalies

**Endpoint:** `GET /api/v1/prediction/anomalies`

**Query Parameters:**
- `time_range_hours` (default: 24, max: 168): How far back to scan
- `risk_level` (optional): Filter by risk level

## Integration with Risk Analysis

The prediction system integrates with TopDeck's existing risk analysis:

```bash
# Get comprehensive risk analysis including predictions
curl "http://localhost:8000/api/v1/risk/resources/{resource_id}/comprehensive"

# This will include:
# - Traditional risk scoring
# - ML-based failure prediction
# - Performance forecasts
# - Anomaly detection results
```

## Python SDK Usage

```python
from topdeck.analysis.prediction import Predictor
from topdeck.analysis.prediction.feature_extractor import FeatureExtractor

# Initialize
feature_extractor = FeatureExtractor()
predictor = Predictor(feature_extractor=feature_extractor)

# Predict failure
prediction = await predictor.predict_failure(
    resource_id="sql-db-prod",
    resource_name="Production Database",
    resource_type="database"
)

print(f"Failure probability: {prediction.failure_probability:.2%}")
print(f"Time to failure: {prediction.time_to_failure_hours} hours")
print(f"Risk level: {prediction.risk_level}")

# Predict performance
perf_prediction = await predictor.predict_performance(
    resource_id="api-gateway",
    resource_name="API Gateway",
    metric_name="latency_p95",
    horizon_hours=24
)

print(f"Current latency: {perf_prediction.current_value}ms")
print(f"Baseline: {perf_prediction.baseline_value}ms")
print(f"Trend: {perf_prediction.trend}")

# Detect anomalies
anomaly_detection = await predictor.detect_anomalies(
    resource_id="webapp-prod",
    resource_name="Production Web App",
    window_hours=24
)

print(f"Anomaly score: {anomaly_detection.overall_anomaly_score:.2f}")
print(f"Anomalies found: {len(anomaly_detection.anomalies)}")
```

## Understanding Risk Levels

| Risk Level | Failure Probability | Action Required |
|------------|-------------------|-----------------|
| **Low** | 0-30% | Continue monitoring |
| **Medium** | 30-60% | Plan preventive action |
| **High** | 60-80% | Take action soon |
| **Critical** | 80-100% | **Immediate action required** |

## Understanding Confidence Levels

| Confidence | Meaning | Model State |
|------------|---------|-------------|
| **Low** | <60% | Limited data, use with caution |
| **Medium** | 60-80% | Reasonable confidence |
| **High** | >80% | High confidence, act on prediction |

## Best Practices

### 1. Regular Monitoring

Check predictions regularly, not just when issues occur:

```bash
# Daily health check script
#!/bin/bash

# Check all critical resources
for resource in sql-db-prod api-gateway webapp-prod; do
    curl -s "http://localhost:8000/api/v1/prediction/resources/$resource/failure-risk" | \
        jq '{resource: .resource_id, probability: .failure_probability, risk: .risk_level}'
done
```

### 2. Set Up Alerts

Configure alerts based on predictions:

```python
# Alert if failure probability exceeds threshold
if prediction.failure_probability > 0.7:
    send_alert(
        severity="high",
        message=f"{prediction.resource_name} has {prediction.failure_probability:.0%} failure risk",
        recommendations=prediction.recommendations
    )
```

### 3. Track Prediction Accuracy

Monitor how accurate predictions are over time:

```python
# After an incident
actual_failure_time = datetime.now()
predicted_failure_time = prediction.predicted_at + timedelta(hours=prediction.time_to_failure_hours)

accuracy = abs((actual_failure_time - predicted_failure_time).total_seconds() / 3600)
print(f"Prediction was off by {accuracy} hours")
```

### 4. Combine with Traditional Monitoring

Use predictions alongside traditional monitoring:

```bash
# Check both current state and predictions
echo "Current State:"
curl "http://localhost:8000/api/v1/risk/resources/sql-db-prod"

echo "Predictions:"
curl "http://localhost:8000/api/v1/prediction/resources/sql-db-prod/failure-risk"
```

## Troubleshooting

### No Predictions Available

**Problem**: API returns empty predictions or errors

**Solutions**:
1. Check that Prometheus is collecting metrics
2. Verify resource ID exists in Neo4j
3. Ensure sufficient historical data (at least 24 hours)

```bash
# Check if resource exists
curl "http://localhost:8000/api/v1/topology/resources/{resource_id}"

# Check metrics availability
curl "http://prometheus:9090/api/v1/query?query=up"
```

### Low Confidence Predictions

**Problem**: Predictions have low confidence

**Solutions**:
1. Collect more historical data
2. Ensure all metrics are being collected
3. Check for gaps in time-series data

### Inaccurate Predictions

**Problem**: Predictions don't match reality

**Solutions**:
1. Model may need retraining (coming in future versions)
2. Check if resource characteristics changed
3. Verify feature extraction is working correctly

## Next Steps

1. **Automate monitoring**: Set up scheduled jobs to check predictions
2. **Integrate with alerting**: Send predictions to Slack, PagerDuty, etc.
3. **Build dashboards**: Visualize predictions in Grafana or your dashboard
4. **Track accuracy**: Monitor prediction accuracy over time

## Future Enhancements

Coming soon:
- **Model training**: Train models on your actual historical data
- **Custom models**: Tune models for your specific infrastructure
- **Capacity planning**: Predict when you'll need to scale
- **Cost optimization**: Predict cost impacts of changes
- **Automated remediation**: Automatically apply fixes for predicted issues

## Support

For questions or issues:
- Check [ML Prediction Research](ML_PREDICTION_RESEARCH.md) for technical details
- Open an issue on GitHub
- Review API documentation at `/api/docs`

## Examples

See `examples/prediction_examples.py` for more code examples and use cases.
