#!/usr/bin/env python3
"""
Demonstration of improved change impact analysis.

This script shows how the enhanced change impact analysis now produces
different results based on resource characteristics, not just change type.
"""

from topdeck.change_management.models import ChangeType
from topdeck.change_management.service import ChangeManagementService


def demonstrate_improved_impact_analysis():
    """
    Demonstrate how change impact now varies by resource characteristics.
    """
    # Note: This creates a service without actual Neo4j connection for demonstration
    # In real usage, you would pass a connected Neo4jClient
    service = ChangeManagementService(neo4j_client=None)

    print("=" * 80)
    print("Change Impact Analysis Improvements Demonstration")
    print("=" * 80)
    print()

    # Scenario 1: DEPLOYMENT change on different resource types
    print("Scenario 1: DEPLOYMENT change on different resource types")
    print("-" * 80)

    db_downtime = service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "database",
        risk_score=60.0,
        dependent_count=10,
        is_critical=True,
    )

    webapp_downtime = service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "web_app",
        risk_score=60.0,
        dependent_count=10,
        is_critical=False,
    )

    func_downtime = service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "function_app",
        risk_score=60.0,
        dependent_count=10,
        is_critical=False,
    )

    print(f"  Database (critical):     {db_downtime:5d} seconds ({db_downtime/60:.1f} minutes)")
    print(
        f"  Web App (standard):      {webapp_downtime:5d} seconds ({webapp_downtime/60:.1f} minutes)"
    )
    print(
        f"  Function App (standard): {func_downtime:5d} seconds ({func_downtime/60:.1f} minutes)"
    )
    print()
    print(
        f"  Impact: Database takes {db_downtime/func_downtime:.1f}x longer than Function App"
    )
    print()

    # Scenario 2: Same resource, different risk scores
    print("Scenario 2: Same resource type, different risk scores")
    print("-" * 80)

    low_risk = service._estimate_downtime_for_resource(
        ChangeType.UPDATE,
        "web_app",
        risk_score=20.0,
        dependent_count=5,
        is_critical=False,
    )

    med_risk = service._estimate_downtime_for_resource(
        ChangeType.UPDATE,
        "web_app",
        risk_score=50.0,
        dependent_count=5,
        is_critical=False,
    )

    high_risk = service._estimate_downtime_for_resource(
        ChangeType.UPDATE,
        "web_app",
        risk_score=85.0,
        dependent_count=5,
        is_critical=False,
    )

    print(f"  Low risk (score 20):  {low_risk:5d} seconds ({low_risk/60:.1f} minutes)")
    print(f"  Med risk (score 50):  {med_risk:5d} seconds ({med_risk/60:.1f} minutes)")
    print(f"  High risk (score 85): {high_risk:5d} seconds ({high_risk/60:.1f} minutes)")
    print()
    print(f"  Impact: High risk takes {high_risk/low_risk:.1f}x longer than low risk")
    print()

    # Scenario 3: Impact of dependencies
    print("Scenario 3: Same resource, different dependency counts")
    print("-" * 80)

    no_deps = service._estimate_downtime_for_resource(
        ChangeType.CONFIGURATION,
        "api_gateway",
        risk_score=50.0,
        dependent_count=0,
        is_critical=False,
    )

    few_deps = service._estimate_downtime_for_resource(
        ChangeType.CONFIGURATION,
        "api_gateway",
        risk_score=50.0,
        dependent_count=5,
        is_critical=False,
    )

    many_deps = service._estimate_downtime_for_resource(
        ChangeType.CONFIGURATION,
        "api_gateway",
        risk_score=50.0,
        dependent_count=25,
        is_critical=False,
    )

    print(
        f"  No dependents:     {no_deps:5d} seconds ({no_deps/60:.1f} minutes)"
    )
    print(
        f"  5 dependents:      {few_deps:5d} seconds ({few_deps/60:.1f} minutes)"
    )
    print(
        f"  25 dependents:     {many_deps:5d} seconds ({many_deps/60:.1f} minutes)"
    )
    print()
    print(f"  Impact: 25 deps takes {many_deps/no_deps:.1f}x longer than 0 deps")
    print()

    # Scenario 4: Change type risk multipliers
    print("Scenario 4: Different change types on same resource")
    print("-" * 80)

    restart_risk = service._get_change_type_risk_multiplier(ChangeType.RESTART)
    deploy_risk = service._get_change_type_risk_multiplier(ChangeType.DEPLOYMENT)
    infra_risk = service._get_change_type_risk_multiplier(ChangeType.INFRASTRUCTURE)
    emergency_risk = service._get_change_type_risk_multiplier(ChangeType.EMERGENCY)

    print(f"  Restart change:         {restart_risk:.2f}x risk multiplier")
    print(f"  Deployment change:      {deploy_risk:.2f}x risk multiplier")
    print(f"  Infrastructure change:  {infra_risk:.2f}x risk multiplier")
    print(f"  Emergency change:       {emergency_risk:.2f}x risk multiplier")
    print()

    # Scenario 5: Performance impact estimation
    print("Scenario 5: Performance impact by risk score")
    print("-" * 80)

    perf_20 = service._estimate_performance_impact(20.0)
    perf_50 = service._estimate_performance_impact(50.0)
    perf_80 = service._estimate_performance_impact(80.0)

    print(f"  Risk score 20:  {perf_20:.1f}% performance degradation")
    print(f"  Risk score 50:  {perf_50:.1f}% performance degradation")
    print(f"  Risk score 80:  {perf_80:.1f}% performance degradation")
    print()

    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("The improved change impact analysis now considers:")
    print("  1. Resource type (databases take longer than function apps)")
    print("  2. Risk score (higher risk = more careful = longer changes)")
    print("  3. Dependencies (more coordination needed)")
    print("  4. Critical path status (critical resources need extra care)")
    print("  5. Change type inherent risk (emergency > infrastructure > restart)")
    print("  6. Specific change+resource combinations (e.g., database updates)")
    print()
    print("This ensures that 'live data shows DIFFERENT impact' based on")
    print("actual resource characteristics, not just the change type!")
    print()


if __name__ == "__main__":
    demonstrate_improved_impact_analysis()
