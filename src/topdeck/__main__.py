"""TopDeck CLI entry point."""

import argparse
import sys

import uvicorn

from topdeck import __version__
from topdeck.common.config import settings


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="TopDeck - Multi-Cloud Integration & Risk Analysis Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start with default settings
  %(prog)s --port 8080              # Start on port 8080
  %(prog)s --host 127.0.0.1         # Bind to localhost only
  %(prog)s --log-level DEBUG        # Enable debug logging
  %(prog)s --no-reload              # Disable auto-reload in development
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"TopDeck v{__version__}",
        help="show program version and exit",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="bind socket to this host (default: 0.0.0.0)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=settings.app_port,
        help=f"bind socket to this port (default: {settings.app_port})",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=settings.log_level,
        help=f"logging level (default: {settings.log_level})",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        default=None,
        help="enable auto-reload (overrides environment setting)",
    )

    parser.add_argument(
        "--no-reload",
        action="store_true",
        default=False,
        help="disable auto-reload (overrides environment setting)",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="number of worker processes (default: 1)",
    )

    return parser.parse_args()


def main() -> None:
    """Run the TopDeck API server."""
    args = parse_args()

    # Determine reload setting
    if args.no_reload:
        reload = False
    elif args.reload:
        reload = True
    else:
        reload = settings.app_env == "development"

    print(f"🚀 Starting TopDeck API v{__version__}")
    print(f"   Environment: {settings.app_env}")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Log Level: {args.log_level}")
    print(f"   Auto-reload: {reload}")
    print(f"   Workers: {args.workers}")
    print()

    try:
        uvicorn.run(
            "topdeck.api.main:app",
            host=args.host,
            port=args.port,
            reload=reload,
            log_level=args.log_level.lower(),
            workers=args.workers if not reload else 1,  # Workers incompatible with reload
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down TopDeck API")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting TopDeck API: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
