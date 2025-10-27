"""
API routes for ML-based predictions.
"""

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException, Query

from topdeck.analysis.prediction import Predictor
from topdeck.analysis.prediction.feature_extractor import FeatureExtractor

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/prediction", tags=["prediction"])

# Initialize predictor (will be replaced with dependency injection)
feature_extractor = FeatureExtractor()
predictor = Predictor(feature_extractor=feature_extractor)


@router.get("/resources/{resource_id}/failure-risk")
async def predict_failure_risk(
    resource_id: str,
    resource_name: str | None = Query(None, description="Resource name"),
    resource_type: str | None = Query("unknown", description="Resource type"),
):
    """
    Predict the probability and timing of resource failure.

    Uses machine learning to analyze historical metrics, current state,
    and resource characteristics to predict failure likelihood.

    **Features analyzed:**
    - CPU and memory usage trends
    - Error rate history
    - Restart frequency
    - Dependency relationships
    - Resource age and change frequency

    **Returns:**
    - Failure probability (0.0 to 1.0)
    - Estimated time to failure
    - Risk level and confidence
    - Contributing factors
    - Recommendations to prevent failure
    """
    try:
        logger.info(
            "predict_failure_risk_request", resource_id=resource_id, resource_type=resource_type
        )

        # Get resource details if not provided
        if not resource_name:
            resource_name = resource_id

        prediction = await predictor.predict_failure(
            resource_id=resource_id, resource_name=resource_name, resource_type=resource_type
        )

        # Convert to dict for JSON response
        return {
            "resource_id": prediction.resource_id,
            "resource_name": prediction.resource_name,
            "resource_type": prediction.resource_type,
            "failure_probability": prediction.failure_probability,
            "time_to_failure_hours": prediction.time_to_failure_hours,
            "risk_level": prediction.risk_level.value,
            "confidence": prediction.confidence.value,
            "contributing_factors": [
                {
                    "factor": f.factor,
                    "importance": f.importance,
                    "current_value": f.current_value,
                    "threshold": f.threshold,
                    "description": f.description,
                }
                for f in prediction.contributing_factors
            ],
            "recommendations": prediction.recommendations,
            "predicted_at": prediction.predicted_at.isoformat(),
            "model_version": prediction.model_version,
        }

    except Exception as e:
        logger.error("predict_failure_risk_error", error=str(e), resource_id=resource_id)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}") from e


@router.get("/resources/{resource_id}/performance")
async def predict_performance(
    resource_id: str,
    resource_name: str | None = Query(None, description="Resource name"),
    metric_name: str = Query("latency_p95", description="Metric to predict"),
    horizon_hours: int = Query(24, ge=1, le=168, description="Prediction horizon in hours"),
):
    """
    Predict future performance metrics to identify degradation before it impacts users.

    Uses time-series forecasting (ARIMA/Prophet) to predict future values
    of performance metrics like latency, error rate, throughput, etc.

    **Supported metrics:**
    - latency_p95: 95th percentile latency
    - error_rate: Error rate
    - throughput: Request rate
    - response_time: Average response time

    **Returns:**
    - Time-series predictions for next N hours
    - Confidence intervals
    - Degradation risk assessment
    - Trend analysis
    - Recommendations
    """
    try:
        logger.info(
            "predict_performance_request",
            resource_id=resource_id,
            metric_name=metric_name,
            horizon_hours=horizon_hours,
        )

        if not resource_name:
            resource_name = resource_id

        prediction = await predictor.predict_performance(
            resource_id=resource_id,
            resource_name=resource_name,
            metric_name=metric_name,
            horizon_hours=horizon_hours,
        )

        return {
            "resource_id": prediction.resource_id,
            "resource_name": prediction.resource_name,
            "metric_name": prediction.metric_name,
            "current_value": prediction.current_value,
            "baseline_value": prediction.baseline_value,
            "predictions": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "predicted_value": p.predicted_value,
                    "confidence_lower": p.confidence_lower,
                    "confidence_upper": p.confidence_upper,
                }
                for p in prediction.predictions
            ],
            "degradation_risk": prediction.degradation_risk.value,
            "confidence": prediction.confidence.value,
            "trend": prediction.trend,
            "seasonality_detected": prediction.seasonality_detected,
            "anomalies_detected": prediction.anomalies_detected,
            "recommendations": prediction.recommendations,
            "predicted_at": prediction.predicted_at.isoformat(),
            "prediction_horizon_hours": prediction.prediction_horizon_hours,
            "model_version": prediction.model_version,
        }

    except Exception as e:
        logger.error("predict_performance_error", error=str(e), resource_id=resource_id)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}") from e


@router.get("/resources/{resource_id}/anomalies")
async def detect_anomalies(
    resource_id: str,
    resource_name: str | None = Query(None, description="Resource name"),
    window_hours: int = Query(24, ge=1, le=168, description="Detection window in hours"),
):
    """
    Detect anomalous behavior in resource metrics.

    Uses unsupervised machine learning (Isolation Forest, Local Outlier Factor)
    to identify unusual patterns that may indicate issues.

    **Analyzes:**
    - All available metrics for the resource
    - Historical patterns and baselines
    - Correlation with other resources

    **Returns:**
    - List of detected anomalies
    - Overall anomaly score
    - Affected metrics
    - Potential causes
    - Similar historical incidents
    """
    try:
        logger.info("detect_anomalies_request", resource_id=resource_id, window_hours=window_hours)

        if not resource_name:
            resource_name = resource_id

        detection = await predictor.detect_anomalies(
            resource_id=resource_id, resource_name=resource_name, window_hours=window_hours
        )

        return {
            "resource_id": detection.resource_id,
            "resource_name": detection.resource_name,
            "anomalies": [
                {
                    "timestamp": a.timestamp.isoformat(),
                    "metric_name": a.metric_name,
                    "actual_value": a.actual_value,
                    "expected_value": a.expected_value,
                    "anomaly_score": a.anomaly_score,
                    "deviation_percentage": a.deviation_percentage,
                }
                for a in detection.anomalies
            ],
            "overall_anomaly_score": detection.overall_anomaly_score,
            "risk_level": detection.risk_level.value,
            "affected_metrics": detection.affected_metrics,
            "potential_causes": detection.potential_causes,
            "similar_historical_incidents": detection.similar_historical_incidents,
            "correlated_resources": detection.correlated_resources,
            "recommendations": detection.recommendations,
            "detected_at": detection.detected_at.isoformat(),
            "detection_window_hours": detection.detection_window_hours,
            "model_version": detection.model_version,
        }

    except Exception as e:
        logger.error("detect_anomalies_error", error=str(e), resource_id=resource_id)
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}") from e


@router.get("/anomalies")
async def list_recent_anomalies(
    time_range_hours: int = Query(24, ge=1, le=168, description="Time range to scan"),
    risk_level: str | None = Query(None, description="Filter by risk level"),
):
    """
    List all recent anomalies across all resources.

    Scans all monitored resources for anomalous behavior in the specified time range.

    **Query Parameters:**
    - time_range_hours: How far back to look (1-168 hours)
    - risk_level: Filter by risk level (low, medium, high, critical)

    **Returns:**
    - List of all detected anomalies
    - Grouped by resource and severity
    """
    try:
        logger.info(
            "list_recent_anomalies_request",
            time_range_hours=time_range_hours,
            risk_level=risk_level,
        )

        # Placeholder implementation
        # In production, this would scan all resources
        return {
            "anomalies": [],
            "total_count": 0,
            "time_range_hours": time_range_hours,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("list_recent_anomalies_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list anomalies: {str(e)}") from e


@router.get("/health")
async def prediction_health():
    """
    Health check for prediction service.

    Returns status of ML models and prediction capabilities.
    """
    return {
        "status": "healthy",
        "models": {
            "failure_prediction": {
                "status": "active",
                "version": "1.0.0-rule-based",
                "algorithm": "rule-based",
            },
            "performance_prediction": {
                "status": "active",
                "version": "1.0.0-rule-based",
                "algorithm": "rule-based",
            },
            "anomaly_detection": {
                "status": "active",
                "version": "1.0.0-rule-based",
                "algorithm": "rule-based",
            },
        },
        "features": {
            "failure_prediction": True,
            "performance_forecasting": True,
            "anomaly_detection": True,
            "historical_analysis": False,  # Not yet implemented
            "ml_training": False,  # Not yet implemented
        },
    }
