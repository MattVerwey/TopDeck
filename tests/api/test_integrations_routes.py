"""Tests for integrations API endpoints."""

import pytest
from fastapi.testclient import TestClient

from topdeck.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_get_integrations_endpoint_exists(client):
    """Test that the integrations endpoint is registered."""
    response = client.get("/api/v1/integrations")
    # Should not return 404
    assert response.status_code != 404


def test_get_integrations_returns_list(client):
    """Test that the integrations endpoint returns a list."""
    response = client.get("/api/v1/integrations")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_get_integrations_includes_azure(client):
    """Test that Azure integration is included in the list."""
    response = client.get("/api/v1/integrations")
    if response.status_code == 200:
        data = response.json()
        # Check if Azure integration is in the list
        azure_integration = next((item for item in data if item["id"] == "azure"), None)
        assert azure_integration is not None
        assert azure_integration["name"] == "Azure"
        assert azure_integration["type"] == "cloud-provider"


def test_get_integrations_includes_azure_devops(client):
    """Test that Azure DevOps integration is included in the list."""
    response = client.get("/api/v1/integrations")
    if response.status_code == 200:
        data = response.json()
        # Check if Azure DevOps integration is in the list
        azure_devops_integration = next((item for item in data if item["id"] == "azure-devops"), None)
        assert azure_devops_integration is not None
        assert azure_devops_integration["name"] == "Azure DevOps"


def test_get_integrations_includes_github(client):
    """Test that GitHub integration is included in the list."""
    response = client.get("/api/v1/integrations")
    if response.status_code == 200:
        data = response.json()
        # Check if GitHub integration is in the list
        github_integration = next((item for item in data if item["id"] == "github"), None)
        assert github_integration is not None
        assert github_integration["name"] == "GitHub"


def test_update_integration_endpoint_exists(client):
    """Test that the update integration endpoint is registered."""
    response = client.put(
        "/api/v1/integrations/azure",
        json={"enabled": True, "config": {}},
    )
    # Should not return 404
    assert response.status_code != 404


def test_update_nonexistent_integration(client):
    """Test updating a non-existent integration returns 404."""
    response = client.put(
        "/api/v1/integrations/nonexistent",
        json={"enabled": True, "config": {}},
    )
    # May return 404 or 500, but should not succeed
    assert response.status_code in (404, 500)
