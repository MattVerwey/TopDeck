"""Unit tests for API endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "TopDeck API"


def test_health_endpoint(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_info_endpoint(client: TestClient) -> None:
    """Test the info endpoint."""
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "environment" in data
    assert "features" in data
    assert isinstance(data["features"], dict)
