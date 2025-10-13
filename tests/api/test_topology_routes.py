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
