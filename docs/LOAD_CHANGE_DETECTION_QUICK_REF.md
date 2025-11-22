# Load Change Detection - Quick Reference

## Quick Start

### Check if service was recently scaled
```bash
curl "http://localhost:8000/api/v1/load/resources/{service-id}/scaling-events?lookback_hours=24"
```

### Get current performance baseline
```bash
curl "http://localhost:8000/api/v1/load/resources/{service-id}/baseline"
```

### Analyze scaling impact
```bash
curl "http://localhost:8000/api/v1/load/resources/{service-id}/impact-analysis?lookback_hours=24"
```

### Predict load at target pod count
```bash
curl "http://localhost:8000/api/v1/load/resources/{service-id}/predict-load?target_pod_count=8&lookback_days=30"
```

### Check for high load issues
```bash
curl "http://localhost:8000/api/v1/load/resources/{service-id}/high-load-patterns?lookback_hours=24"
```

## Common Workflows

### Before Scaling
```bash
# 1. Get current baseline
BASELINE=$(curl -s "http://localhost:8000/api/v1/load/resources/my-api/baseline")
echo "Current pods: $(echo $BASELINE | jq -r '.pod_count')"
echo "Current CPU: $(echo $BASELINE | jq -r '.metrics.cpu_usage')"

# 2. Predict impact of scaling
PREDICTION=$(curl -s "http://localhost:8000/api/v1/load/resources/my-api/predict-load?target_pod_count=10")
echo "Predicted CPU: $(echo $PREDICTION | jq -r '.predicted_metrics.cpu_usage')"
echo "Confidence: $(echo $PREDICTION | jq -r '.confidence')"
echo "Recommendations: $(echo $PREDICTION | jq -r '.recommendations[]')"
```

### After Scaling
```bash
# Wait 15 minutes for stabilization
sleep 900

# Analyze impact
curl "http://localhost:8000/api/v1/load/resources/my-api/impact-analysis?lookback_hours=1" | jq '{
  overall_impact: .impacts[0].overall_impact,
  cpu_change: .impacts[0].changes.cpu_change_pct,
  latency_change: .impacts[0].changes.latency_change_pct,
  error_change: .impacts[0].changes.error_rate_change_pct,
  recommendations: .impacts[0].recommendations
}'
```

### Daily Health Check
```bash
# Check all services for high load
for service in api-gateway web-frontend order-service payment-api; do
  PATTERNS=$(curl -s "http://localhost:8000/api/v1/load/resources/$service/high-load-patterns")
  NEEDS_SCALING=$(echo $PATTERNS | jq -r '.needs_scaling')
  
  if [ "$NEEDS_SCALING" = "true" ]; then
    echo "⚠️  $service needs attention:"
    echo $PATTERNS | jq -r '.insights[]'
  fi
done
```

## Key Metrics

### Load Baseline
- **pod_count**: Current number of pods
- **cpu_usage**: 0-1 (0.8 = 80%)
- **memory_usage_bytes**: Bytes
- **request_rate**: Requests per second
- **latency_p95_seconds**: 95th percentile latency
- **error_rate**: 0-1 (0.05 = 5%)

### Impact Analysis
- **cpu_change_pct**: % change in CPU
- **memory_change_pct**: % change in memory
- **latency_change_pct**: % change in latency
- **error_rate_change_pct**: % change in errors

**Impact Levels:**
- **minimal**: <10% change
- **moderate**: 10-25% change
- **significant**: 25-50% change
- **critical**: >50% change or >20% error increase

### High Load Indicators
- **high_cpu**: >80% usage
- **high_memory**: >80% of limit
- **high_latency**: P95 >1 second
- **high_errors**: >5% error rate

## Response Interpretation

### Scaling Event
```json
{
  "timestamp": "2024-11-22T14:30:00Z",
  "pod_count_before": 3,
  "pod_count_after": 6,
  "scaling_type": "scale_up"
}
```
**Interpretation:** Service scaled from 3 to 6 pods at 14:30 UTC

### Impact Analysis
```json
{
  "changes": {
    "cpu_change_pct": -35.0,
    "latency_change_pct": -44.0
  },
  "overall_impact": "significant"
}
```
**Interpretation:** 
- CPU decreased 35% (good! ✅)
- Latency decreased 44% (excellent! ✅)
- Significant positive impact

### Prediction
```json
{
  "predicted_metrics": {
    "cpu_usage": 0.45
  },
  "confidence": 0.85,
  "recommendations": ["Predicted metrics look healthy"]
}
```
**Interpretation:**
- High confidence (85%)
- CPU predicted at 45% (safe ✅)
- Safe to proceed

## Troubleshooting

### "No scaling events detected"
**Check:** Is Prometheus scraping your service?
```bash
# Verify Prometheus has data
curl 'http://prometheus:9090/api/v1/query?query=kube_deployment_status_replicas{deployment=~".*my-service.*"}'
```

### "Low confidence prediction"
**Solution:** Increase lookback period
```bash
curl "http://localhost:8000/api/v1/load/resources/my-service/predict-load?target_pod_count=5&lookback_days=60"
```

### "Time to stabilize: null"
**Meaning:** Metrics haven't stabilized within 30 minutes
**Action:** Wait longer or investigate instability

## Best Practices

1. **Always predict before scaling in production**
   ```bash
   # Get prediction first
   PRED=$(curl -s "...predict-load?target_pod_count=N")
   # Check confidence > 0.5 and review recommendations
   ```

2. **Wait for stabilization before analyzing**
   ```bash
   # After scaling, wait 15-30 minutes
   sleep 900
   # Then analyze impact
   ```

3. **Monitor high load patterns daily**
   ```bash
   # Cron: Daily at 9 AM
   0 9 * * * /scripts/check-high-load.sh
   ```

4. **Compare predictions to actual results**
   ```bash
   # Before scaling
   PRED=$(curl -s "...predict-load?target_pod_count=8")
   echo $PRED > /tmp/prediction.json
   
   # After scaling + stabilization
   ACTUAL=$(curl -s ".../baseline")
   echo $ACTUAL > /tmp/actual.json
   
   # Compare
   diff <(jq '.predicted_metrics' /tmp/prediction.json) \
        <(jq '.metrics' /tmp/actual.json)
   ```

## API Quick Reference

| Endpoint | Method | Purpose | Key Params |
|----------|--------|---------|------------|
| `/scaling-events` | GET | Detect scaling | `lookback_hours` |
| `/baseline` | GET | Current metrics | - |
| `/impact-analysis` | GET | Scaling impact | `lookback_hours` |
| `/predict-load` | GET | Predict metrics | `target_pod_count`, `lookback_days` |
| `/high-load-patterns` | GET | Detect stress | `lookback_hours` |

## Integration Examples

### Bash Script
```bash
#!/bin/bash
SERVICE=$1
TARGET_PODS=$2

# Predict
PRED=$(curl -s "http://topdeck/api/v1/load/resources/$SERVICE/predict-load?target_pod_count=$TARGET_PODS")
CONF=$(echo $PRED | jq -r '.confidence')

if (( $(echo "$CONF < 0.5" | bc -l) )); then
  echo "Low confidence. Proceed with caution."
  exit 1
fi

echo "Prediction looks good. Safe to scale."
```

### Python
```python
import requests

def check_scaling_safe(service_id, target_pods):
    url = f"http://topdeck/api/v1/load/resources/{service_id}/predict-load"
    params = {"target_pod_count": target_pods}
    
    response = requests.get(url, params=params)
    prediction = response.json()
    
    if prediction["confidence"] < 0.5:
        print("Low confidence prediction")
        return False
    
    if prediction["predicted_metrics"]["cpu_usage"] > 0.8:
        print("Predicted CPU too high")
        return False
    
    print("Safe to scale:", prediction["recommendations"])
    return True
```

### CI/CD (GitHub Actions)
```yaml
- name: Validate scaling
  run: |
    PRED=$(curl -s "$TOPDECK_URL/api/v1/load/resources/$SERVICE/predict-load?target_pod_count=$NEW_COUNT")
    CONF=$(echo $PRED | jq -r '.confidence')
    
    if (( $(echo "$CONF < 0.6" | bc -l) )); then
      echo "::warning::Low confidence prediction"
      echo $PRED | jq '.recommendations[]'
    fi
```

## Related Commands

### Check Prometheus Connection
```bash
curl "http://localhost:8000/api/v1/load/health"
```

### List Available Services
```bash
# Query your service registry
curl "http://localhost:8000/api/v1/topology"
```

### Get Resource Details
```bash
curl "http://localhost:8000/api/v1/topology/resources/{id}"
```

## Support

- Full documentation: [LOAD_CHANGE_DETECTION.md](LOAD_CHANGE_DETECTION.md)
- Prometheus setup: [monitoring/collectors/prometheus.py](../src/topdeck/monitoring/collectors/prometheus.py)
- API source: [api/routes/load_detection.py](../src/topdeck/api/routes/load_detection.py)
