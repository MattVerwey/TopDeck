"""
Tests for the Dependency Health Monitor.

Tests the functionality that addresses Market Gap #5:
Service Dependency Health Dashboard.
"""

from datetime import UTC, datetime, timedelta

import pytest

from topdeck.troubleshooting.dependency_health import (
    ConnectionPoolStatus,
    DependencyHealthMonitor,
    DependencyHealthReport,
    DependencyMetrics,
    DependencyStatus,
    DependencyTimeline,
    DependencyType,
    HealthStatus,
    HistoricalDataPoint,
)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_values(self):
        """Test health status values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestDependencyType:
    """Tests for DependencyType enum."""

    def test_values(self):
        """Test dependency type values."""
        assert DependencyType.DATABASE.value == "database"
        assert DependencyType.CACHE.value == "cache"
        assert DependencyType.API.value == "api"
        assert DependencyType.MESSAGE_QUEUE.value == "message_queue"


class TestConnectionPoolStatus:
    """Tests for ConnectionPoolStatus dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        status = ConnectionPoolStatus(
            pool_name="db-pool",
            total_connections=20,
            active_connections=15,
            idle_connections=5,
            waiting_requests=0,
            max_connections=50,
            utilization_percent=40.0,
            status=HealthStatus.HEALTHY,
            last_updated=now,
        )

        result = status.to_dict()

        assert result["pool_name"] == "db-pool"
        assert result["active_connections"] == 15
        assert result["utilization_percent"] == 40.0
        assert result["status"] == "healthy"


class TestDependencyMetrics:
    """Tests for DependencyMetrics dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = DependencyMetrics(
            latency_p50_ms=50.0,
            latency_p95_ms=150.0,
            latency_p99_ms=300.0,
            request_rate_per_sec=100.0,
            error_rate_percent=0.5,
            success_rate_percent=99.5,
        )

        result = metrics.to_dict()

        assert result["latency_p50_ms"] == 50.0
        assert result["error_rate_percent"] == 0.5

    def test_to_dict_with_none_values(self):
        """Test conversion with None values."""
        metrics = DependencyMetrics()

        result = metrics.to_dict()

        assert result["latency_p50_ms"] is None
        assert result["error_rate_percent"] is None


class TestDependencyStatus:
    """Tests for DependencyStatus dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        status = DependencyStatus(
            dependency_id="db-prod",
            dependency_name="Production Database",
            dependency_type=DependencyType.DATABASE,
            status=HealthStatus.HEALTHY,
            health_score=95.0,
            metrics=DependencyMetrics(latency_p95_ms=50.0),
            connection_pool=None,
            circuit_breaker_status="closed",
            last_success=now,
            last_failure=None,
            failure_count_1h=0,
            anomalies=[],
            last_updated=now,
        )

        result = status.to_dict()

        assert result["dependency_id"] == "db-prod"
        assert result["dependency_type"] == "database"
        assert result["health_score"] == 95.0
        assert result["circuit_breaker_status"] == "closed"


class TestDependencyHealthReport:
    """Tests for DependencyHealthReport dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        report = DependencyHealthReport(
            resource_id="api-service",
            resource_name="API Service",
            overall_health=HealthStatus.HEALTHY,
            overall_health_score=92.0,
            dependencies=[],
            critical_issues=[],
            recommendations=["All dependencies healthy"],
            generated_at=now,
        )

        result = report.to_dict()

        assert result["resource_id"] == "api-service"
        assert result["overall_health"] == "healthy"
        assert result["overall_health_score"] == 92.0


class TestHistoricalDataPoint:
    """Tests for HistoricalDataPoint dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        point = HistoricalDataPoint(
            timestamp=now,
            health_score=85.0,
            latency_p95_ms=100.0,
            error_rate_percent=0.5,
        )

        result = point.to_dict()

        assert result["health_score"] == 85.0
        assert result["latency_p95_ms"] == 100.0


class TestDependencyTimeline:
    """Tests for DependencyTimeline dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        timeline = DependencyTimeline(
            dependency_id="db-prod",
            dependency_name="Production DB",
            time_range_start=now - timedelta(hours=24),
            time_range_end=now,
            data_points=[],
            average_health_score=90.0,
            degraded_periods=[],
        )

        result = timeline.to_dict()

        assert result["dependency_id"] == "db-prod"
        assert result["average_health_score"] == 90.0


class TestDependencyHealthMonitor:
    """Tests for DependencyHealthMonitor."""

    @pytest.fixture
    def monitor(self):
        """Create monitor with no dependencies."""
        return DependencyHealthMonitor()

    def test_categorize_dependency_type(self, monitor):
        """Test categorization of resource types to dependency types."""
        test_cases = [
            ("azure_sql_database", DependencyType.DATABASE),
            ("sql_server", DependencyType.DATABASE),
            ("cosmos_db", DependencyType.DATABASE),
            ("postgresql", DependencyType.DATABASE),
            ("redis_cache", DependencyType.CACHE),
            ("elasticache", DependencyType.CACHE),
            ("memcached", DependencyType.CACHE),
            ("rabbitmq", DependencyType.MESSAGE_QUEUE),
            ("servicebus_queue", DependencyType.MESSAGE_QUEUE),
            ("sqs", DependencyType.MESSAGE_QUEUE),
            ("kafka", DependencyType.MESSAGE_QUEUE),
            ("blob_storage", DependencyType.STORAGE),
            ("s3_bucket", DependencyType.STORAGE),
            ("external_api", DependencyType.EXTERNAL),
            ("unknown_service", DependencyType.API),  # Default
        ]

        for resource_type, expected in test_cases:
            result = monitor._categorize_dependency_type(resource_type)
            assert result == expected, f"Failed for type: {resource_type}"

    def test_calculate_health_score_perfect(self, monitor):
        """Test health score calculation with perfect metrics."""
        metrics = DependencyMetrics(
            latency_p95_ms=50.0,  # Below warning threshold
            error_rate_percent=0.1,  # Below warning threshold
        )

        score = monitor._calculate_health_score(metrics, None)

        assert score == 100.0

    def test_calculate_health_score_with_high_latency(self, monitor):
        """Test health score with high latency."""
        metrics = DependencyMetrics(
            latency_p95_ms=600.0,  # Above critical threshold
            error_rate_percent=0.1,
        )

        score = monitor._calculate_health_score(metrics, None)

        assert score < 100.0
        assert score > 50.0  # Still not terrible

    def test_calculate_health_score_with_high_errors(self, monitor):
        """Test health score with high error rate."""
        metrics = DependencyMetrics(
            latency_p95_ms=50.0,
            error_rate_percent=10.0,  # Above critical threshold
        )

        score = monitor._calculate_health_score(metrics, None)

        assert score < 70.0  # Significant penalty

    def test_calculate_health_score_with_pool_issues(self, monitor):
        """Test health score with connection pool issues."""
        now = datetime.now(UTC)
        metrics = DependencyMetrics(latency_p95_ms=50.0)
        pool = ConnectionPoolStatus(
            pool_name="db-pool",
            total_connections=45,
            active_connections=45,
            idle_connections=0,
            waiting_requests=5,  # Requests waiting!
            max_connections=50,
            utilization_percent=90.0,  # Critical threshold
            status=HealthStatus.UNHEALTHY,
            last_updated=now,
        )

        score = monitor._calculate_health_score(metrics, pool)

        assert score < 80.0  # Pool issues reduce score

    def test_score_to_status(self, monitor):
        """Test conversion of score to status."""
        assert monitor._score_to_status(95) == HealthStatus.HEALTHY
        assert monitor._score_to_status(80) == HealthStatus.HEALTHY
        assert monitor._score_to_status(65) == HealthStatus.DEGRADED
        assert monitor._score_to_status(50) == HealthStatus.DEGRADED
        assert monitor._score_to_status(40) == HealthStatus.UNHEALTHY
        assert monitor._score_to_status(0) == HealthStatus.UNHEALTHY

    def test_calculate_overall_health_all_healthy(self, monitor):
        """Test overall health calculation with all healthy deps."""
        now = datetime.now(UTC)
        deps = [
            DependencyStatus(
                dependency_id=f"dep-{i}",
                dependency_name=f"Dependency {i}",
                dependency_type=DependencyType.API,
                status=HealthStatus.HEALTHY,
                health_score=90.0,
                metrics=DependencyMetrics(),
                connection_pool=None,
                circuit_breaker_status=None,
                last_success=now,
                last_failure=None,
                failure_count_1h=0,
                anomalies=[],
                last_updated=now,
            )
            for i in range(3)
        ]

        score = monitor._calculate_overall_health(deps)

        assert score == 90.0  # Average of all

    def test_calculate_overall_health_mixed(self, monitor):
        """Test overall health with mixed health states."""
        now = datetime.now(UTC)
        deps = [
            DependencyStatus(
                dependency_id="dep-1",
                dependency_name="Healthy Dep",
                dependency_type=DependencyType.API,
                status=HealthStatus.HEALTHY,
                health_score=90.0,
                metrics=DependencyMetrics(),
                connection_pool=None,
                circuit_breaker_status=None,
                last_success=now,
                last_failure=None,
                failure_count_1h=0,
                anomalies=[],
                last_updated=now,
            ),
            DependencyStatus(
                dependency_id="dep-2",
                dependency_name="Unhealthy Dep",
                dependency_type=DependencyType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                health_score=30.0,
                metrics=DependencyMetrics(),
                connection_pool=None,
                circuit_breaker_status="open",
                last_success=None,
                last_failure=now,
                failure_count_1h=100,
                anomalies=["High error rate"],
                last_updated=now,
            ),
        ]

        score = monitor._calculate_overall_health(deps)

        # Unhealthy dep should have more weight
        assert score < 60.0  # Weighted toward unhealthy

    def test_identify_critical_issues(self, monitor):
        """Test identification of critical issues."""
        now = datetime.now(UTC)
        deps = [
            DependencyStatus(
                dependency_id="dep-1",
                dependency_name="Unhealthy DB",
                dependency_type=DependencyType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                health_score=30.0,
                metrics=DependencyMetrics(
                    error_rate_percent=10.0,  # Critical
                    latency_p95_ms=700.0,  # Critical
                ),
                connection_pool=ConnectionPoolStatus(
                    pool_name="db-pool",
                    total_connections=50,
                    active_connections=50,
                    idle_connections=0,
                    waiting_requests=10,
                    max_connections=50,
                    utilization_percent=100.0,
                    status=HealthStatus.UNHEALTHY,
                    last_updated=now,
                ),
                circuit_breaker_status="open",
                last_success=None,
                last_failure=now,
                failure_count_1h=100,
                anomalies=[],
                last_updated=now,
            ),
        ]

        issues = monitor._identify_critical_issues(deps)

        assert len(issues) >= 3  # Error rate, latency, circuit breaker, pool
        assert any("error rate" in i.lower() for i in issues)
        assert any("circuit breaker" in i.lower() for i in issues)

    def test_detect_anomalies(self, monitor):
        """Test anomaly detection in metrics."""
        now = datetime.now(UTC)
        metrics = DependencyMetrics(
            latency_p95_ms=600.0,  # Above critical
            error_rate_percent=7.0,  # Above critical
        )
        pool = ConnectionPoolStatus(
            pool_name="db-pool",
            total_connections=48,
            active_connections=48,
            idle_connections=0,
            waiting_requests=5,
            max_connections=50,
            utilization_percent=96.0,
            status=HealthStatus.UNHEALTHY,
            last_updated=now,
        )

        anomalies = monitor._detect_anomalies(metrics, pool)

        assert len(anomalies) >= 3
        assert any("latency" in a.lower() for a in anomalies)
        assert any("error" in a.lower() for a in anomalies)
        assert any("pool" in a.lower() for a in anomalies)

    def test_generate_recommendations(self, monitor):
        """Test recommendation generation."""
        now = datetime.now(UTC)
        deps = [
            DependencyStatus(
                dependency_id="db-1",
                dependency_name="Database",
                dependency_type=DependencyType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                health_score=30.0,
                metrics=DependencyMetrics(error_rate_percent=10.0),
                connection_pool=ConnectionPoolStatus(
                    pool_name="db-pool",
                    total_connections=48,
                    active_connections=48,
                    idle_connections=0,
                    waiting_requests=5,
                    max_connections=50,
                    utilization_percent=96.0,
                    status=HealthStatus.UNHEALTHY,
                    last_updated=now,
                ),
                circuit_breaker_status="open",
                last_success=None,
                last_failure=now,
                failure_count_1h=100,
                anomalies=[],
                last_updated=now,
            ),
        ]

        recs = monitor._generate_recommendations(deps)

        assert len(recs) >= 2
        assert any("circuit breaker" in r.lower() or "availability" in r.lower() for r in recs)
        assert any("pool" in r.lower() or "connection" in r.lower() for r in recs)

    def test_find_degraded_periods(self, monitor):
        """Test finding degraded periods in history."""
        now = datetime.now(UTC)
        data_points = [
            HistoricalDataPoint(now - timedelta(hours=4), 90.0, 50.0, 0.5),  # Healthy
            HistoricalDataPoint(now - timedelta(hours=3), 60.0, 200.0, 2.0),  # Degraded
            HistoricalDataPoint(now - timedelta(hours=2), 50.0, 300.0, 5.0),  # Degraded
            HistoricalDataPoint(now - timedelta(hours=1), 95.0, 50.0, 0.1),  # Healthy
            HistoricalDataPoint(now, 92.0, 60.0, 0.2),  # Healthy
        ]

        periods = monitor._find_degraded_periods(data_points)

        assert len(periods) == 1
        # Period should span the two degraded points
        start, end = periods[0]
        assert start == now - timedelta(hours=3)
        # End is the last degraded point (previous timestamp before healthy)
        assert end == now - timedelta(hours=2)

    @pytest.mark.asyncio
    async def test_get_dependency_health_no_deps(self, monitor):
        """Test getting health with no dependencies configured."""
        result = await monitor.get_dependency_health("test-service")

        assert result.resource_id == "test-service"
        assert result.overall_health == HealthStatus.HEALTHY
        assert len(result.dependencies) == 0

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_no_services(self, monitor):
        """Test dashboard summary with no services."""
        result = await monitor.get_dashboard_summary()

        assert result.total_services == 0
        assert result.healthy_services == 0

    @pytest.mark.asyncio
    async def test_get_dependency_timeline_no_data(self, monitor):
        """Test timeline with no historical data."""
        result = await monitor.get_dependency_timeline(
            resource_id="test-service",
            dependency_id="test-dep",
            hours=24,
        )

        assert result.dependency_id == "test-dep"
        assert len(result.data_points) == 0
        assert result.average_health_score == 100.0
