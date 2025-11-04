"""
Risk trend analysis module.

Tracks risk changes over time and identifies trends.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TrendDirection(str, Enum):
    """Trend direction indicators."""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"


class TrendSeverity(str, Enum):
    """Severity of trend change."""

    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"


@dataclass
class RiskSnapshot:
    """
    Point-in-time risk assessment snapshot.

    Attributes:
        timestamp: When the snapshot was taken
        risk_score: Risk score at this point
        risk_level: Risk level at this point
        factors: Contributing factors
    """

    timestamp: datetime
    risk_score: float
    risk_level: str
    factors: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskTrend:
    """
    Risk trend analysis over time.

    Attributes:
        resource_id: Resource being analyzed
        resource_name: Name of the resource
        current_risk_score: Current risk score
        previous_risk_score: Previous risk score for comparison
        trend_direction: Direction of trend
        trend_severity: Severity of change
        change_percentage: Percentage change in risk
        snapshots: Historical snapshots
        contributing_factors: Factors driving the trend
        recommendations: Actions to address the trend
    """

    resource_id: str
    resource_name: str
    current_risk_score: float
    previous_risk_score: float
    trend_direction: TrendDirection
    trend_severity: TrendSeverity
    change_percentage: float
    snapshots: list[RiskSnapshot] = field(default_factory=list)
    contributing_factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class RiskTrendAnalyzer:
    """
    Analyzes risk trends over time.

    Tracks how risk changes and identifies patterns.
    """

    def __init__(self, volatility_threshold: float = 15.0):
        """
        Initialize trend analyzer.

        Args:
            volatility_threshold: Threshold for volatility detection (percentage)
        """
        self.volatility_threshold = volatility_threshold

    def analyze_trend(
        self,
        resource_id: str,
        resource_name: str,
        snapshots: list[RiskSnapshot],
    ) -> RiskTrend:
        """
        Analyze risk trend from historical snapshots.

        Args:
            resource_id: Resource identifier
            resource_name: Resource name
            snapshots: List of historical risk snapshots (sorted by time)

        Returns:
            RiskTrend analysis
        """
        if len(snapshots) < 2:
            # Not enough data for trend analysis
            return self._create_insufficient_data_trend(
                resource_id, resource_name, snapshots
            )

        # Sort by timestamp
        sorted_snapshots = sorted(snapshots, key=lambda s: s.timestamp)

        current = sorted_snapshots[-1]
        previous = sorted_snapshots[-2]

        # Calculate change
        change = current.risk_score - previous.risk_score
        change_percentage = (
            (change / previous.risk_score * 100) if previous.risk_score > 0 else 0.0
        )

        # Determine trend direction
        trend_direction = self._determine_trend_direction(sorted_snapshots)

        # Determine trend severity
        trend_severity = self._determine_severity(abs(change_percentage))

        # Identify contributing factors
        contributing_factors = self._identify_contributing_factors(
            current.factors, previous.factors
        )

        # Generate recommendations
        recommendations = self._generate_trend_recommendations(
            trend_direction, trend_severity, contributing_factors
        )

        return RiskTrend(
            resource_id=resource_id,
            resource_name=resource_name,
            current_risk_score=current.risk_score,
            previous_risk_score=previous.risk_score,
            trend_direction=trend_direction,
            trend_severity=trend_severity,
            change_percentage=round(change_percentage, 2),
            snapshots=sorted_snapshots,
            contributing_factors=contributing_factors,
            recommendations=recommendations,
        )

    def detect_anomalies(
        self, snapshots: list[RiskSnapshot], window_size: int = 7
    ) -> list[dict[str, Any]]:
        """
        Detect anomalies in risk scores.

        Args:
            snapshots: Historical risk snapshots
            window_size: Number of previous snapshots to compare against

        Returns:
            List of detected anomalies
        """
        if len(snapshots) < window_size + 1:
            return []

        sorted_snapshots = sorted(snapshots, key=lambda s: s.timestamp)
        anomalies = []

        for i in range(window_size, len(sorted_snapshots)):
            current = sorted_snapshots[i]
            window = sorted_snapshots[i - window_size : i]

            # Calculate mean and standard deviation
            mean_risk = sum(s.risk_score for s in window) / len(window)
            variance = sum((s.risk_score - mean_risk) ** 2 for s in window) / len(window)
            std_dev = variance**0.5

            # Check if current value is an anomaly (> 2 standard deviations)
            if std_dev > 0:
                z_score = (current.risk_score - mean_risk) / std_dev

                if abs(z_score) > 2:
                    anomalies.append(
                        {
                            "timestamp": current.timestamp.isoformat(),
                            "risk_score": current.risk_score,
                            "expected_risk": round(mean_risk, 2),
                            "deviation": round(current.risk_score - mean_risk, 2),
                            "z_score": round(z_score, 2),
                            "severity": "high" if abs(z_score) > 3 else "medium",
                        }
                    )

        return anomalies

    def predict_future_risk(
        self, snapshots: list[RiskSnapshot], days_ahead: int = 7
    ) -> dict[str, Any]:
        """
        Simple linear prediction of future risk.

        Args:
            snapshots: Historical risk snapshots
            days_ahead: Number of days to predict ahead

        Returns:
            Dictionary with prediction and confidence
        """
        if len(snapshots) < 3:
            return {
                "prediction": None,
                "confidence": "low",
                "message": "Insufficient data for prediction",
            }

        sorted_snapshots = sorted(snapshots, key=lambda s: s.timestamp)

        # Use simple linear regression on recent data
        recent_snapshots = sorted_snapshots[-10:]  # Last 10 data points

        # Calculate trend line
        n = len(recent_snapshots)
        x_values = list(range(n))
        y_values = [s.risk_score for s in recent_snapshots]

        # Linear regression: y = mx + b
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        intercept = y_mean - slope * x_mean

        # Predict future value
        future_x = n + days_ahead
        predicted_risk = slope * future_x + intercept

        # Clamp to valid range
        predicted_risk = max(0.0, min(100.0, predicted_risk))

        # Calculate confidence based on variance
        variance = sum((y - y_mean) ** 2 for y in y_values) / n
        confidence = "high" if variance < 25 else "medium" if variance < 100 else "low"

        return {
            "predicted_risk_score": round(predicted_risk, 2),
            "days_ahead": days_ahead,
            "trend_slope": round(slope, 3),
            "confidence": confidence,
            "current_risk": recent_snapshots[-1].risk_score,
            "interpretation": self._interpret_prediction(slope, predicted_risk),
        }

    def compare_resources_trends(
        self, resource_trends: list[RiskTrend]
    ) -> dict[str, Any]:
        """
        Compare risk trends across multiple resources.

        Args:
            resource_trends: List of risk trends for different resources

        Returns:
            Comparative analysis
        """
        improving = [t for t in resource_trends if t.trend_direction == TrendDirection.IMPROVING]
        degrading = [t for t in resource_trends if t.trend_direction == TrendDirection.DEGRADING]
        stable = [t for t in resource_trends if t.trend_direction == TrendDirection.STABLE]
        volatile = [t for t in resource_trends if t.trend_direction == TrendDirection.VOLATILE]

        # Find most concerning trends
        critical_trends = [
            t
            for t in resource_trends
            if t.trend_severity == TrendSeverity.CRITICAL
            or (
                t.trend_direction == TrendDirection.DEGRADING
                and t.trend_severity == TrendSeverity.SIGNIFICANT
            )
        ]

        return {
            "total_resources": len(resource_trends),
            "improving_count": len(improving),
            "degrading_count": len(degrading),
            "stable_count": len(stable),
            "volatile_count": len(volatile),
            "critical_trends": [
                {
                    "resource_id": t.resource_id,
                    "resource_name": t.resource_name,
                    "current_risk": t.current_risk_score,
                    "change_percentage": t.change_percentage,
                    "trend_direction": t.trend_direction.value,
                }
                for t in critical_trends
            ],
            "overall_health": self._calculate_overall_health(resource_trends),
            "recommendations": self._generate_portfolio_recommendations(resource_trends),
        }

    def _determine_trend_direction(self, snapshots: list[RiskSnapshot]) -> TrendDirection:
        """Determine overall trend direction."""
        if len(snapshots) < 3:
            return TrendDirection.STABLE

        # Look at last 3-5 snapshots
        recent = snapshots[-5:] if len(snapshots) >= 5 else snapshots[-3:]

        scores = [s.risk_score for s in recent]

        # Check volatility
        mean_score = sum(scores) / len(scores)
        max_deviation = max(abs(s - mean_score) for s in scores)

        if max_deviation > self.volatility_threshold:
            return TrendDirection.VOLATILE

        # Check direction
        first_half = scores[: len(scores) // 2]
        second_half = scores[len(scores) // 2 :]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        difference = avg_second - avg_first

        if abs(difference) < 5:
            return TrendDirection.STABLE
        elif difference > 0:
            return TrendDirection.DEGRADING
        else:
            return TrendDirection.IMPROVING

    def _determine_severity(self, change_percentage: float) -> TrendSeverity:
        """Determine severity of change."""
        if change_percentage < 5:
            return TrendSeverity.MINOR
        elif change_percentage < 15:
            return TrendSeverity.MODERATE
        elif change_percentage < 30:
            return TrendSeverity.SIGNIFICANT
        else:
            return TrendSeverity.CRITICAL

    def _identify_contributing_factors(
        self, current_factors: dict, previous_factors: dict
    ) -> list[str]:
        """Identify factors contributing to risk change."""
        factors = []

        for key, current_value in current_factors.items():
            previous_value = previous_factors.get(key)

            if previous_value is None:
                continue

            if isinstance(current_value, (int, float)) and isinstance(
                previous_value, (int, float)
            ):
                if current_value > previous_value:
                    factors.append(f"{key} increased from {previous_value} to {current_value}")
                elif current_value < previous_value:
                    factors.append(f"{key} decreased from {previous_value} to {current_value}")

            elif isinstance(current_value, bool) and current_value != previous_value:
                factors.append(f"{key} changed from {previous_value} to {current_value}")

        return factors

    def _generate_trend_recommendations(
        self,
        direction: TrendDirection,
        severity: TrendSeverity,
        contributing_factors: list[str],
    ) -> list[str]:
        """Generate recommendations based on trend."""
        recommendations = []

        if direction == TrendDirection.DEGRADING:
            if severity in [TrendSeverity.SIGNIFICANT, TrendSeverity.CRITICAL]:
                recommendations.append(
                    "🚨 Risk is rapidly increasing - immediate action required"
                )
                recommendations.append("Review recent changes and consider rollback")
            else:
                recommendations.append("⚠️ Risk is increasing - monitor closely")

        elif direction == TrendDirection.VOLATILE:
            recommendations.append("📊 Risk is volatile - investigate root causes")
            recommendations.append("Consider stabilizing infrastructure and dependencies")

        elif direction == TrendDirection.IMPROVING:
            recommendations.append("✅ Risk is decreasing - continue current practices")

        if contributing_factors:
            recommendations.append(
                f"Key factors: {', '.join(contributing_factors[:3])}"
            )

        return recommendations

    def _calculate_overall_health(self, trends: list[RiskTrend]) -> str:
        """Calculate overall portfolio health."""
        if not trends:
            return "unknown"

        # Count critical issues
        critical_count = sum(
            1 for t in trends if t.trend_severity == TrendSeverity.CRITICAL
        )
        degrading_count = sum(
            1 for t in trends if t.trend_direction == TrendDirection.DEGRADING
        )

        if critical_count > len(trends) * 0.2:
            return "critical"
        elif degrading_count > len(trends) * 0.4:
            return "poor"
        elif degrading_count > len(trends) * 0.2:
            return "fair"
        else:
            return "good"

    def _generate_portfolio_recommendations(self, trends: list[RiskTrend]) -> list[str]:
        """Generate portfolio-level recommendations."""
        recommendations = []

        degrading = [t for t in trends if t.trend_direction == TrendDirection.DEGRADING]
        volatile = [t for t in trends if t.trend_direction == TrendDirection.VOLATILE]

        if len(degrading) > len(trends) * 0.3:
            recommendations.append(
                f"⚠️ {len(degrading)} resources showing degrading risk - "
                "consider infrastructure review"
            )

        if len(volatile) > len(trends) * 0.2:
            recommendations.append(
                f"📊 {len(volatile)} resources showing volatile risk - "
                "investigate for instability"
            )

        return recommendations

    def _interpret_prediction(self, slope: float, predicted_risk: float) -> str:
        """Interpret prediction results."""
        if abs(slope) < 0.1:
            return "Risk expected to remain stable"
        elif slope > 0.5:
            return "Risk expected to increase significantly"
        elif slope > 0:
            return "Risk expected to increase moderately"
        elif slope < -0.5:
            return "Risk expected to decrease significantly"
        else:
            return "Risk expected to decrease moderately"

    def _create_insufficient_data_trend(
        self, resource_id: str, resource_name: str, snapshots: list[RiskSnapshot]
    ) -> RiskTrend:
        """Create trend object when insufficient data."""
        current_score = snapshots[0].risk_score if snapshots else 0.0

        return RiskTrend(
            resource_id=resource_id,
            resource_name=resource_name,
            current_risk_score=current_score,
            previous_risk_score=current_score,
            trend_direction=TrendDirection.STABLE,
            trend_severity=TrendSeverity.MINOR,
            change_percentage=0.0,
            snapshots=snapshots,
            contributing_factors=[],
            recommendations=["⏳ Insufficient data for trend analysis - collect more snapshots"],
        )
