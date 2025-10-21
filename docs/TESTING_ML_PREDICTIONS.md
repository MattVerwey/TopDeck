# Testing ML Prediction Implementation

## Prerequisites

Install dependencies:
```bash
pip install -r requirements.txt
```

This will install:
- scikit-learn (ML algorithms)
- statsmodels (statistical models)
- prophet (time-series forecasting)
- numpy, pandas (data processing)
- joblib (model serialization)

## Unit Tests

Run the prediction tests:

```bash
# Run all prediction tests
pytest tests/prediction/ -v

# Run specific test
pytest tests/prediction/test_predictor.py::test_predict_failure_basic -v

# Run with coverage
pytest tests/prediction/ -v --cov=topdeck.analysis.prediction --cov-report=term-missing
```

Expected output:
```
tests/prediction/test_predictor.py::test_predict_failure_basic PASSED
tests/prediction/test_predictor.py::test_predict_failure_high_risk PASSED
tests/prediction/test_predictor.py::test_predict_performance PASSED
tests/prediction/test_predictor.py::test_predict_performance_predictions_structure PASSED
tests/prediction/test_predictor.py::test_detect_anomalies PASSED
tests/prediction/test_predictor.py::test_predictor_handles_different_resource_types PASSED
tests/prediction/test_predictor.py::test_predictor_recommendations_relevant PASSED
tests/prediction/test_predictor.py::test_risk_level_calculation PASSED
tests/prediction/test_predictor.py::test_contributing_factors_structure PASSED
```

## Example Script

Run the example to see predictions in action:

```bash
# From project root
python examples/prediction_example.py
```

This demonstrates:
- Failure prediction
- Performance forecasting
- Anomaly detection
- Monitoring integration
- Batch predictions

## API Testing

### 1. Start the API Server

```bash
# Terminal 1: Start API server
python -m topdeck
```

Server will start at: http://localhost:8000

### 2. Test Prediction Endpoints

```bash
# Terminal 2: Test endpoints

# Health check
curl http://localhost:8000/api/v1/prediction/health

# Predict failure
curl "http://localhost:8000/api/v1/prediction/resources/test-db/failure-risk?resource_type=database"

# Forecast performance
curl "http://localhost:8000/api/v1/prediction/resources/test-api/performance?metric_name=latency_p95&horizon_hours=24"

# Detect anomalies
curl "http://localhost:8000/api/v1/prediction/resources/test-app/anomalies?window_hours=24"
```

### 3. API Documentation

Visit http://localhost:8000/api/docs to see interactive API documentation.

## Integration Testing

Test with actual TopDeck infrastructure:

```bash
# Start services
docker-compose up -d

# Run API server
python -m topdeck

# In another terminal, test with real resources
curl "http://localhost:8000/api/v1/prediction/resources/{actual-resource-id}/failure-risk"
```

## Validation Checklist

- [ ] Unit tests pass
- [ ] Example script runs without errors
- [ ] API server starts successfully
- [ ] Health check returns "healthy"
- [ ] Failure prediction endpoint returns valid JSON
- [ ] Performance prediction endpoint returns time-series
- [ ] Anomaly detection endpoint returns results
- [ ] API documentation loads at /api/docs
- [ ] Predictions have reasonable values (0-1 for probabilities)
- [ ] Recommendations are present in responses

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "scikit-learn|statsmodels|prophet|numpy|pandas"
```

### API Server Won't Start

Check for:
- Port 8000 already in use
- Missing environment variables
- Neo4j/Redis/RabbitMQ not running (optional for predictions)

```bash
# Check port
lsof -i :8000

# Check environment
cat .env

# Start services
docker-compose up -d
```

### Tests Fail

Common issues:
- Missing test dependencies: `pip install -r requirements-dev.txt`
- Wrong Python version: Requires Python 3.11+
- Import path issues: Run from project root

## Performance Testing

Test prediction speed:

```bash
# Time a single prediction
time curl -s "http://localhost:8000/api/v1/prediction/resources/test-db/failure-risk" > /dev/null

# Expected: < 100ms
```

Run load test:

```bash
# Install ab (Apache Bench)
# Ubuntu: apt-get install apache2-utils
# Mac: brew install ab

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:8000/api/v1/prediction/health

# Check response times in output
```

## Security Testing

Verify no sensitive data in predictions:

```bash
# Check that predictions don't leak sensitive info
curl "http://localhost:8000/api/v1/prediction/resources/test-db/failure-risk" | jq .

# Verify:
# - No database connection strings
# - No API keys or secrets
# - No internal IP addresses (unless expected)
```

## Monitoring

Monitor prediction service in production:

```bash
# Check metrics
curl http://localhost:8000/metrics | grep prediction

# Look for:
# - topdeck_predictions_total
# - topdeck_prediction_duration_seconds
# - topdeck_prediction_errors_total
```

## Next Steps After Testing

Once tests pass:

1. **Collect Historical Data**
   - Let Prometheus collect metrics for 7+ days
   - Verify data quality and completeness

2. **Train ML Models**
   - Use collected data to train models
   - Replace rule-based logic with trained models

3. **Monitor Accuracy**
   - Track prediction accuracy over time
   - Compare predictions to actual outcomes

4. **Tune Models**
   - Adjust hyperparameters based on performance
   - Retrain periodically with new data

5. **Production Deployment**
   - Deploy to production environment
   - Set up monitoring and alerting
   - Create runbooks for common issues

## Expected Test Results

### Unit Tests
- ✅ All 9 tests should pass
- ✅ Test coverage > 80%
- ✅ No warnings or errors

### API Tests
- ✅ Health check returns 200 OK
- ✅ All endpoints return valid JSON
- ✅ Response times < 100ms
- ✅ No 500 errors

### Example Script
- ✅ Runs without errors
- ✅ Displays predictions for 5 examples
- ✅ Shows risk levels and recommendations

## Support

If tests fail or you encounter issues:

1. Check the [ML Prediction Guide](ML_PREDICTION_GUIDE.md)
2. Review the [Research Document](ML_PREDICTION_RESEARCH.md)
3. Check logs: `tail -f logs/topdeck.log`
4. Open an issue on GitHub with test output
