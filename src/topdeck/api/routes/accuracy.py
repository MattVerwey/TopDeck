"""
API endpoints for accuracy tracking and validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from topdeck.analysis.accuracy import (
    DependencyValidator,
    PredictionCalibrator,
    PredictionTracker,
)
from topdeck.analysis.accuracy.multi_source_verifier import (
    MultiSourceDependencyVerifier,
)
from topdeck.storage.neo4j_client import Neo4jClient

router = APIRouter(prefix="/api/v1/accuracy", tags=["accuracy"])


# Request/Response models
class PredictionRecordRequest(BaseModel):
    """Request to record a prediction."""

    resource_id: str
    failure_probability: float = Field(ge=0.0, le=1.0)
    time_to_failure_hours: float | None = None
    confidence: str
    metadata: dict[str, Any] | None = None


class PredictionValidationRequest(BaseModel):
    """Request to validate a prediction."""

    actual_outcome: str = Field(
        description="Actual outcome: 'failed', 'no_failure', or 'degraded'"
    )
    notes: str | None = None


class AccuracyMetricsResponse(BaseModel):
    """Response with accuracy metrics."""

    precision: float
    recall: float
    f1_score: float
    accuracy: float
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    total_predictions: int


class ValidationResultResponse(BaseModel):
    """Response with validation results."""

    metrics: AccuracyMetricsResponse
    validated_count: int
    pending_count: int
    time_range: dict[str, str]
    details: dict[str, Any] | None = None


class DependencyValidationResponse(BaseModel):
    """Response with dependency validation."""

    source_id: str
    target_id: str
    detected_confidence: float
    evidence_sources: list[str]
    validation_status: str
    is_correct: bool | None
    validation_method: str | None
    notes: str | None


class VerificationEvidenceResponse(BaseModel):
    """Response for a single verification evidence."""

    source: str
    evidence_type: str
    confidence: float
    details: dict[str, Any]
    verified_at: str


class MultiSourceVerificationResponse(BaseModel):
    """Response with multi-source verification result."""

    source_id: str
    target_id: str
    is_verified: bool
    overall_confidence: float
    verification_score: float
    evidence: list[VerificationEvidenceResponse]
    recommendations: list[str]
    verified_at: str


# Dependency injection
def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client instance."""
    # This would be properly injected in production
    # For now, return a configured instance with default test values
    import os
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    return Neo4jClient(uri, username, password)


def get_prediction_tracker(
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> PredictionTracker:
    """Get prediction tracker instance."""
    return PredictionTracker(neo4j_client)


def get_dependency_validator(
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> DependencyValidator:
    """Get dependency validator instance."""
    return DependencyValidator(neo4j_client)


def get_prediction_calibrator(
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> PredictionCalibrator:
    """Get prediction calibrator instance."""
    return PredictionCalibrator(neo4j_client)


def get_multi_source_verifier(
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> MultiSourceDependencyVerifier:
    """Get multi-source dependency verifier instance."""
    import os
    
    from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer
    from topdeck.monitoring.collectors.prometheus import PrometheusCollector
    from topdeck.monitoring.collectors.tempo import TempoCollector
    
    # Initialize optional collectors based on environment variables
    ado_discoverer = None
    if os.getenv("AZURE_DEVOPS_ORG") and os.getenv("AZURE_DEVOPS_PROJECT"):
        ado_discoverer = AzureDevOpsDiscoverer(
            organization=os.getenv("AZURE_DEVOPS_ORG"),
            project=os.getenv("AZURE_DEVOPS_PROJECT"),
            personal_access_token=os.getenv("AZURE_DEVOPS_PAT"),
        )
    
    prometheus_collector = None
    if os.getenv("PROMETHEUS_URL"):
        prometheus_collector = PrometheusCollector(os.getenv("PROMETHEUS_URL"))
    
    tempo_collector = None
    if os.getenv("TEMPO_URL"):
        tempo_collector = TempoCollector(os.getenv("TEMPO_URL"))
    
    return MultiSourceDependencyVerifier(
        neo4j_client=neo4j_client,
        ado_discoverer=ado_discoverer,
        prometheus_collector=prometheus_collector,
        tempo_collector=tempo_collector,
    )


# Prediction accuracy endpoints
@router.post("/predictions/record")
async def record_prediction(
    request: PredictionRecordRequest,
    tracker: PredictionTracker = Depends(get_prediction_tracker),
) -> dict[str, str]:
    """
    Record a prediction for later validation.
    
    This endpoint should be called whenever a prediction is made, storing it
    for later validation against actual outcomes.
    
    Returns:
        prediction_id: Unique ID for the prediction
    """
    prediction_id = await tracker.record_prediction(
        resource_id=request.resource_id,
        failure_probability=request.failure_probability,
        time_to_failure_hours=request.time_to_failure_hours,
        confidence=request.confidence,
        metadata=request.metadata,
    )
    
    return {"prediction_id": prediction_id, "status": "recorded"}


@router.post("/predictions/{prediction_id}/validate")
async def validate_prediction(
    prediction_id: str,
    request: PredictionValidationRequest,
    tracker: PredictionTracker = Depends(get_prediction_tracker),
) -> dict[str, Any]:
    """
    Validate a prediction against actual outcome.
    
    This endpoint should be called when the actual outcome is known, allowing
    the system to calculate accuracy metrics.
    
    Returns:
        Validation details including outcome type
    """
    validation = await tracker.validate_prediction(
        prediction_id=prediction_id,
        actual_outcome=request.actual_outcome,
        notes=request.notes,
    )
    
    return {
        "prediction_id": validation.prediction_id,
        "resource_id": validation.resource_id,
        "outcome_type": validation.outcome_type.value,
        "actual_outcome": validation.actual_outcome,
        "validated_at": validation.validated_at.isoformat(),
    }


@router.get("/predictions/metrics", response_model=ValidationResultResponse)
async def get_prediction_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    tracker: PredictionTracker = Depends(get_prediction_tracker),
) -> ValidationResultResponse:
    """
    Get prediction accuracy metrics.
    
    Returns metrics like precision, recall, F1 score for predictions made
    in the specified time range.
    
    Query Parameters:
        days: Number of days to analyze (default: 30)
        resource_id: Optional filter by specific resource
    
    Returns:
        Accuracy metrics and validation results
    """
    result = await tracker.get_accuracy_metrics(
        start_date=datetime.now(timezone.utc) - timedelta(days=days),
        resource_id=resource_id,
    )
    
    return ValidationResultResponse(
        metrics=AccuracyMetricsResponse(
            precision=result.metrics.precision,
            recall=result.metrics.recall,
            f1_score=result.metrics.f1_score,
            accuracy=result.metrics.accuracy,
            true_positives=result.metrics.true_positives,
            true_negatives=result.metrics.true_negatives,
            false_positives=result.metrics.false_positives,
            false_negatives=result.metrics.false_negatives,
            total_predictions=result.metrics.total_predictions,
        ),
        validated_count=result.validated_count,
        pending_count=result.pending_count,
        time_range={
            "start": result.time_range["start"].isoformat(),
            "end": result.time_range["end"].isoformat(),
        },
        details=result.details,
    )


@router.get("/predictions/pending")
async def get_pending_predictions(
    max_age_hours: int = Query(
        72, ge=1, le=720, description="Maximum age of predictions"
    ),
    tracker: PredictionTracker = Depends(get_prediction_tracker),
) -> dict[str, Any]:
    """
    Get predictions awaiting validation.
    
    Returns predictions that have been made but not yet validated,
    helping identify which predictions need outcome data.
    
    Query Parameters:
        max_age_hours: Maximum age of predictions to return (default: 72)
    
    Returns:
        List of pending predictions
    """
    pending = await tracker.get_pending_validations(max_age_hours=max_age_hours)
    
    return {
        "pending_count": len(pending),
        "predictions": pending,
    }


# Dependency accuracy endpoints
@router.post("/dependencies/validate")
async def validate_dependency(
    source_id: str = Query(..., description="Source resource ID"),
    target_id: str = Query(..., description="Target resource ID"),
    validator: DependencyValidator = Depends(get_dependency_validator),
) -> DependencyValidationResponse:
    """
    Cross-validate a dependency using multiple evidence sources.
    
    Checks if a dependency has multiple evidence sources and determines
    if it's likely to be correct.
    
    Query Parameters:
        source_id: Source resource ID
        target_id: Target resource ID
    
    Returns:
        Dependency validation result
    """
    validation = await validator.cross_validate_dependency(source_id, target_id)
    
    return DependencyValidationResponse(
        source_id=validation.source_id,
        target_id=validation.target_id,
        detected_confidence=validation.detected_confidence,
        evidence_sources=validation.evidence_sources,
        validation_status=validation.validation_status.value,
        is_correct=validation.is_correct,
        validation_method=validation.validation_method,
        notes=validation.notes,
    )


@router.get("/dependencies/stale")
async def get_stale_dependencies(
    max_age_days: int = Query(
        7, ge=1, le=90, description="Maximum age before considering stale"
    ),
    validator: DependencyValidator = Depends(get_dependency_validator),
) -> dict[str, Any]:
    """
    Get stale dependencies that need revalidation.
    
    Returns dependencies that haven't been confirmed recently and may
    no longer be valid.
    
    Query Parameters:
        max_age_days: Days before considering dependency stale (default: 7)
    
    Returns:
        List of stale dependencies
    """
    stale = await validator.validate_stale_dependencies(max_age_days=max_age_days)
    
    return {
        "stale_count": len(stale),
        "dependencies": [
            {
                "source_id": dep.source_id,
                "target_id": dep.target_id,
                "confidence": dep.detected_confidence,
                "evidence_sources": dep.evidence_sources,
                "notes": dep.notes,
            }
            for dep in stale
        ],
    }


@router.post("/dependencies/decay")
async def apply_confidence_decay(
    decay_rate: float = Query(
        0.1, ge=0.0, le=1.0, description="Rate to decay confidence"
    ),
    days_threshold: int = Query(
        3, ge=1, le=30, description="Days before starting decay"
    ),
    validator: DependencyValidator = Depends(get_dependency_validator),
) -> dict[str, Any]:
    """
    Apply confidence decay to unconfirmed dependencies.
    
    Reduces confidence for dependencies that haven't been recently confirmed,
    reflecting uncertainty about their current state.
    
    Query Parameters:
        decay_rate: Rate to decay confidence (0.0-1.0, default: 0.1)
        days_threshold: Days before starting decay (default: 3)
    
    Returns:
        Number of dependencies updated
    """
    updated_count = await validator.apply_confidence_decay(
        decay_rate=decay_rate, days_threshold=days_threshold
    )
    
    return {
        "updated_count": updated_count,
        "decay_rate": decay_rate,
        "days_threshold": days_threshold,
    }


@router.get("/dependencies/metrics", response_model=ValidationResultResponse)
async def get_dependency_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    validator: DependencyValidator = Depends(get_dependency_validator),
) -> ValidationResultResponse:
    """
    Get dependency detection accuracy metrics.
    
    Returns metrics about dependency detection accuracy, including validated,
    pending, and stale dependencies.
    
    Query Parameters:
        days: Number of days to analyze (default: 30)
    
    Returns:
        Accuracy metrics and validation results
    """
    result = await validator.get_dependency_accuracy_metrics(time_range_days=days)
    
    return ValidationResultResponse(
        metrics=AccuracyMetricsResponse(
            precision=result.metrics.precision,
            recall=result.metrics.recall,
            f1_score=result.metrics.f1_score,
            accuracy=result.metrics.accuracy,
            true_positives=result.metrics.true_positives,
            true_negatives=result.metrics.true_negatives,
            false_positives=result.metrics.false_positives,
            false_negatives=result.metrics.false_negatives,
            total_predictions=result.metrics.total_predictions,
        ),
        validated_count=result.validated_count,
        pending_count=result.pending_count,
        time_range={
            "start": result.time_range["start"].isoformat(),
            "end": result.time_range["end"].isoformat(),
        },
        details=result.details,
    )


@router.get("/calibration/thresholds")
async def calibrate_thresholds(
    target_precision: float = Query(
        0.85, ge=0.5, le=1.0, description="Target precision"
    ),
    days: int = Query(30, ge=7, le=180, description="Days of history to analyze"),
    calibrator: PredictionCalibrator = Depends(get_prediction_calibrator),
) -> dict[str, Any]:
    """
    Calibrate prediction thresholds based on historical accuracy.
    
    Analyzes historical predictions to recommend threshold adjustments
    that will achieve the target precision.
    
    Query Parameters:
        target_precision: Desired precision (default: 0.85)
        days: Days of history to analyze (default: 30)
    
    Returns:
        Recommended threshold adjustments
    """
    result = await calibrator.calibrate_thresholds(
        target_precision=target_precision, time_range_days=days
    )
    return result


@router.get("/calibration/systematic-errors")
async def analyze_systematic_errors(
    days: int = Query(30, ge=7, le=180, description="Days of history to analyze"),
    calibrator: PredictionCalibrator = Depends(get_prediction_calibrator),
) -> dict[str, Any]:
    """
    Analyze systematic errors in predictions.
    
    Identifies patterns in false positives and false negatives to understand
    where the prediction model is failing.
    
    Query Parameters:
        days: Days of history to analyze (default: 30)
    
    Returns:
        Error analysis with recommendations
    """
    result = await calibrator.analyze_systematic_errors(time_range_days=days)
    return result


@router.get("/calibration/confidence")
async def calibrate_confidence(
    days: int = Query(30, ge=7, le=180, description="Days of history to analyze"),
    calibrator: PredictionCalibrator = Depends(get_prediction_calibrator),
) -> dict[str, Any]:
    """
    Check if confidence levels are properly calibrated.
    
    Ensures that high-confidence predictions are more accurate than
    medium or low-confidence predictions.
    
    Query Parameters:
        days: Days of history to analyze (default: 30)
    
    Returns:
        Confidence calibration status and recommendations
    """
    result = await calibrator.calibrate_confidence_levels(time_range_days=days)
    return result


@router.get("/calibration/report")
async def get_improvement_report(
    calibrator: PredictionCalibrator = Depends(get_prediction_calibrator),
) -> dict[str, Any]:
    """
    Generate comprehensive improvement report.
    
    Combines all calibration analyses to provide actionable recommendations
    for improving prediction accuracy.
    
    Returns:
        Complete improvement report with priority actions
    """
    result = await calibrator.generate_improvement_report()
    return result


@router.get("/dependencies/verify", response_model=MultiSourceVerificationResponse)
async def verify_dependency_multi_source(
    source_id: str = Query(..., description="Source resource ID"),
    target_id: str = Query(..., description="Target resource ID"),
    duration_hours: int = Query(
        24, ge=1, le=168, description="Time range for monitoring verification (hours)"
    ),
    verifier: MultiSourceDependencyVerifier = Depends(get_multi_source_verifier),
) -> MultiSourceVerificationResponse:
    """
    Verify a dependency using multiple independent sources.
    
    This endpoint performs comprehensive dependency verification by checking:
    1. Azure infrastructure (IPs, backends, network topology)
    2. Azure DevOps code (deployment configs, secrets, storage)
    3. Prometheus metrics (actual traffic patterns)
    4. Tempo traces (distributed transaction flows)
    
    Multiple verification sources increase confidence and help catch false positives.
    
    Query Parameters:
        source_id: Source resource ID
        target_id: Target resource ID
        duration_hours: Time range for monitoring data verification (default: 24)
    
    Returns:
        Comprehensive verification result with evidence from all sources
    
    Example:
        GET /api/v1/accuracy/dependencies/verify?source_id=app-1&target_id=db-1&duration_hours=48
    """
    result = await verifier.verify_dependency(
        source_id=source_id,
        target_id=target_id,
        duration=timedelta(hours=duration_hours),
    )
    
    return MultiSourceVerificationResponse(
        source_id=result.source_id,
        target_id=result.target_id,
        is_verified=result.is_verified,
        overall_confidence=result.overall_confidence,
        verification_score=result.verification_score,
        evidence=[
            VerificationEvidenceResponse(
                source=ev.source,
                evidence_type=ev.evidence_type,
                confidence=ev.confidence,
                details=ev.details,
                verified_at=ev.verified_at.isoformat(),
            )
            for ev in result.evidence
        ],
        recommendations=result.recommendations,
        verified_at=result.verified_at.isoformat(),
    )


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check for accuracy tracking service.
    
    Returns:
        Status of the accuracy tracking service
    """
    return {"status": "healthy", "service": "accuracy_tracking"}


# Operational Monitoring Endpoints


@router.get("/monitoring/dashboard")
async def get_accuracy_dashboard(
    days: int = Query(7, ge=1, le=90, description="Days of data to display"),
    tracker: PredictionTracker = Depends(get_prediction_tracker),
    validator: DependencyValidator = Depends(get_dependency_validator),
) -> dict[str, Any]:
    """
    Get comprehensive accuracy dashboard data.
    
    Returns metrics, trends, and status information for monitoring accuracy
    across predictions and dependencies.
    
    Query Parameters:
        days: Number of days of data to include (default: 7)
    
    Returns:
        Dashboard data with metrics, trends, and alerts
    """
    # Get prediction metrics
    pred_metrics = await tracker.get_accuracy_metrics(days=days)
    
    # Get dependency metrics  
    dep_metrics = await validator.get_dependency_accuracy_metrics(days=days)
    
    # Get pending validations (use hours relative to days, capped at 7 days)
    max_pending_hours = min(days * 24, 168)  # Max 7 days (168 hours)
    pending = await tracker.get_pending_validations(max_age_hours=max_pending_hours)
    
    # Get stale dependencies (use days parameter directly, capped at 30 days)
    max_stale_days = min(days, 30)
    stale = await validator.validate_stale_dependencies(max_age_days=max_stale_days)
    
    # Extract dependency details for cleaner access
    dep_details = dep_metrics.details if dep_metrics and dep_metrics.details else {}
    dep_validated = dep_details.get("validated_count", dep_metrics.validated_count if dep_metrics else 0)
    dep_stale = dep_details.get("stale_count", 0)
    dep_total = dep_details.get("total_dependencies", 0)
    
    return {
        "prediction_accuracy": {
            "precision": pred_metrics.metrics.precision if pred_metrics else 0.0,
            "recall": pred_metrics.metrics.recall if pred_metrics else 0.0,
            "f1_score": pred_metrics.metrics.f1_score if pred_metrics else 0.0,
            "total_predictions": pred_metrics.count if pred_metrics else 0,
        },
        "dependency_accuracy": {
            "validated_count": dep_validated,
            "stale_count": dep_stale,
            "total_dependencies": dep_total,
        },
        "pending_work": {
            "predictions_to_validate": len(pending),
            "stale_dependencies": len(stale),
        },
        "time_range": {
            "days": days,
            "from": (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(),
            "to": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/monitoring/alerts")
async def get_accuracy_alerts(
    precision_threshold: float = Query(0.85, ge=0.0, le=1.0),
    recall_threshold: float = Query(0.90, ge=0.0, le=1.0),
    f1_threshold: float = Query(0.85, ge=0.0, le=1.0),
    tracker: PredictionTracker = Depends(get_prediction_tracker),
) -> dict[str, Any]:
    """
    Get accuracy alerts based on thresholds.
    
    Checks recent accuracy metrics and returns alerts if any metrics
    fall below their configured thresholds.
    
    Query Parameters:
        precision_threshold: Minimum acceptable precision (default: 0.85)
        recall_threshold: Minimum acceptable recall (default: 0.90)
        f1_threshold: Minimum acceptable F1 score (default: 0.85)
    
    Returns:
        Alert status and details of any threshold violations
    """
    # Get recent metrics (last 7 days)
    metrics_result = await tracker.get_accuracy_metrics(days=7)
    
    if not metrics_result or not metrics_result.metrics:
        return {
            "status": "unknown",
            "alerts": ["No accuracy data available"],
            "metrics": None,
        }
    
    metrics = metrics_result.metrics
    alerts = []
    
    # Check precision
    if metrics.precision < precision_threshold:
        alerts.append({
            "severity": "warning",
            "metric": "precision",
            "current": metrics.precision,
            "threshold": precision_threshold,
            "message": f"Precision ({metrics.precision:.2%}) below threshold ({precision_threshold:.2%})",
        })
    
    # Check recall
    if metrics.recall < recall_threshold:
        alerts.append({
            "severity": "warning",
            "metric": "recall",
            "current": metrics.recall,
            "threshold": recall_threshold,
            "message": f"Recall ({metrics.recall:.2%}) below threshold ({recall_threshold:.2%})",
        })
    
    # Check F1 score
    if metrics.f1_score < f1_threshold:
        alerts.append({
            "severity": "warning",
            "metric": "f1_score",
            "current": metrics.f1_score,
            "threshold": f1_threshold,
            "message": f"F1 Score ({metrics.f1_score:.2%}) below threshold ({f1_threshold:.2%})",
        })
    
    return {
        "status": "alert" if alerts else "ok",
        "alert_count": len(alerts),
        "alerts": alerts,
        "metrics": {
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1_score": metrics.f1_score,
            "accuracy": metrics.accuracy,
        },
        "thresholds": {
            "precision": precision_threshold,
            "recall": recall_threshold,
            "f1_score": f1_threshold,
        },
    }


@router.get("/monitoring/trends")
async def get_accuracy_trends(
    tracker: PredictionTracker = Depends(get_prediction_tracker),
) -> dict[str, Any]:
    """
    Get accuracy trends over time.
    
    Returns accuracy metrics for the most recent week. Currently shows only
    the latest week's data - full historical trends require database schema
    extension for weekly aggregation.
    
    Returns:
        Recent accuracy trend data
    """
    # Note: This is a simplified implementation that returns recent metrics
    # A full implementation would query historical data for each week
    # For now, we return the most recent week's data as a trend indicator
    
    metrics_result = await tracker.get_accuracy_metrics(days=7)
    
    trends = []
    if metrics_result and metrics_result.metrics:
        # Return recent week as a trend data point
        # TODO: Extend to query historical weekly metrics from database
        trends.append({
            "week": 1,
            "start_date": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
            "end_date": datetime.now(timezone.utc).isoformat(),
            "precision": metrics_result.metrics.precision,
            "recall": metrics_result.metrics.recall,
            "f1_score": metrics_result.metrics.f1_score,
            "prediction_count": metrics_result.count,
        })
    
    return {
        "weeks_analyzed": len(trends),
        "trends": trends,
        "note": "Currently showing most recent week only. Full historical trends require database schema extension for weekly aggregation.",
    }


@router.post("/maintenance/run-validation")
async def trigger_validation(
    max_age_hours: int = Query(24, ge=1, le=168, description="Max age of predictions"),
    tracker: PredictionTracker = Depends(get_prediction_tracker),
) -> dict[str, Any]:
    """
    Manually trigger prediction validation.
    
    Validates pending predictions that are older than the specified age.
    This is typically run automatically by the scheduler but can be
    triggered manually if needed.
    
    Query Parameters:
        max_age_hours: Maximum age of predictions to validate (default: 24)
    
    Returns:
        Validation results summary
    """
    # Get pending predictions
    pending = await tracker.get_pending_validations(max_age_hours=max_age_hours)
    
    # Note: Actual validation logic would integrate with monitoring systems
    # to determine the actual outcome. This is a placeholder.
    
    return {
        "status": "queued",
        "predictions_found": len(pending),
        "message": "Validation queued for processing. Integrate with monitoring system to determine actual outcomes.",
        "note": "This endpoint requires integration with monitoring/health check systems to automatically determine outcomes.",
    }


@router.post("/maintenance/run-decay")
async def trigger_decay(
    decay_rate: float = Query(0.1, ge=0.0, le=1.0),
    days_threshold: int = Query(3, ge=1, le=30),
    validator: DependencyValidator = Depends(get_dependency_validator),
) -> dict[str, Any]:
    """
    Manually trigger confidence decay.
    
    Applies confidence decay to dependencies that haven't been recently
    verified. This is typically run automatically by the scheduler.
    
    Query Parameters:
        decay_rate: Rate to decay confidence (default: 0.1)
        days_threshold: Days before starting decay (default: 3)
    
    Returns:
        Decay application results
    """
    updated_count = await validator.apply_confidence_decay(
        decay_rate=decay_rate,
        days_threshold=days_threshold,
    )
    
    return {
        "status": "success",
        "dependencies_updated": updated_count,
        "decay_rate": decay_rate,
        "days_threshold": days_threshold,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
