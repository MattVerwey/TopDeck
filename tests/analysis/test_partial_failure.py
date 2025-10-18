"""
Tests for partial failure analysis.
"""

import pytest

from topdeck.analysis.risk.partial_failure import PartialFailureAnalyzer
from topdeck.analysis.risk.models import (
    FailureType,
    OutcomeType,
    ImpactLevel,
)


class TestPartialFailureAnalyzer:
    """Test partial failure scenario analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return PartialFailureAnalyzer()
    
    def test_analyze_degraded_performance_database(self, analyzer):
        """Test degraded performance analysis for database."""
        scenario = analyzer.analyze_degraded_performance(
            resource_id="db-001",
            resource_name="production-db",
            resource_type="database",
            current_load=0.8,
        )
        
        assert scenario.resource_id == "db-001"
        assert scenario.resource_name == "production-db"
        assert scenario.failure_type == FailureType.DEGRADED_PERFORMANCE
        assert len(scenario.outcomes) > 0
        assert scenario.overall_impact in [
            ImpactLevel.LOW,
            ImpactLevel.MEDIUM,
            ImpactLevel.HIGH,
        ]
        
        # Check outcomes have expected types
        outcome_types = {o.outcome_type for o in scenario.outcomes}
        assert OutcomeType.DEGRADED in outcome_types or OutcomeType.TIMEOUT in outcome_types
        
        # Check mitigation strategies provided
        assert len(scenario.mitigation_strategies) > 0
        assert any("connection pool" in s.lower() for s in scenario.mitigation_strategies)
        
        # Check monitoring recommendations
        assert len(scenario.monitoring_recommendations) > 0
    
    def test_analyze_degraded_performance_web_app(self, analyzer):
        """Test degraded performance analysis for web application."""
        scenario = analyzer.analyze_degraded_performance(
            resource_id="web-001",
            resource_name="api-service",
            resource_type="web_app",
            current_load=0.6,
        )
        
        assert scenario.resource_id == "web-001"
        assert scenario.failure_type == FailureType.DEGRADED_PERFORMANCE
        assert len(scenario.outcomes) > 0
        
        # Check auto-scaling recommendation
        assert any("auto-scaling" in s.lower() for s in scenario.mitigation_strategies)
    
    def test_analyze_degraded_performance_redis(self, analyzer):
        """Test degraded performance analysis for Redis cache."""
        scenario = analyzer.analyze_degraded_performance(
            resource_id="cache-001",
            resource_name="redis-cache",
            resource_type="redis_cache",
            current_load=0.9,
        )
        
        assert scenario.resource_id == "cache-001"
        assert len(scenario.outcomes) > 0
        
        # High load should increase impact
        assert scenario.overall_impact in [ImpactLevel.MEDIUM, ImpactLevel.HIGH, ImpactLevel.SEVERE]
        
        # Check cache-specific recommendations
        mitigation_text = " ".join(scenario.mitigation_strategies).lower()
        assert "cache" in mitigation_text or "eviction" in mitigation_text
    
    def test_analyze_degraded_performance_load_affects_probability(self, analyzer):
        """Test that current load affects failure probability."""
        # Low load scenario
        low_load = analyzer.analyze_degraded_performance(
            resource_id="test-001",
            resource_name="test",
            resource_type="web_app",
            current_load=0.3,
        )
        
        # High load scenario
        high_load = analyzer.analyze_degraded_performance(
            resource_id="test-001",
            resource_name="test",
            resource_type="web_app",
            current_load=0.9,
        )
        
        # High load should have higher probability outcomes
        low_load_max_prob = max(o.probability for o in low_load.outcomes)
        high_load_max_prob = max(o.probability for o in high_load.outcomes)
        
        assert high_load_max_prob >= low_load_max_prob
    
    def test_analyze_intermittent_failure(self, analyzer):
        """Test intermittent failure analysis."""
        scenario = analyzer.analyze_intermittent_failure(
            resource_id="api-001",
            resource_name="payment-api",
            resource_type="api_gateway",
            failure_frequency=0.05,
        )
        
        assert scenario.resource_id == "api-001"
        assert scenario.failure_type == FailureType.INTERMITTENT_FAILURE
        assert len(scenario.outcomes) > 0
        
        # Should include blip or error rate outcomes
        outcome_types = {o.outcome_type for o in scenario.outcomes}
        assert OutcomeType.BLIP in outcome_types or OutcomeType.ERROR_RATE in outcome_types
        
        # Check retry recommendations
        mitigation_text = " ".join(scenario.mitigation_strategies).lower()
        assert "retry" in mitigation_text or "circuit breaker" in mitigation_text
        
        # Check monitoring includes error rate
        monitoring_text = " ".join(scenario.monitoring_recommendations).lower()
        assert "error" in monitoring_text or "latency" in monitoring_text
    
    def test_analyze_intermittent_failure_low_frequency(self, analyzer):
        """Test intermittent failure with low frequency."""
        scenario = analyzer.analyze_intermittent_failure(
            resource_id="test-001",
            resource_name="test",
            resource_type="web_app",
            failure_frequency=0.01,  # 1% failure rate
        )
        
        # Low failure rate should result in low impact
        assert scenario.overall_impact in [ImpactLevel.MINIMAL, ImpactLevel.LOW]
    
    def test_analyze_intermittent_failure_high_frequency(self, analyzer):
        """Test intermittent failure with high frequency."""
        scenario = analyzer.analyze_intermittent_failure(
            resource_id="test-001",
            resource_name="test",
            resource_type="web_app",
            failure_frequency=0.15,  # 15% failure rate
        )
        
        # High failure rate should result in medium or higher impact
        assert scenario.overall_impact in [ImpactLevel.MEDIUM, ImpactLevel.HIGH]
    
    def test_analyze_partial_outage_single_zone(self, analyzer):
        """Test partial outage with single zone affected."""
        scenario = analyzer.analyze_partial_outage(
            resource_id="lb-001",
            resource_name="load-balancer",
            resource_type="load_balancer",
            affected_zones=["zone-a"],
        )
        
        assert scenario.resource_id == "lb-001"
        assert scenario.failure_type == FailureType.PARTIAL_OUTAGE
        assert len(scenario.outcomes) > 0
        
        # Should include partial outage outcome
        outcome_types = {o.outcome_type for o in scenario.outcomes}
        assert OutcomeType.PARTIAL_OUTAGE in outcome_types
        
        # Single zone = ~33% affected = low/medium impact
        assert scenario.overall_impact in [ImpactLevel.LOW, ImpactLevel.MEDIUM]
    
    def test_analyze_partial_outage_multiple_zones(self, analyzer):
        """Test partial outage with multiple zones affected."""
        scenario = analyzer.analyze_partial_outage(
            resource_id="aks-001",
            resource_name="kubernetes-cluster",
            resource_type="aks",
            affected_zones=["zone-a", "zone-b"],
        )
        
        assert len(scenario.outcomes) > 0
        
        # Multiple zones = ~66% affected = high impact
        assert scenario.overall_impact in [ImpactLevel.MEDIUM, ImpactLevel.HIGH]
        
        # Check multi-zone recommendations
        mitigation_text = " ".join(scenario.mitigation_strategies).lower()
        assert "zone" in mitigation_text or "availability" in mitigation_text
    
    def test_analyze_partial_outage_default_zone(self, analyzer):
        """Test partial outage with default zone assumption."""
        scenario = analyzer.analyze_partial_outage(
            resource_id="test-001",
            resource_name="test",
            resource_type="web_app",
            affected_zones=None,  # Should default to one zone
        )
        
        assert len(scenario.outcomes) > 0
        # Default should be low/medium impact (1 of 3 zones)
        assert scenario.overall_impact in [ImpactLevel.LOW, ImpactLevel.MEDIUM]
    
    def test_user_impact_descriptions_are_meaningful(self, analyzer):
        """Test that user impact descriptions are human-readable."""
        scenario = analyzer.analyze_degraded_performance(
            resource_id="test-001",
            resource_name="test",
            resource_type="database",
            current_load=0.7,
        )
        
        for outcome in scenario.outcomes:
            # Should have non-empty description
            assert len(outcome.user_impact_description) > 0
            # Should mention users or requests
            desc_lower = outcome.user_impact_description.lower()
            assert "user" in desc_lower or "request" in desc_lower or "service" in desc_lower
    
    def test_outcome_probabilities_sum_makes_sense(self, analyzer):
        """Test that outcome probabilities are reasonable."""
        scenario = analyzer.analyze_degraded_performance(
            resource_id="test-001",
            resource_name="test",
            resource_type="web_app",
            current_load=0.7,
        )
        
        # Probabilities should all be between 0 and 1
        for outcome in scenario.outcomes:
            assert 0.0 <= outcome.probability <= 1.0
        
        # Total probability can be > 1 (multiple outcomes can occur)
        # but each individual one should be reasonable
        assert all(o.probability > 0 for o in scenario.outcomes)
    
    def test_outcome_durations_are_realistic(self, analyzer):
        """Test that outcome durations are realistic."""
        scenario = analyzer.analyze_intermittent_failure(
            resource_id="test-001",
            resource_name="test",
            resource_type="api_gateway",
            failure_frequency=0.05,
        )
        
        for outcome in scenario.outcomes:
            # Durations should be positive and reasonable (not years)
            assert outcome.duration_seconds > 0
            assert outcome.duration_seconds < 7200  # Less than 2 hours
    
    def test_affected_percentage_within_bounds(self, analyzer):
        """Test that affected percentages are within valid bounds."""
        scenario = analyzer.analyze_partial_outage(
            resource_id="test-001",
            resource_name="test",
            resource_type="load_balancer",
            affected_zones=["zone-a"],
        )
        
        for outcome in scenario.outcomes:
            # Affected percentage should be 0-100
            assert 0.0 <= outcome.affected_percentage <= 100.0
    
    def test_mitigation_strategies_not_empty(self, analyzer):
        """Test that all scenarios provide mitigation strategies."""
        scenarios = [
            analyzer.analyze_degraded_performance("test", "test", "database"),
            analyzer.analyze_intermittent_failure("test", "test", "web_app"),
            analyzer.analyze_partial_outage("test", "test", "aks"),
        ]
        
        for scenario in scenarios:
            assert len(scenario.mitigation_strategies) > 0
            # Strategies should be actionable (contain verbs)
            strategy_text = " ".join(scenario.mitigation_strategies).lower()
            assert any(verb in strategy_text for verb in [
                "implement", "add", "configure", "set up", "deploy", "enable"
            ])
    
    def test_monitoring_recommendations_not_empty(self, analyzer):
        """Test that all scenarios provide monitoring recommendations."""
        scenarios = [
            analyzer.analyze_degraded_performance("test", "test", "redis_cache"),
            analyzer.analyze_intermittent_failure("test", "test", "api_gateway"),
            analyzer.analyze_partial_outage("test", "test", "load_balancer"),
        ]
        
        for scenario in scenarios:
            assert len(scenario.monitoring_recommendations) > 0
            # Monitoring should mention metrics or alerts
            monitoring_text = " ".join(scenario.monitoring_recommendations).lower()
            assert any(word in monitoring_text for word in [
                "monitor", "alert", "track", "metric", "latency", "error"
            ])
    
    def test_overall_impact_calculation(self, analyzer):
        """Test overall impact level calculation logic."""
        # Create scenarios with different severity levels
        low_impact = analyzer.analyze_intermittent_failure(
            "test", "test", "web_app", failure_frequency=0.01
        )
        high_impact = analyzer.analyze_partial_outage(
            "test", "test", "database", affected_zones=["zone-a", "zone-b"]
        )
        
        # Different scenarios should potentially have different impact levels
        # (This is probabilistic, but generally should hold)
        # We're mainly checking the calculation doesn't error
        assert low_impact.overall_impact in ImpactLevel
        assert high_impact.overall_impact in ImpactLevel
