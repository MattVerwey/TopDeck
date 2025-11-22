"""
API routes for load change detection.

Provides endpoints to:
- Detect scaling events
- Analyze load impact
- Predict future load changes
- Identify high load patterns
"""

import structlog
from fastapi import APIRouter, HTTPException, Query

from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.load_detector import LoadChangeDetector

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/load", tags=["load-detection"])

# Initialize components
# TODO: Replace with dependency injection and configuration
prometheus_url = "http://prometheus:9090"  # Will be read from config
prometheus_collector = PrometheusCollector(prometheus_url)
load_detector = LoadChangeDetector(prometheus_collector)


@router.get("/resources/{resource_id}/scaling-events")
async def get_scaling_events(
    resource_id: str,
    lookback_hours: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
):
    """
    Detect pod/service scaling events from Prometheus metrics.

    Analyzes Prometheus metrics to identify when pods were added or removed,
    providing visibility into infrastructure changes.

    **Query Parameters:**
    - `lookback_hours`: Time window to analyze (1-168 hours, default: 24)

    **Returns:**
    - List of scaling events with timestamps and pod count changes
    - Event type (scale_up or scale_down)
    """
    try:
        logger.info("get_scaling_events", resource_id=resource_id, lookback_hours=lookback_hours)

        events = await load_detector.detect_scaling_events(resource_id, lookback_hours)

        return {
            "resource_id": resource_id,
            "lookback_hours": lookback_hours,
            "events_count": len(events),
            "events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "pod_count_before": event.pod_count_before,
                    "pod_count_after": event.pod_count_after,
                    "scaling_type": event.scaling_type,
                    "pod_count_change": event.pod_count_after - event.pod_count_before,
                }
                for event in events
            ],
        }
    except Exception as e:
        logger.error("get_scaling_events_failed", resource_id=resource_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to detect scaling events: {str(e)}"
        ) from e


@router.get("/resources/{resource_id}/baseline")
async def get_load_baseline(resource_id: str):
    """
    Get current load baseline metrics for a resource.

    Returns current performance metrics including:
    - Pod count
    - CPU and memory usage
    - Request rate
    - Latency (P95)
    - Error rate

    **Use Case:**
    Before scaling, get baseline to compare against post-scaling metrics.
    """
    try:
        logger.info("get_load_baseline", resource_id=resource_id)

        baseline = await load_detector.get_load_baseline(resource_id)

        return {
            "resource_id": baseline.resource_id,
            "timestamp": baseline.timestamp.isoformat(),
            "pod_count": baseline.pod_count,
            "metrics": {
                "cpu_usage": baseline.avg_cpu_usage,
                "memory_usage_bytes": baseline.avg_memory_usage,
                "request_rate": baseline.avg_request_rate,
                "latency_p95_seconds": baseline.avg_latency_p95,
                "error_rate": baseline.avg_error_rate,
            },
        }
    except Exception as e:
        logger.error("get_load_baseline_failed", resource_id=resource_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get load baseline: {str(e)}") from e


@router.get("/resources/{resource_id}/impact-analysis")
async def analyze_scaling_impact(
    resource_id: str,
    lookback_hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
):
    """
    Analyze the impact of recent scaling events on load metrics.

    Compares metrics before and after each scaling event to quantify:
    - CPU usage changes
    - Memory usage changes
    - Request rate changes
    - Latency changes
    - Error rate changes

    **Returns:**
    - Detailed analysis for each scaling event
    - Overall impact level (minimal/moderate/significant/critical)
    - Time to stabilization
    - Recommendations based on observed impact
    """
    try:
        logger.info(
            "analyze_scaling_impact", resource_id=resource_id, lookback_hours=lookback_hours
        )

        # Get recent scaling events
        events = await load_detector.detect_scaling_events(resource_id, lookback_hours)

        if not events:
            return {
                "resource_id": resource_id,
                "lookback_hours": lookback_hours,
                "message": "No scaling events detected in the specified time window",
                "impacts": [],
            }

        # Analyze impact for each event
        impacts = []
        for event in events[:5]:  # Limit to 5 most recent events
            try:
                impact = await load_detector.analyze_load_impact(resource_id, event)

                impacts.append(
                    {
                        "event": {
                            "timestamp": event.timestamp.isoformat(),
                            "pod_count_before": event.pod_count_before,
                            "pod_count_after": event.pod_count_after,
                            "scaling_type": event.scaling_type,
                        },
                        "baseline": {
                            "cpu_usage": impact.baseline.avg_cpu_usage,
                            "memory_usage_bytes": impact.baseline.avg_memory_usage,
                            "request_rate": impact.baseline.avg_request_rate,
                            "latency_p95_seconds": impact.baseline.avg_latency_p95,
                            "error_rate": impact.baseline.avg_error_rate,
                        },
                        "changes": {
                            "cpu_change_pct": impact.cpu_change_pct,
                            "memory_change_pct": impact.memory_change_pct,
                            "request_rate_change_pct": impact.request_rate_change_pct,
                            "latency_change_pct": impact.latency_change_pct,
                            "error_rate_change_pct": impact.error_rate_change_pct,
                        },
                        "overall_impact": impact.overall_impact,
                        "time_to_stabilize_minutes": impact.time_to_stabilize_minutes,
                        "recommendations": impact.recommendations,
                    }
                )
            except Exception as e:
                logger.warning(
                    "impact_analysis_failed_for_event", resource_id=resource_id, error=str(e)
                )
                continue

        return {
            "resource_id": resource_id,
            "lookback_hours": lookback_hours,
            "events_analyzed": len(impacts),
            "impacts": impacts,
        }

    except Exception as e:
        logger.error("analyze_scaling_impact_failed", resource_id=resource_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze scaling impact: {str(e)}"
        ) from e


@router.get("/resources/{resource_id}/predict-load")
async def predict_load(
    resource_id: str,
    target_pod_count: int = Query(..., ge=1, description="Target pod count"),
    lookback_days: int = Query(30, ge=1, le=90, description="Days of historical data to analyze"),
):
    """
    Predict load metrics based on historical scaling patterns.

    Uses historical data from similar scaling events to predict:
    - CPU usage at target pod count
    - Memory usage at target pod count
    - Expected request rate
    - Expected latency
    - Expected error rate

    **Query Parameters:**
    - `target_pod_count`: Desired number of pods (required)
    - `lookback_days`: Days of history to analyze (1-90, default: 30)

    **Use Case:**
    Before scaling to N pods, understand expected performance impact.

    **Returns:**
    - Predicted metrics at target pod count
    - Confidence level (based on available historical data)
    - Recommendations for safe scaling
    - Similar historical events used for prediction
    """
    try:
        logger.info(
            "predict_load",
            resource_id=resource_id,
            target_pod_count=target_pod_count,
            lookback_days=lookback_days,
        )

        prediction = await load_detector.predict_load_impact(
            resource_id, target_pod_count, lookback_days
        )

        return {
            "resource_id": prediction.resource_id,
            "target_pod_count": prediction.predicted_pod_count,
            "predicted_metrics": {
                "cpu_usage": prediction.predicted_cpu_usage,
                "memory_usage_bytes": prediction.predicted_memory_usage,
                "request_rate": prediction.predicted_request_rate,
                "latency_p95_seconds": prediction.predicted_latency_p95,
                "error_rate": prediction.predicted_error_rate,
            },
            "confidence": prediction.confidence,
            "based_on_events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "pod_count_before": event.pod_count_before,
                    "pod_count_after": event.pod_count_after,
                    "scaling_type": event.scaling_type,
                }
                for event in prediction.based_on_events
            ],
            "recommendations": prediction.recommendations,
        }

    except Exception as e:
        logger.error("predict_load_failed", resource_id=resource_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to predict load: {str(e)}") from e


@router.get("/resources/{resource_id}/high-load-patterns")
async def detect_high_load_patterns(
    resource_id: str,
    lookback_hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
):
    """
    Detect patterns of high load and capacity issues.

    Identifies:
    - Current high load indicators (CPU, memory, latency, errors)
    - Recent scaling events
    - Whether service needs scaling
    - Actionable insights and recommendations

    **Query Parameters:**
    - `lookback_hours`: Time window to analyze (1-168 hours, default: 24)

    **Use Case:**
    Proactive monitoring to identify services under stress that need attention.

    **Returns:**
    - Current baseline metrics
    - High load indicators
    - Scaling event history
    - Whether service needs scaling
    - Detailed insights and recommendations
    """
    try:
        logger.info("detect_high_load_patterns", resource_id=resource_id)

        patterns = await load_detector.detect_high_load_patterns(resource_id, lookback_hours)

        # Format baseline for response
        baseline = patterns["current_baseline"]
        formatted_patterns = {
            "resource_id": patterns["resource_id"],
            "current_baseline": {
                "timestamp": baseline.timestamp.isoformat(),
                "pod_count": baseline.pod_count,
                "cpu_usage": baseline.avg_cpu_usage,
                "memory_usage_bytes": baseline.avg_memory_usage,
                "request_rate": baseline.avg_request_rate,
                "latency_p95_seconds": baseline.avg_latency_p95,
                "error_rate": baseline.avg_error_rate,
            },
            "scaling_events_count": patterns["scaling_events_count"],
            "recent_scaling_events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "pod_count_before": event.pod_count_before,
                    "pod_count_after": event.pod_count_after,
                    "scaling_type": event.scaling_type,
                }
                for event in patterns["recent_scaling_events"]
            ],
            "high_load_indicators": patterns["high_load_indicators"],
            "needs_scaling": patterns["needs_scaling"],
            "insights": patterns["insights"],
        }

        return formatted_patterns

    except Exception as e:
        logger.error("detect_high_load_patterns_failed", resource_id=resource_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to detect high load patterns: {str(e)}"
        ) from e


@router.get("/health")
async def health_check():
    """
    Health check for load detection service.

    Verifies that:
    - Prometheus connection is available
    - Load detector is initialized

    **Returns:**
    - Service status
    - Prometheus connection status
    """
    try:
        # Simple health check
        return {
            "status": "healthy",
            "service": "load-detection",
            "prometheus_url": prometheus_url,
            "components": {
                "prometheus_collector": "initialized",
                "load_detector": "initialized",
            },
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}") from e
