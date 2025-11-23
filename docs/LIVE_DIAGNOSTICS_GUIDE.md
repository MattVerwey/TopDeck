# Live Diagnostics Guide

## Overview

The Live Diagnostics panel provides real-time monitoring and ML-based anomaly detection for your network topology. It helps you quickly identify failing services, detect abnormal traffic patterns, and diagnose issues before they impact users.

## Features

### 1. Real-Time Service Health Monitoring

The Live Diagnostics panel continuously monitors all services in your topology and provides instant visibility into their health status:

- **Healthy** (Green): Service is operating normally
- **Degraded** (Orange): Service is experiencing issues but still operational
- **Failed** (Red): Service has failed and is not operational
- **Unknown** (Gray): Service status cannot be determined

### 2. ML-Based Anomaly Detection

Uses Isolation Forest machine learning algorithm to detect anomalies in:

- Request rates
- Error rates
- Latency (P95)
- CPU usage
- Memory usage
- Connection counts
- And more...

Anomalies are classified by severity:

- **Critical**: Immediate attention required
- **High**: Should be addressed soon
- **Medium**: Monitor closely
- **Low**: Informational

### 3. Traffic Pattern Analysis

Analyzes traffic flows between services to identify:

- Abnormal request patterns
- High error rates
- Latency spikes
- Traffic trends (increasing, decreasing, stable)

### 4. Dependency Failure Detection

Automatically identifies dependencies that are failing or degraded, helping you understand cascading failures and blast radius.

## Accessing Live Diagnostics

1. Navigate to the main TopDeck application
2. Click on **"Live Diagnostics"** in the left sidebar (icon: 🔍 Troubleshoot)
3. The panel will automatically load the latest diagnostics data

### Real-Time Updates (WebSocket)

**NEW in Phase 6:** Live Diagnostics now uses WebSocket for true real-time updates!

**Connection Status Indicator:**
- 🟢 **WebSocket (Real-time)**: Connected via WebSocket, receiving instant updates every 10 seconds
- 🟡 **Polling (Fallback)**: WebSocket unavailable, using 30-second polling as fallback
- 🔴 **Disconnected**: No connection, attempting to reconnect

**Features:**
- ✅ **Instant Updates**: Changes appear immediately (10s WebSocket vs 30s polling)
- ✅ **Auto-Reconnection**: Automatically reconnects if connection drops (up to 5 attempts)
- ✅ **Graceful Fallback**: Falls back to polling if WebSocket unavailable
- ✅ **Lower Bandwidth**: Push model uses less bandwidth than polling
- ✅ **Connection Status**: Visual indicator shows current connection type

**Configuration:**
The WebSocket endpoint is available at: `ws://<your-server>:8000/api/v1/ws/live-diagnostics`

Query parameters:
- `update_interval`: Update frequency in seconds (1-60, default: 10)

Example: `ws://localhost:8000/api/v1/ws/live-diagnostics?update_interval=5`

## Panel Layout

### Header

- **System Status**: Overall health indicator (Healthy / Degraded / Critical)
- **Connection Status**: WebSocket/Polling/Disconnected indicator with icon
- **Refresh Button**: Manually request immediate snapshot update

### Summary Cards

Four key metrics at a glance:

1. **Total Services**: Number of monitored services with health percentage bar
2. **Active Anomalies**: Count of detected anomalies with critical count
3. **Failing Dependencies**: Number of dependency failures
4. **Abnormal Traffic**: Count of abnormal traffic flows

### Tabs

#### 1. Topology Tab

Interactive network topology visualization showing:

- **Nodes**: Represent services, color-coded by health status
- **Edges**: Show dependencies between services
- **Visual Indicators**:
  - Node color = Health status
  - Node border thickness = Anomaly count (thicker = more anomalies)
  - Red border = Critical anomalies
  - Edge color = Dependency health (red = failed, orange = degraded)

**Interactions:**
- Click on any node to view detailed error information
- Zoom in/out using mouse wheel
- Pan by clicking and dragging
- Auto-layout arranges nodes for optimal visibility

#### 2. Anomalies Tab

List of all detected anomalies with:

- Severity indicator
- Resource name
- Metric name (e.g., "error_rate", "latency_p95")
- Current value vs. expected value
- Deviation percentage
- Potential causes
- Detection timestamp

**Filtering:** Use the severity filter to show only critical/high priority anomalies

Click on any anomaly to view full service details.

#### 3. Traffic Patterns Tab

Bar chart visualization showing traffic metrics between service pairs:

- **Request Rate**: Requests per second
- **Error Rate**: Percentage of failed requests
- **Latency**: 95th percentile latency in milliseconds

**Visual Indicators:**
- Red bars = Abnormal traffic patterns
- Blue bars = Normal traffic patterns

Click on any bar to view source service details.

#### 4. Failing Dependencies Tab

List of all failing dependencies with:

- Source service → Target service
- Status (Degraded / Failed)
- Health score (0-100)
- Anomaly count

Click on any dependency to view target service error details.

## Error Detail Drawer

When you click on a service, anomaly, or dependency, a side drawer opens showing:

### Service Information
- Service name and type
- Current status
- Health score
- Last update timestamp

### Current Metrics
All current metric values including:
- CPU usage
- Memory usage
- Request rate
- Error rate
- Latency
- Connection counts

### Detected Anomalies
List of all anomalies for this service:
- Severity level
- Metric name
- Anomaly message
- Deviation percentage

### System Anomalies
Additional system-level anomalies detected by Prometheus

## API Endpoints

### Get Complete Snapshot

```bash
GET /api/v1/live-diagnostics/snapshot?duration_hours=1
```

Returns complete diagnostics snapshot including services, anomalies, traffic patterns, and failing dependencies.

**Parameters:**
- `duration_hours` (optional, default: 1): Time window for analysis (1-24 hours)

### Get Service Health

```bash
GET /api/v1/live-diagnostics/services/{resource_id}/health?resource_type=service&duration_hours=1
```

Get detailed health information for a specific service.

**Parameters:**
- `resource_type` (optional, default: "service"): Type of resource
- `duration_hours` (optional, default: 1): Time window for analysis

### Get Anomalies

```bash
GET /api/v1/live-diagnostics/anomalies?severity=high&duration_hours=1&limit=50
```

Get list of detected anomalies with optional filtering.

**Parameters:**
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `duration_hours` (optional, default: 1): Time window for detection
- `limit` (optional, default: 50): Maximum number of results (1-500)

### Get Traffic Patterns

```bash
GET /api/v1/live-diagnostics/traffic-patterns?duration_hours=1&abnormal_only=false
```

Analyze traffic patterns between services.

**Parameters:**
- `duration_hours` (optional, default: 1): Time window for analysis
- `abnormal_only` (optional, default: false): Return only abnormal patterns

### Get Failing Dependencies

```bash
GET /api/v1/live-diagnostics/failing-dependencies
```

Get list of dependencies where the target service is failed or degraded.

### Health Check

```bash
GET /api/v1/live-diagnostics/health
```

Check health of the live diagnostics service and its dependencies (Prometheus, Neo4j).

## Use Cases

### 1. Service Failure Investigation

**Scenario**: A service has failed and you need to understand why.

**Steps:**
1. Open Live Diagnostics
2. Check the Topology tab - failed services are highlighted in red
3. Click on the failed service to open the Error Detail Drawer
4. Review:
   - Current metrics to see what's abnormal
   - Detected anomalies to understand the failure cause
   - System anomalies for additional context
5. Check the Failing Dependencies tab to see what other services are affected
6. Review Traffic Patterns to identify if traffic spikes caused the failure

### 2. Proactive Monitoring

**Scenario**: You want to catch issues before they become failures.

**Steps:**
1. Enable Auto-Refresh (default ON)
2. Monitor the Summary Cards for trends
3. Review the Anomalies tab regularly for early warning signs
4. Watch for degraded services (orange) in the Topology
5. Investigate medium/high severity anomalies before they escalate

### 3. Traffic Analysis

**Scenario**: Understand how traffic is flowing and identify bottlenecks.

**Steps:**
1. Go to the Traffic Patterns tab
2. Look for red bars indicating abnormal patterns
3. Review error rates and latency metrics
4. Identify services receiving high error rates
5. Use the trend indicator to understand if issues are getting worse

### 4. Dependency Impact Analysis

**Scenario**: A database is failing - which services are affected?

**Steps:**
1. Go to the Failing Dependencies tab
2. Find the database in the target column
3. See all services that depend on it in the source column
4. Click through to each affected service to understand blast radius
5. Use the Topology tab for visual representation of the impact

## Configuration

### Backend Configuration

Live Diagnostics requires the following services to be configured:

**Prometheus** (for metrics):
```bash
export PROMETHEUS_URL=http://prometheus:9090
```

**Neo4j** (for topology):
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your-password
```

### Anomaly Detection Thresholds

The following thresholds can be customized in `src/topdeck/monitoring/live_diagnostics.py`:

```python
# Health status thresholds
HEALTH_EXCELLENT_THRESHOLD = 90.0
HEALTH_GOOD_THRESHOLD = 70.0
HEALTH_DEGRADED_THRESHOLD = 50.0

# Anomaly detection thresholds
ANOMALY_SCORE_CRITICAL = 0.8
ANOMALY_SCORE_HIGH = 0.6
ANOMALY_SCORE_MEDIUM = 0.4
```

### Refresh Interval

Default auto-refresh interval is 30 seconds. This can be adjusted in the frontend component.

## Troubleshooting

### No Data Displayed

**Possible causes:**
1. Prometheus is not configured or not running
2. Neo4j is not configured or not running
3. No resources have been discovered yet

**Solution:**
- Check `/api/v1/live-diagnostics/health` endpoint
- Verify Prometheus and Neo4j connectivity
- Run resource discovery if topology is empty

### Anomalies Not Detected

**Possible causes:**
1. Prometheus is not collecting metrics
2. Metric names don't match expected patterns
3. Not enough historical data for ML models

**Solution:**
- Verify Prometheus is scraping your services
- Check metric naming conventions
- Allow time for data collection (at least 1 hour)

### High False Positive Rate

**Possible causes:**
1. Anomaly thresholds are too sensitive
2. Services have high variance in normal behavior

**Solution:**
- Adjust anomaly score thresholds
- Increase Isolation Forest contamination parameter
- Train models on longer historical data

## Best Practices

1. **Enable Auto-Refresh**: Keep auto-refresh enabled for real-time monitoring
2. **Monitor Trends**: Watch for increasing anomaly counts over time
3. **Investigate Degraded Services**: Don't wait for failures - investigate degraded services proactively
4. **Use Multiple Views**: Combine Topology, Anomalies, and Traffic Patterns for complete picture
5. **Set Up Alerts**: Use the API endpoints to build custom alerting based on anomaly counts
6. **Review Historical Patterns**: Compare current state with historical baselines
7. **Document Incidents**: Use the detailed information in the Error Drawer for incident reports

## Integration with Other Features

Live Diagnostics integrates seamlessly with other TopDeck features:

- **Risk Analysis**: Anomalies inform risk scores for change impact
- **Error Replay**: Captured errors feed into anomaly detection
- **Topology**: Shared topology data ensures consistency
- **SLA/SLO**: Health scores inform SLO calculations
- **Change Management**: Correlate anomalies with recent changes

## Performance Considerations

- **Data Volume**: For large topologies (>1000 services), consider filtering by resource type
- **Refresh Rate**: For very large deployments, increase refresh interval to reduce load
- **Time Window**: Shorter time windows (1 hour) are faster than longer windows (24 hours)
- **Anomaly Limit**: Use the `limit` parameter to control result size

## Security

Live Diagnostics uses read-only access to:
- Prometheus metrics
- Neo4j topology database

No credentials or sensitive data are exposed in the UI. All API calls use the same authentication as the main TopDeck application.

## Metrics Reference

### Service Metrics

- `cpu_usage`: CPU utilization (0.0 - 1.0)
- `memory_usage`: Memory usage in bytes
- `latency_p95`: 95th percentile latency in seconds
- `request_rate`: Requests per second
- `error_rate`: Error rate (0.0 - 1.0)

### Database Metrics

- `query_duration_p95`: 95th percentile query duration in seconds
- `connections`: Active connection count
- `deadlocks`: Deadlock rate

### Load Balancer Metrics

- `request_rate`: Requests per second
- `backend_connection_errors`: Backend connection error rate

## Future Enhancements

Planned improvements for Live Diagnostics:

1. **WebSocket Support**: True real-time updates without polling
2. **Custom Dashboards**: Create personalized diagnostic views
3. **Alerting**: Built-in alerting based on anomaly detection
4. **Historical Comparison**: Compare current state with past incidents
5. **Root Cause Analysis**: Automated RCA using ML
6. **Predictive Alerts**: Predict failures before they occur
7. **Custom Metrics**: Support for custom metric types
8. **Multi-Cluster**: View diagnostics across multiple clusters

## Support

For issues or questions:
- Check the [troubleshooting section](#troubleshooting)
- Review API endpoint responses for error messages
- Check service health at `/api/v1/live-diagnostics/health`
- Review logs in the backend service

## Related Documentation

- [Prometheus Integration](./PROMETHEUS_INTEGRATION.md)
- [ML Prediction Guide](./ML_PREDICTION_GUIDE.md)
- [Topology Analysis](./ENHANCED_TOPOLOGY_ANALYSIS.md)
- [Risk Analysis](./ENHANCED_RISK_ANALYSIS.md)
- [Error Replay Guide](./ERROR_REPLAY_GUIDE.md)
