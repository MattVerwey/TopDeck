"""
Chart generation utilities for reports.

Generates chart data in a format-agnostic way that can be rendered
by various frontends (matplotlib, plotly, Chart.js, etc.).
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def _parse_timestamp(timestamp: Any) -> datetime | None:
    """
    Parse a timestamp from various formats.

    Args:
        timestamp: Timestamp as string, datetime, or other

    Returns:
        datetime object or None if parsing fails
    """
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
    elif isinstance(timestamp, datetime):
        return timestamp
    return None


class ChartGenerator:
    """Generates chart data for reports."""

    @staticmethod
    def generate_error_timeline_chart(
        errors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a timeline chart showing errors over time.

        Args:
            errors: List of error snapshots with timestamps

        Returns:
            Chart data in a generic format
        """
        # Group errors by hour
        error_counts: dict[str, int] = {}
        severity_counts: dict[str, dict[str, int]] = {}

        for error in errors:
            timestamp = _parse_timestamp(error.get("timestamp"))
            if not timestamp:
                continue

            # Round to hour
            hour_key = timestamp.strftime("%Y-%m-%d %H:00")
            error_counts[hour_key] = error_counts.get(hour_key, 0) + 1

            # Track by severity
            severity = error.get("severity", "unknown")
            if severity not in severity_counts:
                severity_counts[severity] = {}
            severity_counts[severity][hour_key] = severity_counts[severity].get(hour_key, 0) + 1

        # Sort by time
        sorted_times = sorted(error_counts.keys())

        return {
            "type": "line",
            "title": "Error Timeline",
            "x_label": "Time",
            "y_label": "Error Count",
            "data": {
                "labels": sorted_times,
                "datasets": [
                    {
                        "label": "Total Errors",
                        "data": [error_counts[t] for t in sorted_times],
                        "color": "red",
                    }
                ]
                + [
                    {
                        "label": f"{severity.title()} Severity",
                        "data": [severity_counts[severity].get(t, 0) for t in sorted_times],
                        "color": ChartGenerator._get_severity_color(severity),
                    }
                    for severity in severity_counts.keys()
                ],
            },
        }

    @staticmethod
    def generate_change_impact_chart(
        changes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a chart showing change impacts over time.

        Args:
            changes: List of change requests with impact data

        Returns:
            Chart data in a generic format
        """
        change_types: dict[str, int] = {}
        risk_levels: dict[str, int] = {}

        for change in changes:
            change_type = change.get("change_type", "unknown")
            change_types[change_type] = change_types.get(change_type, 0) + 1

            risk_level = change.get("risk_level", "unknown")
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1

        return {
            "type": "bar",
            "title": "Changes by Type and Risk",
            "data": {
                "labels": list(change_types.keys()),
                "datasets": [
                    {
                        "label": "Changes by Type",
                        "data": list(change_types.values()),
                        "color": "blue",
                    }
                ],
            },
            "additional_charts": [
                {
                    "type": "pie",
                    "title": "Risk Distribution",
                    "data": {
                        "labels": list(risk_levels.keys()),
                        "datasets": [
                            {
                                "label": "Risk Levels",
                                "data": list(risk_levels.values()),
                                "colors": [
                                    ChartGenerator._get_risk_color(level)
                                    for level in risk_levels.keys()
                                ],
                            }
                        ],
                    },
                }
            ],
        }

    @staticmethod
    def generate_resource_health_chart(
        health_metrics: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a chart showing resource health over time.

        Args:
            health_metrics: List of health metric snapshots

        Returns:
            Chart data in a generic format
        """
        # Group metrics by time
        time_points: dict[str, dict[str, float]] = {}

        for metric in health_metrics:
            timestamp = _parse_timestamp(metric.get("timestamp"))
            if not timestamp:
                continue

            time_key = timestamp.strftime("%Y-%m-%d %H:%M")

            if time_key not in time_points:
                time_points[time_key] = {}

            # Extract common metrics
            for key in ["cpu_usage", "memory_usage", "error_rate", "latency_p95"]:
                if key in metric:
                    time_points[time_key][key] = metric[key]

        sorted_times = sorted(time_points.keys())

        # Build datasets for each metric
        datasets = []
        metric_names = set()
        for metrics in time_points.values():
            metric_names.update(metrics.keys())

        for metric_name in sorted(metric_names):
            datasets.append(
                {
                    "label": metric_name.replace("_", " ").title(),
                    "data": [time_points[t].get(metric_name, None) for t in sorted_times],
                    "color": ChartGenerator._get_metric_color(metric_name),
                }
            )

        return {
            "type": "line",
            "title": "Resource Health Metrics",
            "x_label": "Time",
            "y_label": "Value",
            "data": {
                "labels": sorted_times,
                "datasets": datasets,
            },
        }

    @staticmethod
    def generate_deployment_correlation_chart(
        deployments: list[dict[str, Any]],
        errors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a chart correlating deployments with error rates.

        Args:
            deployments: List of deployment events
            errors: List of errors

        Returns:
            Chart data showing correlation
        """
        # Create timeline with both deployments and errors
        timeline: dict[str, dict[str, Any]] = {}

        # Add deployments
        for deployment in deployments:
            timestamp = _parse_timestamp(deployment.get("timestamp"))
            if not timestamp:
                continue

            hour_key = timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in timeline:
                timeline[hour_key] = {"deployments": 0, "errors": 0}
            timeline[hour_key]["deployments"] += 1

        # Add errors
        for error in errors:
            timestamp = _parse_timestamp(error.get("timestamp"))
            if not timestamp:
                continue

            hour_key = timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in timeline:
                timeline[hour_key] = {"deployments": 0, "errors": 0}
            timeline[hour_key]["errors"] += 1

        sorted_times = sorted(timeline.keys())

        return {
            "type": "combo",
            "title": "Deployment and Error Correlation",
            "x_label": "Time",
            "y_label": "Count",
            "data": {
                "labels": sorted_times,
                "datasets": [
                    {
                        "label": "Deployments",
                        "data": [timeline[t]["deployments"] for t in sorted_times],
                        "type": "bar",
                        "color": "green",
                    },
                    {
                        "label": "Errors",
                        "data": [timeline[t]["errors"] for t in sorted_times],
                        "type": "line",
                        "color": "red",
                    },
                ],
            },
        }

    @staticmethod
    def _get_severity_color(severity: str) -> str:
        """Get color for error severity."""
        colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
            "info": "#17a2b8",
        }
        return colors.get(severity.lower(), "#6c757d")

    @staticmethod
    def _get_risk_color(risk_level: str) -> str:
        """Get color for risk level."""
        colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
        }
        return colors.get(risk_level.lower(), "#6c757d")

    @staticmethod
    def _get_metric_color(metric_name: str) -> str:
        """Get color for metric type."""
        colors = {
            "cpu_usage": "#007bff",
            "memory_usage": "#6f42c1",
            "error_rate": "#dc3545",
            "latency_p95": "#fd7e14",
            "request_rate": "#28a745",
            "success_rate": "#20c997",
        }
        return colors.get(metric_name.lower(), "#6c757d")
