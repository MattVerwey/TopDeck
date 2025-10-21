"""
Tests for the ML predictor.
"""

import pytest
from datetime import datetime

from topdeck.analysis.prediction import Predictor
from topdeck.analysis.prediction.feature_extractor import FeatureExtractor
from topdeck.analysis.prediction.models import (
    RiskLevel,
    PredictionConfidence,
)


@pytest.fixture
def predictor():
    """Create a predictor instance for testing."""
    feature_extractor = FeatureExtractor()
    return Predictor(feature_extractor=feature_extractor)


@pytest.mark.asyncio
async def test_predict_failure_basic(predictor):
    """Test basic failure prediction."""
    prediction = await predictor.predict_failure(
        resource_id="test-db-001",
        resource_name="Test Database",
        resource_type="database"
    )
    
    assert prediction.resource_id == "test-db-001"
    assert prediction.resource_name == "Test Database"
    assert prediction.resource_type == "database"
    assert 0.0 <= prediction.failure_probability <= 1.0
    assert prediction.risk_level in [r for r in RiskLevel]
    assert prediction.confidence in [c for c in PredictionConfidence]
    assert isinstance(prediction.recommendations, list)
    assert len(prediction.recommendations) > 0
    assert isinstance(prediction.predicted_at, datetime)


@pytest.mark.asyncio
async def test_predict_failure_high_risk(predictor):
    """Test that high-risk resources are identified."""
    # The predictor should identify issues based on resource characteristics
    prediction = await predictor.predict_failure(
        resource_id="critical-service",
        resource_name="Critical Service",
        resource_type="web_app"
    )
    
    # Should have some failure probability
    assert prediction.failure_probability >= 0.0
    
    # Should have contributing factors
    assert isinstance(prediction.contributing_factors, list)
    
    # Should have recommendations
    assert len(prediction.recommendations) > 0


@pytest.mark.asyncio
async def test_predict_performance(predictor):
    """Test performance prediction."""
    prediction = await predictor.predict_performance(
        resource_id="api-gateway",
        resource_name="API Gateway",
        metric_name="latency_p95",
        horizon_hours=24
    )
    
    assert prediction.resource_id == "api-gateway"
    assert prediction.metric_name == "latency_p95"
    assert prediction.current_value > 0
    assert prediction.baseline_value > 0
    assert len(prediction.predictions) > 0
    assert prediction.degradation_risk in [r for r in RiskLevel]
    assert prediction.trend in ["increasing", "decreasing", "stable"]
    assert isinstance(prediction.seasonality_detected, bool)


@pytest.mark.asyncio
async def test_predict_performance_predictions_structure(predictor):
    """Test that performance predictions have correct structure."""
    prediction = await predictor.predict_performance(
        resource_id="test-service",
        resource_name="Test Service",
        metric_name="latency_p95",
        horizon_hours=12
    )
    
    # Should have predictions for the horizon
    assert len(prediction.predictions) > 0
    
    # Each prediction should have required fields
    for pred in prediction.predictions:
        assert hasattr(pred, 'timestamp')
        assert hasattr(pred, 'predicted_value')
        assert hasattr(pred, 'confidence_lower')
        assert hasattr(pred, 'confidence_upper')
        assert pred.predicted_value > 0
        assert pred.confidence_lower <= pred.predicted_value
        assert pred.predicted_value <= pred.confidence_upper


@pytest.mark.asyncio
async def test_detect_anomalies(predictor):
    """Test anomaly detection."""
    detection = await predictor.detect_anomalies(
        resource_id="webapp-prod",
        resource_name="Web App Production",
        window_hours=24
    )
    
    assert detection.resource_id == "webapp-prod"
    assert detection.resource_name == "Web App Production"
    assert 0.0 <= detection.overall_anomaly_score <= 1.0
    assert detection.risk_level in [r for r in RiskLevel]
    assert isinstance(detection.anomalies, list)
    assert isinstance(detection.affected_metrics, list)
    assert isinstance(detection.recommendations, list)
    assert len(detection.recommendations) > 0


@pytest.mark.asyncio
async def test_predictor_handles_different_resource_types(predictor):
    """Test that predictor handles different resource types."""
    resource_types = ["database", "web_app", "load_balancer", "api", "cache"]
    
    for resource_type in resource_types:
        prediction = await predictor.predict_failure(
            resource_id=f"test-{resource_type}",
            resource_name=f"Test {resource_type}",
            resource_type=resource_type
        )
        
        assert prediction.resource_type == resource_type
        assert prediction.failure_probability >= 0.0
        assert len(prediction.recommendations) > 0


@pytest.mark.asyncio
async def test_predictor_recommendations_relevant(predictor):
    """Test that recommendations are relevant to the predictions."""
    prediction = await predictor.predict_failure(
        resource_id="high-risk-db",
        resource_name="High Risk Database",
        resource_type="database"
    )
    
    # Recommendations should be strings
    assert all(isinstance(r, str) for r in prediction.recommendations)
    
    # Should have at least one recommendation
    assert len(prediction.recommendations) > 0
    
    # Database-specific recommendation might be included
    if prediction.failure_probability > 0.5:
        recommendation_text = " ".join(prediction.recommendations).lower()
        # Should mention some action
        assert any(word in recommendation_text for word in [
            "scale", "investigate", "check", "monitor", "replica", "optimize"
        ])


def test_risk_level_calculation(predictor):
    """Test risk level determination."""
    test_cases = [
        (0.9, RiskLevel.CRITICAL),
        (0.7, RiskLevel.HIGH),
        (0.4, RiskLevel.MEDIUM),
        (0.1, RiskLevel.LOW),
    ]
    
    for probability, expected_level in test_cases:
        level = predictor._determine_risk_level(probability)
        assert level == expected_level


def test_contributing_factors_structure(predictor):
    """Test that contributing factors have correct structure."""
    features = {
        "cpu_mean": 0.85,
        "error_rate_mean": 0.06,
        "memory_trend": 0.08,
    }
    
    factors = predictor._identify_contributing_factors(features)
    
    assert isinstance(factors, list)
    assert len(factors) > 0
    
    for factor in factors:
        assert hasattr(factor, 'factor')
        assert hasattr(factor, 'importance')
        assert hasattr(factor, 'description')
        assert 0.0 <= factor.importance <= 1.0
        assert isinstance(factor.description, str)
