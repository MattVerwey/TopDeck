# Issue #7: Implement Performance Monitoring Integration

**Labels**: `enhancement`, `monitoring`, `priority: medium`, `phase-4`

## Description

Integrate with performance monitoring and observability platforms to track errors, API latency, database deadlocks, and other performance issues. This data feeds into the risk analysis and helps identify root causes.

## Requirements

### Data to Collect

1. **Application Performance Metrics**
   - API response times
   - Request rates
   - Error rates and status codes
   - Transaction traces

2. **Database Performance**
   - Query execution times
   - Deadlocks and timeouts
   - Connection pool metrics
   - Lock wait times

3. **Infrastructure Metrics**
   - CPU and memory usage
   - Network throughput
   - Disk I/O
   - Container restarts

4. **Error Tracking**
   - Exception types and frequencies
   - Stack traces
   - Error context and correlation IDs
   - User impact

### Platforms to Integrate

**Azure Monitor**:
- Application Insights
- Log Analytics
- Azure Monitor Metrics

**AWS**:
- CloudWatch
- X-Ray
- CloudWatch Logs Insights

**Third-Party**:
- Datadog
- New Relic
- Prometheus + Grafana
- Elastic APM

## Use Cases

### Use Case 1: Error Correlation
```
User reports: "App is slow"

TopDeck Analysis:
1. Check recent deployments → webapp-prod updated 2 hours ago
2. Check Application Insights → 500 errors increased 400%
3. Check dependencies → sql-db-prod showing high query times
4. Check database logs → Deadlock detected on Orders table

Root Cause: New deployment introduced a query that causes deadlocks
```

### Use Case 2: Performance Degradation
```
Alert: API Gateway latency increased

TopDeck Analysis:
1. Trace requests through topology
2. Identify slow service: recommendation-api (p95 latency 5s)
3. Check dependencies: calls external product-catalog-api
4. Check external API: Experiencing issues (3rd party status page)

Recommendation: Implement caching or circuit breaker
```

### Use Case 3: Predictive Analysis
```
TopDeck Notice: sql-db-prod at risk

Analysis:
- Query execution times trending up over 7 days
- DTU usage consistently >80%
- Deadlocks increasing (5 in last week)
- 12 services depend on this database

Recommendation: Scale up database tier before impact escalates
```

## Technical Design

### Module Structure
```
src/monitoring/
├── __init__.py
├── collectors/
│   ├── azure_monitor.py     # Azure Monitor/App Insights
│   ├── cloudwatch.py        # AWS CloudWatch
│   ├── datadog.py           # Datadog integration
│   ├── prometheus.py        # Prometheus metrics
│   └── elastic.py           # Elastic APM
├── metrics/
│   ├── aggregator.py        # Aggregate metrics from sources
│   ├── anomaly_detector.py  # Detect anomalies
│   └── correlator.py        # Correlate errors to resources
├── alerts/
│   ├── processor.py         # Process incoming alerts
│   ├── correlator.py        # Correlate alerts to topology
│   └── notifier.py          # Send notifications
└── config.py
```

### Key Classes

```python
class MetricsCollector:
    def __init__(self, platform: str, credentials):
        """Initialize metrics collector for platform"""
        
    def collect_application_metrics(
        self, 
        resource_id: str, 
        time_range: TimeRange
    ) -> ApplicationMetrics:
        """Collect application performance metrics"""
        
    def collect_database_metrics(
        self, 
        resource_id: str, 
        time_range: TimeRange
    ) -> DatabaseMetrics:
        """Collect database performance metrics"""
        
    def detect_anomalies(
        self, 
        metrics: List[Metric]
    ) -> List[Anomaly]:
        """Detect anomalies in metrics"""

class ErrorCorrelator:
    def __init__(self, graph_db):
        """Initialize with graph database"""
        
    def correlate_error_to_resource(
        self, 
        error: Error
    ) -> CorrelationResult:
        """Correlate error to specific resource"""
        
    def trace_error_path(
        self, 
        error_id: str
    ) -> List[Resource]:
        """Trace error through system topology"""
        
    def get_root_cause_analysis(
        self, 
        error_id: str
    ) -> RootCauseAnalysis:
        """Attempt to determine root cause"""
```

### Data Models

```python
@dataclass
class ApplicationMetrics:
    resource_id: str
    timestamp: datetime
    request_rate: float
    error_rate: float
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    status_codes: Dict[int, int]

@dataclass
class DatabaseMetrics:
    resource_id: str
    timestamp: datetime
    query_count: int
    avg_query_time: float
    slow_queries: int
    deadlocks: int
    connection_pool_usage: float
    cpu_usage: float
    storage_usage: float

@dataclass
class Anomaly:
    metric_name: str
    resource_id: str
    detected_at: datetime
    severity: str
    baseline_value: float
    current_value: float
    deviation: float
    description: str
```

## Integration Examples

### Azure Application Insights
```python
from azure.monitor.query import LogsQueryClient

# Query Application Insights
query = """
requests
| where timestamp > ago(1h)
| summarize 
    count=count(),
    avg_duration=avg(duration),
    p95=percentile(duration, 95)
  by operation_Name, resultCode
"""

results = client.query_workspace(workspace_id, query, timespan)
```

### Prometheus
```python
from prometheus_api_client import PrometheusConnect

prom = PrometheusConnect(url="http://prometheus:9090")

# Query API latency
query = 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
result = prom.custom_query(query)
```

## Visualization

### Performance Dashboard
```
┌────────────────────────────────────────────────────────┐
│  Performance Overview                                  │
├────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐  │
│  │  API Latency (p95)                               │  │
│  │  [Line chart showing latency over time]          │  │
│  │                                                   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Error Rate                                      │  │
│  │  [Chart with spikes highlighted]                 │  │
│  │  ⚠️ Spike detected at 14:32 - correlated with    │  │
│  │     deployment of webapp-prod v1.2.5            │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Active Issues                                         │
│  • sql-db-prod: High deadlock rate (5 in last hour)   │
│  • api-gateway: 95th percentile latency increased 200% │
│  • redis-cache: Connection pool exhaustion            │
└────────────────────────────────────────────────────────┘
```

## Tasks

- [ ] Research monitoring platform APIs
- [ ] Implement Azure Monitor integration
- [ ] Implement CloudWatch integration
- [ ] Implement Prometheus integration
- [ ] Create metrics aggregator
- [ ] Implement anomaly detection
- [ ] Build error correlation logic
- [ ] Create performance metrics storage
- [ ] Add alerting system
- [ ] Build performance dashboard
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Create documentation

## Success Criteria

- [ ] Can collect metrics from monitoring platforms
- [ ] Accurately correlates errors to resources
- [ ] Detects performance anomalies
- [ ] Links performance issues to topology changes
- [ ] Alerting works reliably
- [ ] Dashboard shows real-time data
- [ ] Tests pass with >80% coverage
- [ ] Documentation complete

## Performance Considerations

- Batch metric collection
- Cache metrics for dashboard queries
- Use time-series database for metrics storage
- Implement data retention policies
- Rate limit external API calls

## Security Considerations

- Securely store monitoring platform credentials
- Implement read-only access
- Mask sensitive data in logs
- Encrypt data in transit

## Dependencies

- Issue #2: Core Data Models
- Issue #3: Azure Resource Discovery
- Issue #5: Risk Analysis Engine (consumes this data)
- Access to monitoring platforms

## Timeline

Weeks 7-8

## Related Issues

- Issue #5: Risk Analysis Engine (uses this data)
- Issue #6: Topology Visualization (displays metrics)
