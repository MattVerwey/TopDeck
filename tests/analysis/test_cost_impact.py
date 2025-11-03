"""Tests for cost impact analysis."""

import pytest

from topdeck.analysis.risk.cost_impact import CostCategory, CostImpactAnalyzer


@pytest.fixture
def cost_analyzer():
    """Create a cost impact analyzer with default rates."""
    return CostImpactAnalyzer()


def test_basic_cost_calculation(cost_analyzer):
    """Test basic cost impact calculation."""
    result = cost_analyzer.calculate_cost_impact(
        resource_id="test-resource",
        resource_name="Test Resource",
        resource_type="web_app",
        downtime_hours=2.0,
        affected_users=1000,
        is_revenue_generating=True,
        has_sla=False,
    )

    assert result.resource_id == "test-resource"
    assert result.total_cost > 0
    assert result.hourly_impact_rate > 0
    assert result.affected_users == 1000

    # Should have revenue loss component
    assert CostCategory.REVENUE_LOSS.value in result.cost_breakdown

    # Should have engineering time component
    assert CostCategory.ENGINEERING_TIME.value in result.cost_breakdown

    # Should have support cost component
    assert CostCategory.CUSTOMER_SUPPORT.value in result.cost_breakdown


def test_revenue_loss_calculation(cost_analyzer):
    """Test revenue loss calculation."""
    # Revenue generating resource
    with_revenue = cost_analyzer.calculate_cost_impact(
        resource_id="test-1",
        resource_name="Revenue Resource",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=1000,
        is_revenue_generating=True,
        has_sla=False,
    )

    # Non-revenue generating resource
    without_revenue = cost_analyzer.calculate_cost_impact(
        resource_id="test-2",
        resource_name="Non-Revenue Resource",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=1000,
        is_revenue_generating=False,
        has_sla=False,
    )

    # Revenue generating should have revenue loss
    assert CostCategory.REVENUE_LOSS.value in with_revenue.cost_breakdown
    assert with_revenue.cost_breakdown[CostCategory.REVENUE_LOSS.value] > 0

    # Non-revenue should not have revenue loss
    if CostCategory.REVENUE_LOSS.value in without_revenue.cost_breakdown:
        assert without_revenue.cost_breakdown[CostCategory.REVENUE_LOSS.value] == 0


def test_sla_penalty_calculation():
    """Test SLA penalty calculation."""
    annual_revenue = 10_000_000  # $10M

    analyzer = CostImpactAnalyzer(annual_revenue=annual_revenue)

    result = analyzer.calculate_cost_impact(
        resource_id="test-resource",
        resource_name="Test Resource",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=1000,
        is_revenue_generating=True,
        has_sla=True,
    )

    # Should have SLA penalty
    assert CostCategory.SLA_PENALTIES.value in result.cost_breakdown
    assert result.cost_breakdown[CostCategory.SLA_PENALTIES.value] > 0


def test_industry_multiplier():
    """Test industry-specific cost multipliers."""
    # Fintech has 3x multiplier
    fintech_analyzer = CostImpactAnalyzer(industry="fintech")

    # Default has 1x multiplier
    default_analyzer = CostImpactAnalyzer(industry="default")

    fintech_result = fintech_analyzer.calculate_cost_impact(
        resource_id="test-1",
        resource_name="Fintech Resource",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=1000,
        is_revenue_generating=True,
        has_sla=False,
    )

    default_result = default_analyzer.calculate_cost_impact(
        resource_id="test-2",
        resource_name="Default Resource",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=1000,
        is_revenue_generating=True,
        has_sla=False,
    )

    # Fintech revenue loss should be ~3x higher
    fintech_revenue_loss = fintech_result.cost_breakdown[CostCategory.REVENUE_LOSS.value]
    default_revenue_loss = default_result.cost_breakdown[CostCategory.REVENUE_LOSS.value]

    assert fintech_revenue_loss > default_revenue_loss * 2.5


def test_recovery_cost_by_resource_type(cost_analyzer):
    """Test that recovery costs vary by resource type."""
    # Database should have high recovery cost
    db_result = cost_analyzer.calculate_cost_impact(
        resource_id="test-db",
        resource_name="Database",
        resource_type="sql_database",
        downtime_hours=1.0,
        affected_users=100,
        is_revenue_generating=False,
        has_sla=False,
    )

    # Cache should have lower recovery cost
    cache_result = cost_analyzer.calculate_cost_impact(
        resource_id="test-cache",
        resource_name="Cache",
        resource_type="redis_cache",
        downtime_hours=1.0,
        affected_users=100,
        is_revenue_generating=False,
        has_sla=False,
    )

    db_recovery = db_result.cost_breakdown[CostCategory.RECOVERY_COSTS.value]
    cache_recovery = cache_result.cost_breakdown[CostCategory.RECOVERY_COSTS.value]

    # Database recovery should cost more
    assert db_recovery > cache_recovery


def test_annual_risk_cost_estimation(cost_analyzer):
    """Test annual risk cost estimation."""
    hourly_rate = 1000.0  # $1000/hour
    failure_probability = 0.1  # 10% chance per year
    recovery_time = 2.0  # 2 hours MTTR

    result = cost_analyzer.estimate_annual_risk_cost(
        hourly_impact_rate=hourly_rate,
        failure_probability_per_year=failure_probability,
        mean_time_to_recovery_hours=recovery_time,
    )

    expected_cost = hourly_rate * failure_probability * recovery_time

    assert result["expected_annual_cost"] == pytest.approx(expected_cost, rel=0.01)
    assert result["min_annual_cost"] < result["expected_annual_cost"]
    assert result["max_annual_cost"] > result["expected_annual_cost"]
    assert result["expected_downtime_hours"] == failure_probability * recovery_time


def test_mitigation_cost_comparison(cost_analyzer):
    """Test mitigation cost comparison."""
    current_risk_cost = 100_000  # $100K annual risk

    mitigations = [
        {
            "name": "Add redundancy",
            "implementation_cost": 20_000,
            "annual_operational_cost": 5_000,
            "risk_reduction_percentage": 80,  # 80% reduction
        },
        {
            "name": "Basic monitoring",
            "implementation_cost": 2_000,
            "annual_operational_cost": 500,
            "risk_reduction_percentage": 20,  # 20% reduction
        },
    ]

    results = cost_analyzer.compare_mitigation_costs(current_risk_cost, mitigations)

    assert len(results) == 2

    # Should be sorted by ROI
    assert results[0]["roi_percentage"] >= results[1]["roi_percentage"]

    # Both should show positive net benefit for high risk cost
    for result in results:
        assert "roi_percentage" in result
        assert "payback_months" in result
        assert "net_benefit_year_1" in result
        assert "recommended" in result


def test_confidence_level_determination(cost_analyzer):
    """Test confidence level determination."""
    # High confidence: revenue generating, SLA, many users
    high_confidence = cost_analyzer.calculate_cost_impact(
        resource_id="test-1",
        resource_name="High Confidence",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=1000,
        is_revenue_generating=True,
        has_sla=True,
    )

    # Low confidence: not revenue generating, no SLA, few users
    low_confidence = cost_analyzer.calculate_cost_impact(
        resource_id="test-2",
        resource_name="Low Confidence",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=5,
        is_revenue_generating=False,
        has_sla=False,
    )

    assert high_confidence.confidence_level in ["high", "medium"]
    assert low_confidence.confidence_level in ["low", "medium"]


def test_assumptions_included(cost_analyzer):
    """Test that assumptions are included in result."""
    result = cost_analyzer.calculate_cost_impact(
        resource_id="test-resource",
        resource_name="Test Resource",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=100,
        is_revenue_generating=True,
        has_sla=False,
    )

    assert len(result.assumptions) > 0
    assert any("Revenue loss" in a for a in result.assumptions)


def test_zero_users_no_revenue_loss(cost_analyzer):
    """Test that zero users means no revenue loss."""
    result = cost_analyzer.calculate_cost_impact(
        resource_id="test-resource",
        resource_name="Test Resource",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=0,
        is_revenue_generating=True,
        has_sla=False,
    )

    # Should not have revenue loss for 0 users
    if CostCategory.REVENUE_LOSS.value in result.cost_breakdown:
        assert result.cost_breakdown[CostCategory.REVENUE_LOSS.value] == 0


def test_longer_downtime_increases_costs(cost_analyzer):
    """Test that longer downtime increases costs."""
    short_downtime = cost_analyzer.calculate_cost_impact(
        resource_id="test-1",
        resource_name="Short Downtime",
        resource_type="web_app",
        downtime_hours=1.0,
        affected_users=1000,
        is_revenue_generating=True,
        has_sla=False,
    )

    long_downtime = cost_analyzer.calculate_cost_impact(
        resource_id="test-2",
        resource_name="Long Downtime",
        resource_type="web_app",
        downtime_hours=10.0,
        affected_users=1000,
        is_revenue_generating=True,
        has_sla=False,
    )

    assert long_downtime.total_cost > short_downtime.total_cost
    assert long_downtime.hourly_impact_rate > 0
