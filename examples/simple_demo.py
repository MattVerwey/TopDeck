"""
Simple demonstration of Phase 2 and Phase 3 features.

This demo shows the key patterns and APIs without requiring external dependencies.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import only what we need without triggering pydantic
from topdeck.common.resilience import (
    RateLimiter,
    retry_with_backoff,
    RetryConfig,
    ErrorTracker,
)
from topdeck.common.logging_config import (
    setup_logging,
    get_logger,
    set_correlation_id,
    LoggingContext,
    log_operation_metrics,
)


async def demo_rate_limiting():
    """Demonstrate rate limiting."""
    print("\n" + "=" * 70)
    print("RATE LIMITING DEMO")
    print("=" * 70)
    print("\nRate limiter allows max 5 calls per 2 seconds")
    print("Watch how calls 6-7 wait...\n")
    
    limiter = RateLimiter(max_calls=5, time_window=2.0)
    
    for i in range(7):
        print(f"[{i+1}] Requesting permission to make API call...")
        await limiter.acquire()
        print(f"[{i+1}] ✓ Permission granted, making call")
    
    print("\n✓ Rate limiting successful")


async def demo_retry_logic():
    """Demonstrate retry with exponential backoff."""
    print("\n" + "=" * 70)
    print("RETRY LOGIC DEMO")
    print("=" * 70)
    print("\nFunction will fail twice, then succeed on 3rd try")
    print("Watch the exponential backoff delays...\n")
    
    attempt_count = 0
    
    @retry_with_backoff(
        config=RetryConfig(
            max_attempts=3,
            initial_delay=0.5,
            max_delay=5.0,
        )
    )
    async def flaky_operation():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  Attempt {attempt_count}...")
        
        if attempt_count < 3:
            print(f"  ✗ Failed!")
            raise ConnectionError("Simulated transient error")
        
        print(f"  ✓ Success!")
        return "completed"
    
    result = await flaky_operation()
    print(f"\n✓ Operation {result} after {attempt_count} attempts")


async def demo_error_tracking():
    """Demonstrate error tracking for batch operations."""
    print("\n" + "=" * 70)
    print("ERROR TRACKING DEMO")
    print("=" * 70)
    print("\nProcessing 10 items, some will fail...")
    print("Error tracker continues despite failures\n")
    
    tracker = ErrorTracker()
    items = [f"item-{i}" for i in range(1, 11)]
    
    for item in items:
        try:
            # Simulate processing with some failures
            if item in ["item-3", "item-5", "item-8"]:
                raise ValueError(f"Failed to process {item}")
            
            print(f"  Processing {item}... ✓")
            tracker.record_success(item)
            await asyncio.sleep(0.05)
        
        except Exception as e:
            print(f"  Processing {item}... ✗ {e}")
            tracker.record_error(item, e)
    
    # Show summary
    summary = tracker.get_summary()
    print(f"\nResults:")
    print(f"  Total items:  {summary['total']}")
    print(f"  Successful:   {summary['success']}")
    print(f"  Failed:       {summary['failure']}")
    print(f"  Success rate: {(1 - summary['error_rate']) * 100:.1f}%")


async def demo_structured_logging():
    """Demonstrate structured logging."""
    print("\n" + "=" * 70)
    print("STRUCTURED LOGGING DEMO")
    print("=" * 70)
    print("\nLogs with correlation IDs and context...")
    print("(Set json_format=True for JSON output)\n")
    
    # Set up logging
    setup_logging(level="INFO", json_format=False)
    logger = get_logger(__name__, context={"component": "demo"})
    
    # Set correlation ID
    set_correlation_id("demo-request-001")
    
    # Log some operations
    logger.info("Starting discovery workflow")
    
    with LoggingContext(operation="discover", resource_type="repository"):
        logger.info("Discovering repositories")
        await asyncio.sleep(0.1)
        logger.info("Found 42 repositories")
    
    with LoggingContext(operation="discover", resource_type="deployment"):
        logger.info("Discovering deployments")
        await asyncio.sleep(0.1)
        logger.info("Found 156 deployments")
    
    # Log metrics
    log_operation_metrics(
        operation="discovery_workflow",
        duration=0.2,
        success=True,
        items_processed=198,
        errors=0,
    )
    
    logger.info("Discovery workflow complete")
    print("\n✓ Logging demonstration complete")


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print(" TOPDECK PHASE 2 & 3 FEATURES DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows the new resilience patterns and logging features")
    print("added in Phase 2 (Enhanced Discovery) and Phase 3 (Production Ready)")
    
    try:
        await demo_rate_limiting()
        await demo_retry_logic()
        await demo_error_tracking()
        await demo_structured_logging()
        
        print("\n" + "=" * 70)
        print(" ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nThese patterns are used throughout TopDeck for:")
        print("  • Azure DevOps API integration")
        print("  • Resource discovery operations")
        print("  • External API calls")
        print("  • Batch processing workflows")
        print("\nSee docs/PHASE_2_3_IMPLEMENTATION.md for more details.")
        print("=" * 70 + "\n")
    
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
