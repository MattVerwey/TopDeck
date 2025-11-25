"""
Log Correlation Engine.

Addresses Market Gap #1: Log Correlation Across Distributed Systems

Problem:
- SREs spend 60% of troubleshooting time correlating logs across services
- No unified view of logs for a specific transaction
- Correlation IDs often missing or inconsistent

Solution:
- Automatic correlation ID detection and propagation tracking
- Cross-service log aggregation by transaction
- Timeline view showing logs from all affected services
- Integration with Loki, Elasticsearch, Azure Log Analytics
"""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CorrelatedLogEntry:
    """A single log entry with correlation information."""

    timestamp: datetime
    message: str
    level: LogLevel
    service_id: str
    service_name: str
    correlation_id: str | None
    trace_id: str | None
    span_id: str | None
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "level": self.level.value,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "properties": self.properties,
        }


@dataclass
class CorrelatedLogs:
    """Collection of correlated log entries across services."""

    correlation_id: str
    start_time: datetime
    end_time: datetime
    entries: list[CorrelatedLogEntry]
    services_involved: list[str]
    error_count: int
    warning_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "correlation_id": self.correlation_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "entries": [e.to_dict() for e in self.entries],
            "services_involved": self.services_involved,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "duration_ms": (self.end_time - self.start_time).total_seconds() * 1000,
        }


@dataclass
class ErrorChainLink:
    """A single link in an error propagation chain."""

    service_id: str
    service_name: str
    error_message: str
    timestamp: datetime
    level: LogLevel
    is_root_cause: bool
    downstream_service: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "is_root_cause": self.is_root_cause,
            "downstream_service": self.downstream_service,
            "properties": self.properties,
        }


@dataclass
class ErrorChain:
    """Error propagation chain across services."""

    error_id: str
    root_cause_service: str
    root_cause_error: str
    affected_services: list[str]
    propagation_path: list[ErrorChainLink]
    total_duration_ms: float
    confidence_score: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "error_id": self.error_id,
            "root_cause_service": self.root_cause_service,
            "root_cause_error": self.root_cause_error,
            "affected_services": self.affected_services,
            "propagation_path": [link.to_dict() for link in self.propagation_path],
            "total_duration_ms": self.total_duration_ms,
            "confidence_score": self.confidence_score,
        }


@dataclass
class TransactionTimelineEvent:
    """A single event in a transaction timeline."""

    timestamp: datetime
    service_id: str
    service_name: str
    event_type: str  # "request", "response", "error", "log"
    message: str
    duration_ms: float | None = None
    level: LogLevel = LogLevel.INFO
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "service_id": self.service_id,
            "service_name": self.service_name,
            "event_type": self.event_type,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "level": self.level.value,
            "properties": self.properties,
        }


@dataclass
class TransactionTimeline:
    """Complete timeline of a transaction across services."""

    transaction_id: str
    start_time: datetime
    end_time: datetime
    total_duration_ms: float
    events: list[TransactionTimelineEvent]
    services_path: list[str]
    success: bool
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "transaction_id": self.transaction_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_duration_ms": self.total_duration_ms,
            "events": [e.to_dict() for e in self.events],
            "services_path": self.services_path,
            "success": self.success,
            "error_message": self.error_message,
        }


class LogCorrelationEngine:
    """
    Engine for correlating logs across distributed services.

    This addresses the critical SRE pain point of spending 60% of
    troubleshooting time correlating logs across services.

    Features:
    - Automatic correlation ID detection and propagation tracking
    - Cross-service log aggregation by transaction
    - Timeline view showing logs from all affected services
    - Integration with Loki, Elasticsearch, Azure Log Analytics
    """

    # Common correlation ID patterns
    CORRELATION_ID_PATTERNS = [
        r"correlation[-_]?id[=:\s]+([a-zA-Z0-9\-]+)",
        r"request[-_]?id[=:\s]+([a-zA-Z0-9\-]+)",
        r"trace[-_]?id[=:\s]+([a-zA-Z0-9\-]+)",
        r"transaction[-_]?id[=:\s]+([a-zA-Z0-9\-]+)",
        r"x[-_]request[-_]id[=:\s]+([a-zA-Z0-9\-]+)",
    ]

    def __init__(
        self,
        loki_collector: Any = None,
        elasticsearch_collector: Any = None,
        azure_log_collector: Any = None,
        neo4j_client: Any = None,
    ):
        """
        Initialize the log correlation engine.

        Args:
            loki_collector: Optional Loki log collector
            elasticsearch_collector: Optional Elasticsearch collector
            azure_log_collector: Optional Azure Log Analytics collector
            neo4j_client: Neo4j client for topology information
        """
        self.loki = loki_collector
        self.elasticsearch = elasticsearch_collector
        self.azure_logs = azure_log_collector
        self.neo4j = neo4j_client
        self._correlation_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.CORRELATION_ID_PATTERNS
        ]

    async def correlate_by_correlation_id(
        self,
        correlation_id: str,
        time_window_minutes: int = 30,
    ) -> CorrelatedLogs:
        """
        Find all logs related to a transaction across all services.

        Args:
            correlation_id: The correlation ID to search for
            time_window_minutes: Time window to search (default 30 minutes)

        Returns:
            CorrelatedLogs containing all related log entries
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(minutes=time_window_minutes)

        entries: list[CorrelatedLogEntry] = []
        services_seen: set[str] = set()

        # Collect from Loki
        if self.loki:
            loki_entries = await self._query_loki(correlation_id, start_time, end_time)
            entries.extend(loki_entries)
            for entry in loki_entries:
                services_seen.add(entry.service_id)

        # Collect from Elasticsearch
        if self.elasticsearch:
            es_entries = await self._query_elasticsearch(correlation_id, start_time, end_time)
            entries.extend(es_entries)
            for entry in es_entries:
                services_seen.add(entry.service_id)

        # Collect from Azure Log Analytics
        if self.azure_logs:
            azure_entries = await self._query_azure_logs(correlation_id, start_time, end_time)
            entries.extend(azure_entries)
            for entry in azure_entries:
                services_seen.add(entry.service_id)

        # Sort entries by timestamp
        entries.sort(key=lambda e: e.timestamp)

        # Calculate statistics
        error_count = sum(1 for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL])
        warning_count = sum(1 for e in entries if e.level == LogLevel.WARNING)

        # Update time bounds based on actual entries
        if entries:
            start_time = entries[0].timestamp
            end_time = entries[-1].timestamp

        return CorrelatedLogs(
            correlation_id=correlation_id,
            start_time=start_time,
            end_time=end_time,
            entries=entries,
            services_involved=list(services_seen),
            error_count=error_count,
            warning_count=warning_count,
        )

    async def find_error_chain(
        self,
        error_id: str,
        depth: int = 5,
    ) -> ErrorChain:
        """
        Trace an error through the dependency chain.

        Args:
            error_id: The error ID or correlation ID of the initial error
            depth: Maximum depth to traverse (default 5)

        Returns:
            ErrorChain showing the propagation path
        """
        # Get correlated logs for this error
        correlated = await self.correlate_by_correlation_id(error_id, time_window_minutes=60)

        # Filter to error entries only
        error_entries = [
            e for e in correlated.entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]
        ]

        if not error_entries:
            return ErrorChain(
                error_id=error_id,
                root_cause_service="unknown",
                root_cause_error="No errors found",
                affected_services=[],
                propagation_path=[],
                total_duration_ms=0,
                confidence_score=0.0,
            )

        # Sort by timestamp to find the earliest error (likely root cause)
        error_entries.sort(key=lambda e: e.timestamp)

        # Build propagation path
        propagation_path: list[ErrorChainLink] = []
        services_affected: set[str] = set()
        root_cause = error_entries[0]

        # Get dependency information if available
        dependencies = await self._get_service_dependencies(root_cause.service_id)

        for i, entry in enumerate(error_entries[:depth]):
            is_root = i == 0
            downstream = None

            # Find if this error propagated to another service
            if i < len(error_entries) - 1:
                next_entry = error_entries[i + 1]
                if next_entry.service_id != entry.service_id:
                    downstream = next_entry.service_id

            propagation_path.append(
                ErrorChainLink(
                    service_id=entry.service_id,
                    service_name=entry.service_name,
                    error_message=entry.message,
                    timestamp=entry.timestamp,
                    level=entry.level,
                    is_root_cause=is_root,
                    downstream_service=downstream,
                    properties=entry.properties,
                )
            )
            services_affected.add(entry.service_id)

        # Calculate duration from first to last error
        if len(error_entries) > 1:
            duration = (error_entries[-1].timestamp - error_entries[0].timestamp).total_seconds()
            total_duration_ms = duration * 1000
        else:
            total_duration_ms = 0

        # Calculate confidence based on correlation quality
        confidence = self._calculate_chain_confidence(propagation_path, dependencies)

        return ErrorChain(
            error_id=error_id,
            root_cause_service=root_cause.service_id,
            root_cause_error=root_cause.message,
            affected_services=list(services_affected),
            propagation_path=propagation_path,
            total_duration_ms=total_duration_ms,
            confidence_score=confidence,
        )

    async def get_transaction_timeline(
        self,
        transaction_id: str,
        time_window_minutes: int = 30,
    ) -> TransactionTimeline:
        """
        Get a complete timeline of a transaction across services.

        Args:
            transaction_id: The transaction ID or correlation ID
            time_window_minutes: Time window to search

        Returns:
            TransactionTimeline with ordered events
        """
        # Get correlated logs
        correlated = await self.correlate_by_correlation_id(
            transaction_id, time_window_minutes
        )

        # Convert log entries to timeline events
        events: list[TransactionTimelineEvent] = []
        services_path: list[str] = []
        last_service: str | None = None

        for entry in correlated.entries:
            # Determine event type based on log content
            event_type = self._determine_event_type(entry)

            events.append(
                TransactionTimelineEvent(
                    timestamp=entry.timestamp,
                    service_id=entry.service_id,
                    service_name=entry.service_name,
                    event_type=event_type,
                    message=entry.message,
                    level=entry.level,
                    properties=entry.properties,
                )
            )

            # Track service path
            if entry.service_id != last_service:
                services_path.append(entry.service_id)
                last_service = entry.service_id

        # Determine if transaction was successful
        has_errors = correlated.error_count > 0
        error_message = None
        if has_errors:
            error_entries = [e for e in correlated.entries if e.level == LogLevel.ERROR]
            if error_entries:
                error_message = error_entries[-1].message

        # Calculate total duration
        if correlated.entries:
            duration = (correlated.end_time - correlated.start_time).total_seconds()
            total_duration_ms = duration * 1000
        else:
            total_duration_ms = 0

        return TransactionTimeline(
            transaction_id=transaction_id,
            start_time=correlated.start_time,
            end_time=correlated.end_time,
            total_duration_ms=total_duration_ms,
            events=events,
            services_path=services_path,
            success=not has_errors,
            error_message=error_message,
        )

    async def find_correlation_ids_for_error(
        self,
        resource_id: str,
        error_pattern: str,
        time_window_minutes: int = 60,
        limit: int = 10,
    ) -> list[str]:
        """
        Find correlation IDs for errors matching a pattern.

        Args:
            resource_id: The resource to search
            error_pattern: Regex pattern to match error messages
            time_window_minutes: Time window to search
            limit: Maximum number of correlation IDs to return

        Returns:
            List of correlation IDs
        """
        correlation_ids: set[str] = set()
        pattern = re.compile(error_pattern, re.IGNORECASE)

        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(minutes=time_window_minutes)

        # Search Loki
        if self.loki:
            try:
                streams = await self.loki.get_error_logs(
                    resource_id=resource_id,
                    duration=timedelta(minutes=time_window_minutes),
                )
                for stream in streams:
                    for entry in stream.entries:
                        if pattern.search(entry.message):
                            corr_id = self._extract_correlation_id(entry.message)
                            if corr_id:
                                correlation_ids.add(corr_id)
                            if len(correlation_ids) >= limit:
                                return list(correlation_ids)[:limit]
            except Exception as e:
                logger.warning("Failed to search Loki", error=str(e))

        # Search Elasticsearch
        if self.elasticsearch:
            try:
                entries = await self.elasticsearch.search_logs(
                    query={"bool": {"must": [
                        {"match": {"resource_id": resource_id}},
                        {"regexp": {"message": error_pattern}},
                    ]}},
                    start_time=start_time,
                    end_time=end_time,
                )
                for entry in entries:
                    if entry.correlation_id:
                        correlation_ids.add(entry.correlation_id)
                    if len(correlation_ids) >= limit:
                        return list(correlation_ids)[:limit]
            except Exception as e:
                logger.warning("Failed to search Elasticsearch", error=str(e))

        return list(correlation_ids)[:limit]

    # Private helper methods

    async def _query_loki(
        self,
        correlation_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[CorrelatedLogEntry]:
        """Query Loki for logs with the given correlation ID."""
        if not self.loki:
            return []

        try:
            # Query for correlation ID in log content
            query = f'{{job=~".+"}} |~ "{correlation_id}"'
            streams = await self.loki.query(
                query=query,
                start=start_time,
                end=end_time,
                limit=1000,
            )

            entries = []
            for stream in streams:
                service_id = stream.labels.get("service", stream.labels.get("job", "unknown"))
                service_name = stream.labels.get("service_name", service_id)

                for log_entry in stream.entries:
                    level = self._parse_log_level(log_entry.level or "info")
                    entries.append(
                        CorrelatedLogEntry(
                            timestamp=log_entry.timestamp,
                            message=log_entry.message,
                            level=level,
                            service_id=service_id,
                            service_name=service_name,
                            correlation_id=correlation_id,
                            trace_id=stream.labels.get("trace_id"),
                            span_id=stream.labels.get("span_id"),
                            properties=stream.labels,
                        )
                    )
            return entries
        except Exception as e:
            logger.warning("Failed to query Loki", error=str(e))
            return []

    async def _query_elasticsearch(
        self,
        correlation_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[CorrelatedLogEntry]:
        """Query Elasticsearch for logs with the given correlation ID."""
        if not self.elasticsearch:
            return []

        try:
            es_entries = await self.elasticsearch.search_by_correlation_id(
                correlation_id=correlation_id,
                start_time=start_time,
                end_time=end_time,
            )

            entries = []
            for es_entry in es_entries:
                level = self._parse_log_level(es_entry.level)
                entries.append(
                    CorrelatedLogEntry(
                        timestamp=es_entry.timestamp,
                        message=es_entry.message,
                        level=level,
                        service_id=es_entry.resource_id,
                        service_name=es_entry.operation_name or es_entry.resource_id,
                        correlation_id=es_entry.correlation_id,
                        trace_id=es_entry.properties.get("trace_id"),
                        span_id=es_entry.properties.get("span_id"),
                        properties=es_entry.properties,
                    )
                )
            return entries
        except Exception as e:
            logger.warning("Failed to query Elasticsearch", error=str(e))
            return []

    async def _query_azure_logs(
        self,
        correlation_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[CorrelatedLogEntry]:
        """Query Azure Log Analytics for logs with the given correlation ID."""
        if not self.azure_logs:
            return []

        try:
            # Query Azure Log Analytics
            query = f"""
            AppTraces
            | where TimeGenerated between(datetime('{start_time.isoformat()}') .. datetime('{end_time.isoformat()}'))
            | where Message contains "{correlation_id}"
               or Properties contains "{correlation_id}"
               or OperationId == "{correlation_id}"
            | order by TimeGenerated asc
            """
            results = await self.azure_logs.query(query)

            entries = []
            for row in results:
                level = self._parse_log_level(row.get("SeverityLevel", "info"))
                entries.append(
                    CorrelatedLogEntry(
                        timestamp=row.get("TimeGenerated", datetime.now(UTC)),
                        message=row.get("Message", ""),
                        level=level,
                        service_id=row.get("AppRoleName", "unknown"),
                        service_name=row.get("AppRoleName", "unknown"),
                        correlation_id=correlation_id,
                        trace_id=row.get("OperationId"),
                        span_id=row.get("ParentId"),
                        properties=row.get("Properties", {}),
                    )
                )
            return entries
        except Exception as e:
            logger.warning("Failed to query Azure Log Analytics", error=str(e))
            return []

    async def _get_service_dependencies(self, service_id: str) -> list[str]:
        """Get the list of services that depend on the given service."""
        if not self.neo4j:
            return []

        try:
            query = """
            MATCH (s:Resource {resource_id: $service_id})<-[:DEPENDS_ON]-(d:Resource)
            RETURN d.resource_id as dependent_id
            """
            results = await self.neo4j.execute_query(query, {"service_id": service_id})
            return [r["dependent_id"] for r in results]
        except Exception:
            return []

    def _extract_correlation_id(self, message: str) -> str | None:
        """Extract correlation ID from a log message."""
        for pattern in self._correlation_patterns:
            match = pattern.search(message)
            if match:
                return match.group(1)
        return None

    def _parse_log_level(self, level: str) -> LogLevel:
        """Parse log level string to enum."""
        level_lower = level.lower()
        if level_lower in ["debug", "trace", "verbose"]:
            return LogLevel.DEBUG
        elif level_lower in ["info", "information"]:
            return LogLevel.INFO
        elif level_lower in ["warn", "warning"]:
            return LogLevel.WARNING
        elif level_lower in ["error", "err"]:
            return LogLevel.ERROR
        elif level_lower in ["critical", "fatal", "crit"]:
            return LogLevel.CRITICAL
        return LogLevel.INFO

    def _determine_event_type(self, entry: CorrelatedLogEntry) -> str:
        """Determine the event type based on log content."""
        message_lower = entry.message.lower()
        if "request" in message_lower and ("received" in message_lower or "incoming" in message_lower):
            return "request"
        elif "response" in message_lower or "completed" in message_lower:
            return "response"
        elif entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            return "error"
        return "log"

    def _calculate_chain_confidence(
        self,
        path: list[ErrorChainLink],
        known_dependencies: list[str],
    ) -> float:
        """Calculate confidence score for an error chain."""
        if not path:
            return 0.0

        confidence = 0.5  # Base confidence

        # Increase confidence if services are in known dependency chain
        services_in_path = {link.service_id for link in path}
        dependency_overlap = services_in_path & set(known_dependencies)
        if dependency_overlap:
            confidence += 0.2 * (len(dependency_overlap) / len(services_in_path))

        # Increase confidence if timestamps are sequential
        timestamps_sequential = all(
            path[i].timestamp <= path[i + 1].timestamp
            for i in range(len(path) - 1)
        )
        if timestamps_sequential:
            confidence += 0.2

        # Increase confidence if there's a clear propagation pattern
        has_downstream_links = sum(1 for link in path if link.downstream_service is not None)
        if has_downstream_links > 0:
            confidence += 0.1 * (has_downstream_links / len(path))

        return min(confidence, 1.0)
