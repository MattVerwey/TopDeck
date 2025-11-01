"""
Error Replay API endpoints.

Provides API endpoints for capturing, storing, searching, and replaying errors
to help debug and understand root causes of problems.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.common.config import settings
from topdeck.monitoring.error_replay import (
    ErrorReplayResult,
    ErrorReplayService,
    ErrorSearchFilter,
    ErrorSeverity,
    ErrorSnapshot,
    ErrorSource,
)
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/error-replay", tags=["error-replay"])


# Pydantic models for API requests/responses


class CaptureErrorRequest(BaseModel):
    """Request model for capturing an error."""

    message: str
    severity: ErrorSeverity
    source: ErrorSource
    resource_id: str | None = None
    resource_type: str | None = None
    error_type: str | None = None
    stack_trace: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorSnapshotResponse(BaseModel):
    """Response model for error snapshot."""

    error_id: str
    timestamp: datetime
    severity: str
    source: str
    resource_id: str | None
    resource_type: str | None
    message: str
    error_type: str | None
    stack_trace: str | None
    correlation_id: str | None
    trace_id: str | None
    span_id: str | None
    logs: list[dict[str, Any]]
    metrics: dict[str, Any]
    traces: list[dict[str, Any]]
    topology_snapshot: dict[str, Any]
    related_errors: list[str]
    affected_resources: list[str]
    deployment_context: dict[str, Any] | None
    tags: dict[str, str]
    metadata: dict[str, Any]


class ErrorReplayResponse(BaseModel):
    """Response model for error replay."""

    error_id: str
    original_timestamp: datetime
    error_snapshot: ErrorSnapshotResponse
    timeline: list[dict[str, Any]]
    root_cause_analysis: dict[str, Any]
    recommendations: list[str]
    related_changes: list[dict[str, Any]]


class ErrorSearchRequest(BaseModel):
    """Request model for searching errors."""

    start_time: datetime | None = None
    end_time: datetime | None = None
    severity: ErrorSeverity | None = None
    source: ErrorSource | None = None
    resource_id: str | None = None
    resource_type: str | None = None
    error_type: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    limit: int = Field(default=100, ge=1, le=1000)


class ErrorStatisticsResponse(BaseModel):
    """Response model for error statistics."""

    total_errors: int
    severities: list[str]
    sources: list[str]
    resource_types: list[str]
    error_types: list[str]
    time_range: dict[str, str]


# Initialize service (will be done in app startup)
_error_replay_service: ErrorReplayService | None = None


def get_error_replay_service() -> ErrorReplayService:
    """Get or create error replay service instance."""
    global _error_replay_service

    if _error_replay_service is None:
        neo4j_client = Neo4jClient(
            uri=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
        )

        _error_replay_service = ErrorReplayService(
            neo4j_client=neo4j_client,
            prometheus_url=settings.PROMETHEUS_URL,
            loki_url=settings.LOKI_URL,
            tempo_url=settings.TEMPO_URL,
            elasticsearch_url=settings.ELASTICSEARCH_URL,
            azure_workspace_id=settings.AZURE_LOG_ANALYTICS_WORKSPACE_ID,
        )

    return _error_replay_service


def _error_snapshot_to_response(snapshot: ErrorSnapshot) -> ErrorSnapshotResponse:
    """Convert ErrorSnapshot to response model."""
    return ErrorSnapshotResponse(
        error_id=snapshot.error_id,
        timestamp=snapshot.timestamp,
        severity=snapshot.severity.value,
        source=snapshot.source.value,
        resource_id=snapshot.resource_id,
        resource_type=snapshot.resource_type,
        message=snapshot.message,
        error_type=snapshot.error_type,
        stack_trace=snapshot.stack_trace,
        correlation_id=snapshot.correlation_id,
        trace_id=snapshot.trace_id,
        span_id=snapshot.span_id,
        logs=snapshot.logs,
        metrics=snapshot.metrics,
        traces=snapshot.traces,
        topology_snapshot=snapshot.topology_snapshot,
        related_errors=snapshot.related_errors,
        affected_resources=snapshot.affected_resources,
        deployment_context=snapshot.deployment_context,
        tags=snapshot.tags,
        metadata=snapshot.metadata,
    )


@router.post("/capture", response_model=ErrorSnapshotResponse, status_code=201)
async def capture_error(request: CaptureErrorRequest) -> ErrorSnapshotResponse:
    """
    Capture an error with full context.

    This endpoint captures an error and automatically collects:
    - Surrounding logs from Loki/Elasticsearch/Azure Log Analytics
    - Metrics at the time of error from Prometheus
    - Distributed traces from Tempo
    - Topology state at time of error
    - Recent deployments and changes
    - Related errors

    Example:
    ```json
    {
        "message": "Database connection timeout",
        "severity": "high",
        "source": "application",
        "resource_id": "sql-db-prod-001",
        "resource_type": "database",
        "error_type": "connection_timeout",
        "correlation_id": "abc123",
        "tags": {"environment": "production"}
    }
    ```
    """
    try:
        service = get_error_replay_service()

        error_snapshot = await service.capture_error(
            message=request.message,
            severity=request.severity,
            source=request.source,
            resource_id=request.resource_id,
            resource_type=request.resource_type,
            error_type=request.error_type,
            stack_trace=request.stack_trace,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
            span_id=request.span_id,
            tags=request.tags,
            metadata=request.metadata,
        )

        return _error_snapshot_to_response(error_snapshot)

    except Exception as e:
        logger.error(f"Error capturing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/replay/{error_id}", response_model=ErrorReplayResponse)
async def replay_error(error_id: str) -> ErrorReplayResponse:
    """
    Replay an error to understand what happened.

    Returns:
    - Complete error snapshot with context
    - Timeline of events leading to error
    - Root cause analysis
    - Recommendations for fixing
    - Related topology changes

    This is the "DVR for errors" - replay any past error to debug what went wrong.
    """
    try:
        service = get_error_replay_service()
        result = await service.replay_error(error_id)

        return ErrorReplayResponse(
            error_id=result.error_id,
            original_timestamp=result.original_timestamp,
            error_snapshot=_error_snapshot_to_response(result.error_snapshot),
            timeline=result.timeline,
            root_cause_analysis=result.root_cause_analysis,
            recommendations=result.recommendations,
            related_changes=result.related_changes,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error replaying error {error_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=list[ErrorSnapshotResponse])
async def search_errors(request: ErrorSearchRequest) -> list[ErrorSnapshotResponse]:
    """
    Search for errors matching criteria.

    Supports filtering by:
    - Time range
    - Severity level
    - Source platform
    - Resource ID/type
    - Error type
    - Correlation/trace IDs
    - Custom tags

    Example:
    ```json
    {
        "severity": "high",
        "resource_type": "database",
        "start_time": "2024-01-01T00:00:00Z",
        "limit": 50
    }
    ```
    """
    try:
        service = get_error_replay_service()

        filter = ErrorSearchFilter(
            start_time=request.start_time,
            end_time=request.end_time,
            severity=request.severity,
            source=request.source,
            resource_id=request.resource_id,
            resource_type=request.resource_type,
            error_type=request.error_type,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
            tags=request.tags,
            limit=request.limit,
        )

        errors = await service.search_errors(filter)
        return [_error_snapshot_to_response(error) for error in errors]

    except Exception as e:
        logger.error(f"Error searching errors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=ErrorStatisticsResponse)
async def get_error_statistics(
    start_time: datetime = Query(..., description="Start time for statistics"),
    end_time: datetime = Query(..., description="End time for statistics"),
) -> ErrorStatisticsResponse:
    """
    Get error statistics for a time range.

    Returns aggregate statistics including:
    - Total error count
    - Breakdown by severity
    - Breakdown by source platform
    - Breakdown by resource type
    - Breakdown by error type
    """
    try:
        service = get_error_replay_service()
        stats = await service.get_error_statistics(start_time, end_time)

        return ErrorStatisticsResponse(
            total_errors=stats["total_errors"],
            severities=stats["severities"],
            sources=stats["sources"],
            resource_types=stats["resource_types"],
            error_types=stats["error_types"],
            time_range=stats["time_range"],
        )

    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=list[ErrorSnapshotResponse])
async def get_recent_errors(
    limit: int = Query(default=20, ge=1, le=100, description="Number of errors to return"),
    severity: ErrorSeverity | None = Query(default=None, description="Filter by severity"),
) -> list[ErrorSnapshotResponse]:
    """
    Get recent errors.

    Returns the most recent errors, optionally filtered by severity.
    Useful for monitoring dashboards and real-time error tracking.
    """
    try:
        service = get_error_replay_service()

        # Search for recent errors (last 24 hours)
        from datetime import UTC, timedelta

        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=24)

        filter = ErrorSearchFilter(
            start_time=start_time, end_time=end_time, severity=severity, limit=limit
        )

        errors = await service.search_errors(filter)
        return [_error_snapshot_to_response(error) for error in errors]

    except Exception as e:
        logger.error(f"Error getting recent errors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-resource/{resource_id}", response_model=list[ErrorSnapshotResponse])
async def get_errors_by_resource(
    resource_id: str,
    limit: int = Query(default=50, ge=1, le=500, description="Number of errors to return"),
) -> list[ErrorSnapshotResponse]:
    """
    Get errors for a specific resource.

    Returns all errors affecting a resource, useful for:
    - Resource health dashboards
    - Troubleshooting specific resources
    - Understanding resource error patterns
    """
    try:
        service = get_error_replay_service()

        filter = ErrorSearchFilter(resource_id=resource_id, limit=limit)

        errors = await service.search_errors(filter)
        return [_error_snapshot_to_response(error) for error in errors]

    except Exception as e:
        logger.error(f"Error getting errors for resource {resource_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-correlation/{correlation_id}", response_model=list[ErrorSnapshotResponse])
async def get_errors_by_correlation(
    correlation_id: str,
    limit: int = Query(default=50, ge=1, le=500, description="Number of errors to return"),
) -> list[ErrorSnapshotResponse]:
    """
    Get errors for a correlation ID.

    Returns all errors with the same correlation ID, useful for:
    - Tracing errors through distributed systems
    - Understanding cascading failures
    - Debugging multi-service transactions
    """
    try:
        service = get_error_replay_service()

        filter = ErrorSearchFilter(correlation_id=correlation_id, limit=limit)

        errors = await service.search_errors(filter)
        return [_error_snapshot_to_response(error) for error in errors]

    except Exception as e:
        logger.error(
            f"Error getting errors for correlation {correlation_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
