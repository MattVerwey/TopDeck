# SLA/SLO Management

## Overview

The SLA/SLO Management feature allows you to define Service Level Agreements (SLAs) for your services and automatically calculate Service Level Objectives (SLOs) with appropriate safety margins. This helps ensure your services meet customer commitments while providing operational visibility into error budgets and availability.

## Concepts

### SLA (Service Level Agreement)
An SLA is your commitment to customers regarding service availability and performance. For example, a 99% uptime SLA means your service should be available 99% of the time.

### SLO (Service Level Objective)
An SLO is your internal target, set stricter than the SLA to provide a safety margin. This ensures you meet your SLA commitments even when unexpected issues occur.

**Example SLA to SLO Conversions:**
- SLA 99% → SLO 99.9% (10x stricter error budget)
- SLA 99.9% → SLO 99.98% (5x stricter error budget)
- SLA 99.99% → SLO 99.998% (5x stricter error budget)

### Error Budget
The error budget is the acceptable amount of downtime or errors within your SLA target. For example:
- 99% SLA = 1% error budget = 432 minutes per month of allowed downtime
- 99.9% SLA = 0.1% error budget = 43.2 minutes per month of allowed downtime
- 99.99% SLA = 0.01% error budget = 4.32 minutes per month of allowed downtime

## Features

### SLA Configuration
- **Create SLAs**: Define SLA targets for services with default 99% uptime
- **Service Association**: Link resources to services that affect the SLA
- **Custom Targets**: Set any SLA percentage between 0% and 100%
- **Description**: Add context and notes to each SLA configuration

### Monitoring & Visibility
- **Dashboard Summary**: View total SLAs, meeting SLA count, and at-risk services
- **Error Budget Tracking**: Visual indicators showing remaining error budget
- **Resource Status**: See which resources are meeting or failing SLO targets
- **Uptime Metrics**: Current uptime percentage for each service

### Visual Indicators
- **Status Icons**: Quick visual indication of SLA compliance (✓, ⚠, ✗)
- **Progress Bars**: Error budget consumption visualization
- **Color Coding**: 
  - Green: Meeting SLA with healthy error budget
  - Blue: Meeting SLA but consuming error budget
  - Orange: Meeting SLA but at risk (>80% error budget consumed)
  - Red: Below SLA target

## API Endpoints

### SLA Configuration Management

#### Create SLA Configuration
```http
POST /api/v1/sla/configs
Content-Type: application/json

{
  "name": "Production API SLA",
  "description": "SLA for production API service",
  "sla_percentage": 99.9,
  "service_name": "api-service",
  "resources": ["resource-id-1", "resource-id-2"]
}
```

#### List SLA Configurations
```http
GET /api/v1/sla/configs
GET /api/v1/sla/configs?service_name=api-service
```

#### Get SLA Configuration
```http
GET /api/v1/sla/configs/{sla_id}
```

#### Update SLA Configuration
```http
PUT /api/v1/sla/configs/{sla_id}
Content-Type: application/json

{
  "name": "Updated SLA",
  "sla_percentage": 99.95,
  ...
}
```

#### Delete SLA Configuration
```http
DELETE /api/v1/sla/configs/{sla_id}
```

### SLO Calculation

#### Calculate SLO from SLA
```http
GET /api/v1/sla/configs/{sla_id}/slo
```

Response:
```json
{
  "sla_id": "sla-1",
  "sla_percentage": 99.0,
  "slo_percentage": 99.9,
  "error_budget_percentage": 1.0,
  "error_budget_minutes_per_month": 432.0,
  "error_budget_minutes_per_year": 5256.0,
  "calculated_at": "2025-11-02T10:15:00Z"
}
```

### Error Budget Monitoring

#### Get Error Budget Status
```http
GET /api/v1/sla/configs/{sla_id}/error-budget?period_hours=24
```

Response:
```json
{
  "sla_id": "sla-1",
  "service_name": "api-service",
  "sla_percentage": 99.0,
  "slo_percentage": 99.9,
  "current_uptime_percentage": 99.95,
  "error_budget_percentage": 1.0,
  "error_budget_remaining_percentage": 95.0,
  "error_budget_consumed_percentage": 5.0,
  "is_within_budget": true,
  "resources_status": [
    {
      "resource_id": "res-1",
      "uptime_percentage": 99.95,
      "meets_slo": true,
      "error_count": 5
    }
  ],
  "period_start": "2025-11-01T00:00:00Z",
  "period_end": "2025-11-02T00:00:00Z",
  "calculated_at": "2025-11-02T10:15:00Z"
}
```

### Resource Availability

#### Get Resource Availability Metrics
```http
GET /api/v1/sla/resources/{resource_id}/availability?period_hours=24&slo_percentage=99.9
```

Response:
```json
{
  "resource_id": "res-1",
  "resource_name": "API Gateway",
  "resource_type": "service",
  "uptime_percentage": 99.95,
  "downtime_minutes": 7.2,
  "error_count": 12,
  "success_rate": 0.9995,
  "meets_slo": true,
  "period_start": "2025-11-01T00:00:00Z",
  "period_end": "2025-11-02T00:00:00Z"
}
```

## Usage Examples

### Creating an SLA for a Critical Service

1. Navigate to **SLA/SLO** in the sidebar
2. Click **Add SLA** button
3. Fill in the form:
   - **SLA Name**: "Production API Uptime"
   - **Description**: "99.9% uptime for customer-facing API"
   - **Service Name**: "api-production"
   - **SLA Target**: 99.9
   - **Resources**: Select all API gateway and backend services
4. Click **Create**

The system will automatically:
- Calculate the SLO (99.98% in this case)
- Set up error budget tracking (43.2 minutes per month)
- Monitor resource availability
- Alert when error budget is being consumed

### Monitoring Error Budget

The main SLA/SLO page shows:
- **Total SLAs**: Number of configured SLAs
- **Meeting SLA**: How many services are within their SLA targets
- **At Risk**: Services consuming >80% of error budget

For each SLA configuration, you can see:
- Current uptime percentage
- Error budget remaining (as a percentage and progress bar)
- Status indicator (healthy, at risk, or failing)
- Number of associated resources
- Individual resource status

### Responding to SLA Violations

When a service exceeds its error budget:
1. The status indicator turns red
2. Error budget shows >100% consumed
3. Review the resource status table to identify failing components
4. Use the Risk Analysis page to understand dependencies
5. Implement fixes or request additional error budget allocation

## Best Practices

1. **Set Realistic SLAs**: Don't promise 100% uptime - it's impossible to achieve
2. **Default to 99%**: Good starting point for most services
3. **Use Error Budget**: The error budget is meant to be used for deployments and maintenance
4. **Monitor Trends**: Watch error budget consumption over time
5. **Assign Resources Carefully**: Only include resources that directly impact service availability
6. **Review Regularly**: Update SLAs as services evolve and improve

## Integration with Other Features

### Risk Analysis
- Use SLA data to prioritize risk mitigation
- Identify Single Points of Failure (SPOFs) affecting SLAs
- Calculate blast radius impact on SLA compliance

### Change Management
- Check error budget before making changes
- Schedule maintenance during low-impact windows
- Track change impact on SLA compliance

### Monitoring
- Integrate with existing monitoring systems
- Alert when approaching error budget limits
- Track availability metrics for SLA reporting

## Future Enhancements

- Real-time monitoring integration (Prometheus, Datadog, etc.)
- Automatic alerting when SLA is at risk
- Historical SLA compliance reporting
- Multi-region SLA configurations
- Custom error budget burn rate alerts
- Integration with incident management systems
