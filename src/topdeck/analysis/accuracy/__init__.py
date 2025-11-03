"""
Accuracy tracking and validation for predictions and dependency detection.

This module provides mechanisms to:
1. Track prediction accuracy over time
2. Validate dependency detection against ground truth
3. Calculate accuracy metrics (precision, recall, F1)
4. Provide feedback for model improvement
5. Calibrate models based on accuracy feedback
6. Multi-source dependency verification across infrastructure, code, and monitoring
"""

from .calibration import PredictionCalibrator
from .dependency_validator import DependencyValidator
from .prediction_tracker import PredictionTracker
from .models import (
    AccuracyMetrics,
    DependencyValidation,
    PredictionOutcome,
    ValidationResult,
)
from .multi_source_verifier import (
    DependencyVerificationResult,
    MultiSourceDependencyVerifier,
    VerificationEvidence,
)

__all__ = [
    "DependencyValidator",
    "DependencyVerificationResult",
    "MultiSourceDependencyVerifier",
    "PredictionCalibrator",
    "PredictionTracker",
    "AccuracyMetrics",
    "DependencyValidation",
    "PredictionOutcome",
    "ValidationResult",
    "VerificationEvidence",
]
