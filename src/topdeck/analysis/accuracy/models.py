"""
Data models for accuracy tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class PredictionOutcome(str, Enum):
    """Outcome of a prediction."""

    TRUE_POSITIVE = "true_positive"  # Predicted failure, actually failed
    TRUE_NEGATIVE = "true_negative"  # Predicted no failure, didn't fail
    FALSE_POSITIVE = "false_positive"  # Predicted failure, didn't fail
    FALSE_NEGATIVE = "false_negative"  # Predicted no failure, but failed
    PENDING = "pending"  # Waiting to validate


class ValidationStatus(str, Enum):
    """Status of validation."""

    VALIDATED = "validated"
    PENDING = "pending"
    EXPIRED = "expired"


@dataclass
class AccuracyMetrics:
    """
    Accuracy metrics for predictions or dependency detection.
    
    Attributes:
        precision: TP / (TP + FP) - How many positive predictions were correct
        recall: TP / (TP + FN) - How many actual positives were found
        f1_score: 2 * (precision * recall) / (precision + recall) - Harmonic mean
        accuracy: (TP + TN) / (TP + TN + FP + FN) - Overall correctness
        true_positives: Count of true positives
        true_negatives: Count of true negatives
        false_positives: Count of false positives
        false_negatives: Count of false negatives
        total_predictions: Total predictions made
    """

    precision: float
    recall: float
    f1_score: float
    accuracy: float
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    total_predictions: int
    
    @classmethod
    def from_counts(
        cls,
        true_positives: int,
        true_negatives: int,
        false_positives: int,
        false_negatives: int,
    ) -> "AccuracyMetrics":
        """Calculate metrics from counts."""
        total = true_positives + true_negatives + false_positives + false_negatives
        
        if total == 0:
            return cls(
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                accuracy=0.0,
                true_positives=0,
                true_negatives=0,
                false_positives=0,
                false_negatives=0,
                total_predictions=0,
            )
        
        # Calculate precision
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        
        # Calculate recall
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        
        # Calculate F1 score
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        
        # Calculate accuracy
        accuracy = (true_positives + true_negatives) / total
        
        return cls(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            accuracy=accuracy,
            true_positives=true_positives,
            true_negatives=true_negatives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            total_predictions=total,
        )


@dataclass
class PredictionValidation:
    """
    Validation of a prediction against actual outcome.
    
    Attributes:
        prediction_id: Unique ID of the prediction
        resource_id: Resource that was predicted on
        predicted_at: When prediction was made
        predicted_failure_probability: Predicted probability
        predicted_time_to_failure_hours: Predicted time to failure
        actual_outcome: Actual outcome that occurred
        validated_at: When validation was performed
        outcome_type: Classification of outcome (TP, FP, TN, FN)
        notes: Additional notes about validation
    """

    prediction_id: str
    resource_id: str
    predicted_at: datetime
    predicted_failure_probability: float
    predicted_time_to_failure_hours: float | None
    actual_outcome: str  # "failed", "no_failure", "degraded"
    validated_at: datetime
    outcome_type: PredictionOutcome
    notes: str | None = None


@dataclass
class DependencyValidation:
    """
    Validation of a discovered dependency.
    
    Attributes:
        source_id: Source resource
        target_id: Target resource
        detected_confidence: Confidence when detected
        evidence_sources: List of evidence sources
        validation_status: Validation status
        validated_at: When validated
        is_correct: Whether dependency actually exists
        validation_method: How it was validated
        notes: Additional notes
    """

    source_id: str
    target_id: str
    detected_confidence: float
    evidence_sources: list[str]
    validation_status: ValidationStatus
    validated_at: datetime | None
    is_correct: bool | None
    validation_method: str | None = None
    notes: str | None = None


@dataclass
class ValidationResult:
    """
    Result of validation process.
    
    Attributes:
        metrics: Calculated accuracy metrics
        validated_count: Number of items validated
        pending_count: Number still pending
        time_range: Time range of validation
        details: Additional details
    """

    metrics: AccuracyMetrics
    validated_count: int
    pending_count: int
    time_range: dict[str, datetime]
    details: dict[str, Any] | None = None
