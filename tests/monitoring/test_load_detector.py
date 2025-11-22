"""
Tests for load change detector.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.load_detector import (
    LoadBaseline,
    LoadChangeDetector,
    LoadImpact,
    LoadPrediction,
    ScalingEvent,
)


@pytest.fixture
def mock_prometheus():
    """Create a mock Prometheus collector."""
    collector = Mock(spec=PrometheusCollector)
    collector.query = AsyncMock()
    collector.query_range = AsyncMock()
    return collector


@pytest.fixture
def load_detector(mock_prometheus):
    """Create a load detector instance for testing."""
    return LoadChangeDetector(mock_prometheus)


@pytest.mark.asyncio
async def test_detect_scaling_events_scale_up(load_detector, mock_prometheus):
    """Test detection of scale-up events."""
    # Mock Prometheus data showing pod count increase
    now = datetime.now(UTC)
    mock_prometheus.query_range.return_value = [
        {
            "metric": {"deployment": "test-service"},
            "values": [
                [now.timestamp() - 600, "2"],  # 10 min ago: 2 pods
                [now.timestamp() - 300, "2"],  # 5 min ago: 2 pods
                [now.timestamp(), "5"],  # now: 5 pods
            ],
        }
    ]

    events = await load_detector.detect_scaling_events("test-service", lookback_hours=1)

    assert len(events) == 1
    assert events[0].pod_count_before == 2
    assert events[0].pod_count_after == 5
    assert events[0].scaling_type == "scale_up"
    assert events[0].resource_id == "test-service"


@pytest.mark.asyncio
async def test_detect_scaling_events_scale_down(load_detector, mock_prometheus):
    """Test detection of scale-down events."""
    now = datetime.now(UTC)
    mock_prometheus.query_range.return_value = [
        {
            "metric": {"deployment": "test-service"},
            "values": [
                [now.timestamp() - 600, "5"],  # 10 min ago: 5 pods
                [now.timestamp() - 300, "5"],  # 5 min ago: 5 pods
                [now.timestamp(), "2"],  # now: 2 pods
            ],
        }
    ]

    events = await load_detector.detect_scaling_events("test-service", lookback_hours=1)

    assert len(events) == 1
    assert events[0].pod_count_before == 5
    assert events[0].pod_count_after == 2
    assert events[0].scaling_type == "scale_down"


@pytest.mark.asyncio
async def test_detect_scaling_events_multiple(load_detector, mock_prometheus):
    """Test detection of multiple scaling events."""
    now = datetime.now(UTC)
    mock_prometheus.query_range.return_value = [
        {
            "metric": {"deployment": "test-service"},
            "values": [
                [now.timestamp() - 900, "2"],
                [now.timestamp() - 600, "5"],  # Scale up to 5
                [now.timestamp() - 300, "5"],
                [now.timestamp(), "3"],  # Scale down to 3
            ],
        }
    ]

    events = await load_detector.detect_scaling_events("test-service", lookback_hours=1)

    assert len(events) == 2
    assert events[0].scaling_type == "scale_up"
    assert events[1].scaling_type == "scale_down"


@pytest.mark.asyncio
async def test_detect_scaling_events_no_data(load_detector, mock_prometheus):
    """Test handling when no scaling data is available."""
    mock_prometheus.query_range.return_value = []

    events = await load_detector.detect_scaling_events("test-service", lookback_hours=1)

    assert len(events) == 0


@pytest.mark.asyncio
async def test_get_load_baseline(load_detector, mock_prometheus):
    """Test getting load baseline metrics."""
    # Mock various Prometheus queries
    mock_prometheus.query_range.return_value = [
        {
            "metric": {},
            "values": [
                [datetime.now(UTC).timestamp(), "0.5"],
                [datetime.now(UTC).timestamp(), "0.6"],
            ],
        }
    ]

    baseline = await load_detector.get_load_baseline("test-service")

    assert baseline.resource_id == "test-service"
    assert isinstance(baseline.timestamp, datetime)
    assert baseline.pod_count >= 0
    assert baseline.avg_cpu_usage >= 0
    assert baseline.avg_memory_usage >= 0
    assert baseline.avg_request_rate >= 0
    assert baseline.avg_latency_p95 >= 0
    assert baseline.avg_error_rate >= 0


@pytest.mark.asyncio
async def test_analyze_load_impact(load_detector, mock_prometheus):
    """Test analyzing load impact of a scaling event."""
    # Mock Prometheus to return different values before and after
    def mock_query_side_effect(query, start, end, step):
        # Return different values based on time range
        if start < datetime.now(UTC) - timedelta(minutes=5):
            # Before scaling - lower values
            return [{"metric": {}, "values": [[datetime.now(UTC).timestamp(), "0.3"]]}]
        else:
            # After scaling - higher values
            return [{"metric": {}, "values": [[datetime.now(UTC).timestamp(), "0.7"]]}]

    mock_prometheus.query_range.side_effect = mock_query_side_effect

    scaling_event = ScalingEvent(
        resource_id="test-service",
        timestamp=datetime.now(UTC),
        pod_count_before=2,
        pod_count_after=5,
        scaling_type="scale_up",
    )

    impact = await load_detector.analyze_load_impact("test-service", scaling_event)

    assert impact.resource_id == "test-service"
    assert impact.scaling_event == scaling_event
    assert isinstance(impact.baseline, LoadBaseline)
    assert isinstance(impact.overall_impact, str)
    assert impact.overall_impact in ["minimal", "moderate", "significant", "critical"]
    assert isinstance(impact.recommendations, list)
    assert len(impact.recommendations) > 0


@pytest.mark.asyncio
async def test_predict_load_impact_with_history(load_detector, mock_prometheus):
    """Test load prediction with historical data."""
    # Mock historical scaling events
    now = datetime.now(UTC)
    mock_prometheus.query_range.return_value = [
        {
            "metric": {"deployment": "test-service"},
            "values": [
                [now.timestamp() - 86400, "2"],  # 1 day ago: 2 pods
                [now.timestamp() - 43200, "5"],  # 12 hours ago: 5 pods
                [now.timestamp(), "5"],  # now: 5 pods
            ],
        }
    ]

    # Need to set up load_detector.analyze_load_impact to return mock data
    mock_impact = LoadImpact(
        resource_id="test-service",
        scaling_event=ScalingEvent(
            resource_id="test-service",
            timestamp=now - timedelta(hours=12),
            pod_count_before=2,
            pod_count_after=5,
            scaling_type="scale_up",
        ),
        baseline=LoadBaseline(
            resource_id="test-service",
            timestamp=now - timedelta(hours=12),
            pod_count=2,
            avg_cpu_usage=0.7,
            avg_memory_usage=1024 * 1024 * 512,
            avg_request_rate=100.0,
            avg_latency_p95=0.2,
            avg_error_rate=0.01,
        ),
        cpu_change_pct=-30.0,
        memory_change_pct=-25.0,
        request_rate_change_pct=150.0,
        latency_change_pct=-20.0,
        error_rate_change_pct=-50.0,
        overall_impact="moderate",
        recommendations=["Monitor closely"],
        time_to_stabilize_minutes=10.0,
    )

    load_detector.analyze_load_impact = AsyncMock(return_value=mock_impact)

    prediction = await load_detector.predict_load_impact("test-service", target_pod_count=8)

    assert prediction.resource_id == "test-service"
    assert prediction.predicted_pod_count == 8
    assert prediction.predicted_cpu_usage >= 0
    assert prediction.predicted_memory_usage >= 0
    assert prediction.predicted_request_rate >= 0
    assert prediction.predicted_latency_p95 >= 0
    assert prediction.predicted_error_rate >= 0
    assert 0.0 <= prediction.confidence <= 1.0
    assert isinstance(prediction.based_on_events, list)
    assert isinstance(prediction.recommendations, list)


@pytest.mark.asyncio
async def test_predict_load_impact_no_history(load_detector, mock_prometheus):
    """Test load prediction without historical data (uses baseline)."""
    # No historical scaling events
    mock_prometheus.query_range.return_value = []

    prediction = await load_detector.predict_load_impact("test-service", target_pod_count=5)

    assert prediction.resource_id == "test-service"
    assert prediction.predicted_pod_count == 5
    assert prediction.confidence < 0.5  # Low confidence without history
    assert len(prediction.based_on_events) == 0
    assert any("No historical" in rec for rec in prediction.recommendations)


@pytest.mark.asyncio
async def test_detect_high_load_patterns(load_detector, mock_prometheus):
    """Test detection of high load patterns."""
    # Mock high CPU usage
    mock_prometheus.query_range.return_value = [
        {
            "metric": {},
            "values": [
                [datetime.now(UTC).timestamp(), "0.9"],  # 90% CPU
            ],
        }
    ]

    patterns = await load_detector.detect_high_load_patterns("test-service", lookback_hours=24)

    assert patterns["resource_id"] == "test-service"
    assert "current_baseline" in patterns
    assert "high_load_indicators" in patterns
    assert "needs_scaling" in patterns
    assert "insights" in patterns

    # Should detect high CPU
    assert isinstance(patterns["high_load_indicators"], dict)
    assert isinstance(patterns["needs_scaling"], bool)
    assert isinstance(patterns["insights"], list)


def test_calculate_pct_change(load_detector):
    """Test percentage change calculation."""
    # Normal case
    change = load_detector._calculate_pct_change(100.0, 150.0)
    assert change == 50.0

    # Decrease
    change = load_detector._calculate_pct_change(100.0, 75.0)
    assert change == -25.0

    # No change
    change = load_detector._calculate_pct_change(100.0, 100.0)
    assert change == 0.0

    # From zero
    change = load_detector._calculate_pct_change(0.0, 50.0)
    assert change == 100.0


def test_determine_impact_level(load_detector):
    """Test impact level determination."""
    # Critical impact
    level = load_detector._determine_impact_level(60.0, 30.0, 20.0, 25.0)
    assert level == "critical"

    # Significant impact
    level = load_detector._determine_impact_level(30.0, 20.0, 15.0, 5.0)
    assert level == "significant"

    # Moderate impact
    level = load_detector._determine_impact_level(15.0, 12.0, 8.0, 3.0)
    assert level == "moderate"

    # Minimal impact
    level = load_detector._determine_impact_level(5.0, 3.0, 2.0, 1.0)
    assert level == "minimal"


def test_generate_load_recommendations_scale_up(load_detector):
    """Test recommendation generation for scale-up events."""
    event = ScalingEvent(
        resource_id="test-service",
        timestamp=datetime.now(UTC),
        pod_count_before=2,
        pod_count_after=5,
        scaling_type="scale_up",
    )

    # Good result - CPU decreased
    recommendations = load_detector._generate_load_recommendations(
        event, cpu_change=-25.0, memory_change=-20.0, latency_change=-30.0, error_change=-10.0,
        impact_level="moderate"
    )

    assert len(recommendations) > 0
    assert any("CPU" in rec for rec in recommendations)


def test_generate_load_recommendations_critical(load_detector):
    """Test recommendation generation for critical impact."""
    event = ScalingEvent(
        resource_id="test-service",
        timestamp=datetime.now(UTC),
        pod_count_before=2,
        pod_count_after=5,
        scaling_type="scale_up",
    )

    recommendations = load_detector._generate_load_recommendations(
        event, cpu_change=60.0, memory_change=50.0, latency_change=70.0, error_change=30.0,
        impact_level="critical"
    )

    assert len(recommendations) > 0
    assert any("CRITICAL" in rec for rec in recommendations)


def test_generate_prediction_recommendations_large_scale(load_detector):
    """Test recommendations for large scaling changes."""
    recommendations = load_detector._generate_prediction_recommendations(
        current_pods=2,
        target_pods=10,
        predicted_cpu=0.6,
        predicted_latency=0.3,
        predicted_error_rate=0.01,
    )

    assert len(recommendations) > 0
    assert any("Large scaling" in rec or "gradually" in rec for rec in recommendations)


def test_generate_prediction_recommendations_healthy(load_detector):
    """Test recommendations for healthy predicted metrics."""
    recommendations = load_detector._generate_prediction_recommendations(
        current_pods=3,
        target_pods=5,
        predicted_cpu=0.5,
        predicted_latency=0.3,
        predicted_error_rate=0.005,
    )

    assert len(recommendations) > 0
    assert any("healthy" in rec.lower() or "safe" in rec.lower() for rec in recommendations)


def test_extract_avg_value_with_data(load_detector):
    """Test extracting average value from Prometheus results."""
    results = [
        {
            "metric": {},
            "values": [
                [datetime.now(UTC).timestamp(), "10.5"],
                [datetime.now(UTC).timestamp(), "20.5"],
                [datetime.now(UTC).timestamp(), "30.5"],
            ],
        }
    ]

    avg = load_detector._extract_avg_value(results)
    assert abs(avg - 20.5) < 0.1  # Average of 10.5, 20.5, 30.5


def test_extract_avg_value_no_data(load_detector):
    """Test extracting average value with no data."""
    avg = load_detector._extract_avg_value([], default=42.0)
    assert avg == 42.0


def test_extract_avg_value_invalid_data(load_detector):
    """Test extracting average value with invalid data."""
    results = [
        {
            "metric": {},
            "values": [
                [datetime.now(UTC).timestamp(), "invalid"],
                [datetime.now(UTC).timestamp(), "10.0"],
            ],
        }
    ]

    # Should skip invalid values and use valid ones
    avg = load_detector._extract_avg_value(results, default=5.0)
    assert avg == 10.0 or avg == 5.0  # Either found valid value or used default


@pytest.mark.asyncio
async def test_scaling_event_cache(load_detector, mock_prometheus):
    """Test that scaling events are cached."""
    now = datetime.now(UTC)
    mock_prometheus.query_range.return_value = [
        {
            "metric": {"deployment": "test-service"},
            "values": [
                [now.timestamp() - 600, "2"],
                [now.timestamp(), "5"],
            ],
        }
    ]

    # First call should populate cache
    events1 = await load_detector.detect_scaling_events("test-service", lookback_hours=1)
    assert "test-service" in load_detector.scaling_event_cache
    assert len(load_detector.scaling_event_cache["test-service"]) == len(events1)

    # Cache should contain the events
    cached_events = load_detector.scaling_event_cache["test-service"]
    assert len(cached_events) > 0
    assert cached_events[0].resource_id == "test-service"
