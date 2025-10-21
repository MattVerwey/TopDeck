"""
Tests for common middleware components.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from topdeck.common.middleware import RequestLoggingMiddleware, RequestIDMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    return app


def test_request_id_middleware(test_app):
    """Test that request ID is added to responses."""
    test_app.add_middleware(RequestIDMiddleware)
    client = TestClient(test_app)
    
    response = client.get("/test")
    
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_logging_middleware_success(test_app):
    """Test logging middleware for successful requests."""
    test_app.add_middleware(RequestLoggingMiddleware)
    client = TestClient(test_app)
    
    response = client.get("/test")
    
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


def test_logging_middleware_error(test_app):
    """Test logging middleware for error requests."""
    test_app.add_middleware(RequestLoggingMiddleware)
    client = TestClient(test_app)
    
    with pytest.raises(ValueError):
        client.get("/error")
