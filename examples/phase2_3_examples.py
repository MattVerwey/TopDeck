"""
Examples demonstrating Phase 2 and Phase 3 features.

These examples show how to use the new Azure DevOps integration,
specialized resource discovery, and resilience patterns.

NOTE: This script demonstrates the API. To run it, you need to install dependencies:
  pip install -r requirements.txt
"""

import asyncio
from datetime import datetime
import sys
import os

# Add src to path for direct imports without package initialization
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Phase 2: Azure DevOps Integration
async def example_azure_devops_discovery():
    """Example: Discover repositories and deployments from Azure DevOps."""
    from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer
    
    # Initialize discoverer with PAT
    discoverer = AzureDevOpsDiscoverer(
        organization="myorg",
        project="myproject",
        personal_access_token="your-pat-token-here"
    )
    
    try:
        # Discover repositories
        print("Discovering repositories...")
        repositories = await discoverer.discover_repositories()
        
        for repo in repositories:
            print(f"\nRepository: {repo.name}")
            print(f"  URL: {repo.url}")
            print(f"  Default branch: {repo.default_branch}")
            print(f"  Last commit: {repo.last_commit_sha}")
        
        # Discover recent deployments
        print("\n\nDiscovering deployments...")
        deployments = await discoverer.discover_deployments(limit=10)
        
        for deployment in deployments:
            print(f"\nDeployment: {deployment.version}")
            print(f"  Pipeline: {deployment.pipeline_name}")
            print(f"  Status: {deployment.status}")
            print(f"  Deployed at: {deployment.deployed_at}")
            print(f"  Deployed by: {deployment.deployed_by}")
        
        # Discover applications
        print("\n\nDiscovering applications...")
        applications = await discoverer.discover_applications()
        
        for app in applications:
            print(f"\nApplication: {app.name}")
            print(f"  Environment: {app.environment}")
            print(f"  Repository: {app.repository_url}")
            print(f"  Deployment method: {app.deployment_method}")
    
    finally:
        # Clean up
        await discoverer.close()


# Phase 3: Resilience Patterns
async def example_resilience_patterns():
    """Example: Use resilience patterns for reliable API calls."""
    from topdeck.common.resilience import (
        RateLimiter,
        retry_with_backoff,
        RetryConfig,
        ErrorTracker,
    )
    
    # Rate limiting
    print("Example: Rate Limiting")
    limiter = RateLimiter(max_calls=5, time_window=10.0)
    
    for i in range(7):
        print(f"Making request {i+1}...")
        await limiter.acquire()
        print(f"  Request {i+1} sent")
    
    # Retry with backoff
    print("\n\nExample: Retry with Backoff")
    
    attempt_count = 0
    
    @retry_with_backoff(
        config=RetryConfig(
            max_attempts=3,
            initial_delay=0.5,
            max_delay=5.0,
        )
    )
    async def unreliable_operation():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  Attempt {attempt_count}")
        
        if attempt_count < 2:
            raise ConnectionError("Simulated failure")
        
        return "success"
    
    result = await unreliable_operation()
    print(f"  Result: {result}")
    
    # Error tracking
    print("\n\nExample: Error Tracking")
    tracker = ErrorTracker()
    
    items = ["item1", "item2", "item3", "item4", "item5"]
    
    for item in items:
        try:
            # Simulate some items failing
            if item in ["item2", "item4"]:
                raise ValueError(f"Processing {item} failed")
            
            # Process item
            print(f"  Processing {item}... success")
            tracker.record_success(item)
        
        except Exception as e:
            print(f"  Processing {item}... failed: {e}")
            tracker.record_error(item, e)
    
    # Get summary
    summary = tracker.get_summary()
    print(f"\nSummary:")
    print(f"  Total: {summary['total']}")
    print(f"  Success: {summary['success']}")
    print(f"  Failed: {summary['failure']}")
    print(f"  Error rate: {summary['error_rate']:.2%}")


# Phase 3: Structured Logging
async def example_structured_logging():
    """Example: Use structured logging with correlation IDs."""
    from topdeck.common.logging_config import (
        setup_logging,
        get_logger,
        set_correlation_id,
        LoggingContext,
        log_operation_metrics,
    )
    import time
    
    # Set up logging (JSON format)
    setup_logging(level="INFO", json_format=False)  # Set to True for JSON
    
    # Get logger
    logger = get_logger(__name__, context={"component": "example"})
    
    # Set correlation ID for request tracing
    set_correlation_id("example-request-123")
    
    # Log with context
    logger.info("Starting discovery operation")
    
    with LoggingContext(operation="discovery", resource_type="repository"):
        logger.info("Discovering repositories")
        
        # Simulate work
        await asyncio.sleep(0.1)
        
        logger.info("Discovery complete")
    
    # Log operation metrics
    start_time = time.time()
    
    # Simulate operation
    await asyncio.sleep(0.2)
    items_processed = 42
    errors = 3
    
    duration = time.time() - start_time
    
    log_operation_metrics(
        operation="discover_repositories",
        duration=duration,
        success=True,
        items_processed=items_processed,
        errors=errors,
        custom_metric="example value"
    )


# Main
async def main():
    """Run all examples."""
    print("=" * 70)
    print("Phase 2 & 3 Examples")
    print("=" * 70)
    
    print("\n\n1. Resilience Patterns")
    print("-" * 70)
    await example_resilience_patterns()
    
    print("\n\n2. Structured Logging")
    print("-" * 70)
    await example_structured_logging()
    
    print("\n\nNote: Azure examples require credentials and are commented out.")
    print("See the source code for Azure DevOps and resource discovery examples.")


if __name__ == "__main__":
    asyncio.run(main())
