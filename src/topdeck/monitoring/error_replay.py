"""
Error Replay Service.

Captures, stores, and replays errors from observability platforms to help
debug and understand the root cause of problems. Acts as a "DVR for cloud errors"
by recording full context (logs, metrics, traces, topology state) at the time
of each error.

Key Features:
- Capture errors from all observability platforms
- Store error snapshots with full context
- Replay error sequences to understand causation
- Correlate errors with topology changes
- Time-travel debugging to see system state at error time
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from topdeck.monitoring.collectors.azure_log_analytics import AzureLogAnalyticsCollector
from topdeck.monitoring.collectors.elasticsearch import ElasticsearchCollector
from topdeck.monitoring.collectors.loki import LokiCollector
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.collectors.tempo import TempoCollector
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorSource(str, Enum):
    """Source of error detection."""

    PROMETHEUS = "prometheus"
    LOKI = "loki"
    TEMPO = "tempo"
    ELASTICSEARCH = "elasticsearch"
    AZURE_LOG_ANALYTICS = "azure_log_analytics"
    APPLICATION = "application"
    MANUAL = "manual"


@dataclass
class ErrorSnapshot:
    """Complete snapshot of an error with full context."""

    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    source: ErrorSource
    resource_id: str | None
    resource_type: str | None
    message: str
    error_type: str | None = None
    stack_trace: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    # Context at time of error
    logs: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    traces: list[dict[str, Any]] = field(default_factory=list)
    topology_snapshot: dict[str, Any] = field(default_factory=dict)

    # Correlation data
    related_errors: list[str] = field(default_factory=list)
    affected_resources: list[str] = field(default_factory=list)
    deployment_context: dict[str, Any] | None = None

    # Metadata
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorReplayResult:
    """Result of replaying an error."""

    error_id: str
    original_timestamp: datetime
    error_snapshot: ErrorSnapshot
    timeline: list[dict[str, Any]]
    root_cause_analysis: dict[str, Any]
    recommendations: list[str]
    related_changes: list[dict[str, Any]]


@dataclass
class ErrorSearchFilter:
    """Filter criteria for searching errors."""

    start_time: datetime | None = None
    end_time: datetime | None = None
    severity: ErrorSeverity | None = None
    source: ErrorSource | None = None
    resource_id: str | None = None
    resource_type: str | None = None
    error_type: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    limit: int = 100


class ErrorReplayService:
    """Service for capturing, storing, and replaying errors."""

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        prometheus_url: str | None = None,
        loki_url: str | None = None,
        tempo_url: str | None = None,
        elasticsearch_url: str | None = None,
        azure_workspace_id: str | None = None,
    ):
        """
        Initialize error replay service.

        Args:
            neo4j_client: Neo4j client for topology and error storage
            prometheus_url: Prometheus server URL
            loki_url: Loki server URL
            tempo_url: Tempo server URL
            elasticsearch_url: Elasticsearch server URL
            azure_workspace_id: Azure Log Analytics workspace ID
        """
        self.neo4j_client = neo4j_client

        # Initialize collectors for different platforms
        self.prometheus_collector = (
            PrometheusCollector(prometheus_url) if prometheus_url else None
        )
        self.loki_collector = LokiCollector(loki_url) if loki_url else None
        self.tempo_collector = TempoCollector(tempo_url) if tempo_url else None
        self.elasticsearch_collector = (
            ElasticsearchCollector(elasticsearch_url) if elasticsearch_url else None
        )
        self.azure_log_collector = (
            AzureLogAnalyticsCollector(azure_workspace_id) if azure_workspace_id else None
        )

    def _generate_error_id(
        self, timestamp: datetime, message: str, resource_id: str | None
    ) -> str:
        """Generate a unique error ID."""
        content = f"{timestamp.isoformat()}-{message}-{resource_id or 'unknown'}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def capture_error(
        self,
        message: str,
        severity: ErrorSeverity,
        source: ErrorSource,
        resource_id: str | None = None,
        resource_type: str | None = None,
        error_type: str | None = None,
        stack_trace: str | None = None,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        tags: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ErrorSnapshot:
        """
        Capture an error with full context.

        Args:
            message: Error message
            severity: Error severity level
            source: Source where error was detected
            resource_id: ID of affected resource
            resource_type: Type of affected resource
            error_type: Type/category of error
            stack_trace: Stack trace if available
            correlation_id: Correlation ID for related events
            trace_id: Distributed trace ID
            span_id: Span ID within trace
            tags: Additional tags
            metadata: Additional metadata

        Returns:
            ErrorSnapshot with full context
        """
        timestamp = datetime.now(UTC)
        error_id = self._generate_error_id(timestamp, message, resource_id)

        # Collect context from all available sources
        logs = await self._collect_surrounding_logs(timestamp, resource_id, correlation_id)
        metrics = await self._collect_metrics_at_time(timestamp, resource_id)
        traces = await self._collect_traces(trace_id, correlation_id)
        topology_snapshot = await self._capture_topology_snapshot(timestamp, resource_id)

        # Find related errors
        related_errors = await self._find_related_errors(
            timestamp, resource_id, correlation_id, trace_id
        )

        # Find affected resources
        affected_resources = await self._identify_affected_resources(
            resource_id, error_type, topology_snapshot
        )

        # Get deployment context
        deployment_context = await self._get_deployment_context(timestamp, resource_id)

        # Create error snapshot
        error_snapshot = ErrorSnapshot(
            error_id=error_id,
            timestamp=timestamp,
            severity=severity,
            source=source,
            resource_id=resource_id,
            resource_type=resource_type,
            message=message,
            error_type=error_type,
            stack_trace=stack_trace,
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            logs=logs,
            metrics=metrics,
            traces=traces,
            topology_snapshot=topology_snapshot,
            related_errors=related_errors,
            affected_resources=affected_resources,
            deployment_context=deployment_context,
            tags=tags or {},
            metadata=metadata or {},
        )

        # Store error snapshot
        await self._store_error_snapshot(error_snapshot)

        return error_snapshot

    async def replay_error(self, error_id: str) -> ErrorReplayResult:
        """
        Replay an error to understand what happened.

        Args:
            error_id: ID of error to replay

        Returns:
            ErrorReplayResult with timeline and analysis
        """
        # Retrieve error snapshot
        error_snapshot = await self._retrieve_error_snapshot(error_id)
        if not error_snapshot:
            raise ValueError(f"Error {error_id} not found")

        # Build timeline of events leading to error
        timeline = await self._build_error_timeline(error_snapshot)

        # Perform root cause analysis
        root_cause = await self._analyze_root_cause(error_snapshot, timeline)

        # Generate recommendations
        recommendations = await self._generate_recommendations(error_snapshot, root_cause)

        # Find related changes (deployments, config changes)
        related_changes = await self._find_related_changes(
            error_snapshot.timestamp, error_snapshot.resource_id
        )

        return ErrorReplayResult(
            error_id=error_id,
            original_timestamp=error_snapshot.timestamp,
            error_snapshot=error_snapshot,
            timeline=timeline,
            root_cause_analysis=root_cause,
            recommendations=recommendations,
            related_changes=related_changes,
        )

    async def search_errors(self, filter: ErrorSearchFilter) -> list[ErrorSnapshot]:
        """
        Search for errors matching criteria.

        Args:
            filter: Search filter criteria

        Returns:
            List of matching error snapshots
        """
        query_parts = ["MATCH (e:ErrorSnapshot)"]
        where_clauses = []
        params: dict[str, Any] = {}

        # Time range filter
        if filter.start_time:
            where_clauses.append("e.timestamp >= $start_time")
            params["start_time"] = filter.start_time.isoformat()
        if filter.end_time:
            where_clauses.append("e.timestamp <= $end_time")
            params["end_time"] = filter.end_time.isoformat()

        # Property filters
        if filter.severity:
            where_clauses.append("e.severity = $severity")
            params["severity"] = filter.severity.value
        if filter.source:
            where_clauses.append("e.source = $source")
            params["source"] = filter.source.value
        if filter.resource_id:
            where_clauses.append("e.resource_id = $resource_id")
            params["resource_id"] = filter.resource_id
        if filter.resource_type:
            where_clauses.append("e.resource_type = $resource_type")
            params["resource_type"] = filter.resource_type
        if filter.error_type:
            where_clauses.append("e.error_type = $error_type")
            params["error_type"] = filter.error_type
        if filter.correlation_id:
            where_clauses.append("e.correlation_id = $correlation_id")
            params["correlation_id"] = filter.correlation_id
        if filter.trace_id:
            where_clauses.append("e.trace_id = $trace_id")
            params["trace_id"] = filter.trace_id

        # Build query
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))

        query_parts.append("RETURN e ORDER BY e.timestamp DESC LIMIT $limit")
        params["limit"] = filter.limit

        query = "\n".join(query_parts)

        # Execute query
        async with self.neo4j_client.session() as session:
            result = await session.run(query, params)
            records = await result.data()

        # Convert to ErrorSnapshot objects
        errors = []
        for record in records:
            error_data = record["e"]
            errors.append(self._dict_to_error_snapshot(error_data))

        return errors

    async def get_error_statistics(
        self, start_time: datetime, end_time: datetime
    ) -> dict[str, Any]:
        """
        Get error statistics for a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dictionary with error statistics
        """
        query = """
        MATCH (e:ErrorSnapshot)
        WHERE e.timestamp >= $start_time AND e.timestamp <= $end_time
        RETURN 
            count(e) as total_errors,
            collect(DISTINCT e.severity) as severities,
            collect(DISTINCT e.source) as sources,
            collect(DISTINCT e.resource_type) as resource_types,
            collect(DISTINCT e.error_type) as error_types
        """

        async with self.neo4j_client.session() as session:
            result = await session.run(
                query,
                {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                },
            )
            stats = await result.single()

        return {
            "total_errors": stats["total_errors"],
            "severities": stats["severities"],
            "sources": stats["sources"],
            "resource_types": stats["resource_types"],
            "error_types": stats["error_types"],
            "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat()},
        }

    # Private helper methods

    async def _collect_surrounding_logs(
        self, timestamp: datetime, resource_id: str | None, correlation_id: str | None
    ) -> list[dict[str, Any]]:
        """Collect logs surrounding the error time."""
        logs = []

        # 5 minutes before and after
        time_window = timedelta(minutes=5)
        start_time = timestamp - time_window
        end_time = timestamp + time_window

        # Try Loki first
        if self.loki_collector and resource_id:
            try:
                loki_logs = await self.loki_collector.get_logs(
                    resource_id=resource_id, start_time=start_time, end_time=end_time, limit=50
                )
                logs.extend([asdict(log) for log in loki_logs])
            except Exception as e:
                logger.debug(f"Failed to collect logs from Loki: {e}")
                pass  # Continue with other sources

        # Try Elasticsearch
        if self.elasticsearch_collector and resource_id:
            try:
                es_logs = await self.elasticsearch_collector.search_logs(
                    resource_id=resource_id, start_time=start_time, end_time=end_time, limit=50
                )
                logs.extend([asdict(log) for log in es_logs])
            except Exception as e:
                logger.debug(f"Failed to collect logs from Elasticsearch: {e}")
                pass

        # Try Azure Log Analytics
        if self.azure_log_collector and resource_id:
            try:
                azure_logs = await self.azure_log_collector.query_logs(
                    resource_id=resource_id, start_time=start_time, end_time=end_time, limit=50
                )
                logs.extend([asdict(log) for log in azure_logs])
            except Exception as e:
                logger.debug(f"Failed to collect logs from Azure Log Analytics: {e}")
                pass

        return logs

    async def _collect_metrics_at_time(
        self, timestamp: datetime, resource_id: str | None
    ) -> dict[str, Any]:
        """Collect metrics at the time of error."""
        if not self.prometheus_collector or not resource_id:
            return {}

        try:
            # Get metrics in 5-minute window around error
            metrics = await self.prometheus_collector.get_resource_metrics(
                resource_id=resource_id,
                start_time=timestamp - timedelta(minutes=5),
                end_time=timestamp + timedelta(minutes=5),
            )
            return asdict(metrics)
        except Exception as e:
            logger.debug(f"Failed to collect metrics from Prometheus: {e}")
            return {}

    async def _collect_traces(
        self, trace_id: str | None, correlation_id: str | None
    ) -> list[dict[str, Any]]:
        """Collect distributed traces related to error."""
        if not self.tempo_collector or not (trace_id or correlation_id):
            return []

        try:
            if trace_id:
                trace = await self.tempo_collector.get_trace(trace_id)
                if trace:
                    return [asdict(trace)]
            return []
        except Exception as e:
            logger.debug(f"Failed to collect traces from Tempo: {e}")
            return []

    async def _capture_topology_snapshot(
        self, timestamp: datetime, resource_id: str | None
    ) -> dict[str, Any]:
        """Capture topology state at time of error."""
        if not resource_id:
            return {}

        query = """
        MATCH (r:Resource {id: $resource_id})
        OPTIONAL MATCH (r)-[rel]-(connected:Resource)
        RETURN r, collect({relation: type(rel), resource: connected}) as connections
        """

        async with self.neo4j_client.session() as session:
            result = await session.run(query, {"resource_id": resource_id})
            record = await result.single()

        if not record:
            return {}

        return {
            "resource": dict(record["r"]),
            "connections": [dict(c) for c in record["connections"]],
            "captured_at": timestamp.isoformat(),
        }

    async def _find_related_errors(
        self,
        timestamp: datetime,
        resource_id: str | None,
        correlation_id: str | None,
        trace_id: str | None,
    ) -> list[str]:
        """Find related errors within time window."""
        query = """
        MATCH (e:ErrorSnapshot)
        WHERE e.timestamp >= $start_time 
          AND e.timestamp <= $end_time
          AND (e.resource_id = $resource_id 
               OR e.correlation_id = $correlation_id 
               OR e.trace_id = $trace_id)
        RETURN e.error_id as error_id
        LIMIT 20
        """

        time_window = timedelta(minutes=10)

        async with self.neo4j_client.session() as session:
            result = await session.run(
                query,
                {
                    "start_time": (timestamp - time_window).isoformat(),
                    "end_time": (timestamp + time_window).isoformat(),
                    "resource_id": resource_id,
                    "correlation_id": correlation_id,
                    "trace_id": trace_id,
                },
            )
            records = await result.data()

        return [record["error_id"] for record in records]

    async def _identify_affected_resources(
        self, resource_id: str | None, error_type: str | None, topology_snapshot: dict[str, Any]
    ) -> list[str]:
        """Identify resources affected by this error."""
        if not resource_id:
            return []

        # Get dependent resources
        query = """
        MATCH (r:Resource {id: $resource_id})<-[:DEPENDS_ON*1..2]-(dependent:Resource)
        RETURN DISTINCT dependent.id as resource_id
        LIMIT 20
        """

        async with self.neo4j_client.session() as session:
            result = await session.run(query, {"resource_id": resource_id})
            records = await result.data()

        return [record["resource_id"] for record in records]

    async def _get_deployment_context(
        self, timestamp: datetime, resource_id: str | None
    ) -> dict[str, Any] | None:
        """Get recent deployment context."""
        if not resource_id:
            return None

        # Look for deployments in last 24 hours
        query = """
        MATCH (r:Resource {id: $resource_id})<-[:DEPLOYS_TO]-(d:Deployment)
        WHERE d.timestamp >= $start_time AND d.timestamp <= $end_time
        RETURN d
        ORDER BY d.timestamp DESC
        LIMIT 5
        """

        async with self.neo4j_client.session() as session:
            result = await session.run(
                query,
                {
                    "resource_id": resource_id,
                    "start_time": (timestamp - timedelta(hours=24)).isoformat(),
                    "end_time": timestamp.isoformat(),
                },
            )
            records = await result.data()

        if not records:
            return None

        return {"recent_deployments": [dict(record["d"]) for record in records]}

    async def _store_error_snapshot(self, error_snapshot: ErrorSnapshot) -> None:
        """Store error snapshot in Neo4j."""
        query = """
        CREATE (e:ErrorSnapshot {
            error_id: $error_id,
            timestamp: $timestamp,
            severity: $severity,
            source: $source,
            resource_id: $resource_id,
            resource_type: $resource_type,
            message: $message,
            error_type: $error_type,
            stack_trace: $stack_trace,
            correlation_id: $correlation_id,
            trace_id: $trace_id,
            span_id: $span_id,
            logs: $logs,
            metrics: $metrics,
            traces: $traces,
            topology_snapshot: $topology_snapshot,
            related_errors: $related_errors,
            affected_resources: $affected_resources,
            deployment_context: $deployment_context,
            tags: $tags,
            metadata: $metadata
        })
        """

        # Convert to storable format
        params = {
            "error_id": error_snapshot.error_id,
            "timestamp": error_snapshot.timestamp.isoformat(),
            "severity": error_snapshot.severity.value,
            "source": error_snapshot.source.value,
            "resource_id": error_snapshot.resource_id,
            "resource_type": error_snapshot.resource_type,
            "message": error_snapshot.message,
            "error_type": error_snapshot.error_type,
            "stack_trace": error_snapshot.stack_trace,
            "correlation_id": error_snapshot.correlation_id,
            "trace_id": error_snapshot.trace_id,
            "span_id": error_snapshot.span_id,
            "logs": json.dumps(error_snapshot.logs),
            "metrics": json.dumps(error_snapshot.metrics),
            "traces": json.dumps(error_snapshot.traces),
            "topology_snapshot": json.dumps(error_snapshot.topology_snapshot),
            "related_errors": error_snapshot.related_errors,
            "affected_resources": error_snapshot.affected_resources,
            "deployment_context": json.dumps(error_snapshot.deployment_context)
            if error_snapshot.deployment_context
            else None,
            "tags": json.dumps(error_snapshot.tags),
            "metadata": json.dumps(error_snapshot.metadata),
        }

        async with self.neo4j_client.session() as session:
            await session.run(query, params)

    async def _retrieve_error_snapshot(self, error_id: str) -> ErrorSnapshot | None:
        """Retrieve error snapshot from Neo4j."""
        query = """
        MATCH (e:ErrorSnapshot {error_id: $error_id})
        RETURN e
        """

        async with self.neo4j_client.session() as session:
            result = await session.run(query, {"error_id": error_id})
            record = await result.single()

        if not record:
            return None

        return self._dict_to_error_snapshot(dict(record["e"]))

    def _dict_to_error_snapshot(self, data: dict[str, Any]) -> ErrorSnapshot:
        """Convert dictionary to ErrorSnapshot."""
        # Handle 'Z' suffix for UTC timezone (Python < 3.11 compatibility)
        timestamp_str = (
            data["timestamp"].replace("Z", "+00:00")
            if data["timestamp"].endswith("Z")
            else data["timestamp"]
        )
        return ErrorSnapshot(
            error_id=data["error_id"],
            timestamp=datetime.fromisoformat(timestamp_str),
            severity=ErrorSeverity(data["severity"]),
            source=ErrorSource(data["source"]),
            resource_id=data.get("resource_id"),
            resource_type=data.get("resource_type"),
            message=data["message"],
            error_type=data.get("error_type"),
            stack_trace=data.get("stack_trace"),
            correlation_id=data.get("correlation_id"),
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            logs=json.loads(data.get("logs", "[]")),
            metrics=json.loads(data.get("metrics", "{}")),
            traces=json.loads(data.get("traces", "[]")),
            topology_snapshot=json.loads(data.get("topology_snapshot", "{}")),
            related_errors=data.get("related_errors", []),
            affected_resources=data.get("affected_resources", []),
            deployment_context=json.loads(data["deployment_context"])
            if data.get("deployment_context")
            else None,
            tags=json.loads(data.get("tags", "{}")),
            metadata=json.loads(data.get("metadata", "{}")),
        )

    async def _build_error_timeline(
        self, error_snapshot: ErrorSnapshot
    ) -> list[dict[str, Any]]:
        """Build timeline of events leading to error."""
        timeline = []

        # Add error event
        timeline.append(
            {
                "timestamp": error_snapshot.timestamp.isoformat(),
                "type": "error",
                "message": error_snapshot.message,
                "severity": error_snapshot.severity.value,
            }
        )

        # Add logs in chronological order
        for log in sorted(error_snapshot.logs, key=lambda x: x.get("timestamp") or ""):
            timeline.append(
                {
                    "timestamp": log.get("timestamp"),
                    "type": "log",
                    "message": log.get("message", ""),
                    "level": log.get("level", "INFO"),
                }
            )

        # Add deployment events
        if error_snapshot.deployment_context:
            deployments = error_snapshot.deployment_context.get("recent_deployments", [])
            for deployment in deployments:
                timeline.append(
                    {
                        "timestamp": deployment.get("timestamp"),
                        "type": "deployment",
                        "message": f"Deployment {deployment.get('version', 'unknown')}",
                    }
                )

        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp") or "")

        return timeline

    async def _analyze_root_cause(
        self, error_snapshot: ErrorSnapshot, timeline: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze root cause of error."""
        root_cause = {
            "primary_cause": "Unknown",
            "contributing_factors": [],
            "confidence": 0.0,
        }

        # Check for recent deployments
        if error_snapshot.deployment_context:
            deployments = error_snapshot.deployment_context.get("recent_deployments", [])
            if deployments:
                root_cause["primary_cause"] = "Recent deployment"
                root_cause["contributing_factors"].append(
                    f"Deployment occurred {len(deployments)} time(s) in last 24h"
                )
                root_cause["confidence"] = 0.7

        # Check for resource issues in metrics
        if error_snapshot.metrics:
            metrics_data = error_snapshot.metrics
            if isinstance(metrics_data, dict):
                anomalies = metrics_data.get("anomalies", [])
                if anomalies:
                    root_cause["contributing_factors"].append(
                        f"Detected {len(anomalies)} metric anomalies"
                    )

        # Check for related errors
        if len(error_snapshot.related_errors) > 5:
            root_cause["contributing_factors"].append(
                f"Part of error cluster ({len(error_snapshot.related_errors)} related errors)"
            )

        return root_cause

    async def _generate_recommendations(
        self, error_snapshot: ErrorSnapshot, root_cause: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations for fixing the error."""
        recommendations = []

        # Based on root cause
        if root_cause["primary_cause"] == "Recent deployment":
            recommendations.append("Consider rolling back the recent deployment")
            recommendations.append("Review deployment logs and changes")

        # Based on severity
        if error_snapshot.severity == ErrorSeverity.CRITICAL:
            recommendations.append("Escalate to on-call engineer immediately")
            recommendations.append("Consider enabling circuit breaker if available")

        # Based on affected resources
        if len(error_snapshot.affected_resources) > 10:
            recommendations.append(
                "Multiple dependent resources affected - consider isolating the issue"
            )

        # Generic recommendations
        recommendations.append("Check resource health and dependencies")
        recommendations.append("Review recent configuration changes")

        return recommendations

    async def _find_related_changes(
        self, timestamp: datetime, resource_id: str | None
    ) -> list[dict[str, Any]]:
        """Find topology changes around error time."""
        if not resource_id:
            return []

        # Look for changes in 6-hour window
        query = """
        MATCH (r:Resource {id: $resource_id})
        OPTIONAL MATCH (d:Deployment)-[:DEPLOYS_TO]->(r)
        WHERE d.timestamp >= $start_time AND d.timestamp <= $end_time
        RETURN collect({
            type: 'deployment',
            timestamp: d.timestamp,
            details: d
        }) as changes
        """

        time_window = timedelta(hours=6)

        async with self.neo4j_client.session() as session:
            result = await session.run(
                query,
                {
                    "resource_id": resource_id,
                    "start_time": (timestamp - time_window).isoformat(),
                    "end_time": timestamp.isoformat(),
                },
            )
            record = await result.single()

        if not record:
            return []

        return record.get("changes", [])
