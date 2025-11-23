"""
Live Diagnostics API endpoints.

Provides real-time diagnostics data for network topology with ML-based
anomaly detection and service health monitoring.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.analysis.prediction.feature_extractor import FeatureExtractor
from topdeck.analysis.prediction.predictor import Predictor
from topdeck.common.config import settings
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.live_diagnostics import (
    AnomalyAlert,
    LiveDiagnosticsService,
    LiveDiagnosticsSnapshot,
    ServiceHealthStatus,
    TrafficPattern,
)
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/live-diagnostics", tags=["live-diagnostics"])


# Pydantic models for API responses
class ServiceHealthResponse(BaseModel):
    """Response model for service health status."""

    resource_id: str
    resource_name: str
    resource_type: str
    status: str
    health_score: float
    anomalies: list[str]
    metrics: dict[str, float]
    last_updated: datetime


class AnomalyAlertResponse(BaseModel):
    """Response model for anomaly alert."""

    alert_id: str
    resource_id: str
    resource_name: str
    severity: str
    metric_name: str
    current_value: float
    expected_value: float
    deviation_percentage: float
    detected_at: datetime
    message: str
    potential_causes: list[str]


class TrafficPatternResponse(BaseModel):
    """Response model for traffic pattern."""

    source_id: str
    target_id: str
    request_rate: float
    error_rate: float
    latency_p95: float
    is_abnormal: bool
    anomaly_score: float
    trend: str


class FailingDependencyResponse(BaseModel):
    """Response model for failing dependency."""

    source_id: str
    source_name: str
    target_id: str
    target_name: str
    status: str
    health_score: float
    anomalies: list[str]
    error_details: dict[str, Any]


class LiveDiagnosticsSnapshotResponse(BaseModel):
    """Response model for complete live diagnostics snapshot."""

    timestamp: datetime
    overall_health: str
    services: list[ServiceHealthResponse]
    anomalies: list[AnomalyAlertResponse]
    traffic_patterns: list[TrafficPatternResponse]
    failing_dependencies: list[FailingDependencyResponse]


# Dependency injection helpers
_prometheus_collector: PrometheusCollector | None = None
_neo4j_client: Neo4jClient | None = None
_diagnostics_service: LiveDiagnosticsService | None = None


def get_prometheus_collector() -> PrometheusCollector:
    """Get Prometheus collector instance."""
    global _prometheus_collector
    if _prometheus_collector is None:
        prometheus_url = settings.get("PROMETHEUS_URL", "http://prometheus:9090")
        _prometheus_collector = PrometheusCollector(prometheus_url)
    return _prometheus_collector


def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client instance."""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient(
            uri=settings.get("NEO4J_URI", "bolt://localhost:7687"),
            username=settings.get("NEO4J_USERNAME", "neo4j"),
            password=settings.get("NEO4J_PASSWORD", "password"),
        )
    return _neo4j_client


def get_diagnostics_service() -> LiveDiagnosticsService:
    """Get live diagnostics service instance."""
    global _diagnostics_service
    if _diagnostics_service is None:
        prometheus = get_prometheus_collector()
        neo4j = get_neo4j_client()
        feature_extractor = FeatureExtractor(prometheus_collector=prometheus)
        predictor = Predictor(feature_extractor=feature_extractor)
        _diagnostics_service = LiveDiagnosticsService(prometheus, neo4j, predictor)
    return _diagnostics_service


@router.get("/snapshot", response_model=LiveDiagnosticsSnapshotResponse)
async def get_live_snapshot(
    duration_hours: int = Query(
        default=1,
        ge=1,
        le=24,
        description="Time window for metrics analysis in hours",
    ),
) -> LiveDiagnosticsSnapshotResponse:
    """
    Get complete live diagnostics snapshot.

    Returns real-time health status, anomalies, traffic patterns,
    and failing dependencies for all services in the topology.

    Args:
        duration_hours: Time window for analysis (1-24 hours)

    Returns:
        Complete diagnostics snapshot

    Example:
        GET /api/v1/live-diagnostics/snapshot?duration_hours=2
    """
    try:
        service = get_diagnostics_service()
        snapshot = await service.get_live_snapshot(duration_hours)

        return LiveDiagnosticsSnapshotResponse(
            timestamp=snapshot.timestamp,
            overall_health=snapshot.overall_health,
            services=[
                ServiceHealthResponse(
                    resource_id=s.resource_id,
                    resource_name=s.resource_name,
                    resource_type=s.resource_type,
                    status=s.status,
                    health_score=s.health_score,
                    anomalies=s.anomalies,
                    metrics=s.metrics,
                    last_updated=s.last_updated,
                )
                for s in snapshot.services
            ],
            anomalies=[
                AnomalyAlertResponse(
                    alert_id=a.alert_id,
                    resource_id=a.resource_id,
                    resource_name=a.resource_name,
                    severity=a.severity,
                    metric_name=a.metric_name,
                    current_value=a.current_value,
                    expected_value=a.expected_value,
                    deviation_percentage=a.deviation_percentage,
                    detected_at=a.detected_at,
                    message=a.message,
                    potential_causes=a.potential_causes,
                )
                for a in snapshot.anomalies
            ],
            traffic_patterns=[
                TrafficPatternResponse(
                    source_id=t.source_id,
                    target_id=t.target_id,
                    request_rate=t.request_rate,
                    error_rate=t.error_rate,
                    latency_p95=t.latency_p95,
                    is_abnormal=t.is_abnormal,
                    anomaly_score=t.anomaly_score,
                    trend=t.trend,
                )
                for t in snapshot.traffic_patterns
            ],
            failing_dependencies=[
                FailingDependencyResponse(**fd) for fd in snapshot.failing_dependencies
            ],
        )

    except Exception as e:
        logger.error("get_live_snapshot_failed", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get live diagnostics snapshot: {str(e)}"
        )


@router.get("/services/{resource_id}/health", response_model=ServiceHealthResponse)
async def get_service_health(
    resource_id: str,
    resource_type: str = Query(default="service", description="Type of resource"),
    duration_hours: int = Query(
        default=1,
        ge=1,
        le=24,
        description="Time window for analysis in hours",
    ),
) -> ServiceHealthResponse:
    """
    Get health status for a specific service.

    Returns detailed health information including status, health score,
    detected anomalies, and key metrics.

    Args:
        resource_id: Resource identifier
        resource_type: Type of resource (service, pod, database, etc.)
        duration_hours: Time window for analysis (1-24 hours)

    Returns:
        Service health status

    Example:
        GET /api/v1/live-diagnostics/services/api-gateway/health?duration_hours=1
    """
    try:
        service = get_diagnostics_service()
        health = await service.get_service_health(resource_id, resource_type, duration_hours)

        return ServiceHealthResponse(
            resource_id=health.resource_id,
            resource_name=health.resource_name,
            resource_type=health.resource_type,
            status=health.status,
            health_score=health.health_score,
            anomalies=health.anomalies,
            metrics=health.metrics,
            last_updated=health.last_updated,
        )

    except Exception as e:
        logger.error("get_service_health_failed", resource_id=resource_id, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get service health: {str(e)}"
        )


@router.get("/anomalies", response_model=list[AnomalyAlertResponse])
async def get_anomalies(
    severity: str | None = Query(
        default=None,
        description="Filter by severity (low, medium, high, critical)",
    ),
    duration_hours: int = Query(
        default=1,
        ge=1,
        le=24,
        description="Time window for detection in hours",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of anomalies to return",
    ),
) -> list[AnomalyAlertResponse]:
    """
    Get detected anomalies across all services.

    Returns list of anomaly alerts sorted by severity and timestamp.

    Args:
        severity: Filter by severity level (optional)
        duration_hours: Time window for detection (1-24 hours)
        limit: Maximum number of results

    Returns:
        List of anomaly alerts

    Example:
        GET /api/v1/live-diagnostics/anomalies?severity=high&duration_hours=2&limit=20
    """
    try:
        service = get_diagnostics_service()

        # Get all resources
        neo4j = get_neo4j_client()
        query = "MATCH (n) WHERE n.id IS NOT NULL RETURN n.id as id LIMIT 1000"
        results = await neo4j.execute_query(query)
        resource_ids = [r["id"] for r in results]

        # Detect anomalies
        anomalies = await service.detect_anomalies(resource_ids, duration_hours)

        # Filter by severity if specified
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity.lower()]

        # Limit results
        anomalies = anomalies[:limit]

        return [
            AnomalyAlertResponse(
                alert_id=a.alert_id,
                resource_id=a.resource_id,
                resource_name=a.resource_name,
                severity=a.severity,
                metric_name=a.metric_name,
                current_value=a.current_value,
                expected_value=a.expected_value,
                deviation_percentage=a.deviation_percentage,
                detected_at=a.detected_at,
                message=a.message,
                potential_causes=a.potential_causes,
            )
            for a in anomalies
        ]

    except Exception as e:
        logger.error("get_anomalies_failed", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get anomalies: {str(e)}")


@router.get("/traffic-patterns", response_model=list[TrafficPatternResponse])
async def get_traffic_patterns(
    duration_hours: int = Query(
        default=1,
        ge=1,
        le=24,
        description="Time window for analysis in hours",
    ),
    abnormal_only: bool = Query(
        default=False,
        description="Return only abnormal traffic patterns",
    ),
) -> list[TrafficPatternResponse]:
    """
    Get traffic patterns between services.

    Analyzes request rates, error rates, and latency between service pairs
    to identify abnormal traffic patterns.

    Args:
        duration_hours: Time window for analysis (1-24 hours)
        abnormal_only: Return only abnormal patterns

    Returns:
        List of traffic patterns

    Example:
        GET /api/v1/live-diagnostics/traffic-patterns?duration_hours=1&abnormal_only=true
    """
    try:
        service = get_diagnostics_service()
        patterns = await service.analyze_traffic_patterns(duration_hours)

        # Filter if requested
        if abnormal_only:
            patterns = [p for p in patterns if p.is_abnormal]

        return [
            TrafficPatternResponse(
                source_id=p.source_id,
                target_id=p.target_id,
                request_rate=p.request_rate,
                error_rate=p.error_rate,
                latency_p95=p.latency_p95,
                is_abnormal=p.is_abnormal,
                anomaly_score=p.anomaly_score,
                trend=p.trend,
            )
            for p in patterns
        ]

    except Exception as e:
        logger.error("get_traffic_patterns_failed", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get traffic patterns: {str(e)}"
        )


@router.get("/failing-dependencies", response_model=list[FailingDependencyResponse])
async def get_failing_dependencies() -> list[FailingDependencyResponse]:
    """
    Get list of failing dependencies.

    Identifies dependencies where the target service is failed or degraded,
    including detailed error information.

    Returns:
        List of failing dependencies with error details

    Example:
        GET /api/v1/live-diagnostics/failing-dependencies
    """
    try:
        service = get_diagnostics_service()
        failing_deps = await service.get_failing_dependencies()

        return [FailingDependencyResponse(**fd) for fd in failing_deps]

    except Exception as e:
        logger.error("get_failing_dependencies_failed", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get failing dependencies: {str(e)}"
        )


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for live diagnostics service.

    Returns:
        Health status with service availability information

    Example:
        GET /api/v1/live-diagnostics/health
    """
    try:
        # Check Prometheus connectivity
        prometheus = get_prometheus_collector()
        prometheus_health = "unknown"
        try:
            # Simple query to check connectivity
            await prometheus.query("up")
            prometheus_health = "healthy"
        except Exception:
            prometheus_health = "unhealthy"

        # Check Neo4j connectivity
        neo4j = get_neo4j_client()
        neo4j_health = "unknown"
        try:
            await neo4j.execute_query("RETURN 1")
            neo4j_health = "healthy"
        except Exception:
            neo4j_health = "unhealthy"

        overall_status = (
            "healthy"
            if prometheus_health == "healthy" and neo4j_health == "healthy"
            else "degraded"
        )

        return {
            "status": overall_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "components": {
                "prometheus": prometheus_health,
                "neo4j": neo4j_health,
            },
        }

    except Exception as e:
        logger.error("health_check_failed", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "error": str(e),
        }
