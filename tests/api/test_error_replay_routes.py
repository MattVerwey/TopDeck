"""
Tests for error replay API routes.
"""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from topdeck.api.main import app
from topdeck.monitoring.error_replay import (
    ErrorReplayResult,
    ErrorSeverity,
    ErrorSnapshot,
    ErrorSource,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_error_replay_service():
    """Create a mock error replay service."""
    return AsyncMock()


@pytest.fixture
def sample_error_snapshot():
    """Create a sample error snapshot."""
    return ErrorSnapshot(
        error_id="test-error-001",
        timestamp=datetime.now(UTC),
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_id="app-001",
        resource_type="application",
        message="Test error message",
        error_type="connection_timeout",
        logs=[{"timestamp": datetime.now(UTC).isoformat(), "message": "Test log"}],
        metrics={"cpu": 80.5},
        traces=[],
        topology_snapshot={},
        related_errors=["error-002"],
        affected_resources=["app-002"],
        tags={"env": "prod"},
        metadata={"user": "test"},
    )


def test_capture_error_success(client, mock_error_replay_service, sample_error_snapshot):
    """Test successful error capture."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.capture_error = AsyncMock(return_value=sample_error_snapshot)

        response = client.post(
            "/error-replay/capture",
            json={
                "message": "Test error",
                "severity": "high",
                "source": "application",
                "resource_id": "app-001",
                "resource_type": "application",
                "error_type": "connection_timeout",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["error_id"] == "test-error-001"
        assert data["message"] == "Test error message"
        assert data["severity"] == "high"
        assert data["source"] == "application"


def test_capture_error_with_trace_info(client, mock_error_replay_service, sample_error_snapshot):
    """Test capturing error with trace information."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.capture_error = AsyncMock(return_value=sample_error_snapshot)

        response = client.post(
            "/error-replay/capture",
            json={
                "message": "Test error",
                "severity": "high",
                "source": "application",
                "correlation_id": "corr-123",
                "trace_id": "trace-456",
                "span_id": "span-789",
                "tags": {"environment": "production"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["error_id"] is not None


def test_capture_error_validation_error(client):
    """Test error capture with invalid data."""
    response = client.post(
        "/error-replay/capture",
        json={
            "message": "Test error",
            # Missing required 'severity' and 'source'
        },
    )

    assert response.status_code == 422  # Validation error


def test_replay_error_success(client, mock_error_replay_service, sample_error_snapshot):
    """Test successful error replay."""
    replay_result = ErrorReplayResult(
        error_id="test-error-001",
        original_timestamp=sample_error_snapshot.timestamp,
        error_snapshot=sample_error_snapshot,
        timeline=[
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "type": "error",
                "message": "Error occurred",
            }
        ],
        root_cause_analysis={
            "primary_cause": "Recent deployment",
            "contributing_factors": ["High load"],
            "confidence": 0.8,
        },
        recommendations=["Rollback deployment", "Check logs"],
        related_changes=[{"type": "deployment", "timestamp": datetime.now(UTC).isoformat()}],
    )

    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.replay_error = AsyncMock(return_value=replay_result)

        response = client.get("/error-replay/replay/test-error-001")

        assert response.status_code == 200
        data = response.json()
        assert data["error_id"] == "test-error-001"
        assert "timeline" in data
        assert "root_cause_analysis" in data
        assert "recommendations" in data
        assert len(data["recommendations"]) == 2


def test_replay_error_not_found(client, mock_error_replay_service):
    """Test replaying non-existent error."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.replay_error = AsyncMock(
            side_effect=ValueError("Error not-found not found")
        )

        response = client.get("/error-replay/replay/not-found")

        assert response.status_code == 404


def test_search_errors_basic(client, mock_error_replay_service, sample_error_snapshot):
    """Test basic error search."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.search_errors = AsyncMock(return_value=[sample_error_snapshot])

        response = client.post(
            "/error-replay/search",
            json={"severity": "high", "limit": 50},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["error_id"] == "test-error-001"


def test_search_errors_with_time_range(client, mock_error_replay_service):
    """Test searching errors with time range."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.search_errors = AsyncMock(return_value=[])

        start_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        end_time = datetime.now(UTC).isoformat()

        response = client.post(
            "/error-replay/search",
            json={"start_time": start_time, "end_time": end_time, "limit": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


def test_search_errors_with_filters(client, mock_error_replay_service):
    """Test searching with multiple filters."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.search_errors = AsyncMock(return_value=[])

        response = client.post(
            "/error-replay/search",
            json={
                "severity": "critical",
                "source": "prometheus",
                "resource_type": "database",
                "error_type": "connection_timeout",
                "limit": 25,
            },
        )

        assert response.status_code == 200


def test_get_error_statistics(client, mock_error_replay_service):
    """Test getting error statistics."""
    stats = {
        "total_errors": 150,
        "severities": ["critical", "high", "medium"],
        "sources": ["application", "prometheus", "loki"],
        "resource_types": ["database", "api", "cache"],
        "error_types": ["timeout", "connection_error"],
        "time_range": {
            "start": (datetime.now(UTC) - timedelta(hours=24)).isoformat(),
            "end": datetime.now(UTC).isoformat(),
        },
    }

    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.get_error_statistics = AsyncMock(return_value=stats)

        start_time = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        end_time = datetime.now(UTC).isoformat()

        response = client.get(
            f"/error-replay/statistics?start_time={start_time}&end_time={end_time}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_errors"] == 150
        assert len(data["severities"]) == 3
        assert "critical" in data["severities"]


def test_get_recent_errors(client, mock_error_replay_service, sample_error_snapshot):
    """Test getting recent errors."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.search_errors = AsyncMock(return_value=[sample_error_snapshot])

        response = client.get("/error-replay/recent?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["error_id"] == "test-error-001"


def test_get_recent_errors_filtered_by_severity(client, mock_error_replay_service):
    """Test getting recent errors filtered by severity."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.search_errors = AsyncMock(return_value=[])

        response = client.get("/error-replay/recent?severity=critical&limit=20")

        assert response.status_code == 200


def test_get_errors_by_resource(client, mock_error_replay_service, sample_error_snapshot):
    """Test getting errors for a specific resource."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.search_errors = AsyncMock(return_value=[sample_error_snapshot])

        response = client.get("/error-replay/by-resource/app-001?limit=50")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["resource_id"] == "app-001"


def test_get_errors_by_correlation(client, mock_error_replay_service, sample_error_snapshot):
    """Test getting errors by correlation ID."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.search_errors = AsyncMock(return_value=[sample_error_snapshot])

        response = client.get("/error-replay/by-correlation/corr-123?limit=50")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


def test_search_errors_limit_validation(client, mock_error_replay_service):
    """Test that search enforces limit validation."""
    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        # Test exceeding max limit
        response = client.post(
            "/error-replay/search",
            json={"limit": 5000},  # Exceeds max of 1000
        )

        assert response.status_code == 422  # Validation error


def test_capture_error_with_stack_trace(client, mock_error_replay_service, sample_error_snapshot):
    """Test capturing error with stack trace."""
    sample_error_snapshot.stack_trace = "Traceback (most recent call last):\n  File ..."

    with patch(
        "topdeck.api.routes.error_replay.get_error_replay_service",
        return_value=mock_error_replay_service,
    ):
        mock_error_replay_service.capture_error = AsyncMock(return_value=sample_error_snapshot)

        response = client.post(
            "/error-replay/capture",
            json={
                "message": "Test error",
                "severity": "high",
                "source": "application",
                "stack_trace": "Traceback (most recent call last):\n  File ...",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["stack_trace"] is not None


def test_error_replay_service_initialization(client):
    """Test that error replay service can be initialized."""
    with patch("topdeck.api.routes.error_replay.Neo4jClient"), patch(
        "topdeck.api.routes.error_replay.settings"
    ) as mock_settings:
        mock_settings.NEO4J_URI = "bolt://localhost:7687"
        mock_settings.NEO4J_USERNAME = "neo4j"
        mock_settings.NEO4J_PASSWORD = "password"
        mock_settings.PROMETHEUS_URL = None
        mock_settings.LOKI_URL = None
        mock_settings.TEMPO_URL = None
        mock_settings.ELASTICSEARCH_URL = None
        mock_settings.AZURE_LOG_ANALYTICS_WORKSPACE_ID = None

        from topdeck.api.routes.error_replay import get_error_replay_service

        service = get_error_replay_service()
        assert service is not None
