#!/usr/bin/env python3
"""
Health check script for TopDeck API.

This script checks if the TopDeck API server is running and responsive.
"""

import argparse
import sys
from typing import Any

import httpx


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Check TopDeck API health")
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="API host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API port (default: 8000)",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed health information including service dependencies",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Request timeout in seconds (default: 5)",
    )
    return parser.parse_args()


def check_basic_health(url: str, timeout: int) -> tuple[bool, dict[str, Any]]:
    """
    Check basic health endpoint.

    Args:
        url: Base URL of the API
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success, response_data)
    """
    try:
        response = httpx.get(f"{url}/health", timeout=timeout)
        response.raise_for_status()
        return True, response.json()
    except httpx.RequestError as e:
        return False, {"error": f"Connection error: {e}"}
    except httpx.HTTPStatusError as e:
        return False, {"error": f"HTTP error: {e.response.status_code}"}
    except Exception as e:
        return False, {"error": f"Unexpected error: {e}"}


def check_detailed_health(url: str, timeout: int) -> tuple[bool, dict[str, Any]]:
    """
    Check detailed health endpoint.

    Args:
        url: Base URL of the API
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success, response_data)
    """
    try:
        response = httpx.get(f"{url}/health/detailed", timeout=timeout)
        response.raise_for_status()
        return True, response.json()
    except httpx.RequestError as e:
        return False, {"error": f"Connection error: {e}"}
    except httpx.HTTPStatusError as e:
        return False, {"error": f"HTTP error: {e.response.status_code}"}
    except Exception as e:
        return False, {"error": f"Unexpected error: {e}"}


def print_health_status(data: dict[str, Any], detailed: bool = False) -> None:
    """
    Print health check results.

    Args:
        data: Health check response data
        detailed: Whether to print detailed information
    """
    if "error" in data:
        print(f"❌ Health Check Failed: {data['error']}")
        return

    if detailed:
        print("🏥 TopDeck API Health Check (Detailed)")
        print("=" * 60)
        print(f"Overall Status: {data.get('status', 'unknown').upper()}")
        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        print()

        components = data.get("components", {})
        for name, component in components.items():
            status = component.get("status", "unknown")
            emoji = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
            print(f"{emoji} {name.upper()}: {status}")
            if component.get("message"):
                print(f"   Message: {component['message']}")
            if component.get("response_time_ms") is not None:
                print(f"   Response Time: {component['response_time_ms']}ms")
            if component.get("details"):
                for key, value in component["details"].items():
                    print(f"   {key}: {value}")
            print()
    else:
        status = data.get("status", "unknown")
        emoji = "✅" if status == "healthy" else "❌"
        print(f"{emoji} TopDeck API Status: {status.upper()}")


def main() -> None:
    """Main entry point."""
    args = parse_args()
    url = f"http://{args.host}:{args.port}"

    print(f"🔍 Checking TopDeck API at {url}...")
    print()

    if args.detailed:
        success, data = check_detailed_health(url, args.timeout)
    else:
        success, data = check_basic_health(url, args.timeout)

    print_health_status(data, args.detailed)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
