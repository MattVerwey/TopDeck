"""
API versioning support for TopDeck.

Provides a versioning strategy for the API to support backward compatibility
and gradual deprecation of old versions.
"""

from collections.abc import Callable

import structlog
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class APIVersion:
    """API version information."""

    V1 = "v1"
    V2 = "v2"
    LATEST = V1  # Current latest version

    @classmethod
    def all_versions(cls) -> list[str]:
        """Get all supported API versions."""
        return [cls.V1]

    @classmethod
    def is_valid(cls, version: str) -> bool:
        """Check if a version string is valid."""
        return version in cls.all_versions()


class VersionedAPIRoute:
    """Helper for creating versioned API routes."""

    @staticmethod
    def prefix(version: str) -> str:
        """
        Get the prefix for a versioned API route.

        Args:
            version: API version (e.g., "v1")

        Returns:
            Route prefix (e.g., "/api/v1")
        """
        if not APIVersion.is_valid(version):
            raise ValueError(f"Invalid API version: {version}")
        return f"/api/{version}"


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle API versioning.

    Extracts the API version from the URL path and validates it.
    Adds version information to the request state.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and extract API version."""
        path = request.url.path

        # Check if this is an API request
        if path.startswith("/api/"):
            # Extract version from path (e.g., /api/v1/...)
            parts = path.split("/")
            if len(parts) >= 3:
                potential_version = parts[2]

                # Check if it's a version string
                if potential_version.startswith("v"):
                    if not APIVersion.is_valid(potential_version):
                        logger.warning(
                            "invalid_api_version",
                            requested_version=potential_version,
                            path=path,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"API version '{potential_version}' not found. "
                            f"Supported versions: {', '.join(APIVersion.all_versions())}",
                        )

                    # Store version in request state
                    request.state.api_version = potential_version
                else:
                    # No version specified, use latest
                    request.state.api_version = APIVersion.LATEST
            else:
                # No version in path, use latest
                request.state.api_version = APIVersion.LATEST
        else:
            # Not an API request, no version needed
            request.state.api_version = None

        response = await call_next(request)

        # Add version header to response
        if hasattr(request.state, "api_version") and request.state.api_version:
            response.headers["X-API-Version"] = request.state.api_version

        return response


def get_api_version(request: Request) -> str:
    """
    Get the API version from request state.

    Args:
        request: FastAPI request object

    Returns:
        API version string (e.g., "v1")
    """
    return getattr(request.state, "api_version", APIVersion.LATEST)


def require_version(version: str):
    """
    Decorator to require a specific API version for an endpoint.

    Args:
        version: Required API version

    Example:
        >>> @router.get("/resource")
        >>> @require_version(APIVersion.V1)
        >>> async def get_resource(request: Request):
        ...     pass
    """

    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            current_version = get_api_version(request)
            if current_version != version:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"This endpoint requires API version {version}",
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
