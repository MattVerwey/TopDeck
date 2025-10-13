"""
Monitoring API endpoints.

Provides API endpoints for retrieving metrics and logs from observability
platforms (Prometheus, Loki) for resource monitoring and failure detection.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.monitoring.collectors.prometheus import PrometheusCollector, ResourceMetrics
from topdeck.monitoring.collectors.loki import LokiCollector, ErrorAnalysis
from topdeck.common.config import settings


# Pydantic models for API responses
class MetricValueResponse(BaseModel):
    """Response model for metric value."""
    
    timestamp: datetime
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)


class MetricSeriesResponse(BaseModel):
    """Response model for metric series."""
    
    metric_name: str
    labels: Dict[str, str] = Field(default_factory=dict)
    values: List[MetricValueResponse]


class ResourceMetricsResponse(BaseModel):
    """Response model for resource metrics."""
    
    resource_id: str
    resource_type: str
    metrics: Dict[str, MetricSeriesResponse]
    anomalies: List[str]
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
    labels: Dict[str, str] = Field(default_factory=dict)
    level: str


class ErrorAnalysisResponse(BaseModel):
    """Response model for error analysis."""
    
    resource_id: str
    error_count: int
    error_types: Dict[str, int]
    recent_errors: List[LogEntryResponse]
    error_rate: float


class FailurePointResponse(BaseModel):
    """Response model for failure point detection."""
    
    resource_id: str
    error_rate: float
    error_count: int
    error_types: Dict[str, int]
    recent_errors: List[Dict[str, Any]]


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
    try:
        # In production, use configured Prometheus URL
        prometheus_url = settings.prometheus_url
        collector = PrometheusCollector(prometheus_url)
        
        try:
            metrics = await collector.get_resource_metrics(
                resource_id=resource_id,
                resource_type=resource_type,
                duration=timedelta(hours=duration_hours)
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
                        ]
                    )
                    for name, series in metrics.metrics.items()
                },
                anomalies=metrics.anomalies,
                health_score=metrics.health_score,
            )
        finally:
            await collector.close()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/flows/{flow_id}/bottlenecks", response_model=List[BottleneckResponse])
async def detect_flow_bottlenecks(
    flow_id: str,
    flow_path: List[str] = Query(..., description="List of resource IDs in the flow path"),
) -> List[BottleneckResponse]:
    """
    Detect bottlenecks in a data flow.
    
    Analyzes metrics across all resources in a flow to identify performance
    bottlenecks like high latency, error rates, or resource saturation.
    """
    try:
        prometheus_url = "http://prometheus:9090"
        collector = PrometheusCollector(prometheus_url)
        
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
            status_code=500,
            detail=f"Failed to detect bottlenecks: {str(e)}"
        )


@router.get("/resources/{resource_id}/errors", response_model=ErrorAnalysisResponse)
async def get_resource_errors(
    resource_id: str,
    duration_hours: int = Query(1, ge=1, le=24, description="Duration in hours to analyze"),
) -> ErrorAnalysisResponse:
    """
    Get error analysis for a specific resource from Loki logs.
    
    Returns error statistics, types, and recent error messages.
    """
    try:
        loki_url = "http://loki:3100"
        collector = LokiCollector(loki_url)
        
        try:
            analysis = await collector.analyze_errors(
                resource_id=resource_id,
                duration=timedelta(hours=duration_hours)
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze errors: {str(e)}"
        )


@router.get("/flows/{flow_id}/failures", response_model=Optional[FailurePointResponse])
async def find_flow_failure_point(
    flow_id: str,
    flow_path: List[str] = Query(..., description="List of resource IDs in the flow path"),
    duration_minutes: int = Query(30, ge=5, le=120, description="Duration in minutes to analyze"),
) -> Optional[FailurePointResponse]:
    """
    Find the failure point in a data flow.
    
    Analyzes errors across all resources in a flow to identify where
    failures are occurring, helping to pinpoint issues in microservice
    architectures.
    """
    try:
        loki_url = "http://loki:3100"
        collector = LokiCollector(loki_url)
        
        try:
            failure = await collector.find_failure_point(
                flow_path=flow_path,
                duration=timedelta(minutes=duration_minutes)
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
            status_code=500,
            detail=f"Failed to find failure point: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_monitoring_health() -> Dict[str, Any]:
    """
    Get health status of monitoring integrations.
    
    Returns connection status for Prometheus and Loki.
    """
    health = {
        "prometheus": {"status": "unknown", "url": None},
        "loki": {"status": "unknown", "url": None},
    }
    
    # Check Prometheus
    try:
        prometheus_url = "http://prometheus:9090"
        collector = PrometheusCollector(prometheus_url)
        try:
            # Try a simple query to check connectivity
            await collector.query("up")
            health["prometheus"] = {"status": "healthy", "url": prometheus_url}
        except Exception:
            health["prometheus"] = {"status": "unhealthy", "url": prometheus_url}
        finally:
            await collector.close()
    except Exception:
        pass
    
    # Check Loki
    try:
        loki_url = "http://loki:3100"
        collector = LokiCollector(loki_url)
        try:
            # Try a simple query to check connectivity
            await collector.query('{job="test"}', limit=1)
            health["loki"] = {"status": "healthy", "url": loki_url}
        except Exception:
            health["loki"] = {"status": "unhealthy", "url": loki_url}
        finally:
            await collector.close()
    except Exception:
        pass
    
    return health
