#!/usr/bin/env python3
"""
Demonstration of Enhanced Resource-Based Risk Scoring

This script demonstrates the enhanced risk scoring methodology based on
research into cloud resource types, their failure modes, and downstream impacts.
"""

from topdeck.analysis.risk.scoring import RiskScorer, ResourceImpactCategory


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def demonstrate_impact_categories():
    """Demonstrate resource impact category classification."""
    print_section("Resource Impact Categories")
    
    scorer = RiskScorer()
    
    # Test various resource types
    test_resources = {
        "Entry Points": ["api_gateway", "load_balancer", "front_door"],
        "Security": ["key_vault", "authentication"],
        "Data Stores": ["sql_database", "cosmos_db", "redis_cache"],
        "Infrastructure": ["aks", "eks", "vm_scale_set"],
        "Messaging": ["servicebus_namespace", "event_hub"],
        "Compute": ["web_app", "function_app", "vm"],
        "Storage": ["blob_storage", "storage_account"],
        "Networking": ["virtual_network", "vpn_gateway"]
    }
    
    for category_name, resources in test_resources.items():
        print(f"{category_name}:")
        for resource_type in resources:
            category = scorer._get_impact_category(resource_type)
            criticality = scorer.CRITICALITY_FACTORS.get(resource_type.lower(), 10)
            print(f"  - {resource_type:30} | Category: {category.value:15} | Base: {criticality:2}")
        print()


def demonstrate_scoring_scenarios():
    """Demonstrate risk scoring for various realistic scenarios."""
    print_section("Risk Scoring Scenarios")
    
    scorer = RiskScorer()
    
    scenarios = [
        {
            "name": "Production API Gateway (No HA)",
            "resource_type": "api_gateway",
            "dependents_count": 15,
            "is_spof": True,
            "has_redundancy": False,
            "description": "Central API gateway without high availability"
        },
        {
            "name": "Production API Gateway (With HA)",
            "resource_type": "api_gateway",
            "dependents_count": 15,
            "is_spof": False,
            "has_redundancy": True,
            "description": "Central API gateway with redundancy across AZs"
        },
        {
            "name": "Critical Database (With Replicas)",
            "resource_type": "sql_database",
            "dependents_count": 12,
            "is_spof": False,
            "has_redundancy": True,
            "description": "Production database with read replicas"
        },
        {
            "name": "Critical Database (Single Instance)",
            "resource_type": "sql_database",
            "dependents_count": 12,
            "is_spof": True,
            "has_redundancy": False,
            "description": "Production database without redundancy"
        },
        {
            "name": "Key Vault (No Redundancy)",
            "resource_type": "key_vault",
            "dependents_count": 20,
            "is_spof": True,
            "has_redundancy": False,
            "description": "Central secrets management without geo-replication"
        },
        {
            "name": "AKS Cluster (Single Zone)",
            "resource_type": "aks",
            "dependents_count": 25,
            "is_spof": True,
            "has_redundancy": False,
            "description": "Kubernetes cluster without multi-zone deployment"
        },
        {
            "name": "AKS Cluster (Multi-Zone)",
            "resource_type": "aks",
            "dependents_count": 25,
            "is_spof": False,
            "has_redundancy": True,
            "description": "Kubernetes cluster across availability zones"
        },
        {
            "name": "Service Bus Namespace",
            "resource_type": "servicebus_namespace",
            "dependents_count": 10,
            "is_spof": True,
            "has_redundancy": False,
            "description": "Message infrastructure for async communication"
        },
        {
            "name": "Individual Function App",
            "resource_type": "function_app",
            "dependents_count": 3,
            "is_spof": False,
            "has_redundancy": True,
            "description": "Serverless function with auto-scaling"
        },
        {
            "name": "Blob Storage Account",
            "resource_type": "blob_storage",
            "dependents_count": 5,
            "is_spof": False,
            "has_redundancy": True,
            "description": "Object storage with geo-redundancy"
        }
    ]
    
    for scenario in scenarios:
        score = scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=scenario["dependents_count"],
            resource_type=scenario["resource_type"],
            is_single_point_of_failure=scenario["is_spof"],
            has_redundancy=scenario["has_redundancy"]
        )
        
        risk_level = scorer.get_risk_level(score)
        
        print(f"Scenario: {scenario['name']}")
        print(f"  Description: {scenario['description']}")
        print(f"  Resource Type: {scenario['resource_type']}")
        print(f"  Dependents: {scenario['dependents_count']}")
        print(f"  SPOF: {scenario['is_spof']}")
        print(f"  Has Redundancy: {scenario['has_redundancy']}")
        print(f"  → Risk Score: {score:.2f} ({risk_level.value.upper()})")
        
        recommendations = scorer.generate_recommendations(
            risk_score=score,
            is_spof=scenario["is_spof"],
            has_redundancy=scenario["has_redundancy"],
            dependents_count=scenario["dependents_count"],
            deployment_failure_rate=0.05
        )
        
        if recommendations:
            print("  Recommendations:")
            for rec in recommendations[:3]:  # Top 3
                print(f"    • {rec}")
        print()


def demonstrate_category_multipliers():
    """Demonstrate how impact category multipliers affect scores."""
    print_section("Impact Category Multiplier Effects")
    
    scorer = RiskScorer()
    
    # Compare same dependents, different categories
    test_cases = [
        ("api_gateway", "Entry Point", ResourceImpactCategory.ENTRY_POINT),
        ("key_vault", "Security", ResourceImpactCategory.SECURITY),
        ("sql_database", "Data Store", ResourceImpactCategory.DATA_STORE),
        ("aks", "Infrastructure", ResourceImpactCategory.INFRASTRUCTURE),
        ("servicebus_namespace", "Messaging", ResourceImpactCategory.MESSAGING),
        ("web_app", "Compute (Baseline)", ResourceImpactCategory.COMPUTE),
        ("blob_storage", "Storage", ResourceImpactCategory.STORAGE),
        ("virtual_network", "Networking", ResourceImpactCategory.NETWORKING),
    ]
    
    dependents = 8
    
    print(f"All resources with {dependents} dependents, no SPOF, with redundancy:\n")
    print(f"{'Resource Type':<25} {'Category':<20} {'Base':<6} {'Score':<8} {'Level':<10}")
    print("-" * 75)
    
    for resource_type, category_name, expected_category in test_cases:
        score = scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=dependents,
            resource_type=resource_type,
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        risk_level = scorer.get_risk_level(score)
        base = scorer.CRITICALITY_FACTORS.get(resource_type.lower(), 10)
        
        print(f"{resource_type:<25} {category_name:<20} {base:<6} {score:<8.2f} {risk_level.value.upper():<10}")


def demonstrate_redundancy_impact():
    """Demonstrate how redundancy affects different resource types."""
    print_section("Redundancy Impact on Different Resource Types")
    
    scorer = RiskScorer()
    
    test_resources = [
        ("api_gateway", "API Gateway"),
        ("aks", "AKS Cluster"),
        ("sql_database", "SQL Database"),
        ("servicebus_namespace", "Service Bus"),
        ("web_app", "Web App")
    ]
    
    dependents = 10
    
    print(f"All resources with {dependents} dependents, SPOF status:\n")
    print(f"{'Resource':<20} {'Without Redundancy':<20} {'With Redundancy':<18} {'Reduction':<10}")
    print("-" * 70)
    
    for resource_type, display_name in test_resources:
        score_no_ha = scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=dependents,
            resource_type=resource_type,
            is_single_point_of_failure=True,
            has_redundancy=False
        )
        
        score_with_ha = scorer.calculate_risk_score(
            dependency_count=2,
            dependents_count=dependents,
            resource_type=resource_type,
            is_single_point_of_failure=False,
            has_redundancy=True
        )
        
        reduction = score_no_ha - score_with_ha
        reduction_pct = (reduction / score_no_ha * 100) if score_no_ha > 0 else 0
        
        print(f"{display_name:<20} {score_no_ha:<20.2f} {score_with_ha:<18.2f} {reduction:.2f} ({reduction_pct:.0f}%)")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("  Enhanced Resource-Based Risk Scoring Demonstration")
    print("  Based on Industry Research and Cloud Best Practices")
    print("=" * 80)
    
    demonstrate_impact_categories()
    demonstrate_scoring_scenarios()
    demonstrate_category_multipliers()
    demonstrate_redundancy_impact()
    
    print("\n" + "=" * 80)
    print("  For detailed methodology, see: docs/RISK_SCORING_METHODOLOGY.md")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
