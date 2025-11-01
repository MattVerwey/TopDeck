"""
Change Management Metrics.

Tracks and reports on change management KPIs and effectiveness.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass
class ChangeMetrics:
    """Metrics for change management effectiveness"""

    # Volume metrics
    total_changes: int = 0
    successful_changes: int = 0
    failed_changes: int = 0
    rolled_back_changes: int = 0
    cancelled_changes: int = 0

    # By type
    emergency_changes: int = 0
    standard_changes: int = 0

    # Risk distribution
    low_risk_changes: int = 0
    medium_risk_changes: int = 0
    high_risk_changes: int = 0
    critical_risk_changes: int = 0

    # Performance metrics
    average_lead_time_hours: float = 0.0  # Time from creation to execution
    average_downtime_seconds: float = 0.0
    average_impact_score: float = 0.0

    # Success rates
    success_rate: float = 0.0
    emergency_change_rate: float = 0.0
    rollback_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_changes": self.total_changes,
            "successful_changes": self.successful_changes,
            "failed_changes": self.failed_changes,
            "rolled_back_changes": self.rolled_back_changes,
            "cancelled_changes": self.cancelled_changes,
            "emergency_changes": self.emergency_changes,
            "standard_changes": self.standard_changes,
            "low_risk_changes": self.low_risk_changes,
            "medium_risk_changes": self.medium_risk_changes,
            "high_risk_changes": self.high_risk_changes,
            "critical_risk_changes": self.critical_risk_changes,
            "average_lead_time_hours": round(self.average_lead_time_hours, 2),
            "average_downtime_seconds": round(self.average_downtime_seconds, 2),
            "average_impact_score": round(self.average_impact_score, 2),
            "success_rate": round(self.success_rate, 2),
            "emergency_change_rate": round(self.emergency_change_rate, 2),
            "rollback_rate": round(self.rollback_rate, 2),
        }


class ChangeMetricsCalculator:
    """Calculates change management metrics"""

    def calculate_metrics(self, changes: list[dict[str, Any]]) -> ChangeMetrics:
        """
        Calculate metrics from a list of change requests.

        Args:
            changes: List of change request dictionaries

        Returns:
            ChangeMetrics object with calculated values
        """
        if not changes:
            return ChangeMetrics()

        metrics = ChangeMetrics()
        metrics.total_changes = len(changes)

        # Count by status
        for change in changes:
            status = change.get("status", "")
            change_type = change.get("change_type", "")
            risk_level = change.get("risk_level", "")

            # Status counts
            if status == "completed":
                metrics.successful_changes += 1
            elif status == "failed":
                metrics.failed_changes += 1
            elif status == "rolled_back":
                metrics.rolled_back_changes += 1
            elif status == "cancelled":
                metrics.cancelled_changes += 1

            # Type counts
            if change_type == "emergency":
                metrics.emergency_changes += 1
            else:
                metrics.standard_changes += 1

            # Risk distribution
            if risk_level == "low":
                metrics.low_risk_changes += 1
            elif risk_level == "medium":
                metrics.medium_risk_changes += 1
            elif risk_level == "high":
                metrics.high_risk_changes += 1
            elif risk_level == "critical":
                metrics.critical_risk_changes += 1

        # Calculate rates
        if metrics.total_changes > 0:
            metrics.success_rate = (metrics.successful_changes / metrics.total_changes) * 100
            metrics.emergency_change_rate = (
                metrics.emergency_changes / metrics.total_changes
            ) * 100
            metrics.rollback_rate = (metrics.rolled_back_changes / metrics.total_changes) * 100

        # Calculate averages
        lead_times = []
        downtimes = []
        impact_scores = []

        for change in changes:
            # Lead time calculation
            created_at = change.get("created_at")
            actual_start = change.get("actual_start")
            if created_at and actual_start:
                try:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    started = datetime.fromisoformat(actual_start.replace("Z", "+00:00"))
                    lead_time = (started - created).total_seconds() / 3600  # hours
                    lead_times.append(lead_time)
                except (ValueError, AttributeError):
                    pass

            # Downtime
            downtime = change.get("estimated_downtime_seconds", 0)
            if downtime:
                downtimes.append(downtime)

            # Impact score (if available)
            impact = change.get("affected_services_count", 0)
            if impact:
                impact_scores.append(impact)

        if lead_times:
            metrics.average_lead_time_hours = sum(lead_times) / len(lead_times)
        if downtimes:
            metrics.average_downtime_seconds = sum(downtimes) / len(downtimes)
        if impact_scores:
            metrics.average_impact_score = sum(impact_scores) / len(impact_scores)

        return metrics

    def get_trend_analysis(
        self, changes: list[dict[str, Any]], period_days: int = 30
    ) -> dict[str, Any]:
        """
        Analyze trends over a time period.

        Args:
            changes: List of change request dictionaries
            period_days: Number of days to analyze

        Returns:
            Dictionary with trend analysis
        """
        if not changes:
            return {
                "period_days": period_days,
                "changes_by_week": [],
                "success_rate_trend": [],
                "risk_distribution_trend": [],
            }

        # Group by week
        now = datetime.now(UTC)
        start_date = now - timedelta(days=period_days)

        changes_by_week: dict[int, list[dict[str, Any]]] = {}

        for change in changes:
            created_at = change.get("created_at")
            if not created_at:
                continue

            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created >= start_date:
                    # Calculate week number
                    week_num = (created - start_date).days // 7
                    if week_num not in changes_by_week:
                        changes_by_week[week_num] = []
                    changes_by_week[week_num].append(change)
            except (ValueError, AttributeError):
                continue

        # Calculate metrics per week
        weekly_data = []
        for week in sorted(changes_by_week.keys()):
            week_changes = changes_by_week[week]
            week_metrics = self.calculate_metrics(week_changes)
            weekly_data.append(
                {
                    "week": week,
                    "total": len(week_changes),
                    "success_rate": week_metrics.success_rate,
                    "emergency_rate": week_metrics.emergency_change_rate,
                }
            )

        return {
            "period_days": period_days,
            "weekly_data": weekly_data,
            "total_changes": len([c for c in changes if self._is_in_period(c, start_date)]),
        }

    def _is_in_period(self, change: dict[str, Any], start_date: datetime) -> bool:
        """Check if change is within the analysis period"""
        created_at = change.get("created_at")
        if not created_at:
            return False

        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            return created >= start_date
        except (ValueError, AttributeError):
            return False

    def get_recommendations(self, metrics: ChangeMetrics) -> list[str]:
        """
        Generate recommendations based on metrics.

        Args:
            metrics: Calculated ChangeMetrics

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Success rate analysis
        if metrics.success_rate < 90 and metrics.total_changes > 10:
            recommendations.append(
                f"Success rate is {metrics.success_rate:.1f}%. "
                "Consider improving testing and validation processes."
            )

        # Emergency change rate
        if metrics.emergency_change_rate > 20 and metrics.total_changes > 10:
            recommendations.append(
                f"Emergency changes represent {metrics.emergency_change_rate:.1f}% of total. "
                "Focus on proactive planning to reduce urgent changes."
            )

        # Rollback rate
        if metrics.rollback_rate > 10 and metrics.total_changes > 10:
            recommendations.append(
                f"Rollback rate is {metrics.rollback_rate:.1f}%. "
                "Improve pre-deployment testing and staged rollouts."
            )

        # Risk distribution
        high_risk_pct = (
            (metrics.high_risk_changes + metrics.critical_risk_changes)
            / metrics.total_changes
            * 100
            if metrics.total_changes > 0
            else 0
        )
        if high_risk_pct > 30:
            recommendations.append(
                f"{high_risk_pct:.1f}% of changes are high/critical risk. "
                "Consider breaking large changes into smaller, safer increments."
            )

        # Lead time
        if metrics.average_lead_time_hours < 24 and metrics.emergency_change_rate < 50:
            recommendations.append(
                f"Average lead time is {metrics.average_lead_time_hours:.1f} hours. "
                "Plan changes further in advance to allow proper review and testing."
            )

        # Positive feedback
        if metrics.success_rate >= 95 and metrics.total_changes > 10:
            recommendations.append(
                f"Excellent success rate of {metrics.success_rate:.1f}%! "
                "Continue following current change management practices."
            )

        return recommendations
