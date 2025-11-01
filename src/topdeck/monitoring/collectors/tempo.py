"""
Tempo trace collector.

Collects and queries distributed traces from Grafana Tempo for transaction
tracing, performance analysis, and debugging.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx


@dataclass
class TraceSpan:
    """Represents a span in a distributed trace."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation_name: str
    service_name: str
    start_time: datetime
    duration_ms: float
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok, error


@dataclass
class Trace:
    """Represents a complete distributed trace."""

    trace_id: str
    spans: list[TraceSpan]
    start_time: datetime
    end_time: datetime
    duration_ms: float
    service_count: int
    error_count: int
    root_service: str | None = None


class TempoCollector:
    """Collector for Tempo distributed traces."""

    def __init__(self, tempo_url: str, timeout: int = 30):
        """
        Initialize Tempo collector.

        Args:
            tempo_url: URL of Tempo server (e.g., "http://tempo:3200")
            timeout: Request timeout in seconds
        """
        self.tempo_url = tempo_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def get_trace(self, trace_id: str) -> Trace | None:
        """
        Get a specific trace by ID.

        Args:
            trace_id: Trace ID to retrieve

        Returns:
            Trace object with all spans, or None if not found
        """
        url = f"{self.tempo_url}/api/traces/{trace_id}"

        try:
            response = await self.client.get(url)
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()

            return self._parse_trace(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception:
            return None

    async def search_traces(
        self,
        service_name: str | None = None,
        operation_name: str | None = None,
        tags: dict[str, str] | None = None,
        min_duration_ms: float | None = None,
        max_duration_ms: float | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 20,
    ) -> list[Trace]:
        """
        Search for traces matching criteria.

        Args:
            service_name: Filter by service name
            operation_name: Filter by operation name
            tags: Filter by tags (key-value pairs)
            min_duration_ms: Minimum trace duration in milliseconds
            max_duration_ms: Maximum trace duration in milliseconds
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of traces to return

        Returns:
            List of matching traces
        """
        url = f"{self.tempo_url}/api/search"
        
        # Build query parameters
        params: dict[str, Any] = {
            "limit": limit,
        }
        
        if start_time:
            params["start"] = int(start_time.timestamp())
        if end_time:
            params["end"] = int(end_time.timestamp())
        if min_duration_ms:
            params["minDuration"] = f"{int(min_duration_ms)}ms"
        if max_duration_ms:
            params["maxDuration"] = f"{int(max_duration_ms)}ms"
        
        # Build TraceQL query
        query_parts = []
        if service_name:
            query_parts.append(f'resource.service.name="{service_name}"')
        if operation_name:
            query_parts.append(f'name="{operation_name}"')
        if tags:
            for key, value in tags.items():
                query_parts.append(f'{key}="{value}"')
        
        if query_parts:
            params["q"] = "{" + " && ".join(query_parts) + "}"

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            traces = []
            for trace_data in data.get("traces", []):
                # Get full trace details
                trace_id = trace_data.get("traceID")
                if trace_id:
                    trace = await self.get_trace(trace_id)
                    if trace:
                        traces.append(trace)

            return traces
        except Exception:
            return []

    async def find_traces_by_resource(
        self,
        resource_id: str,
        duration: timedelta = timedelta(hours=1),
        limit: int = 50,
    ) -> list[Trace]:
        """
        Find traces involving a specific resource.

        Args:
            resource_id: Resource identifier to search for
            duration: Time range to search
            limit: Maximum number of traces to return

        Returns:
            List of traces involving the resource
        """
        end_time = datetime.now(UTC)
        start_time = end_time - duration

        # Search for traces with the resource_id in tags
        traces = await self.search_traces(
            tags={"resource.id": resource_id},
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return traces

    async def get_service_dependencies(
        self,
        service_name: str,
        duration: timedelta = timedelta(hours=1),
    ) -> dict[str, list[str]]:
        """
        Get service dependencies from traces.

        Args:
            service_name: Service to analyze
            duration: Time range to analyze

        Returns:
            Dictionary mapping services to their downstream dependencies
        """
        end_time = datetime.now(UTC)
        start_time = end_time - duration

        traces = await self.search_traces(
            service_name=service_name,
            start_time=start_time,
            end_time=end_time,
            limit=100,
        )

        dependencies: dict[str, set[str]] = {}

        for trace in traces:
            # Build dependency graph from spans
            for span in trace.spans:
                service = span.service_name
                if service not in dependencies:
                    dependencies[service] = set()

                # Find child spans (dependencies)
                for other_span in trace.spans:
                    if other_span.parent_span_id == span.span_id:
                        dependencies[service].add(other_span.service_name)

        # Convert sets to lists
        return {k: list(v) for k, v in dependencies.items()}

    def _parse_trace(self, data: dict[str, Any]) -> Trace:
        """Parse trace data from Tempo API response."""
        trace_id = data.get("traceID", "")
        batches = data.get("batches", [])

        spans: list[TraceSpan] = []
        services: set[str] = set()
        error_count = 0

        for batch in batches:
            resource = batch.get("resource", {})
            service_name = self._get_service_name(resource)
            services.add(service_name)

            for span_data in batch.get("scopeSpans", []):
                for span in span_data.get("spans", []):
                    trace_span = self._parse_span(span, service_name, trace_id)
                    spans.append(trace_span)
                    if trace_span.status == "error":
                        error_count += 1

        # Calculate trace timing
        if spans:
            start_times = [s.start_time for s in spans]
            end_times = [
                s.start_time.timestamp() + s.duration_ms / 1000 for s in spans
            ]
            start_time = min(start_times)
            end_time = datetime.fromtimestamp(max(end_times), tz=UTC)
            duration_ms = (end_time - start_time).total_seconds() * 1000
        else:
            start_time = datetime.now(UTC)
            end_time = start_time
            duration_ms = 0

        # Find root service (span with no parent)
        root_service = None
        for span in spans:
            if not span.parent_span_id:
                root_service = span.service_name
                break

        return Trace(
            trace_id=trace_id,
            spans=spans,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            service_count=len(services),
            error_count=error_count,
            root_service=root_service,
        )

    def _parse_span(
        self, span_data: dict[str, Any], service_name: str, trace_id: str
    ) -> TraceSpan:
        """Parse span data from Tempo API response."""
        span_id = span_data.get("spanID", "")
        parent_span_id = span_data.get("parentSpanID")
        operation_name = span_data.get("name", "")
        
        # Parse timestamps (Tempo uses nanoseconds)
        start_time_ns = int(span_data.get("startTimeUnixNano", 0))
        end_time_ns = int(span_data.get("endTimeUnixNano", 0))
        
        start_time = datetime.fromtimestamp(start_time_ns / 1e9, tz=UTC)
        duration_ms = (end_time_ns - start_time_ns) / 1e6  # Convert to milliseconds

        # Parse attributes/tags
        tags = {}
        for attr in span_data.get("attributes", []):
            key = attr.get("key", "")
            value = attr.get("value", {})
            # Extract value from the value object
            if "stringValue" in value:
                tags[key] = value["stringValue"]
            elif "intValue" in value:
                tags[key] = value["intValue"]
            elif "boolValue" in value:
                tags[key] = value["boolValue"]

        # Parse events/logs
        logs = []
        for event in span_data.get("events", []):
            log_entry = {
                "timestamp": datetime.fromtimestamp(
                    int(event.get("timeUnixNano", 0)) / 1e9, tz=UTC
                ),
                "name": event.get("name", ""),
                "attributes": event.get("attributes", []),
            }
            logs.append(log_entry)

        # Determine status
        status_data = span_data.get("status", {})
        status_code = status_data.get("code", 0)
        status = "error" if status_code == 2 else "ok"  # 2 = ERROR in OpenTelemetry

        return TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id if parent_span_id else None,
            operation_name=operation_name,
            service_name=service_name,
            start_time=start_time,
            duration_ms=duration_ms,
            tags=tags,
            logs=logs,
            status=status,
        )

    def _get_service_name(self, resource: dict[str, Any]) -> str:
        """Extract service name from resource attributes."""
        for attr in resource.get("attributes", []):
            if attr.get("key") == "service.name":
                value = attr.get("value", {})
                return value.get("stringValue", "unknown")
        return "unknown"
