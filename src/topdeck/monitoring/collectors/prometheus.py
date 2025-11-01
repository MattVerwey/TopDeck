"""
Prometheus metrics collector.

Collects and queries metrics from Prometheus for performance monitoring,
bottleneck detection, and failure analysis.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx


@dataclass
class MetricValue:
    """Represents a metric value at a specific time."""

    timestamp: datetime
    value: float
    labels: dict[str, str]


@dataclass
class MetricSeries:
    """Represents a time series of metric values."""

    metric_name: str
    labels: dict[str, str]
    values: list[MetricValue]


@dataclass
class ResourceMetrics:
    """Metrics for a specific resource."""

    resource_id: str
    resource_type: str
    metrics: dict[str, MetricSeries]
    anomalies: list[str]
    health_score: float


class PrometheusCollector:
    """Collector for Prometheus metrics."""

    def __init__(self, prometheus_url: str, timeout: int = 30):
        """
        Initialize Prometheus collector.

        Args:
            prometheus_url: URL of Prometheus server (e.g., "http://prometheus:9090")
            timeout: Request timeout in seconds
        """
        self.prometheus_url = prometheus_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def query(self, query: str) -> list[dict[str, Any]]:
        """
        Execute a PromQL query.

        Args:
            query: PromQL query string

        Returns:
            List of query results
        """
        url = f"{self.prometheus_url}/api/v1/query"
        params = {"query": query}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return data.get("data", {}).get("result", [])
            return []
        except Exception:
            return []

    async def query_range(
        self, query: str, start: datetime, end: datetime, step: str = "1m"
    ) -> list[dict[str, Any]]:
        """
        Execute a PromQL range query.

        Args:
            query: PromQL query string
            start: Start time
            end: End time
            step: Query resolution step (e.g., "1m", "5m")

        Returns:
            List of query results with time series
        """
        url = f"{self.prometheus_url}/api/v1/query_range"
        params = {
            "query": query,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "step": step,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return data.get("data", {}).get("result", [])
            return []
        except Exception:
            return []

    async def get_resource_metrics(
        self, resource_id: str, resource_type: str, duration: timedelta = timedelta(hours=1)
    ) -> ResourceMetrics:
        """
        Get metrics for a specific resource.

        Args:
            resource_id: Resource identifier
            resource_type: Type of resource (pod, service, database, etc.)
            duration: Time range to query

        Returns:
            ResourceMetrics with collected metrics and analysis
        """
        end = datetime.now(UTC)
        start = end - duration

        metrics = {}
        anomalies = []

        # Define metric queries based on resource type
        metric_queries = self._get_metric_queries(resource_id, resource_type)

        for metric_name, query in metric_queries.items():
            results = await self.query_range(query, start, end, "1m")

            if results:
                for result in results:
                    labels = result.get("metric", {})
                    values_data = result.get("values", [])

                    values = [
                        MetricValue(
                            timestamp=datetime.fromtimestamp(ts), value=float(val), labels=labels
                        )
                        for ts, val in values_data
                    ]

                    series = MetricSeries(metric_name=metric_name, labels=labels, values=values)
                    metrics[metric_name] = series

                    # Check for anomalies
                    anomaly = self._detect_anomaly(metric_name, values)
                    if anomaly:
                        anomalies.append(anomaly)

        # Calculate health score
        health_score = self._calculate_health_score(metrics, anomalies)

        return ResourceMetrics(
            resource_id=resource_id,
            resource_type=resource_type,
            metrics=metrics,
            anomalies=anomalies,
            health_score=health_score,
        )

    async def get_flow_metrics(
        self, flow_path: list[str], duration: timedelta = timedelta(hours=1)
    ) -> dict[str, ResourceMetrics]:
        """
        Get metrics for all resources in a data flow.

        Args:
            flow_path: List of resource IDs in the flow
            duration: Time range to query

        Returns:
            Dictionary mapping resource IDs to their metrics
        """
        flow_metrics = {}

        for resource_id in flow_path:
            # In a real implementation, we'd need to look up the resource type
            # For now, we'll use a generic approach
            metrics = await self.get_resource_metrics(
                resource_id=resource_id, resource_type="service", duration=duration  # Default
            )
            flow_metrics[resource_id] = metrics

        return flow_metrics

    async def detect_bottlenecks(self, flow_path: list[str]) -> list[dict[str, Any]]:
        """
        Detect bottlenecks in a data flow.

        Args:
            flow_path: List of resource IDs in the flow

        Returns:
            List of detected bottlenecks with details
        """
        bottlenecks = []

        # Get metrics for all resources in the flow
        flow_metrics = await self.get_flow_metrics(flow_path)

        # Analyze each resource for bottleneck indicators
        for resource_id, metrics in flow_metrics.items():
            # High latency
            if "latency_p95" in metrics.metrics:
                latency_values = [v.value for v in metrics.metrics["latency_p95"].values]
                if latency_values and max(latency_values) > 1000:  # >1s
                    bottlenecks.append(
                        {
                            "resource_id": resource_id,
                            "type": "high_latency",
                            "severity": "high",
                            "details": f"P95 latency: {max(latency_values):.2f}ms",
                        }
                    )

            # High error rate
            if "error_rate" in metrics.metrics:
                error_values = [v.value for v in metrics.metrics["error_rate"].values]
                if error_values and max(error_values) > 0.05:  # >5% error rate
                    bottlenecks.append(
                        {
                            "resource_id": resource_id,
                            "type": "high_error_rate",
                            "severity": "critical",
                            "details": f"Error rate: {max(error_values)*100:.2f}%",
                        }
                    )

            # Resource saturation
            if "cpu_usage" in metrics.metrics:
                cpu_values = [v.value for v in metrics.metrics["cpu_usage"].values]
                if cpu_values and max(cpu_values) > 0.9:  # >90% CPU
                    bottlenecks.append(
                        {
                            "resource_id": resource_id,
                            "type": "cpu_saturation",
                            "severity": "high",
                            "details": f"CPU usage: {max(cpu_values)*100:.2f}%",
                        }
                    )

        return bottlenecks

    def _get_metric_queries(self, resource_id: str, resource_type: str) -> dict[str, str]:
        """Get PromQL queries for a resource type."""
        queries = {}

        if resource_type in ("pod", "service", "container"):
            queries.update(
                {
                    "cpu_usage": f'rate(container_cpu_usage_seconds_total{{pod=~".*{resource_id}.*"}}[5m])',
                    "memory_usage": f'container_memory_usage_bytes{{pod=~".*{resource_id}.*"}}',
                    "latency_p95": f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{pod=~".*{resource_id}.*"}}[5m]))',
                    "request_rate": f'rate(http_requests_total{{pod=~".*{resource_id}.*"}}[5m])',
                    "error_rate": f'rate(http_requests_total{{pod=~".*{resource_id}.*", status=~"5.."}}[5m]) / rate(http_requests_total{{pod=~".*{resource_id}.*"}}[5m])',
                }
            )
        elif resource_type == "database":
            queries.update(
                {
                    "query_duration_p95": f'histogram_quantile(0.95, rate(database_query_duration_seconds_bucket{{instance=~".*{resource_id}.*"}}[5m]))',
                    "connections": f'database_connections{{instance=~".*{resource_id}.*"}}',
                    "deadlocks": f'rate(database_deadlocks_total{{instance=~".*{resource_id}.*"}}[5m])',
                }
            )
        elif resource_type == "load_balancer":
            queries.update(
                {
                    "request_rate": f'rate(loadbalancer_requests_total{{name=~".*{resource_id}.*"}}[5m])',
                    "backend_connection_errors": f'rate(loadbalancer_backend_connection_errors_total{{name=~".*{resource_id}.*"}}[5m])',
                }
            )

        return queries

    def _detect_anomaly(self, metric_name: str, values: list[MetricValue]) -> str | None:
        """Detect anomalies in metric values."""
        if not values:
            return None

        # Simple threshold-based detection
        numeric_values = [v.value for v in values]

        if metric_name == "error_rate" and max(numeric_values) > 0.05:
            return f"High error rate detected: {max(numeric_values)*100:.2f}%"

        if "latency" in metric_name and max(numeric_values) > 1.0:
            return f"High latency detected: {max(numeric_values)*1000:.2f}ms"

        if "cpu" in metric_name and max(numeric_values) > 0.9:
            return f"CPU saturation detected: {max(numeric_values)*100:.2f}%"

        return None

    def _calculate_health_score(
        self, metrics: dict[str, MetricSeries], anomalies: list[str]
    ) -> float:
        """Calculate overall health score (0-100)."""
        if not metrics:
            return 100.0

        # Start with perfect score
        score = 100.0

        # Deduct points for anomalies
        score -= len(anomalies) * 10

        # Additional deductions based on metrics
        if "error_rate" in metrics:
            values = [v.value for v in metrics["error_rate"].values]
            if values:
                avg_error_rate = sum(values) / len(values)
                score -= avg_error_rate * 100  # Error rate penalty

        return max(0.0, min(100.0, score))
