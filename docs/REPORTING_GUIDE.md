# Reporting Guide

## Overview

TopDeck's Reporting features provide comprehensive reports with charts and analysis to help you understand what changes affected your resources or services, when code changes were made, and when resources became unstable or started erroring. This guide covers how to generate and use reports effectively.

## Features

### 1. Resource Health Reports

Track the health and performance of your resources over time:

- **Health metrics** - CPU, memory, latency, error rates
- **Status tracking** - Monitor resource state changes
- **Performance trends** - Identify degradation patterns
- **Error correlation** - Link errors to resource health

### 2. Change Impact Reports

Understand the impact of changes on your infrastructure:

- **Change distribution** - View changes by type and risk level
- **Impact analysis** - See directly and indirectly affected resources
- **Risk assessment** - Understand the risk level of changes
- **Timeline visualization** - Track when changes occurred

### 3. Error Timeline Reports

Analyze error patterns and identify when problems started:

- **Error timeline** - Visualize when errors occurred
- **Severity distribution** - Group errors by severity level
- **Error clustering** - Identify periods of high error rates
- **Root cause indicators** - Link errors to potential causes

### 4. Code Deployment Correlation Reports

Correlate deployments with system stability:

- **Deployment timeline** - Track when code was deployed
- **Error correlation** - See errors that occurred after deployments
- **Stability metrics** - Calculate deployment success rates
- **Post-deployment analysis** - Identify problematic deployments

### 5. Comprehensive Reports

Get a complete view combining all report types:

- **All-in-one view** - Resource health, changes, errors, and deployments
- **Correlation analysis** - Understand relationships between events
- **Stability scoring** - Overall system stability metrics
- **Actionable insights** - Recommendations for improvement

## API Reference

### Generate Report

Generate a new report based on specified parameters:

```bash
POST /api/v1/reports/generate
Content-Type: application/json

{
  "report_type": "comprehensive",
  "resource_id": "resource-123",
  "time_range_hours": 48,
  "include_charts": true,
  "include_error_details": true,
  "include_change_details": true,
  "include_code_changes": true,
  "max_errors": 50,
  "max_changes": 20
}
```

Response:
```json
{
  "metadata": {
    "report_id": "report-456",
    "report_type": "comprehensive",
    "report_format": "json",
    "generated_at": "2024-11-02T12:00:00Z",
    "resource_id": "resource-123",
    "resource_name": "api-gateway-prod",
    "time_range_start": "2024-10-31T12:00:00Z",
    "time_range_end": "2024-11-02T12:00:00Z"
  },
  "title": "Comprehensive Report: api-gateway-prod",
  "summary": "Comprehensive report covering resource health, 5 changes, 23 errors, and 8 deployments in the last 48 hours.",
  "sections": [
    {
      "title": "Resource Overview",
      "content": "Resource details and current status",
      "section_type": "text",
      "data": { ... },
      "order": 1
    },
    {
      "title": "Health Metrics",
      "content": "Resource health metrics over time.",
      "section_type": "chart",
      "charts": [
        {
          "type": "line",
          "title": "Resource Health Metrics",
          "data": { ... }
        }
      ],
      "order": 2
    },
    {
      "title": "Error Timeline",
      "content": "Timeline of errors by severity.",
      "section_type": "chart",
      "charts": [
        {
          "type": "line",
          "title": "Error Timeline",
          "data": { ... }
        }
      ],
      "order": 5
    }
  ],
  "status": "completed"
}
```

### Generate Resource Report (Quick)

Quick way to generate a report for a specific resource:

```bash
POST /api/v1/reports/resource/{resource_id}?report_type=comprehensive&time_range_hours=48
```

Example:
```bash
POST /api/v1/reports/resource/aks-cluster-prod?report_type=error_timeline&time_range_hours=24
```

### Get Available Report Types

```bash
GET /api/v1/reports/types
```

Response:
```json
[
  "resource_health",
  "change_impact",
  "error_timeline",
  "code_deployment_correlation",
  "comprehensive"
]
```

### Get Available Report Formats

```bash
GET /api/v1/reports/formats
```

Response:
```json
[
  "json",
  "html",
  "markdown"
]
```

### Health Check

```bash
GET /api/v1/reports/health
```

Response:
```json
{
  "status": "healthy",
  "service": "reporting"
}
```

## Report Types

### Resource Health Report

Focus on resource health metrics and status:

```bash
POST /api/v1/reports/generate
{
  "report_type": "resource_health",
  "resource_id": "sql-db-prod",
  "time_range_hours": 24
}
```

**Sections included:**
- Resource overview (name, type, status, region)
- Health metrics over time (CPU, memory, performance)
- Error summary for the resource
- Current status and recent changes

**Use when:** You want to understand the health of a specific resource over time.

### Change Impact Report

Focus on changes and their impact:

```bash
POST /api/v1/reports/generate
{
  "report_type": "change_impact",
  "resource_id": "api-gateway-prod",
  "time_range_hours": 48
}
```

**Sections included:**
- Changes overview (count by type and risk)
- Change distribution chart
- Detailed change analysis
- Impact assessment for each change

**Use when:** You want to understand what changes were made and their potential impact.

### Error Timeline Report

Focus on errors and when they occurred:

```bash
POST /api/v1/reports/generate
{
  "report_type": "error_timeline",
  "resource_id": "web-app-prod",
  "time_range_hours": 72
}
```

**Sections included:**
- Error summary (total count by severity)
- Error timeline chart
- Detailed error list with timestamps
- Error clustering and patterns

**Use when:** You want to identify when resources became unstable or started erroring.

### Code Deployment Correlation Report

Focus on deployments and their correlation with errors:

```bash
POST /api/v1/reports/generate
{
  "report_type": "code_deployment_correlation",
  "resource_id": "api-service-prod",
  "time_range_hours": 96
}
```

**Sections included:**
- Deployments overview
- Deployment and error correlation chart
- Code changes details (commit SHA, version)
- Stability analysis (success rate, errors per deployment)
- Post-deployment error analysis

**Use when:** You want to understand if deployments are causing stability issues.

### Comprehensive Report

Combines all report types into one:

```bash
POST /api/v1/reports/generate
{
  "report_type": "comprehensive",
  "resource_id": "load-balancer-prod",
  "time_range_hours": 48
}
```

**Sections included:**
- Resource overview
- Health metrics
- Changes overview and distribution
- Error summary and timeline
- Deployment correlation
- Stability analysis

**Use when:** You want a complete picture of a resource's health, changes, and stability.

## Configuration Options

### Time Range

Control how far back to look for data:

```json
{
  "time_range_hours": 24  // 1-168 hours (1 hour to 7 days)
}
```

### Include Charts

Control whether to include chart data:

```json
{
  "include_charts": true  // Default: true
}
```

Charts are returned in a format-agnostic way that can be rendered by various frontends (matplotlib, plotly, Chart.js, D3.js, etc.).

### Error and Change Limits

Control the maximum number of items to include:

```json
{
  "max_errors": 50,   // Default: 50, max: 500
  "max_changes": 20   // Default: 20, max: 100
}
```

### Detail Levels

Control what details to include:

```json
{
  "include_error_details": true,   // Include detailed error information
  "include_change_details": true,  // Include detailed change information
  "include_code_changes": true     // Include code change details
}
```

## Use Cases

### Use Case 1: Post-Incident Analysis

**Scenario:** An incident occurred, and you need to understand what happened.

**Solution:**
```bash
POST /api/v1/reports/generate
{
  "report_type": "comprehensive",
  "resource_id": "affected-resource-id",
  "time_range_hours": 24,
  "include_charts": true
}
```

**What you get:**
- Complete timeline of events
- Changes that were made before the incident
- Error patterns leading up to the incident
- Deployments that may have triggered issues
- Correlation analysis to identify root cause

### Use Case 2: Deployment Impact Assessment

**Scenario:** You deployed new code and want to see if it affected stability.

**Solution:**
```bash
POST /api/v1/reports/generate
{
  "report_type": "code_deployment_correlation",
  "resource_id": "deployed-service-id",
  "time_range_hours": 8
}
```

**What you get:**
- Deployment timeline
- Errors that occurred after deployment
- Stability metrics (deployment success rate)
- Post-deployment error rate analysis

### Use Case 3: Resource Health Monitoring

**Scenario:** You want to monitor a critical resource's health over time.

**Solution:**
```bash
POST /api/v1/reports/resource/critical-database-id?report_type=resource_health&time_range_hours=48
```

**What you get:**
- Health metrics trend (CPU, memory, performance)
- Recent errors affecting the resource
- Status changes
- Early warning indicators

### Use Case 4: Change Management Review

**Scenario:** You want to review all changes made in the last week.

**Solution:**
```bash
POST /api/v1/reports/generate
{
  "report_type": "change_impact",
  "time_range_hours": 168
}
```

**What you get:**
- All changes in the time window
- Distribution by type and risk level
- Impact assessment for each change
- Recommendations for high-risk changes

## Chart Data Format

Reports include chart data in a format-agnostic structure that can be rendered by any visualization library:

```json
{
  "type": "line",
  "title": "Error Timeline",
  "x_label": "Time",
  "y_label": "Error Count",
  "data": {
    "labels": ["2024-11-01 10:00", "2024-11-01 11:00", ...],
    "datasets": [
      {
        "label": "Total Errors",
        "data": [5, 12, 8, ...],
        "color": "red"
      },
      {
        "label": "Critical Severity",
        "data": [2, 5, 3, ...],
        "color": "#dc3545"
      }
    ]
  }
}
```

### Chart Types

- **line** - Time series data (errors, metrics over time)
- **bar** - Categorical data (changes by type)
- **pie** - Distribution data (risk levels)
- **combo** - Mixed types (deployments as bars, errors as line)

### Rendering Charts

The chart data can be rendered using your preferred visualization library:

**Chart.js:**
```javascript
new Chart(ctx, {
  type: chart.type,
  data: chart.data,
  options: { ... }
});
```

**Plotly:**
```python
import plotly.graph_objects as go

fig = go.Figure()
for dataset in chart['data']['datasets']:
    fig.add_trace(go.Scatter(
        x=chart['data']['labels'],
        y=dataset['data'],
        name=dataset['label']
    ))
```

**Matplotlib:**
```python
import matplotlib.pyplot as plt

for dataset in chart['data']['datasets']:
    plt.plot(
        chart['data']['labels'],
        dataset['data'],
        label=dataset['label'],
        color=dataset['color']
    )
plt.xlabel(chart['x_label'])
plt.ylabel(chart['y_label'])
plt.legend()
```

## Best Practices

### 1. Choose the Right Report Type

- Use **resource_health** for performance monitoring
- Use **change_impact** for change reviews
- Use **error_timeline** for debugging error spikes
- Use **code_deployment_correlation** for deployment validation
- Use **comprehensive** for incident analysis

### 2. Set Appropriate Time Ranges

- **Short term (1-24 hours):** Recent incidents, immediate issues
- **Medium term (24-72 hours):** Trend analysis, deployment impact
- **Long term (72-168 hours):** Pattern identification, weekly reviews

### 3. Use Resource-Specific Reports

Always specify a `resource_id` when analyzing a specific resource:

```json
{
  "resource_id": "specific-resource-id"
}
```

For system-wide reports, omit the `resource_id`.

### 4. Limit Data Volume

Use `max_errors` and `max_changes` to control report size:

```json
{
  "max_errors": 20,     // For focused analysis
  "max_changes": 10     // For recent changes only
}
```

### 5. Automate Report Generation

Schedule regular report generation for key resources:

```bash
# Daily health check
curl -X POST /api/v1/reports/resource/critical-db-id?report_type=resource_health&time_range_hours=24

# Weekly deployment review
curl -X POST /api/v1/reports/generate \
  -d '{"report_type":"code_deployment_correlation","time_range_hours":168}'
```

## Integration Examples

### Python Integration

```python
import requests

def generate_incident_report(resource_id, hours=24):
    """Generate comprehensive incident report."""
    response = requests.post(
        "http://localhost:8000/api/v1/reports/generate",
        json={
            "report_type": "comprehensive",
            "resource_id": resource_id,
            "time_range_hours": hours,
            "include_charts": True
        }
    )
    return response.json()

# Use it
report = generate_incident_report("aks-cluster-prod", 48)
print(f"Report: {report['title']}")
print(f"Summary: {report['summary']}")

# Access sections
for section in report['sections']:
    print(f"\n{section['title']}")
    print(section['content'])
```

### Bash/cURL Integration

```bash
#!/bin/bash
# Generate daily report for critical resources

RESOURCES=("db-prod" "api-gateway" "load-balancer")

for resource in "${RESOURCES[@]}"; do
  echo "Generating report for $resource..."
  curl -X POST "http://localhost:8000/api/v1/reports/resource/$resource?report_type=resource_health&time_range_hours=24" \
    -o "reports/$resource-$(date +%Y%m%d).json"
done
```

### JavaScript/TypeScript Integration

```typescript
async function generateReport(
  resourceId: string,
  reportType: string = 'comprehensive'
): Promise<Report> {
  const response = await fetch('/api/v1/reports/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      report_type: reportType,
      resource_id: resourceId,
      time_range_hours: 48,
      include_charts: true
    })
  });
  
  return await response.json();
}

// Usage
const report = await generateReport('api-service-prod');
console.log(report.title);

// Render charts
report.sections.forEach(section => {
  if (section.section_type === 'chart') {
    section.charts.forEach(chart => {
      renderChart(chart);
    });
  }
});
```

## Troubleshooting

### Issue: Report generation is slow

**Solution:** 
- Reduce `time_range_hours`
- Reduce `max_errors` and `max_changes`
- Set `include_charts: false` if charts aren't needed

### Issue: Report is too large

**Solution:**
- Use specific report types instead of comprehensive
- Reduce time range
- Set lower limits for errors and changes

### Issue: Missing data in report

**Solution:**
- Check that the resource_id is correct
- Verify data exists in Neo4j for the time range
- Ensure error replay and change management are configured

### Issue: Charts not rendering

**Solution:**
- Verify chart data structure is correct
- Check that the frontend visualization library is installed
- Review chart type compatibility with your renderer

## Related Documentation

- [Change Management Guide](CHANGE_MANAGEMENT_GUIDE.md)
- [Error Replay Guide](ERROR_REPLAY_GUIDE.md)
- [Enhanced Risk Analysis Guide](ENHANCED_RISK_ANALYSIS.md)
- [API Documentation](../src/topdeck/api/routes/reporting.py)

## Support

For issues or questions:
- Create an [Issue](https://github.com/MattVerwey/TopDeck/issues)
- Check [Documentation](https://github.com/MattVerwey/TopDeck/tree/main/docs)
