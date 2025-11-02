# Reporting Quick Reference

Quick reference for TopDeck's reporting functionality.

## Report Types

| Type | Description | Use Case |
|------|-------------|----------|
| `resource_health` | Health metrics and status | Monitor resource performance |
| `change_impact` | Changes and their impact | Review what changed |
| `error_timeline` | Error patterns over time | Debug error spikes |
| `code_deployment_correlation` | Deployments vs errors | Validate deployment stability |
| `comprehensive` | All of the above | Post-incident analysis |

## Quick Commands

### Generate Comprehensive Report
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "comprehensive",
    "resource_id": "resource-123",
    "time_range_hours": 48
  }'
```

### Quick Resource Report
```bash
curl -X POST "http://localhost:8000/api/v1/reports/resource/my-resource?report_type=comprehensive&time_range_hours=24"
```

### Resource Health Report
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "resource_health",
    "resource_id": "db-prod-01",
    "time_range_hours": 24
  }'
```

### Error Timeline Report
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "error_timeline",
    "resource_id": "api-gateway",
    "time_range_hours": 72
  }'
```

### Deployment Correlation Report
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "code_deployment_correlation",
    "resource_id": "app-service",
    "time_range_hours": 96
  }'
```

### Change Impact Report
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "change_impact",
    "time_range_hours": 168
  }'
```

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/reports/generate` | POST | Generate any report type |
| `/api/v1/reports/resource/{id}` | POST | Quick resource report |
| `/api/v1/reports/types` | GET | List report types |
| `/api/v1/reports/formats` | GET | List output formats |
| `/api/v1/reports/health` | GET | Service health check |

## Request Parameters

### Core Parameters
```json
{
  "report_type": "comprehensive",        // Required
  "report_format": "json",              // Optional: json, html, markdown
  "resource_id": "resource-123",        // Optional: specific resource
  "time_range_hours": 48                // Optional: 1-168 hours (default: 24)
}
```

### Optional Parameters
```json
{
  "include_charts": true,               // Include chart data (default: true)
  "include_error_details": true,        // Include error details (default: true)
  "include_change_details": true,       // Include change details (default: true)
  "include_code_changes": true,         // Include code changes (default: true)
  "max_errors": 50,                     // Max errors to include (default: 50)
  "max_changes": 20                     // Max changes to include (default: 20)
}
```

## Response Structure

```json
{
  "metadata": {
    "report_id": "report-456",
    "report_type": "comprehensive",
    "generated_at": "2024-11-02T12:00:00Z",
    "resource_id": "resource-123",
    "time_range_start": "2024-10-31T12:00:00Z",
    "time_range_end": "2024-11-02T12:00:00Z"
  },
  "title": "Comprehensive Report",
  "summary": "Report summary text",
  "sections": [
    {
      "title": "Section Title",
      "content": "Section content",
      "section_type": "text|chart|table",
      "data": { ... },
      "charts": [ ... ],
      "order": 1
    }
  ],
  "status": "completed"
}
```

## Common Use Cases

### Post-Incident Analysis
```bash
# Get complete picture of what happened
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -d '{"report_type":"comprehensive","resource_id":"failed-resource","time_range_hours":24}'
```

### Deployment Validation
```bash
# Check if deployment caused issues
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -d '{"report_type":"code_deployment_correlation","resource_id":"deployed-service","time_range_hours":8}'
```

### Daily Health Check
```bash
# Monitor critical resource health
curl -X POST "http://localhost:8000/api/v1/reports/resource/critical-db?report_type=resource_health&time_range_hours=24"
```

### Weekly Change Review
```bash
# Review all changes for the week
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -d '{"report_type":"change_impact","time_range_hours":168}'
```

## Chart Data Format

Charts are returned in format-agnostic structure:

```json
{
  "type": "line|bar|pie|combo",
  "title": "Chart Title",
  "x_label": "X Axis",
  "y_label": "Y Axis",
  "data": {
    "labels": ["Label1", "Label2", ...],
    "datasets": [
      {
        "label": "Dataset Name",
        "data": [1, 2, 3, ...],
        "color": "#ff0000",
        "type": "line|bar"
      }
    ]
  }
}
```

## Python Example

```python
import requests

def generate_report(resource_id, report_type="comprehensive", hours=24):
    response = requests.post(
        "http://localhost:8000/api/v1/reports/generate",
        json={
            "report_type": report_type,
            "resource_id": resource_id,
            "time_range_hours": hours
        }
    )
    return response.json()

# Use it
report = generate_report("my-resource", "resource_health", 48)
print(f"Title: {report['title']}")
print(f"Summary: {report['summary']}")

for section in report['sections']:
    print(f"\n{section['title']}")
    if section['charts']:
        print(f"  - Contains {len(section['charts'])} chart(s)")
```

## Time Range Recommendations

| Duration | Use Case |
|----------|----------|
| 1-4 hours | Real-time incident response |
| 4-24 hours | Recent issues, immediate debugging |
| 24-48 hours | Deployment impact analysis |
| 48-72 hours | Short-term trend analysis |
| 72-168 hours | Weekly reviews, pattern identification |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Slow generation | Reduce time_range_hours or set include_charts=false |
| Missing data | Check resource_id and ensure data exists |
| Large report | Reduce max_errors and max_changes |
| No charts | Verify include_charts=true in request |

## Integration with Other Features

### With Error Replay
Reports automatically include data from error replay service:
- Error snapshots
- Error correlation
- Timeline reconstruction

### With Change Management
Reports pull change data from change management:
- Change requests
- Impact assessments
- Risk levels

### With Monitoring
Reports integrate with monitoring platforms:
- Prometheus metrics
- Loki logs
- Tempo traces

## See Also

- [Full Reporting Guide](REPORTING_GUIDE.md)
- [Change Management Guide](CHANGE_MANAGEMENT_GUIDE.md)
- [Error Replay Guide](ERROR_REPLAY_GUIDE.md)
- [API Documentation](../src/topdeck/api/routes/reporting.py)
