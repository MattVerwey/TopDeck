"""
Error Replay Demo Script

Demonstrates the error replay feature by simulating error scenarios
and showing how to capture, search, and replay errors.

Usage:
    python examples/error_replay_demo.py
"""

import asyncio
from datetime import UTC, datetime, timedelta

from topdeck.monitoring.error_replay import (
    ErrorReplayService,
    ErrorSearchFilter,
    ErrorSeverity,
    ErrorSource,
)
from topdeck.storage.neo4j_client import Neo4jClient


async def demo_basic_error_capture(service: ErrorReplayService) -> str:
    """Demo: Capture a basic error."""
    print("\n=== Demo 1: Capture a Basic Error ===\n")

    error = await service.capture_error(
        message="Database connection timeout after 30 seconds",
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_id="sql-db-prod-001",
        resource_type="database",
        error_type="connection_timeout",
        tags={"environment": "production", "region": "us-west-2"},
    )

    print(f"✅ Error captured with ID: {error.error_id}")
    print(f"   Timestamp: {error.timestamp}")
    print(f"   Severity: {error.severity.value}")
    print(f"   Message: {error.message}")
    print(f"   Resource: {error.resource_id}")
    print(f"   Logs collected: {len(error.logs)}")
    print(f"   Related errors: {len(error.related_errors)}")
    print(f"   Affected resources: {len(error.affected_resources)}")

    return error.error_id


async def demo_error_with_trace_info(service: ErrorReplayService) -> str:
    """Demo: Capture error with distributed trace information."""
    print("\n=== Demo 2: Capture Error with Trace Information ===\n")

    error = await service.capture_error(
        message="API Gateway timeout calling downstream service",
        severity=ErrorSeverity.MEDIUM,
        source=ErrorSource.APPLICATION,
        resource_id="api-gateway-prod",
        resource_type="api_gateway",
        error_type="downstream_timeout",
        correlation_id="corr-abc-123-def",
        trace_id="trace-456-789-ghi",
        span_id="span-001",
        stack_trace="""
Traceback (most recent call last):
  File "api_gateway.py", line 42, in handle_request
    response = await downstream_service.call()
  File "downstream.py", line 15, in call
    raise TimeoutError("Service did not respond in time")
TimeoutError: Service did not respond in time
        """.strip(),
        tags={"service": "api-gateway", "endpoint": "/api/users"},
        metadata={"request_id": "req-xyz-789", "user_id": "user-12345"},
    )

    print(f"✅ Error captured with ID: {error.error_id}")
    print(f"   Correlation ID: {error.correlation_id}")
    print(f"   Trace ID: {error.trace_id}")
    print(f"   Has stack trace: {error.stack_trace is not None}")
    print(f"   Tags: {error.tags}")

    return error.error_id


async def demo_error_replay(service: ErrorReplayService, error_id: str) -> None:
    """Demo: Replay an error to understand what happened."""
    print("\n=== Demo 3: Replay an Error ===\n")

    try:
        result = await service.replay_error(error_id)

        print(f"🔄 Replaying error: {result.error_id}")
        print(f"   Original timestamp: {result.original_timestamp}")

        print("\n📅 Timeline of events:")
        for i, event in enumerate(result.timeline[:5], 1):  # Show first 5 events
            print(f"   {i}. [{event['timestamp']}] {event['type']}: {event.get('message', 'N/A')}")

        if len(result.timeline) > 5:
            print(f"   ... and {len(result.timeline) - 5} more events")

        print("\n🔍 Root Cause Analysis:")
        rca = result.root_cause_analysis
        print(f"   Primary cause: {rca['primary_cause']}")
        print(f"   Confidence: {rca['confidence'] * 100:.0f}%")
        if rca["contributing_factors"]:
            print("   Contributing factors:")
            for factor in rca["contributing_factors"]:
                print(f"     - {factor}")

        print("\n💡 Recommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"   {i}. {rec}")

    except ValueError as e:
        print(f"❌ Error not found: {e}")


async def demo_search_errors(service: ErrorReplayService) -> None:
    """Demo: Search for errors with different filters."""
    print("\n=== Demo 4: Search for Errors ===\n")

    # Search by severity
    print("🔍 Searching for HIGH severity errors...")
    filter = ErrorSearchFilter(severity=ErrorSeverity.HIGH, limit=5)
    errors = await service.search_errors(filter)
    print(f"   Found {len(errors)} high severity errors")
    for error in errors:
        print(f"   - {error.error_id}: {error.message}")

    # Search by time range
    print("\n🔍 Searching for errors in last hour...")
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=1)
    filter = ErrorSearchFilter(start_time=start_time, end_time=end_time, limit=10)
    errors = await service.search_errors(filter)
    print(f"   Found {len(errors)} errors in last hour")

    # Search by resource
    print("\n🔍 Searching for errors on sql-db-prod-001...")
    filter = ErrorSearchFilter(resource_id="sql-db-prod-001", limit=5)
    errors = await service.search_errors(filter)
    print(f"   Found {len(errors)} errors on this resource")


async def demo_error_statistics(service: ErrorReplayService) -> None:
    """Demo: Get error statistics."""
    print("\n=== Demo 5: Error Statistics ===\n")

    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)

    stats = await service.get_error_statistics(start_time, end_time)

    print(f"📊 Error statistics for last 24 hours:")
    print(f"   Total errors: {stats['total_errors']}")
    print(f"   Severities: {', '.join(stats['severities'])}")
    print(f"   Sources: {', '.join(stats['sources'])}")
    print(f"   Resource types: {', '.join(stats['resource_types'])}")
    if stats["error_types"]:
        print(f"   Error types: {', '.join(stats['error_types'])}")


async def demo_cascading_failures(service: ErrorReplayService) -> None:
    """Demo: Capture and trace cascading failures."""
    print("\n=== Demo 6: Cascading Failures ===\n")

    correlation_id = "cascade-demo-001"

    # Simulate a cascading failure scenario
    print("🔥 Simulating cascading failure scenario...")

    # Initial failure in database
    error1 = await service.capture_error(
        message="Database deadlock detected",
        severity=ErrorSeverity.CRITICAL,
        source=ErrorSource.APPLICATION,
        resource_id="sql-db-prod-001",
        resource_type="database",
        error_type="deadlock",
        correlation_id=correlation_id,
        tags={"cascade": "initial"},
    )
    print(f"   1. Database error: {error1.error_id}")

    # API service fails due to database issue
    await asyncio.sleep(0.1)  # Small delay to simulate propagation
    error2 = await service.capture_error(
        message="API request failed - database unavailable",
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_id="api-service-prod",
        resource_type="api",
        error_type="service_unavailable",
        correlation_id=correlation_id,
        tags={"cascade": "secondary"},
    )
    print(f"   2. API service error: {error2.error_id}")

    # Web application fails due to API issue
    await asyncio.sleep(0.1)
    error3 = await service.capture_error(
        message="Web page timeout - API not responding",
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_id="web-app-prod",
        resource_type="web_app",
        error_type="timeout",
        correlation_id=correlation_id,
        tags={"cascade": "tertiary"},
    )
    print(f"   3. Web app error: {error3.error_id}")

    # Search for all related errors
    print(f"\n🔗 Searching for all errors with correlation ID: {correlation_id}")
    filter = ErrorSearchFilter(correlation_id=correlation_id)
    related_errors = await service.search_errors(filter)

    print(f"   Found {len(related_errors)} related errors:")
    for i, error in enumerate(related_errors, 1):
        print(f"   {i}. [{error.severity.value}] {error.resource_id}: {error.message}")

    print("\n💡 This demonstrates how error replay can trace cascading failures")
    print("   across multiple services using correlation IDs.")


async def main() -> None:
    """Run all demos."""
    print("=" * 70)
    print("Error Replay Feature Demo")
    print("=" * 70)

    # Initialize service
    print("\n🔧 Initializing Error Replay Service...")
    neo4j_client = Neo4jClient(
        uri="bolt://localhost:7687", username="neo4j", password="topdeck123"
    )

    service = ErrorReplayService(
        neo4j_client=neo4j_client,
        prometheus_url="http://localhost:9090",
        loki_url="http://localhost:3100",
    )
    print("✅ Service initialized")

    # Run demos
    try:
        # Demo 1: Basic error capture
        error_id_1 = await demo_basic_error_capture(service)

        # Demo 2: Error with trace info
        await demo_error_with_trace_info(service)

        # Demo 3: Replay an error
        await demo_error_replay(service, error_id_1)

        # Demo 4: Search for errors
        await demo_search_errors(service)

        # Demo 5: Error statistics
        await demo_error_statistics(service)

        # Demo 6: Cascading failures
        await demo_cascading_failures(service)

    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("✅ Errors are captured with full context automatically")
    print("✅ You can replay any past error to debug what happened")
    print("✅ Search and filter errors by multiple criteria")
    print("✅ Trace cascading failures using correlation IDs")
    print("✅ Get actionable recommendations for fixing issues")
    print("\n📚 See docs/ERROR_REPLAY_GUIDE.md for complete documentation")


if __name__ == "__main__":
    asyncio.run(main())
