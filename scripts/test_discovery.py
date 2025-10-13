#!/usr/bin/env python3
"""
Test Azure resource discovery.

This script tests the TopDeck Azure discovery functionality
against the deployed test infrastructure.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from azure.identity import ClientSecretCredential


async def test_discovery():
    """Test Azure resource discovery."""
    # Load environment
    load_dotenv()
    
    # Get credentials
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("TEST_RESOURCE_GROUP", "topdeck-test-rg")
    
    # Validate credentials
    if not all([tenant_id, client_id, client_secret, subscription_id]):
        print("❌ Error: Azure credentials not configured")
        print("   Please set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET,")
        print("   and AZURE_SUBSCRIPTION_ID in your .env file")
        sys.exit(1)
    
    print("=" * 70)
    print("🔍 TopDeck Azure Resource Discovery Test")
    print("=" * 70)
    print()
    print(f"   Subscription: {subscription_id}")
    print(f"   Resource Group: {resource_group}")
    print()
    
    try:
        # Import here to avoid loading if credentials are missing
        from topdeck.discovery.azure.discoverer import AzureDiscoverer
        
        # Create credential
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        
        # Create discoverer
        print("📡 Initializing Azure discoverer...")
        discoverer = AzureDiscoverer(credential, subscription_id)
        print("✓ Discoverer initialized")
        print()
        
        # Discover resources
        print("🔄 Starting resource discovery...")
        result = await discoverer.discover_resources(resource_group_filter=resource_group)
        print("✓ Discovery complete")
        print()
        
        # Display summary
        print("=" * 70)
        print("📊 DISCOVERY RESULTS")
        print("=" * 70)
        print()
        print(f"✅ Resources found: {result.resource_count}")
        print(f"✅ Dependencies found: {result.dependency_count}")
        print(f"✅ Applications found: {result.application_count}")
        print(f"✅ Errors: {len(result.errors)}")
        print()
        
        # Show resources
        if result.resources:
            print("=" * 70)
            print("📦 DISCOVERED RESOURCES")
            print("=" * 70)
            print()
            
            # Group by type
            by_type = {}
            for resource in result.resources:
                rtype = resource.resource_type
                if rtype not in by_type:
                    by_type[rtype] = []
                by_type[rtype].append(resource)
            
            for rtype, resources in sorted(by_type.items()):
                print(f"\n{rtype} ({len(resources)}):")
                for resource in resources[:5]:  # Show first 5 of each type
                    print(f"   - {resource.name}")
                    if hasattr(resource, 'region') and resource.region:
                        print(f"     Region: {resource.region}")
                    if hasattr(resource, 'tags') and resource.tags:
                        print(f"     Tags: {len(resource.tags)} tags")
                if len(resources) > 5:
                    print(f"   ... and {len(resources) - 5} more")
        else:
            print("⚠️  No resources found")
            print("   Make sure Azure test infrastructure is deployed:")
            print("   cd scripts/azure-testing && ./deploy-test-infrastructure.sh")
        
        # Show dependencies
        if result.dependencies:
            print()
            print("=" * 70)
            print("🔗 DISCOVERED DEPENDENCIES")
            print("=" * 70)
            print()
            for dep in result.dependencies[:10]:  # Show first 10
                print(f"   {dep.source_id}")
                print(f"   └─> {dep.target_id} ({dep.relationship_type})")
            if len(result.dependencies) > 10:
                print(f"   ... and {len(result.dependencies) - 10} more")
        
        # Show errors if any
        if result.errors:
            print()
            print("=" * 70)
            print("⚠️  ERRORS")
            print("=" * 70)
            print()
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(result.errors) > 5:
                print(f"   ... and {len(result.errors) - 5} more")
        
        print()
        print("=" * 70)
        print("✅ Test completed successfully!")
        print("=" * 70)
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print()
        print(f"   {type(e).__name__}: {e}")
        print()
        print("Troubleshooting:")
        print("   1. Verify Azure credentials are correct")
        print("   2. Ensure service principal has Reader role")
        print("   3. Check that test resources are deployed")
        print("   4. Review docs/HOSTING_AND_TESTING_GUIDE.md")
        print()
        return 1


def main():
    """Main entry point."""
    return asyncio.run(test_discovery())


if __name__ == "__main__":
    sys.exit(main())
