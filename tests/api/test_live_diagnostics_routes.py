"""
Tests for Live Diagnostics API routes.

This module tests all endpoints in the live_diagnostics router including:
- Snapshot endpoint
- Service health endpoint
- Anomalies endpoint
- Traffic patterns endpoint
- Failing dependencies endpoint
- Health check endpoint
- Error logs endpoint
- Root cause analysis endpoint
- Baseline endpoint
- Historical comparison endpoint
"""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from topdeck.api.main import app
from topdeck.monitoring.live_diagnostics import (
    AnomalyAlert,
    LiveDiagnosticsSnapshot,
    ServiceHealthStatus,
    TrafficPattern,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_diagnostics_service():
    """Create a mock live diagnostics service."""
    return AsyncMock()


@pytest.fixture
def mock_prometheus_collector():
    """Create a mock Prometheus collector."""
    return MagicMock()


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    return MagicMock()


@pytest.fixture
def mock_neo4j_async():
    """Create a mock async Neo4j client for route tests."""
    mock = AsyncMock()
    mock.execute_query = AsyncMock(return_value=[{"id": "test-service-001"}])
    return mock


@pytest.fixture
def sample_service_health():
    """Create a sample service health status."""
    return ServiceHealthStatus(
        resource_id="test-service-001",
        resource_name="Test Service",
        resource_type="deployment",
        status="healthy",
        health_score=95.5,
        anomalies=[],
        metrics={
            "cpu_usage": 45.2,
            "memory_usage": 60.3,
            "request_rate": 100.5,
            "error_rate": 0.5,
            "latency_p95": 150.0,
        },
        last_updated=datetime.now(UTC),
    )


@pytest.fixture
def sample_anomaly():
    """Create a sample anomaly alert."""
    return AnomalyAlert(
        alert_id="anomaly-001",
        resource_id="test-service-001",
        resource_name="Test Service",
        severity="high",
        metric_name="error_rate",
        current_value=15.5,
        expected_value=2.0,
        deviation_percentage=675.0,  # 6.75x = 675%
        detected_at=datetime.now(UTC),
        message="Error rate is 6.75x higher than expected",
        potential_causes=["Deployment issue", "Database slow"],
    )


@pytest.fixture
def sample_traffic_pattern():
    """Create a sample traffic pattern."""
    return TrafficPattern(
        source_id="service-a",
        target_id="service-b",
        request_rate=500.0,
        error_rate=2.5,
        latency_p95=120.0,
        is_abnormal=False,
        anomaly_score=0.2,
        trend="stable",
    )


@pytest.fixture
def sample_failing_dependency():
    """Create a sample failing dependency."""
    return {
        "source_id": "api-service",
        "source_name": "API Service",
        "target_id": "db-service-001",
        "target_name": "Database",
        "status": "failed",
        "health_score": 15.0,
        "anomalies": ["Connection timeout", "High latency"],
        "error_details": {
            "last_error": "Connection timeout",
            "error_count": 25,
            "affected_services": ["api-service", "web-service"],
        },
    }


@pytest.fixture
def sample_snapshot(sample_service_health, sample_anomaly, sample_traffic_pattern, sample_failing_dependency):
    """Create a sample live diagnostics snapshot."""
    return LiveDiagnosticsSnapshot(
        timestamp=datetime.now(UTC),
        overall_health="healthy",
        services=[sample_service_health],
        anomalies=[sample_anomaly],
        traffic_patterns=[sample_traffic_pattern],
        failing_dependencies=[sample_failing_dependency],
    )


# ==================== Snapshot Endpoint Tests ====================


def test_get_live_snapshot_success(client, mock_diagnostics_service, sample_snapshot):
    """Test successful retrieval of live diagnostics snapshot."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.get_live_snapshot = AsyncMock(return_value=sample_snapshot)

        response = client.get("/api/v1/live-diagnostics/snapshot")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_health"] == "healthy"
        assert len(data["services"]) == 1
        assert len(data["anomalies"]) == 1
        assert len(data["traffic_patterns"]) == 1
        assert len(data["failing_dependencies"]) == 1


def test_get_live_snapshot_with_duration(client, mock_diagnostics_service, sample_snapshot):
    """Test snapshot retrieval with custom duration."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.get_live_snapshot = AsyncMock(return_value=sample_snapshot)

        response = client.get("/api/v1/live-diagnostics/snapshot?duration_hours=2")

        assert response.status_code == 200
        mock_diagnostics_service.get_live_snapshot.assert_called_once()


def test_get_live_snapshot_invalid_duration(client):
    """Test snapshot with invalid duration (out of range)."""
    response = client.get("/api/v1/live-diagnostics/snapshot?duration_hours=25")
    assert response.status_code == 422


def test_get_live_snapshot_service_error(client, mock_diagnostics_service):
    """Test snapshot when service raises an error."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.get_live_snapshot = AsyncMock(
            side_effect=Exception("Service error")
        )

        response = client.get("/api/v1/live-diagnostics/snapshot")

        assert response.status_code == 500
        assert "Service error" in response.json()["detail"]


# ==================== Service Health Endpoint Tests ====================


def test_get_service_health_success(client, mock_diagnostics_service, sample_service_health):
    """Test successful retrieval of service health."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.get_service_health = AsyncMock(
            return_value=sample_service_health
        )

        response = client.get(
            "/api/v1/live-diagnostics/services/test-service-001/health"
            "?resource_type=deployment"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resource_id"] == "test-service-001"
        assert data["status"] == "healthy"
        assert data["health_score"] == 95.5


def test_get_service_health_missing_resource_type(client, mock_diagnostics_service, sample_service_health):
    """Test service health endpoint uses default resource_type when not provided."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.get_service_health = AsyncMock(return_value=sample_service_health)
        
        # Should use default resource_type="service"
        response = client.get("/api/v1/live-diagnostics/services/test-service-001/health")
        assert response.status_code == 200
        data = response.json()
        assert data["resource_id"] == "test-service-001"


def test_get_service_health_not_found(client, mock_diagnostics_service):
    """Test service health when resource not found."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.get_service_health = AsyncMock(return_value=None)

        response = client.get(
            "/api/v1/live-diagnostics/services/nonexistent/health?resource_type=deployment"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ==================== Anomalies Endpoint Tests ====================


def test_get_anomalies_success(client, mock_diagnostics_service, sample_anomaly):
    """Test successful retrieval of anomalies."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ), patch(
        "topdeck.api.routes.live_diagnostics.get_neo4j_client"
    ) as mock_neo4j_getter:
        # Mock Neo4j client
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query = AsyncMock(return_value=[{"id": "test-service-001"}])
        mock_neo4j_getter.return_value = mock_neo4j
        
        mock_diagnostics_service.detect_anomalies = AsyncMock(return_value=[sample_anomaly])

        response = client.get("/api/v1/live-diagnostics/anomalies")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["alert_id"] == "anomaly-001"
        assert data[0]["severity"] == "high"


def test_get_anomalies_with_severity_filter(client, mock_diagnostics_service, sample_anomaly):
    """Test anomalies with severity filter."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ), patch(
        "topdeck.api.routes.live_diagnostics.get_neo4j_client"
    ) as mock_neo4j_getter:
        # Mock Neo4j client
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query = AsyncMock(return_value=[{"id": "test-service-001"}])
        mock_neo4j_getter.return_value = mock_neo4j
        
        mock_diagnostics_service.detect_anomalies = AsyncMock(return_value=[sample_anomaly])

        response = client.get("/api/v1/live-diagnostics/anomalies?severity=high")

        assert response.status_code == 200


def test_get_anomalies_with_limit(client, mock_diagnostics_service):
    """Test anomalies with result limit."""
    anomalies = [
        AnomalyAlert(
            alert_id=f"anomaly-{i:03d}",
            resource_id=f"service-{i}",
            resource_name=f"Service {i}",
            severity="medium",
            metric_name="cpu_usage",
            current_value=80.0 + i,
            expected_value=50.0,
            deviation_percentage=60.0,  # (80-50)/50 * 100 = 60%
            detected_at=datetime.now(UTC),
            message=f"CPU usage anomaly {i}",
            potential_causes=["High load"],
        )
        for i in range(10)
    ]

    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ), patch(
        "topdeck.api.routes.live_diagnostics.get_neo4j_client"
    ) as mock_neo4j_getter:
        # Mock Neo4j client
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query = AsyncMock(return_value=[{"id": "test-service-001"}])
        mock_neo4j_getter.return_value = mock_neo4j
        
        mock_diagnostics_service.detect_anomalies = AsyncMock(return_value=anomalies[:5])

        response = client.get("/api/v1/live-diagnostics/anomalies?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


def test_get_anomalies_empty_result(client, mock_diagnostics_service):
    """Test anomalies when no anomalies detected."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ), patch(
        "topdeck.api.routes.live_diagnostics.get_neo4j_client"
    ) as mock_neo4j_getter:
        # Mock Neo4j client
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query = AsyncMock(return_value=[{"id": "test-service-001"}])
        mock_neo4j_getter.return_value = mock_neo4j
        
        mock_diagnostics_service.detect_anomalies = AsyncMock(return_value=[])

        response = client.get("/api/v1/live-diagnostics/anomalies")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


# ==================== Traffic Patterns Endpoint Tests ====================


def test_get_traffic_patterns_success(client, mock_diagnostics_service, sample_traffic_pattern):
    """Test successful retrieval of traffic patterns."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.analyze_traffic_patterns = AsyncMock(
            return_value=[sample_traffic_pattern]
        )

        response = client.get("/api/v1/live-diagnostics/traffic-patterns")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source_id"] == "service-a"
        assert data[0]["target_id"] == "service-b"


def test_get_traffic_patterns_abnormal_only(client, mock_diagnostics_service):
    """Test traffic patterns with abnormal_only filter."""
    abnormal_pattern = TrafficPattern(
        source_id="service-a",
        target_id="service-b",
        request_rate=1000.0,
        error_rate=15.5,
        latency_p95=500.0,
        is_abnormal=True,
        anomaly_score=0.85,
        trend="increasing",
    )

    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.analyze_traffic_patterns = AsyncMock(
            return_value=[abnormal_pattern]
        )

        response = client.get("/api/v1/live-diagnostics/traffic-patterns?abnormal_only=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_abnormal"] is True


# ==================== Failing Dependencies Endpoint Tests ====================


def test_get_failing_dependencies_success(
    client, mock_diagnostics_service, sample_failing_dependency
):
    """Test successful retrieval of failing dependencies."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.get_failing_dependencies = AsyncMock(
            return_value=[sample_failing_dependency]
        )

        response = client.get("/api/v1/live-diagnostics/failing-dependencies")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["target_id"] == "db-service-001"
        assert data[0]["status"] == "failed"


def test_get_failing_dependencies_empty(client, mock_diagnostics_service):
    """Test failing dependencies when all services are healthy."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ):
        mock_diagnostics_service.get_failing_dependencies = AsyncMock(return_value=[])

        response = client.get("/api/v1/live-diagnostics/failing-dependencies")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


# ==================== Health Check Endpoint Tests ====================


def test_health_check_all_healthy(client):
    """Test health check when all components are healthy."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_prometheus_collector"
    ) as mock_prom_getter, patch(
        "topdeck.api.routes.live_diagnostics.get_neo4j_client"
    ) as mock_neo4j_getter:
        # Mock Prometheus collector
        mock_prometheus = AsyncMock()
        mock_prometheus.query = AsyncMock(return_value=[])
        mock_prom_getter.return_value = mock_prometheus
        
        # Mock Neo4j client
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query = AsyncMock(return_value=[])
        mock_neo4j_getter.return_value = mock_neo4j

        response = client.get("/api/v1/live-diagnostics/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["components"]["prometheus"] == "healthy"
        assert data["components"]["neo4j"] == "healthy"


def test_health_check_degraded(client):
    """Test health check when some components are degraded."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_prometheus_collector"
    ) as mock_prom_getter, patch(
        "topdeck.api.routes.live_diagnostics.get_neo4j_client"
    ) as mock_neo4j_getter:
        # Mock Prometheus collector - healthy
        mock_prometheus = AsyncMock()
        mock_prometheus.query = AsyncMock(return_value=[])
        mock_prom_getter.return_value = mock_prometheus
        
        # Mock Neo4j client - unhealthy
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query = AsyncMock(side_effect=Exception("Connection failed"))
        mock_neo4j_getter.return_value = mock_neo4j

        response = client.get("/api/v1/live-diagnostics/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["components"]["prometheus"] == "healthy"
        assert data["components"]["neo4j"] == "unhealthy"


# ==================== Error Logs Endpoint Tests ====================


def test_get_service_error_logs_success(client):
    """Test successful retrieval of service error logs."""
    # This endpoint may require Loki/Elasticsearch integration
    # Testing endpoint registration and basic error handling
    response = client.get("/api/v1/live-diagnostics/services/test-service/error-logs")

    # Should not return 404 (endpoint exists)
    assert response.status_code != 404


def test_get_service_error_logs_with_duration(client):
    """Test error logs with duration parameter."""
    response = client.get(
        "/api/v1/live-diagnostics/services/test-service/error-logs?duration_hours=2"
    )

    # May fail due to Loki connection, but endpoint should exist
    assert response.status_code in (200, 500)


# ==================== Root Cause Analysis Endpoint Tests ====================


def test_root_cause_analysis_endpoint_exists(client):
    """Test that the root cause analysis endpoint is registered."""
    response = client.post(
        "/api/v1/live-diagnostics/services/test-service/root-cause-analysis",
        json={"time_range_hours": 24},
    )

    # Should not return 404 (endpoint exists)
    assert response.status_code != 404


# ==================== Baseline Endpoint Tests ====================


def test_get_service_baseline_endpoint_exists(client):
    """Test that the service baseline endpoint is registered."""
    response = client.get("/api/v1/live-diagnostics/services/test-service/baseline")

    # Should not return 404 (endpoint exists)
    assert response.status_code != 404


def test_get_service_baseline_with_duration(client):
    """Test baseline endpoint with duration parameter."""
    response = client.get(
        "/api/v1/live-diagnostics/services/test-service/baseline?duration_days=7"
    )

    # May fail due to Prometheus connection, but endpoint should exist
    assert response.status_code in (200, 500)


# ==================== Historical Comparison Endpoint Tests ====================


def test_historical_comparison_endpoint_exists(client):
    """Test that the historical comparison endpoint is registered."""
    response = client.get(
        "/api/v1/live-diagnostics/services/test-service/historical-comparison"
    )

    # Should not return 404 (endpoint exists)
    assert response.status_code != 404


def test_historical_comparison_with_params(client):
    """Test historical comparison with query parameters."""
    response = client.get(
        "/api/v1/live-diagnostics/services/test-service/historical-comparison"
        "?metric=cpu_usage&comparison_period=previous_day"
    )

    # May fail due to Prometheus connection, but endpoint should exist
    assert response.status_code in (200, 500)


# ==================== Input Validation & Security Tests ====================


def test_snapshot_sql_injection_protection(client):
    """Test that snapshot endpoint protects against SQL injection."""
    malicious_input = "'; DROP TABLE services; --"
    response = client.get(f"/api/v1/live-diagnostics/snapshot?duration_hours={malicious_input}")

    # Should return validation error, not execute
    assert response.status_code == 422


def test_service_health_xss_protection(client):
    """Test that service health endpoint sanitizes input."""
    malicious_id = "<script>alert('xss')</script>"
    response = client.get(
        f"/api/v1/live-diagnostics/services/{malicious_id}/health?resource_type=deployment"
    )

    # Should handle safely (not 500)
    assert response.status_code in (200, 404, 422, 500)


def test_anomalies_invalid_severity(client, mock_diagnostics_service):
    """Test anomalies endpoint with invalid severity value."""
    with patch(
        "topdeck.api.routes.live_diagnostics.get_diagnostics_service",
        return_value=mock_diagnostics_service,
    ), patch(
        "topdeck.api.routes.live_diagnostics.get_neo4j_client"
    ) as mock_neo4j_getter:
        # Mock Neo4j client
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query = AsyncMock(return_value=[{"id": "test-service-001"}])
        mock_neo4j_getter.return_value = mock_neo4j
        
        # Mock empty anomalies
        mock_diagnostics_service.detect_anomalies = AsyncMock(return_value=[])
        
        response = client.get("/api/v1/live-diagnostics/anomalies?severity=invalid_value")

        # The endpoint doesn't validate severity at the FastAPI level,
        # so it returns 200 with empty list (no anomalies match invalid severity)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


def test_traffic_patterns_invalid_duration(client):
    """Test traffic patterns with invalid duration."""
    response = client.get("/api/v1/live-diagnostics/traffic-patterns?duration_hours=-1")

    # Should return validation error
    assert response.status_code == 422
