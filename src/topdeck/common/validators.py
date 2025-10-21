"""
Input validation utilities for API endpoints.

Provides reusable validators and error responses for common input patterns.
"""

import re

from fastapi import HTTPException, status


class ValidationError(HTTPException):
    """Custom validation error with consistent format."""

    def __init__(
        self, field: str, message: str, status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    ):
        """
        Initialize validation error.

        Args:
            field: Field name that failed validation
            message: Error message
            status_code: HTTP status code
        """
        super().__init__(
            status_code=status_code,
            detail={"field": field, "message": message},
        )


def validate_resource_id(resource_id: str) -> str:
    """
    Validate resource ID format.

    Args:
        resource_id: Resource identifier

    Returns:
        Validated resource ID

    Raises:
        ValidationError: If resource ID is invalid
    """
    if not resource_id or not resource_id.strip():
        raise ValidationError("resource_id", "Resource ID cannot be empty")

    if len(resource_id) > 500:
        raise ValidationError("resource_id", "Resource ID too long (max 500 characters)")

    return resource_id.strip()


def validate_cloud_provider(provider: str) -> str:
    """
    Validate cloud provider name.

    Args:
        provider: Cloud provider name

    Returns:
        Normalized provider name

    Raises:
        ValidationError: If provider is invalid
    """
    valid_providers = ["azure", "aws", "gcp"]
    provider_lower = provider.lower().strip()

    if provider_lower not in valid_providers:
        raise ValidationError(
            "provider",
            f"Invalid cloud provider. Must be one of: {', '.join(valid_providers)}",
        )

    return provider_lower


def validate_resource_type(resource_type: str) -> str:
    """
    Validate resource type.

    Args:
        resource_type: Resource type string

    Returns:
        Validated resource type

    Raises:
        ValidationError: If resource type is invalid
    """
    if not resource_type or not resource_type.strip():
        raise ValidationError("resource_type", "Resource type cannot be empty")

    if len(resource_type) > 100:
        raise ValidationError("resource_type", "Resource type too long (max 100 characters)")

    # Resource type should be alphanumeric with underscores, hyphens, or dots
    if not re.match(r"^[a-zA-Z0-9._-]+$", resource_type):
        raise ValidationError(
            "resource_type",
            "Resource type must contain only alphanumeric characters, dots, hyphens, or underscores",
        )

    return resource_type.strip()


def validate_subscription_id(subscription_id: str) -> str:
    """
    Validate Azure subscription ID format.

    Args:
        subscription_id: Azure subscription ID

    Returns:
        Validated subscription ID

    Raises:
        ValidationError: If subscription ID is invalid
    """
    if not subscription_id or not subscription_id.strip():
        raise ValidationError("subscription_id", "Subscription ID cannot be empty")

    # Azure subscription IDs are GUIDs
    guid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    if not re.match(guid_pattern, subscription_id.lower()):
        raise ValidationError(
            "subscription_id",
            "Invalid subscription ID format (must be a valid GUID)",
        )

    return subscription_id.strip()


def validate_pagination(
    page: int = 1, per_page: int = 50, max_per_page: int = 100
) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum allowed items per page

    Returns:
        Tuple of (validated_page, validated_per_page)

    Raises:
        ValidationError: If pagination parameters are invalid
    """
    if page < 1:
        raise ValidationError("page", "Page number must be >= 1")

    if per_page < 1:
        raise ValidationError("per_page", "Items per page must be >= 1")

    if per_page > max_per_page:
        raise ValidationError("per_page", f"Items per page cannot exceed {max_per_page}")

    return page, per_page


def validate_risk_score(score: float) -> float:
    """
    Validate risk score value.

    Args:
        score: Risk score value

    Returns:
        Validated score

    Raises:
        ValidationError: If score is invalid
    """
    if not 0.0 <= score <= 1.0:
        raise ValidationError("risk_score", "Risk score must be between 0.0 and 1.0")

    return score


def validate_time_range(
    start_time: str | None, end_time: str | None
) -> tuple[str | None, str | None]:
    """
    Validate time range parameters.

    Args:
        start_time: Start time in ISO format
        end_time: End time in ISO format

    Returns:
        Tuple of (validated_start_time, validated_end_time)

    Raises:
        ValidationError: If time range is invalid
    """
    from datetime import datetime

    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValidationError("start_time", "Invalid ISO format for start_time") from e

        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValidationError("end_time", "Invalid ISO format for end_time") from e

            if start_dt >= end_dt:
                raise ValidationError("time_range", "start_time must be before end_time")

    return start_time, end_time


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string value for safe storage and display.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValidationError: If string is too long
    """
    if not value:
        return ""

    # Strip whitespace
    sanitized = value.strip()

    # Check length
    if len(sanitized) > max_length:
        raise ValidationError("value", f"String too long (max {max_length} characters)")

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    return sanitized
