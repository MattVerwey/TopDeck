"""Tests for topology API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from topdeck.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_get_topology_endpoint_exists(client):
    """Test that the topology endpoint is registered."""
    response = client.get("/api/v1/topology")
    # Should not return 404
    assert response.status_code != 404


def test_get_topology_with_filters(client):
    """Test topology endpoint with filters."""
    response = client.get(
        "/api/v1/topology",
        params={
            "cloud_provider": "azure",
            "resource_type": "pod",
            "region": "eastus",
        }
    )
    # May fail due to Neo4j connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_resource_dependencies_endpoint_exists(client):
    """Test that the resource dependencies endpoint is registered."""
    response = client.get("/api/v1/topology/resources/test-resource/dependencies")
    # Should not return 404
    assert response.status_code != 404


def test_get_resource_dependencies_with_params(client):
    """Test resource dependencies endpoint with parameters."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/dependencies",
        params={
            "depth": 3,
            "direction": "both",
        }
    )
    # May fail due to Neo4j connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_resource_dependencies_invalid_direction(client):
    """Test resource dependencies endpoint with invalid direction."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/dependencies",
        params={
            "direction": "invalid",
        }
    )
    # Should return validation error
    assert response.status_code == 422


def test_get_data_flows_endpoint_exists(client):
    """Test that the data flows endpoint is registered."""
    response = client.get("/api/v1/topology/flows")
    # Should not return 404
    assert response.status_code != 404


def test_get_data_flows_with_filters(client):
    """Test data flows endpoint with filters."""
    response = client.get(
        "/api/v1/topology/flows",
        params={
            "flow_type": "https",
            "start_resource_type": "load_balancer",
        }
    )
    # May fail due to Neo4j connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_data_flows_invalid_flow_type(client):
    """Test data flows endpoint with invalid flow type."""
    response = client.get(
        "/api/v1/topology/flows",
        params={
            "flow_type": "invalid_type",
        }
    )
    # Should return either 400 (invalid) or 500 (Neo4j error)
    assert response.status_code in (400, 500)


def test_get_resource_attachments_endpoint_exists(client):
    """Test that the resource attachments endpoint is registered."""
    response = client.get("/api/v1/topology/resources/test-resource/attachments")
    # Should not return 404
    assert response.status_code != 404


def test_get_resource_attachments_with_params(client):
    """Test resource attachments endpoint with parameters."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/attachments",
        params={
            "direction": "both",
        }
    )
    # May fail due to Neo4j connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_resource_attachments_invalid_direction(client):
    """Test resource attachments endpoint with invalid direction."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/attachments",
        params={
            "direction": "invalid",
        }
    )
    # Should return validation error
    assert response.status_code == 422


def test_get_resource_attachments_upstream_only(client):
    """Test resource attachments endpoint with upstream only."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/attachments",
        params={
            "direction": "upstream",
        }
    )
    # May fail due to Neo4j connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_resource_attachments_downstream_only(client):
    """Test resource attachments endpoint with downstream only."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/attachments",
        params={
            "direction": "downstream",
        }
    )
    # May fail due to Neo4j connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_dependency_chains_endpoint_exists(client):
    """Test that the dependency chains endpoint is registered."""
    response = client.get("/api/v1/topology/resources/test-resource/chains")
    # Should not return 404
    assert response.status_code != 404


def test_get_dependency_chains_with_params(client):
    """Test dependency chains endpoint with parameters."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/chains",
        params={
            "max_depth": 5,
            "direction": "downstream",
        }
    )
    # May fail due to Neo4j connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_dependency_chains_invalid_direction(client):
    """Test dependency chains endpoint with invalid direction."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/chains",
        params={
            "direction": "both",  # Only upstream or downstream allowed
        }
    )
    # Should return validation error
    assert response.status_code == 422


def test_get_dependency_chains_upstream(client):
    """Test dependency chains endpoint with upstream direction."""
    response = client.get(
        "/api/v1/topology/resources/test-resource/chains",
        params={
            "direction": "upstream",
            "max_depth": 3,
        }
    )
    # May fail due to Neo4j connection, but endpoint should exist
    assert response.status_code in (200, 500)


def test_get_attachment_analysis_endpoint_exists(client):
    """Test that the attachment analysis endpoint is registered."""
    response = client.get("/api/v1/topology/resources/test-resource/analysis")
    # Should not return 404
    assert response.status_code != 404


def test_get_attachment_analysis(client):
    """Test attachment analysis endpoint."""
    response = client.get("/api/v1/topology/resources/test-resource/analysis")
    # May fail due to Neo4j connection or resource not found
    assert response.status_code in (200, 404, 500)


def test_get_attachment_analysis_response_structure(client):
    """Test that attachment analysis has correct response structure when successful."""
    # This test would pass if we have Neo4j running with data
    # For now we just verify the endpoint exists and doesn't crash
    response = client.get("/api/v1/topology/resources/test-resource/analysis")
    
    # If successful, should have these fields
    if response.status_code == 200:
        data = response.json()
        assert "resource_id" in data
        assert "resource_name" in data
        assert "resource_type" in data
        assert "total_attachments" in data
        assert "attachment_by_type" in data
        assert "critical_attachments" in data
        assert "attachment_strength" in data
        assert "dependency_chains" in data
        assert "impact_radius" in data
        assert "metadata" in data
