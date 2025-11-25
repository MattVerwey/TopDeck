"""
Error Context Aggregation.

Addresses Market Gap #2: Error Context Aggregation

Problem:
- When an error occurs, SREs must manually gather context
- Metrics, logs, traces, and configuration are in different tools
- Time-sensitive: context disappears after rotation/retention

Solution:
- Automatic context capture on error detection
- Aggregates: logs (±5 min), metrics (±15 min), traces, config state
- Topology snapshot at error time
- One-click access to all related data
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog

logger = structlog.get_logger(__name__)


class ContextType(str, Enum):
    """Type of context data."""

    LOGS = "logs"
    METRICS = "metrics"
    TRACES = "traces"
    TOPOLOGY = "topology"
    DEPLOYMENTS = "deployments"
    CONFIGURATION = "configuration"
    DEPENDENCIES = "dependencies"


@dataclass
class MetricSnapshot:
    """Snapshot of a metric at error time."""

    name: str
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)
    unit: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "unit": self.unit,
        }


@dataclass
class LogSnapshot:
    """Snapshot of logs around error time."""

    entries: list[dict[str, Any]]
    error_count: int
    warning_count: int
    time_range_start: datetime
    time_range_end: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entries": self.entries,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "time_range_start": self.time_range_start.isoformat(),
            "time_range_end": self.time_range_end.isoformat(),
        }


@dataclass
class TraceSnapshot:
    """Snapshot of traces at error time."""

    trace_id: str
    spans: list[dict[str, Any]]
    duration_ms: float
    service_path: list[str]
    has_errors: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "trace_id": self.trace_id,
            "spans": self.spans,
            "duration_ms": self.duration_ms,
            "service_path": self.service_path,
            "has_errors": self.has_errors,
        }


@dataclass
class DeploymentSnapshot:
    """Snapshot of recent deployments."""

    deployment_id: str
    service_id: str
    version: str
    deployed_at: datetime
    deployed_by: str
    commit_sha: str | None = None
    is_recent: bool = False  # Within last 24h

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "deployment_id": self.deployment_id,
            "service_id": self.service_id,
            "version": self.version,
            "deployed_at": self.deployed_at.isoformat(),
            "deployed_by": self.deployed_by,
            "commit_sha": self.commit_sha,
            "is_recent": self.is_recent,
        }


@dataclass
class DependencySnapshot:
    """Snapshot of dependency health at error time."""

    dependency_id: str
    dependency_name: str
    dependency_type: str  # database, cache, api, queue
    status: str  # healthy, degraded, unhealthy
    latency_ms: float | None
    error_rate: float | None
    last_check: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "dependency_id": self.dependency_id,
            "dependency_name": self.dependency_name,
            "dependency_type": self.dependency_type,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "error_rate": self.error_rate,
            "last_check": self.last_check.isoformat(),
        }


@dataclass
class TopologySnapshot:
    """Snapshot of topology at error time."""

    resource_id: str
    resource_type: str
    upstream_dependencies: list[str]
    downstream_dependencies: list[str]
    blast_radius_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "upstream_dependencies": self.upstream_dependencies,
            "downstream_dependencies": self.downstream_dependencies,
            "blast_radius_count": self.blast_radius_count,
        }


@dataclass
class ContextSnapshot:
    """Complete context snapshot for a specific point in time."""

    context_type: ContextType
    captured_at: datetime
    data: Any

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        data_dict = self.data.to_dict() if hasattr(self.data, "to_dict") else self.data
        return {
            "context_type": self.context_type.value,
            "captured_at": self.captured_at.isoformat(),
            "data": data_dict,
        }


@dataclass
class ErrorContext:
    """Complete error context with all aggregated data."""

    context_id: str
    error_time: datetime
    resource_id: str
    resource_name: str
    error_message: str
    error_type: str
    severity: str
    snapshots: dict[ContextType, ContextSnapshot]
    recommendations: list[str]
    created_at: datetime
    expires_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "context_id": self.context_id,
            "error_time": self.error_time.isoformat(),
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "severity": self.severity,
            "snapshots": {
                k.value: v.to_dict() for k, v in self.snapshots.items()
            },
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class ErrorContextAggregator:
    """
    Aggregator for capturing complete error context.

    This addresses the critical SRE pain point of manually gathering
    context from multiple tools when errors occur.

    Features:
    - Automatic context capture on error detection
    - Aggregates: logs (±5 min), metrics (±15 min), traces, config state
    - Topology snapshot at error time
    - One-click access to all related data
    """

    # Default context window sizes
    LOG_WINDOW_MINUTES = 5
    METRIC_WINDOW_MINUTES = 15
    DEPLOYMENT_WINDOW_HOURS = 24
    CONTEXT_RETENTION_HOURS = 72

    def __init__(
        self,
        prometheus_collector: Any = None,
        loki_collector: Any = None,
        tempo_collector: Any = None,
        elasticsearch_collector: Any = None,
        neo4j_client: Any = None,
    ):
        """
        Initialize the error context aggregator.

        Args:
            prometheus_collector: Prometheus metrics collector
            loki_collector: Loki log collector
            tempo_collector: Tempo trace collector
            elasticsearch_collector: Elasticsearch collector
            neo4j_client: Neo4j client for topology
        """
        self.prometheus = prometheus_collector
        self.loki = loki_collector
        self.tempo = tempo_collector
        self.elasticsearch = elasticsearch_collector
        self.neo4j = neo4j_client
        self._context_cache: dict[str, ErrorContext] = {}

    async def capture_context(
        self,
        resource_id: str,
        error_time: datetime | None = None,
        error_message: str = "",
        error_type: str = "unknown",
        severity: str = "error",
        context_window_minutes: int = 5,
    ) -> ErrorContext:
        """
        Capture complete error context for a resource.

        Args:
            resource_id: Resource identifier
            error_time: Time of the error (default: now)
            error_message: The error message
            error_type: Type of error (e.g., timeout, connection_error)
            severity: Error severity level
            context_window_minutes: Time window around error for logs

        Returns:
            ErrorContext with all aggregated data
        """
        if error_time is None:
            error_time = datetime.now(UTC)

        context_id = str(uuid4())
        now = datetime.now(UTC)

        logger.info(
            "Capturing error context",
            context_id=context_id,
            resource_id=resource_id,
            error_time=error_time.isoformat(),
        )

        snapshots: dict[ContextType, ContextSnapshot] = {}

        # Get resource information
        resource_name = await self._get_resource_name(resource_id)

        # Capture logs
        log_snapshot = await self._capture_logs(
            resource_id, error_time, context_window_minutes
        )
        if log_snapshot:
            snapshots[ContextType.LOGS] = ContextSnapshot(
                context_type=ContextType.LOGS,
                captured_at=now,
                data=log_snapshot,
            )

        # Capture metrics
        metric_snapshot = await self._capture_metrics(
            resource_id, error_time, self.METRIC_WINDOW_MINUTES
        )
        if metric_snapshot:
            snapshots[ContextType.METRICS] = ContextSnapshot(
                context_type=ContextType.METRICS,
                captured_at=now,
                data=metric_snapshot,
            )

        # Capture traces
        trace_snapshot = await self._capture_traces(resource_id, error_time)
        if trace_snapshot:
            snapshots[ContextType.TRACES] = ContextSnapshot(
                context_type=ContextType.TRACES,
                captured_at=now,
                data=trace_snapshot,
            )

        # Capture topology
        topology_snapshot = await self._capture_topology(resource_id)
        if topology_snapshot:
            snapshots[ContextType.TOPOLOGY] = ContextSnapshot(
                context_type=ContextType.TOPOLOGY,
                captured_at=now,
                data=topology_snapshot,
            )

        # Capture recent deployments
        deployment_snapshot = await self._capture_deployments(resource_id, error_time)
        if deployment_snapshot:
            snapshots[ContextType.DEPLOYMENTS] = ContextSnapshot(
                context_type=ContextType.DEPLOYMENTS,
                captured_at=now,
                data=deployment_snapshot,
            )

        # Capture dependency health
        dependency_snapshot = await self._capture_dependencies(resource_id)
        if dependency_snapshot:
            snapshots[ContextType.DEPENDENCIES] = ContextSnapshot(
                context_type=ContextType.DEPENDENCIES,
                captured_at=now,
                data=dependency_snapshot,
            )

        # Generate recommendations based on context
        recommendations = self._generate_recommendations(
            error_type, severity, snapshots
        )

        context = ErrorContext(
            context_id=context_id,
            error_time=error_time,
            resource_id=resource_id,
            resource_name=resource_name,
            error_message=error_message,
            error_type=error_type,
            severity=severity,
            snapshots=snapshots,
            recommendations=recommendations,
            created_at=now,
            expires_at=now + timedelta(hours=self.CONTEXT_RETENTION_HOURS),
        )

        # Cache the context
        self._context_cache[context_id] = context

        logger.info(
            "Error context captured",
            context_id=context_id,
            snapshots_count=len(snapshots),
        )

        return context

    async def get_context(self, context_id: str) -> ErrorContext | None:
        """
        Retrieve a previously captured error context.

        Args:
            context_id: The context ID

        Returns:
            ErrorContext if found and not expired, None otherwise
        """
        context = self._context_cache.get(context_id)
        if context and context.expires_at > datetime.now(UTC):
            return context
        return None

    async def get_contexts_by_resource(
        self,
        resource_id: str,
        limit: int = 10,
    ) -> list[ErrorContext]:
        """
        Get recent error contexts for a resource.

        Args:
            resource_id: Resource identifier
            limit: Maximum number of contexts to return

        Returns:
            List of ErrorContext objects
        """
        now = datetime.now(UTC)
        contexts = [
            ctx for ctx in self._context_cache.values()
            if ctx.resource_id == resource_id and ctx.expires_at > now
        ]
        contexts.sort(key=lambda c: c.error_time, reverse=True)
        return contexts[:limit]

    async def enrich_context(
        self,
        context_id: str,
        additional_data: dict[str, Any],
    ) -> ErrorContext | None:
        """
        Enrich an existing context with additional data.

        Args:
            context_id: The context ID
            additional_data: Additional data to add

        Returns:
            Updated ErrorContext if found
        """
        context = await self.get_context(context_id)
        if not context:
            return None

        # Add additional data to configuration snapshot
        if ContextType.CONFIGURATION not in context.snapshots:
            context.snapshots[ContextType.CONFIGURATION] = ContextSnapshot(
                context_type=ContextType.CONFIGURATION,
                captured_at=datetime.now(UTC),
                data=additional_data,
            )
        else:
            existing = context.snapshots[ContextType.CONFIGURATION].data
            if isinstance(existing, dict):
                existing.update(additional_data)

        return context

    # Private helper methods

    async def _get_resource_name(self, resource_id: str) -> str:
        """Get the resource name from Neo4j."""
        if not self.neo4j:
            return resource_id

        try:
            query = """
            MATCH (r:Resource {resource_id: $resource_id})
            RETURN r.name as name
            """
            results = await self.neo4j.execute_query(query, {"resource_id": resource_id})
            if results:
                return results[0].get("name", resource_id)
        except Exception as e:
            logger.warning("Failed to get resource name", error=str(e))

        return resource_id

    async def _capture_logs(
        self,
        resource_id: str,
        error_time: datetime,
        window_minutes: int,
    ) -> LogSnapshot | None:
        """Capture logs around the error time."""
        start_time = error_time - timedelta(minutes=window_minutes)
        end_time = error_time + timedelta(minutes=window_minutes)

        entries: list[dict[str, Any]] = []
        error_count = 0
        warning_count = 0

        # Try Loki first
        if self.loki:
            try:
                streams = await self.loki.get_resource_logs(
                    resource_id=resource_id,
                    duration=timedelta(minutes=window_minutes * 2),
                )
                for stream in streams:
                    for entry in stream.entries:
                        level = entry.level.lower() if entry.level else "info"
                        entries.append({
                            "timestamp": entry.timestamp.isoformat(),
                            "message": entry.message,
                            "level": level,
                            "labels": stream.labels,
                        })
                        if level in ["error", "critical", "fatal"]:
                            error_count += 1
                        elif level in ["warn", "warning"]:
                            warning_count += 1
            except Exception as e:
                logger.warning("Failed to capture Loki logs", error=str(e))

        # Try Elasticsearch
        if self.elasticsearch and not entries:
            try:
                es_entries = await self.elasticsearch.query_logs(
                    resource_id=resource_id,
                    start_time=start_time,
                    end_time=end_time,
                )
                for entry in es_entries:
                    level = entry.level.lower() if entry.level else "info"
                    entries.append({
                        "timestamp": entry.timestamp.isoformat(),
                        "message": entry.message,
                        "level": level,
                        "properties": entry.properties,
                    })
                    if level in ["error", "critical", "fatal"]:
                        error_count += 1
                    elif level in ["warn", "warning"]:
                        warning_count += 1
            except Exception as e:
                logger.warning("Failed to capture Elasticsearch logs", error=str(e))

        if entries:
            # Sort by timestamp
            entries.sort(key=lambda e: e["timestamp"])
            return LogSnapshot(
                entries=entries,
                error_count=error_count,
                warning_count=warning_count,
                time_range_start=start_time,
                time_range_end=end_time,
            )

        return None

    async def _capture_metrics(
        self,
        resource_id: str,
        error_time: datetime,
        window_minutes: int,
    ) -> list[MetricSnapshot] | None:
        """Capture metrics around the error time."""
        if not self.prometheus:
            return None

        metrics: list[MetricSnapshot] = []
        sanitized_id = resource_id.replace("-", "_")

        # Key metrics to capture
        metric_queries = [
            ("cpu_usage", f'rate(container_cpu_usage_seconds_total{{pod=~".*{sanitized_id}.*"}}[5m])'),
            ("memory_usage", f'container_memory_usage_bytes{{pod=~".*{sanitized_id}.*"}}'),
            ("request_rate", f'rate(http_requests_total{{service=~".*{sanitized_id}.*"}}[5m])'),
            ("error_rate", f'rate(http_requests_total{{service=~".*{sanitized_id}.*",status=~"5.."}}[5m])'),
            ("latency_p95", f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service=~".*{sanitized_id}.*"}}[5m]))'),
            ("latency_p99", f'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{{service=~".*{sanitized_id}.*"}}[5m]))'),
        ]

        try:
            for metric_name, query in metric_queries:
                result = await self.prometheus.query(query)
                if result and "data" in result and "result" in result["data"]:
                    for item in result["data"]["result"]:
                        if item.get("value"):
                            timestamp, value = item["value"]
                            metrics.append(
                                MetricSnapshot(
                                    name=metric_name,
                                    value=float(value),
                                    timestamp=datetime.fromtimestamp(timestamp, tz=UTC),
                                    labels=item.get("metric", {}),
                                )
                            )
        except Exception as e:
            logger.warning("Failed to capture Prometheus metrics", error=str(e))

        return metrics if metrics else None

    async def _capture_traces(
        self,
        resource_id: str,
        error_time: datetime,
    ) -> list[TraceSnapshot] | None:
        """Capture traces at the error time."""
        if not self.tempo:
            return None

        try:
            # Query for traces involving this service
            traces = await self.tempo.query_traces(
                service=resource_id,
                start=error_time - timedelta(minutes=5),
                end=error_time + timedelta(minutes=5),
                limit=10,
            )

            snapshots = []
            for trace in traces:
                snapshots.append(
                    TraceSnapshot(
                        trace_id=trace.trace_id,
                        spans=[span.to_dict() for span in trace.spans] if hasattr(trace, "spans") else [],
                        duration_ms=trace.duration_ms if hasattr(trace, "duration_ms") else 0,
                        service_path=trace.services if hasattr(trace, "services") else [],
                        has_errors=trace.has_errors if hasattr(trace, "has_errors") else False,
                    )
                )
            return snapshots if snapshots else None
        except Exception as e:
            logger.warning("Failed to capture Tempo traces", error=str(e))

        return None

    async def _capture_topology(
        self,
        resource_id: str,
    ) -> TopologySnapshot | None:
        """Capture topology state for the resource."""
        if not self.neo4j:
            return None

        try:
            # Get resource type
            type_query = """
            MATCH (r:Resource {resource_id: $resource_id})
            RETURN r.resource_type as resource_type
            """
            type_results = await self.neo4j.execute_query(type_query, {"resource_id": resource_id})
            resource_type = type_results[0].get("resource_type", "unknown") if type_results else "unknown"

            # Get upstream dependencies (what this resource depends on)
            upstream_query = """
            MATCH (r:Resource {resource_id: $resource_id})-[:DEPENDS_ON]->(u:Resource)
            RETURN u.resource_id as upstream_id
            """
            upstream_results = await self.neo4j.execute_query(upstream_query, {"resource_id": resource_id})
            upstream = [r["upstream_id"] for r in upstream_results]

            # Get downstream dependencies (what depends on this resource)
            downstream_query = """
            MATCH (r:Resource {resource_id: $resource_id})<-[:DEPENDS_ON]-(d:Resource)
            RETURN d.resource_id as downstream_id
            """
            downstream_results = await self.neo4j.execute_query(downstream_query, {"resource_id": resource_id})
            downstream = [r["downstream_id"] for r in downstream_results]

            # Calculate blast radius (all transitively dependent resources)
            blast_query = """
            MATCH (r:Resource {resource_id: $resource_id})<-[:DEPENDS_ON*1..5]-(affected:Resource)
            RETURN COUNT(DISTINCT affected) as blast_count
            """
            blast_results = await self.neo4j.execute_query(blast_query, {"resource_id": resource_id})
            blast_count = blast_results[0].get("blast_count", 0) if blast_results else 0

            return TopologySnapshot(
                resource_id=resource_id,
                resource_type=resource_type,
                upstream_dependencies=upstream,
                downstream_dependencies=downstream,
                blast_radius_count=blast_count,
            )
        except Exception as e:
            logger.warning("Failed to capture topology", error=str(e))

        return None

    async def _capture_deployments(
        self,
        resource_id: str,
        error_time: datetime,
    ) -> list[DeploymentSnapshot] | None:
        """Capture recent deployments for the resource."""
        if not self.neo4j:
            return None

        try:
            cutoff = error_time - timedelta(hours=self.DEPLOYMENT_WINDOW_HOURS)

            query = """
            MATCH (r:Resource {resource_id: $resource_id})<-[:DEPLOYED_TO]-(d:Deployment)
            WHERE d.deployed_at >= datetime($cutoff)
            RETURN d.deployment_id as deployment_id,
                   d.version as version,
                   d.deployed_at as deployed_at,
                   d.deployed_by as deployed_by,
                   d.commit_sha as commit_sha
            ORDER BY d.deployed_at DESC
            LIMIT 5
            """
            results = await self.neo4j.execute_query(
                query,
                {"resource_id": resource_id, "cutoff": cutoff.isoformat()},
            )

            deployments = []
            for r in results:
                deployed_at = r.get("deployed_at", datetime.now(UTC))
                if isinstance(deployed_at, str):
                    # Handle various ISO format variations safely
                    time_str = deployed_at
                    if time_str.endswith("Z"):
                        time_str = time_str[:-1] + "+00:00"
                    deployed_at = datetime.fromisoformat(time_str)
                    # Ensure timezone-aware
                    if deployed_at.tzinfo is None:
                        deployed_at = deployed_at.replace(tzinfo=UTC)

                is_recent = (error_time - deployed_at).total_seconds() < 3600  # Within 1 hour

                deployments.append(
                    DeploymentSnapshot(
                        deployment_id=r.get("deployment_id", ""),
                        service_id=resource_id,
                        version=r.get("version", ""),
                        deployed_at=deployed_at,
                        deployed_by=r.get("deployed_by", "unknown"),
                        commit_sha=r.get("commit_sha"),
                        is_recent=is_recent,
                    )
                )

            return deployments if deployments else None
        except Exception as e:
            logger.warning("Failed to capture deployments", error=str(e))

        return None

    async def _capture_dependencies(
        self,
        resource_id: str,
    ) -> list[DependencySnapshot] | None:
        """Capture dependency health status."""
        dependencies: list[DependencySnapshot] = []

        # Get dependencies from topology
        if self.neo4j:
            try:
                query = """
                MATCH (r:Resource {resource_id: $resource_id})-[:DEPENDS_ON]->(d:Resource)
                RETURN d.resource_id as dep_id,
                       d.name as dep_name,
                       d.resource_type as dep_type
                """
                results = await self.neo4j.execute_query(query, {"resource_id": resource_id})

                for r in results:
                    dep_id = r.get("dep_id", "")
                    dep_type = r.get("dep_type", "unknown")

                    # Categorize dependency type
                    if "sql" in dep_type.lower() or "database" in dep_type.lower():
                        category = "database"
                    elif "redis" in dep_type.lower() or "cache" in dep_type.lower():
                        category = "cache"
                    elif "queue" in dep_type.lower() or "rabbitmq" in dep_type.lower():
                        category = "queue"
                    else:
                        category = "api"

                    # Get health metrics if Prometheus is available
                    status = "healthy"
                    latency = None
                    error_rate = None

                    if self.prometheus:
                        try:
                            health_result = await self._get_dependency_health(dep_id)
                            status = health_result.get("status", "healthy")
                            latency = health_result.get("latency_ms")
                            error_rate = health_result.get("error_rate")
                        except Exception:
                            pass

                    dependencies.append(
                        DependencySnapshot(
                            dependency_id=dep_id,
                            dependency_name=r.get("dep_name", dep_id),
                            dependency_type=category,
                            status=status,
                            latency_ms=latency,
                            error_rate=error_rate,
                            last_check=datetime.now(UTC),
                        )
                    )
            except Exception as e:
                logger.warning("Failed to capture dependencies", error=str(e))

        return dependencies if dependencies else None

    async def _get_dependency_health(
        self,
        dependency_id: str,
    ) -> dict[str, Any]:
        """Get health metrics for a dependency."""
        if not self.prometheus:
            return {"status": "unknown"}

        try:
            sanitized_id = dependency_id.replace("-", "_")

            # Check error rate
            error_query = f'rate(http_requests_total{{service=~".*{sanitized_id}.*",status=~"5.."}}[5m])'
            error_result = await self.prometheus.query(error_query)
            error_rate = 0.0
            if error_result and "data" in error_result:
                for item in error_result["data"].get("result", []):
                    if item.get("value"):
                        error_rate = float(item["value"][1])
                        break

            # Check latency
            latency_query = f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service=~".*{sanitized_id}.*"}}[5m]))'
            latency_result = await self.prometheus.query(latency_query)
            latency_ms = None
            if latency_result and "data" in latency_result:
                for item in latency_result["data"].get("result", []):
                    if item.get("value"):
                        latency_ms = float(item["value"][1]) * 1000  # Convert to ms
                        break

            # Determine status
            status = "healthy"
            if error_rate > 0.1:  # > 10% error rate
                status = "unhealthy"
            elif error_rate > 0.01:  # > 1% error rate
                status = "degraded"
            elif latency_ms and latency_ms > 500:  # > 500ms latency
                status = "degraded"

            return {
                "status": status,
                "error_rate": error_rate,
                "latency_ms": latency_ms,
            }
        except Exception:
            return {"status": "unknown"}

    def _generate_recommendations(
        self,
        error_type: str,
        severity: str,
        snapshots: dict[ContextType, ContextSnapshot],
    ) -> list[str]:
        """Generate recommendations based on captured context."""
        recommendations: list[str] = []

        # Check for recent deployments
        if ContextType.DEPLOYMENTS in snapshots:
            deployments = snapshots[ContextType.DEPLOYMENTS].data
            if deployments:
                recent_deployments = [d for d in deployments if d.is_recent]
                if recent_deployments:
                    recommendations.append(
                        f"Recent deployment detected ({len(recent_deployments)} in last hour). "
                        "Consider rollback if this is a new issue."
                    )

        # Check dependency health
        if ContextType.DEPENDENCIES in snapshots:
            dependencies = snapshots[ContextType.DEPENDENCIES].data
            if dependencies:
                unhealthy = [d for d in dependencies if d.status in ["unhealthy", "degraded"]]
                if unhealthy:
                    dep_names = ", ".join(d.dependency_name for d in unhealthy[:3])
                    recommendations.append(
                        f"Dependencies with issues: {dep_names}. "
                        "Check dependency health before investigating service code."
                    )

        # Check blast radius
        if ContextType.TOPOLOGY in snapshots:
            topology = snapshots[ContextType.TOPOLOGY].data
            if topology and topology.blast_radius_count > 5:
                recommendations.append(
                    f"High blast radius ({topology.blast_radius_count} affected services). "
                    "Prioritize resolution and consider notifying stakeholders."
                )

        # Check error patterns in logs
        if ContextType.LOGS in snapshots:
            logs = snapshots[ContextType.LOGS].data
            if logs and logs.error_count > 10:
                recommendations.append(
                    f"High error frequency ({logs.error_count} errors). "
                    "Check for cascading failures or retry storms."
                )

        # Generic recommendations based on error type
        error_recommendations = {
            "timeout": [
                "Check for increased latency in downstream services",
                "Review connection pool settings and timeouts",
                "Look for database deadlocks or slow queries",
            ],
            "connection_error": [
                "Verify network connectivity to dependencies",
                "Check for circuit breaker trips",
                "Review DNS resolution and load balancer health",
            ],
            "memory_error": [
                "Check for memory leaks in recent deployments",
                "Review pod memory limits and requests",
                "Look for large payload processing",
            ],
            "rate_limit": [
                "Check for traffic spikes or retry loops",
                "Review rate limiting configuration",
                "Consider implementing backoff strategies",
            ],
        }

        if error_type.lower() in error_recommendations:
            recommendations.extend(error_recommendations[error_type.lower()])

        # Default recommendations if none generated
        if not recommendations:
            recommendations = [
                "Review recent deployments and configuration changes",
                "Check dependency health and connectivity",
                "Monitor metrics for anomalies",
                "Review error logs for patterns",
            ]

        return recommendations
