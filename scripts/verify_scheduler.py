#!/usr/bin/env python3
"""
Verify that the automated discovery scheduler is configured correctly.

This script checks the configuration and verifies that the scheduler
can be initialized without errors.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from topdeck.common.config import settings
from topdeck.common.scheduler import DiscoveryScheduler


def check_credentials():
    """Check which cloud providers have valid credentials."""
    print("\n" + "=" * 60)
    print("CREDENTIAL CHECK")
    print("=" * 60)
    
    providers_configured = []
    
    # Check Azure
    if settings.enable_azure_discovery:
        has_creds = bool(
            settings.azure_tenant_id
            and settings.azure_client_id
            and settings.azure_client_secret
            and settings.azure_subscription_id
        )
        status = "✓ Configured" if has_creds else "✗ Missing credentials"
        print(f"\nAzure Discovery: {status}")
        if has_creds:
            providers_configured.append("azure")
            print(f"  Tenant ID: {settings.azure_tenant_id[:8]}...")
            print(f"  Client ID: {settings.azure_client_id[:8]}...")
            print(f"  Subscription ID: {settings.azure_subscription_id[:8]}...")
    else:
        print("\nAzure Discovery: Disabled")
    
    # Check AWS
    if settings.enable_aws_discovery:
        has_creds = bool(
            settings.aws_access_key_id and settings.aws_secret_access_key
        )
        status = "✓ Configured" if has_creds else "✗ Missing credentials"
        print(f"\nAWS Discovery: {status}")
        if has_creds:
            providers_configured.append("aws")
            print(f"  Access Key ID: {settings.aws_access_key_id[:8]}...")
            print(f"  Region: {settings.aws_region}")
    else:
        print("\nAWS Discovery: Disabled")
    
    # Check GCP
    if settings.enable_gcp_discovery:
        has_creds = bool(
            settings.google_application_credentials and settings.gcp_project_id
        )
        status = "✓ Configured" if has_creds else "✗ Missing credentials"
        print(f"\nGCP Discovery: {status}")
        if has_creds:
            providers_configured.append("gcp")
            print(f"  Credentials Path: {settings.google_application_credentials}")
            print(f"  Project ID: {settings.gcp_project_id}")
    else:
        print("\nGCP Discovery: Disabled")
    
    return providers_configured


def check_scheduler_config():
    """Check scheduler configuration."""
    print("\n" + "=" * 60)
    print("SCHEDULER CONFIGURATION")
    print("=" * 60)
    
    interval_hours = settings.discovery_scan_interval // 3600
    print(f"\nScan Interval: {interval_hours} hours ({settings.discovery_scan_interval} seconds)")
    print(f"Parallel Workers: {settings.discovery_parallel_workers}")
    print(f"Timeout: {settings.discovery_timeout} seconds")


def check_scheduler_initialization():
    """Check if scheduler can be initialized."""
    print("\n" + "=" * 60)
    print("SCHEDULER INITIALIZATION TEST")
    print("=" * 60)
    
    try:
        scheduler = DiscoveryScheduler()
        print("\n✓ Scheduler initialized successfully")
        
        # Check if discovery should run
        should_run = scheduler._should_run_discovery()
        if should_run:
            print("✓ Discovery will run automatically (credentials configured)")
        else:
            print("⚠ Discovery will NOT run (no credentials configured)")
            print("  Configure cloud provider credentials in .env to enable discovery")
        
        return True
    except Exception as e:
        print(f"\n✗ Failed to initialize scheduler: {e}")
        return False


def check_neo4j_config():
    """Check Neo4j configuration."""
    print("\n" + "=" * 60)
    print("NEO4J CONFIGURATION")
    print("=" * 60)
    
    print(f"\nURI: {settings.neo4j_uri}")
    print(f"Username: {settings.neo4j_username}")
    print(f"Password: {'*' * len(settings.neo4j_password) if settings.neo4j_password else '(not set)'}")
    
    if not settings.neo4j_password:
        print("\n⚠ Warning: Neo4j password not set")
        print("  Set NEO4J_PASSWORD in .env file")


def main():
    """Main entry point."""
    print("=" * 60)
    print("TOPDECK AUTOMATED DISCOVERY VERIFICATION")
    print("=" * 60)
    
    # Check credentials
    providers_configured = check_credentials()
    
    # Check scheduler config
    check_scheduler_config()
    
    # Check Neo4j config
    check_neo4j_config()
    
    # Check scheduler initialization
    success = check_scheduler_initialization()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if success and providers_configured:
        print(f"\n✓ Scheduler is ready!")
        print(f"✓ Discovery enabled for: {', '.join(providers_configured).upper()}")
        print(f"✓ Scans will run every {settings.discovery_scan_interval // 3600} hours")
        print("\nTo start the API server with automated discovery:")
        print("  make run")
        print("\nOr:")
        print("  python -m topdeck")
        return 0
    elif success and not providers_configured:
        print("\n⚠ Scheduler is ready but no cloud providers are configured")
        print("\nTo enable discovery, configure credentials in .env:")
        print("  - Azure: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID")
        print("  - AWS: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("  - GCP: GOOGLE_APPLICATION_CREDENTIALS, GCP_PROJECT_ID")
        return 0
    else:
        print("\n✗ Scheduler initialization failed")
        print("\nPlease check the errors above and fix the configuration")
        return 1


if __name__ == "__main__":
    sys.exit(main())
