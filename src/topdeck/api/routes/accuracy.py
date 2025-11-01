"""
API endpoints for accuracy tracking and validation.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.analysis.accuracy import DependencyValidator, PredictionTracker
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


# Dependency injection
def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client instance."""
    # This would be properly injected in production
    # For now, return a configured instance
    from topdeck.storage.neo4j_client import Neo4jClient
    
    return Neo4jClient()


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
        start_date=datetime.now() - datetime.timedelta(days=days),
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


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check for accuracy tracking service.
    
    Returns:
        Status of the accuracy tracking service
    """
    return {"status": "healthy", "service": "accuracy_tracking"}
