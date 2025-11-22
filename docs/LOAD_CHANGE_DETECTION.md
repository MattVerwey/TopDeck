# Load Change Detection with Prometheus

## Overview

TopDeck's Load Change Detection feature monitors Prometheus metrics to detect when new pods or services are added to your infrastructure, and analyzes the impact on system load. This helps you understand how scaling events affect performance and predict future load based on historical patterns.

## Problem Solved

When you scale your services (e.g., add more pods to handle increased traffic, connect to a new database, or introduce a message queue like Service Bus AMQ), it's crucial to understand:

- **Did the scaling actually help?** Did CPU/memory usage decrease as expected?
- **What was the impact?** How did latency, error rates, and throughput change?
- **Is it safe to scale further?** Based on historical data, what will happen if we add more capacity?
- **Are we approaching capacity limits?** Is the service under high load and needs attention?

Load Change Detection answers these questions by analyzing Prometheus metrics over time.

## Key Features

### 1. Scaling Event Detection
Automatically detects when pods are added or removed by monitoring Kubernetes metrics in Prometheus.

**Metrics monitored:**
- `kube_deployment_status_replicas` - Pod count over time

**Detected events:**
- Scale-up: Pod count increased
- Scale-down: Pod count decreased

### 2. Load Impact Analysis
Compares performance metrics before and after scaling events to quantify the impact.

**Metrics analyzed:**
- **CPU Usage**: Did scaling reduce CPU pressure?
- **Memory Usage**: How did memory consumption change?
- **Request Rate**: Did throughput increase as expected?
- **Latency (P95)**: Did response times improve?
- **Error Rate**: Did errors increase or decrease?

**Impact levels:**
- **Minimal**: <10% change in metrics
- **Moderate**: 10-25% change
- **Significant**: 25-50% change
- **Critical**: >50% change or >20% error rate increase

### 3. Load Prediction
Predicts future performance based on historical scaling patterns.

**Uses historical data to forecast:**
- Expected CPU usage at target pod count
- Predicted memory consumption
- Anticipated request rate
- Expected latency
- Projected error rate

**Confidence scoring:**
- High confidence with 5+ similar historical events
- Medium confidence with 3-4 events
- Low confidence with fewer events

### 4. High Load Pattern Detection
Proactively identifies services under stress.

**Detects:**
- High CPU usage (>80%)
- High memory usage (>80% of limit)
- High latency (P95 >1 second)
- High error rate (>5%)

**Provides:**
- Current baseline metrics
- Recent scaling history
- Actionable recommendations

## API Endpoints

### Get Scaling Events
```bash
GET /api/v1/load/resources/{resource_id}/scaling-events?lookback_hours=24
```

Detects pod/service scaling events from Prometheus metrics.

**Query Parameters:**
- `lookback_hours` (int): Time window to analyze (1-168 hours, default: 24)

**Response:**
```json
{
  "resource_id": "web-api",
  "lookback_hours": 24,
  "events_count": 2,
  "events": [
    {
      "timestamp": "2024-11-22T14:30:00Z",
      "pod_count_before": 3,
      "pod_count_after": 6,
      "scaling_type": "scale_up",
      "pod_count_change": 3
    }
  ]
}
```

### Get Load Baseline
```bash
GET /api/v1/load/resources/{resource_id}/baseline
```

Returns current performance metrics for a service.

**Response:**
```json
{
  "resource_id": "web-api",
  "timestamp": "2024-11-22T15:00:00Z",
  "pod_count": 6,
  "metrics": {
    "cpu_usage": 0.65,
    "memory_usage_bytes": 536870912,
    "request_rate": 150.5,
    "latency_p95_seconds": 0.25,
    "error_rate": 0.02
  }
}
```

### Analyze Scaling Impact
```bash
GET /api/v1/load/resources/{resource_id}/impact-analysis?lookback_hours=24
```

Compares metrics before and after each scaling event.

**Query Parameters:**
- `lookback_hours` (int): Time window to analyze (1-168 hours, default: 24)

**Response:**
```json
{
  "resource_id": "web-api",
  "lookback_hours": 24,
  "events_analyzed": 1,
  "impacts": [
    {
      "event": {
        "timestamp": "2024-11-22T14:30:00Z",
        "pod_count_before": 3,
        "pod_count_after": 6,
        "scaling_type": "scale_up"
      },
      "baseline": {
        "cpu_usage": 0.85,
        "memory_usage_bytes": 805306368,
        "request_rate": 200.0,
        "latency_p95_seconds": 0.45,
        "error_rate": 0.05
      },
      "changes": {
        "cpu_change_pct": -35.0,
        "memory_change_pct": -30.0,
        "request_rate_change_pct": 180.0,
        "latency_change_pct": -44.0,
        "error_rate_change_pct": -60.0
      },
      "overall_impact": "significant",
      "time_to_stabilize_minutes": 15.0,
      "recommendations": [
        "✅ CPU usage decreased significantly after scaling up. Good result.",
        "✅ Latency improved after scaling up. Good result."
      ]
    }
  ]
}
```

### Predict Load
```bash
GET /api/v1/load/resources/{resource_id}/predict-load?target_pod_count=10&lookback_days=30
```

Predicts performance at a target pod count based on historical patterns.

**Query Parameters:**
- `target_pod_count` (int, required): Desired number of pods
- `lookback_days` (int): Days of history to analyze (1-90, default: 30)

**Response:**
```json
{
  "resource_id": "web-api",
  "target_pod_count": 10,
  "predicted_metrics": {
    "cpu_usage": 0.45,
    "memory_usage_bytes": 429496729,
    "request_rate": 300.0,
    "latency_p95_seconds": 0.18,
    "error_rate": 0.008
  },
  "confidence": 0.85,
  "based_on_events": [
    {
      "timestamp": "2024-11-15T10:00:00Z",
      "pod_count_before": 4,
      "pod_count_after": 8,
      "scaling_type": "scale_up"
    }
  ],
  "recommendations": [
    "✅ Predicted metrics look healthy. This scaling change should be safe."
  ]
}
```

### Detect High Load Patterns
```bash
GET /api/v1/load/resources/{resource_id}/high-load-patterns?lookback_hours=24
```

Identifies services under stress that may need scaling.

**Query Parameters:**
- `lookback_hours` (int): Time window to analyze (1-168 hours, default: 24)

**Response:**
```json
{
  "resource_id": "web-api",
  "current_baseline": {
    "timestamp": "2024-11-22T15:00:00Z",
    "pod_count": 3,
    "cpu_usage": 0.92,
    "memory_usage_bytes": 858993459,
    "request_rate": 250.0,
    "latency_p95_seconds": 0.85,
    "error_rate": 0.06
  },
  "scaling_events_count": 0,
  "recent_scaling_events": [],
  "high_load_indicators": {
    "high_cpu": true,
    "high_memory": false,
    "high_latency": false,
    "high_errors": true
  },
  "needs_scaling": true,
  "insights": [
    "CPU usage is high (92.0%). Consider scaling up or optimizing CPU-intensive operations.",
    "Error rate is high (6.0%). This may indicate system instability or capacity limits."
  ]
}
```

## Use Cases

### Use Case 1: Validate Scaling Effectiveness

**Scenario:** You scaled your API from 3 to 6 pods to handle increased traffic.

**Steps:**
1. Get scaling events to confirm the change was detected:
   ```bash
   curl http://localhost:8000/api/v1/load/resources/api-service/scaling-events?lookback_hours=6
   ```

2. Analyze the impact:
   ```bash
   curl http://localhost:8000/api/v1/load/resources/api-service/impact-analysis?lookback_hours=6
   ```

3. **Evaluate results:**
   - CPU decreased by 35% ✅ Good!
   - Latency decreased by 44% ✅ Excellent!
   - Error rate decreased by 60% ✅ Perfect!
   - **Conclusion:** Scaling was effective, system is healthier

### Use Case 2: Plan Future Scaling

**Scenario:** Your database is getting slow. Should you scale to 8 pods?

**Steps:**
1. Get current baseline:
   ```bash
   curl http://localhost:8000/api/v1/load/resources/postgres-db/baseline
   ```
   Current: 4 pods, CPU 75%, latency 450ms

2. Predict impact of scaling to 8:
   ```bash
   curl "http://localhost:8000/api/v1/load/resources/postgres-db/predict-load?target_pod_count=8"
   ```

3. **Review prediction:**
   - Predicted CPU: 45% ✅
   - Predicted latency: 250ms ✅
   - Confidence: 0.85 (high) ✅
   - **Recommendation:** "Predicted metrics look healthy. This scaling change should be safe."

4. **Decision:** Safe to scale to 8 pods

### Use Case 3: Proactive Monitoring

**Scenario:** Regular monitoring to catch services under stress.

**Steps:**
1. Check for high load patterns across services:
   ```bash
   for service in api-gateway web-frontend order-service; do
     curl "http://localhost:8000/api/v1/load/resources/$service/high-load-patterns"
   done
   ```

2. **Results:**
   - `api-gateway`: needs_scaling=false ✅
   - `web-frontend`: needs_scaling=false ✅
   - `order-service`: needs_scaling=true ⚠️
     - High CPU: 88%
     - High latency: 1.2 seconds
     - **Action:** Scale order-service immediately

### Use Case 4: Post-Incident Analysis

**Scenario:** Error spike occurred at 2pm. Was it related to scaling?

**Steps:**
1. Check scaling events around that time:
   ```bash
   curl "http://localhost:8000/api/v1/load/resources/payment-api/scaling-events?lookback_hours=12"
   ```

2. Found: Scale-up from 2 to 5 pods at 1:55pm

3. Analyze impact:
   ```bash
   curl "http://localhost:8000/api/v1/load/resources/payment-api/impact-analysis?lookback_hours=12"
   ```

4. **Findings:**
   - Error rate increased by 40% after scaling ❌
   - CPU actually increased by 15% ❌
   - **Root cause:** Scaling exposed a database connection pool issue
   - **Action:** Fix connection pool configuration

## Prometheus Metrics Required

For optimal functionality, your services should expose these metrics to Prometheus:

### Kubernetes Metrics
- `kube_deployment_status_replicas{deployment="..."}` - Pod count
- `kube_pod_container_resource_requests_cpu_cores` - CPU requests
- `kube_pod_container_resource_requests_memory_bytes` - Memory requests

### Application Metrics
- `container_cpu_usage_seconds_total` - CPU usage
- `container_memory_usage_bytes` - Memory usage
- `http_requests_total` - Request count
- `http_request_duration_seconds_bucket` - Latency histogram
- `http_requests_total{status=~"5.."}` - Error count

### Service-Specific Metrics
For databases:
- `database_query_duration_seconds_bucket` - Query latency
- `database_connections` - Active connections
- `database_deadlocks_total` - Deadlock count

For message queues:
- `rabbitmq_queue_messages` - Queue depth
- `kafka_consumer_lag` - Consumer lag

## Configuration

The load detector uses environment variables for Prometheus connection:

```bash
# .env file
PROMETHEUS_URL=http://prometheus:9090
PROMETHEUS_TIMEOUT=30
```

In production, update `src/topdeck/api/routes/load_detection.py` to use proper dependency injection:

```python
from topdeck.common.config import settings

prometheus_collector = PrometheusCollector(settings.prometheus_url)
```

## Limitations

1. **Requires Historical Data**: Predictions are only as good as historical patterns. New services have low prediction confidence.

2. **Prometheus Metric Availability**: Relies on Prometheus metrics being available. Missing metrics will reduce accuracy.

3. **Correlation vs Causation**: Detects correlation between scaling and load changes, but can't always prove causation.

4. **Time Lag**: Stabilization time varies by service. Default analysis waits 10 minutes after scaling.

## Best Practices

### 1. Regular Baseline Checks
Monitor baselines daily to understand normal patterns:
```bash
# Cron job
0 */6 * * * curl http://topdeck/api/v1/load/resources/critical-service/baseline >> /var/log/baselines.log
```

### 2. Scaling Window Analysis
Always analyze impact 15-30 minutes after scaling:
```bash
# After scaling
sleep 1800  # Wait 30 minutes
curl http://topdeck/api/v1/load/resources/my-service/impact-analysis?lookback_hours=1
```

### 3. Prediction Before Changes
Always predict before scaling in production:
```bash
# Before scaling to N pods
curl "http://topdeck/api/v1/load/resources/prod-api/predict-load?target_pod_count=N"
# Review predictions and recommendations before proceeding
```

### 4. Alert on High Load
Set up alerts based on high load patterns:
```python
# Integration example
response = requests.get(f"{topdeck_url}/api/v1/load/resources/{service}/high-load-patterns")
if response.json()["needs_scaling"]:
    send_alert(f"Service {service} needs scaling", response.json()["insights"])
```

## Integration with CI/CD

Integrate load detection into deployment pipelines:

```yaml
# GitHub Actions example
- name: Check load before deployment
  run: |
    # Get prediction for post-deployment state
    PREDICTION=$(curl -s "http://topdeck/api/v1/load/resources/$SERVICE/predict-load?target_pod_count=$NEW_COUNT")
    
    # Extract confidence
    CONFIDENCE=$(echo $PREDICTION | jq -r '.confidence')
    
    # Fail if low confidence or poor predictions
    if (( $(echo "$CONFIDENCE < 0.5" | bc -l) )); then
      echo "Low confidence prediction. Manual review required."
      exit 1
    fi

- name: Analyze scaling impact post-deployment
  run: |
    # Wait for stabilization
    sleep 900  # 15 minutes
    
    # Get impact analysis
    curl "http://topdeck/api/v1/load/resources/$SERVICE/impact-analysis?lookback_hours=1"
```

## Troubleshooting

### No Scaling Events Detected
**Symptom:** `events_count: 0`

**Causes:**
1. Prometheus metric not available
2. Resource ID doesn't match metric labels
3. No actual scaling occurred

**Solution:**
```bash
# Check Prometheus directly
curl 'http://prometheus:9090/api/v1/query?query=kube_deployment_status_replicas{deployment=~".*my-service.*"}'
```

### Predictions Have Low Confidence
**Symptom:** `confidence < 0.5`

**Causes:**
1. Not enough historical data
2. Irregular scaling patterns
3. Short lookback window

**Solution:**
```bash
# Increase lookback period
curl "http://topdeck/api/v1/load/resources/my-service/predict-load?target_pod_count=5&lookback_days=60"
```

### Unexpected Impact Results
**Symptom:** Metrics changed opposite of expected

**Causes:**
1. External factors (database slowdown, network issues)
2. Configuration changes concurrent with scaling
3. Time of day effects (peak hours)

**Solution:** Review timeline and correlate with other events:
```bash
# Check error replay for concurrent issues
curl "http://topdeck/error-replay/by-resource/my-service"
```

## Future Enhancements

Planned improvements:
- [ ] Machine learning models for better predictions
- [ ] Multi-dimensional analysis (time of day, day of week)
- [ ] Cost impact analysis (resource usage × cost)
- [ ] Automated scaling recommendations
- [ ] Integration with Kubernetes HPA
- [ ] Custom metric support beyond standard Prometheus metrics

## Related Documentation

- [Prometheus Collector](../src/topdeck/monitoring/collectors/prometheus.py)
- [ML Prediction Guide](ML_PREDICTION_GUIDE.md)
- [Enhanced Risk Analysis](ENHANCED_RISK_ANALYSIS.md)
- [Monitoring Integration](../README.md#monitoring-integration)
