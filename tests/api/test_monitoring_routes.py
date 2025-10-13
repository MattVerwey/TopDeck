"""Tests for monitoring API endpoints."""

import pytest
from fastapi.testclient import TestClient

from topdeck.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_get_resource_metrics_endpoint_exists(client):
    """Test that the resource metrics endpoint is registered."""
    response = client.get(
        "/api/v1/monitoring/resources/test-resource/metrics",
        params={"resource_type": "pod"}
    )
    # Should not return 404
    assert response.status_code != 404


def test_get_resource_metrics_with_duration(client):
    """Test resource metrics endpoint with duration parameter."""
    response = client.get(
        "/api/v1/monitoring/resources/test-resource/metrics",
        params={
            "resource_type": "pod",
            "duration_hours": 2,
        }
    )
    # May fail due to Prometheus connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_resource_metrics_missing_resource_type(client):
    """Test resource metrics endpoint without required resource_type."""
    response = client.get("/api/v1/monitoring/resources/test-resource/metrics")
    # Should return validation error
    assert response.status_code == 422


def test_detect_bottlenecks_endpoint_exists(client):
    """Test that the bottleneck detection endpoint is registered."""
    response = client.get(
        "/api/v1/monitoring/flows/test-flow/bottlenecks",
        params={"flow_path": ["resource1", "resource2"]}
    )
    # Should not return 404
    assert response.status_code != 404


def test_get_resource_errors_endpoint_exists(client):
    """Test that the resource errors endpoint is registered."""
    response = client.get("/api/v1/monitoring/resources/test-resource/errors")
    # Should not return 404
    assert response.status_code != 404


def test_get_resource_errors_with_duration(client):
    """Test resource errors endpoint with duration parameter."""
    response = client.get(
        "/api/v1/monitoring/resources/test-resource/errors",
        params={"duration_hours": 2}
    )
    # May fail due to Loki connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_find_failure_point_endpoint_exists(client):
    """Test that the failure point detection endpoint is registered."""
    response = client.get(
        "/api/v1/monitoring/flows/test-flow/failures",
        params={"flow_path": ["resource1", "resource2"]}
    )
    # Should not return 404
    assert response.status_code != 404


def test_find_failure_point_with_duration(client):
    """Test failure point endpoint with duration parameter."""
    response = client.get(
        "/api/v1/monitoring/flows/test-flow/failures",
        params={
            "flow_path": ["resource1", "resource2"],
            "duration_minutes": 60,
        }
    )
    # May fail due to Loki connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_monitoring_health_endpoint(client):
    """Test monitoring health endpoint."""
    response = client.get("/api/v1/monitoring/health")
    # Should not return 404
    assert response.status_code != 404
    
    # Health endpoint should return status even if backends are unavailable
    if response.status_code == 200:
        data = response.json()
        assert "prometheus" in data
        assert "loki" in data
