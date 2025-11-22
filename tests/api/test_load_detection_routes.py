"""
Tests for load detection API endpoints.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from topdeck.api.main import app
from topdeck.monitoring.load_detector import (
    LoadBaseline,
    LoadImpact,
    LoadPrediction,
    ScalingEvent,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_load_detector():
    """Create a mock load detector."""
    detector = Mock()
    detector.detect_scaling_events = AsyncMock()
    detector.get_load_baseline = AsyncMock()
    detector.analyze_load_impact = AsyncMock()
    detector.predict_load_impact = AsyncMock()
    detector.detect_high_load_patterns = AsyncMock()
    return detector


@pytest.mark.asyncio
async def test_get_scaling_events_success(client, mock_load_detector):
    """Test successful scaling events retrieval."""
    # Mock scaling events
    now = datetime.now(UTC)
    events = [
        ScalingEvent(
            resource_id="test-service",
            timestamp=now,
            pod_count_before=2,
            pod_count_after=5,
            scaling_type="scale_up",
        )
    ]
    mock_load_detector.detect_scaling_events.return_value = events

    with patch(
        "topdeck.api.routes.load_detection.load_detector", mock_load_detector
    ):
        response = client.get("/api/v1/load/resources/test-service/scaling-events?lookback_hours=24")

    assert response.status_code == 200
    data = response.json()
    assert data["resource_id"] == "test-service"
    assert data["lookback_hours"] == 24
    assert data["events_count"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["scaling_type"] == "scale_up"
    assert data["events"][0]["pod_count_before"] == 2
    assert data["events"][0]["pod_count_after"] == 5


@pytest.mark.asyncio
async def test_get_scaling_events_no_events(client, mock_load_detector):
    """Test scaling events retrieval with no events found."""
    mock_load_detector.detect_scaling_events.return_value = []

    with patch(
        "topdeck.api.routes.load_detection.load_detector", mock_load_detector
    ):
        response = client.get("/api/v1/load/resources/test-service/scaling-events")

    assert response.status_code == 200
    data = response.json()
    assert data["events_count"] == 0
    assert len(data["events"]) == 0


@pytest.mark.asyncio
async def test_get_load_baseline_success(client, mock_load_detector):
    """Test successful load baseline retrieval."""
    baseline = LoadBaseline(
        resource_id="test-service",
        timestamp=datetime.now(UTC),
        pod_count=3,
        avg_cpu_usage=0.65,
        avg_memory_usage=1024 * 1024 * 512,
        avg_request_rate=150.0,
        avg_latency_p95=0.25,
        avg_error_rate=0.02,
    )
    mock_load_detector.get_load_baseline.return_value = baseline

    with patch(
        "topdeck.api.routes.load_detection.load_detector", mock_load_detector
    ):
        response = client.get("/api/v1/load/resources/test-service/baseline")

    assert response.status_code == 200
    data = response.json()
    assert data["resource_id"] == "test-service"
    assert data["pod_count"] == 3
    assert "metrics" in data
    assert data["metrics"]["cpu_usage"] == 0.65
    assert data["metrics"]["request_rate"] == 150.0


@pytest.mark.asyncio
async def test_analyze_scaling_impact_success(client, mock_load_detector):
    """Test successful scaling impact analysis."""
    now = datetime.now(UTC)
    scaling_event = ScalingEvent(
        resource_id="test-service",
        timestamp=now,
        pod_count_before=2,
        pod_count_after=5,
        scaling_type="scale_up",
    )

    impact = LoadImpact(
        resource_id="test-service",
        scaling_event=scaling_event,
        baseline=LoadBaseline(
            resource_id="test-service",
            timestamp=now,
            pod_count=2,
            avg_cpu_usage=0.75,
            avg_memory_usage=1024 * 1024 * 512,
            avg_request_rate=100.0,
            avg_latency_p95=0.3,
            avg_error_rate=0.03,
        ),
        cpu_change_pct=-30.0,
        memory_change_pct=-25.0,
        request_rate_change_pct=150.0,
        latency_change_pct=-20.0,
        error_rate_change_pct=-40.0,
        overall_impact="moderate",
        recommendations=["Monitor metrics closely", "Good scaling result"],
        time_to_stabilize_minutes=15.0,
    )

    mock_load_detector.detect_scaling_events.return_value = [scaling_event]
    mock_load_detector.analyze_load_impact.return_value = impact

    with patch(
        "topdeck.api.routes.load_detection.load_detector", mock_load_detector
    ):
        response = client.get("/api/v1/load/resources/test-service/impact-analysis?lookback_hours=24")

    assert response.status_code == 200
    data = response.json()
    assert data["resource_id"] == "test-service"
    assert data["events_analyzed"] == 1
    assert len(data["impacts"]) == 1

    impact_data = data["impacts"][0]
    assert impact_data["overall_impact"] == "moderate"
    assert impact_data["changes"]["cpu_change_pct"] == -30.0
    assert len(impact_data["recommendations"]) == 2


@pytest.mark.asyncio
async def test_analyze_scaling_impact_no_events(client, mock_load_detector):
    """Test scaling impact analysis with no events."""
    mock_load_detector.detect_scaling_events.return_value = []

    with patch(
        "topdeck.api.routes.load_detection.load_detector", mock_load_detector
    ):
        response = client.get("/api/v1/load/resources/test-service/impact-analysis")

    assert response.status_code == 200
    data = response.json()
    assert "No scaling events detected" in data["message"]
    assert len(data["impacts"]) == 0


@pytest.mark.asyncio
async def test_predict_load_success(client, mock_load_detector):
    """Test successful load prediction."""
    prediction = LoadPrediction(
        resource_id="test-service",
        predicted_pod_count=8,
        predicted_cpu_usage=0.55,
        predicted_memory_usage=1024 * 1024 * 600,
        predicted_request_rate=200.0,
        predicted_latency_p95=0.22,
        predicted_error_rate=0.015,
        confidence=0.85,
        based_on_events=[
            ScalingEvent(
                resource_id="test-service",
                timestamp=datetime.now(UTC),
                pod_count_before=3,
                pod_count_after=6,
                scaling_type="scale_up",
            )
        ],
        recommendations=["Predicted metrics look healthy", "Safe to proceed"],
    )

    mock_load_detector.predict_load_impact.return_value = prediction

    with patch(
        "topdeck.api.routes.load_detection.load_detector", mock_load_detector
    ):
        response = client.get(
            "/api/v1/load/resources/test-service/predict-load?target_pod_count=8&lookback_days=30"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["resource_id"] == "test-service"
    assert data["target_pod_count"] == 8
    assert data["confidence"] == 0.85
    assert "predicted_metrics" in data
    assert data["predicted_metrics"]["cpu_usage"] == 0.55
    assert len(data["recommendations"]) == 2
    assert len(data["based_on_events"]) == 1


@pytest.mark.asyncio
async def test_predict_load_missing_target_pod_count(client):
    """Test load prediction without target pod count."""
    response = client.get("/api/v1/load/resources/test-service/predict-load")
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_detect_high_load_patterns_success(client, mock_load_detector):
    """Test successful high load pattern detection."""
    now = datetime.now(UTC)
    patterns = {
        "resource_id": "test-service",
        "current_baseline": LoadBaseline(
            resource_id="test-service",
            timestamp=now,
            pod_count=3,
            avg_cpu_usage=0.85,  # High CPU
            avg_memory_usage=1024 * 1024 * 512,
            avg_request_rate=200.0,
            avg_latency_p95=0.8,
            avg_error_rate=0.02,
        ),
        "scaling_events_count": 2,
        "recent_scaling_events": [
            ScalingEvent(
                resource_id="test-service",
                timestamp=now,
                pod_count_before=2,
                pod_count_after=3,
                scaling_type="scale_up",
            )
        ],
        "high_load_indicators": {
            "high_cpu": True,
            "high_memory": False,
            "high_latency": False,
            "high_errors": False,
        },
        "needs_scaling": True,
        "insights": [
            "CPU usage is high (85.0%). Consider scaling up or optimizing CPU-intensive operations.",
            "Detected 2 scaling events in the last 24 hours. Service has been experiencing load changes.",
        ],
    }

    mock_load_detector.detect_high_load_patterns.return_value = patterns

    with patch(
        "topdeck.api.routes.load_detection.load_detector", mock_load_detector
    ):
        response = client.get("/api/v1/load/resources/test-service/high-load-patterns?lookback_hours=24")

    assert response.status_code == 200
    data = response.json()
    assert data["resource_id"] == "test-service"
    assert data["needs_scaling"] is True
    assert data["high_load_indicators"]["high_cpu"] is True
    assert len(data["insights"]) == 2
    assert "current_baseline" in data
    assert data["scaling_events_count"] == 2


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/load/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "load-detection"
    assert "prometheus_url" in data
    assert "components" in data


@pytest.mark.asyncio
async def test_lookback_hours_validation(client):
    """Test validation of lookback_hours parameter."""
    # Test with lookback_hours too high
    response = client.get("/api/v1/load/resources/test-service/scaling-events?lookback_hours=200")
    assert response.status_code == 422  # Validation error

    # Test with lookback_hours too low
    response = client.get("/api/v1/load/resources/test-service/scaling-events?lookback_hours=0")
    assert response.status_code == 422  # Validation error

    # Test with valid lookback_hours
    with patch(
        "topdeck.api.routes.load_detection.load_detector.detect_scaling_events",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = client.get("/api/v1/load/resources/test-service/scaling-events?lookback_hours=48")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_lookback_days_validation(client):
    """Test validation of lookback_days parameter."""
    # Test with lookback_days too high
    response = client.get("/api/v1/load/resources/test-service/predict-load?target_pod_count=5&lookback_days=100")
    assert response.status_code == 422  # Validation error

    # Test with lookback_days too low
    response = client.get("/api/v1/load/resources/test-service/predict-load?target_pod_count=5&lookback_days=0")
    assert response.status_code == 422  # Validation error
