"""
ML-based prediction module for TopDeck.

This module provides machine learning capabilities for predicting:
- Resource failures before they occur
- Performance degradation trends
- Capacity planning requirements
- Anomalous behavior detection

Uses traditional ML/statistical methods (scikit-learn, statsmodels, Prophet)
rather than LLMs for efficient, accurate time-series prediction.
"""

from .models import (
    FailurePrediction,
    PerformancePrediction,
    AnomalyDetection,
    PredictionConfidence,
)
from .predictor import Predictor

__all__ = [
    "FailurePrediction",
    "PerformancePrediction",
    "AnomalyDetection",
    "PredictionConfidence",
    "Predictor",
]
