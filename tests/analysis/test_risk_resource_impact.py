"""Tests for resource-based risk impact scoring."""

import pytest

from topdeck.analysis.risk.scoring import ResourceImpactCategory, RiskScorer


@pytest.fixture
def risk_scorer():
    """Create a risk scorer with default weights."""
    return RiskScorer()


class TestResourceImpactCategories:
    """Test resource impact category classification."""
    
    def test_entry_point_category(self, risk_scorer):
        """Test entry point resources are correctly categorized."""
        entry_points = ["api_gateway", "app_gateway", "load_balancer", "front_door"]
        
        for resource_type in entry_points:
            category = risk_scorer._get_impact_category(resource_type)
            assert category == ResourceImpactCategory.ENTRY_POINT, \
                f"{resource_type} should be categorized as ENTRY_POINT"
    
    def test_data_store_category(self, risk_scorer):
        """Test data store resources are correctly categorized."""
        data_stores = [
            "database", "sql_database", "cosmos_db", "redis_cache",
            "postgresql_server", "mysql_server"
        ]
        
        for resource_type in data_stores:
            category = risk_scorer._get_impact_category(resource_type)
            assert category == ResourceImpactCategory.DATA_STORE, \
                f"{resource_type} should be categorized as DATA_STORE"
    
    def test_infrastructure_category(self, risk_scorer):
        """Test infrastructure resources are correctly categorized."""
        infrastructure = ["aks", "eks", "gke_cluster", "kubernetes", "vm_scale_set"]
        
        for resource_type in infrastructure:
            category = risk_scorer._get_impact_category(resource_type)
            assert category == ResourceImpactCategory.INFRASTRUCTURE, \
                f"{resource_type} should be categorized as INFRASTRUCTURE"
    
    def test_messaging_category(self, risk_scorer):
        """Test messaging resources are correctly categorized."""
        messaging = [
            "servicebus_namespace", "servicebus_topic", 
            "servicebus_queue", "event_hub"
        ]
        
        for resource_type in messaging:
            category = risk_scorer._get_impact_category(resource_type)
            assert category == ResourceImpactCategory.MESSAGING, \
                f"{resource_type} should be categorized as MESSAGING"
    
    def test_security_category(self, risk_scorer):
        """Test security resources are correctly categorized."""
        security = ["key_vault", "authentication", "active_directory"]
        
        for resource_type in security:
            category = risk_scorer._get_impact_category(resource_type)
            assert category == ResourceImpactCategory.SECURITY, \
                f"{resource_type} should be categorized as SECURITY"
    
    def test_unknown_type_defaults_to_compute(self, risk_scorer):
        """Test unknown resource types default to COMPUTE category."""
        category = risk_scorer._get_impact_category("unknown_resource_type")
        assert category == ResourceImpactCategory.COMPUTE


class TestEnhancedCriticalityFactors:
    """Test enhanced criticality scoring based on resource type research."""
    
    def test_entry_point_high_criticality(self, risk_scorer):
        """Test entry points have high criticality (they block all downstream)."""
        # API Gateway should have very high base criticality
        score = risk_scorer.calculate_risk_score(
            dependency_count=1,
            dependents_count=5,
            resource_type="api_gateway",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Entry points should score high even with redundancy
        assert score >= 40, "API gateway should have high risk score due to entry point role"
    
    def test_key_vault_highest_criticality(self, risk_scorer):
        """Test Key Vault has highest criticality (credential leaks affect all)."""
        score = risk_scorer.calculate_risk_score(
            dependency_count=1,
            dependents_count=5,
            resource_type="key_vault",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Key Vault should have very high criticality
        assert score >= 50, "Key Vault should have very high risk score"
    
    def test_database_vs_storage_criticality(self, risk_scorer):
        """Test databases score higher than storage accounts."""
        db_score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="sql_database",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        storage_score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="blob_storage",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Databases contain business data, storage is usually backed up
        assert db_score > storage_score, \
            "Database should score higher than blob storage"
    
    def test_messaging_infrastructure_criticality(self, risk_scorer):
        """Test messaging infrastructure has appropriate criticality."""
        score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=8,
            resource_type="servicebus_namespace",
            is_single_point_of_failure=False,
            has_redundancy=False
        )
        
        # Service Bus is async communication backbone
        assert score >= 40, \
            "Service Bus namespace should have high criticality"
    
    def test_networking_lower_criticality(self, risk_scorer):
        """Test networking resources have lower criticality (usually redundant)."""
        vnet_score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="virtual_network",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # VNets are network infrastructure, usually redundant
        assert vnet_score < 30, \
            "Virtual network should have lower criticality than databases/gateways"


class TestCategoryMultiplierEffects:
    """Test that impact category multipliers work correctly."""
    
    def test_entry_point_multiplier_increases_score(self, risk_scorer):
        """Test entry point category increases criticality via multiplier."""
        # Compare entry point (API gateway) vs compute (web app) with same dependents
        gateway_score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="api_gateway",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        web_app_score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="web_app",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Gateway should score higher due to entry point multiplier
        assert gateway_score > web_app_score, \
            "Entry point should score higher than compute with same dependents"
    
    def test_security_category_high_multiplier(self, risk_scorer):
        """Test security resources get high multiplier."""
        # Key vault vs regular VM
        kv_score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=3,
            resource_type="key_vault",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        vm_score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=3,
            resource_type="vm",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        assert kv_score > vm_score * 2, \
            "Security resources should have significantly higher scores than VMs"


class TestResourceTypeSpecificScoring:
    """Test scoring for specific resource types based on research."""
    
    def test_aks_without_ha_high_risk(self, risk_scorer):
        """Test AKS without HA has high risk (hosts multiple services)."""
        score = risk_scorer.calculate_risk_score(
            dependency_count=3,
            dependents_count=10,
            resource_type="aks",
            is_single_point_of_failure=False,
            has_redundancy=False
        )
        
        # AKS hosts multiple workloads, failure cascades
        assert score >= 60, \
            "AKS without HA should have high risk score"
    
    def test_load_balancer_as_entry_point(self, risk_scorer):
        """Test load balancer treated as entry point."""
        score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=8,
            resource_type="load_balancer",
            is_single_point_of_failure=False,
            has_redundancy=False
        )
        
        # Load balancers are traffic routing entry points
        assert score >= 45, \
            "Load balancer should have high score as entry point"
    
    def test_cosmos_db_data_store_criticality(self, risk_scorer):
        """Test Cosmos DB has high criticality as mission-critical data store."""
        score = risk_scorer.calculate_risk_score(
            dependency_count=1,
            dependents_count=7,
            resource_type="cosmos_db",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Cosmos DB often holds mission-critical data
        assert score >= 40, \
            "Cosmos DB should have high criticality as data store"
    
    def test_event_hub_messaging_infrastructure(self, risk_scorer):
        """Test Event Hub as messaging infrastructure."""
        score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=6,
            resource_type="event_hub",
            is_single_point_of_failure=False,
            has_redundancy=False
        )
        
        # Event Hub is event streaming infrastructure
        assert score >= 35, \
            "Event Hub should have appropriate criticality for messaging"


class TestBlastRadiusAwareness:
    """Test that scoring accounts for blast radius of different resource types."""
    
    def test_high_dependent_count_increases_score(self, risk_scorer):
        """Test resources with many dependents score higher."""
        low_dependents = risk_scorer.calculate_risk_score(
            dependency_count=1,
            dependents_count=2,
            resource_type="database",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        high_dependents = risk_scorer.calculate_risk_score(
            dependency_count=1,
            dependents_count=15,
            resource_type="database",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # More dependents = larger blast radius
        assert high_dependents > low_dependents + 15, \
            "High dependent count should significantly increase risk"
    
    def test_spof_with_high_dependents_critical(self, risk_scorer):
        """Test SPOF with many dependents reaches critical level."""
        score = risk_scorer.calculate_risk_score(
            dependency_count=1,
            dependents_count=12,
            resource_type="database",
            is_single_point_of_failure=True,
            has_redundancy=False
        )
        
        # SPOF + high dependents = critical risk
        assert score >= 75, \
            "SPOF with many dependents should reach critical risk level"


class TestRedundancyImpact:
    """Test how redundancy affects different resource types."""
    
    def test_infrastructure_redundancy_major_impact(self, risk_scorer):
        """Test infrastructure resources benefit greatly from redundancy."""
        no_ha = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=8,
            resource_type="aks",
            is_single_point_of_failure=False,
            has_redundancy=False
        )
        
        with_ha = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=8,
            resource_type="aks",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Infrastructure should see major reduction with HA
        reduction = no_ha - with_ha
        assert reduction >= 20, \
            f"Infrastructure should see major risk reduction with HA, got {reduction}"
    
    def test_entry_point_redundancy_impact(self, risk_scorer):
        """Test entry points benefit from redundancy."""
        no_redundancy = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=10,
            resource_type="api_gateway",
            is_single_point_of_failure=False,
            has_redundancy=False
        )
        
        with_redundancy = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=10,
            resource_type="api_gateway",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Redundancy should reduce risk
        assert with_redundancy < no_redundancy, \
            "Redundancy should reduce entry point risk"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_unknown_resource_type_gets_default(self, risk_scorer):
        """Test unknown resource types get reasonable default score."""
        score = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="unknown_new_service",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Should get default criticality + compute multiplier
        assert 10 <= score <= 50, \
            "Unknown types should get moderate default score"
    
    def test_zero_dependents_still_scores_on_type(self, risk_scorer):
        """Test resources with no dependents still score based on type."""
        # Key vault with no recorded dependents should still be high
        score = risk_scorer.calculate_risk_score(
            dependency_count=1,
            dependents_count=0,
            resource_type="key_vault",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # Base criticality of key vault should still result in medium score
        assert score >= 30, \
            "Security resources should score high even without recorded dependents"
    
    def test_case_insensitive_type_matching(self, risk_scorer):
        """Test resource type matching is case-insensitive."""
        score_lower = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="api_gateway",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        score_upper = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="API_GATEWAY",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        score_mixed = risk_scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=5,
            resource_type="Api_Gateway",
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        # All should produce the same score
        assert score_lower == score_upper == score_mixed, \
            "Resource type matching should be case-insensitive"
