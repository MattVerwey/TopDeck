"""Tests for risk scoring module."""

import pytest

from topdeck.analysis.risk.models import RiskLevel
from topdeck.analysis.risk.scoring import RiskScorer


@pytest.fixture
def risk_scorer():
    """Create a risk scorer with default weights."""
    return RiskScorer()


def test_risk_scorer_initialization():
    """Test risk scorer initialization with default weights."""
    scorer = RiskScorer()
    assert scorer.weights is not None
    assert "dependency_count" in scorer.weights
    assert "criticality" in scorer.weights


def test_risk_scorer_custom_weights():
    """Test risk scorer with custom weights."""
    custom_weights = {
        "dependency_count": 0.3,
        "criticality": 0.3,
        "failure_rate": 0.2,
        "time_since_change": -0.1,
        "redundancy": -0.1,
    }
    scorer = RiskScorer(weights=custom_weights)
    assert scorer.weights == custom_weights


def test_calculate_risk_score_low_risk(risk_scorer):
    """Test risk score calculation for low-risk resource."""
    score = risk_scorer.calculate_risk_score(
        dependency_count=1,
        dependents_count=1,
        resource_type="vm",
        is_single_point_of_failure=False,
        has_redundancy=True,
    )
    assert 0 <= score <= 100
    assert score < 30  # Should be low risk


def test_calculate_risk_score_high_risk(risk_scorer):
    """Test risk score calculation for high-risk resource."""
    score = risk_scorer.calculate_risk_score(
        dependency_count=5,
        dependents_count=20,
        resource_type="database",
        is_single_point_of_failure=True,
        deployment_failure_rate=0.3,
        has_redundancy=False,
    )
    assert 0 <= score <= 100
    assert score > 50  # Should be high risk


def test_calculate_risk_score_spof(risk_scorer):
    """Test risk score for single point of failure."""
    score_spof = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=10,
        resource_type="database",
        is_single_point_of_failure=True,
        has_redundancy=False,
    )

    score_redundant = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=10,
        resource_type="database",
        is_single_point_of_failure=False,
        has_redundancy=True,
    )

    # SPOF should have higher risk
    assert score_spof > score_redundant


def test_calculate_risk_score_time_factor(risk_scorer):
    """Test time since change reduces risk."""
    score_recent = risk_scorer.calculate_risk_score(
        dependency_count=5,
        dependents_count=5,
        resource_type="web_app",
        is_single_point_of_failure=False,
        time_since_last_change_hours=1.0,
    )

    score_old = risk_scorer.calculate_risk_score(
        dependency_count=5,
        dependents_count=5,
        resource_type="web_app",
        is_single_point_of_failure=False,
        time_since_last_change_hours=1000.0,
    )

    # Recent changes should have higher risk
    assert score_recent > score_old


def test_calculate_criticality_database(risk_scorer):
    """Test criticality calculation for database."""
    criticality = risk_scorer._calculate_criticality(
        resource_type="database", is_spof=False, dependents_count=5
    )
    assert criticality > 30  # Databases are critical


def test_calculate_criticality_key_vault(risk_scorer):
    """Test criticality calculation for key vault."""
    criticality = risk_scorer._calculate_criticality(
        resource_type="key_vault", is_spof=False, dependents_count=5
    )
    assert criticality > 40  # Key vaults are very critical


def test_calculate_criticality_with_spof_boost(risk_scorer):
    """Test criticality boost for SPOF."""
    criticality_normal = risk_scorer._calculate_criticality(
        resource_type="web_app", is_spof=False, dependents_count=5
    )

    criticality_spof = risk_scorer._calculate_criticality(
        resource_type="web_app", is_spof=True, dependents_count=5
    )

    assert criticality_spof > criticality_normal


def test_calculate_criticality_with_many_dependents(risk_scorer):
    """Test criticality increases with dependents."""
    criticality_few = risk_scorer._calculate_criticality(
        resource_type="web_app", is_spof=False, dependents_count=2
    )

    criticality_many = risk_scorer._calculate_criticality(
        resource_type="web_app", is_spof=False, dependents_count=15
    )

    assert criticality_many > criticality_few


def test_get_risk_level_low(risk_scorer):
    """Test risk level classification for low risk."""
    level = risk_scorer.get_risk_level(15.0)
    assert level == RiskLevel.LOW


def test_get_risk_level_medium(risk_scorer):
    """Test risk level classification for medium risk."""
    level = risk_scorer.get_risk_level(35.0)
    assert level == RiskLevel.MEDIUM


def test_get_risk_level_high(risk_scorer):
    """Test risk level classification for high risk."""
    level = risk_scorer.get_risk_level(60.0)
    assert level == RiskLevel.HIGH


def test_get_risk_level_critical(risk_scorer):
    """Test risk level classification for critical risk."""
    level = risk_scorer.get_risk_level(80.0)
    assert level == RiskLevel.CRITICAL


def test_generate_recommendations_critical_risk(risk_scorer):
    """Test recommendations for critical risk."""
    recommendations = risk_scorer.generate_recommendations(
        risk_score=80.0,
        is_spof=False,
        has_redundancy=True,
        dependents_count=5,
        deployment_failure_rate=0.1,
    )
    assert len(recommendations) > 0
    assert any("CRITICAL RISK" in r for r in recommendations)


def test_generate_recommendations_spof(risk_scorer):
    """Test recommendations for SPOF."""
    recommendations = risk_scorer.generate_recommendations(
        risk_score=50.0,
        is_spof=True,
        has_redundancy=False,
        dependents_count=5,
        deployment_failure_rate=0.1,
    )
    assert len(recommendations) > 0
    assert any("Single Point of Failure" in r for r in recommendations)
    assert any("redundancy" in r.lower() for r in recommendations)


def test_generate_recommendations_high_dependency(risk_scorer):
    """Test recommendations for high dependency count."""
    recommendations = risk_scorer.generate_recommendations(
        risk_score=50.0,
        is_spof=False,
        has_redundancy=True,
        dependents_count=15,
        deployment_failure_rate=0.1,
    )
    assert len(recommendations) > 0
    assert any("dependency count" in r.lower() for r in recommendations)


def test_generate_recommendations_high_failure_rate(risk_scorer):
    """Test recommendations for high failure rate."""
    recommendations = risk_scorer.generate_recommendations(
        risk_score=40.0,
        is_spof=False,
        has_redundancy=True,
        dependents_count=5,
        deployment_failure_rate=0.3,
    )
    assert len(recommendations) > 0
    assert any("failure rate" in r.lower() for r in recommendations)


def test_generate_recommendations_always_returns_something(risk_scorer):
    """Test that recommendations are always generated."""
    recommendations = risk_scorer.generate_recommendations(
        risk_score=30.0,
        is_spof=False,
        has_redundancy=True,
        dependents_count=3,
        deployment_failure_rate=0.05,
    )
    assert len(recommendations) > 0


def test_risk_score_bounds(risk_scorer):
    """Test that risk scores are always within 0-100."""
    # Test extreme values
    score_max = risk_scorer.calculate_risk_score(
        dependency_count=100,
        dependents_count=100,
        resource_type="database",
        is_single_point_of_failure=True,
        deployment_failure_rate=1.0,
        time_since_last_change_hours=0.0,
        has_redundancy=False,
    )
    assert 0 <= score_max <= 100

    score_min = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=0,
        resource_type="vnet",
        is_single_point_of_failure=False,
        deployment_failure_rate=0.0,
        time_since_last_change_hours=10000.0,
        has_redundancy=True,
    )
    assert 0 <= score_min <= 100


def test_aks_cluster_without_ha_never_low_risk(risk_scorer):
    """Test that AKS cluster without HA is never LOW risk."""
    # Even with minimal dependents and no SPOF marking,
    # AKS without HA should be at least MEDIUM risk
    score = risk_scorer.calculate_risk_score(
        dependency_count=2,
        dependents_count=2,
        resource_type="aks",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    risk_level = risk_scorer.get_risk_level(score)
    
    # Should NOT be LOW risk (score should be >= 25)
    assert score >= 25, f"AKS without HA should never be LOW risk, got score {score}"
    assert risk_level != RiskLevel.LOW, "AKS without HA should not have LOW risk level"


def test_aks_cluster_with_ha_can_be_lower_risk(risk_scorer):
    """Test that AKS cluster with HA has significantly lower risk."""
    # Score without HA
    score_no_ha = risk_scorer.calculate_risk_score(
        dependency_count=2,
        dependents_count=5,
        resource_type="aks",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    # Score with HA
    score_with_ha = risk_scorer.calculate_risk_score(
        dependency_count=2,
        dependents_count=5,
        resource_type="aks",
        is_single_point_of_failure=False,
        has_redundancy=True,
    )
    
    # HA should significantly reduce risk
    assert score_with_ha < score_no_ha, "HA should reduce risk score"
    assert (score_no_ha - score_with_ha) > 15, "HA should reduce risk by significant amount"


def test_infrastructure_without_redundancy_is_critical(risk_scorer):
    """Test that infrastructure components without redundancy get higher criticality."""
    # Load balancer without redundancy
    lb_no_redundancy = risk_scorer.calculate_risk_score(
        dependency_count=1,
        dependents_count=10,
        resource_type="load_balancer",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    # Load balancer with redundancy
    lb_with_redundancy = risk_scorer.calculate_risk_score(
        dependency_count=1,
        dependents_count=10,
        resource_type="load_balancer",
        is_single_point_of_failure=False,
        has_redundancy=True,
    )
    
    # Without redundancy should have higher risk
    assert lb_no_redundancy > lb_with_redundancy
    # And should be at least MEDIUM risk
    assert lb_no_redundancy >= 25
