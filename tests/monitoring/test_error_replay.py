"""
Tests for error replay service.
"""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from topdeck.monitoring.error_replay import (
    ErrorReplayService,
    ErrorSearchFilter,
    ErrorSeverity,
    ErrorSnapshot,
    ErrorSource,
)


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    client = MagicMock()
    session = AsyncMock()
    client.session.return_value.__aenter__.return_value = session
    return client


@pytest.fixture
def error_replay_service(mock_neo4j_client):
    """Create an error replay service with mocked dependencies."""
    return ErrorReplayService(
        neo4j_client=mock_neo4j_client,
        prometheus_url="http://prometheus:9090",
        loki_url="http://loki:3100",
    )


@pytest.mark.asyncio
async def test_capture_error_basic(error_replay_service, mock_neo4j_client):
    """Test capturing a basic error."""
    # Mock the store method
    session = mock_neo4j_client.session.return_value.__aenter__.return_value
    session.run = AsyncMock()

    # Mock all the collection methods to return empty data
    with patch.object(
        error_replay_service, "_collect_surrounding_logs", return_value=[]
    ), patch.object(error_replay_service, "_collect_metrics_at_time", return_value={}), patch.object(
        error_replay_service, "_collect_traces", return_value=[]
    ), patch.object(
        error_replay_service, "_capture_topology_snapshot", return_value={}
    ), patch.object(
        error_replay_service, "_find_related_errors", return_value=[]
    ), patch.object(
        error_replay_service, "_identify_affected_resources", return_value=[]
    ), patch.object(
        error_replay_service, "_get_deployment_context", return_value=None
    ):

        error = await error_replay_service.capture_error(
            message="Database connection timeout",
            severity=ErrorSeverity.HIGH,
            source=ErrorSource.APPLICATION,
            resource_id="db-001",
            resource_type="database",
            error_type="connection_timeout",
        )

        assert error.message == "Database connection timeout"
        assert error.severity == ErrorSeverity.HIGH
        assert error.source == ErrorSource.APPLICATION
        assert error.resource_id == "db-001"
        assert error.resource_type == "database"
        assert error.error_type == "connection_timeout"
        assert error.error_id is not None
        assert isinstance(error.timestamp, datetime)


@pytest.mark.asyncio
async def test_capture_error_with_context(error_replay_service, mock_neo4j_client):
    """Test capturing an error with full context."""
    session = mock_neo4j_client.session.return_value.__aenter__.return_value
    session.run = AsyncMock()

    # Mock collection methods to return sample data
    sample_logs = [
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Connection attempt failed",
            "level": "ERROR",
        }
    ]
    sample_metrics = {"cpu_usage": 85.5, "memory_usage": 72.3}
    sample_topology = {"resource": {"id": "db-001", "type": "database"}, "connections": []}

    with patch.object(
        error_replay_service, "_collect_surrounding_logs", return_value=sample_logs
    ), patch.object(
        error_replay_service, "_collect_metrics_at_time", return_value=sample_metrics
    ), patch.object(
        error_replay_service, "_collect_traces", return_value=[]
    ), patch.object(
        error_replay_service, "_capture_topology_snapshot", return_value=sample_topology
    ), patch.object(
        error_replay_service, "_find_related_errors", return_value=["error-123"]
    ), patch.object(
        error_replay_service, "_identify_affected_resources", return_value=["app-001"]
    ), patch.object(
        error_replay_service, "_get_deployment_context", return_value={"recent_deployments": []}
    ):

        error = await error_replay_service.capture_error(
            message="Database connection timeout",
            severity=ErrorSeverity.HIGH,
            source=ErrorSource.APPLICATION,
            resource_id="db-001",
            correlation_id="corr-123",
            trace_id="trace-456",
        )

        assert len(error.logs) == 1
        assert error.logs[0]["message"] == "Connection attempt failed"
        assert error.metrics == sample_metrics
        assert error.topology_snapshot == sample_topology
        assert error.related_errors == ["error-123"]
        assert error.affected_resources == ["app-001"]


@pytest.mark.asyncio
async def test_search_errors_by_severity(error_replay_service, mock_neo4j_client):
    """Test searching errors by severity."""
    session = mock_neo4j_client.session.return_value.__aenter__.return_value

    # Mock query result
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(
        return_value=[
            {
                "e": {
                    "error_id": "error-001",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "severity": "high",
                    "source": "application",
                    "message": "Test error",
                    "logs": "[]",
                    "metrics": "{}",
                    "traces": "[]",
                    "topology_snapshot": "{}",
                    "related_errors": [],
                    "affected_resources": [],
                    "tags": "{}",
                    "metadata": "{}",
                }
            }
        ]
    )
    session.run = AsyncMock(return_value=mock_result)

    filter = ErrorSearchFilter(severity=ErrorSeverity.HIGH, limit=10)
    errors = await error_replay_service.search_errors(filter)

    assert len(errors) == 1
    assert errors[0].error_id == "error-001"
    assert errors[0].severity == ErrorSeverity.HIGH


@pytest.mark.asyncio
async def test_search_errors_by_time_range(error_replay_service, mock_neo4j_client):
    """Test searching errors by time range."""
    session = mock_neo4j_client.session.return_value.__aenter__.return_value

    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[])
    session.run = AsyncMock(return_value=mock_result)

    start_time = datetime.now(UTC) - timedelta(hours=1)
    end_time = datetime.now(UTC)

    filter = ErrorSearchFilter(start_time=start_time, end_time=end_time, limit=50)
    errors = await error_replay_service.search_errors(filter)

    assert isinstance(errors, list)
    # Verify the query was called with time parameters
    session.run.assert_called_once()


@pytest.mark.asyncio
async def test_search_errors_by_resource(error_replay_service, mock_neo4j_client):
    """Test searching errors by resource ID."""
    session = mock_neo4j_client.session.return_value.__aenter__.return_value

    mock_result = AsyncMock()
    mock_result.data = AsyncMock(
        return_value=[
            {
                "e": {
                    "error_id": "error-002",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "severity": "medium",
                    "source": "prometheus",
                    "resource_id": "app-001",
                    "message": "High latency detected",
                    "logs": "[]",
                    "metrics": "{}",
                    "traces": "[]",
                    "topology_snapshot": "{}",
                    "related_errors": [],
                    "affected_resources": [],
                    "tags": "{}",
                    "metadata": "{}",
                }
            }
        ]
    )
    session.run = AsyncMock(return_value=mock_result)

    filter = ErrorSearchFilter(resource_id="app-001")
    errors = await error_replay_service.search_errors(filter)

    assert len(errors) == 1
    assert errors[0].resource_id == "app-001"


@pytest.mark.asyncio
async def test_replay_error(error_replay_service, mock_neo4j_client):
    """Test replaying an error."""
    session = mock_neo4j_client.session.return_value.__aenter__.return_value

    # Mock error retrieval
    mock_error_result = AsyncMock()
    mock_error_result.single = AsyncMock(
        return_value={
            "e": {
                "error_id": "error-001",
                "timestamp": datetime.now(UTC).isoformat(),
                "severity": "high",
                "source": "application",
                "message": "Test error",
                "logs": '[{"timestamp": "2024-01-01T00:00:00Z", "message": "Log entry"}]',
                "metrics": '{"cpu": 80}',
                "traces": "[]",
                "topology_snapshot": "{}",
                "related_errors": [],
                "affected_resources": ["app-002"],
                "deployment_context": '{"recent_deployments": []}',
                "tags": "{}",
                "metadata": "{}",
            }
        }
    )

    # Mock changes query
    mock_changes_result = AsyncMock()
    mock_changes_result.single = AsyncMock(return_value={"changes": []})

    session.run = AsyncMock(side_effect=[mock_error_result, mock_changes_result])

    result = await error_replay_service.replay_error("error-001")

    assert result.error_id == "error-001"
    assert result.error_snapshot.message == "Test error"
    assert isinstance(result.timeline, list)
    assert isinstance(result.root_cause_analysis, dict)
    assert isinstance(result.recommendations, list)


@pytest.mark.asyncio
async def test_replay_error_not_found(error_replay_service, mock_neo4j_client):
    """Test replaying a non-existent error."""
    session = mock_neo4j_client.session.return_value.__aenter__.return_value

    mock_result = AsyncMock()
    mock_result.single = AsyncMock(return_value=None)
    session.run = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="Error error-999 not found"):
        await error_replay_service.replay_error("error-999")


@pytest.mark.asyncio
async def test_get_error_statistics(error_replay_service, mock_neo4j_client):
    """Test getting error statistics."""
    session = mock_neo4j_client.session.return_value.__aenter__.return_value

    mock_result = AsyncMock()
    mock_result.single = AsyncMock(
        return_value={
            "total_errors": 42,
            "severities": ["high", "medium", "low"],
            "sources": ["application", "prometheus"],
            "resource_types": ["database", "api"],
            "error_types": ["timeout", "connection_error"],
        }
    )
    session.run = AsyncMock(return_value=mock_result)

    start_time = datetime.now(UTC) - timedelta(hours=24)
    end_time = datetime.now(UTC)

    stats = await error_replay_service.get_error_statistics(start_time, end_time)

    assert stats["total_errors"] == 42
    assert len(stats["severities"]) == 3
    assert "high" in stats["severities"]
    assert len(stats["sources"]) == 2


@pytest.mark.asyncio
async def test_generate_error_id(error_replay_service):
    """Test error ID generation."""
    timestamp = datetime.now(UTC)
    message = "Test error"
    resource_id = "resource-001"

    error_id_1 = error_replay_service._generate_error_id(timestamp, message, resource_id)
    error_id_2 = error_replay_service._generate_error_id(timestamp, message, resource_id)

    # Same inputs should generate same ID
    assert error_id_1 == error_id_2
    assert len(error_id_1) == 16  # SHA256 truncated to 16 chars


@pytest.mark.asyncio
async def test_build_error_timeline(error_replay_service):
    """Test building error timeline."""
    timestamp = datetime.now(UTC)
    error_snapshot = ErrorSnapshot(
        error_id="error-001",
        timestamp=timestamp,
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_id="app-001",
        resource_type="application",
        message="Test error",
        logs=[
            {
                "timestamp": (timestamp - timedelta(minutes=5)).isoformat(),
                "message": "Warning sign",
                "level": "WARN",
            },
            {
                "timestamp": (timestamp - timedelta(minutes=1)).isoformat(),
                "message": "Error occurred",
                "level": "ERROR",
            },
        ],
        deployment_context={
            "recent_deployments": [{"timestamp": (timestamp - timedelta(hours=2)).isoformat()}]
        },
    )

    timeline = await error_replay_service._build_error_timeline(error_snapshot)

    assert len(timeline) > 0
    # Timeline should include error, logs, and deployments
    assert any(item["type"] == "error" for item in timeline)
    assert any(item["type"] == "log" for item in timeline)
    assert any(item["type"] == "deployment" for item in timeline)
    # Should be sorted by timestamp
    timestamps = [item["timestamp"] for item in timeline]
    assert timestamps == sorted(timestamps)


@pytest.mark.asyncio
async def test_analyze_root_cause_with_deployment(error_replay_service):
    """Test root cause analysis with recent deployment."""
    timestamp = datetime.now(UTC)
    error_snapshot = ErrorSnapshot(
        error_id="error-001",
        timestamp=timestamp,
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_id="app-001",
        resource_type="application",
        message="Application crash",
        deployment_context={
            "recent_deployments": [
                {"timestamp": (timestamp - timedelta(hours=1)).isoformat(), "version": "v1.2.0"}
            ]
        },
    )

    timeline = []
    root_cause = await error_replay_service._analyze_root_cause(error_snapshot, timeline)

    assert root_cause["primary_cause"] == "Recent deployment"
    assert "Deployment occurred" in str(root_cause["contributing_factors"])
    assert root_cause["confidence"] == 0.7


@pytest.mark.asyncio
async def test_generate_recommendations(error_replay_service):
    """Test generating recommendations."""
    error_snapshot = ErrorSnapshot(
        error_id="error-001",
        timestamp=datetime.now(UTC),
        severity=ErrorSeverity.CRITICAL,
        source=ErrorSource.APPLICATION,
        resource_id="app-001",
        resource_type="application",
        message="Critical failure",
        affected_resources=["app-002", "app-003", "app-004"],
    )

    root_cause = {
        "primary_cause": "Recent deployment",
        "contributing_factors": [],
        "confidence": 0.7,
    }

    recommendations = await error_replay_service._generate_recommendations(
        error_snapshot, root_cause
    )

    assert len(recommendations) > 0
    assert any("rolling back" in rec.lower() for rec in recommendations)
    assert any("escalate" in rec.lower() for rec in recommendations)


@pytest.mark.asyncio
async def test_search_errors_multiple_filters(error_replay_service, mock_neo4j_client):
    """Test searching with multiple filters."""
    session = mock_neo4j_client.session.return_value.__aenter__.return_value

    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[])
    session.run = AsyncMock(return_value=mock_result)

    filter = ErrorSearchFilter(
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_type="database",
        error_type="connection_timeout",
        limit=25,
    )

    await error_replay_service.search_errors(filter)

    # Verify query was built with all filters
    call_args = session.run.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    assert "WHERE" in query
    assert params["severity"] == "high"
    assert params["source"] == "application"
    assert params["resource_type"] == "database"
    assert params["error_type"] == "connection_timeout"
    assert params["limit"] == 25
