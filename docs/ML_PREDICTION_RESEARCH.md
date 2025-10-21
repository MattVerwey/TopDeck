# ML-Based Prediction Research for TopDeck

## Executive Summary

This document analyzes the requirements and approaches for implementing ML-based predictions in TopDeck to forecast failures, performance issues, and resource degradation before they occur.

**Recommendation**: Use traditional ML/statistical libraries (scikit-learn, statsmodels, Prophet) rather than LLMs. An LLM is not necessary for time-series prediction and would add significant cost and complexity.

## Problem Statement

TopDeck needs to predict:
1. **Failure Prediction**: Which resources are likely to fail based on historical patterns
2. **Performance Degradation**: When services will experience degradation before it impacts users
3. **Capacity Planning**: When resources will reach capacity limits
4. **Anomaly Detection**: Unusual patterns that may indicate issues

## Current Infrastructure

### Data Collection (Already Implemented)

TopDeck already has robust data collection infrastructure:

1. **Prometheus Integration** (`src/topdeck/monitoring/collectors/prometheus.py`)
   - Collects time-series metrics (CPU, memory, latency, error rates)
   - Historical data for training models
   - Query API for retrieving metric history

2. **Custom Metrics** (`src/topdeck/common/metrics.py`)
   - HTTP request tracking
   - Resource discovery metrics
   - Risk assessment metrics
   - Database operation metrics

3. **Neo4j Graph Database**
   - Resource relationships and dependencies
   - Topology information for contextual predictions
   - Historical deployment and change data

### Existing Analysis Capabilities

- Risk scoring (`src/topdeck/analysis/risk/scoring.py`)
- Failure simulation (`src/topdeck/analysis/risk/simulation.py`)
- Impact analysis (`src/topdeck/analysis/risk/impact.py`)
- Anomaly detection (basic threshold-based in Prometheus collector)

## Approach Analysis

### Option 1: Large Language Models (LLM) ❌ NOT RECOMMENDED

**Pros:**
- Can understand natural language queries
- May identify complex patterns
- Good for explaining predictions to users

**Cons:**
- Massive overkill for time-series prediction
- High cost (API calls to OpenAI, Anthropic, etc.)
- Slower inference time
- Requires prompt engineering
- Not designed for numerical time-series data
- Needs external API dependency
- Privacy concerns (sending metrics to external services)
- Not deterministic

**Verdict**: LLMs are designed for natural language processing, not numerical time-series prediction. Using an LLM would be like using a sledgehammer to crack a nut.

### Option 2: Traditional ML Libraries ✅ RECOMMENDED

**Libraries:**
- **scikit-learn**: General ML algorithms (Random Forest, Gradient Boosting, SVM)
- **statsmodels**: Statistical models (ARIMA, SARIMA, VAR)
- **Prophet** (by Meta): Time-series forecasting with seasonality
- **numpy/scipy**: Statistical analysis
- **pandas**: Data manipulation

**Pros:**
- Purpose-built for time-series and numerical prediction
- Fast inference (milliseconds)
- No external dependencies or API costs
- Full control and privacy
- Well-documented and mature
- Can run locally or in-cluster
- Interpretable results
- Lightweight

**Cons:**
- Requires some ML expertise to tune
- Need to select appropriate algorithms
- Model training and updates required

**Verdict**: Perfect fit for TopDeck's needs. These libraries are specifically designed for the type of predictions we need.

### Option 3: Cloud Provider ML Services

**Services:**
- Azure Machine Learning
- AWS SageMaker
- GCP Vertex AI

**Pros:**
- Managed infrastructure
- Auto-scaling
- Built-in monitoring

**Cons:**
- Vendor lock-in
- Additional cost
- Requires cloud-specific integration
- Overkill for our use case
- Slower than local inference

**Verdict**: Unnecessary complexity for TopDeck's prediction needs.

## Recommended Implementation

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Prediction Service                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Feature    │  │    Model     │  │  Prediction  │  │
│  │  Extraction  │  │   Training   │  │   Engine     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                          │                              │
└──────────────────────────┼──────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│  Prometheus  │                    │    Neo4j     │
│  (Metrics)   │                    │  (Context)   │
└──────────────┘                    └──────────────┘
```

### Module Structure

```
src/topdeck/analysis/prediction/
├── __init__.py
├── models.py              # Data models for predictions
├── feature_extractor.py   # Extract features from Prometheus/Neo4j
├── trainer.py             # Train and update models
├── predictor.py           # Make predictions
├── failure_predictor.py   # Predict resource failures
├── performance_predictor.py  # Predict performance degradation
├── anomaly_detector.py    # Advanced anomaly detection
└── model_storage.py       # Save/load trained models
```

### Prediction Types

#### 1. Failure Prediction

**Input Features:**
- CPU usage trends (last 7 days)
- Memory usage trends
- Error rate history
- Restart count
- Deployment frequency
- Resource age
- Dependency count (from graph)

**Algorithm:** Random Forest or Gradient Boosting
- Good for tabular data
- Handles non-linear relationships
- Feature importance for explainability

**Output:**
- Failure probability (0-1)
- Time to failure estimate
- Contributing factors
- Confidence level

#### 2. Performance Degradation Prediction

**Input Features:**
- Response time trends (p50, p95, p99)
- Request rate changes
- Resource utilization trends
- Dependency health scores
- Recent deployments

**Algorithm:** ARIMA or Prophet
- Time-series specific
- Handles seasonality (daily, weekly patterns)
- Trend detection

**Output:**
- Predicted latency for next 24h
- Degradation risk score
- Recommended actions

#### 3. Anomaly Detection (Advanced)

**Input Features:**
- All available metrics
- Historical patterns
- Resource relationships

**Algorithm:** Isolation Forest or Local Outlier Factor
- Unsupervised learning
- No labeled data needed
- Detects unusual patterns

**Output:**
- Anomaly score
- Affected metrics
- Similar historical incidents

### Implementation Phases

#### Phase 1: Foundation (Week 1)
- Set up prediction module structure
- Implement feature extraction from Prometheus
- Create data models
- Add basic statistical analysis

#### Phase 2: Failure Prediction (Week 2)
- Implement Random Forest model for failure prediction
- Train on historical data (synthetic initially)
- Create prediction API endpoint
- Add tests

#### Phase 3: Performance Prediction (Week 3)
- Implement Prophet/ARIMA for time-series
- Add performance degradation prediction
- Integrate with risk analysis engine

#### Phase 4: Anomaly Detection (Week 4)
- Implement Isolation Forest
- Replace threshold-based detection
- Add confidence scoring
- Integration and testing

### Dependencies

Add to `requirements.txt`:
```python
# ML and statistical libraries
scikit-learn==1.3.2        # General ML algorithms
statsmodels==0.14.0        # Statistical models
prophet==1.1.5             # Time-series forecasting
numpy==1.26.2              # Numerical computing
pandas==2.1.4              # Data manipulation
joblib==1.3.2              # Model serialization
```

Estimated total size: ~50MB (lightweight compared to LLM which would be GBs)

### API Endpoints

```python
# Predict resource failure
GET /api/v1/prediction/resources/{resource_id}/failure-risk
Response: {
    "resource_id": "sql-db-prod",
    "failure_probability": 0.73,
    "time_to_failure_hours": 48,
    "confidence": 0.85,
    "contributing_factors": [
        {"factor": "cpu_trend", "importance": 0.45},
        {"factor": "error_rate_increase", "importance": 0.30},
        {"factor": "high_dependency_count", "importance": 0.15}
    ],
    "recommendations": [
        "Scale up CPU allocation",
        "Investigate error spike",
        "Review dependent services"
    ]
}

# Predict performance degradation
GET /api/v1/prediction/resources/{resource_id}/performance
Response: {
    "resource_id": "api-gateway",
    "predicted_latency_p95": [
        {"timestamp": "2025-10-22T00:00:00Z", "value": 250.5},
        {"timestamp": "2025-10-22T01:00:00Z", "value": 275.2},
        ...
    ],
    "degradation_risk": "medium",
    "confidence": 0.78,
    "seasonality_detected": true
}

# Detect anomalies
GET /api/v1/prediction/anomalies?time_range=24h
Response: {
    "anomalies": [
        {
            "resource_id": "webapp-prod",
            "metric": "memory_usage",
            "anomaly_score": 0.92,
            "timestamp": "2025-10-21T15:30:00Z",
            "similar_incidents": [...]
        }
    ]
}
```

## Training Strategy

### Initial Training
1. **Synthetic Data**: Generate realistic training data based on patterns
2. **Bootstrap**: Use rule-based predictions initially
3. **Feedback Loop**: Learn from actual incidents

### Continuous Learning
1. **Periodic Retraining**: Daily or weekly based on new data
2. **Model Versioning**: Keep track of model performance
3. **A/B Testing**: Compare model versions
4. **Monitoring**: Track prediction accuracy

### Model Storage
- Store trained models in `/data/models/`
- Use joblib for serialization
- Version models with timestamps
- Keep last 3 versions for rollback

## Performance Considerations

### Inference Speed
- **Target**: <100ms per prediction
- **Expected**: 10-50ms with scikit-learn
- **Compare**: LLM would be 1-5 seconds

### Resource Usage
- **Memory**: ~200MB for loaded models
- **CPU**: Minimal during inference
- **Storage**: ~50MB per model version

### Scalability
- Models loaded in memory
- Stateless prediction service
- Can scale horizontally
- Cache predictions for 5-10 minutes

## Success Metrics

### Model Performance
- **Accuracy**: >80% for failure prediction
- **False Positive Rate**: <10%
- **Lead Time**: 24-48 hours advance warning

### Business Impact
- Reduce MTTR (Mean Time To Recover) by 30%
- Prevent 50% of incidents through early detection
- Improve capacity planning accuracy

## Comparison: LLM vs ML Library

| Aspect | LLM | ML Library |
|--------|-----|------------|
| **Training Time** | Hours/Days | Minutes |
| **Inference Time** | 1-5 seconds | 10-50ms |
| **Cost** | $$$ (API calls) | $ (compute) |
| **Privacy** | Risk (external API) | Secure (local) |
| **Accuracy** | Unknown | Proven |
| **Interpretability** | Black box | Explainable |
| **Dependencies** | External API | Self-contained |
| **Maintenance** | API version changes | Stable |
| **Scaling** | Rate limited | Unlimited |

## Conclusion

**Recommendation: Use Traditional ML Libraries**

For TopDeck's ML-based prediction needs, traditional ML and statistical libraries (scikit-learn, statsmodels, Prophet) are the clear choice:

1. **Purpose-Built**: Designed specifically for time-series and numerical prediction
2. **Cost-Effective**: No API costs, runs locally
3. **Fast**: Millisecond inference times
4. **Private**: No data leaves the system
5. **Proven**: Well-established for this use case
6. **Lightweight**: ~50MB vs GBs for LLMs
7. **Explainable**: Can show why predictions were made

An LLM would be massive overkill and would introduce unnecessary complexity, cost, and latency. Save LLMs for natural language tasks like:
- Explaining predictions in natural language to users
- Query interface ("Is my database going to crash?")
- Generating remediation documentation

But for the core numerical prediction task, traditional ML is the right tool.

## Next Steps

1. Add ML dependencies to requirements.txt
2. Implement prediction module structure
3. Create feature extraction from Prometheus
4. Build failure prediction model
5. Add API endpoints
6. Write tests
7. Document usage
8. Train initial models

## References

- [scikit-learn Documentation](https://scikit-learn.org/)
- [Prophet Documentation](https://facebook.github.io/prophet/)
- [statsmodels Documentation](https://www.statsmodels.org/)
- [Prometheus Query API](https://prometheus.io/docs/prometheus/latest/querying/api/)
