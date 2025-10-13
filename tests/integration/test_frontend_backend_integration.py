"""
Integration tests for frontend-backend API endpoint mapping.

These tests verify that all frontend API calls map to existing backend endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from topdeck.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test that the health endpoint exists and responds correctly."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_integrations_list_endpoint(client):
    """Test that the integrations list endpoint exists."""
    response = client.get("/api/v1/integrations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Verify structure
    assert "id" in data[0]
    assert "name" in data[0]
    assert "type" in data[0]
    assert "enabled" in data[0]


def test_integrations_update_endpoint(client):
    """Test that the integrations update endpoint exists."""
    response = client.put(
        "/api/v1/integrations/github",
        json={"enabled": True, "config": {}}
    )
    # Should not return 404
    assert response.status_code != 404


def test_topology_endpoint_exists(client):
    """Test that the topology endpoint is registered."""
    response = client.get("/api/v1/topology")
    # Should not return 404 (may return 500 without Neo4j)
    assert response.status_code != 404


def test_topology_dependencies_endpoint_exists(client):
    """Test that the resource dependencies endpoint is registered."""
    response = client.get("/api/v1/topology/resources/test-id/dependencies")
    # Should not return 404 (may return 500 without Neo4j)
    assert response.status_code != 404


def test_topology_flows_endpoint_exists(client):
    """Test that the data flows endpoint is registered."""
    response = client.get("/api/v1/topology/flows")
    # Should not return 404 (may return 500 without Neo4j)
    assert response.status_code != 404


def test_risk_assessment_endpoint_exists(client):
    """Test that the risk assessment endpoint is registered."""
    response = client.get("/api/v1/risk/resources/test-id")
    # Should not return 404 (may return 500 without Neo4j)
    assert response.status_code != 404


def test_risk_all_endpoint_exists(client):
    """Test that the all risks endpoint is registered."""
    response = client.get("/api/v1/risk/all")
    # Should not return 404 (may return 500 without Neo4j)
    assert response.status_code != 404


def test_risk_impact_endpoint_exists(client):
    """Test that the change impact endpoint is registered."""
    response = client.post(
        "/api/v1/risk/impact",
        json={"service_id": "test", "change_type": "deployment"}
    )
    # Should not return 404 (may return 500 without Neo4j)
    assert response.status_code != 404


def test_monitoring_metrics_endpoint(client):
    """Test that the monitoring metrics endpoint exists and works."""
    response = client.get(
        "/api/v1/monitoring/resources/test/metrics",
        params={"resource_type": "pod", "duration_hours": 1}
    )
    assert response.status_code == 200
    data = response.json()
    assert "resource_id" in data
    assert "metrics" in data


def test_monitoring_bottlenecks_endpoint_exists(client):
    """Test that the bottlenecks endpoint has correct path."""
    # Frontend calls /api/v1/monitoring/flows/bottlenecks with flow_path param
    response = client.get(
        "/api/v1/monitoring/flows/bottlenecks",
        params={"flow_path": ["resource1", "resource2"]}
    )
    # Should not return 404
    assert response.status_code != 404


def test_all_frontend_endpoints_registered(client):
    """
    Comprehensive test that all frontend API endpoints are registered.
    
    This test verifies the complete mapping between frontend API client
    and backend routes.
    """
    endpoints = [
        ("GET", "/health"),
        ("GET", "/api/v1/topology"),
        ("GET", "/api/v1/topology/resources/test/dependencies"),
        ("GET", "/api/v1/topology/flows"),
        ("GET", "/api/v1/risk/resources/test"),
        ("GET", "/api/v1/risk/all"),
        ("POST", "/api/v1/risk/impact"),
        ("GET", "/api/v1/monitoring/resources/test/metrics?resource_type=pod&duration_hours=1"),
        ("GET", "/api/v1/monitoring/flows/bottlenecks?flow_path=test"),
        ("GET", "/api/v1/integrations"),
        ("PUT", "/api/v1/integrations/github"),
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})
        elif method == "PUT":
            response = client.put(endpoint, json={})
        
        # None should return 404 (not found)
        assert response.status_code != 404, f"{method} {endpoint} returned 404 - endpoint not registered"
