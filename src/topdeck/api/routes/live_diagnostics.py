"""
Live Diagnostics API endpoints.

Provides real-time diagnostics data for network topology with ML-based
anomaly detection and service health monitoring.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from topdeck.analysis.prediction.feature_extractor import FeatureExtractor
from topdeck.analysis.prediction.predictor import Predictor
from topdeck.common.config import settings
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.live_diagnostics import (
    LiveDiagnosticsService,
)
from topdeck.storage.neo4j_client import Neo4jClient

if TYPE_CHECKING:
    from topdeck.analysis.baseline import BaselineAnalyzer
    from topdeck.analysis.root_cause import RootCauseAnalyzer

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/live-diagnostics", tags=["live-diagnostics"])


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

        # Initialize Loki collector if configured
        loki_url = settings.get("LOKI_URL")
        loki_collector = None
        if loki_url:
            from topdeck.monitoring.collectors.loki import LokiCollector

            loki_collector = LokiCollector(loki_url)

        _diagnostics_service = LiveDiagnosticsService(prometheus, neo4j, predictor, loki_collector)
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
        ) from e


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

        if health is None:
            raise HTTPException(
                status_code=404,
                detail=f"Service {resource_id} not found or no health data available"
            )

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

    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error("get_service_health_failed", resource_id=resource_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get service health: {str(e)}") from e


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
        raise HTTPException(status_code=500, detail=f"Failed to get anomalies: {str(e)}") from e


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
        raise HTTPException(status_code=500, detail=f"Failed to get traffic patterns: {str(e)}") from e


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
        raise HTTPException(status_code=500, detail=f"Failed to get failing dependencies: {str(e)}") from e


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


@router.get("/services/{resource_id}/error-logs")
async def get_service_error_logs(
    resource_id: str,
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of error logs to return",
    ),
    duration_hours: int = Query(
        default=1,
        ge=1,
        le=24,
        description="Time window for log search in hours",
    ),
) -> dict[str, Any]:
    """
    Get recent error logs for a specific service.

    Returns the most recent error logs to help with diagnostics and troubleshooting.
    This endpoint queries Loki for error-level logs related to the specified resource.

    Args:
        resource_id: Resource identifier
        limit: Maximum number of error logs to return (1-100)
        duration_hours: Time window for log search (1-24 hours)

    Returns:
        Dictionary with error logs and metadata

    Example:
        GET /api/v1/live-diagnostics/services/api-gateway/error-logs?limit=10&duration_hours=1
    """
    try:
        service = get_diagnostics_service()
        error_logs = await service.get_recent_error_logs(
            resource_id=resource_id, limit=limit, duration_hours=duration_hours
        )

        return {
            "resource_id": resource_id,
            "count": len(error_logs),
            "limit": limit,
            "duration_hours": duration_hours,
            "timestamp": datetime.now(UTC).isoformat(),
            "error_logs": error_logs,
        }

    except Exception as e:
        logger.error("get_service_error_logs_failed", resource_id=resource_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get error logs: {str(e)}") from e


# Root Cause Analysis endpoints

class RootCauseAnalysisResponse(BaseModel):
    """Response model for root cause analysis."""

    analysis_id: str
    resource_id: str
    resource_name: str
    failure_time: datetime
    root_cause_type: str
    primary_cause: str
    contributing_factors: list[str]
    confidence: float
    timeline: list[dict[str, Any]]
    correlated_anomalies: list[dict[str, Any]]
    propagation: dict[str, Any] | None
    recommendations: list[str]
    metadata: dict[str, Any]


_rca_analyzer: "RootCauseAnalyzer | None" = None


def get_rca_analyzer():
    """Get or create RCA analyzer instance."""
    global _rca_analyzer

    if _rca_analyzer is None:
        from topdeck.analysis.root_cause import RootCauseAnalyzer

        neo4j = get_neo4j_client()
        prometheus = get_prometheus_collector()
        diagnostics = get_diagnostics_service()

        _rca_analyzer = RootCauseAnalyzer(
            neo4j_client=neo4j,
            prometheus_collector=prometheus,
            diagnostics_service=diagnostics,
        )

    return _rca_analyzer


@router.post("/services/{resource_id}/root-cause-analysis", response_model=RootCauseAnalysisResponse)
async def analyze_root_cause(
    resource_id: str,
    failure_time: datetime | None = Query(
        None,
        description="When the failure occurred (defaults to now)",
    ),
    lookback_hours: int = Query(
        2,
        ge=1,
        le=24,
        description="How far back to analyze (1-24 hours)",
    ),
) -> RootCauseAnalysisResponse:
    """
    Perform root cause analysis for a service failure.

    Analyzes a service failure to identify the root cause through:
    - Timeline reconstruction of events leading to failure
    - Correlation analysis with anomalies
    - Dependency chain analysis
    - Failure propagation detection

    Args:
        resource_id: ID of the failed resource
        failure_time: When the failure occurred (defaults to now)
        lookback_hours: How far back to analyze (1-24 hours)

    Returns:
        Complete root cause analysis with recommendations

    Example:
        POST /api/v1/live-diagnostics/services/web-app-001/root-cause-analysis?lookback_hours=2
    """
    try:
        analyzer = get_rca_analyzer()

        # Perform RCA
        analysis = await analyzer.analyze_failure(
            resource_id=resource_id,
            failure_time=failure_time,
            lookback_hours=lookback_hours,
        )

        # Convert to response format
        timeline_data = [
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "resource_id": event.resource_id,
                "resource_name": event.resource_name,
                "description": event.description,
                "severity": event.severity,
                "metadata": event.metadata,
            }
            for event in analysis.timeline
        ]

        anomalies_data = [
            {
                "resource_id": anomaly.resource_id,
                "resource_name": anomaly.resource_name,
                "metric_name": anomaly.metric_name,
                "deviation": anomaly.deviation,
                "severity": anomaly.severity,
                "timestamp": anomaly.timestamp.isoformat(),
                "correlation_score": anomaly.correlation_score,
            }
            for anomaly in analysis.correlated_anomalies
        ]

        propagation_data = None
        if analysis.propagation:
            propagation_data = {
                "initial_failure": analysis.propagation.initial_failure,
                "propagation_path": analysis.propagation.propagation_path,
                "propagation_delay": analysis.propagation.propagation_delay,
                "affected_services": analysis.propagation.affected_services,
                "metadata": analysis.propagation.metadata,
            }

        return RootCauseAnalysisResponse(
            analysis_id=analysis.analysis_id,
            resource_id=analysis.resource_id,
            resource_name=analysis.resource_name,
            failure_time=analysis.failure_time,
            root_cause_type=analysis.root_cause_type.value,
            primary_cause=analysis.primary_cause,
            contributing_factors=analysis.contributing_factors,
            confidence=analysis.confidence,
            timeline=timeline_data,
            correlated_anomalies=anomalies_data,
            propagation=propagation_data,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
        )

    except Exception as e:
        logger.error("root_cause_analysis_failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform root cause analysis: {str(e)}",
        ) from e


# Historical Comparison endpoints

class BaselineMetricResponse(BaseModel):
    """Response model for baseline metric."""

    metric_name: str
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_95: float
    percentile_99: float
    sample_count: int
    calculation_period: str
    calculated_at: datetime


class BaselineResponse(BaseModel):
    """Response model for baseline."""

    resource_id: str
    resource_name: str
    metrics: dict[str, dict[str, Any]]
    calculated_at: datetime
    valid_until: datetime
    metadata: dict[str, Any]


class MetricComparisonResponse(BaseModel):
    """Response model for metric comparison."""

    metric_name: str
    current_value: float
    historical_value: float
    percent_change: float
    absolute_change: float
    is_anomalous: bool
    deviation_from_baseline: float
    trend: str


class HistoricalComparisonResponse(BaseModel):
    """Response model for historical comparison."""

    resource_id: str
    resource_name: str
    comparison_period: str
    current_time: datetime
    historical_time: datetime
    metrics: list[MetricComparisonResponse]
    overall_trend: str
    anomaly_count: int
    metadata: dict[str, Any]


_baseline_analyzer: "BaselineAnalyzer | None" = None


def get_baseline_analyzer():
    """Get or create baseline analyzer instance."""
    global _baseline_analyzer

    if _baseline_analyzer is None:
        from topdeck.analysis.baseline import BaselineAnalyzer

        prometheus = get_prometheus_collector()
        neo4j = get_neo4j_client()

        _baseline_analyzer = BaselineAnalyzer(
            prometheus_collector=prometheus,
            neo4j_client=neo4j,
            baseline_period_days=7,
            anomaly_threshold_stdev=2.0,
        )

    return _baseline_analyzer


@router.get("/services/{resource_id}/baseline", response_model=BaselineResponse)
async def get_service_baseline(
    resource_id: str,
    force_recalculate: bool = Query(
        False,
        description="Force recalculation even if cached",
    ),
) -> BaselineResponse:
    """
    Get baseline for a service.

    Calculates baseline metrics for normal service behavior based on
    historical data (default 7 days).

    Args:
        resource_id: ID of the resource
        force_recalculate: Force recalculation even if cached

    Returns:
        Baseline metrics with statistics

    Example:
        GET /api/v1/live-diagnostics/services/web-app-001/baseline
    """
    try:
        analyzer = get_baseline_analyzer()

        baseline = await analyzer.calculate_baseline(
            resource_id=resource_id,
            force_recalculate=force_recalculate,
        )

        # Convert metrics to response format
        metrics_data = {}
        for metric_name, metric in baseline.metrics.items():
            metrics_data[metric_name] = {
                "mean": metric.mean,
                "median": metric.median,
                "std_dev": metric.std_dev,
                "min_value": metric.min_value,
                "max_value": metric.max_value,
                "percentile_95": metric.percentile_95,
                "percentile_99": metric.percentile_99,
                "sample_count": metric.sample_count,
                "calculation_period": metric.calculation_period,
                "calculated_at": metric.calculated_at.isoformat(),
            }

        return BaselineResponse(
            resource_id=baseline.resource_id,
            resource_name=baseline.resource_name,
            metrics=metrics_data,
            calculated_at=baseline.calculated_at,
            valid_until=baseline.valid_until,
            metadata=baseline.metadata,
        )

    except Exception as e:
        logger.error("get_baseline_failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate baseline: {str(e)}",
        ) from e


@router.get("/services/{resource_id}/historical-comparison", response_model=HistoricalComparisonResponse)
async def compare_with_historical(
    resource_id: str,
    comparison_period: str = Query(
        "previous_hour",
        description="Period to compare with (previous_hour, previous_day, previous_week, same_hour_yesterday, same_day_last_week)",
    ),
) -> HistoricalComparisonResponse:
    """
    Compare current metrics with historical period.

    Compares current service metrics with a historical period to identify
    changes, trends, and anomalies.

    Args:
        resource_id: ID of the resource
        comparison_period: Which historical period to compare with

    Returns:
        Historical comparison with trend analysis

    Example:
        GET /api/v1/live-diagnostics/services/web-app-001/historical-comparison?comparison_period=previous_day
    """
    try:
        from topdeck.analysis.baseline import ComparisonPeriod

        analyzer = get_baseline_analyzer()

        # Convert string to enum
        try:
            period = ComparisonPeriod(comparison_period)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid comparison period: {comparison_period}",
            ) from e

        comparison = await analyzer.compare_with_historical(
            resource_id=resource_id,
            comparison_period=period,
        )

        # Convert to response format
        metrics_data = [
            MetricComparisonResponse(
                metric_name=m.metric_name,
                current_value=m.current_value,
                historical_value=m.historical_value,
                percent_change=m.percent_change,
                absolute_change=m.absolute_change,
                is_anomalous=m.is_anomalous,
                deviation_from_baseline=m.deviation_from_baseline,
                trend=m.trend,
            )
            for m in comparison.metrics
        ]

        return HistoricalComparisonResponse(
            resource_id=comparison.resource_id,
            resource_name=comparison.resource_name,
            comparison_period=comparison.comparison_period.value,
            current_time=comparison.current_time,
            historical_time=comparison.historical_time,
            metrics=metrics_data,
            overall_trend=comparison.overall_trend,
            anomaly_count=comparison.anomaly_count,
            metadata=comparison.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("historical_comparison_failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform historical comparison: {str(e)}",
        ) from e
