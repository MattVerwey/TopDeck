"""TopDeck CLI entry point."""

import uvicorn

from topdeck import __version__
from topdeck.common.config import settings


def main() -> None:
    """Run the TopDeck API server."""
    print(f"🚀 Starting TopDeck API v{__version__}")
    print(f"   Environment: {settings.app_env}")
    print(f"   Port: {settings.app_port}")
    print(f"   Log Level: {settings.log_level}")
    print()

    uvicorn.run(
        "topdeck.api.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
