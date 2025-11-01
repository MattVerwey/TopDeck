"""
Enhanced error handling and response utilities.

Provides consistent error responses with correlation IDs and detailed error information.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: ErrorDetail
    request_id: str
    timestamp: str
    path: str


class TopDeckException(Exception):
    """Base exception for TopDeck application errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize TopDeck exception.

        Args:
            code: Error code (e.g., "RESOURCE_NOT_FOUND")
            message: Human-readable error message
            status_code: HTTP status code
            field: Optional field name that caused the error
            details: Optional additional error details
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field
        self.details = details or {}
        super().__init__(message)


class ResourceNotFoundException(TopDeckException):
    """Exception for resource not found errors."""

    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        """
        Initialize resource not found exception.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
        """
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource_type} with ID '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs,
        )


class InvalidInputException(TopDeckException):
    """Exception for invalid input errors."""

    def __init__(self, field: str, message: str, **kwargs):
        """
        Initialize invalid input exception.

        Args:
            field: Field name with invalid input
            message: Error message
        """
        super().__init__(
            code="INVALID_INPUT",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            field=field,
            **kwargs,
        )


class ServiceUnavailableException(TopDeckException):
    """Exception for service unavailable errors."""

    def __init__(self, service: str, reason: str, **kwargs):
        """
        Initialize service unavailable exception.

        Args:
            service: Service name
            reason: Reason for unavailability
        """
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=f"Service '{service}' is unavailable: {reason}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service, "reason": reason},
            **kwargs,
        )


class RateLimitExceededException(TopDeckException):
    """Exception for rate limit exceeded errors."""

    def __init__(self, retry_after: int, **kwargs):
        """
        Initialize rate limit exceeded exception.

        Args:
            retry_after: Seconds until retry is allowed
        """
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after},
            **kwargs,
        )


def create_error_response(
    request: Request,
    exception: TopDeckException,
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        request: FastAPI request object
        exception: TopDeck exception

    Returns:
        JSONResponse with error details
    """
    from topdeck.common.middleware import get_request_id

    request_id = get_request_id(request)

    error_detail = ErrorDetail(
        code=exception.code,
        message=exception.message,
        field=exception.field,
        details=exception.details,
    )

    error_response = ErrorResponse(
        error=error_detail,
        request_id=request_id,
        timestamp=datetime.now(UTC).isoformat(),
        path=str(request.url.path),
    )

    # Log the error
    logger.error(
        "api_error",
        request_id=request_id,
        code=exception.code,
        message=exception.message,
        path=str(request.url.path),
        status_code=exception.status_code,
    )

    return JSONResponse(
        status_code=exception.status_code,
        content=error_response.model_dump(),
    )


async def topdeck_exception_handler(request: Request, exc: TopDeckException) -> JSONResponse:
    """
    Exception handler for TopDeck exceptions.

    Args:
        request: FastAPI request object
        exc: TopDeck exception

    Returns:
        JSONResponse with error details
    """
    return create_error_response(request, exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Exception handler for unhandled exceptions.

    Args:
        request: FastAPI request object
        exc: Exception

    Returns:
        JSONResponse with error details
    """
    from topdeck.common.middleware import get_request_id

    request_id = get_request_id(request)

    # Log the unexpected error
    logger.exception(
        "unhandled_exception",
        request_id=request_id,
        path=str(request.url.path),
        error_type=type(exc).__name__,
        error_message=str(exc),
    )

    error_detail = ErrorDetail(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"error_type": type(exc).__name__},
    )

    error_response = ErrorResponse(
        error=error_detail,
        request_id=request_id,
        timestamp=datetime.now(UTC).isoformat(),
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )
