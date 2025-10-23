"""
Tests for monitoring-based dependency discovery.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from topdeck.discovery.monitoring_dependency_discovery import (
    DependencyEvidence,
    MonitoringDependencyDiscovery,
    TrafficPattern,
)
from topdeck.discovery.models import DependencyCategory, DependencyType
from topdeck.monitoring.collectors.loki import LogEntry, LogStream


@pytest.fixture
def mock_loki_collector():
    """Create mock Loki collector."""
    collector = MagicMock()
    collector.get_resource_logs = AsyncMock()
    return collector


@pytest.fixture
def mock_prometheus_collector():
    """Create mock Prometheus collector."""
    collector = MagicMock()
    collector.get_resource_metrics = AsyncMock()
    return collector


@pytest.fixture
def discovery_service(mock_loki_collector, mock_prometheus_collector):
    """Create monitoring dependency discovery service."""
    return MonitoringDependencyDiscovery(
        loki_collector=mock_loki_collector,
        prometheus_collector=mock_prometheus_collector
    )


class TestMonitoringDependencyDiscovery:
    """Test monitoring-based dependency discovery."""

    @pytest.mark.asyncio
    async def test_discover_dependencies_from_logs_http(self, discovery_service, mock_loki_collector):
        """Test discovering dependencies from HTTP log entries."""
        # Mock log data with HTTP requests
        log_entries = [
            LogEntry(
                timestamp=datetime.utcnow(),
                message="GET https://api.example.com/users HTTP/1.1 200",
                labels={"resource_id": "service-a"},
                level="info"
            ),
            LogEntry(
                timestamp=datetime.utcnow(),
                message="POST https://api.example.com/orders HTTP/1.1 201",
                labels={"resource_id": "service-a"},
                level="info"
            )
        ]
        
        mock_loki_collector.get_resource_logs.return_value = [
            LogStream(labels={"resource_id": "service-a"}, entries=log_entries)
        ]
        
        evidence = await discovery_service.discover_dependencies_from_logs(
            resource_ids=["service-a"],
            duration=timedelta(hours=1)
        )
        
        assert len(evidence) > 0
        # Should find dependency to api.example.com
        assert any(e.target_id == "api.example.com" for e in evidence)
        assert any(e.evidence_type == "aggregated" for e in evidence)

    @pytest.mark.asyncio
    async def test_discover_dependencies_from_logs_database(self, discovery_service, mock_loki_collector):
        """Test discovering dependencies from database connection logs."""
        log_entries = [
            LogEntry(
                timestamp=datetime.utcnow(),
                message="Connecting to postgres://db.example.com:5432/mydb",
                labels={"resource_id": "app-service"},
                level="info"
            )
        ]
        
        mock_loki_collector.get_resource_logs.return_value = [
            LogStream(labels={"resource_id": "app-service"}, entries=log_entries)
        ]
        
        evidence = await discovery_service.discover_dependencies_from_logs(
            resource_ids=["app-service"],
            duration=timedelta(hours=1)
        )
        
        assert len(evidence) > 0
        assert any(e.target_id == "db.example.com" for e in evidence)
        assert any(e.details.get("protocol") == "postgres" for e in evidence)

    @pytest.mark.asyncio
    async def test_discover_dependencies_no_logs(self, discovery_service, mock_loki_collector):
        """Test discovering dependencies when no logs available."""
        mock_loki_collector.get_resource_logs.return_value = []
        
        evidence = await discovery_service.discover_dependencies_from_logs(
            resource_ids=["service-a"],
            duration=timedelta(hours=1)
        )
        
        assert len(evidence) == 0

    @pytest.mark.asyncio
    async def test_discover_dependencies_from_metrics(self, discovery_service, mock_prometheus_collector):
        """Test discovering dependencies from Prometheus metrics."""
        from topdeck.monitoring.collectors.prometheus import MetricSeries, MetricValue, ResourceMetrics
        
        # Mock metric data
        metrics = ResourceMetrics(
            resource_id="service-a",
            resource_type="service",
            metrics={
                "request_rate": MetricSeries(
                    metric_name="request_rate",
                    labels={"target_service": "service-b"},
                    values=[
                        MetricValue(
                            timestamp=datetime.utcnow(),
                            value=10.5,
                            labels={"target_service": "service-b"}
                        )
                    ]
                )
            },
            anomalies=[],
            health_score=95.0
        )
        
        mock_prometheus_collector.get_resource_metrics.return_value = metrics
        
        evidence = await discovery_service.discover_dependencies_from_metrics(
            resource_ids=["service-a"],
            duration=timedelta(hours=1)
        )
        
        assert len(evidence) > 0
        assert evidence[0].source_id == "service-a"
        assert evidence[0].target_id == "service-b"
        assert evidence[0].evidence_type == "metrics"
        assert evidence[0].confidence > 0.5

    @pytest.mark.asyncio
    async def test_analyze_traffic_patterns(self, discovery_service, mock_loki_collector, mock_prometheus_collector):
        """Test analyzing traffic patterns combining logs and metrics."""
        from topdeck.monitoring.collectors.prometheus import MetricSeries, MetricValue, ResourceMetrics
        
        # Mock log data
        log_entries = [
            LogEntry(
                timestamp=datetime.utcnow(),
                message="Calling service-b",
                labels={"resource_id": "service-a"},
                level="info"
            )
        ]
        mock_loki_collector.get_resource_logs.return_value = [
            LogStream(labels={"resource_id": "service-a"}, entries=log_entries)
        ]
        
        # Mock metric data
        metrics = ResourceMetrics(
            resource_id="service-a",
            resource_type="service",
            metrics={
                "request_rate": MetricSeries(
                    metric_name="request_rate",
                    labels={"target_service": "service-b"},
                    values=[
                        MetricValue(
                            timestamp=datetime.utcnow(),
                            value=15.0,
                            labels={"target_service": "service-b"}
                        )
                    ]
                )
            },
            anomalies=[],
            health_score=95.0
        )
        mock_prometheus_collector.get_resource_metrics.return_value = metrics
        
        patterns = await discovery_service.analyze_traffic_patterns(
            resource_ids=["service-a"],
            duration=timedelta(hours=1)
        )
        
        assert len(patterns) > 0
        assert patterns[0].source_id == "service-a"
        assert patterns[0].target_id == "service-b"
        # Confidence should be boosted due to multiple evidence types
        assert patterns[0].confidence > 0.6

    def test_create_dependencies_from_traffic_patterns(self, discovery_service):
        """Test creating dependencies from traffic patterns."""
        patterns = [
            TrafficPattern(
                source_id="service-a",
                target_id="service-b",
                protocol="https",
                request_count=150,
                confidence=0.9
            ),
            TrafficPattern(
                source_id="service-a",
                target_id="service-c",
                protocol="http",
                request_count=5,
                confidence=0.6
            ),
            TrafficPattern(
                source_id="service-b",
                target_id="database-1",
                protocol="postgresql",
                request_count=200,
                confidence=0.95
            )
        ]
        
        dependencies = discovery_service.create_dependencies_from_traffic_patterns(
            patterns,
            min_confidence=0.5
        )
        
        assert len(dependencies) == 3
        
        # High request count should create REQUIRED dependency
        high_traffic_dep = next(d for d in dependencies if d.target_id == "service-b")
        assert high_traffic_dep.dependency_type == DependencyType.REQUIRED
        assert high_traffic_dep.strength > 0.8
        
        # Low request count should create OPTIONAL dependency
        low_traffic_dep = next(d for d in dependencies if d.target_id == "service-c")
        assert low_traffic_dep.dependency_type == DependencyType.OPTIONAL
        
        # Database should be DATA category
        db_dep = next(d for d in dependencies if d.target_id == "database-1")
        assert db_dep.category == DependencyCategory.DATA

    def test_create_dependencies_filters_low_confidence(self, discovery_service):
        """Test that low-confidence patterns are filtered out."""
        patterns = [
            TrafficPattern(
                source_id="service-a",
                target_id="service-b",
                protocol="https",
                request_count=100,
                confidence=0.3  # Low confidence
            )
        ]
        
        dependencies = discovery_service.create_dependencies_from_traffic_patterns(
            patterns,
            min_confidence=0.5
        )
        
        assert len(dependencies) == 0

    def test_extract_targets_from_log_http(self, discovery_service):
        """Test extracting HTTP targets from log messages."""
        message = "Sending GET request to https://api.example.com:8443/users"
        
        targets = discovery_service._extract_targets_from_log(message)
        
        assert len(targets) > 0
        assert targets[0]["id"] == "api.example.com:8443"
        assert targets[0]["protocol"] == "https"
        assert targets[0]["confidence"] > 0.5

    def test_extract_targets_from_log_database(self, discovery_service):
        """Test extracting database targets from log messages."""
        message = "Connecting to postgres://mydb.database.windows.net:5432"
        
        targets = discovery_service._extract_targets_from_log(message)
        
        assert len(targets) > 0
        assert "mydb.database.windows.net" in targets[0]["id"]
        assert targets[0]["protocol"] == "postgres"

    def test_extract_targets_from_log_service_name(self, discovery_service):
        """Test extracting service names from log messages."""
        message = "Calling order-service for processing"
        
        targets = discovery_service._extract_targets_from_log(message)
        
        assert len(targets) > 0
        assert targets[0]["id"] == "order-service"
        assert targets[0]["confidence"] < 0.7  # Service name has lower confidence

    def test_aggregate_evidence(self, discovery_service):
        """Test aggregating evidence from multiple sources."""
        evidence_list = [
            DependencyEvidence(
                source_id="service-a",
                target_id="service-b",
                evidence_type="logs",
                confidence=0.6,
                details={"source": "logs"},
                discovered_at=datetime.utcnow()
            ),
            DependencyEvidence(
                source_id="service-a",
                target_id="service-b",
                evidence_type="metrics",
                confidence=0.8,
                details={"source": "metrics"},
                discovered_at=datetime.utcnow()
            ),
            DependencyEvidence(
                source_id="service-a",
                target_id="service-c",
                evidence_type="logs",
                confidence=0.7,
                details={"source": "logs"},
                discovered_at=datetime.utcnow()
            )
        ]
        
        aggregated = discovery_service._aggregate_evidence(evidence_list)
        
        # Should combine the two pieces of evidence for service-b
        assert len(aggregated) == 2
        
        # Find the aggregated evidence for service-b
        service_b_evidence = next(e for e in aggregated if e.target_id == "service-b")
        assert service_b_evidence.evidence_type == "aggregated"
        # Confidence should be boosted due to multiple evidence types
        assert service_b_evidence.confidence > 0.7
        assert service_b_evidence.details["occurrence_count"] == 2
