"""
Main prediction orchestrator.

Coordinates feature extraction, model loading, and prediction generation.
"""

from datetime import datetime, timezone

import structlog

from .feature_extractor import FeatureExtractor
from .models import (
    AnomalyDetection,
    ContributingFactor,
    FailurePrediction,
    PerformancePrediction,
    PredictionConfidence,
    RiskLevel,
)

logger = structlog.get_logger(__name__)


class Predictor:
    """
    Main prediction orchestrator.

    Coordinates all prediction types and manages model lifecycle.
    """

    def __init__(
        self, feature_extractor: FeatureExtractor | None = None, model_dir: str = "/data/models"
    ):
        """
        Initialize predictor.

        Args:
            feature_extractor: FeatureExtractor instance
            model_dir: Directory to store/load models
        """
        self.feature_extractor = feature_extractor or FeatureExtractor()
        self.model_dir = model_dir

        # Models will be loaded on demand
        self.failure_model = None
        self.performance_model = None
        self.anomaly_model = None

    async def predict_failure(
        self, resource_id: str, resource_name: str, resource_type: str
    ) -> FailurePrediction:
        """
        Predict probability and timing of resource failure.

        Args:
            resource_id: Resource to analyze
            resource_name: Resource name
            resource_type: Type of resource

        Returns:
            FailurePrediction with analysis
        """
        logger.info("predict_failure", resource_id=resource_id, resource_type=resource_type)

        # Extract features
        features = await self.feature_extractor.extract_failure_features(resource_id, resource_type)

        # For now, use rule-based prediction
        # In production, this would use trained ML model
        failure_probability = self._calculate_failure_probability(features)
        time_to_failure = self._estimate_time_to_failure(features, failure_probability)
        risk_level = self._determine_risk_level(failure_probability)
        confidence, confidence_metrics = self._calculate_confidence_with_metrics(features)

        # Identify contributing factors
        contributing_factors = self._identify_contributing_factors(features)

        # Generate recommendations
        recommendations = self._generate_failure_recommendations(
            features, failure_probability, resource_type
        )

        return FailurePrediction(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
            failure_probability=failure_probability,
            time_to_failure_hours=time_to_failure,
            risk_level=risk_level,
            confidence=confidence,
            contributing_factors=contributing_factors,
            recommendations=recommendations,
            predicted_at=datetime.now(timezone.utc),
            model_version="1.0.0-rule-based",
            similar_incidents=[],
            confidence_metrics=confidence_metrics,
        )

    async def predict_performance(
        self,
        resource_id: str,
        resource_name: str,
        metric_name: str = "latency_p95",
        horizon_hours: int = 24,
    ) -> PerformancePrediction:
        """
        Predict future performance metrics.

        Args:
            resource_id: Resource to analyze
            resource_name: Resource name
            metric_name: Metric to predict
            horizon_hours: How far ahead to predict

        Returns:
            PerformancePrediction with forecast
        """
        logger.info(
            "predict_performance",
            resource_id=resource_id,
            metric_name=metric_name,
            horizon_hours=horizon_hours,
        )

        # Extract time-series features
        await self.feature_extractor.extract_performance_features(resource_id, metric_name)

        # For now, return placeholder
        # In production, this would use Prophet or ARIMA

        from .models import TimeSeriesPoint

        current_value = 250.0
        baseline = 200.0

        # Simple linear trend for demonstration
        predictions = []
        for i in range(horizon_hours):
            timestamp = datetime.now(timezone.utc)
            predicted = current_value + (i * 5.0)  # Increasing trend
            predictions.append(
                TimeSeriesPoint(
                    timestamp=timestamp,
                    predicted_value=predicted,
                    confidence_lower=predicted * 0.9,
                    confidence_upper=predicted * 1.1,
                )
            )

        degradation_risk = RiskLevel.MEDIUM if current_value > baseline * 1.2 else RiskLevel.LOW

        return PerformancePrediction(
            resource_id=resource_id,
            resource_name=resource_name,
            metric_name=metric_name,
            current_value=current_value,
            baseline_value=baseline,
            predictions=predictions,
            degradation_risk=degradation_risk,
            confidence=PredictionConfidence.MEDIUM,
            trend="increasing",
            seasonality_detected=False,
            anomalies_detected=0,
            recommendations=self._generate_performance_recommendations(current_value, baseline),
            predicted_at=datetime.now(timezone.utc),
            prediction_horizon_hours=horizon_hours,
            model_version="1.0.0-rule-based",
        )

    async def detect_anomalies(
        self, resource_id: str, resource_name: str, window_hours: int = 24
    ) -> AnomalyDetection:
        """
        Detect anomalous behavior in resource metrics.

        Args:
            resource_id: Resource to analyze
            resource_name: Resource name
            window_hours: Time window to analyze

        Returns:
            AnomalyDetection with findings
        """
        logger.info("detect_anomalies", resource_id=resource_id, window_hours=window_hours)

        # Extract features
        await self.feature_extractor.extract_anomaly_features(resource_id, window_hours)

        # For now, return placeholder
        # In production, this would use Isolation Forest or similar

        anomalies = []
        overall_score = 0.3  # Low anomaly score for demo

        return AnomalyDetection(
            resource_id=resource_id,
            resource_name=resource_name,
            anomalies=anomalies,
            overall_anomaly_score=overall_score,
            risk_level=RiskLevel.LOW,
            affected_metrics=[],
            potential_causes=[],
            similar_historical_incidents=[],
            correlated_resources=[],
            recommendations=["Continue monitoring", "No immediate action required"],
            detected_at=datetime.now(timezone.utc),
            detection_window_hours=window_hours,
            model_version="1.0.0-rule-based",
        )

    # Helper methods for rule-based predictions (to be replaced by ML models)

    def _calculate_failure_probability(self, features: dict) -> float:
        """Calculate failure probability from features."""
        score = 0.0

        # High CPU usage
        if features.get("cpu_mean", 0) > 0.8:
            score += 0.3

        # Increasing CPU trend
        if features.get("cpu_trend", 0) > 0.1:
            score += 0.2

        # High memory usage
        if features.get("memory_mean", 0) > 0.8:
            score += 0.2

        # Error rate issues
        if features.get("error_rate_mean", 0) > 0.05:
            score += 0.3

        # Recent restarts
        if features.get("restart_count", 0) > 3:
            score += 0.2

        # Single point of failure
        if features.get("is_spof", 0) > 0.5:
            score += 0.1

        return min(1.0, score)

    def _estimate_time_to_failure(self, features: dict, failure_probability: float) -> float | None:
        """Estimate hours until failure."""
        if failure_probability < 0.3:
            return None

        # Simple estimation based on trends
        cpu_trend = features.get("cpu_trend", 0)
        memory_trend = features.get("memory_trend", 0)

        if cpu_trend > 0.1 or memory_trend > 0.1:
            # Extrapolate when resource will hit 100%
            return 48.0  # Placeholder: 48 hours

        return 72.0  # Default: 3 days

    def _determine_risk_level(self, probability: float) -> RiskLevel:
        """Determine risk level from probability."""
        if probability >= 0.8:
            return RiskLevel.CRITICAL
        elif probability >= 0.6:
            return RiskLevel.HIGH
        elif probability >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _calculate_confidence_with_metrics(
        self, features: dict
    ) -> tuple[PredictionConfidence, "ConfidenceMetrics"]:
        """
        Calculate confidence with detailed metrics.

        Returns:
            Tuple of (PredictionConfidence, ConfidenceMetrics)
        """
        from .models import ConfidenceMetrics

        # Factor 1: Feature completeness (0-1 scale)
        feature_count = sum(1 for v in features.values() if v is not None)
        total_possible_features = 30  # Expected number of features
        completeness_score = min(feature_count / total_possible_features, 1.0)

        # Factor 2: Feature quality (0-1 scale)
        quality_score = self._calculate_feature_quality(features)

        # Factor 3: Data recency (0-1 scale)
        recency_score = self._calculate_data_recency(features)

        # Factor 4: Prediction consistency (0-1 scale)
        consistency_score = self._calculate_prediction_consistency(features)

        # Weighted average of all factors
        weights = {
            "completeness": 0.3,
            "quality": 0.3,
            "recency": 0.2,
            "consistency": 0.2,
        }

        confidence_score = (
            completeness_score * weights["completeness"]
            + quality_score * weights["quality"]
            + recency_score * weights["recency"]
            + consistency_score * weights["consistency"]
        )

        # Map to confidence levels
        if confidence_score >= 0.8:
            confidence_level = PredictionConfidence.HIGH
        elif confidence_score >= 0.6:
            confidence_level = PredictionConfidence.MEDIUM
        else:
            confidence_level = PredictionConfidence.LOW

        # Count valid features
        valid_features = sum(
            1
            for k, v in features.items()
            if v is not None and self._is_feature_valid(k, v)
        )
        missing_features = total_possible_features - feature_count

        # Create detailed metrics
        metrics = ConfidenceMetrics(
            overall_score=confidence_score,
            confidence_level=confidence_level,
            feature_completeness=completeness_score,
            feature_quality=quality_score,
            data_recency=recency_score,
            prediction_consistency=consistency_score,
            total_features=feature_count,
            valid_features=valid_features,
            missing_features=missing_features,
        )

        return confidence_level, metrics

    def _calculate_confidence(self, features: dict) -> PredictionConfidence:
        """
        Calculate confidence in prediction (backward compatibility method).

        Returns:
            PredictionConfidence level (LOW, MEDIUM, HIGH)
        """
        confidence, _ = self._calculate_confidence_with_metrics(features)
        return confidence

    def _is_feature_valid(self, key: str, value: float) -> bool:
        """Check if a feature value is valid."""
        if key in ("cpu_mean", "cpu_max", "memory_mean", "memory_max"):
            return 0.0 <= value <= 1.0
        elif key in ("cpu_std", "memory_std"):
            return 0.0 <= value <= 0.5
        elif key in ("error_rate_mean", "error_rate_max"):
            return 0.0 <= value <= 1.0
        elif key in ("latency_p95_mean", "latency_p95_max"):
            return value >= 0
        elif key.startswith("is_"):
            return value in (0.0, 1.0)
        else:
            return value >= 0

    def _calculate_feature_quality(self, features: dict) -> float:
        """
        Calculate feature quality score based on validity and ranges.

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not features:
            return 0.0

        valid_features = 0
        total_features = 0

        for key, value in features.items():
            if value is None:
                continue

            total_features += 1

            # Check if feature values are in expected ranges
            if key in ("cpu_mean", "cpu_max", "memory_mean", "memory_max"):
                # CPU and memory should be 0-1
                if 0.0 <= value <= 1.0:
                    valid_features += 1
            elif key in ("cpu_std", "memory_std"):
                # Standard deviation should be reasonable (0-0.5)
                if 0.0 <= value <= 0.5:
                    valid_features += 1
            elif key in ("error_rate_mean", "error_rate_max"):
                # Error rates should be 0-1 (0-100%)
                if 0.0 <= value <= 1.0:
                    valid_features += 1
            elif key in ("latency_p95_mean", "latency_p95_max"):
                # Latency should be positive
                if value >= 0:
                    valid_features += 1
            elif key.startswith("is_"):
                # Boolean features should be 0 or 1
                if value in (0.0, 1.0):
                    valid_features += 1
            else:
                # Other features should be non-negative
                if value >= 0:
                    valid_features += 1

        return valid_features / total_features if total_features > 0 else 0.0

    def _calculate_data_recency(self, features: dict) -> float:
        """
        Calculate data recency score.

        Returns:
            Recency score between 0.0 and 1.0
        """
        # Check if we have recent failure/restart data
        days_since_last_failure = features.get("days_since_last_failure")

        if days_since_last_failure is None:
            # No historical data available
            return 0.5

        # More recent data (failures/events) = higher confidence in patterns
        # But too recent (< 7 days) might not have enough historical context
        if days_since_last_failure < 7:
            # Very recent failure - moderate confidence
            return 0.7
        elif days_since_last_failure < 30:
            # Recent enough to be relevant
            return 0.9
        elif days_since_last_failure < 90:
            # Still relevant but getting older
            return 0.8
        elif days_since_last_failure < 180:
            # Older data
            return 0.6
        else:
            # Very old or no failures - could mean stable or no data
            return 0.5

    def _calculate_prediction_consistency(self, features: dict) -> float:
        """
        Calculate prediction consistency based on feature variance.

        Low variance in metrics indicates stable patterns = higher confidence.
        High variance indicates unstable system = lower confidence.

        Returns:
            Consistency score between 0.0 and 1.0
        """
        # Check variance/std metrics
        cpu_std = features.get("cpu_std", 0)
        memory_std = features.get("memory_std", 0)

        # Lower standard deviation = more consistent = higher confidence
        # High std (>0.3) = very inconsistent, Low std (<0.1) = very consistent
        avg_std = (cpu_std + memory_std) / 2

        if avg_std < 0.1:
            return 1.0  # Very consistent
        elif avg_std < 0.2:
            return 0.8  # Fairly consistent
        elif avg_std < 0.3:
            return 0.6  # Moderate variance
        else:
            return 0.4  # High variance

    def _identify_contributing_factors(self, features: dict) -> list:
        """Identify top contributing factors."""
        factors = []

        # Check each feature and add if significant
        if features.get("cpu_mean", 0) > 0.7:
            factors.append(
                ContributingFactor(
                    factor="cpu_usage",
                    importance=0.35,
                    current_value=features["cpu_mean"],
                    threshold=0.8,
                    description="CPU usage is consistently high",
                )
            )

        if features.get("error_rate_mean", 0) > 0.03:
            factors.append(
                ContributingFactor(
                    factor="error_rate",
                    importance=0.30,
                    current_value=features["error_rate_mean"],
                    threshold=0.05,
                    description="Error rate is elevated",
                )
            )

        if features.get("memory_trend", 0) > 0.05:
            factors.append(
                ContributingFactor(
                    factor="memory_trend",
                    importance=0.25,
                    current_value=features["memory_trend"],
                    threshold=0.1,
                    description="Memory usage is increasing over time",
                )
            )

        # Sort by importance
        factors.sort(key=lambda f: f.importance, reverse=True)

        return factors[:5]  # Top 5

    def _generate_failure_recommendations(
        self, features: dict, probability: float, resource_type: str
    ) -> list:
        """Generate recommendations to prevent failure."""
        recommendations = []

        if probability > 0.6:
            recommendations.append("Immediate attention required - high failure risk")

        if features.get("cpu_mean", 0) > 0.7:
            recommendations.append("Scale up CPU allocation or add horizontal scaling")

        if features.get("memory_mean", 0) > 0.7:
            recommendations.append("Increase memory allocation or investigate memory leaks")

        if features.get("error_rate_mean", 0) > 0.03:
            recommendations.append("Investigate error spike - check logs and dependencies")

        if "database" in resource_type.lower():
            recommendations.append("Consider read replicas or database optimization")

        if not recommendations:
            recommendations.append("Continue monitoring - no immediate action needed")

        return recommendations

    def _generate_performance_recommendations(self, current: float, baseline: float) -> list:
        """Generate performance recommendations."""
        recommendations = []

        if current > baseline * 1.5:
            recommendations.append("Performance significantly degraded - investigate immediately")
            recommendations.append("Check for recent deployments or configuration changes")
        elif current > baseline * 1.2:
            recommendations.append("Performance degrading - monitor closely")
            recommendations.append("Consider scaling or optimization")
        else:
            recommendations.append("Performance within acceptable range")

        return recommendations
