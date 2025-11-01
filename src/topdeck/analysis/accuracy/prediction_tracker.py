"""
Track prediction accuracy over time and validate against actual outcomes.
"""

from datetime import datetime, timezone, timedelta
from typing import Any
import uuid

import structlog

from topdeck.storage.neo4j_client import Neo4jClient
from .models import (
    AccuracyMetrics,
    PredictionOutcome,
    PredictionValidation,
    ValidationResult,
)

logger = structlog.get_logger(__name__)


class PredictionTracker:
    """
    Tracks prediction accuracy and validates predictions against outcomes.
    
    Stores predictions in Neo4j and validates them when outcomes are known.
    Calculates accuracy metrics over time to improve model confidence.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize prediction tracker.
        
        Args:
            neo4j_client: Neo4j client for storage
        """
        self.neo4j = neo4j_client

    async def record_prediction(
        self,
        resource_id: str,
        failure_probability: float,
        time_to_failure_hours: float | None,
        confidence: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Record a prediction for later validation.
        
        Args:
            resource_id: Resource that was predicted on
            failure_probability: Predicted failure probability
            time_to_failure_hours: Predicted time to failure
            confidence: Confidence level (HIGH, MEDIUM, LOW)
            metadata: Additional metadata
            
        Returns:
            Prediction ID
        """
        prediction_id = str(uuid.uuid4())
        predicted_at = datetime.now(timezone.utc)
        
        # Store prediction in Neo4j
        query = """
        CREATE (p:Prediction {
            id: $prediction_id,
            resource_id: $resource_id,
            failure_probability: $failure_probability,
            time_to_failure_hours: $time_to_failure_hours,
            confidence: $confidence,
            predicted_at: datetime($predicted_at),
            outcome_type: $outcome_type,
            metadata: $metadata
        })
        RETURN p
        """
        
        await self.neo4j.execute_query(
            query,
            {
                "prediction_id": prediction_id,
                "resource_id": resource_id,
                "failure_probability": failure_probability,
                "time_to_failure_hours": time_to_failure_hours,
                "confidence": confidence,
                "predicted_at": predicted_at.isoformat(),
                "outcome_type": PredictionOutcome.PENDING.value,
                "metadata": metadata or {},
            },
        )
        
        logger.info(
            "recorded_prediction",
            prediction_id=prediction_id,
            resource_id=resource_id,
            failure_probability=failure_probability,
        )
        
        return prediction_id

    async def validate_prediction(
        self,
        prediction_id: str,
        actual_outcome: str,
        notes: str | None = None,
    ) -> PredictionValidation:
        """
        Validate a prediction against actual outcome.
        
        Args:
            prediction_id: ID of prediction to validate
            actual_outcome: Actual outcome ("failed", "no_failure", "degraded")
            notes: Additional notes
            
        Returns:
            PredictionValidation result
        """
        validated_at = datetime.now(timezone.utc)
        
        # Get prediction
        query = """
        MATCH (p:Prediction {id: $prediction_id})
        RETURN p
        """
        result = await self.neo4j.execute_query(query, {"prediction_id": prediction_id})
        
        if not result:
            raise ValueError(f"Prediction {prediction_id} not found")
        
        prediction = result[0]["p"]
        
        # Determine outcome type
        failure_probability = prediction["failure_probability"]
        predicted_failure = failure_probability >= 0.5  # Threshold for "predicted failure"
        actual_failure = actual_outcome in ["failed", "degraded"]
        
        if predicted_failure and actual_failure:
            outcome_type = PredictionOutcome.TRUE_POSITIVE
        elif not predicted_failure and not actual_failure:
            outcome_type = PredictionOutcome.TRUE_NEGATIVE
        elif predicted_failure and not actual_failure:
            outcome_type = PredictionOutcome.FALSE_POSITIVE
        else:
            outcome_type = PredictionOutcome.FALSE_NEGATIVE
        
        # Update prediction with outcome
        update_query = """
        MATCH (p:Prediction {id: $prediction_id})
        SET p.actual_outcome = $actual_outcome,
            p.validated_at = datetime($validated_at),
            p.outcome_type = $outcome_type,
            p.validation_notes = $notes
        RETURN p
        """
        
        await self.neo4j.execute_query(
            update_query,
            {
                "prediction_id": prediction_id,
                "actual_outcome": actual_outcome,
                "validated_at": validated_at.isoformat(),
                "outcome_type": outcome_type.value,
                "notes": notes,
            },
        )
        
        logger.info(
            "validated_prediction",
            prediction_id=prediction_id,
            outcome_type=outcome_type.value,
            actual_outcome=actual_outcome,
        )
        
        return PredictionValidation(
            prediction_id=prediction_id,
            resource_id=prediction["resource_id"],
            predicted_at=datetime.fromisoformat(prediction["predicted_at"]),
            predicted_failure_probability=failure_probability,
            predicted_time_to_failure_hours=prediction.get("time_to_failure_hours"),
            actual_outcome=actual_outcome,
            validated_at=validated_at,
            outcome_type=outcome_type,
            notes=notes,
        )

    async def get_accuracy_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        resource_id: str | None = None,
    ) -> ValidationResult:
        """
        Calculate accuracy metrics for predictions in a time range.
        
        Args:
            start_date: Start of time range (default: 30 days ago)
            end_date: End of time range (default: now)
            resource_id: Optional filter by resource
            
        Returns:
            ValidationResult with accuracy metrics
        """
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        # Count outcomes
        query = """
        MATCH (p:Prediction)
        WHERE datetime(p.predicted_at) >= datetime($start_date)
          AND datetime(p.predicted_at) <= datetime($end_date)
          AND ($resource_id IS NULL OR p.resource_id = $resource_id)
        RETURN 
            p.outcome_type as outcome_type,
            count(*) as count
        """
        
        results = await self.neo4j.execute_query(
            query,
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "resource_id": resource_id,
            },
        )
        
        # Count by outcome type
        counts = {
            PredictionOutcome.TRUE_POSITIVE: 0,
            PredictionOutcome.TRUE_NEGATIVE: 0,
            PredictionOutcome.FALSE_POSITIVE: 0,
            PredictionOutcome.FALSE_NEGATIVE: 0,
            PredictionOutcome.PENDING: 0,
        }
        
        for row in results:
            outcome_type = PredictionOutcome(row["outcome_type"])
            counts[outcome_type] = row["count"]
        
        # Calculate metrics (excluding pending)
        validated_count = sum(
            counts[t]
            for t in [
                PredictionOutcome.TRUE_POSITIVE,
                PredictionOutcome.TRUE_NEGATIVE,
                PredictionOutcome.FALSE_POSITIVE,
                PredictionOutcome.FALSE_NEGATIVE,
            ]
        )
        
        metrics = AccuracyMetrics.from_counts(
            true_positives=counts[PredictionOutcome.TRUE_POSITIVE],
            true_negatives=counts[PredictionOutcome.TRUE_NEGATIVE],
            false_positives=counts[PredictionOutcome.FALSE_POSITIVE],
            false_negatives=counts[PredictionOutcome.FALSE_NEGATIVE],
        )
        
        return ValidationResult(
            metrics=metrics,
            validated_count=validated_count,
            pending_count=counts[PredictionOutcome.PENDING],
            time_range={"start": start_date, "end": end_date},
            details={
                "resource_id": resource_id,
                "by_outcome": {
                    outcome.value: counts[outcome] for outcome in PredictionOutcome
                },
            },
        )

    async def get_pending_validations(
        self, max_age_hours: int = 72
    ) -> list[dict[str, Any]]:
        """
        Get predictions pending validation.
        
        Args:
            max_age_hours: Maximum age of predictions to return
            
        Returns:
            List of pending predictions
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        query = """
        MATCH (p:Prediction)
        WHERE p.outcome_type = $pending
          AND datetime(p.predicted_at) >= datetime($cutoff)
        RETURN p
        ORDER BY p.predicted_at DESC
        """
        
        results = await self.neo4j.execute_query(
            query,
            {
                "pending": PredictionOutcome.PENDING.value,
                "cutoff": cutoff.isoformat(),
            },
        )
        
        return [row["p"] for row in results]
