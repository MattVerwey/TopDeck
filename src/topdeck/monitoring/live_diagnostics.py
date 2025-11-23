"""
Live diagnostics service for real-time anomaly detection and service health monitoring.

Integrates ML-based anomaly detection with network topology to identify
failing services and abnormal traffic patterns in real-time.
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import structlog
from sklearn.ensemble import IsolationForest

from topdeck.analysis.prediction.predictor import Predictor
from topdeck.monitoring.collectors.loki import LokiCollector
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.storage.neo4j_client import Neo4jClient

logger = structlog.get_logger(__name__)


@dataclass
class ServiceHealthStatus:
    """Health status of a service."""

    resource_id: str
    resource_name: str
    resource_type: str
    status: str  # "healthy", "degraded", "failed", "unknown"
    health_score: float  # 0.0 to 100.0
    anomalies: list[str]
    metrics: dict[str, float]
    last_updated: datetime


@dataclass
class AnomalyAlert:
    """Alert for detected anomaly."""

    alert_id: str
    resource_id: str
    resource_name: str
    severity: str  # "low", "medium", "high", "critical"
    metric_name: str
    current_value: float
    expected_value: float
    deviation_percentage: float
    detected_at: datetime
    message: str
    potential_causes: list[str]


@dataclass
class TrafficPattern:
    """Traffic pattern analysis result."""

    source_id: str
    target_id: str
    request_rate: float
    error_rate: float
    latency_p95: float
    is_abnormal: bool
    anomaly_score: float
    trend: str  # "increasing", "decreasing", "stable"


@dataclass
class LiveDiagnosticsSnapshot:
    """Complete snapshot of live diagnostics data."""

    timestamp: datetime
    overall_health: str  # "healthy", "degraded", "critical"
    services: list[ServiceHealthStatus]
    anomalies: list[AnomalyAlert]
    traffic_patterns: list[TrafficPattern]
    failing_dependencies: list[dict[str, Any]]


class LiveDiagnosticsService:
    """Service for live diagnostics and anomaly detection."""

    # Health status thresholds
    HEALTH_EXCELLENT_THRESHOLD = 90.0
    HEALTH_GOOD_THRESHOLD = 70.0
    HEALTH_DEGRADED_THRESHOLD = 50.0

    # Anomaly detection thresholds
    ANOMALY_SCORE_CRITICAL = 0.8
    ANOMALY_SCORE_HIGH = 0.6
    ANOMALY_SCORE_MEDIUM = 0.4

    def __init__(
        self,
        prometheus_collector: PrometheusCollector,
        neo4j_client: Neo4jClient,
        predictor: Predictor,
        loki_collector: LokiCollector | None = None,
    ):
        """
        Initialize live diagnostics service.

        Args:
            prometheus_collector: Prometheus metrics collector
            neo4j_client: Neo4j database client
            predictor: ML predictor for anomaly detection
            loki_collector: Optional Loki log collector for error logs
        """
        self.prometheus = prometheus_collector
        self.neo4j = neo4j_client
        self.predictor = predictor
        self.loki = loki_collector

        # Initialize anomaly detection model
        self.anomaly_detector = IsolationForest(
            contamination=0.1,  # Expect 10% of data to be anomalies
            random_state=42,
            n_estimators=100,
        )
        self.is_trained = False
        self.baseline_data: dict[str, list[float]] = {}

    async def get_live_snapshot(self, duration_hours: int = 1) -> LiveDiagnosticsSnapshot:
        """
        Get complete live diagnostics snapshot.

        Args:
            duration_hours: Time window for metrics analysis

        Returns:
            LiveDiagnosticsSnapshot with current state
        """
        logger.info("get_live_snapshot", duration_hours=duration_hours)

        # Get all resources from topology
        resources = await self._get_topology_resources()

        # Get health status for each resource
        services = []
        for resource in resources:
            health = await self.get_service_health(resource["id"], resource["type"], duration_hours)
            services.append(health)

        # Detect anomalies
        anomalies = await self.detect_anomalies([s.resource_id for s in services], duration_hours)

        # Analyze traffic patterns
        traffic_patterns = await self.analyze_traffic_patterns(duration_hours)

        # Identify failing dependencies
        failing_deps = await self.get_failing_dependencies()

        # Determine overall health
        overall_health = self._calculate_overall_health(services)

        return LiveDiagnosticsSnapshot(
            timestamp=datetime.now(UTC),
            overall_health=overall_health,
            services=services,
            anomalies=anomalies,
            traffic_patterns=traffic_patterns,
            failing_dependencies=failing_deps,
        )

    async def get_service_health(
        self, resource_id: str, resource_type: str, duration_hours: int = 1
    ) -> ServiceHealthStatus:
        """
        Get health status for a specific service.

        Args:
            resource_id: Resource identifier
            resource_type: Type of resource
            duration_hours: Time window for analysis

        Returns:
            ServiceHealthStatus with current health
        """
        # Get metrics from Prometheus
        metrics_result = await self.prometheus.get_resource_metrics(
            resource_id=resource_id,
            resource_type=resource_type,
            duration=timedelta(hours=duration_hours),
        )

        # Determine status based on health score and anomalies
        if metrics_result.health_score >= self.HEALTH_GOOD_THRESHOLD:
            status = "healthy"
        elif metrics_result.health_score >= self.HEALTH_DEGRADED_THRESHOLD:
            status = "degraded"
        else:
            status = "failed"

        # Extract key metrics
        key_metrics = {}
        for metric_name, series in metrics_result.metrics.items():
            if series.values:
                latest_value = series.values[-1].value
                key_metrics[metric_name] = latest_value

        # Get resource name from topology
        resource_name = await self._get_resource_name(resource_id)

        return ServiceHealthStatus(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
            status=status,
            health_score=metrics_result.health_score,
            anomalies=metrics_result.anomalies,
            metrics=key_metrics,
            last_updated=datetime.now(UTC),
        )

    async def detect_anomalies(
        self, resource_ids: list[str], duration_hours: int = 1
    ) -> list[AnomalyAlert]:
        """
        Detect anomalies across multiple resources.

        Args:
            resource_ids: List of resource IDs to analyze
            duration_hours: Time window for analysis

        Returns:
            List of detected anomaly alerts
        """
        alerts = []

        for resource_id in resource_ids:
            # Use ML predictor for anomaly detection
            try:
                resource_info = await self._get_resource_info(resource_id)
                anomaly_result = await self.predictor.detect_anomalies(
                    resource_id=resource_id,
                    resource_name=resource_info.get("name", resource_id),
                    detection_window_hours=duration_hours,
                )

                # Convert anomaly points to alerts
                for anomaly_point in anomaly_result.anomalies:
                    severity = self._determine_severity(anomaly_point.anomaly_score)

                    alert = AnomalyAlert(
                        alert_id=f"{resource_id}_{anomaly_point.metric_name}_{anomaly_point.timestamp.isoformat()}",
                        resource_id=resource_id,
                        resource_name=resource_info.get("name", resource_id),
                        severity=severity,
                        metric_name=anomaly_point.metric_name,
                        current_value=anomaly_point.actual_value,
                        expected_value=anomaly_point.expected_value,
                        deviation_percentage=anomaly_point.deviation_percentage,
                        detected_at=anomaly_point.timestamp,
                        message=f"Anomaly detected in {anomaly_point.metric_name}: {anomaly_point.deviation_percentage:.1f}% deviation",
                        potential_causes=anomaly_result.potential_causes,
                    )
                    alerts.append(alert)

            except Exception as e:
                logger.warning(
                    "anomaly_detection_failed",
                    resource_id=resource_id,
                    error=str(e),
                )

        # Sort by severity (critical first) and timestamp (newest first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(
            key=lambda a: (severity_order.get(a.severity, 4), a.detected_at),
            reverse=True,
        )

        return alerts

    async def analyze_traffic_patterns(self, duration_hours: int = 1) -> list[TrafficPattern]:
        """
        Analyze traffic patterns between services.

        Args:
            duration_hours: Time window for analysis

        Returns:
            List of traffic patterns with anomaly detection
        """
        patterns = []

        # Get all service dependencies
        dependencies = await self._get_service_dependencies()

        for dep in dependencies:
            source_id = dep["source"]
            target_id = dep["target"]

            # Sanitize input for Prometheus queries
            # Only allow alphanumeric, dash, underscore, and dot characters
            if not re.match(r"^[a-zA-Z0-9\-_.]+$", source_id) or not re.match(
                r"^[a-zA-Z0-9\-_.]+$", target_id
            ):
                logger.warning(
                    "invalid_resource_id_for_prometheus",
                    source_id=source_id,
                    target_id=target_id,
                )
                continue

            # Query Prometheus for traffic metrics
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(hours=duration_hours)

            # Request rate - use safe string formatting
            request_rate_query = (
                f'rate(http_requests_total{{source="{source_id}",target="{target_id}"}}[5m])'
            )
            request_rate_results = await self.prometheus.query_range(
                request_rate_query, start_time, end_time, "1m"
            )

            # Error rate - use safe string formatting
            error_rate_query = f'rate(http_requests_total{{source="{source_id}",target="{target_id}",status=~"5.."}}[5m]) / rate(http_requests_total{{source="{source_id}",target="{target_id}"}}[5m])'
            error_rate_results = await self.prometheus.query_range(
                error_rate_query, start_time, end_time, "1m"
            )

            # Latency - use safe string formatting
            latency_query = f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{source="{source_id}",target="{target_id}"}}[5m]))'
            latency_results = await self.prometheus.query_range(
                latency_query, start_time, end_time, "1m"
            )

            # Extract values
            request_rate = self._extract_avg_value(request_rate_results)
            error_rate = self._extract_avg_value(error_rate_results)
            latency_p95 = self._extract_avg_value(latency_results)

            # Detect abnormalities
            is_abnormal, anomaly_score = self._detect_traffic_anomaly(
                source_id, target_id, request_rate, error_rate, latency_p95
            )

            # Determine trend
            trend = self._calculate_trend(request_rate_results)

            pattern = TrafficPattern(
                source_id=source_id,
                target_id=target_id,
                request_rate=request_rate,
                error_rate=error_rate,
                latency_p95=latency_p95,
                is_abnormal=is_abnormal,
                anomaly_score=anomaly_score,
                trend=trend,
            )
            patterns.append(pattern)

        return patterns

    async def get_failing_dependencies(self) -> list[dict[str, Any]]:
        """
        Get list of failing dependencies with error details.

        Returns:
            List of failing dependencies with details
        """
        failing_deps = []

        # Query topology for all dependencies
        query = """
        MATCH (source)-[r:DEPENDS_ON]->(target)
        RETURN source.id as source_id,
               source.name as source_name,
               target.id as target_id,
               target.name as target_name,
               r.properties as relationship_props
        """

        try:
            results = await self.neo4j.execute_query(query)

            for record in results:
                source_id = record["source_id"]
                target_id = record["target_id"]

                # Check if dependency is failing
                target_health = await self.get_service_health(target_id, "service", 1)

                if target_health.status in ("failed", "degraded"):
                    failing_deps.append(
                        {
                            "source_id": source_id,
                            "source_name": record["source_name"],
                            "target_id": target_id,
                            "target_name": record["target_name"],
                            "status": target_health.status,
                            "health_score": target_health.health_score,
                            "anomalies": target_health.anomalies,
                            "error_details": self._extract_error_details(target_health),
                        }
                    )

        except Exception as e:
            logger.error("get_failing_dependencies_failed", error=str(e))

        return failing_deps

    async def get_recent_error_logs(
        self, resource_id: str, limit: int = 10, duration_hours: int = 1
    ) -> list[dict[str, Any]]:
        """
        Get recent error logs for a specific resource with ML-based analysis.

        Args:
            resource_id: Resource identifier
            limit: Maximum number of error logs to return (default: 10)
            duration_hours: Time window for log search (default: 1 hour)

        Returns:
            List of error log entries with timestamp, message, level, and ML analysis
        """
        if not self.loki:
            logger.warning("loki_collector_not_configured")
            return []

        try:
            # Get error logs from Loki
            error_streams = await self.loki.get_error_logs(
                resource_id=resource_id, duration=timedelta(hours=duration_hours)
            )

            # Collect all error entries
            error_entries = []
            for stream in error_streams:
                for entry in stream.entries:
                    error_entries.append(
                        {
                            "timestamp": entry.timestamp.isoformat(),
                            "message": entry.message,
                            "level": entry.level,
                            "labels": entry.labels,
                        }
                    )

            # Sort by timestamp (most recent first) and limit
            error_entries.sort(key=lambda e: e["timestamp"], reverse=True)
            limited_entries = error_entries[:limit]

            # Use ML to analyze error patterns and provide insights
            if limited_entries:
                resource_info = await self._get_resource_info(resource_id)
                resource_type = resource_info.get("type", "service")

                ml_analysis = self.predictor.analyze_error_logs(
                    error_logs=limited_entries,
                    resource_id=resource_id,
                    resource_type=resource_type,
                )

                # Add ML analysis to response
                for entry in limited_entries:
                    entry["ml_analysis"] = ml_analysis

            return limited_entries

        except Exception as e:
            logger.error("get_recent_error_logs_failed", resource_id=resource_id, error=str(e))
            return []

    def _calculate_overall_health(self, services: list[ServiceHealthStatus]) -> str:
        """Calculate overall system health from service statuses."""
        if not services:
            return "unknown"

        failed_count = sum(1 for s in services if s.status == "failed")
        degraded_count = sum(1 for s in services if s.status == "degraded")
        total = len(services)

        if failed_count > 0:
            return "critical"
        elif degraded_count > total * 0.3:  # More than 30% degraded
            return "degraded"
        else:
            return "healthy"

    def _determine_severity(self, anomaly_score: float) -> str:
        """Determine severity level from anomaly score."""
        if anomaly_score >= self.ANOMALY_SCORE_CRITICAL:
            return "critical"
        elif anomaly_score >= self.ANOMALY_SCORE_HIGH:
            return "high"
        elif anomaly_score >= self.ANOMALY_SCORE_MEDIUM:
            return "medium"
        else:
            return "low"

    def _detect_traffic_anomaly(
        self,
        source_id: str,
        target_id: str,
        request_rate: float,
        error_rate: float,
        latency_p95: float,
    ) -> tuple[bool, float]:
        """
        Detect if traffic pattern is anomalous.

        Returns:
            Tuple of (is_abnormal, anomaly_score)
        """
        anomaly_score = 0.0

        # High error rate is anomalous
        if error_rate > 0.05:  # 5%
            anomaly_score += 0.4

        # High latency is anomalous
        if latency_p95 > 1.0:  # 1 second
            anomaly_score += 0.3

        # Very low request rate might indicate issues
        if request_rate < 0.1 and error_rate > 0.01:
            anomaly_score += 0.3

        is_abnormal = anomaly_score > 0.5

        return is_abnormal, min(anomaly_score, 1.0)

    def _calculate_trend(self, query_results: list[dict[str, Any]]) -> str:
        """Calculate trend from time series data."""
        if not query_results:
            return "stable"

        try:
            values = []
            for result in query_results:
                for _, val in result.get("values", []):
                    values.append(float(val))

            if len(values) < 2:
                return "stable"

            # Simple linear trend
            first_half = np.mean(values[: len(values) // 2])
            second_half = np.mean(values[len(values) // 2 :])

            if second_half > first_half * 1.1:
                return "increasing"
            elif second_half < first_half * 0.9:
                return "decreasing"
            else:
                return "stable"

        except Exception:
            return "stable"

    def _extract_avg_value(self, query_results: list[dict[str, Any]]) -> float:
        """Extract average value from Prometheus query results."""
        if not query_results:
            return 0.0

        try:
            values = []
            for result in query_results:
                for _, val in result.get("values", []):
                    values.append(float(val))

            return np.mean(values) if values else 0.0

        except Exception:
            return 0.0

    def _extract_error_details(self, health_status: ServiceHealthStatus) -> dict[str, Any]:
        """Extract detailed error information from health status."""
        return {
            "status": health_status.status,
            "health_score": health_status.health_score,
            "anomalies": health_status.anomalies,
            "metrics": health_status.metrics,
            "timestamp": health_status.last_updated.isoformat(),
        }

    async def _get_topology_resources(self) -> list[dict[str, str]]:
        """Get all resources from topology."""
        query = """
        MATCH (n)
        WHERE n.id IS NOT NULL
        RETURN n.id as id, n.name as name, labels(n)[0] as type
        LIMIT 1000
        """

        try:
            results = await self.neo4j.execute_query(query)
            return [
                {"id": r["id"], "name": r.get("name", r["id"]), "type": r.get("type", "unknown")}
                for r in results
            ]
        except Exception as e:
            logger.error("get_topology_resources_failed", error=str(e))
            return []

    async def _get_service_dependencies(self) -> list[dict[str, str]]:
        """Get service dependencies from topology."""
        query = """
        MATCH (source)-[:DEPENDS_ON]->(target)
        RETURN source.id as source, target.id as target
        """

        try:
            results = await self.neo4j.execute_query(query)
            return [{"source": r["source"], "target": r["target"]} for r in results]
        except Exception as e:
            logger.error("get_service_dependencies_failed", error=str(e))
            return []

    async def _get_resource_name(self, resource_id: str) -> str:
        """Get resource name from topology."""
        query = """
        MATCH (n {id: $resource_id})
        RETURN n.name as name
        """

        try:
            results = await self.neo4j.execute_query(query, {"resource_id": resource_id})
            if results:
                return results[0].get("name", resource_id)
        except Exception as e:
            logger.error("get_resource_name_failed", error=str(e))

        return resource_id

    async def _get_resource_info(self, resource_id: str) -> dict[str, Any]:
        """Get resource information from topology."""
        query = """
        MATCH (n {id: $resource_id})
        RETURN n.name as name, n.type as type, labels(n)[0] as label
        """

        try:
            results = await self.neo4j.execute_query(query, {"resource_id": resource_id})
            if results:
                return {
                    "name": results[0].get("name", resource_id),
                    "type": results[0].get("type", "unknown"),
                    "label": results[0].get("label", "unknown"),
                }
        except Exception as e:
            logger.error("get_resource_info_failed", error=str(e), resource_id=resource_id)

        return {"name": resource_id, "type": "unknown", "label": "unknown"}
