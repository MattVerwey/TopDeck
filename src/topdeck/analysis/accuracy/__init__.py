"""
Accuracy tracking and validation for predictions and dependency detection.

This module provides mechanisms to:
1. Track prediction accuracy over time
2. Validate dependency detection against ground truth
3. Calculate accuracy metrics (precision, recall, F1)
4. Provide feedback for model improvement
"""

from .dependency_validator import DependencyValidator
from .prediction_tracker import PredictionTracker
from .models import (
    AccuracyMetrics,
    DependencyValidation,
    PredictionOutcome,
    ValidationResult,
)

__all__ = [
    "DependencyValidator",
    "PredictionTracker",
    "AccuracyMetrics",
    "DependencyValidation",
    "PredictionOutcome",
    "ValidationResult",
]
