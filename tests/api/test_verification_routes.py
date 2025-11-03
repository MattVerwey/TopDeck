"""
Tests for multi-source verification API routes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient


@pytest.fixture
def mock_verifier():
    """Mock multi-source verifier."""
    verifier = MagicMock()
    
    # Mock verification result
    from topdeck.analysis.accuracy.multi_source_verifier import (
        DependencyVerificationResult,
        VerificationEvidence,
    )
    
    mock_result = DependencyVerificationResult(
        source_id="test-source",
        target_id="test-target",
        is_verified=True,
        overall_confidence=0.85,
        verification_score=0.90,
        evidence=[
            VerificationEvidence(
                source="azure_infrastructure",
                evidence_type="network_topology",
                confidence=0.9,
                details={"evidence_items": ["Test evidence"]},
                verified_at=datetime.now(timezone.utc),
            )
        ],
        recommendations=["Test recommendation"],
        verified_at=datetime.now(timezone.utc),
    )
    
    verifier.verify_dependency = AsyncMock(return_value=mock_result)
    return verifier


def test_verify_dependency_endpoint(mock_verifier):
    """Test multi-source verification endpoint."""
    with patch(
        "topdeck.api.routes.accuracy.get_multi_source_verifier",
        return_value=mock_verifier,
    ):
        from topdeck.api.routes.accuracy import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test verification endpoint
        response = client.get(
            "/api/v1/accuracy/dependencies/verify",
            params={
                "source_id": "test-source",
                "target_id": "test-target",
                "duration_hours": 24,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["source_id"] == "test-source"
        assert data["target_id"] == "test-target"
        assert data["is_verified"] is True
        assert data["overall_confidence"] == 0.85
        assert data["verification_score"] == 0.90
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["source"] == "azure_infrastructure"
        assert data["evidence"][0]["confidence"] == 0.9
        assert len(data["recommendations"]) == 1


def test_verify_dependency_endpoint_missing_params():
    """Test verification endpoint with missing parameters."""
    with patch("topdeck.api.routes.accuracy.get_multi_source_verifier"):
        from topdeck.api.routes.accuracy import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test without source_id
        response = client.get(
            "/api/v1/accuracy/dependencies/verify",
            params={"target_id": "test-target"},
        )
        assert response.status_code == 422  # Validation error
        
        # Test without target_id
        response = client.get(
            "/api/v1/accuracy/dependencies/verify",
            params={"source_id": "test-source"},
        )
        assert response.status_code == 422  # Validation error


def test_verify_dependency_endpoint_with_duration():
    """Test verification endpoint with custom duration."""
    mock_verifier = MagicMock()
    
    from topdeck.analysis.accuracy.multi_source_verifier import (
        DependencyVerificationResult,
    )
    
    mock_result = DependencyVerificationResult(
        source_id="test-source",
        target_id="test-target",
        is_verified=False,
        overall_confidence=0.35,
        verification_score=0.40,
        evidence=[],
        recommendations=["Enable more verification sources"],
        verified_at=datetime.now(timezone.utc),
    )
    
    mock_verifier.verify_dependency = AsyncMock(return_value=mock_result)
    
    with patch(
        "topdeck.api.routes.accuracy.get_multi_source_verifier",
        return_value=mock_verifier,
    ):
        from topdeck.api.routes.accuracy import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test with 48-hour duration
        response = client.get(
            "/api/v1/accuracy/dependencies/verify",
            params={
                "source_id": "test-source",
                "target_id": "test-target",
                "duration_hours": 48,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_verified"] is False
        assert data["overall_confidence"] == 0.35
        assert "Enable more verification sources" in data["recommendations"]


def test_health_check():
    """Test accuracy service health check endpoint."""
    from topdeck.api.routes.accuracy import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    response = client.get("/api/v1/accuracy/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "accuracy_tracking"
