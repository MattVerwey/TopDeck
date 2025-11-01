#!/usr/bin/env python
"""
Enhanced Dependency Analysis Demo

Demonstrates the new dependency analysis features:
- Circular dependency detection
- Dependency health scoring
- Risk comparison
- Cascading failure probability

This example shows how to use these features to improve infrastructure health.
"""

import sys
from typing import Any

import requests


class DependencyAnalysisDemo:
    """Demo class for enhanced dependency analysis features."""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """Initialize demo with API base URL."""
        self.api_base_url = api_base_url
        self.session = requests.Session()

    def _make_request(self, endpoint: str) -> dict[str, Any] | None:
        """Make API request and handle errors."""
        try:
            response = self.session.get(f"{self.api_base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ Error calling {endpoint}: {e}")
            return None

    def detect_circular_dependencies(self, resource_id: str = None) -> None:
        """Demonstrate circular dependency detection."""
        print("\n" + "=" * 80)
        print("🔄 CIRCULAR DEPENDENCY DETECTION")
        print("=" * 80)

        if resource_id:
            endpoint = f"/api/v1/risk/dependencies/circular?resource_id={resource_id}"
            print(f"\nChecking resource: {resource_id}")
        else:
            endpoint = "/api/v1/risk/dependencies/circular"
            print("\nScanning entire infrastructure...")

        result = self._make_request(endpoint)
        if not result:
            return

        print(f"\n📊 Results:")
        print(f"   Circular dependencies found: {result['circular_dependencies_found']}")
        print(f"   Severity: {result['severity'].upper()}")

        if result["cycles"]:
            print(f"\n⚠️  Detected {len(result['cycles'])} circular dependency path(s):")
            for i, cycle in enumerate(result["cycles"], 1):
                print(f"\n   Cycle {i}:")
                cycle_str = " → ".join(cycle[:-1]) + f" → {cycle[0]}"
                print(f"   {cycle_str}")

            print("\n💡 Recommendations:")
            for rec in result["recommendations"]:
                print(f"   • {rec}")
        else:
            print("\n✅ No circular dependencies found - infrastructure is healthy!")

    def check_dependency_health(self, resource_id: str) -> None:
        """Demonstrate dependency health scoring."""
        print("\n" + "=" * 80)
        print("🏥 DEPENDENCY HEALTH ANALYSIS")
        print("=" * 80)
        print(f"\nAnalyzing resource: {resource_id}")

        result = self._make_request(f"/api/v1/risk/dependencies/{resource_id}/health")
        if not result:
            return

        # Display health score
        health_score = result["health_score"]
        health_level = result["health_level"]

        # Color-code the output based on health level
        emoji_map = {
            "excellent": "🟢",
            "good": "🟡",
            "fair": "🟠",
            "poor": "🔴",
            "critical": "⚠️ ",
        }
        emoji = emoji_map.get(health_level, "⚪")

        print(f"\n📊 Health Score: {health_score}/100 {emoji} ({health_level.upper()})")

        # Display factors
        if result["factors"]:
            print(f"\n⚠️  Issues Found:")
            for factor_name, factor_data in result["factors"].items():
                print(f"\n   {factor_name.replace('_', ' ').title()}:")
                print(f"   • {factor_data['reason']}")
                print(f"   • Penalty: {factor_data['penalty']} points")

                # Show additional details
                if "cycles" in factor_data:
                    print(f"   • Affected cycles: {len(factor_data['cycles'])}")
                if "resources" in factor_data:
                    print(f"   • Affected resources: {len(factor_data['resources'])}")
        else:
            print("\n✅ No significant issues detected!")

        # Display recommendations
        print(f"\n💡 Recommendations:")
        for rec in result["recommendations"]:
            print(f"   • {rec}")

    def compare_resources(self, resource_ids: list[str]) -> None:
        """Demonstrate risk comparison across resources."""
        print("\n" + "=" * 80)
        print("📊 RISK COMPARISON ANALYSIS")
        print("=" * 80)
        print(f"\nComparing {len(resource_ids)} resources...")

        ids_param = ",".join(resource_ids)
        result = self._make_request(f"/api/v1/risk/compare?resource_ids={ids_param}")
        if not result:
            return

        # Summary statistics
        print(f"\n📈 Summary:")
        print(f"   Resources compared: {result['resources_compared']}")
        print(f"   Average risk score: {result['average_risk_score']:.1f}")

        # Highest risk
        highest = result["highest_risk"]
        print(f"\n🔴 Highest Risk:")
        print(f"   Resource: {highest['resource_name']} ({highest['resource_id']})")
        print(f"   Risk Score: {highest['risk_score']:.1f}")
        print(f"   Risk Level: {highest['risk_level'].upper()}")

        # Lowest risk
        lowest = result["lowest_risk"]
        print(f"\n🟢 Lowest Risk:")
        print(f"   Resource: {lowest['resource_name']} ({lowest['resource_id']})")
        print(f"   Risk Score: {lowest['risk_score']:.1f}")
        print(f"   Risk Level: {lowest['risk_level'].upper()}")

        # Distribution
        dist = result["risk_distribution"]
        print(f"\n📊 Risk Distribution:")
        print(f"   Critical: {dist['critical']}")
        print(f"   High: {dist['high']}")
        print(f"   Medium: {dist['medium']}")
        print(f"   Low: {dist['low']}")

        # Common factors
        if result["common_risk_factors"]:
            print(f"\n⚠️  Common Risk Factors:")
            for factor in result["common_risk_factors"]:
                print(f"   • {factor}")

        # All assessments
        print(f"\n📋 All Resources (sorted by risk):")
        for assessment in result["all_assessments"]:
            spof_indicator = "⚠️  SPOF" if assessment["is_spof"] else ""
            print(
                f"   • {assessment['resource_name']}: "
                f"{assessment['risk_score']:.1f} ({assessment['risk_level']}) {spof_indicator}"
            )

    def analyze_cascading_failure(
        self, resource_id: str, initial_probability: float = 1.0
    ) -> None:
        """Demonstrate cascading failure probability analysis."""
        print("\n" + "=" * 80)
        print("⚡ CASCADING FAILURE PROBABILITY ANALYSIS")
        print("=" * 80)
        print(f"\nAnalyzing resource: {resource_id}")
        print(f"Initial failure probability: {initial_probability * 100:.0f}%")

        result = self._make_request(
            f"/api/v1/risk/cascading-failure/{resource_id}"
            f"?initial_probability={initial_probability}"
        )
        if not result:
            return

        # Summary
        summary = result["summary"]
        print(f"\n📊 Summary:")
        print(f"   Maximum cascade depth: {summary['max_cascade_depth']} levels")
        print(f"   Total resources at risk: {summary['total_resources_at_risk']}")
        print(f"   Expected failures: {summary['expected_failures']:.2f} resources")

        # Detailed cascade levels
        if result["levels"]:
            print(f"\n🔍 Cascade Details:")
            for level in result["levels"]:
                print(f"\n   Level {level['level']}:")
                print(f"   Failure probability: {level['failure_probability'] * 100:.1f}%")
                print(f"   Affected resources ({len(level['affected_resources'])}):")

                for resource in level["affected_resources"][:5]:  # Show first 5
                    print(
                        f"      • {resource['resource_name']} ({resource['resource_type']}): "
                        f"{resource['failure_probability'] * 100:.1f}% failure risk"
                    )

                if len(level["affected_resources"]) > 5:
                    remaining = len(level["affected_resources"]) - 5
                    print(f"      ... and {remaining} more")
        else:
            print("\n✅ No cascading impact detected!")

        # Recommendations
        print(f"\n💡 Recommendations:")
        for rec in summary["recommendations"]:
            print(f"   • {rec}")


def get_sample_resources(api_base_url: str, limit: int = 3) -> tuple[str | None, list[str]]:
    """
    Fetch sample resources from the API.
    
    Returns:
        Tuple of (first_resource_id, list_of_resource_ids)
    """
    try:
        response = requests.get(f"{api_base_url}/api/v1/topology", timeout=5)
        response.raise_for_status()
        topology = response.json()
        
        if "nodes" in topology and topology["nodes"]:
            # Get resource IDs from topology
            resource_ids = [node["id"] for node in topology["nodes"][:limit]]
            return resource_ids[0] if resource_ids else None, resource_ids
    except Exception as e:
        print(f"⚠️  Could not fetch resources from API: {e}")
    
    return None, []


def main():
    """Run the demo."""
    print("\n" + "=" * 80)
    print("🚀 ENHANCED DEPENDENCY ANALYSIS DEMO")
    print("=" * 80)
    print("\nThis demo showcases TopDeck's advanced dependency analysis features.")
    print("Make sure the TopDeck API server is running on http://localhost:8000")

    # Initialize demo
    demo = DependencyAnalysisDemo()

    # Try to fetch actual resource IDs from the API
    print("\n🔍 Fetching sample resources from API...")
    example_resource_id, example_resources = get_sample_resources(demo.api_base_url)
    
    if not example_resource_id:
        print("\n⚠️  No resources found in the system.")
        print("   This demo requires resources to be discovered first.")
        print("   Run resource discovery before using this demo:")
        print("   python -m topdeck.discovery.azure.discoverer --subscription-id <id>")
        print("\n   Or provide resource IDs manually by editing this script.")
        return

    print(f"✅ Found {len(example_resources)} sample resource(s)")
    print(f"   Using resource: {example_resource_id}")

    # 1. Check for circular dependencies
    demo.detect_circular_dependencies()

    # 2. Check dependency health for a specific resource
    demo.check_dependency_health(example_resource_id)

    # 3. Compare multiple resources (if we have more than one)
    if len(example_resources) > 1:
        demo.compare_resources(example_resources)
    else:
        print("\n⚠️  Skipping comparison - need at least 2 resources")

    # 4. Analyze cascading failure probability
    demo.analyze_cascading_failure(example_resource_id, initial_probability=1.0)

    print("\n" + "=" * 80)
    print("✅ Demo complete!")
    print("=" * 80)
    print("\nFor more information, see:")
    print("  • docs/ENHANCED_DEPENDENCY_ANALYSIS.md")
    print("  • docs/ENHANCED_RISK_ANALYSIS.md")
    print("  • http://localhost:8000/api/docs (API documentation)")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
