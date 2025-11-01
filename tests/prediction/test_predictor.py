"""
Tests for the ML predictor.
"""

from datetime import datetime

import pytest

from topdeck.analysis.prediction import Predictor
from topdeck.analysis.prediction.feature_extractor import FeatureExtractor
from topdeck.analysis.prediction.models import (
    PredictionConfidence,
    RiskLevel,
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
        resource_id="test-db-001", resource_name="Test Database", resource_type="database"
    )

    assert prediction.resource_id == "test-db-001"
    assert prediction.resource_name == "Test Database"
    assert prediction.resource_type == "database"
    assert 0.0 <= prediction.failure_probability <= 1.0
    assert prediction.risk_level in list(RiskLevel)
    assert prediction.confidence in list(PredictionConfidence)
    assert isinstance(prediction.recommendations, list)
    assert len(prediction.recommendations) > 0
    assert isinstance(prediction.predicted_at, datetime)


@pytest.mark.asyncio
async def test_predict_failure_high_risk(predictor):
    """Test that high-risk resources are identified."""
    # The predictor should identify issues based on resource characteristics
    prediction = await predictor.predict_failure(
        resource_id="critical-service", resource_name="Critical Service", resource_type="web_app"
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
        horizon_hours=24,
    )

    assert prediction.resource_id == "api-gateway"
    assert prediction.metric_name == "latency_p95"
    assert prediction.current_value > 0
    assert prediction.baseline_value > 0
    assert len(prediction.predictions) > 0
    assert prediction.degradation_risk in list(RiskLevel)
    assert prediction.trend in ["increasing", "decreasing", "stable"]
    assert isinstance(prediction.seasonality_detected, bool)


@pytest.mark.asyncio
async def test_predict_performance_predictions_structure(predictor):
    """Test that performance predictions have correct structure."""
    prediction = await predictor.predict_performance(
        resource_id="test-service",
        resource_name="Test Service",
        metric_name="latency_p95",
        horizon_hours=12,
    )

    # Should have predictions for the horizon
    assert len(prediction.predictions) > 0

    # Each prediction should have required fields
    for pred in prediction.predictions:
        assert hasattr(pred, "timestamp")
        assert hasattr(pred, "predicted_value")
        assert hasattr(pred, "confidence_lower")
        assert hasattr(pred, "confidence_upper")
        assert pred.predicted_value > 0
        assert pred.confidence_lower <= pred.predicted_value
        assert pred.predicted_value <= pred.confidence_upper


@pytest.mark.asyncio
async def test_detect_anomalies(predictor):
    """Test anomaly detection."""
    detection = await predictor.detect_anomalies(
        resource_id="webapp-prod", resource_name="Web App Production", window_hours=24
    )

    assert detection.resource_id == "webapp-prod"
    assert detection.resource_name == "Web App Production"
    assert 0.0 <= detection.overall_anomaly_score <= 1.0
    assert detection.risk_level in list(RiskLevel)
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
            resource_type=resource_type,
        )

        assert prediction.resource_type == resource_type
        assert prediction.failure_probability >= 0.0
        assert len(prediction.recommendations) > 0


@pytest.mark.asyncio
async def test_predictor_recommendations_relevant(predictor):
    """Test that recommendations are relevant to the predictions."""
    prediction = await predictor.predict_failure(
        resource_id="high-risk-db", resource_name="High Risk Database", resource_type="database"
    )

    # Recommendations should be strings
    assert all(isinstance(r, str) for r in prediction.recommendations)

    # Should have at least one recommendation
    assert len(prediction.recommendations) > 0

    # Database-specific recommendation might be included
    if prediction.failure_probability > 0.5:
        recommendation_text = " ".join(prediction.recommendations).lower()
        # Should mention some action
        assert any(
            word in recommendation_text
            for word in ["scale", "investigate", "check", "monitor", "replica", "optimize"]
        )


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
        assert hasattr(factor, "factor")
        assert hasattr(factor, "importance")
        assert hasattr(factor, "description")
        assert 0.0 <= factor.importance <= 1.0
        assert isinstance(factor.description, str)


def test_enhanced_confidence_calculation(predictor):
    """Test enhanced confidence calculation with multiple factors."""
    # High quality features - should give HIGH confidence
    high_quality_features = {
        "cpu_mean": 0.75,
        "cpu_max": 0.85,
        "cpu_std": 0.10,
        "cpu_trend": 0.05,
        "memory_mean": 0.65,
        "memory_max": 0.80,
        "memory_std": 0.08,
        "memory_trend": 0.03,
        "error_rate_mean": 0.02,
        "error_rate_max": 0.04,
        "error_spike_count": 2,
        "latency_p95_mean": 200.0,
        "latency_p95_max": 350.0,
        "restart_count": 1,
        "days_since_last_failure": 25.0,
        "dependency_count": 5.0,
        "dependent_count": 8.0,
        "is_central_node": 1.0,
        "blast_radius": 12.0,
    }

    confidence = predictor._calculate_confidence(high_quality_features)
    assert confidence in list(PredictionConfidence)
    # With good features, should be at least MEDIUM or HIGH
    assert confidence in [PredictionConfidence.MEDIUM, PredictionConfidence.HIGH]


def test_confidence_with_metrics(predictor):
    """Test that confidence calculation returns detailed metrics."""
    features = {
        "cpu_mean": 0.7,
        "memory_mean": 0.6,
        "error_rate_mean": 0.02,
        "days_since_last_failure": 30.0,
        "cpu_std": 0.15,
        "memory_std": 0.12,
    }

    confidence, metrics = predictor._calculate_confidence_with_metrics(features)

    # Check confidence level
    assert confidence in list(PredictionConfidence)

    # Check metrics structure
    assert hasattr(metrics, "overall_score")
    assert hasattr(metrics, "confidence_level")
    assert hasattr(metrics, "feature_completeness")
    assert hasattr(metrics, "feature_quality")
    assert hasattr(metrics, "data_recency")
    assert hasattr(metrics, "prediction_consistency")

    # Check metrics values are in valid ranges
    assert 0.0 <= metrics.overall_score <= 1.0
    assert 0.0 <= metrics.feature_completeness <= 1.0
    assert 0.0 <= metrics.feature_quality <= 1.0
    assert 0.0 <= metrics.data_recency <= 1.0
    assert 0.0 <= metrics.prediction_consistency <= 1.0

    # Check metadata
    assert metrics.total_features > 0
    assert metrics.valid_features >= 0
    assert metrics.missing_features >= 0


def test_feature_quality_scoring(predictor):
    """Test feature quality calculation."""
    # All valid features
    valid_features = {
        "cpu_mean": 0.75,
        "memory_mean": 0.65,
        "error_rate_mean": 0.02,
    }
    quality_valid = predictor._calculate_feature_quality(valid_features)
    assert quality_valid == 1.0

    # Some invalid features
    mixed_features = {
        "cpu_mean": 1.5,  # Invalid: > 1.0
        "memory_mean": 0.65,  # Valid
        "error_rate_mean": -0.1,  # Invalid: < 0
    }
    quality_mixed = predictor._calculate_feature_quality(mixed_features)
    assert 0.0 < quality_mixed < 1.0

    # Empty features
    quality_empty = predictor._calculate_feature_quality({})
    assert quality_empty == 0.0


def test_data_recency_scoring(predictor):
    """Test data recency calculation."""
    # Recent failure (high confidence in patterns)
    recent_features = {"days_since_last_failure": 20.0}
    recency_recent = predictor._calculate_data_recency(recent_features)
    assert recency_recent >= 0.8

    # Old failure (lower confidence)
    old_features = {"days_since_last_failure": 200.0}
    recency_old = predictor._calculate_data_recency(old_features)
    assert recency_old <= 0.6

    # No data
    no_data = {}
    recency_none = predictor._calculate_data_recency(no_data)
    assert recency_none == 0.5


def test_prediction_consistency_scoring(predictor):
    """Test prediction consistency calculation."""
    # Very consistent (low variance)
    consistent_features = {"cpu_std": 0.05, "memory_std": 0.05}
    consistency_high = predictor._calculate_prediction_consistency(consistent_features)
    assert consistency_high >= 0.8

    # High variance (inconsistent)
    inconsistent_features = {"cpu_std": 0.35, "memory_std": 0.35}
    consistency_low = predictor._calculate_prediction_consistency(inconsistent_features)
    assert consistency_low <= 0.6


@pytest.mark.asyncio
async def test_failure_prediction_includes_confidence_metrics(predictor):
    """Test that failure predictions include detailed confidence metrics."""
    prediction = await predictor.predict_failure(
        resource_id="test-resource",
        resource_name="Test Resource",
        resource_type="web_app",
    )

    # Check that confidence metrics are included
    assert prediction.confidence_metrics is not None
    assert hasattr(prediction.confidence_metrics, "overall_score")
    assert hasattr(prediction.confidence_metrics, "feature_completeness")
    assert hasattr(prediction.confidence_metrics, "feature_quality")
    assert hasattr(prediction.confidence_metrics, "data_recency")
    assert hasattr(prediction.confidence_metrics, "prediction_consistency")

    # Validate metrics are reasonable
    assert 0.0 <= prediction.confidence_metrics.overall_score <= 1.0
    assert prediction.confidence_metrics.confidence_level == prediction.confidence


def test_confidence_levels_mapping(predictor):
    """Test confidence score to level mapping."""
    # High confidence (>= 0.8)
    high_features = {
        "cpu_mean": 0.7,
        "cpu_std": 0.05,
        "memory_mean": 0.6,
        "memory_std": 0.05,
        "error_rate_mean": 0.01,
        "days_since_last_failure": 25.0,
        "dependency_count": 5.0,
        "dependent_count": 8.0,
        "blast_radius": 10.0,
        "restart_count": 1,
        "is_central_node": 1.0,
        "betweenness_centrality": 0.6,
        "is_database": 1.0,
        "resource_age_days": 180.0,
        "deployment_frequency": 2.0,
        "config_change_frequency": 1.0,
        "latency_p95_mean": 250.0,
        "latency_p95_max": 400.0,
        "cpu_max": 0.85,
        "memory_max": 0.75,
    }

    confidence, metrics = predictor._calculate_confidence_with_metrics(high_features)
    # With many good features, should have reasonable confidence
    assert confidence in list(PredictionConfidence)
    assert metrics.overall_score > 0.0
