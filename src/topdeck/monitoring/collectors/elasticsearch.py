"""
Elasticsearch collector.

Collects and queries logs from Elasticsearch for transaction tracing,
error tracking, and correlation with resource topology.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ElasticsearchEntry:
    """
    Represents a single log entry from Elasticsearch.

    Attributes:
        timestamp: When the log entry was created
        message: The log message content
        properties: Additional custom fields from the log entry
        resource_id: Identifier of the resource that generated the log
        correlation_id: Optional correlation/trace ID for request tracking
        operation_name: Optional name of the operation being performed
        level: Log level (debug, info, warning, error, critical)
    """

    timestamp: datetime
    message: str
    properties: dict[str, Any]
    resource_id: str
    correlation_id: str | None = None
    operation_name: str | None = None
    level: str = "info"


@dataclass
class TransactionTrace:
    """
    Represents a trace of a transaction through the system.

    Attributes:
        transaction_id: Unique identifier for the transaction
        start_time: When the transaction started
        end_time: When the transaction completed
        duration_ms: Total duration in milliseconds
        entries: All log entries associated with this transaction
        resource_path: Ordered list of resources the transaction touched
        error_count: Number of error-level log entries
        warning_count: Number of warning-level log entries
    """

    transaction_id: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    entries: list[ElasticsearchEntry]
    resource_path: list[str]
    error_count: int
    warning_count: int


class ElasticsearchCollector:
    """Collector for Elasticsearch logs."""

    # Log level constants
    LEVEL_DEBUG = "debug"
    LEVEL_INFO = "info"
    LEVEL_WARNING = "warning"
    LEVEL_ERROR = "error"
    LEVEL_CRITICAL = "critical"

    # Fields to exclude from properties extraction
    EXCLUDED_PROPERTY_FIELDS = {
        "@timestamp",
        "message",
        "level",
        "severity",
        "correlation_id",
        "correlationId",
        "transaction_id",
        "transactionId",
        "trace_id",
        "traceId",
        "resource_id",
        "operation_name",
        "operation",
    }

    def __init__(
        self,
        url: str,
        index_pattern: str = "logs-*",
        username: str | None = None,
        password: str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
    ):
        """
        Initialize Elasticsearch collector.

        Args:
            url: Elasticsearch URL (e.g., "https://elasticsearch.example.com:9200")
            index_pattern: Index pattern to search (default: "logs-*")
            username: Basic auth username (optional)
            password: Basic auth password (optional)
            api_key: API key for authentication (optional, preferred over basic auth)
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip("/")
        self.index_pattern = index_pattern
        self.timeout = timeout

        # Setup authentication
        headers = {"Content-Type": "application/json"}
        auth = None

        if api_key:
            headers["Authorization"] = f"ApiKey {api_key}"
        elif username and password:
            auth = (username, password)

        self.client = httpx.AsyncClient(timeout=timeout, auth=auth, headers=headers)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def search(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Execute an Elasticsearch query.

        Args:
            query: Elasticsearch query DSL

        Returns:
            List of search results (hits)
        """
        try:
            response = await self.client.post(
                f"{self.url}/{self.index_pattern}/_search", json=query
            )
            response.raise_for_status()
            data = response.json()

            # Extract hits
            hits = data.get("hits", {}).get("hits", [])
            return [hit.get("_source", {}) for hit in hits]

        except Exception as e:
            logger.error(f"Failed to search Elasticsearch: {e}", exc_info=True)
            return []

    async def get_logs_by_correlation_id(
        self, correlation_id: str, duration: timedelta = timedelta(hours=1)
    ) -> list[ElasticsearchEntry]:
        """
        Get all logs for a specific correlation/transaction ID.

        Args:
            correlation_id: Transaction/correlation ID to trace
            duration: Time range to search (backwards from now)

        Returns:
            List of log entries ordered by timestamp
        """
        # Build Elasticsearch query to find logs with correlation_id
        now = datetime.now(UTC)
        start_time = now - duration

        query = {
            "size": 10000,
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": now.isoformat(),
                                }
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {"term": {"correlation_id": correlation_id}},
                                    {"term": {"correlationId": correlation_id}},
                                    {"term": {"transaction_id": correlation_id}},
                                    {"term": {"transactionId": correlation_id}},
                                    {"term": {"trace_id": correlation_id}},
                                    {"term": {"traceId": correlation_id}},
                                    {"match_phrase": {"message": correlation_id}},
                                ],
                                "minimum_should_match": 1,
                            }
                        },
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "asc"}}],
        }

        results = await self.search(query)

        entries = []
        for result in results:
            entries.append(
                ElasticsearchEntry(
                    timestamp=self._parse_timestamp(result.get("@timestamp")),
                    message=result.get("message", ""),
                    properties=self._extract_properties(result),
                    resource_id=self._extract_resource_id(result),
                    correlation_id=self._extract_correlation_id(result),
                    operation_name=result.get("operation_name") or result.get("operation"),
                    level=self._normalize_level(
                        result.get("level", result.get("severity", "info"))
                    ),
                )
            )

        return entries

    async def trace_transaction_flow(
        self, correlation_id: str, duration: timedelta = timedelta(hours=1)
    ) -> TransactionTrace | None:
        """
        Trace a transaction through the system using correlation ID.

        Args:
            correlation_id: Transaction/correlation ID to trace
            duration: Time range to search

        Returns:
            TransactionTrace with complete flow information
        """
        entries = await self.get_logs_by_correlation_id(correlation_id, duration)

        if not entries:
            return None

        # Extract resource path (order of resources touched)
        resource_path = []
        seen_resources = set()
        for entry in entries:
            if entry.resource_id and entry.resource_id not in seen_resources:
                resource_path.append(entry.resource_id)
                seen_resources.add(entry.resource_id)

        # Count errors and warnings
        error_count = sum(1 for e in entries if e.level in (self.LEVEL_ERROR, self.LEVEL_CRITICAL))
        warning_count = sum(1 for e in entries if e.level == self.LEVEL_WARNING)

        # Calculate duration
        start_time = entries[0].timestamp
        end_time = entries[-1].timestamp
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return TransactionTrace(
            transaction_id=correlation_id,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            entries=entries,
            resource_path=resource_path,
            error_count=error_count,
            warning_count=warning_count,
        )

    async def get_resource_logs(
        self, resource_id: str, level: str | None = None, duration: timedelta = timedelta(hours=1)
    ) -> list[ElasticsearchEntry]:
        """
        Get logs for a specific resource.

        Args:
            resource_id: Resource identifier
            level: Filter by log level (error, warn, info, etc.)
            duration: Time range to query

        Returns:
            List of log entries
        """
        now = datetime.now(UTC)
        start_time = now - duration

        must_clauses: list[dict[str, Any]] = [
            {"range": {"@timestamp": {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
            {
                "bool": {
                    "should": [
                        {"term": {"resource_id": resource_id}},
                        {"term": {"resource.id": resource_id}},
                        {"term": {"kubernetes.pod.name": resource_id}},
                        {"term": {"container.name": resource_id}},
                        {"term": {"service.name": resource_id}},
                    ],
                    "minimum_should_match": 1,
                }
            },
        ]

        if level:
            must_clauses.append({"term": {"level": level.lower()}})

        query = {
            "size": 1000,
            "query": {"bool": {"must": must_clauses}},
            "sort": [{"@timestamp": {"order": "desc"}}],
        }

        results = await self.search(query)

        entries = []
        for result in results:
            entries.append(
                ElasticsearchEntry(
                    timestamp=self._parse_timestamp(result.get("@timestamp")),
                    message=result.get("message", ""),
                    properties=self._extract_properties(result),
                    resource_id=self._extract_resource_id(result),
                    correlation_id=self._extract_correlation_id(result),
                    operation_name=result.get("operation_name") or result.get("operation"),
                    level=self._normalize_level(
                        result.get("level", result.get("severity", "info"))
                    ),
                )
            )

        return entries

    async def find_correlation_ids_for_resource(
        self, resource_id: str, duration: timedelta = timedelta(hours=1), limit: int = 100
    ) -> list[str]:
        """
        Find correlation IDs associated with a resource.

        Args:
            resource_id: Resource identifier
            duration: Time range to search
            limit: Maximum number of correlation IDs to return

        Returns:
            List of unique correlation IDs
        """
        now = datetime.now(UTC)
        start_time = now - duration

        query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": now.isoformat(),
                                }
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {"term": {"resource_id": resource_id}},
                                    {"term": {"resource.id": resource_id}},
                                    {"term": {"kubernetes.pod.name": resource_id}},
                                    {"term": {"container.name": resource_id}},
                                    {"term": {"service.name": resource_id}},
                                ],
                                "minimum_should_match": 1,
                            }
                        },
                        {"exists": {"field": "correlation_id"}},
                    ]
                }
            },
            "aggs": {
                "correlation_ids": {"terms": {"field": "correlation_id.keyword", "size": limit}}
            },
        }

        try:
            response = await self.client.post(
                f"{self.url}/{self.index_pattern}/_search", json=query
            )
            response.raise_for_status()
            data = response.json()

            # Extract correlation IDs from aggregation
            buckets = data.get("aggregations", {}).get("correlation_ids", {}).get("buckets", [])
            return [bucket["key"] for bucket in buckets]

        except Exception as e:
            logger.error(
                f"Failed to find correlation IDs for resource {resource_id}: {e}", exc_info=True
            )
            return []

    def _parse_timestamp(self, timestamp_str: str | None) -> datetime:
        """Parse timestamp string to datetime."""
        if not timestamp_str:
            return datetime.now(UTC)

        try:
            # Handle ISO format with trailing 'Z' for UTC
            # Only replace 'Z' if it's at the end of the string
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError):
            # Fallback to current time if parsing fails
            logger.warning(f"Failed to parse timestamp: {timestamp_str}")
            return datetime.now(UTC)

    def _extract_resource_id(self, doc: dict[str, Any]) -> str:
        """Extract resource ID from document."""
        # Try various common field names
        return (
            doc.get("resource_id")
            or doc.get("resource", {}).get("id")
            or doc.get("kubernetes", {}).get("pod", {}).get("name")
            or doc.get("container", {}).get("name")
            or doc.get("service", {}).get("name")
            or ""
        )

    def _extract_correlation_id(self, doc: dict[str, Any]) -> str | None:
        """Extract correlation ID from document."""
        return (
            doc.get("correlation_id")
            or doc.get("correlationId")
            or doc.get("transaction_id")
            or doc.get("transactionId")
            or doc.get("trace_id")
            or doc.get("traceId")
        )

    def _extract_properties(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Extract additional properties from document."""
        # Exclude common fields to avoid duplication
        return {k: v for k, v in doc.items() if k not in self.EXCLUDED_PROPERTY_FIELDS}

    def _normalize_level(self, level: str | int) -> str:
        """Normalize log level to standard format."""
        if isinstance(level, int):
            # Syslog severity levels
            if level <= 1:
                return self.LEVEL_CRITICAL
            elif level <= 3:
                return self.LEVEL_ERROR
            elif level == 4:
                return self.LEVEL_WARNING
            elif level <= 6:
                return self.LEVEL_INFO
            else:
                return self.LEVEL_DEBUG

        level_lower = str(level).lower()

        if level_lower in ("0", "verbose", "trace", "debug"):
            return self.LEVEL_DEBUG
        elif level_lower in ("1", "information", "info"):
            return self.LEVEL_INFO
        elif level_lower in ("2", "warning", "warn"):
            return self.LEVEL_WARNING
        elif level_lower in ("3", "error", "err"):
            return self.LEVEL_ERROR
        elif level_lower in ("4", "critical", "fatal", "crit"):
            return self.LEVEL_CRITICAL
        else:
            return self.LEVEL_INFO
