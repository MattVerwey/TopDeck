"""
Test that risk scoring produces unique scores for different resources.

This test specifically addresses the bug where all resources were getting the same risk score.
"""

import pytest

from topdeck.analysis.risk.scoring import RiskScorer


@pytest.fixture
def risk_scorer():
    """Create a risk scorer with default weights."""
    return RiskScorer()


def test_different_resource_types_get_different_scores(risk_scorer):
    """Test that different resource types get different base scores."""
    # All with zero dependents and no redundancy
    database_score = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=0,
        resource_type="database",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    web_app_score = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=0,
        resource_type="web_app",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    storage_score = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=0,
        resource_type="storage_account",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    vnet_score = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=0,
        resource_type="vnet",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    # Scores should be different based on resource type criticality
    # storage_account and unknown both have base criticality of 10, so they'll be equal
    scores = [database_score, web_app_score, storage_score, vnet_score]
    assert len(set(scores)) == 4, f"Expected 4 unique scores, got {len(set(scores))}: {scores}"
    
    # Database should have highest risk due to higher criticality
    assert database_score > web_app_score > storage_score > vnet_score


def test_no_resources_with_zero_risk(risk_scorer):
    """Test that no resources end up with exactly zero risk."""
    # Even the lowest risk resource should have some base risk
    score = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=0,
        resource_type="unknown",
        is_single_point_of_failure=False,
        has_redundancy=True,  # Even with redundancy
    )
    
    assert score > 0, f"Resource with minimum risk factors should still have score > 0, got {score}"


def test_dependents_increase_risk(risk_scorer):
    """Test that resources with more dependents have higher risk."""
    score_0_deps = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=0,
        resource_type="web_app",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    score_5_deps = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=5,
        resource_type="web_app",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    score_20_deps = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=20,
        resource_type="web_app",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    assert score_20_deps > score_5_deps > score_0_deps, \
        f"More dependents should increase risk: 0={score_0_deps}, 5={score_5_deps}, 20={score_20_deps}"


def test_redundancy_reduces_risk(risk_scorer):
    """Test that redundancy reduces risk score."""
    score_no_redundancy = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=10,
        resource_type="database",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    score_with_redundancy = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=10,
        resource_type="database",
        is_single_point_of_failure=False,
        has_redundancy=True,
    )
    
    assert score_with_redundancy < score_no_redundancy, \
        f"Redundancy should reduce risk: no_redundancy={score_no_redundancy}, with_redundancy={score_with_redundancy}"


def test_spof_increases_risk(risk_scorer):
    """Test that being a SPOF increases risk."""
    score_not_spof = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=10,
        resource_type="database",
        is_single_point_of_failure=False,
        has_redundancy=False,
    )
    
    score_is_spof = risk_scorer.calculate_risk_score(
        dependency_count=0,
        dependents_count=10,
        resource_type="database",
        is_single_point_of_failure=True,
        has_redundancy=False,
    )
    
    assert score_is_spof > score_not_spof, \
        f"SPOF should increase risk: not_spof={score_not_spof}, is_spof={score_is_spof}"


def test_score_always_within_bounds(risk_scorer):
    """Test that scores are always between 0 and 100."""
    # Test with extreme values
    test_cases = [
        {"dependency_count": 0, "dependents_count": 0, "resource_type": "unknown", 
         "is_single_point_of_failure": False, "has_redundancy": True},
        {"dependency_count": 100, "dependents_count": 100, "resource_type": "database", 
         "is_single_point_of_failure": True, "has_redundancy": False, "deployment_failure_rate": 1.0},
        {"dependency_count": 50, "dependents_count": 50, "resource_type": "cache", 
         "is_single_point_of_failure": True, "has_redundancy": False},
    ]
    
    for test_case in test_cases:
        score = risk_scorer.calculate_risk_score(**test_case)
        assert 0 <= score <= 100, f"Score {score} out of bounds for case: {test_case}"


def test_diverse_scenarios_produce_diverse_scores(risk_scorer):
    """Test that a variety of resource configurations produce a good distribution of scores."""
    scenarios = [
        # Low risk scenarios
        {"dependency_count": 0, "dependents_count": 0, "resource_type": "vm", 
         "is_single_point_of_failure": False, "has_redundancy": True},
        {"dependency_count": 1, "dependents_count": 1, "resource_type": "storage_account", 
         "is_single_point_of_failure": False, "has_redundancy": True},
        
        # Medium risk scenarios
        {"dependency_count": 2, "dependents_count": 5, "resource_type": "web_app", 
         "is_single_point_of_failure": False, "has_redundancy": False},
        {"dependency_count": 3, "dependents_count": 8, "resource_type": "function_app", 
         "is_single_point_of_failure": False, "has_redundancy": False},
        
        # High risk scenarios
        {"dependency_count": 5, "dependents_count": 15, "resource_type": "database", 
         "is_single_point_of_failure": True, "has_redundancy": False},
        {"dependency_count": 10, "dependents_count": 25, "resource_type": "cache", 
         "is_single_point_of_failure": True, "has_redundancy": False},
    ]
    
    scores = [risk_scorer.calculate_risk_score(**scenario) for scenario in scenarios]
    
    # Check that we have at least 5 unique scores
    unique_scores = len(set(scores))
    assert unique_scores >= 5, f"Expected at least 5 unique scores from {len(scenarios)} scenarios, got {unique_scores}: {scores}"
    
    # Check that scores span a reasonable range
    score_range = max(scores) - min(scores)
    assert score_range >= 30, f"Expected score range of at least 30 points, got {score_range}"
