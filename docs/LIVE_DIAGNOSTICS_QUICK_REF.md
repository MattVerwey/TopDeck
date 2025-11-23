# Live Diagnostics Quick Reference

Quick reference for the Live Diagnostics feature in TopDeck.

## Quick Start

1. Navigate to **Live Diagnostics** in the sidebar
2. View the **Summary Cards** for at-a-glance metrics
3. Check the **Topology** tab to see service health visualization
4. Click on any service to view detailed error information

## API Endpoints

### Get Complete Snapshot
```bash
curl "http://localhost:8000/api/v1/live-diagnostics/snapshot?duration_hours=1"
```

### Get Service Health
```bash
curl "http://localhost:8000/api/v1/live-diagnostics/services/api-gateway/health?duration_hours=1"
```

### Get Anomalies
```bash
curl "http://localhost:8000/api/v1/live-diagnostics/anomalies?severity=high&limit=20"
```

### Get Traffic Patterns
```bash
curl "http://localhost:8000/api/v1/live-diagnostics/traffic-patterns?abnormal_only=true"
```

### Get Failing Dependencies
```bash
curl "http://localhost:8000/api/v1/live-diagnostics/failing-dependencies"
```

### Health Check
```bash
curl "http://localhost:8000/api/v1/live-diagnostics/health"
```

## Color Codes

### Service Health Status
- 🟢 **Green**: Healthy
- 🟠 **Orange**: Degraded  
- 🔴 **Red**: Failed
- ⚪ **Gray**: Unknown

### Anomaly Severity
- 🔴 **Critical/High**: Immediate attention required
- 🟠 **Medium**: Monitor closely
- 🔵 **Low**: Informational

## Key Metrics

### Service Metrics
- **CPU Usage**: 0.0 - 1.0 (>0.9 = saturated)
- **Memory Usage**: Bytes
- **Latency P95**: Seconds (>1.0s = high)
- **Request Rate**: Requests/second
- **Error Rate**: 0.0 - 1.0 (>0.05 = high)

### Database Metrics
- **Query Duration P95**: Seconds
- **Connections**: Active count
- **Deadlocks**: Rate

### Health Score
- **90-100**: Excellent
- **70-89**: Good
- **50-69**: Degraded
- **0-49**: Failed

## Common Tasks

### Investigate Service Failure
1. Go to **Topology** tab
2. Click on red node
3. Review metrics and anomalies in drawer
4. Check **Failing Dependencies** tab for impact

### Monitor for Issues
1. Enable **Auto-Refresh** (default ON)
2. Watch **Summary Cards** for trends
3. Review **Anomalies** tab for warnings
4. Investigate degraded (orange) services

### Analyze Traffic
1. Go to **Traffic Patterns** tab
2. Look for red bars (abnormal)
3. Review error rates and latency
4. Check trend indicators

### Find Dependency Impact
1. Go to **Failing Dependencies** tab
2. Find target service
3. See all affected source services
4. View **Topology** for visual impact

## Troubleshooting

### No Data
- Check Prometheus: `/api/v1/live-diagnostics/health`
- Verify Neo4j connectivity
- Run resource discovery

### No Anomalies
- Verify Prometheus is scraping
- Check metric naming
- Wait for data collection (1+ hour)

### High False Positives
- Adjust thresholds in backend
- Increase contamination parameter
- Use longer historical data

## Configuration

### Environment Variables
```bash
export PROMETHEUS_URL=http://prometheus:9090
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password
```

### Thresholds (in code)
```python
# Health
HEALTH_EXCELLENT_THRESHOLD = 90.0
HEALTH_DEGRADED_THRESHOLD = 50.0

# Anomalies
ANOMALY_SCORE_CRITICAL = 0.8
ANOMALY_SCORE_HIGH = 0.6
```

## Integration

- **Risk Analysis**: Anomalies inform risk scores
- **Error Replay**: Errors feed anomaly detection
- **Topology**: Shared topology data
- **SLA/SLO**: Health informs SLO calculations

## Panel Tabs

1. **Topology**: Interactive network graph
2. **Anomalies**: List of detected anomalies
3. **Traffic Patterns**: Bar chart of traffic flows
4. **Failing Dependencies**: List of failed dependencies

## Auto-Refresh

- **Default**: ON (every 30 seconds)
- **Toggle**: Button in header
- **Manual**: Refresh button

## Best Practices

1. ✅ Enable auto-refresh for real-time monitoring
2. ✅ Investigate degraded services proactively
3. ✅ Use multiple tabs for complete picture
4. ✅ Monitor trends over time
5. ✅ Document incidents using drawer details

## ML Algorithm

- **Method**: Isolation Forest
- **Purpose**: Unsupervised anomaly detection
- **Features**: Metrics from Prometheus
- **Output**: Anomaly score (0.0 - 1.0)

## Performance Tips

- Use shorter time windows (1 hour) for speed
- Increase refresh interval for large deployments
- Filter by resource type for large topologies
- Use limit parameter to control result size

## Quick Commands

### Python
```python
import requests

# Get snapshot
response = requests.get(
    "http://localhost:8000/api/v1/live-diagnostics/snapshot",
    params={"duration_hours": 1}
)
snapshot = response.json()

# Get service health
health = requests.get(
    f"http://localhost:8000/api/v1/live-diagnostics/services/{resource_id}/health"
).json()

# Get critical anomalies
anomalies = requests.get(
    "http://localhost:8000/api/v1/live-diagnostics/anomalies",
    params={"severity": "critical", "limit": 10}
).json()
```

### JavaScript
```javascript
// Get snapshot
const snapshot = await fetch(
  'http://localhost:8000/api/v1/live-diagnostics/snapshot?duration_hours=1'
).then(r => r.json());

// Get anomalies
const anomalies = await fetch(
  'http://localhost:8000/api/v1/live-diagnostics/anomalies?severity=high'
).then(r => r.json());
```

## Related Docs

- [Full Live Diagnostics Guide](./LIVE_DIAGNOSTICS_GUIDE.md)
- [ML Prediction Guide](./ML_PREDICTION_GUIDE.md)
- [Topology Analysis](./ENHANCED_TOPOLOGY_ANALYSIS.md)
- [Risk Analysis](./ENHANCED_RISK_ANALYSIS.md)

## Support

- Health Check: `/api/v1/live-diagnostics/health`
- Logs: Check backend service logs
- Issues: Review [troubleshooting](#troubleshooting) section
