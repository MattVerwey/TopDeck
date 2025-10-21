"""Tests for Prometheus collector."""

from datetime import datetime

import pytest

from topdeck.monitoring.collectors.prometheus import (
    MetricSeries,
    MetricValue,
    PrometheusCollector,
)


@pytest.fixture
def prometheus_collector():
    """Create a Prometheus collector instance."""
    return PrometheusCollector("http://prometheus:9090")


@pytest.mark.asyncio
async def test_prometheus_collector_initialization(prometheus_collector):
    """Test Prometheus collector initialization."""
    assert prometheus_collector.prometheus_url == "http://prometheus:9090"
    assert prometheus_collector.timeout == 30
    await prometheus_collector.close()


@pytest.mark.asyncio
async def test_close(prometheus_collector):
    """Test closing the collector."""
    await prometheus_collector.close()
    # No assertion needed, just ensure it doesn't raise


def test_get_metric_queries_pod(prometheus_collector):
    """Test metric queries for pod resource type."""
    queries = prometheus_collector._get_metric_queries("test-pod", "pod")

    assert "cpu_usage" in queries
    assert "memory_usage" in queries
    assert "latency_p95" in queries
    assert "request_rate" in queries
    assert "error_rate" in queries


def test_get_metric_queries_database(prometheus_collector):
    """Test metric queries for database resource type."""
    queries = prometheus_collector._get_metric_queries("test-db", "database")

    assert "query_duration_p95" in queries
    assert "connections" in queries
    assert "deadlocks" in queries


def test_get_metric_queries_load_balancer(prometheus_collector):
    """Test metric queries for load balancer resource type."""
    queries = prometheus_collector._get_metric_queries("test-lb", "load_balancer")

    assert "request_rate" in queries
    assert "backend_connection_errors" in queries


def test_detect_anomaly_high_error_rate(prometheus_collector):
    """Test anomaly detection for high error rate."""
    values = [
        MetricValue(datetime.utcnow(), 0.1, {}),
        MetricValue(datetime.utcnow(), 0.15, {}),
    ]

    anomaly = prometheus_collector._detect_anomaly("error_rate", values)
    assert anomaly is not None
    assert "error rate" in anomaly.lower()


def test_detect_anomaly_high_latency(prometheus_collector):
    """Test anomaly detection for high latency."""
    values = [
        MetricValue(datetime.utcnow(), 1.5, {}),
        MetricValue(datetime.utcnow(), 2.0, {}),
    ]

    anomaly = prometheus_collector._detect_anomaly("latency_p95", values)
    assert anomaly is not None
    assert "latency" in anomaly.lower()


def test_detect_anomaly_cpu_saturation(prometheus_collector):
    """Test anomaly detection for CPU saturation."""
    values = [
        MetricValue(datetime.utcnow(), 0.95, {}),
        MetricValue(datetime.utcnow(), 0.98, {}),
    ]

    anomaly = prometheus_collector._detect_anomaly("cpu_usage", values)
    assert anomaly is not None
    assert "cpu" in anomaly.lower()


def test_detect_anomaly_no_anomaly(prometheus_collector):
    """Test anomaly detection with normal values."""
    values = [
        MetricValue(datetime.utcnow(), 0.02, {}),
        MetricValue(datetime.utcnow(), 0.03, {}),
    ]

    anomaly = prometheus_collector._detect_anomaly("error_rate", values)
    assert anomaly is None


def test_calculate_health_score_perfect(prometheus_collector):
    """Test health score calculation with no issues."""
    metrics = {}
    anomalies = []

    score = prometheus_collector._calculate_health_score(metrics, anomalies)
    assert score == 100.0


def test_calculate_health_score_with_anomalies(prometheus_collector):
    """Test health score calculation with anomalies."""
    metrics = {}
    anomalies = ["High error rate", "High latency"]

    score = prometheus_collector._calculate_health_score(metrics, anomalies)
    assert score == 80.0  # 100 - (2 * 10)


def test_calculate_health_score_with_error_rate(prometheus_collector):
    """Test health score calculation with error rate metric."""
    values = [MetricValue(datetime.utcnow(), 0.05, {}) for _ in range(5)]
    metrics = {"error_rate": MetricSeries("error_rate", {}, values)}
    anomalies = []

    score = prometheus_collector._calculate_health_score(metrics, anomalies)
    assert score < 100.0  # Should be reduced due to error rate
