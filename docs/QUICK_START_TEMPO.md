# Quick Start: Tempo Integration

## What Changed?

**Before**: Trace IDs incorrectly associated with Prometheus ❌  
**After**: Trace IDs properly stored in Tempo ✅

## The Three Pillars

| System | Purpose | What It Stores |
|--------|---------|----------------|
| **Prometheus** | Metrics | CPU, memory, latency, error rates |
| **Tempo** | Traces | Trace IDs, spans, service calls |
| **Loki** | Logs | Application logs, errors |

## Quick Setup (5 minutes)

### 1. Ensure Tempo is Available
TopDeck integrates with your existing Tempo installation. Make sure:
- Tempo is running and accessible
- You have the Tempo query endpoint URL (default: `http://tempo:3200`)

### 2. Configure TopDeck
```bash
# Add to .env
TEMPO_URL=http://localhost:3200
```

### 3. Start/Restart TopDeck API
```bash
docker-compose restart api
# or
make run
```

### 4. Verify
```bash
curl http://localhost:8000/api/v1/monitoring/health | jq .tempo
```

Expected:
```json
{
  "status": "healthy",
  "url": "http://localhost:3200"
}
```

## Using the API

### Get a Trace
```bash
curl http://localhost:8000/api/v1/monitoring/traces/{trace-id}
```

### Get Traces for a Resource
```bash
curl "http://localhost:8000/api/v1/monitoring/resources/pod-123/traces?duration_hours=1&limit=20"
```

## When to Use What?

### Use Prometheus when you need:
- ✅ Current CPU/memory usage
- ✅ Request rate metrics
- ✅ Error rate percentages
- ✅ Latency percentiles (p95, p99)
- ✅ Resource saturation

### Use Tempo when you need:
- ✅ Full request trace (trace ID)
- ✅ Service-to-service calls
- ✅ Where time was spent in a request
- ✅ Which service is slow
- ✅ Error propagation path

### Use Loki when you need:
- ✅ Error messages
- ✅ Stack traces
- ✅ Debug logs
- ✅ Audit trails
- ✅ Correlation IDs

## Example: Debug Slow API Call

**Step 1**: Check Prometheus
```bash
# Find high latency
curl "http://localhost:8000/api/v1/monitoring/resources/api-service/metrics?resource_type=service"
```

**Step 2**: Get Trace from Tempo
```bash
# See which service is slow
curl "http://localhost:8000/api/v1/monitoring/traces/abc123"
```

**Step 3**: Check Logs in Loki
```bash
# Get error details
curl "http://localhost:8000/api/v1/monitoring/resources/slow-service/errors"
```

## Common Patterns

### Pattern: "Why is my service slow?"
1. Prometheus → Identify high latency
2. Tempo → See trace of slow request
3. Loki → Find error logs

### Pattern: "What services depend on this?"
1. Tempo → Get service dependency graph
2. Neo4j → Validate against expected topology

### Pattern: "Where did this error come from?"
1. Loki → Find error with trace_id
2. Tempo → Follow trace back to origin
3. Prometheus → Check metrics at that time

## Health Check

```bash
curl http://localhost:8000/api/v1/monitoring/health
```

All three should show "healthy":
```json
{
  "prometheus": {"status": "healthy"},
  "tempo": {"status": "healthy"},
  "loki": {"status": "healthy"}
}
```

## Troubleshooting

### Tempo shows "not_configured"
```bash
# Set environment variable
export TEMPO_URL=http://localhost:3200
```

### Tempo shows "unhealthy"
```bash
# Verify Tempo is accessible
curl http://your-tempo-url:3200/ready

# Check your Tempo instance logs
# (depends on your Tempo deployment)
```

### No traces returned
- Tempo stores traces sent via OTLP from your applications
- Ensure your applications are configured to send traces to your Tempo instance
- Check your Tempo OTLP receiver configuration

## Next Steps

1. **Configure trace sampling** in your applications
2. **Set up Grafana** to visualize traces
3. **Review** [OBSERVABILITY.md](./OBSERVABILITY.md) for architecture details
4. **Read** [TEMPO_INTEGRATION_SUMMARY.md](./TEMPO_INTEGRATION_SUMMARY.md) for full details

## Key Takeaways

✅ Prometheus is for **metrics** (numbers over time)  
✅ Tempo is for **traces** (request flows)  
✅ Loki is for **logs** (detailed messages)

✅ Trace IDs belong in **Tempo**, not Prometheus  
✅ All three work together for full observability  
✅ Each system has a specific purpose
