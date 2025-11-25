"""
Tests for the Error Context Aggregator.

Tests the functionality that addresses Market Gap #2:
Error Context Aggregation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from topdeck.troubleshooting.error_context import (
    ContextSnapshot,
    ContextType,
    DeploymentSnapshot,
    DependencySnapshot,
    ErrorContext,
    ErrorContextAggregator,
    LogSnapshot,
    MetricSnapshot,
    TopologySnapshot,
)


class TestMetricSnapshot:
    """Tests for MetricSnapshot dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        snapshot = MetricSnapshot(
            name="cpu_usage",
            value=75.5,
            timestamp=now,
            labels={"pod": "api-pod-1"},
            unit="percent",
        )

        result = snapshot.to_dict()

        assert result["name"] == "cpu_usage"
        assert result["value"] == 75.5
        assert result["labels"]["pod"] == "api-pod-1"


class TestLogSnapshot:
    """Tests for LogSnapshot dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        snapshot = LogSnapshot(
            entries=[
                {"timestamp": now.isoformat(), "message": "Log 1", "level": "error"},
                {"timestamp": now.isoformat(), "message": "Log 2", "level": "warning"},
            ],
            error_count=1,
            warning_count=1,
            time_range_start=now - timedelta(minutes=5),
            time_range_end=now,
        )

        result = snapshot.to_dict()

        assert len(result["entries"]) == 2
        assert result["error_count"] == 1
        assert result["warning_count"] == 1


class TestDeploymentSnapshot:
    """Tests for DeploymentSnapshot dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        snapshot = DeploymentSnapshot(
            deployment_id="dep-123",
            service_id="api-service",
            version="v1.2.3",
            deployed_at=now - timedelta(hours=1),
            deployed_by="ci-pipeline",
            commit_sha="abc123def",
            is_recent=True,
        )

        result = snapshot.to_dict()

        assert result["deployment_id"] == "dep-123"
        assert result["version"] == "v1.2.3"
        assert result["is_recent"] is True


class TestDependencySnapshot:
    """Tests for DependencySnapshot dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        snapshot = DependencySnapshot(
            dependency_id="db-prod",
            dependency_name="Production Database",
            dependency_type="database",
            status="healthy",
            latency_ms=25.5,
            error_rate=0.01,
            last_check=now,
        )

        result = snapshot.to_dict()

        assert result["dependency_id"] == "db-prod"
        assert result["status"] == "healthy"
        assert result["latency_ms"] == 25.5


class TestTopologySnapshot:
    """Tests for TopologySnapshot dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        snapshot = TopologySnapshot(
            resource_id="api-service",
            resource_type="kubernetes_deployment",
            upstream_dependencies=["db-prod", "cache-prod"],
            downstream_dependencies=["web-app", "mobile-api"],
            blast_radius_count=15,
        )

        result = snapshot.to_dict()

        assert result["resource_id"] == "api-service"
        assert len(result["upstream_dependencies"]) == 2
        assert result["blast_radius_count"] == 15


class TestContextSnapshot:
    """Tests for ContextSnapshot dataclass."""

    def test_to_dict_with_dataclass(self):
        """Test conversion to dictionary with dataclass data."""
        now = datetime.now(UTC)
        metric = MetricSnapshot(
            name="cpu_usage",
            value=75.5,
            timestamp=now,
        )
        snapshot = ContextSnapshot(
            context_type=ContextType.METRICS,
            captured_at=now,
            data=metric,
        )

        result = snapshot.to_dict()

        assert result["context_type"] == "metrics"
        assert result["data"]["name"] == "cpu_usage"

    def test_to_dict_with_dict(self):
        """Test conversion to dictionary with dict data."""
        now = datetime.now(UTC)
        snapshot = ContextSnapshot(
            context_type=ContextType.CONFIGURATION,
            captured_at=now,
            data={"key": "value"},
        )

        result = snapshot.to_dict()

        assert result["context_type"] == "configuration"
        assert result["data"]["key"] == "value"


class TestErrorContext:
    """Tests for ErrorContext dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        context = ErrorContext(
            context_id="ctx-123",
            error_time=now,
            resource_id="api-service",
            resource_name="API Service",
            error_message="Connection timeout",
            error_type="timeout",
            severity="error",
            snapshots={
                ContextType.TOPOLOGY: ContextSnapshot(
                    context_type=ContextType.TOPOLOGY,
                    captured_at=now,
                    data=TopologySnapshot(
                        resource_id="api-service",
                        resource_type="kubernetes_deployment",
                        upstream_dependencies=["db-prod"],
                        downstream_dependencies=["web-app"],
                        blast_radius_count=5,
                    ),
                )
            },
            recommendations=["Check database connectivity"],
            created_at=now,
            expires_at=now + timedelta(hours=72),
        )

        result = context.to_dict()

        assert result["context_id"] == "ctx-123"
        assert result["error_type"] == "timeout"
        assert "topology" in result["snapshots"]


class TestErrorContextAggregator:
    """Tests for ErrorContextAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator with no dependencies."""
        return ErrorContextAggregator()

    def test_generate_recommendations_with_deployment(self, aggregator):
        """Test recommendations when recent deployment detected."""
        now = datetime.now(UTC)
        snapshots = {
            ContextType.DEPLOYMENTS: ContextSnapshot(
                context_type=ContextType.DEPLOYMENTS,
                captured_at=now,
                data=[
                    DeploymentSnapshot(
                        deployment_id="dep-1",
                        service_id="api",
                        version="v1.2.3",
                        deployed_at=now - timedelta(minutes=30),
                        deployed_by="ci",
                        is_recent=True,
                    )
                ],
            )
        }

        result = aggregator._generate_recommendations("timeout", "error", snapshots)

        assert any("deployment" in r.lower() for r in result)

    def test_generate_recommendations_with_unhealthy_deps(self, aggregator):
        """Test recommendations when dependencies are unhealthy."""
        now = datetime.now(UTC)
        snapshots = {
            ContextType.DEPENDENCIES: ContextSnapshot(
                context_type=ContextType.DEPENDENCIES,
                captured_at=now,
                data=[
                    DependencySnapshot(
                        dependency_id="db-prod",
                        dependency_name="Production DB",
                        dependency_type="database",
                        status="unhealthy",
                        latency_ms=1000,
                        error_rate=0.5,
                        last_check=now,
                    )
                ],
            )
        }

        result = aggregator._generate_recommendations("timeout", "error", snapshots)

        assert any("dependency" in r.lower() for r in result)

    def test_generate_recommendations_by_error_type(self, aggregator):
        """Test error-type specific recommendations."""
        # Timeout error
        result = aggregator._generate_recommendations("timeout", "error", {})
        assert any("latency" in r.lower() or "timeout" in r.lower() for r in result)

        # Connection error
        result = aggregator._generate_recommendations("connection_error", "error", {})
        assert any("connectivity" in r.lower() or "network" in r.lower() for r in result)

        # Memory error
        result = aggregator._generate_recommendations("memory_error", "error", {})
        assert any("memory" in r.lower() for r in result)

    def test_generate_recommendations_default(self, aggregator):
        """Test default recommendations when no specific context."""
        result = aggregator._generate_recommendations("unknown", "error", {})

        assert len(result) > 0
        assert any("deployment" in r.lower() or "change" in r.lower() for r in result)

    @pytest.mark.asyncio
    async def test_capture_context_basic(self, aggregator):
        """Test basic context capture without external services."""
        result = await aggregator.capture_context(
            resource_id="test-service",
            error_message="Test error",
            error_type="test",
            severity="error",
        )

        assert result.resource_id == "test-service"
        assert result.error_message == "Test error"
        assert result.context_id is not None
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_capture_context_with_time(self, aggregator):
        """Test context capture with specific error time."""
        error_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        result = await aggregator.capture_context(
            resource_id="test-service",
            error_time=error_time,
            error_message="Test error",
        )

        assert result.error_time == error_time

    @pytest.mark.asyncio
    async def test_get_context(self, aggregator):
        """Test retrieving captured context."""
        # First capture a context
        captured = await aggregator.capture_context(
            resource_id="test-service",
            error_message="Test error",
        )

        # Then retrieve it
        result = await aggregator.get_context(captured.context_id)

        assert result is not None
        assert result.context_id == captured.context_id

    @pytest.mark.asyncio
    async def test_get_context_not_found(self, aggregator):
        """Test retrieving non-existent context."""
        result = await aggregator.get_context("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_contexts_by_resource(self, aggregator):
        """Test retrieving contexts by resource."""
        # Capture multiple contexts
        await aggregator.capture_context(resource_id="test-service", error_message="Error 1")
        await aggregator.capture_context(resource_id="test-service", error_message="Error 2")
        await aggregator.capture_context(resource_id="other-service", error_message="Error 3")

        # Get contexts for test-service
        result = await aggregator.get_contexts_by_resource("test-service")

        assert len(result) == 2
        assert all(ctx.resource_id == "test-service" for ctx in result)

    @pytest.mark.asyncio
    async def test_enrich_context(self, aggregator):
        """Test enriching existing context."""
        # First capture a context
        captured = await aggregator.capture_context(
            resource_id="test-service",
            error_message="Test error",
        )

        # Enrich with additional data
        result = await aggregator.enrich_context(
            captured.context_id,
            {"additional_key": "additional_value"},
        )

        assert result is not None
        assert ContextType.CONFIGURATION in result.snapshots

    @pytest.mark.asyncio
    async def test_capture_with_prometheus(self):
        """Test context capture with Prometheus collector."""
        mock_prometheus = AsyncMock()
        mock_prometheus.query.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "value": [1705312200, "75.5"],
                        "metric": {"pod": "api-pod-1"},
                    }
                ]
            },
        }

        aggregator = ErrorContextAggregator(prometheus_collector=mock_prometheus)

        result = await aggregator.capture_context(
            resource_id="test-service",
            error_message="Test error",
        )

        assert result.context_id is not None
        # Prometheus was called
        assert mock_prometheus.query.called

    @pytest.mark.asyncio
    async def test_capture_with_neo4j(self):
        """Test context capture with Neo4j client."""
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query.return_value = [{"name": "Test Service"}]

        aggregator = ErrorContextAggregator(neo4j_client=mock_neo4j)

        result = await aggregator.capture_context(
            resource_id="test-service",
            error_message="Test error",
        )

        assert result.resource_name == "Test Service"
