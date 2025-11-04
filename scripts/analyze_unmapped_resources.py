#!/usr/bin/env python3
"""
Analyze Unmapped Azure Resources

This script analyzes discovered Azure resources and reports which resource types
are currently unmapped (showing as "unknown"). This helps identify which resource
types need to be added to the mapper.

Usage:
    python scripts/analyze_unmapped_resources.py --subscription-id <sub-id>

Environment variables (for authentication):
    AZURE_TENANT_ID
    AZURE_CLIENT_ID
    AZURE_CLIENT_SECRET
"""

import argparse
import asyncio
import os
import sys
from collections import Counter
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from topdeck.discovery.azure import AzureDiscoverer
from topdeck.discovery.azure.mapper import AzureResourceMapper


async def analyze_unmapped_resources(subscription_id: str, tenant_id: str | None = None,
                                      client_id: str | None = None, client_secret: str | None = None):
    """
    Discover Azure resources and analyze which types are unmapped.
    
    Args:
        subscription_id: Azure subscription ID
        tenant_id: Azure tenant ID (optional, uses DefaultAzureCredential if not provided)
        client_id: Azure client ID (optional)
        client_secret: Azure client secret (optional)
    """
    print("=" * 80)
    print("Azure Resource Type Analysis")
    print("=" * 80)
    print(f"\nSubscription ID: {subscription_id}")
    
    # Initialize discoverer
    discoverer = AzureDiscoverer(
        subscription_id=subscription_id,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    
    try:
        # Discover all resources
        print("\nDiscovering resources...")
        result = await discoverer.discover_all_resources()
        
        print(f"\nDiscovery completed!")
        print(f"Total resources discovered: {len(result.resources)}")
        
        # Analyze resource types
        resource_type_counts = Counter()
        unmapped_azure_types = Counter()
        
        for resource in result.resources:
            resource_type_counts[resource.resource_type] += 1
            
            # Check if this is an unmapped resource
            if resource.resource_type == "unknown":
                # Try to extract the Azure type from the resource ID
                # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/{type}/...
                parts = resource.id.split('/providers/')
                if len(parts) > 1:
                    azure_type_parts = parts[1].split('/')
                    if len(azure_type_parts) >= 2:
                        azure_type = f"{azure_type_parts[0]}/{azure_type_parts[1]}"
                        unmapped_azure_types[azure_type] += 1
        
        # Display results
        print("\n" + "=" * 80)
        print("Resource Type Distribution")
        print("=" * 80)
        
        # Sort by count (descending)
        sorted_types = sorted(resource_type_counts.items(), key=lambda x: x[1], reverse=True)
        
        unknown_count = resource_type_counts.get("unknown", 0)
        known_count = len(result.resources) - unknown_count
        
        print(f"\nKnown resource types: {known_count} resources")
        print(f"Unknown resource types: {unknown_count} resources")
        print(f"Mapping coverage: {(known_count / len(result.resources) * 100):.1f}%")
        
        if unknown_count > 0:
            print(f"\n⚠️  {unknown_count} resources are currently unmapped!")
        
        # Show top 10 mapped types
        print("\nTop 10 Mapped Resource Types:")
        print("-" * 80)
        count = 0
        for rtype, cnt in sorted_types:
            if rtype != "unknown":
                print(f"  {cnt:4d} × {rtype}")
                count += 1
                if count >= 10:
                    break
        
        # Show unmapped types
        if unmapped_azure_types:
            print("\n" + "=" * 80)
            print("Unmapped Azure Resource Types")
            print("=" * 80)
            print(f"\nFound {len(unmapped_azure_types)} unmapped resource type(s):\n")
            
            sorted_unmapped = sorted(unmapped_azure_types.items(), key=lambda x: x[1], reverse=True)
            for azure_type, cnt in sorted_unmapped:
                print(f"  {cnt:4d} × {azure_type}")
            
            print("\n" + "-" * 80)
            print("Recommended Actions:")
            print("-" * 80)
            print("1. Check Azure documentation for these resource types")
            print("2. Add mappings to src/topdeck/discovery/azure/mapper.py")
            print("3. Update the RESOURCE_TYPE_MAP dictionary with appropriate names")
            print("4. Run tests to verify: pytest tests/discovery/azure/test_mapper.py")
            print("\nExample mapping format:")
            print('  "Microsoft.Example/resourceType": "example_resource",')
        else:
            print("\n✓ All discovered resources are properly mapped!")
        
        # Check against current mappings
        print("\n" + "=" * 80)
        print("Mapper Statistics")
        print("=" * 80)
        total_mappings = len(AzureResourceMapper.RESOURCE_TYPE_MAP)
        print(f"\nTotal mappings in mapper: {total_mappings}")
        print(f"Resource types in use: {len(resource_type_counts) - (1 if unknown_count > 0 else 0)}")
        
    except Exception as e:
        print(f"\n❌ Error during discovery: {e}", file=sys.stderr)
        raise
    finally:
        await discoverer.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze unmapped Azure resources in a subscription"
    )
    parser.add_argument(
        "--subscription-id",
        required=True,
        help="Azure subscription ID",
    )
    parser.add_argument(
        "--tenant-id",
        help="Azure tenant ID (optional, uses env var AZURE_TENANT_ID or DefaultAzureCredential)",
    )
    parser.add_argument(
        "--client-id",
        help="Azure client ID (optional, uses env var AZURE_CLIENT_ID)",
    )
    parser.add_argument(
        "--client-secret",
        help="Azure client secret (optional, uses env var AZURE_CLIENT_SECRET)",
    )
    
    args = parser.parse_args()
    
    # Get credentials from args or environment
    tenant_id = args.tenant_id or os.getenv("AZURE_TENANT_ID")
    client_id = args.client_id or os.getenv("AZURE_CLIENT_ID")
    client_secret = args.client_secret or os.getenv("AZURE_CLIENT_SECRET")
    
    # Run the analysis
    asyncio.run(
        analyze_unmapped_resources(
            subscription_id=args.subscription_id,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
    )


if __name__ == "__main__":
    main()
