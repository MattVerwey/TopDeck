"""Tests for chart generator."""

from datetime import UTC, datetime, timedelta

from topdeck.reporting.chart_generator import ChartGenerator


def test_generate_error_timeline_chart():
    """Test generating error timeline chart."""
    now = datetime.now(UTC)
    errors = [
        {
            "timestamp": now - timedelta(hours=2),
            "severity": "critical",
            "message": "Error 1",
        },
        {
            "timestamp": now - timedelta(hours=1),
            "severity": "high",
            "message": "Error 2",
        },
        {
            "timestamp": now - timedelta(hours=1),
            "severity": "critical",
            "message": "Error 3",
        },
    ]

    chart = ChartGenerator.generate_error_timeline_chart(errors)

    assert chart["type"] == "line"
    assert chart["title"] == "Error Timeline"
    assert "data" in chart
    assert "labels" in chart["data"]
    assert "datasets" in chart["data"]
    assert len(chart["data"]["datasets"]) > 0


def test_generate_error_timeline_chart_with_string_timestamps():
    """Test generating error timeline chart with string timestamps."""
    errors = [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "severity": "high",
            "message": "Error 1",
        },
        {
            "timestamp": "2024-01-01T11:00:00Z",
            "severity": "medium",
            "message": "Error 2",
        },
    ]

    chart = ChartGenerator.generate_error_timeline_chart(errors)

    assert chart["type"] == "line"
    assert len(chart["data"]["datasets"]) > 0


def test_generate_change_impact_chart():
    """Test generating change impact chart."""
    changes = [
        {
            "change_type": "deployment",
            "risk_level": "high",
            "title": "Deploy v1.0",
        },
        {
            "change_type": "configuration",
            "risk_level": "medium",
            "title": "Update config",
        },
        {
            "change_type": "deployment",
            "risk_level": "low",
            "title": "Deploy v1.1",
        },
    ]

    chart = ChartGenerator.generate_change_impact_chart(changes)

    assert chart["type"] == "bar"
    assert chart["title"] == "Changes by Type and Risk"
    assert "data" in chart
    assert "additional_charts" in chart
    assert len(chart["additional_charts"]) > 0
    assert chart["additional_charts"][0]["type"] == "pie"


def test_generate_resource_health_chart():
    """Test generating resource health chart."""
    now = datetime.now(UTC)
    health_metrics = [
        {
            "timestamp": now - timedelta(hours=2),
            "cpu_usage": 45.5,
            "memory_usage": 60.2,
            "error_rate": 0.01,
        },
        {
            "timestamp": now - timedelta(hours=1),
            "cpu_usage": 55.3,
            "memory_usage": 65.8,
            "error_rate": 0.02,
        },
    ]

    chart = ChartGenerator.generate_resource_health_chart(health_metrics)

    assert chart["type"] == "line"
    assert chart["title"] == "Resource Health Metrics"
    assert "data" in chart
    assert "labels" in chart["data"]
    assert "datasets" in chart["data"]
    # Should have datasets for each metric
    assert len(chart["data"]["datasets"]) >= 3


def test_generate_deployment_correlation_chart():
    """Test generating deployment correlation chart."""
    now = datetime.now(UTC)
    deployments = [
        {
            "timestamp": now - timedelta(hours=2),
            "version": "v1.0",
        },
        {
            "timestamp": now - timedelta(hours=1),
            "version": "v1.1",
        },
    ]
    errors = [
        {
            "timestamp": now - timedelta(hours=2, minutes=30),
            "severity": "high",
        },
        {
            "timestamp": now - timedelta(hours=1, minutes=15),
            "severity": "critical",
        },
    ]

    chart = ChartGenerator.generate_deployment_correlation_chart(deployments, errors)

    assert chart["type"] == "combo"
    assert chart["title"] == "Deployment and Error Correlation"
    assert "data" in chart
    assert len(chart["data"]["datasets"]) == 2
    # First dataset should be deployments (bar)
    assert chart["data"]["datasets"][0]["label"] == "Deployments"
    assert chart["data"]["datasets"][0]["type"] == "bar"
    # Second dataset should be errors (line)
    assert chart["data"]["datasets"][1]["label"] == "Errors"
    assert chart["data"]["datasets"][1]["type"] == "line"


def test_get_severity_color():
    """Test getting color for severity."""
    assert ChartGenerator._get_severity_color("critical") == "#dc3545"
    assert ChartGenerator._get_severity_color("high") == "#fd7e14"
    assert ChartGenerator._get_severity_color("medium") == "#ffc107"
    assert ChartGenerator._get_severity_color("low") == "#28a745"
    assert ChartGenerator._get_severity_color("info") == "#17a2b8"
    assert ChartGenerator._get_severity_color("unknown") == "#6c757d"


def test_get_risk_color():
    """Test getting color for risk level."""
    assert ChartGenerator._get_risk_color("critical") == "#dc3545"
    assert ChartGenerator._get_risk_color("high") == "#fd7e14"
    assert ChartGenerator._get_risk_color("medium") == "#ffc107"
    assert ChartGenerator._get_risk_color("low") == "#28a745"
    assert ChartGenerator._get_risk_color("unknown") == "#6c757d"


def test_get_metric_color():
    """Test getting color for metric type."""
    assert ChartGenerator._get_metric_color("cpu_usage") == "#007bff"
    assert ChartGenerator._get_metric_color("memory_usage") == "#6f42c1"
    assert ChartGenerator._get_metric_color("error_rate") == "#dc3545"
    assert ChartGenerator._get_metric_color("latency_p95") == "#fd7e14"
    assert ChartGenerator._get_metric_color("unknown") == "#6c757d"


def test_empty_error_timeline():
    """Test generating error timeline with empty data."""
    chart = ChartGenerator.generate_error_timeline_chart([])

    assert chart["type"] == "line"
    assert chart["data"]["labels"] == []
    assert len(chart["data"]["datasets"]) == 1  # Total errors dataset


def test_empty_change_impact():
    """Test generating change impact chart with empty data."""
    chart = ChartGenerator.generate_change_impact_chart([])

    assert chart["type"] == "bar"
    assert chart["data"]["labels"] == []


def test_empty_resource_health():
    """Test generating resource health chart with empty data."""
    chart = ChartGenerator.generate_resource_health_chart([])

    assert chart["type"] == "line"
    assert chart["data"]["labels"] == []
    assert len(chart["data"]["datasets"]) == 0
