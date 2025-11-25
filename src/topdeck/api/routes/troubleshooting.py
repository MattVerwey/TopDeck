"""
Troubleshooting API endpoints.

Provides API endpoints for the troubleshooting features that fill market gaps:
- Log Correlation Engine (Gap 1)
- Error Context Aggregation (Gap 2)
- Dependency Health Dashboard (Gap 5)

These endpoints address critical SRE needs for faster incident resolution.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.common.config import settings
from topdeck.monitoring.collectors.loki import LokiCollector
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.storage.neo4j_client import Neo4jClient
from topdeck.troubleshooting.dependency_health import (
    DependencyHealthMonitor,
)
from topdeck.troubleshooting.error_context import (
    ErrorContextAggregator,
)
from topdeck.troubleshooting.log_correlation import (
    LogCorrelationEngine,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/troubleshooting", tags=["troubleshooting"])


# ============================================================================
# Pydantic Models for API Requests/Responses
# ============================================================================


class CorrelatedLogsResponse(BaseModel):
    """Response model for correlated logs."""

    correlation_id: str
    start_time: str
    end_time: str
    entries: list[dict[str, Any]]
    services_involved: list[str]
    error_count: int
    warning_count: int
    duration_ms: float


class ErrorChainResponse(BaseModel):
    """Response model for error chain."""

    error_id: str
    root_cause_service: str
    root_cause_error: str
    affected_services: list[str]
    propagation_path: list[dict[str, Any]]
    total_duration_ms: float
    confidence_score: float


class TransactionTimelineResponse(BaseModel):
    """Response model for transaction timeline."""

    transaction_id: str
    start_time: str
    end_time: str
    total_duration_ms: float
    events: list[dict[str, Any]]
    services_path: list[str]
    success: bool
    error_message: str | None


class CaptureContextRequest(BaseModel):
    """Request model for capturing error context."""

    resource_id: str = Field(..., description="Resource identifier")
    error_message: str = Field(default="", description="Error message")
    error_type: str = Field(default="unknown", description="Error type")
    severity: str = Field(default="error", description="Severity level")
    error_time: str | None = Field(default=None, description="Error time (ISO format)")
    context_window_minutes: int = Field(default=5, ge=1, le=60)


class ErrorContextResponse(BaseModel):
    """Response model for error context."""

    context_id: str
    error_time: str
    resource_id: str
    resource_name: str
    error_message: str
    error_type: str
    severity: str
    snapshots: dict[str, Any]
    recommendations: list[str]
    created_at: str
    expires_at: str


class DependencyHealthResponse(BaseModel):
    """Response model for dependency health."""

    resource_id: str
    resource_name: str
    overall_health: str
    overall_health_score: float
    dependencies: list[dict[str, Any]]
    critical_issues: list[str]
    recommendations: list[str]
    generated_at: str


class DependencyTimelineResponse(BaseModel):
    """Response model for dependency timeline."""

    dependency_id: str
    dependency_name: str
    time_range_start: str
    time_range_end: str
    data_points: list[dict[str, Any]]
    average_health_score: float
    degraded_periods: list[dict[str, str]]


class DashboardSummaryResponse(BaseModel):
    """Response model for dashboard summary."""

    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    total_dependencies: int
    healthy_dependencies: int
    critical_alerts: list[str]
    top_issues: list[dict[str, Any]]
    generated_at: str


# ============================================================================
# Dependency Injection Helpers
# ============================================================================


def get_log_correlation_engine() -> LogCorrelationEngine:
    """Get the log correlation engine instance."""
    loki_collector = None
    if settings.loki_url:
        loki_collector = LokiCollector(settings.loki_url)

    neo4j_client = None
    if settings.neo4j_uri:
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )

    return LogCorrelationEngine(
        loki_collector=loki_collector,
        neo4j_client=neo4j_client,
    )


def get_error_context_aggregator() -> ErrorContextAggregator:
    """Get the error context aggregator instance."""
    prometheus_collector = None
    if settings.prometheus_url:
        prometheus_collector = PrometheusCollector(settings.prometheus_url)

    loki_collector = None
    if settings.loki_url:
        loki_collector = LokiCollector(settings.loki_url)

    neo4j_client = None
    if settings.neo4j_uri:
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )

    return ErrorContextAggregator(
        prometheus_collector=prometheus_collector,
        loki_collector=loki_collector,
        neo4j_client=neo4j_client,
    )


def get_dependency_health_monitor() -> DependencyHealthMonitor:
    """Get the dependency health monitor instance."""
    prometheus_collector = None
    if settings.prometheus_url:
        prometheus_collector = PrometheusCollector(settings.prometheus_url)

    neo4j_client = None
    if settings.neo4j_uri:
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )

    return DependencyHealthMonitor(
        prometheus_collector=prometheus_collector,
        neo4j_client=neo4j_client,
    )


# ============================================================================
# Log Correlation Endpoints (Gap 1)
# ============================================================================


@router.get(
    "/logs/correlate/{correlation_id}",
    response_model=CorrelatedLogsResponse,
    summary="Correlate logs by correlation ID",
    description="Find all logs related to a transaction across all services using the correlation ID.",
)
async def correlate_logs(
    correlation_id: str,
    time_window_minutes: int = Query(default=30, ge=1, le=1440),
) -> CorrelatedLogsResponse:
    """
    Correlate logs across distributed services using a correlation ID.

    This addresses Gap 1: Log Correlation Across Distributed Systems.
    SREs spend 60% of troubleshooting time correlating logs - this API
    reduces that to seconds.
    """
    try:
        engine = get_log_correlation_engine()
        result = await engine.correlate_by_correlation_id(
            correlation_id=correlation_id,
            time_window_minutes=time_window_minutes,
        )

        return CorrelatedLogsResponse(
            correlation_id=result.correlation_id,
            start_time=result.start_time.isoformat(),
            end_time=result.end_time.isoformat(),
            entries=[e.to_dict() for e in result.entries],
            services_involved=result.services_involved,
            error_count=result.error_count,
            warning_count=result.warning_count,
            duration_ms=(result.end_time - result.start_time).total_seconds() * 1000,
        )
    except Exception as e:
        logger.error("Failed to correlate logs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to correlate logs: {str(e)}")


@router.get(
    "/logs/error-chain/{error_id}",
    response_model=ErrorChainResponse,
    summary="Trace error propagation",
    description="Trace an error through the dependency chain to find the root cause.",
)
async def get_error_chain(
    error_id: str,
    depth: int = Query(default=5, ge=1, le=10),
) -> ErrorChainResponse:
    """
    Trace an error through the dependency chain.

    Shows how an error propagated through services, helping identify
    the root cause and all affected services.
    """
    try:
        engine = get_log_correlation_engine()
        result = await engine.find_error_chain(
            error_id=error_id,
            depth=depth,
        )

        return ErrorChainResponse(
            error_id=result.error_id,
            root_cause_service=result.root_cause_service,
            root_cause_error=result.root_cause_error,
            affected_services=result.affected_services,
            propagation_path=[link.to_dict() for link in result.propagation_path],
            total_duration_ms=result.total_duration_ms,
            confidence_score=result.confidence_score,
        )
    except Exception as e:
        logger.error("Failed to find error chain", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to find error chain: {str(e)}")


@router.get(
    "/logs/transaction-timeline/{transaction_id}",
    response_model=TransactionTimelineResponse,
    summary="Get transaction timeline",
    description="Get a complete timeline of a transaction across services.",
)
async def get_transaction_timeline(
    transaction_id: str,
    time_window_minutes: int = Query(default=30, ge=1, le=1440),
) -> TransactionTimelineResponse:
    """
    Get a complete timeline of a transaction across services.

    Shows the sequence of events as a transaction flows through
    different services, making it easy to identify where issues occurred.
    """
    try:
        engine = get_log_correlation_engine()
        result = await engine.get_transaction_timeline(
            transaction_id=transaction_id,
            time_window_minutes=time_window_minutes,
        )

        return TransactionTimelineResponse(
            transaction_id=result.transaction_id,
            start_time=result.start_time.isoformat(),
            end_time=result.end_time.isoformat(),
            total_duration_ms=result.total_duration_ms,
            events=[e.to_dict() for e in result.events],
            services_path=result.services_path,
            success=result.success,
            error_message=result.error_message,
        )
    except Exception as e:
        logger.error("Failed to get transaction timeline", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@router.get(
    "/logs/find-correlation-ids/{resource_id}",
    response_model=list[str],
    summary="Find correlation IDs for errors",
    description="Find correlation IDs for errors matching a pattern in a resource.",
)
async def find_correlation_ids(
    resource_id: str,
    error_pattern: str = Query(..., description="Regex pattern to match error messages"),
    time_window_minutes: int = Query(default=60, ge=1, le=1440),
    limit: int = Query(default=10, ge=1, le=100),
) -> list[str]:
    """
    Find correlation IDs for errors matching a pattern.

    Useful when you know what type of error you're looking for
    but need to find specific instances to investigate.
    """
    try:
        engine = get_log_correlation_engine()
        return await engine.find_correlation_ids_for_error(
            resource_id=resource_id,
            error_pattern=error_pattern,
            time_window_minutes=time_window_minutes,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to find correlation IDs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to find correlation IDs: {str(e)}")


# ============================================================================
# Error Context Endpoints (Gap 2)
# ============================================================================


@router.post(
    "/context/capture",
    response_model=ErrorContextResponse,
    summary="Capture error context",
    description="Capture complete error context including logs, metrics, traces, and topology.",
)
async def capture_error_context(
    request: CaptureContextRequest,
) -> ErrorContextResponse:
    """
    Capture complete error context for a resource.

    This addresses Gap 2: Error Context Aggregation.
    When an error occurs, this API automatically gathers all relevant
    context (logs, metrics, traces, topology) in one call.
    """
    try:
        aggregator = get_error_context_aggregator()

        error_time = None
        if request.error_time:
            # Handle various ISO format variations safely
            time_str = request.error_time
            if time_str.endswith("Z"):
                time_str = time_str[:-1] + "+00:00"
            error_time = datetime.fromisoformat(time_str)
            # Ensure timezone-aware
            if error_time.tzinfo is None:
                error_time = error_time.replace(tzinfo=UTC)

        result = await aggregator.capture_context(
            resource_id=request.resource_id,
            error_time=error_time,
            error_message=request.error_message,
            error_type=request.error_type,
            severity=request.severity,
            context_window_minutes=request.context_window_minutes,
        )

        response_data = result.to_dict()
        return ErrorContextResponse(**response_data)
    except Exception as e:
        logger.error("Failed to capture error context", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to capture context: {str(e)}")


@router.get(
    "/context/{context_id}",
    response_model=ErrorContextResponse,
    summary="Get error context",
    description="Retrieve a previously captured error context.",
)
async def get_error_context(
    context_id: str,
) -> ErrorContextResponse:
    """
    Retrieve a previously captured error context.

    Error contexts are retained for 72 hours, allowing post-incident
    analysis even after the original data has been rotated.
    """
    try:
        aggregator = get_error_context_aggregator()
        result = await aggregator.get_context(context_id)

        if not result:
            raise HTTPException(status_code=404, detail="Context not found or expired")

        response_data = result.to_dict()
        return ErrorContextResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get error context", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.get(
    "/context/by-resource/{resource_id}",
    response_model=list[ErrorContextResponse],
    summary="Get contexts by resource",
    description="Get recent error contexts for a resource.",
)
async def get_contexts_by_resource(
    resource_id: str,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[ErrorContextResponse]:
    """
    Get recent error contexts for a resource.

    Useful for reviewing the history of errors for a particular service.
    """
    try:
        aggregator = get_error_context_aggregator()
        results = await aggregator.get_contexts_by_resource(
            resource_id=resource_id,
            limit=limit,
        )

        return [ErrorContextResponse(**ctx.to_dict()) for ctx in results]
    except Exception as e:
        logger.error("Failed to get contexts by resource", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get contexts: {str(e)}")


# ============================================================================
# Dependency Health Endpoints (Gap 5)
# ============================================================================


@router.get(
    "/dependencies/{resource_id}/health",
    response_model=DependencyHealthResponse,
    summary="Get dependency health",
    description="Get comprehensive health status of all dependencies for a resource.",
)
async def get_dependency_health(
    resource_id: str,
) -> DependencyHealthResponse:
    """
    Get comprehensive health status of all dependencies.

    This addresses Gap 5: Service Dependency Health Dashboard.
    During incidents, SREs need to quickly see which dependencies are healthy.
    This API provides a complete health view in one call.
    """
    try:
        monitor = get_dependency_health_monitor()
        result = await monitor.get_dependency_health(resource_id)

        response_data = result.to_dict()
        return DependencyHealthResponse(**response_data)
    except Exception as e:
        logger.error("Failed to get dependency health", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get health: {str(e)}")


@router.get(
    "/dependencies/{resource_id}/timeline/{dependency_id}",
    response_model=DependencyTimelineResponse,
    summary="Get dependency timeline",
    description="Get historical health timeline for a specific dependency.",
)
async def get_dependency_timeline(
    resource_id: str,
    dependency_id: str,
    hours: int = Query(default=24, ge=1, le=168),
) -> DependencyTimelineResponse:
    """
    Get historical health timeline for a dependency.

    Shows how the health of a dependency has changed over time,
    helping identify patterns and degradation trends.
    """
    try:
        monitor = get_dependency_health_monitor()
        result = await monitor.get_dependency_timeline(
            resource_id=resource_id,
            dependency_id=dependency_id,
            hours=hours,
        )

        response_data = result.to_dict()
        return DependencyTimelineResponse(**response_data)
    except Exception as e:
        logger.error("Failed to get dependency timeline", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@router.get(
    "/dependencies/dashboard",
    response_model=DashboardSummaryResponse,
    summary="Get dashboard summary",
    description="Get summary for the dependency health dashboard.",
)
async def get_dashboard_summary() -> DashboardSummaryResponse:
    """
    Get summary for the dependency health dashboard.

    Provides a high-level overview of all services and dependencies,
    highlighting critical issues that need attention.
    """
    try:
        monitor = get_dependency_health_monitor()
        result = await monitor.get_dashboard_summary()

        response_data = result.to_dict()
        return DashboardSummaryResponse(**response_data)
    except Exception as e:
        logger.error("Failed to get dashboard summary", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")
