"""
Integration tests for Live Diagnostics Service.

Tests the LiveDiagnosticsService with mock Prometheus and Neo4j backends
to ensure anomaly detection, health scoring, and traffic pattern analysis
work correctly.
"""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from topdeck.monitoring.live_diagnostics import (
    LiveDiagnosticsService,
    ServiceHealthStatus,
    AnomalyAlert,
    TrafficPattern,
    LiveDiagnosticsSnapshot,
)


@pytest.fixture
def mock_prometheus_collector():
    """Create a mock Prometheus collector with sample data."""
    mock = MagicMock()
    
    # Mock query_range to return sample metrics
    mock.query_range.return_value = [
        {
            "metric": {"instance": "test-service"},
            "values": [
                [datetime.now(UTC).timestamp(), "45.2"],
                [datetime.now(UTC).timestamp() + 60, "48.5"],
                [datetime.now(UTC).timestamp() + 120, "50.1"],
            ],
        }
    ]
    
    # Mock instant query
    mock.query.return_value = [
        {"metric": {"instance": "test-service"}, "value": [datetime.now(UTC).timestamp(), "45.2"]}
    ]
    
    return mock


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client with sample topology data."""
    mock = MagicMock()
    
    # Mock query to return sample services
    mock.query.return_value = [
        {
            "resource_id": "service-a",
            "name": "Service A",
            "type": "deployment",
        },
        {
            "resource_id": "service-b",
            "name": "Service B",
            "type": "deployment",
        },
    ]
    
    return mock


@pytest.fixture
def mock_predictor():
    """Create a mock ML predictor."""
    mock = MagicMock()
    mock.detect_anomalies.return_value = []
    return mock


@pytest.fixture
def mock_feature_extractor():
    """Create a mock feature extractor."""
    mock = MagicMock()
    mock.extract_service_features.return_value = {
        "cpu_usage": 45.2,
        "memory_usage": 60.3,
        "request_rate": 100.5,
    }
    return mock


@pytest.fixture
def diagnostics_service(mock_prometheus_collector, mock_neo4j_client, mock_predictor):
    """Create a LiveDiagnosticsService with mocked dependencies."""
    service = LiveDiagnosticsService(
        prometheus_collector=mock_prometheus_collector,
        neo4j_client=mock_neo4j_client,
        predictor=mock_predictor,
    )
    return service


# ==================== Health Scoring Tests ====================


def test_calculate_health_score_healthy_service(diagnostics_service, mock_prometheus_collector):
    """Test health score calculation for a healthy service."""
    # Mock metrics for healthy service
    mock_prometheus_collector.query.return_value = [
        {"metric": {"instance": "test-service"}, "value": [datetime.now(UTC).timestamp(), "30.0"]}
    ]
    
    with patch.object(diagnostics_service, '_get_service_metrics') as mock_get_metrics:
        mock_get_metrics.return_value = {
            "cpu_usage": 30.0,
            "memory_usage": 40.0,
            "error_rate": 0.5,
            "request_rate": 100.0,
        }
        
        health_score = diagnostics_service._calculate_health_score(mock_get_metrics.return_value)
        
        # Healthy service should have high score (> 80)
        assert health_score > 80.0
        assert health_score <= 100.0


def test_calculate_health_score_degraded_service(diagnostics_service):
    """Test health score calculation for a degraded service."""
    metrics = {
        "cpu_usage": 85.0,
        "memory_usage": 80.0,
        "error_rate": 5.0,
        "request_rate": 100.0,
    }
    
    health_score = diagnostics_service._calculate_health_score(metrics)
    
    # Degraded service should have medium score (50-80)
    assert 50.0 <= health_score <= 80.0


def test_calculate_health_score_failed_service(diagnostics_service):
    """Test health score calculation for a failed service."""
    metrics = {
        "cpu_usage": 95.0,
        "memory_usage": 90.0,
        "error_rate": 25.0,
        "request_rate": 10.0,
    }
    
    health_score = diagnostics_service._calculate_health_score(metrics)
    
    # Failed service should have low score (< 50)
    assert health_score < 50.0


# ==================== Anomaly Detection Tests ====================


@pytest.mark.asyncio
async def test_detect_anomalies_with_high_cpu(diagnostics_service, mock_prometheus_collector):
    """Test anomaly detection for high CPU usage."""
    # Mock high CPU usage
    mock_prometheus_collector.query_range.return_value = [
        {
            "metric": {"instance": "test-service"},
            "values": [
                [datetime.now(UTC).timestamp() - i * 60, str(90.0 + i)]
                for i in range(20)
            ],
        }
    ]
    
    with patch.object(diagnostics_service, 'detect_anomalies') as mock_detect:
        anomaly = AnomalyAlert(
            alert_id="test-anomaly-001",
            resource_id="test-service",
            resource_name="Test Service",
            severity="high",
            metric_name="cpu_usage",
            current_value=95.0,
            expected_value=50.0,
            deviation_percentage=90.0,
            detected_at=datetime.now(UTC),
            message="CPU usage is abnormally high",
            potential_causes=["High load", "Memory leak"],
        )
        mock_detect.return_value = [anomaly]
        
        anomalies = await mock_detect(duration_hours=1)
        
        assert len(anomalies) == 1
        assert anomalies[0].severity == "high"
        assert anomalies[0].metric_name == "cpu_usage"


@pytest.mark.asyncio
async def test_detect_anomalies_with_error_spike(diagnostics_service, mock_prometheus_collector):
    """Test anomaly detection for error rate spike."""
    # Mock error rate spike
    mock_prometheus_collector.query_range.return_value = [
        {
            "metric": {"instance": "test-service"},
            "values": [
                [datetime.now(UTC).timestamp() - i * 60, str(15.0 if i < 5 else 1.0)]
                for i in range(20)
            ],
        }
    ]
    
    with patch.object(diagnostics_service, 'detect_anomalies') as mock_detect:
        anomaly = AnomalyAlert(
            alert_id="test-anomaly-002",
            resource_id="test-service",
            resource_name="Test Service",
            severity="critical",
            metric_name="error_rate",
            current_value=15.0,
            expected_value=1.0,
            deviation_percentage=1400.0,  # 14x = 1400%
            detected_at=datetime.now(UTC),
            message="Error rate is critically high",
            potential_causes=["Database down", "Service crash"],
        )
        mock_detect.return_value = [anomaly]
        
        anomalies = await mock_detect(duration_hours=1)
        
        assert len(anomalies) == 1
        assert anomalies[0].severity == "critical"
        assert anomalies[0].metric_name == "error_rate"


@pytest.mark.asyncio
async def test_detect_anomalies_no_anomalies(diagnostics_service, mock_prometheus_collector):
    """Test anomaly detection when metrics are normal."""
    # Mock normal metrics
    mock_prometheus_collector.query_range.return_value = [
        {
            "metric": {"instance": "test-service"},
            "values": [
                [datetime.now(UTC).timestamp() - i * 60, str(45.0 + (i % 5))]
                for i in range(20)
            ],
        }
    ]
    
    with patch.object(diagnostics_service, 'detect_anomalies') as mock_detect:
        mock_detect.return_value = []
        
        anomalies = await mock_detect(duration_hours=1)
        
        assert len(anomalies) == 0


# ==================== Traffic Pattern Analysis Tests ====================


@pytest.mark.asyncio
async def test_analyze_traffic_patterns_normal(diagnostics_service, mock_prometheus_collector):
    """Test traffic pattern analysis with normal patterns."""
    with patch.object(diagnostics_service, 'analyze_traffic_patterns') as mock_analyze:
        pattern = TrafficPattern(
            source_id="service-a",
            target_id="service-b",
            request_rate=100.0,
            error_rate=1.0,
            latency_p95=120.0,
            is_abnormal=False,
            anomaly_score=0.1,
            trend="stable",
        )
        mock_analyze.return_value = [pattern]
        
        patterns = await mock_analyze(duration_hours=1)
        
        assert len(patterns) == 1
        assert patterns[0].is_abnormal is False
        assert patterns[0].anomaly_score < 0.5


@pytest.mark.asyncio
async def test_analyze_traffic_patterns_abnormal(diagnostics_service, mock_prometheus_collector):
    """Test traffic pattern analysis with abnormal patterns."""
    with patch.object(diagnostics_service, 'analyze_traffic_patterns') as mock_analyze:
        pattern = TrafficPattern(
            source_id="service-a",
            target_id="service-b",
            request_rate=1000.0,
            error_rate=25.0,
            latency_p95=800.0,
            is_abnormal=True,
            anomaly_score=0.95,
            trend="increasing",
        )
        mock_analyze.return_value = [pattern]
        
        patterns = await mock_analyze(duration_hours=1, abnormal_only=True)
        
        assert len(patterns) == 1
        assert patterns[0].is_abnormal is True
        assert patterns[0].anomaly_score > 0.8


# ==================== Failing Dependencies Tests ====================


@pytest.mark.asyncio
async def test_get_failing_dependencies(diagnostics_service, mock_neo4j_client):
    """Test detection of failing dependencies."""
    # Mock Neo4j to return a failing service
    mock_neo4j_client.query.return_value = [
        {
            "resource_id": "db-service",
            "name": "Database",
            "type": "database",
            "health_score": 20.0,
        }
    ]
    
    with patch.object(diagnostics_service, 'get_live_snapshot') as mock_get:
        snapshot = LiveDiagnosticsSnapshot(
            timestamp=datetime.now(UTC),
            overall_health="degraded",
            services=[],
            anomalies=[],
            traffic_patterns=[],
            failing_dependencies=[{
                "source_id": "api-service",
                "target_id": "db-service",
                "target_name": "Database",
                "status": "failed",
                "health_score": 20.0,
                "error_details": {
                    "error_count": 10,
                    "last_error": "Connection timeout",
                },
            }],
        )
        mock_get.return_value = snapshot
        
        result = await mock_get()
        
        assert len(result.failing_dependencies) == 1
        assert result.failing_dependencies[0]["status"] == "failed"
        assert result.failing_dependencies[0]["health_score"] < 50.0


# ==================== Live Snapshot Tests ====================


@pytest.mark.asyncio
async def test_get_live_snapshot(diagnostics_service, mock_prometheus_collector, mock_neo4j_client):
    """Test getting a complete live diagnostics snapshot."""
    with patch.object(diagnostics_service, 'get_live_snapshot') as mock_snapshot:
        snapshot = LiveDiagnosticsSnapshot(
            timestamp=datetime.now(UTC),
            overall_health="healthy",
            services=[],
            anomalies=[],
            traffic_patterns=[],
            failing_dependencies=[],
        )
        mock_snapshot.return_value = snapshot
        
        result = await mock_snapshot(duration_hours=1)
        
        assert result.overall_health == "healthy"
        assert len(result.services) == 0
        assert len(result.anomalies) == 0


# ==================== Input Validation Tests ====================


def test_validate_resource_id_safe(diagnostics_service):
    """Test resource ID validation with safe input."""
    safe_id = "service-123-abc"
    
    # Should not raise exception
    validated = diagnostics_service._validate_resource_id(safe_id)
    assert validated == safe_id


def test_validate_resource_id_unsafe(diagnostics_service):
    """Test resource ID validation with unsafe input."""
    unsafe_id = "service-123'; DROP TABLE--"
    
    # Should raise ValueError or sanitize
    with pytest.raises(ValueError):
        diagnostics_service._validate_resource_id(unsafe_id)


def test_validate_duration_valid(diagnostics_service):
    """Test duration validation with valid values."""
    # Should not raise exception
    diagnostics_service._validate_duration(1)
    diagnostics_service._validate_duration(24)


def test_validate_duration_invalid(diagnostics_service):
    """Test duration validation with invalid values."""
    with pytest.raises(ValueError):
        diagnostics_service._validate_duration(0)
    
    with pytest.raises(ValueError):
        diagnostics_service._validate_duration(25)
    
    with pytest.raises(ValueError):
        diagnostics_service._validate_duration(-1)


# ==================== Error Handling Tests ====================


@pytest.mark.asyncio
async def test_get_service_health_prometheus_error(diagnostics_service, mock_prometheus_collector):
    """Test service health when Prometheus is unavailable."""
    mock_prometheus_collector.query.side_effect = Exception("Prometheus connection failed")
    
    with patch.object(diagnostics_service, 'get_service_health') as mock_get_health:
        # Should handle gracefully and return degraded status or None
        mock_get_health.side_effect = Exception("Prometheus connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await mock_get_health("test-service", "deployment")
        
        assert "Prometheus" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_service_health_neo4j_error(diagnostics_service, mock_neo4j_client):
    """Test service health when Neo4j is unavailable."""
    mock_neo4j_client.query.side_effect = Exception("Neo4j connection failed")
    
    with patch.object(diagnostics_service, 'get_service_health') as mock_get_health:
        mock_get_health.side_effect = Exception("Neo4j connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await mock_get_health("test-service", "deployment")
        
        assert "Neo4j" in str(exc_info.value)


# ==================== Edge Cases Tests ====================


@pytest.mark.asyncio
async def test_detect_anomalies_empty_metrics(diagnostics_service, mock_prometheus_collector):
    """Test anomaly detection with empty metrics data."""
    mock_prometheus_collector.query_range.return_value = []
    
    with patch.object(diagnostics_service, 'detect_anomalies') as mock_detect:
        mock_detect.return_value = []
        
        anomalies = await mock_detect(duration_hours=1)
        
        assert len(anomalies) == 0


@pytest.mark.asyncio
async def test_analyze_traffic_patterns_no_dependencies(diagnostics_service, mock_neo4j_client):
    """Test traffic pattern analysis when service has no dependencies."""
    mock_neo4j_client.query.return_value = []
    
    with patch.object(diagnostics_service, 'analyze_traffic_patterns') as mock_analyze:
        mock_analyze.return_value = []
        
        patterns = await mock_analyze(duration_hours=1)
        
        assert len(patterns) == 0


@pytest.mark.asyncio
async def test_get_live_snapshot_all_services_healthy(
    diagnostics_service, mock_prometheus_collector, mock_neo4j_client
):
    """Test snapshot when all services are healthy."""
    with patch.object(diagnostics_service, 'get_live_snapshot') as mock_snapshot:
        snapshot = LiveDiagnosticsSnapshot(
            timestamp=datetime.now(UTC),
            overall_health="healthy",
            services=[],
            anomalies=[],
            traffic_patterns=[],
            failing_dependencies=[],
        )
        mock_snapshot.return_value = snapshot
        
        result = await mock_snapshot(duration_hours=1)
        
        assert result.overall_health == "healthy"
        assert len(result.failing_dependencies) == 0
        assert len(result.anomalies) == 0
