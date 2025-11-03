# Risk Analysis Improvements

## Overview

This document describes the new enhanced risk analysis capabilities added to TopDeck. These improvements provide deeper insights into risk management with time-awareness, financial impact analysis, and trend tracking.

---

## 🕐 Time-Aware Risk Scoring

### What is it?

Time-aware risk scoring adjusts risk assessments based on **when** a deployment or change is scheduled. Not all times are created equal - deploying during peak business hours on a weekday is significantly riskier than deploying at 2 AM on Sunday.

### Key Features

- **Day Type Recognition**: Weekdays, weekends, holidays
- **Time Window Detection**: Business hours, peak hours, low traffic periods, maintenance windows
- **Risk Multipliers**: Automatic adjustment of base risk scores (0.2x - 2.0x)
- **Optimal Window Suggestions**: Recommends best deployment times in the next 7 days

### API Usage

#### Get Time-Aware Risk Assessment

```bash
curl "http://localhost:8000/api/v1/risk/resources/db-prod-001/time-aware-risk?deployment_time=2024-11-03T14:00:00Z"
```

**Response:**
```json
{
  "resource_id": "db-prod-001",
  "resource_name": "Production Database",
  "base_risk_score": 65.0,
  "adjusted_risk_score": 84.5,
  "time_multiplier": 1.3,
  "timing_factors": [
    "Weekday deployment increases risk (+30%)",
    "Business hours increase risk (+20%)"
  ],
  "recommendation": "⚠️ Suboptimal time for deployment - elevated risk",
  "day_type": "weekday",
  "time_window": "business_hours",
  "optimal_deployment_windows": [
    {
      "datetime": "2024-11-03T02:00:00",
      "risk_multiplier": 0.42,
      "day_type": "weekend",
      "time_window": "low_traffic",
      "recommendation": "✅ Excellent time for deployment - minimal risk"
    }
  ]
}
```

### Configuration Options

Time-aware scoring can be customized:

```python
from datetime import time
from topdeck.analysis.risk import TimeAwareRiskScorer

# Custom business hours
custom_scorer = TimeAwareRiskScorer(
    business_hours={
        "start": time(9, 0),  # 9 AM
        "end": time(17, 0),   # 5 PM
    },
    peak_hours={
        "start": time(11, 0),  # 11 AM
        "end": time(15, 0),    # 3 PM
    },
    maintenance_windows=[
        {
            "start": time(2, 0),   # 2 AM
            "end": time(4, 0),     # 4 AM
        }
    ],
    holidays=[
        datetime(2024, 12, 25),  # Christmas
        datetime(2024, 1, 1),     # New Year's
    ]
)
```

### Risk Multiplier Guidelines

| Time Window | Day Type | Typical Multiplier | Impact |
|------------|----------|-------------------|---------|
| Peak Hours | Weekday | 1.5x - 2.0x | 🚨 High Risk |
| Business Hours | Weekday | 1.2x - 1.5x | ⚠️ Elevated Risk |
| Off Hours | Weekday | 0.9x - 1.1x | 📊 Moderate Risk |
| Low Traffic | Any | 0.5x - 0.7x | 👍 Low Risk |
| Maintenance Window | Any | 0.3x - 0.5x | ✅ Minimal Risk |
| Any | Weekend | 0.7x | 👍 Reduced Risk |
| Any | Holiday | 0.5x | ✅ Minimal Risk |

---

## 💰 Cost Impact Analysis

### What is it?

Cost impact analysis quantifies the **financial consequences** of resource failures. Instead of just knowing that "database failure affects 5 services," you now know "database failure costs $50,000 per hour."

### Cost Components

1. **Revenue Loss**: Direct revenue impact from service unavailability
2. **Engineering Time**: Cost of incident response and troubleshooting
3. **Customer Support**: Cost of handling user complaints and support tickets
4. **SLA Penalties**: Contractual penalties for service level violations
5. **Reputation Damage**: Intangible costs (customer churn, brand damage)
6. **Recovery Costs**: Infrastructure restoration and data recovery

### API Usage

#### Calculate Cost Impact

```bash
curl "http://localhost:8000/api/v1/risk/resources/api-gateway-prod/cost-impact?\
downtime_hours=2&\
affected_users=50000&\
is_revenue_generating=true&\
has_sla=true&\
industry=ecommerce&\
annual_revenue=10000000"
```

**Response:**
```json
{
  "resource_id": "api-gateway-prod",
  "resource_name": "Production API Gateway",
  "total_cost": 87350.50,
  "cost_breakdown": {
    "revenue_loss": 50000.00,
    "engineering_time": 900.00,
    "customer_support": 200.00,
    "sla_penalties": 20000.00,
    "reputation_damage": 15245.15,
    "recovery_costs": 1005.35
  },
  "hourly_impact_rate": 43675.25,
  "affected_users": 50000,
  "confidence_level": "high",
  "assumptions": [
    "Revenue loss based on 50000 users at $0.50/user/hour",
    "Engineering cost based on 3 engineers at $150/hour",
    "Support cost based on 2 staff at $50/hour",
    "SLA penalty at 1.0% of annual revenue per hour",
    "Reputation damage estimated at 30% of tangible costs",
    "Recovery costs estimated for api_gateway"
  ],
  "annual_risk_cost": {
    "expected_annual_cost": 8735.05,
    "min_annual_cost": 4367.53,
    "max_annual_cost": 13102.58,
    "expected_downtime_hours": 0.20,
    "hourly_impact_rate": 43675.25,
    "recommendations": [
      "📊 Consider cost-benefit analysis of high-availability architecture"
    ]
  }
}
```

### Industry Multipliers

Different industries have different cost profiles:

| Industry | Multiplier | Rationale |
|----------|-----------|-----------|
| Fintech | 3.0x | Regulatory compliance, trust is critical |
| Healthcare | 2.5x | Patient safety, HIPAA compliance |
| E-commerce | 2.0x | Direct revenue dependency |
| Gaming | 1.8x | User engagement and retention critical |
| SaaS | 1.5x | Subscription-based, churn risk |
| Media | 1.3x | Content delivery focused |
| Enterprise | 1.2x | B2B impacts, relationship damage |
| Default | 1.0x | General use case |

### Mitigation ROI Analysis

Compare the cost of implementing mitigations vs. the risk:

```python
from topdeck.analysis.risk import CostImpactAnalyzer

analyzer = CostImpactAnalyzer(industry="fintech", annual_revenue=10_000_000)

current_risk_cost = 100_000  # $100K annual risk

mitigations = [
    {
        "name": "Multi-AZ deployment",
        "implementation_cost": 50_000,
        "annual_operational_cost": 20_000,
        "risk_reduction_percentage": 90,  # 90% reduction
    },
    {
        "name": "Enhanced monitoring",
        "implementation_cost": 5_000,
        "annual_operational_cost": 2_000,
        "risk_reduction_percentage": 30,  # 30% reduction
    },
]

results = analyzer.compare_mitigation_costs(current_risk_cost, mitigations)
```

**Output:**
```json
[
  {
    "mitigation": "Multi-AZ deployment",
    "implementation_cost": 50000,
    "annual_operational_cost": 20000,
    "annual_savings": 90000,
    "roi_percentage": 28.57,
    "payback_months": 6.7,
    "net_benefit_year_1": 20000,
    "recommended": true
  },
  {
    "mitigation": "Enhanced monitoring",
    "implementation_cost": 5000,
    "annual_operational_cost": 2000,
    "annual_savings": 30000,
    "roi_percentage": 328.57,
    "payback_months": 2.0,
    "net_benefit_year_1": 23000,
    "recommended": true
  }
]
```

### Custom Cost Rates

Default rates can be customized per organization:

```python
custom_rates = {
    "revenue_per_user_hour": 1.50,  # $1.50 per user per hour
    "engineering_hour_rate": 200.0,  # $200/hour
    "support_hour_rate": 75.0,       # $75/hour
    "avg_engineers_per_incident": 5,
    "avg_support_per_incident": 3,
    "sla_penalty_rate_per_hour": 0.02,  # 2% per hour
    "reputation_damage_multiplier": 0.5,  # 50%
}

analyzer = CostImpactAnalyzer(rates=custom_rates)
```

---

## 📈 Risk Trend Analysis

### What is it?

Risk trend analysis tracks how risk changes over time, detecting patterns, anomalies, and predicting future risk. This helps identify resources that are becoming more unstable or problematic.

### Key Features

- **Trend Direction**: Improving, degrading, stable, or volatile
- **Anomaly Detection**: Identifies unusual risk spikes using statistical methods
- **Future Prediction**: Simple linear prediction of future risk
- **Portfolio Analysis**: Compare trends across multiple resources
- **Contributing Factors**: Identifies what's driving risk changes

### API Usage

#### 1. Create Risk Snapshot

First, capture current risk state:

```bash
curl -X POST "http://localhost:8000/api/v1/risk/resources/web-app-prod/trend-snapshot"
```

**Response:**
```json
{
  "resource_id": "web-app-prod",
  "snapshot": {
    "timestamp": "2024-11-03T18:00:00Z",
    "risk_score": 45.5,
    "risk_level": "medium",
    "factors": {
      "dependencies_count": 5,
      "dependents_count": 8,
      "is_spof": false
    }
  },
  "message": "Snapshot created successfully. Store this for trend analysis."
}
```

**Important**: Store snapshots in your database or time-series store for trend analysis.

#### 2. Analyze Trend

After collecting multiple snapshots over time:

```bash
curl -X POST "http://localhost:8000/api/v1/risk/resources/web-app-prod/analyze-trend" \
  -H "Content-Type: application/json" \
  -d '{
    "snapshots": [
      {
        "timestamp": "2024-10-01T00:00:00Z",
        "risk_score": 30.0,
        "risk_level": "low",
        "factors": {"dependencies_count": 3, "dependents_count": 5}
      },
      {
        "timestamp": "2024-10-08T00:00:00Z",
        "risk_score": 35.0,
        "risk_level": "medium",
        "factors": {"dependencies_count": 4, "dependents_count": 6}
      },
      {
        "timestamp": "2024-10-15T00:00:00Z",
        "risk_score": 42.0,
        "risk_level": "medium",
        "factors": {"dependencies_count": 5, "dependents_count": 7}
      },
      {
        "timestamp": "2024-10-22T00:00:00Z",
        "risk_score": 48.0,
        "risk_level": "medium",
        "factors": {"dependencies_count": 5, "dependents_count": 8}
      }
    ]
  }'
```

**Response:**
```json
{
  "resource_id": "web-app-prod",
  "resource_name": "Production Web App",
  "current_risk_score": 48.0,
  "previous_risk_score": 42.0,
  "trend_direction": "degrading",
  "trend_severity": "moderate",
  "change_percentage": 14.29,
  "contributing_factors": [
    "dependencies_count increased from 4 to 5",
    "dependents_count increased from 7 to 8"
  ],
  "recommendations": [
    "⚠️ Risk is increasing - monitor closely",
    "Key factors: dependencies_count increased from 4 to 5, dependents_count increased from 7 to 8"
  ],
  "anomalies": [],
  "prediction": {
    "predicted_risk_score": 54.3,
    "days_ahead": 7,
    "trend_slope": 0.9,
    "confidence": "high",
    "current_risk": 48.0,
    "interpretation": "Risk expected to increase moderately"
  }
}
```

### Trend Directions

| Direction | Description | Action Required |
|-----------|-------------|-----------------|
| **Improving** | Risk decreasing over time | ✅ Continue current practices |
| **Stable** | Risk relatively constant | 📊 Maintain monitoring |
| **Degrading** | Risk increasing over time | ⚠️ Investigate and address |
| **Volatile** | Risk fluctuating significantly | 🔍 Find root cause of instability |

### Anomaly Detection

Automatically detects unusual risk spikes using z-scores:

- **Z-score > 2**: Medium severity anomaly
- **Z-score > 3**: High severity anomaly

Example anomaly:
```json
{
  "timestamp": "2024-10-29T00:00:00Z",
  "risk_score": 85.0,
  "expected_risk": 48.0,
  "deviation": 37.0,
  "z_score": 3.2,
  "severity": "high"
}
```

### Portfolio Comparison

Compare trends across multiple resources:

```python
from topdeck.analysis.risk import RiskTrendAnalyzer, RiskSnapshot

analyzer = RiskTrendAnalyzer()

# Analyze trends for multiple resources
trends = []
for resource_data in resources:
    trend = analyzer.analyze_trend(
        resource_data["id"],
        resource_data["name"],
        resource_data["snapshots"]
    )
    trends.append(trend)

# Compare across portfolio
comparison = analyzer.compare_resources_trends(trends)
```

**Output:**
```json
{
  "total_resources": 10,
  "improving_count": 3,
  "degrading_count": 4,
  "stable_count": 2,
  "volatile_count": 1,
  "critical_trends": [
    {
      "resource_id": "api-gateway-prod",
      "resource_name": "Production API Gateway",
      "current_risk": 78.5,
      "change_percentage": 35.2,
      "trend_direction": "degrading"
    }
  ],
  "overall_health": "fair",
  "recommendations": [
    "⚠️ 4 resources showing degrading risk - consider infrastructure review",
    "📊 1 resources showing volatile risk - investigate for instability"
  ]
}
```

---

## Best Practices

### 1. Regular Snapshot Collection

- **Frequency**: Daily for production resources, weekly for non-critical
- **Automation**: Set up cron jobs or scheduled tasks
- **Storage**: Use time-series database (InfluxDB, Prometheus, TimescaleDB)

### 2. Cost Analysis Integration

- **Deployment Gates**: Block high-cost risky deployments
- **Budget Planning**: Use annual risk costs for infrastructure budgeting
- **Justification**: Use ROI analysis to justify infrastructure investments

### 3. Time-Aware Deployments

- **CI/CD Integration**: Check time-aware risk before deployments
- **Automated Scheduling**: Find and schedule optimal deployment windows
- **Emergency Override**: Allow bypass for critical fixes with approval

### 4. Alerting Thresholds

Recommended alert thresholds:

```yaml
alerts:
  risk_score:
    warning: 60
    critical: 80
  
  cost_impact:
    hourly_warning: 5000  # $5K/hour
    hourly_critical: 20000  # $20K/hour
  
  trend:
    degrading_percentage: 20  # Alert if risk increases >20%
    anomaly_z_score: 2.5
```

### 5. Documentation

Document your organization's:
- Custom cost rates
- Business hours and maintenance windows
- Industry-specific multipliers
- Risk tolerance thresholds

---

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# GitHub Actions example
- name: Check Deployment Risk
  run: |
    RISK_RESPONSE=$(curl -s "http://topdeck/api/v1/risk/resources/${RESOURCE_ID}/time-aware-risk")
    RISK_SCORE=$(echo $RISK_RESPONSE | jq -r '.adjusted_risk_score')
    
    if (( $(echo "$RISK_SCORE > 75" | bc -l) )); then
      echo "::error::Risk score too high for deployment: $RISK_SCORE"
      exit 1
    fi
```

### Monitoring Integration

```python
# Prometheus alerting example
from topdeck.analysis.risk import RiskTrendAnalyzer, RiskSnapshot
import prometheus_client as prom

# Export risk metrics to Prometheus
risk_gauge = prom.Gauge('resource_risk_score', 'Current risk score', ['resource_id'])
trend_gauge = prom.Gauge('resource_risk_trend', 'Risk trend direction', ['resource_id', 'direction'])

def update_metrics(resource_id, snapshot):
    risk_gauge.labels(resource_id=resource_id).set(snapshot.risk_score)
    
    trend = analyzer.analyze_trend(resource_id, "Resource", snapshots)
    trend_gauge.labels(
        resource_id=resource_id,
        direction=trend.trend_direction.value
    ).set(1)
```

---

## Limitations and Future Enhancements

### Current Limitations

1. **Historical Data**: Requires manual snapshot collection and storage
2. **Prediction Accuracy**: Simple linear regression (not ML-based)
3. **Cost Estimation**: Based on industry averages, not actual SLA data
4. **Real-time Integration**: No automatic monitoring data integration

### Planned Enhancements

1. **Automatic Snapshot Collection**: Background job to capture snapshots
2. **Advanced Predictions**: ML-based risk forecasting
3. **Live Monitoring Integration**: Real-time health metric adjustments
4. **Business Criticality Tags**: Allow tagging resources with business context
5. **Report Generation**: Automated risk trend reports
6. **Alert Integration**: Built-in alerting for risk thresholds

---

## Summary

The improved risk analysis provides three powerful new capabilities:

1. **Time-Aware Scoring** 🕐: Deploy at the right time to minimize risk
2. **Cost Impact** 💰: Understand financial consequences of failures
3. **Trend Analysis** 📈: Track risk evolution and predict future problems

Together, these features enable proactive risk management, better deployment scheduling, and data-driven infrastructure investment decisions.
