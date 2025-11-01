# Enhanced ML-Based Confidence Scoring

## Overview

TopDeck's ML prediction system now includes an enhanced confidence scoring mechanism that provides transparent, multi-factor assessment of prediction reliability. This helps users understand how much they can trust each prediction.

## Confidence Levels

Predictions are assigned one of three confidence levels:

| Level | Score Range | Meaning | Action |
|-------|-------------|---------|--------|
| **HIGH** | ≥ 0.8 | Very reliable prediction | Act on the prediction |
| **MEDIUM** | 0.6 - 0.8 | Reasonably reliable | Review and consider acting |
| **LOW** | < 0.6 | Limited reliability | Gather more data or monitor |

## How Confidence is Calculated

Confidence is calculated using a weighted combination of four factors:

### 1. Feature Completeness (30% weight)

**What it measures:** How many features are available vs. expected.

- **High completeness:** All or most features are present (> 20 out of 30)
- **Low completeness:** Many features are missing (< 10 out of 30)

**Why it matters:** More features = more information = better predictions.

### 2. Feature Quality (30% weight)

**What it measures:** Whether feature values are valid and within expected ranges.

Feature validation rules:
- CPU/Memory usage: Must be between 0.0 and 1.0
- Standard deviations: Must be between 0.0 and 0.5
- Error rates: Must be between 0.0 and 1.0
- Latency: Must be positive
- Boolean features: Must be 0.0 or 1.0

**Why it matters:** Invalid data leads to unreliable predictions.

### 3. Data Recency (20% weight)

**What it measures:** How recent the historical data is.

| Days Since Last Event | Score | Interpretation |
|-----------------------|-------|----------------|
| < 7 days | 0.7 | Very recent, but might lack historical context |
| 7-30 days | 0.9 | Optimal - recent and contextual |
| 30-90 days | 0.8 | Still relevant |
| 90-180 days | 0.6 | Getting old |
| > 180 days | 0.5 | Very old or no historical data |

**Why it matters:** Recent patterns are more relevant for predicting near-term behavior.

### 4. Prediction Consistency (20% weight)

**What it measures:** Variance in metrics (low variance = consistent patterns).

| Average Std Dev | Score | Interpretation |
|-----------------|-------|----------------|
| < 0.1 | 1.0 | Very consistent - high confidence |
| 0.1 - 0.2 | 0.8 | Fairly consistent |
| 0.2 - 0.3 | 0.6 | Moderate variance |
| > 0.3 | 0.4 | High variance - unpredictable |

**Why it matters:** Consistent patterns are easier to predict accurately.

## Penalty for Minimal Data

If feature completeness is below 10% (< 3 features), the confidence score is halved. This prevents false confidence when we have very little information.

## Confidence Metrics API Response

When you make a prediction request, you'll receive detailed confidence metrics:

```json
{
  "resource_id": "sql-db-prod",
  "failure_probability": 0.65,
  "risk_level": "high",
  "confidence": "medium",
  "confidence_metrics": {
    "overall_score": 0.72,
    "confidence_level": "medium",
    "feature_completeness": 0.67,
    "feature_quality": 0.95,
    "data_recency": 0.8,
    "prediction_consistency": 0.75,
    "total_features": 20,
    "valid_features": 19,
    "missing_features": 10
  }
}
```

## Example Scenarios

### Scenario 1: High Confidence Prediction

```
Feature Completeness: 0.9 (27/30 features)
Feature Quality: 0.95 (all features valid)
Data Recency: 0.9 (20 days since last event)
Consistency: 0.85 (std dev = 0.15)

Overall Score: 0.9 * 0.3 + 0.95 * 0.3 + 0.9 * 0.2 + 0.85 * 0.2 = 0.905
Confidence: HIGH ✅
```

**Interpretation:** Excellent data quality and quantity. Act on this prediction.

### Scenario 2: Medium Confidence Prediction

```
Feature Completeness: 0.5 (15/30 features)
Feature Quality: 0.87 (some invalid values)
Data Recency: 0.8 (45 days since last event)
Consistency: 0.7 (std dev = 0.22)

Overall Score: 0.5 * 0.3 + 0.87 * 0.3 + 0.8 * 0.2 + 0.7 * 0.2 = 0.711
Confidence: MEDIUM ⚠️
```

**Interpretation:** Reasonable data but incomplete. Review before acting.

### Scenario 3: Low Confidence Prediction

```
Feature Completeness: 0.07 (2/30 features) → Penalty applied!
Feature Quality: 1.0 (both features valid)
Data Recency: 0.5 (no recent data)
Consistency: 1.0 (no variance data)

Base Score: 0.07 * 0.3 + 1.0 * 0.3 + 0.5 * 0.2 + 1.0 * 0.2 = 0.621
After Penalty: 0.621 * 0.5 = 0.31
Confidence: LOW ❌
```

**Interpretation:** Insufficient data. Gather more information before relying on prediction.

## Using Confidence Scores

### In Automated Systems

```python
prediction = await predictor.predict_failure(
    resource_id="api-gateway",
    resource_name="API Gateway",
    resource_type="web_app"
)

if prediction.confidence == PredictionConfidence.HIGH:
    if prediction.failure_probability > 0.7:
        # Automatically trigger scaling
        await scale_resource(prediction.resource_id)
elif prediction.confidence == PredictionConfidence.MEDIUM:
    if prediction.failure_probability > 0.8:
        # Alert ops team for manual review
        await alert_ops_team(prediction)
else:
    # Low confidence - log and monitor
    logger.info("Low confidence prediction", prediction=prediction)
```

### In Dashboards

Display confidence visually with color coding:
- 🟢 **HIGH** (green) - Trust this prediction
- 🟡 **MEDIUM** (yellow) - Review before acting
- 🔴 **LOW** (red) - More data needed

### In Reports

Include confidence breakdown in reports:

```
Prediction Confidence: MEDIUM (72%)

Factors:
- Feature Completeness: 67% ⚠️ (20/30 features available)
- Feature Quality: 95% ✅ (19/20 features valid)
- Data Recency: 80% ✅ (30 days since last event)
- Prediction Consistency: 75% ✅ (moderate variance)

Recommendation: Prediction is reasonably reliable but could be improved 
with more complete feature data.
```

## Improving Confidence Scores

To improve confidence in your predictions:

1. **Increase Feature Completeness**
   - Ensure Prometheus is collecting all relevant metrics
   - Verify Neo4j has complete topology data
   - Check that resource metadata is up-to-date

2. **Improve Feature Quality**
   - Validate data sources are healthy
   - Check for metric collection errors
   - Ensure metrics are properly normalized

3. **Maintain Recent Data**
   - Keep historical data current
   - Regularly update resource information
   - Track events and incidents

4. **Reduce Variance**
   - For inconsistent systems, increase monitoring
   - Consider longer lookback windows
   - Use ensemble methods for volatile metrics

## Technical Implementation

### Main Components

1. **`predictor.py`**: Core confidence calculation logic
   - `_calculate_confidence_with_metrics()`: Main entry point
   - `_calculate_feature_quality()`: Feature validation
   - `_calculate_data_recency()`: Recency scoring
   - `_calculate_prediction_consistency()`: Consistency scoring

2. **`models.py`**: Data structures
   - `ConfidenceMetrics`: Detailed confidence breakdown
   - `PredictionConfidence`: Enum for confidence levels

3. **`feature_extractor.py`**: Feature metadata
   - `get_feature_metadata()`: Expected ranges and importance

### Adding Custom Factors

To add a new confidence factor:

```python
def _calculate_custom_factor(self, features: dict) -> float:
    """Calculate custom confidence factor (0.0 to 1.0)."""
    # Your logic here
    return score

# Update _calculate_confidence_with_metrics():
custom_score = self._calculate_custom_factor(features)

# Adjust weights (must sum to 1.0):
weights = {
    "completeness": 0.25,
    "quality": 0.25,
    "recency": 0.2,
    "consistency": 0.2,
    "custom": 0.1,  # New factor
}

confidence_score = (
    completeness_score * weights["completeness"]
    + quality_score * weights["quality"]
    + recency_score * weights["recency"]
    + consistency_score * weights["consistency"]
    + custom_score * weights["custom"]
)
```

## Testing

Run the confidence scoring tests:

```bash
pytest tests/prediction/test_predictor.py::test_enhanced_confidence_calculation -v
pytest tests/prediction/test_predictor.py::test_confidence_with_metrics -v
pytest tests/prediction/test_predictor.py::test_feature_quality_scoring -v
pytest tests/prediction/test_predictor.py::test_data_recency_scoring -v
pytest tests/prediction/test_predictor.py::test_prediction_consistency_scoring -v
```

## FAQ

**Q: Why is my prediction confidence LOW despite having a high failure probability?**

A: Confidence and probability are independent. You can have a HIGH probability prediction with LOW confidence if the data quality is poor. Both factors should be considered together.

**Q: How do I know which factor is lowering my confidence score?**

A: Check the `confidence_metrics` in the API response. It breaks down each factor's contribution.

**Q: Can I override confidence thresholds?**

A: Currently thresholds are fixed. For custom logic, process the `overall_score` directly rather than using the `confidence_level`.

**Q: What if I have less than 30 features?**

A: The system expects ~30 features but will work with fewer. However, completeness will be lower, which may reduce confidence.

## References

- [ML Prediction Guide](ML_PREDICTION_GUIDE.md) - General ML prediction usage
- [ML Prediction Research](ML_PREDICTION_RESEARCH.md) - Technical background
- [Feature Extractor](../src/topdeck/analysis/prediction/feature_extractor.py) - Feature definitions
- [Predictor Implementation](../src/topdeck/analysis/prediction/predictor.py) - Confidence calculation code
