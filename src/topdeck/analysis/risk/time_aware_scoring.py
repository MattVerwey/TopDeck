"""
Time-aware risk scoring module.

Adjusts risk scores based on timing factors like business hours,
maintenance windows, and deployment schedules.
"""

from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any


class TimeWindow(str, Enum):
    """Time window categories."""

    BUSINESS_HOURS = "business_hours"
    OFF_HOURS = "off_hours"
    MAINTENANCE_WINDOW = "maintenance_window"
    PEAK_HOURS = "peak_hours"
    LOW_TRAFFIC = "low_traffic"


class DayType(str, Enum):
    """Day type categories."""

    WEEKDAY = "weekday"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


class TimeAwareRiskScorer:
    """
    Calculates time-aware risk adjustments.

    Considers timing factors to provide context-sensitive risk scores.
    Example: Deploying during business hours on a weekday has higher
    risk than deploying at 2 AM on Sunday.
    """

    # Default business hours (24-hour format)
    DEFAULT_BUSINESS_HOURS = {
        "start": time(8, 0),  # 8 AM
        "end": time(18, 0),  # 6 PM
    }

    # Default peak traffic hours (24-hour format)
    DEFAULT_PEAK_HOURS = {
        "start": time(10, 0),  # 10 AM
        "end": time(16, 0),  # 4 PM
    }

    def __init__(
        self,
        business_hours: dict[str, time] | None = None,
        peak_hours: dict[str, time] | None = None,
        maintenance_windows: list[dict[str, Any]] | None = None,
        holidays: list[datetime] | None = None,
    ):
        """
        Initialize time-aware risk scorer.

        Args:
            business_hours: Dictionary with 'start' and 'end' times
            peak_hours: Dictionary with 'start' and 'end' times for peak traffic
            maintenance_windows: List of maintenance window definitions
            holidays: List of holiday dates
        """
        self.business_hours = business_hours or self.DEFAULT_BUSINESS_HOURS
        self.peak_hours = peak_hours or self.DEFAULT_PEAK_HOURS
        self.maintenance_windows = maintenance_windows or []
        self.holidays = holidays or []

    def calculate_time_based_risk_multiplier(
        self, deployment_time: datetime | None = None
    ) -> dict[str, Any]:
        """
        Calculate risk multiplier based on deployment time.

        Args:
            deployment_time: Planned deployment time (defaults to now)

        Returns:
            Dictionary with multiplier and reasoning
        """
        if deployment_time is None:
            deployment_time = datetime.utcnow()

        multiplier = 1.0
        factors = []

        # Check day type
        day_type = self._get_day_type(deployment_time)

        # Check time window
        time_window = self._get_time_window(deployment_time)

        # Apply day type multiplier
        if day_type == DayType.WEEKDAY:
            multiplier *= 1.3
            factors.append("Weekday deployment increases risk (+30%)")
        elif day_type == DayType.WEEKEND:
            multiplier *= 0.7
            factors.append("Weekend deployment reduces risk (-30%)")
        elif day_type == DayType.HOLIDAY:
            multiplier *= 0.5
            factors.append("Holiday deployment significantly reduces risk (-50%)")

        # Apply time window multiplier
        if time_window == TimeWindow.PEAK_HOURS:
            multiplier *= 1.5
            factors.append("Peak traffic hours significantly increase risk (+50%)")
        elif time_window == TimeWindow.BUSINESS_HOURS:
            multiplier *= 1.2
            factors.append("Business hours increase risk (+20%)")
        elif time_window == TimeWindow.MAINTENANCE_WINDOW:
            multiplier *= 0.4
            factors.append("Maintenance window significantly reduces risk (-60%)")
        elif time_window == TimeWindow.LOW_TRAFFIC:
            multiplier *= 0.6
            factors.append("Low traffic period reduces risk (-40%)")

        # Cap multiplier at reasonable bounds
        multiplier = max(0.2, min(2.0, multiplier))

        return {
            "multiplier": round(multiplier, 2),
            "day_type": day_type.value,
            "time_window": time_window.value,
            "deployment_time": deployment_time.isoformat(),
            "factors": factors,
            "recommendation": self._generate_timing_recommendation(multiplier, time_window, day_type),
        }

    def suggest_optimal_deployment_window(
        self, current_time: datetime | None = None, days_ahead: int = 7
    ) -> list[dict[str, Any]]:
        """
        Suggest optimal deployment windows in the next N days.

        Args:
            current_time: Starting time for search (defaults to now)
            days_ahead: Number of days to look ahead

        Returns:
            List of optimal time windows with risk multipliers
        """
        if current_time is None:
            current_time = datetime.utcnow()

        suggestions = []

        # Check each day
        for day_offset in range(days_ahead):
            check_date = current_time + timedelta(days=day_offset)

            # For each day, check multiple time windows
            time_slots = [
                time(2, 0),  # 2 AM - typical low traffic
                time(6, 0),  # 6 AM - early morning
                time(12, 0),  # Noon - business hours
                time(20, 0),  # 8 PM - evening
                time(23, 0),  # 11 PM - late night
            ]

            for time_slot in time_slots:
                check_datetime = datetime.combine(check_date.date(), time_slot)
                risk_analysis = self.calculate_time_based_risk_multiplier(check_datetime)

                # Only suggest windows with low risk multipliers
                if risk_analysis["multiplier"] < 1.0:
                    suggestions.append(
                        {
                            "datetime": check_datetime.isoformat(),
                            "risk_multiplier": risk_analysis["multiplier"],
                            "day_type": risk_analysis["day_type"],
                            "time_window": risk_analysis["time_window"],
                            "recommendation": risk_analysis["recommendation"],
                        }
                    )

        # Sort by risk multiplier (lowest first)
        suggestions.sort(key=lambda x: x["risk_multiplier"])

        # Return top 5 suggestions
        return suggestions[:5]

    def _get_day_type(self, dt: datetime) -> DayType:
        """Determine day type."""
        # Check if holiday
        if any(h.date() == dt.date() for h in self.holidays):
            return DayType.HOLIDAY

        # Check if weekend
        if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return DayType.WEEKEND

        return DayType.WEEKDAY

    def _get_time_window(self, dt: datetime) -> TimeWindow:
        """Determine time window."""
        current_time = dt.time()

        # Check if in maintenance window
        for window in self.maintenance_windows:
            if self._is_in_time_range(
                current_time, window.get("start"), window.get("end")
            ):
                return TimeWindow.MAINTENANCE_WINDOW

        # Check if peak hours (subset of business hours)
        if self._is_in_time_range(
            current_time, self.peak_hours["start"], self.peak_hours["end"]
        ):
            return TimeWindow.PEAK_HOURS

        # Check if business hours
        if self._is_in_time_range(
            current_time, self.business_hours["start"], self.business_hours["end"]
        ):
            return TimeWindow.BUSINESS_HOURS

        # Check if low traffic (typically 11 PM to 5 AM)
        if current_time >= time(23, 0) or current_time < time(5, 0):
            return TimeWindow.LOW_TRAFFIC

        # Otherwise off hours
        return TimeWindow.OFF_HOURS

    def _is_in_time_range(self, check_time: time, start: time, end: time) -> bool:
        """Check if time is within range."""
        if start <= end:
            return start <= check_time <= end
        else:
            # Handle ranges that cross midnight
            return check_time >= start or check_time <= end

    def _generate_timing_recommendation(
        self, multiplier: float, time_window: TimeWindow, day_type: DayType
    ) -> str:
        """Generate human-readable timing recommendation."""
        if multiplier <= 0.5:
            return "✅ Excellent time for deployment - minimal risk"
        elif multiplier <= 0.8:
            return "👍 Good time for deployment - low risk"
        elif multiplier <= 1.2:
            return "⚠️ Moderate time for deployment - average risk"
        elif multiplier <= 1.5:
            return "⚠️ Suboptimal time for deployment - elevated risk"
        else:
            return "🚨 High-risk deployment time - consider rescheduling"


def adjust_risk_score_for_timing(
    base_risk_score: float,
    deployment_time: datetime | None = None,
    time_aware_scorer: TimeAwareRiskScorer | None = None,
) -> dict[str, Any]:
    """
    Adjust a base risk score based on deployment timing.

    Args:
        base_risk_score: Original risk score (0-100)
        deployment_time: Planned deployment time
        time_aware_scorer: Optional custom time-aware scorer

    Returns:
        Dictionary with adjusted score and details
    """
    if time_aware_scorer is None:
        time_aware_scorer = TimeAwareRiskScorer()

    timing_analysis = time_aware_scorer.calculate_time_based_risk_multiplier(deployment_time)

    adjusted_score = base_risk_score * timing_analysis["multiplier"]
    adjusted_score = max(0.0, min(100.0, adjusted_score))

    return {
        "base_risk_score": base_risk_score,
        "adjusted_risk_score": round(adjusted_score, 2),
        "time_multiplier": timing_analysis["multiplier"],
        "timing_factors": timing_analysis["factors"],
        "recommendation": timing_analysis["recommendation"],
        "day_type": timing_analysis["day_type"],
        "time_window": timing_analysis["time_window"],
    }
