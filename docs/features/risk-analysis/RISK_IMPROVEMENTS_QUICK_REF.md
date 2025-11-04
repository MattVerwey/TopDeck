# Risk Analysis Improvements - Quick Reference

## 🕐 Time-Aware Risk Scoring

### Quick Start
```bash
# Get risk with time adjustment (defaults to now)
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/time-aware-risk"

# Check specific deployment time
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/time-aware-risk?deployment_time=2024-11-03T14:00:00Z"
```

### Risk Multipliers Cheat Sheet
- **Peak Hours + Weekday**: 1.5x - 2.0x (🚨 Avoid)
- **Business Hours + Weekday**: 1.2x - 1.5x (⚠️ Caution)
- **Weekend**: 0.7x (👍 Good)
- **Low Traffic (2-5 AM)**: 0.5x - 0.7x (✅ Best)
- **Maintenance Window**: 0.3x - 0.5x (✅ Optimal)
- **Holiday**: 0.5x (✅ Excellent)

### Response Keys
- `adjusted_risk_score`: Final risk after time adjustment
- `time_multiplier`: The multiplier applied (0.2 - 2.0)
- `optimal_deployment_windows`: Top 5 best times in next 7 days

---

## 💰 Cost Impact Analysis

### Quick Start
```bash
# Basic cost calculation
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/cost-impact?\
downtime_hours=2&\
affected_users=10000"

# Full analysis with SLA
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/cost-impact?\
downtime_hours=2&\
affected_users=10000&\
is_revenue_generating=true&\
has_sla=true&\
industry=fintech&\
annual_revenue=10000000"
```

### Industry Multipliers
| Industry | Multiplier | Example Impact |
|----------|-----------|----------------|
| fintech | 3.0x | £1K → £3K |
| healthcare | 2.5x | £1K → £2.5K |
| ecommerce | 2.0x | £1K → £2K |
| gaming | 1.8x | £1K → £1.8K |
| saas | 1.5x | £1K → £1.5K |
| media | 1.3x | £1K → £1.3K |
| enterprise | 1.2x | £1K → £1.2K |
| default | 1.0x | £1K → £1K |

### Cost Breakdown Components
1. `revenue_loss`: Direct revenue impact
2. `engineering_time`: Incident response cost
3. `customer_support`: Support ticket handling
4. `sla_penalties`: Contract penalties
5. `reputation_damage`: Intangible costs (30% of tangible)
6. `recovery_costs`: Infrastructure restoration

### Quick Estimates
- **Small App**: ~£500-£2K/hour downtime
- **Medium Service**: ~£5K-£20K/hour downtime  
- **Critical System**: ~£50K-£200K/hour downtime
- **Enterprise Platform**: £100K-£1M+/hour downtime

---

## 📈 Risk Trend Analysis

### Quick Start
```bash
# Step 1: Create snapshot (do this daily/weekly)
curl -X POST "http://localhost:8000/api/v1/risk/resources/{resource-id}/trend-snapshot"

# Step 2: Analyze trend (after collecting multiple snapshots)
curl -X POST "http://localhost:8000/api/v1/risk/resources/{resource-id}/analyze-trend" \
  -H "Content-Type: application/json" \
  -d '{
    "snapshots": [
      {"timestamp": "2024-10-01T00:00:00Z", "risk_score": 30, "risk_level": "low", "factors": {}},
      {"timestamp": "2024-10-08T00:00:00Z", "risk_score": 35, "risk_level": "medium", "factors": {}},
      {"timestamp": "2024-10-15T00:00:00Z", "risk_score": 42, "risk_level": "medium", "factors": {}}
    ]
  }'
```

### Trend Directions
| Direction | Meaning | Action |
|-----------|---------|--------|
| `improving` | Risk ↓ | ✅ Good, continue |
| `stable` | Risk → | 📊 Monitor |
| `degrading` | Risk ↑ | ⚠️ Investigate |
| `volatile` | Risk ↕ | 🔍 Find root cause |

### Severity Levels
| Severity | Change % | Impact |
|----------|----------|--------|
| `minor` | < 5% | Minimal |
| `moderate` | 5-15% | Notable |
| `significant` | 15-30% | Serious |
| `critical` | > 30% | Urgent |

### Anomaly Detection
- **Z-score > 2.0**: Medium severity anomaly
- **Z-score > 3.0**: High severity anomaly

### Response Keys
- `trend_direction`: improving/stable/degrading/volatile
- `change_percentage`: % change since previous snapshot
- `anomalies`: List of detected unusual spikes
- `prediction`: 7-day forecast with confidence level

---

## Integration Examples

### CI/CD Gate
```yaml
# GitHub Actions
- name: Check Risk
  run: |
    RISK=$(curl -s "http://topdeck/api/v1/risk/resources/${ID}/time-aware-risk" | jq '.adjusted_risk_score')
    if (( $(echo "$RISK > 75" | bc -l) )); then
      echo "Risk too high: $RISK"
      exit 1
    fi
```

### Scheduled Snapshot Collection
```bash
#!/bin/bash
# Cron: 0 2 * * * (daily at 2 AM)
for resource in $(get_critical_resources); do
  curl -X POST "http://topdeck/api/v1/risk/resources/$resource/trend-snapshot"
done
```

### Alert on High Cost
```python
response = requests.get(f"{base_url}/cost-impact?downtime_hours=1&affected_users=10000")
cost = response.json()["hourly_impact_rate"]

if cost > 10000:  # Alert if > £10K/hour
    send_alert(f"High cost impact: £{cost}/hour")
```

---

## Common Patterns

### Pattern 1: Pre-Deployment Check
```bash
# 1. Get time-aware risk
RISK_DATA=$(curl "http://topdeck/api/v1/risk/resources/${ID}/time-aware-risk")

# 2. Check if acceptable
RISK_SCORE=$(echo $RISK_DATA | jq '.adjusted_risk_score')
OPTIMAL_TIME=$(echo $RISK_DATA | jq -r '.optimal_deployment_windows[0].datetime')

# 3. Decide
if [ $RISK_SCORE -gt 75 ]; then
  echo "Suggest rescheduling to: $OPTIMAL_TIME"
fi
```

### Pattern 2: Cost Justification
```bash
# 1. Calculate current risk cost
COST_DATA=$(curl "http://topdeck/api/v1/risk/resources/${ID}/cost-impact?downtime_hours=2&affected_users=50000")
ANNUAL_COST=$(echo $COST_DATA | jq '.annual_risk_cost.expected_annual_cost')

# 2. Compare with mitigation cost
# If annual_cost (£100K) > mitigation_cost (£50K), it's justified
```

### Pattern 3: Health Monitoring
```bash
#!/bin/bash
# Daily health check

for resource in $(get_all_resources); do
  # Create snapshot
  curl -X POST "http://topdeck/api/v1/risk/resources/$resource/trend-snapshot"
  
  # Get current risk
  CURRENT=$(curl -s "http://topdeck/api/v1/risk/resources/$resource" | jq '.risk_score')
  
  # Alert if high
  if (( $(echo "$CURRENT > 80" | bc -l) )); then
    send_alert "High risk on $resource: $CURRENT"
  fi
done
```

---

## Thresholds Reference

### Recommended Alert Thresholds
```yaml
risk_scores:
  warning: 60
  critical: 80

time_multipliers:
  avoid_deployment: 1.5  # Don't deploy if multiplier > 1.5x

cost_per_hour:
  warning: 5000   # £5K/hour
  critical: 20000  # £20K/hour

trend_change:
  warning: 15   # Alert if risk increases > 15%
  critical: 30  # Alert if risk increases > 30%

anomaly_detection:
  threshold: 2.5  # Z-score threshold
```

### Resource Type Benchmarks
| Type | Typical Risk | Critical Threshold |
|------|--------------|-------------------|
| Database | 60-70 | > 80 |
| API Gateway | 55-65 | > 75 |
| Cache | 40-50 | > 65 |
| Web App | 45-55 | > 70 |
| Storage | 35-45 | > 60 |

---

## Quick Troubleshooting

### High Time-Aware Risk
**Problem**: `adjusted_risk_score` too high  
**Solution**: Use `optimal_deployment_windows` to find better time

### Cost Seems Wrong
**Problem**: Cost estimates don't match expectations  
**Solution**: 
1. Check `industry` parameter (default vs specific)
2. Verify `annual_revenue` if using SLA penalties
3. Review `assumptions` in response
4. Consider custom rates (see full docs)

### No Trend Data
**Problem**: "Insufficient data for trend analysis"  
**Solution**: Need at least 2 snapshots, preferably 7+ for good analysis

### Anomaly False Positives
**Problem**: Too many anomalies detected  
**Solution**: Adjust `volatility_threshold` (default 15.0) or increase z-score threshold

---

## Resource-Specific Examples

### Database Deployment
```bash
# High-value, high-risk resource
curl "http://localhost:8000/api/v1/risk/resources/db-prod-001/time-aware-risk?deployment_time=2024-11-03T02:00:00Z"
# Expect: Low multiplier (0.5x), optimal time

curl "http://localhost:8000/api/v1/risk/resources/db-prod-001/cost-impact?downtime_hours=1&affected_users=100000&has_sla=true"
# Expect: High cost (£50K-£200K)
```

### Cache Update
```bash
# Lower risk, rebuild-able
curl "http://localhost:8000/api/v1/risk/resources/redis-cache-001/cost-impact?downtime_hours=0.5&affected_users=10000"
# Expect: Moderate cost (£2K-£10K)
```

### API Gateway Change
```bash
# High visibility, user-facing
curl "http://localhost:8000/api/v1/risk/resources/api-gateway-prod/time-aware-risk"
# Check time carefully - very sensitive to business hours
```

---

## Best Practices

1. **Always check time-aware risk** before deployments
2. **Calculate cost impact** for critical resources to justify investments
3. **Collect snapshots regularly** (daily for critical, weekly for others)
4. **Review trends monthly** to identify degrading resources
5. **Set up alerts** on risk thresholds
6. **Document your thresholds** and adjust based on experience
7. **Use cost analysis** for capacity planning and budgeting

---

## See Also

- [Full Documentation](RISK_ANALYSIS_IMPROVEMENTS.md) - Comprehensive guide
- [Enhanced Risk Analysis](ENHANCED_RISK_ANALYSIS.md) - Original features
- [Risk API Reference](../src/topdeck/api/routes/risk.py) - All endpoints
