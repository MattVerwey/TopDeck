"""
Multi-Cloud Discovery Example

This example demonstrates how to discover resources from Azure, AWS, and GCP
simultaneously and store them in Neo4j with proper formatting.
"""

import asyncio
from datetime import datetime
from typing import Dict, List

from topdeck.common.config import Settings
from topdeck.discovery.azure import AzureDiscoverer
from topdeck.discovery.aws import AWSDiscoverer
from topdeck.discovery.gcp import GCPDiscoverer
from topdeck.discovery.models import DiscoveryResult
from topdeck.storage.neo4j_client import Neo4jClient


class MultiCloudDiscovery:
    """
    Orchestrates resource discovery across multiple cloud providers.
    """

    def __init__(self, settings: Settings):
        """
        Initialize multi-cloud discovery.

        Args:
            settings: Application settings with cloud credentials
        """
        self.settings = settings
        self.neo4j = None

    def connect_neo4j(self) -> None:
        """Connect to Neo4j database."""
        self.neo4j = Neo4jClient(
            self.settings.neo4j_uri,
            self.settings.neo4j_username,
            self.settings.neo4j_password,
        )
        self.neo4j.connect()
        print(f"✓ Connected to Neo4j at {self.settings.neo4j_uri}")

    async def discover_azure(self) -> DiscoveryResult:
        """
        Discover Azure resources.

        Returns:
            DiscoveryResult with Azure resources
        """
        print("\n🔍 Discovering Azure resources...")

        discoverer = AzureDiscoverer(
            subscription_id=self.settings.azure_subscription_id,
            tenant_id=self.settings.azure_tenant_id,
            client_id=self.settings.azure_client_id,
            client_secret=self.settings.azure_client_secret,
        )

        result = await discoverer.discover_all_resources()
        print(f"  Found {len(result.resources)} Azure resources")

        return result

    async def discover_aws(self) -> DiscoveryResult:
        """
        Discover AWS resources.

        Returns:
            DiscoveryResult with AWS resources
        """
        print("\n🔍 Discovering AWS resources...")

        discoverer = AWSDiscoverer(
            access_key_id=self.settings.aws_access_key_id,
            secret_access_key=self.settings.aws_secret_access_key,
            region=self.settings.aws_region,
        )

        result = await discoverer.discover_all_resources()
        print(f"  Found {len(result.resources)} AWS resources")

        return result

    async def discover_gcp(self) -> DiscoveryResult:
        """
        Discover GCP resources.

        Returns:
            DiscoveryResult with GCP resources
        """
        print("\n🔍 Discovering GCP resources...")

        discoverer = GCPDiscoverer(
            project_id=self.settings.gcp_project_id,
            credentials_path=self.settings.google_application_credentials,
        )

        result = await discoverer.discover_all_resources()
        print(f"  Found {len(result.resources)} GCP resources")

        return result

    async def discover_all_sequential(self) -> Dict[str, DiscoveryResult]:
        """
        Discover resources from all enabled clouds sequentially.

        Returns:
            Dictionary mapping cloud provider to discovery results
        """
        results = {}

        if self.settings.enable_azure_discovery:
            results["azure"] = await self.discover_azure()

        if self.settings.enable_aws_discovery:
            results["aws"] = await self.discover_aws()

        if self.settings.enable_gcp_discovery:
            results["gcp"] = await self.discover_gcp()

        return results

    async def discover_all_parallel(self) -> Dict[str, DiscoveryResult]:
        """
        Discover resources from all enabled clouds in parallel.

        Returns:
            Dictionary mapping cloud provider to discovery results
        """
        tasks = []
        cloud_names = []

        if self.settings.enable_azure_discovery:
            tasks.append(self.discover_azure())
            cloud_names.append("azure")

        if self.settings.enable_aws_discovery:
            tasks.append(self.discover_aws())
            cloud_names.append("aws")

        if self.settings.enable_gcp_discovery:
            tasks.append(self.discover_gcp())
            cloud_names.append("gcp")

        print("\n⚡ Running parallel discovery across all clouds...")
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for cloud, result in zip(cloud_names, results_list):
            if isinstance(result, Exception):
                print(f"  ❌ {cloud.upper()}: {str(result)}")
            else:
                results[cloud] = result

        return results

    def store_in_neo4j(self, results: Dict[str, DiscoveryResult]) -> None:
        """
        Store discovered resources in Neo4j.

        Args:
            results: Dictionary of discovery results per cloud
        """
        if not self.neo4j:
            raise RuntimeError("Neo4j not connected. Call connect_neo4j() first.")

        print("\n💾 Storing resources in Neo4j...")

        total_stored = 0
        for cloud, result in results.items():
            print(f"\n  {cloud.upper()}:")

            # Store resources
            for resource in result.resources:
                try:
                    neo4j_props = resource.to_neo4j_properties()
                    self.neo4j.upsert_resource(neo4j_props)
                    total_stored += 1
                except Exception as e:
                    print(f"    ❌ Failed to store {resource.name}: {str(e)}")

            print(f"    ✓ Stored {len(result.resources)} resources")

            # Store dependencies
            for dependency in result.dependencies:
                try:
                    self.neo4j.create_dependency(
                        dependency.source_id,
                        dependency.target_id,
                        dependency.to_neo4j_properties(),
                    )
                except Exception as e:
                    print(f"    ❌ Failed to store dependency: {str(e)}")

        print(f"\n✓ Total stored: {total_stored} resources")

    def print_summary(self, results: Dict[str, DiscoveryResult]) -> None:
        """
        Print summary of discovered resources.

        Args:
            results: Dictionary of discovery results per cloud
        """
        print("\n" + "=" * 60)
        print("DISCOVERY SUMMARY")
        print("=" * 60)

        for cloud, result in results.items():
            print(f"\n{cloud.upper()}:")
            print(f"  Resources: {len(result.resources)}")
            print(f"  Dependencies: {len(result.dependencies)}")
            print(f"  Applications: {len(result.applications)}")

            # Group by resource type
            type_counts = {}
            for resource in result.resources:
                type_counts[resource.resource_type] = (
                    type_counts.get(resource.resource_type, 0) + 1
                )

            if type_counts:
                print("\n  Resource Types:")
                for rtype, count in sorted(
                    type_counts.items(), key=lambda x: x[1], reverse=True
                ):
                    print(f"    - {rtype}: {count}")

        print("\n" + "=" * 60)


async def main():
    """Main entry point for multi-cloud discovery."""
    print("=" * 60)
    print("TopDeck Multi-Cloud Discovery")
    print("=" * 60)

    # Load configuration
    settings = Settings()

    # Initialize discovery
    discovery = MultiCloudDiscovery(settings)

    # Connect to Neo4j
    try:
        discovery.connect_neo4j()
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {str(e)}")
        return

    # Discover resources (choose parallel or sequential)
    try:
        # Option 1: Parallel discovery (faster)
        results = await discovery.discover_all_parallel()

        # Option 2: Sequential discovery (more controlled)
        # results = await discovery.discover_all_sequential()

    except Exception as e:
        print(f"❌ Discovery failed: {str(e)}")
        return

    # Store in Neo4j
    try:
        discovery.store_in_neo4j(results)
    except Exception as e:
        print(f"❌ Failed to store in Neo4j: {str(e)}")

    # Print summary
    discovery.print_summary(results)

    print("\n✓ Multi-cloud discovery complete!")


if __name__ == "__main__":
    asyncio.run(main())
