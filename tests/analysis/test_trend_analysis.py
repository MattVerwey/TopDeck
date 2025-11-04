"""Tests for risk trend analysis."""

from datetime import datetime, timedelta

import pytest

from topdeck.analysis.risk.trend_analysis import (
    RiskSnapshot,
    RiskTrendAnalyzer,
    TrendDirection,
    TrendSeverity,
)


@pytest.fixture
def trend_analyzer():
    """Create a trend analyzer."""
    return RiskTrendAnalyzer()


@pytest.fixture
def stable_snapshots():
    """Create snapshots with stable risk."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    return [
        RiskSnapshot(
            timestamp=base_time + timedelta(days=i),
            risk_score=50.0 + i * 0.5,  # Minimal change
            risk_level="medium",
            factors={},
        )
        for i in range(10)
    ]


@pytest.fixture
def improving_snapshots():
    """Create snapshots with improving risk."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    return [
        RiskSnapshot(
            timestamp=base_time + timedelta(days=i),
            risk_score=70.0 - i * 5,  # Decreasing risk
            risk_level="high",
            factors={},
        )
        for i in range(10)
    ]


@pytest.fixture
def degrading_snapshots():
    """Create snapshots with degrading risk."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    return [
        RiskSnapshot(
            timestamp=base_time + timedelta(days=i),
            risk_score=30.0 + i * 5,  # Increasing risk
            risk_level="low",
            factors={},
        )
        for i in range(10)
    ]


@pytest.fixture
def volatile_snapshots():
    """Create snapshots with volatile risk."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    values = [50, 65, 45, 70, 40, 75, 35, 80, 30, 85]
    return [
        RiskSnapshot(
            timestamp=base_time + timedelta(days=i),
            risk_score=float(values[i]),
            risk_level="medium",
            factors={},
        )
        for i in range(10)
    ]


def test_analyze_stable_trend(trend_analyzer, stable_snapshots):
    """Test analyzing a stable risk trend."""
    trend = trend_analyzer.analyze_trend(
        resource_id="test-resource",
        resource_name="Test Resource",
        snapshots=stable_snapshots,
    )

    assert trend.trend_direction == TrendDirection.STABLE
    assert abs(trend.change_percentage) < 10


def test_analyze_improving_trend(trend_analyzer, improving_snapshots):
    """Test analyzing an improving risk trend."""
    trend = trend_analyzer.analyze_trend(
        resource_id="test-resource",
        resource_name="Test Resource",
        snapshots=improving_snapshots,
    )

    assert trend.trend_direction == TrendDirection.IMPROVING
    assert trend.change_percentage < 0  # Negative change = improvement


def test_analyze_degrading_trend(trend_analyzer, degrading_snapshots):
    """Test analyzing a degrading risk trend."""
    trend = trend_analyzer.analyze_trend(
        resource_id="test-resource",
        resource_name="Test Resource",
        snapshots=degrading_snapshots,
    )

    assert trend.trend_direction == TrendDirection.DEGRADING
    assert trend.change_percentage > 0  # Positive change = degrading


def test_analyze_volatile_trend(trend_analyzer, volatile_snapshots):
    """Test analyzing a volatile risk trend."""
    trend = trend_analyzer.analyze_trend(
        resource_id="test-resource",
        resource_name="Test Resource",
        snapshots=volatile_snapshots,
    )

    assert trend.trend_direction == TrendDirection.VOLATILE


def test_insufficient_data_trend(trend_analyzer):
    """Test handling insufficient data."""
    single_snapshot = [
        RiskSnapshot(
            timestamp=datetime(2024, 1, 1),
            risk_score=50.0,
            risk_level="medium",
            factors={},
        )
    ]

    trend = trend_analyzer.analyze_trend(
        resource_id="test-resource",
        resource_name="Test Resource",
        snapshots=single_snapshot,
    )

    assert trend.trend_direction == TrendDirection.STABLE
    assert trend.change_percentage == 0.0
    assert any("Insufficient data" in r for r in trend.recommendations)


def test_severity_determination(trend_analyzer):
    """Test severity determination based on change percentage."""
    # Minor change
    assert trend_analyzer._determine_severity(3.0) == TrendSeverity.MINOR

    # Moderate change
    assert trend_analyzer._determine_severity(10.0) == TrendSeverity.MODERATE

    # Significant change
    assert trend_analyzer._determine_severity(20.0) == TrendSeverity.SIGNIFICANT

    # Critical change
    assert trend_analyzer._determine_severity(40.0) == TrendSeverity.CRITICAL


def test_detect_anomalies(trend_analyzer, stable_snapshots):
    """Test anomaly detection."""
    # Add an anomalous spike
    snapshots = stable_snapshots.copy()
    snapshots.append(
        RiskSnapshot(
            timestamp=datetime(2024, 1, 11),
            risk_score=90.0,  # Sudden spike
            risk_level="high",
            factors={},
        )
    )

    anomalies = trend_analyzer.detect_anomalies(snapshots, window_size=7)

    assert len(anomalies) > 0
    # The spike should be detected as anomaly
    assert any(a["risk_score"] == 90.0 for a in anomalies)


def test_predict_future_risk(trend_analyzer, improving_snapshots):
    """Test future risk prediction."""
    prediction = trend_analyzer.predict_future_risk(improving_snapshots, days_ahead=7)

    assert "predicted_risk_score" in prediction
    assert "confidence" in prediction
    assert "trend_slope" in prediction

    # For improving trend, predicted risk should be lower
    current_risk = improving_snapshots[-1].risk_score
    assert prediction["predicted_risk_score"] < current_risk


def test_predict_with_insufficient_data(trend_analyzer):
    """Test prediction with insufficient data."""
    few_snapshots = [
        RiskSnapshot(
            timestamp=datetime(2024, 1, 1),
            risk_score=50.0,
            risk_level="medium",
            factors={},
        ),
        RiskSnapshot(
            timestamp=datetime(2024, 1, 2),
            risk_score=51.0,
            risk_level="medium",
            factors={},
        ),
    ]

    prediction = trend_analyzer.predict_future_risk(few_snapshots)

    assert prediction["prediction"] is None
    assert "Insufficient data" in prediction["message"]


def test_compare_resources_trends(trend_analyzer, improving_snapshots, degrading_snapshots):
    """Test comparing trends across resources."""
    improving_trend = trend_analyzer.analyze_trend(
        "resource-1", "Resource 1", improving_snapshots
    )

    degrading_trend = trend_analyzer.analyze_trend(
        "resource-2", "Resource 2", degrading_snapshots
    )

    comparison = trend_analyzer.compare_resources_trends([improving_trend, degrading_trend])

    assert comparison["total_resources"] == 2
    assert comparison["improving_count"] == 1
    assert comparison["degrading_count"] == 1
    assert "overall_health" in comparison


def test_identify_contributing_factors(trend_analyzer):
    """Test identifying contributing factors."""
    current_factors = {
        "dependencies_count": 10,
        "dependents_count": 5,
        "is_spof": True,
    }

    previous_factors = {
        "dependencies_count": 8,
        "dependents_count": 3,
        "is_spof": False,
    }

    factors = trend_analyzer._identify_contributing_factors(
        current_factors, previous_factors
    )

    assert len(factors) > 0
    assert any("dependencies_count" in f for f in factors)
    assert any("dependents_count" in f for f in factors)


def test_generate_trend_recommendations(trend_analyzer):
    """Test recommendation generation."""
    # Degrading with significant severity
    recs = trend_analyzer._generate_trend_recommendations(
        TrendDirection.DEGRADING,
        TrendSeverity.SIGNIFICANT,
        ["dependency count increased"],
    )

    assert len(recs) > 0
    assert any("increasing" in r.lower() for r in recs)

    # Volatile trend
    recs = trend_analyzer._generate_trend_recommendations(
        TrendDirection.VOLATILE,
        TrendSeverity.MODERATE,
        [],
    )

    assert any("volatile" in r.lower() for r in recs)


def test_overall_health_calculation(trend_analyzer, improving_snapshots, degrading_snapshots):
    """Test overall health calculation."""
    # Create trends
    trends = []

    # Mostly improving
    for i in range(7):
        trend = trend_analyzer.analyze_trend(f"resource-{i}", f"Resource {i}", improving_snapshots)
        trends.append(trend)

    # Few degrading
    for i in range(3):
        trend = trend_analyzer.analyze_trend(
            f"resource-deg-{i}", f"Degrading {i}", degrading_snapshots
        )
        trends.append(trend)

    health = trend_analyzer._calculate_overall_health(trends)

    # Should be good or fair since most are improving
    assert health in ["good", "fair"]


def test_critical_trends_identification(trend_analyzer, degrading_snapshots):
    """Test identification of critical trends."""
    # Create severe degrading snapshots
    severe_snapshots = [
        RiskSnapshot(
            timestamp=datetime(2024, 1, 1) + timedelta(days=i),
            risk_score=30.0 + i * 10,  # Rapid increase
            risk_level="high",
            factors={},
        )
        for i in range(10)
    ]

    trend = trend_analyzer.analyze_trend(
        "critical-resource", "Critical Resource", severe_snapshots
    )

    assert trend.trend_severity in [TrendSeverity.SIGNIFICANT, TrendSeverity.CRITICAL]


def test_prediction_bounds(trend_analyzer, degrading_snapshots):
    """Test that predictions stay within valid bounds."""
    prediction = trend_analyzer.predict_future_risk(degrading_snapshots, days_ahead=30)

    if prediction["predicted_risk_score"] is not None:
        # Risk score should be between 0 and 100
        assert 0 <= prediction["predicted_risk_score"] <= 100


def test_anomaly_severity(trend_analyzer, stable_snapshots):
    """Test anomaly severity classification."""
    snapshots = stable_snapshots.copy()

    # Add moderate anomaly (2-3 std devs)
    snapshots.append(
        RiskSnapshot(
            timestamp=datetime(2024, 1, 11),
            risk_score=70.0,
            risk_level="high",
            factors={},
        )
    )

    # Add severe anomaly (>3 std devs)
    snapshots.append(
        RiskSnapshot(
            timestamp=datetime(2024, 1, 12),
            risk_score=95.0,
            risk_level="critical",
            factors={},
        )
    )

    anomalies = trend_analyzer.detect_anomalies(snapshots, window_size=7)

    # Should have both anomalies with different severities
    if len(anomalies) >= 2:
        severities = [a["severity"] for a in anomalies]
        assert "medium" in severities or "high" in severities


def test_portfolio_recommendations(trend_analyzer, degrading_snapshots):
    """Test portfolio-level recommendations."""
    # Create many degrading trends
    trends = [
        trend_analyzer.analyze_trend(f"resource-{i}", f"Resource {i}", degrading_snapshots)
        for i in range(10)
    ]

    recs = trend_analyzer._generate_portfolio_recommendations(trends)

    assert len(recs) > 0
    # Should mention the number of degrading resources
    assert any("degrading" in r.lower() for r in recs)
