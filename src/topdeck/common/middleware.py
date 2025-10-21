"""
Middleware components for the TopDeck API.

Provides logging, error handling, and request tracking middleware.
"""

import time
import uuid
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log the incoming request
        logger.info(
            "incoming_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_host=request.client.host if request.client else None,
        )

        # Track request timing
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log the response
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time_ms=round(process_time * 1000, 2),
            )
            raise


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request state if not present."""
        if not hasattr(request.state, "request_id"):
            request.state.request_id = str(uuid.uuid4())

        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


def get_request_id(request: Request) -> str:
    """Get the request ID from the request state."""
    return getattr(request.state, "request_id", "unknown")
