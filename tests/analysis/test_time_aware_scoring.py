"""Tests for time-aware risk scoring."""

from datetime import datetime, time, timedelta

import pytest

from topdeck.analysis.risk.time_aware_scoring import (
    DayType,
    TimeAwareRiskScorer,
    TimeWindow,
    adjust_risk_score_for_timing,
)


@pytest.fixture
def time_scorer():
    """Create a time-aware risk scorer."""
    return TimeAwareRiskScorer()


def test_weekday_business_hours_increases_risk(time_scorer):
    """Test that weekday business hours increase risk."""
    # Wednesday at 2 PM
    dt = datetime(2024, 1, 10, 14, 0, 0)
    result = time_scorer.calculate_time_based_risk_multiplier(dt)

    assert result["multiplier"] > 1.0
    assert result["day_type"] == DayType.WEEKDAY.value
    assert "Weekday" in " ".join(result["factors"])


def test_weekend_reduces_risk(time_scorer):
    """Test that weekend deployments reduce risk."""
    # Saturday at 10 AM
    dt = datetime(2024, 1, 13, 10, 0, 0)
    result = time_scorer.calculate_time_based_risk_multiplier(dt)

    assert result["multiplier"] < 1.0
    assert result["day_type"] == DayType.WEEKEND.value


def test_low_traffic_hours_reduce_risk(time_scorer):
    """Test that low traffic hours (late night) reduce risk."""
    # Wednesday at 2 AM
    dt = datetime(2024, 1, 10, 2, 0, 0)
    result = time_scorer.calculate_time_based_risk_multiplier(dt)

    assert result["multiplier"] < 1.0
    assert result["time_window"] == TimeWindow.LOW_TRAFFIC.value


def test_peak_hours_increase_risk(time_scorer):
    """Test that peak hours significantly increase risk."""
    # Weekday at 1 PM (peak hours: 10 AM - 4 PM)
    dt = datetime(2024, 1, 10, 13, 0, 0)
    result = time_scorer.calculate_time_based_risk_multiplier(dt)

    assert result["multiplier"] > 1.0
    assert result["time_window"] == TimeWindow.PEAK_HOURS.value


def test_maintenance_window_reduces_risk():
    """Test that maintenance windows significantly reduce risk."""
    # Define maintenance window: 2 AM - 5 AM
    maintenance_windows = [
        {
            "start": time(2, 0),
            "end": time(5, 0),
        }
    ]

    scorer = TimeAwareRiskScorer(maintenance_windows=maintenance_windows)

    # Wednesday at 3 AM
    dt = datetime(2024, 1, 10, 3, 0, 0)
    result = scorer.calculate_time_based_risk_multiplier(dt)

    assert result["multiplier"] < 0.5
    assert result["time_window"] == TimeWindow.MAINTENANCE_WINDOW.value


def test_holiday_reduces_risk():
    """Test that holidays reduce risk."""
    # Define New Year's Day as holiday
    holidays = [datetime(2024, 1, 1)]

    scorer = TimeAwareRiskScorer(holidays=holidays)

    # New Year's Day at 10 AM
    dt = datetime(2024, 1, 1, 10, 0, 0)
    result = scorer.calculate_time_based_risk_multiplier(dt)

    assert result["multiplier"] < 1.0
    assert result["day_type"] == DayType.HOLIDAY.value


def test_suggest_optimal_deployment_window(time_scorer):
    """Test suggesting optimal deployment windows."""
    # Start from a weekday during business hours
    current_time = datetime(2024, 1, 10, 14, 0, 0)

    suggestions = time_scorer.suggest_optimal_deployment_window(
        current_time, days_ahead=7
    )

    assert len(suggestions) > 0

    # All suggestions should have risk multiplier < 1.0
    assert all(s["risk_multiplier"] < 1.0 for s in suggestions)

    # Suggestions should be sorted by risk multiplier
    multipliers = [s["risk_multiplier"] for s in suggestions]
    assert multipliers == sorted(multipliers)


def test_adjust_risk_score_for_timing():
    """Test adjusting a base risk score for timing."""
    base_score = 50.0

    # High-risk time (weekday business hours)
    high_risk_time = datetime(2024, 1, 10, 14, 0, 0)
    high_risk_result = adjust_risk_score_for_timing(base_score, high_risk_time)

    # Low-risk time (weekend early morning)
    low_risk_time = datetime(2024, 1, 13, 2, 0, 0)
    low_risk_result = adjust_risk_score_for_timing(base_score, low_risk_time)

    # High-risk time should increase score
    assert high_risk_result["adjusted_risk_score"] > base_score

    # Low-risk time should decrease score
    assert low_risk_result["adjusted_risk_score"] < base_score


def test_multiplier_bounds(time_scorer):
    """Test that multiplier stays within reasonable bounds."""
    # Test various times
    times = [
        datetime(2024, 1, 10, 13, 0, 0),  # Weekday peak hours
        datetime(2024, 1, 13, 2, 0, 0),  # Weekend early morning
        datetime(2024, 1, 1, 10, 0, 0),  # Holiday
    ]

    for dt in times:
        result = time_scorer.calculate_time_based_risk_multiplier(dt)

        # Multiplier should be between 0.2 and 2.0
        assert 0.2 <= result["multiplier"] <= 2.0


def test_day_type_detection(time_scorer):
    """Test day type detection."""
    # Weekday
    weekday = datetime(2024, 1, 10, 10, 0, 0)  # Wednesday
    assert time_scorer._get_day_type(weekday) == DayType.WEEKDAY

    # Weekend
    saturday = datetime(2024, 1, 13, 10, 0, 0)
    assert time_scorer._get_day_type(saturday) == DayType.WEEKEND

    sunday = datetime(2024, 1, 14, 10, 0, 0)
    assert time_scorer._get_day_type(sunday) == DayType.WEEKEND

    # Holiday
    holidays = [datetime(2024, 1, 1)]
    scorer_with_holidays = TimeAwareRiskScorer(holidays=holidays)
    new_years = datetime(2024, 1, 1, 10, 0, 0)
    assert scorer_with_holidays._get_day_type(new_years) == DayType.HOLIDAY


def test_time_window_detection(time_scorer):
    """Test time window detection."""
    # Peak hours (10 AM - 4 PM)
    peak = datetime(2024, 1, 10, 13, 0, 0)
    assert time_scorer._get_time_window(peak) == TimeWindow.PEAK_HOURS

    # Business hours but not peak (8 AM - 10 AM, 4 PM - 6 PM)
    business = datetime(2024, 1, 10, 9, 0, 0)
    assert time_scorer._get_time_window(business) == TimeWindow.BUSINESS_HOURS

    # Low traffic (11 PM - 5 AM)
    low_traffic = datetime(2024, 1, 10, 2, 0, 0)
    assert time_scorer._get_time_window(low_traffic) == TimeWindow.LOW_TRAFFIC

    # Off hours (6 PM - 11 PM, 5 AM - 8 AM)
    off_hours = datetime(2024, 1, 10, 19, 0, 0)
    assert time_scorer._get_time_window(off_hours) == TimeWindow.OFF_HOURS
