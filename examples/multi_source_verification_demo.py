#!/usr/bin/env python
"""
Multi-Source Dependency Verification Demo

Demonstrates how TopDeck verifies dependencies using multiple independent sources:
1. Azure infrastructure discovery (IPs, backends, network topology)
2. Azure DevOps code analysis (deployment configs, secrets, storage)
3. Prometheus metrics (actual traffic patterns)
4. Tempo traces (distributed transaction flows)

This comprehensive verification ensures dependency accuracy and catches false positives.
"""

import asyncio
import os
import sys
from typing import Any

import httpx


class MultiSourceVerificationDemo:
    """Demo class for multi-source dependency verification."""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """Initialize demo with API base URL."""
        self.api_base_url = api_base_url

    async def verify_dependency(
        self, source_id: str, target_id: str
    ) -> dict[str, Any] | None:
        """
        Verify a dependency using the multi-source verification API.

        Args:
            source_id: Source resource ID
            target_id: Target resource ID

        Returns:
            Verification result or None if error
        """
        endpoint = f"{self.api_base_url}/api/v1/dependencies/verify"
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "duration_hours": 24,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"❌ Error verifying dependency: {e}")
            return None

    async def get_sample_resources(self) -> tuple[str | None, str | None]:
        """
        Fetch sample resources from topology.

        Returns:
            Tuple of (source_id, target_id) or (None, None)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_base_url}/api/v1/topology")
                response.raise_for_status()
                topology = response.json()

                if "nodes" in topology and len(topology["nodes"]) >= 2:
                    return topology["nodes"][0]["id"], topology["nodes"][1]["id"]
        except Exception as e:
            print(f"⚠️  Could not fetch resources: {e}")

        return None, None

    def display_verification_result(self, result: dict[str, Any]) -> None:
        """Display verification result in a readable format."""
        print("\n" + "=" * 80)
        print("🔍 MULTI-SOURCE DEPENDENCY VERIFICATION RESULT")
        print("=" * 80)

        print(f"\n📌 Dependency:")
        print(f"   Source: {result['source_id']}")
        print(f"   Target: {result['target_id']}")

        # Verification status
        is_verified = result["is_verified"]
        status_emoji = "✅" if is_verified else "❌"
        print(f"\n{status_emoji} Verification Status: {'VERIFIED' if is_verified else 'NOT VERIFIED'}")

        # Scores
        print(f"\n📊 Verification Metrics:")
        print(f"   Overall Confidence: {result['overall_confidence']:.2%}")
        print(f"   Verification Score: {result['verification_score']:.2%}")

        # Evidence from each source
        if result.get("evidence"):
            print(f"\n🔬 Evidence Sources ({len(result['evidence'])} total):")

            source_emoji = {
                "azure_infrastructure": "🌐",
                "ado_code": "📝",
                "prometheus": "📈",
                "tempo": "🔄",
            }

            for evidence in result["evidence"]:
                emoji = source_emoji.get(evidence["source"], "•")
                print(f"\n   {emoji} {evidence['source'].upper()}")
                print(f"      Evidence Type: {evidence['evidence_type']}")
                print(f"      Confidence: {evidence['confidence']:.2%}")

                if "evidence_items" in evidence["details"]:
                    print(f"      Details:")
                    for item in evidence["details"]["evidence_items"]:
                        print(f"         • {item}")
        else:
            print("\n⚠️  No evidence found from any source")

        # Recommendations
        if result.get("recommendations"):
            print(f"\n💡 Recommendations:")
            for rec in result["recommendations"]:
                print(f"   • {rec}")

        print("\n" + "=" * 80)

    async def demo_verification_scenarios(self) -> None:
        """Demonstrate different verification scenarios."""
        print("\n" + "=" * 80)
        print("🚀 MULTI-SOURCE DEPENDENCY VERIFICATION DEMO")
        print("=" * 80)
        print("\nThis demo shows how TopDeck verifies dependencies using multiple")
        print("independent sources to ensure accuracy and catch false positives.")

        print("\n📋 Verification Sources:")
        print("   🌐 Azure Infrastructure - IPs, backends, network topology")
        print("   📝 Azure DevOps Code - deployment configs, secrets, storage")
        print("   📈 Prometheus Metrics - actual traffic patterns")
        print("   🔄 Tempo Traces - distributed transaction flows")

        # Try to get sample resources
        print("\n🔍 Fetching sample resources from topology...")
        source_id, target_id = await self.get_sample_resources()

        if not source_id or not target_id:
            print("\n⚠️  No resources found in the system.")
            print("   This demo requires resources to be discovered first.")
            print("\n   To discover Azure resources, run:")
            print("   python -m topdeck.discovery.azure.discoverer --subscription-id <id>")
            return

        print(f"✅ Found resources:")
        print(f"   Source: {source_id}")
        print(f"   Target: {target_id}")

        # Verify the dependency
        print("\n🔄 Running multi-source verification...")
        result = await self.verify_dependency(source_id, target_id)

        if result:
            self.display_verification_result(result)

            # Explain the verification
            print("\n📖 Understanding the Results:")
            print()
            print("   ✅ High Confidence (>70%): Dependency confirmed by multiple sources")
            print("   ⚠️  Medium Confidence (40-70%): Some evidence, needs more validation")
            print("   ❌ Low Confidence (<40%): Likely false positive or stale dependency")
            print()
            print("   The more sources that verify a dependency, the higher the confidence.")
            print("   Azure infrastructure evidence is weighted highest (most reliable).")
            print("   Tempo traces provide strong evidence of actual service communication.")

        print("\n" + "=" * 80)
        print("✅ Demo complete!")
        print("=" * 80)
        print("\nFor more information, see:")
        print("  • docs/DEPENDENCY_VERIFICATION.md")
        print("  • http://localhost:8000/api/docs (API documentation)")
        print()


async def main():
    """Run the demo."""
    # Check if API is available
    api_url = os.getenv("TOPDECK_API_URL", "http://localhost:8000")
    demo = MultiSourceVerificationDemo(api_url)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{api_url}/health")
            response.raise_for_status()
    except Exception as e:
        print(f"\n❌ Error: Cannot connect to TopDeck API at {api_url}")
        print(f"   {e}")
        print("\n   Make sure the TopDeck API server is running:")
        print("   make run")
        print("\n   Or set TOPDECK_API_URL environment variable")
        sys.exit(1)

    await demo.demo_verification_scenarios()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
