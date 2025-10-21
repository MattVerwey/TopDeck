"""
Data models for ML predictions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level for predictions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredictionConfidence(str, Enum):
    """Confidence level for predictions."""
    LOW = "low"        # <60% confidence
    MEDIUM = "medium"  # 60-80% confidence
    HIGH = "high"      # >80% confidence


@dataclass
class ContributingFactor:
    """A factor contributing to a prediction."""
    factor: str
    importance: float  # 0.0 to 1.0
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    description: str = ""


@dataclass
class FailurePrediction:
    """
    Prediction of resource failure.
    
    Predicts the likelihood and timing of resource failures based on
    historical patterns, current metrics, and resource characteristics.
    """
    resource_id: str
    resource_name: str
    resource_type: str
    
    # Prediction results
    failure_probability: float  # 0.0 to 1.0
    time_to_failure_hours: Optional[float]  # None if no failure predicted
    risk_level: RiskLevel
    confidence: PredictionConfidence
    
    # Contributing factors
    contributing_factors: List[ContributingFactor]
    
    # Recommendations
    recommendations: List[str]
    
    # Metadata
    predicted_at: datetime
    model_version: str
    
    # Similar historical incidents
    similar_incidents: List[Dict[str, any]] = None


@dataclass
class TimeSeriesPoint:
    """A point in a time series prediction."""
    timestamp: datetime
    predicted_value: float
    confidence_lower: float  # Lower bound of confidence interval
    confidence_upper: float  # Upper bound of confidence interval


@dataclass
class PerformancePrediction:
    """
    Prediction of performance degradation.
    
    Predicts future performance metrics (latency, throughput, etc.)
    to identify degradation before it impacts users.
    """
    resource_id: str
    resource_name: str
    metric_name: str  # e.g., "latency_p95", "error_rate"
    
    # Current state
    current_value: float
    baseline_value: float  # Historical baseline
    
    # Predictions
    predictions: List[TimeSeriesPoint]
    degradation_risk: RiskLevel
    confidence: PredictionConfidence
    
    # Analysis
    trend: str  # "increasing", "decreasing", "stable"
    seasonality_detected: bool
    anomalies_detected: int
    
    # Recommendations
    recommendations: List[str]
    
    # Metadata
    predicted_at: datetime
    prediction_horizon_hours: int
    model_version: str


@dataclass
class AnomalyPoint:
    """An anomalous data point."""
    timestamp: datetime
    metric_name: str
    actual_value: float
    expected_value: float
    anomaly_score: float  # 0.0 to 1.0, higher = more anomalous
    deviation_percentage: float


@dataclass
class AnomalyDetection:
    """
    Detection of anomalous behavior.
    
    Identifies unusual patterns in metrics that may indicate
    issues or changes in system behavior.
    """
    resource_id: str
    resource_name: str
    
    # Detected anomalies
    anomalies: List[AnomalyPoint]
    overall_anomaly_score: float  # 0.0 to 1.0
    risk_level: RiskLevel
    
    # Analysis
    affected_metrics: List[str]
    potential_causes: List[str]
    
    # Context
    similar_historical_incidents: List[Dict[str, any]]
    correlated_resources: List[str]  # Other resources showing similar anomalies
    
    # Recommendations
    recommendations: List[str]
    
    # Metadata
    detected_at: datetime
    detection_window_hours: int
    model_version: str


@dataclass
class TrainingMetrics:
    """Metrics for model training."""
    model_name: str
    model_version: str
    trained_at: datetime
    training_duration_seconds: float
    
    # Performance metrics
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mae: Optional[float] = None  # Mean Absolute Error
    rmse: Optional[float] = None  # Root Mean Squared Error
    
    # Training data
    training_samples: int
    features_used: List[str] = None
    
    # Model info
    algorithm: str = ""
    hyperparameters: Dict[str, any] = None


@dataclass
class ModelInfo:
    """Information about a trained model."""
    model_name: str
    model_version: str
    model_type: str  # "failure_prediction", "performance_prediction", "anomaly_detection"
    algorithm: str
    
    created_at: datetime
    last_trained: datetime
    training_metrics: TrainingMetrics
    
    # Model status
    is_active: bool
    performance_degraded: bool  # True if recent predictions are inaccurate
    
    # Storage
    model_path: str
    model_size_mb: float
