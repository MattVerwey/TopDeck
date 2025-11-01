"""
Monitoring API endpoints.

Provides API endpoints for retrieving metrics and logs from observability
platforms (Prometheus, Loki) for resource monitoring and failure detection.
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.common.config import settings
from topdeck.monitoring.collectors.loki import LokiCollector
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.transaction_flow import TransactionFlowService
from topdeck.storage.neo4j_client import Neo4jClient


# Pydantic models for API responses
class MetricValueResponse(BaseModel):
    """Response model for metric value."""

    timestamp: datetime
    value: float
    labels: dict[str, str] = Field(default_factory=dict)


class MetricSeriesResponse(BaseModel):
    """Response model for metric series."""

    metric_name: str
    labels: dict[str, str] = Field(default_factory=dict)
    values: list[MetricValueResponse]


class ResourceMetricsResponse(BaseModel):
    """Response model for resource metrics."""

    resource_id: str
    resource_type: str
    metrics: dict[str, MetricSeriesResponse]
    anomalies: list[str]
    health_score: float


class BottleneckResponse(BaseModel):
    """Response model for bottleneck detection."""

    resource_id: str
    type: str
    severity: str
    details: str


class LogEntryResponse(BaseModel):
    """Response model for log entry."""

    timestamp: datetime
    message: str
    labels: dict[str, str] = Field(default_factory=dict)
    level: str


class ErrorAnalysisResponse(BaseModel):
    """Response model for error analysis."""

    resource_id: str
    error_count: int
    error_types: dict[str, int]
    recent_errors: list[LogEntryResponse]
    error_rate: float


class FailurePointResponse(BaseModel):
    """Response model for failure point detection."""

    resource_id: str
    error_rate: float
    error_count: int
    error_types: dict[str, int]
    recent_errors: list[dict[str, Any]]


class FlowNodeResponse(BaseModel):
    """Response model for transaction flow node."""

    resource_id: str
    resource_name: str
    resource_type: str
    timestamp: datetime
    duration_ms: float | None = None
    status: str
    log_count: int
    metrics: dict[str, Any] = Field(default_factory=dict)


class FlowEdgeResponse(BaseModel):
    """Response model for transaction flow edge."""

    source_id: str
    target_id: str
    protocol: str | None = None
    duration_ms: float | None = None
    status_code: int | None = None


class TransactionFlowResponse(BaseModel):
    """Response model for transaction flow visualization."""

    transaction_id: str
    start_time: datetime
    end_time: datetime
    total_duration_ms: float
    nodes: list[FlowNodeResponse]
    edges: list[FlowEdgeResponse]
    status: str
    error_count: int
    warning_count: int
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# Create router
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


# Configuration for observability platforms
PROMETHEUS_URL = settings.prometheus_url  # Use configured Prometheus URL
LOKI_URL = settings.loki_url  # Use configured Loki URL


@router.get("/resources/{resource_id}/metrics", response_model=ResourceMetricsResponse)
async def get_resource_metrics(
    resource_id: str,
    resource_type: str = Query(..., description="Type of resource (pod, service, database, etc.)"),
    duration_hours: int = Query(1, ge=1, le=24, description="Duration in hours to query"),
) -> ResourceMetricsResponse:
    """
    Get metrics for a specific resource from Prometheus.

    Returns performance metrics like CPU usage, memory, latency, error rates, etc.
    """
    # Check if Prometheus is configured
    if not settings.prometheus_url:
        raise HTTPException(
            status_code=503,
            detail="Prometheus integration is not configured. Please set PROMETHEUS_URL in your environment.",
        )

    try:
        collector = PrometheusCollector(settings.prometheus_url)

        try:
            metrics = await collector.get_resource_metrics(
                resource_id=resource_id,
                resource_type=resource_type,
                duration=timedelta(hours=duration_hours),
            )

            return ResourceMetricsResponse(
                resource_id=metrics.resource_id,
                resource_type=metrics.resource_type,
                metrics={
                    name: MetricSeriesResponse(
                        metric_name=series.metric_name,
                        labels=series.labels,
                        values=[
                            MetricValueResponse(
                                timestamp=v.timestamp,
                                value=v.value,
                                labels=v.labels,
                            )
                            for v in series.values
                        ],
                    )
                    for name, series in metrics.metrics.items()
                },
                anomalies=metrics.anomalies,
                health_score=metrics.health_score,
            )
        finally:
            await collector.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}") from e


@router.get("/flows/bottlenecks", response_model=list[BottleneckResponse])
async def detect_flow_bottlenecks(
    flow_path: list[str] = Query(..., description="List of resource IDs in the flow path"),
) -> list[BottleneckResponse]:
    """
    Detect bottlenecks in a data flow.

    Analyzes metrics across all resources in a flow to identify performance
    bottlenecks like high latency, error rates, or resource saturation.
    """
    # Check if Prometheus is configured
    if not settings.prometheus_url:
        raise HTTPException(
            status_code=503,
            detail="Prometheus integration is not configured. Please set PROMETHEUS_URL in your environment.",
        )

    try:
        collector = PrometheusCollector(settings.prometheus_url)

        try:
            bottlenecks = await collector.detect_bottlenecks(flow_path)

            return [
                BottleneckResponse(
                    resource_id=b["resource_id"],
                    type=b["type"],
                    severity=b["severity"],
                    details=b["details"],
                )
                for b in bottlenecks
            ]
        finally:
            await collector.close()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to detect bottlenecks: {str(e)}"
        ) from e


@router.get("/resources/{resource_id}/errors", response_model=ErrorAnalysisResponse)
async def get_resource_errors(
    resource_id: str,
    duration_hours: int = Query(1, ge=1, le=24, description="Duration in hours to analyze"),
) -> ErrorAnalysisResponse:
    """
    Get error analysis for a specific resource from Loki logs.

    Returns error statistics, types, and recent error messages.
    """
    # Check if Loki is configured
    if not settings.loki_url:
        raise HTTPException(
            status_code=503,
            detail="Loki integration is not configured. Please set LOKI_URL in your environment.",
        )

    try:
        collector = LokiCollector(settings.loki_url)

        try:
            analysis = await collector.analyze_errors(
                resource_id=resource_id, duration=timedelta(hours=duration_hours)
            )

            return ErrorAnalysisResponse(
                resource_id=analysis.resource_id,
                error_count=analysis.error_count,
                error_types=analysis.error_types,
                recent_errors=[
                    LogEntryResponse(
                        timestamp=e.timestamp,
                        message=e.message,
                        labels=e.labels,
                        level=e.level,
                    )
                    for e in analysis.recent_errors
                ],
                error_rate=analysis.error_rate,
            )
        finally:
            await collector.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze errors: {str(e)}") from e


@router.get("/flows/{flow_id}/failures", response_model=FailurePointResponse | None)
async def find_flow_failure_point(
    flow_id: str,
    flow_path: list[str] = Query(..., description="List of resource IDs in the flow path"),
    duration_minutes: int = Query(30, ge=5, le=120, description="Duration in minutes to analyze"),
) -> FailurePointResponse | None:
    """
    Find the failure point in a data flow.

    Analyzes errors across all resources in a flow to identify where
    failures are occurring, helping to pinpoint issues in microservice
    architectures.
    """
    # Check if Loki is configured
    if not settings.loki_url:
        raise HTTPException(
            status_code=503,
            detail="Loki integration is not configured. Please set LOKI_URL in your environment.",
        )

    try:
        collector = LokiCollector(settings.loki_url)

        try:
            failure = await collector.find_failure_point(
                flow_path=flow_path, duration=timedelta(minutes=duration_minutes)
            )

            if not failure:
                return None

            return FailurePointResponse(
                resource_id=failure["resource_id"],
                error_rate=failure["error_rate"],
                error_count=failure["error_count"],
                error_types=failure["error_types"],
                recent_errors=failure["recent_errors"],
            )
        finally:
            await collector.close()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to find failure point: {str(e)}"
        ) from e


@router.get("/resources/{resource_id}/correlation-ids", response_model=list[str])
async def get_resource_correlation_ids(
    resource_id: str,
    duration_hours: int = Query(1, ge=1, le=24, description="Duration in hours to search"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of correlation IDs"),
) -> list[str]:
    """
    Get correlation/transaction IDs for a specific resource (pod).

    Returns a list of correlation IDs found in the logs for this resource,
    which can be used to trace transaction flows. Works with any configured
    log source (Loki, Azure Log Analytics, or both).
    """
    # Check if at least one log source is configured
    if not settings.loki_url and not getattr(settings, "azure_log_analytics_workspace_id", None):
        raise HTTPException(
            status_code=503,
            detail="No log integration configured. Please configure at least one: LOKI_URL or AZURE_LOG_ANALYTICS_WORKSPACE_ID",
        )

    try:
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
        )
        neo4j_client.connect()

        try:
            service = TransactionFlowService(
                neo4j_client=neo4j_client,
                loki_url=settings.loki_url if settings.loki_url else None,
                prometheus_url=settings.prometheus_url if settings.prometheus_url else None,
                azure_workspace_id=getattr(settings, "azure_log_analytics_workspace_id", None)
                or None,
            )

            correlation_ids = await service.find_correlation_ids_for_pod(
                pod_resource_id=resource_id,
                duration=timedelta(hours=duration_hours),
                limit=limit,
            )

            if not correlation_ids:
                raise HTTPException(
                    status_code=404,
                    detail=f"No correlation IDs found for resource {resource_id} in the specified time range",
                )

            return correlation_ids
        finally:
            neo4j_client.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get correlation IDs: {str(e)}"
        ) from e


@router.get("/flows/trace/{correlation_id}", response_model=TransactionFlowResponse)
async def trace_transaction_flow(
    correlation_id: str,
    duration_hours: int = Query(1, ge=1, le=24, description="Duration in hours to search"),
    source: str = Query(
        "auto",
        regex="^(auto|loki|azure_log_analytics|all)$",
        description="Data source to use for tracing",
    ),
    enrich: bool = Query(True, description="Enrich with topology and metrics data"),
) -> TransactionFlowResponse:
    """
    Trace a transaction through the network using correlation ID.

    Returns complete flow visualization showing how the transaction moved through
    resources, including timing, errors, and log entries. Works with any configured
    log source (Loki, Azure Log Analytics, or both).

    This enables users to:
    - See the path a transaction took through the network
    - Identify performance bottlenecks
    - Trace errors to their source
    - Understand service dependencies in action
    """
    # Check if at least one log source is configured
    loki_configured = bool(settings.loki_url)
    azure_configured = bool(getattr(settings, "azure_log_analytics_workspace_id", None))

    if not loki_configured and not azure_configured:
        raise HTTPException(
            status_code=503,
            detail="No log integration configured. Please configure at least one: LOKI_URL or AZURE_LOG_ANALYTICS_WORKSPACE_ID",
        )

    # Validate source parameter against configured integrations
    if source == "loki" and not loki_configured:
        raise HTTPException(
            status_code=400, detail="Loki source requested but LOKI_URL is not configured"
        )

    if source == "azure_log_analytics" and not azure_configured:
        raise HTTPException(
            status_code=400,
            detail="Azure Log Analytics source requested but AZURE_LOG_ANALYTICS_WORKSPACE_ID is not configured",
        )

    try:
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
        )
        neo4j_client.connect()

        try:
            service = TransactionFlowService(
                neo4j_client=neo4j_client,
                loki_url=settings.loki_url if loki_configured else None,
                prometheus_url=settings.prometheus_url if settings.prometheus_url else None,
                azure_workspace_id=(
                    getattr(settings, "azure_log_analytics_workspace_id", None)
                    if azure_configured
                    else None
                ),
            )

            if enrich:
                flow = await service.get_flow_with_enrichment(
                    correlation_id=correlation_id,
                    duration=timedelta(hours=duration_hours),
                )
            else:
                flow = await service.trace_transaction(
                    correlation_id=correlation_id,
                    duration=timedelta(hours=duration_hours),
                    source=source,
                )

            if not flow:
                raise HTTPException(
                    status_code=404, detail=f"No flow found for correlation ID: {correlation_id}"
                )

            return TransactionFlowResponse(
                transaction_id=flow.transaction_id,
                start_time=flow.start_time,
                end_time=flow.end_time,
                total_duration_ms=flow.total_duration_ms,
                nodes=[
                    FlowNodeResponse(
                        resource_id=node.resource_id,
                        resource_name=node.resource_name,
                        resource_type=node.resource_type,
                        timestamp=node.timestamp,
                        duration_ms=node.duration_ms,
                        status=node.status,
                        log_count=len(node.log_entries),
                        metrics=node.metrics,
                    )
                    for node in flow.nodes
                ],
                edges=[
                    FlowEdgeResponse(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        protocol=edge.protocol,
                        duration_ms=edge.duration_ms,
                        status_code=edge.status_code,
                    )
                    for edge in flow.edges
                ],
                status=flow.status,
                error_count=flow.error_count,
                warning_count=flow.warning_count,
                source=flow.source,
                metadata=flow.metadata,
            )
        finally:
            neo4j_client.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trace transaction: {str(e)}") from e


@router.get("/health", response_model=dict[str, Any])
async def get_monitoring_health() -> dict[str, Any]:
    """
    Get health status of monitoring integrations.

    Returns connection status for configured monitoring services.
    Each integration is checked independently - unconfigured services
    will show as "not_configured".
    """
    health = {
        "prometheus": {"status": "not_configured", "url": None},
        "loki": {"status": "not_configured", "url": None},
        "azure_log_analytics": {"status": "not_configured", "workspace_id": None},
        "elasticsearch": {"status": "not_configured", "url": None},
    }

    # Check Prometheus (only if configured)
    if settings.prometheus_url:
        try:
            collector = PrometheusCollector(settings.prometheus_url)
            try:
                # Try a simple query to check connectivity
                await collector.query("up")
                health["prometheus"] = {"status": "healthy", "url": settings.prometheus_url}
            except Exception:
                health["prometheus"] = {"status": "unhealthy", "url": settings.prometheus_url}
            finally:
                await collector.close()
        except Exception:
            health["prometheus"] = {"status": "error", "url": settings.prometheus_url}

    # Check Loki (only if configured)
    if settings.loki_url:
        try:
            collector = LokiCollector(settings.loki_url)
            try:
                # Try a simple query to check connectivity
                await collector.query('{job="test"}', limit=1)
                health["loki"] = {"status": "healthy", "url": settings.loki_url}
            except Exception:
                health["loki"] = {"status": "unhealthy", "url": settings.loki_url}
            finally:
                await collector.close()
        except Exception:
            health["loki"] = {"status": "error", "url": settings.loki_url}

    # Check Azure Log Analytics (only if configured)
    azure_workspace_id = getattr(settings, "azure_log_analytics_workspace_id", None)
    if azure_workspace_id:
        try:
            from topdeck.monitoring.collectors.azure_log_analytics import AzureLogAnalyticsCollector

            collector = AzureLogAnalyticsCollector(azure_workspace_id)
            try:
                # Try a simple query to check connectivity
                await collector.query("print 'test'", timespan="PT1M")
                health["azure_log_analytics"] = {
                    "status": "healthy",
                    "workspace_id": azure_workspace_id,
                }
            except Exception:
                health["azure_log_analytics"] = {
                    "status": "unhealthy",
                    "workspace_id": azure_workspace_id,
                }
            finally:
                await collector.close()
        except Exception:
            health["azure_log_analytics"] = {"status": "error", "workspace_id": azure_workspace_id}

    # Check Elasticsearch (only if configured)
    elasticsearch_url = getattr(settings, "elasticsearch_url", None)
    if elasticsearch_url:
        try:
            from topdeck.monitoring.collectors.elasticsearch import ElasticsearchCollector

            # Get optional auth settings
            es_username = getattr(settings, "elasticsearch_username", None)
            es_password = getattr(settings, "elasticsearch_password", None)
            es_api_key = getattr(settings, "elasticsearch_api_key", None)
            es_index = getattr(settings, "elasticsearch_index_pattern", "logs-*")

            collector = ElasticsearchCollector(
                url=elasticsearch_url,
                index_pattern=es_index,
                username=es_username,
                password=es_password,
                api_key=es_api_key,
            )
            try:
                # Try a simple search to check connectivity
                await collector.search({"size": 1, "query": {"match_all": {}}})
                health["elasticsearch"] = {"status": "healthy", "url": elasticsearch_url}
            except Exception:
                health["elasticsearch"] = {"status": "unhealthy", "url": elasticsearch_url}
            finally:
                await collector.close()
        except Exception:
            health["elasticsearch"] = {"status": "error", "url": elasticsearch_url}

    return health
