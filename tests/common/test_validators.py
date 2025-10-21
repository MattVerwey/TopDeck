"""
Tests for input validators.
"""

import pytest
from topdeck.common.validators import (
    validate_resource_id,
    validate_cloud_provider,
    validate_resource_type,
    validate_subscription_id,
    validate_pagination,
    validate_risk_score,
    sanitize_string,
    ValidationError,
)


def test_validate_resource_id_success():
    """Test successful resource ID validation."""
    assert validate_resource_id("resource-123") == "resource-123"
    assert validate_resource_id("  resource-123  ") == "resource-123"


def test_validate_resource_id_empty():
    """Test resource ID validation with empty string."""
    with pytest.raises(ValidationError) as exc:
        validate_resource_id("")
    assert "empty" in str(exc.value.detail["message"]).lower()


def test_validate_resource_id_too_long():
    """Test resource ID validation with too long string."""
    with pytest.raises(ValidationError):
        validate_resource_id("a" * 501)


def test_validate_cloud_provider_success():
    """Test successful cloud provider validation."""
    assert validate_cloud_provider("azure") == "azure"
    assert validate_cloud_provider("AWS") == "aws"
    assert validate_cloud_provider("  GCP  ") == "gcp"


def test_validate_cloud_provider_invalid():
    """Test cloud provider validation with invalid provider."""
    with pytest.raises(ValidationError) as exc:
        validate_cloud_provider("digitalocean")
    assert "invalid" in str(exc.value.detail["message"]).lower()


def test_validate_resource_type_success():
    """Test successful resource type validation."""
    assert validate_resource_type("compute.vm") == "compute.vm"
    assert validate_resource_type("storage_account") == "storage_account"


def test_validate_resource_type_invalid_chars():
    """Test resource type validation with invalid characters."""
    with pytest.raises(ValidationError):
        validate_resource_type("invalid type!")


def test_validate_subscription_id_success():
    """Test successful subscription ID validation."""
    valid_id = "12345678-1234-1234-1234-123456789012"
    assert validate_subscription_id(valid_id) == valid_id


def test_validate_subscription_id_invalid_format():
    """Test subscription ID validation with invalid format."""
    with pytest.raises(ValidationError):
        validate_subscription_id("not-a-guid")


def test_validate_pagination_success():
    """Test successful pagination validation."""
    page, per_page = validate_pagination(1, 50)
    assert page == 1
    assert per_page == 50


def test_validate_pagination_invalid_page():
    """Test pagination validation with invalid page."""
    with pytest.raises(ValidationError):
        validate_pagination(0, 50)


def test_validate_pagination_too_many_items():
    """Test pagination validation with too many items per page."""
    with pytest.raises(ValidationError):
        validate_pagination(1, 150, max_per_page=100)


def test_validate_risk_score_success():
    """Test successful risk score validation."""
    assert validate_risk_score(0.5) == 0.5
    assert validate_risk_score(0.0) == 0.0
    assert validate_risk_score(1.0) == 1.0


def test_validate_risk_score_out_of_range():
    """Test risk score validation with out of range value."""
    with pytest.raises(ValidationError):
        validate_risk_score(1.5)
    with pytest.raises(ValidationError):
        validate_risk_score(-0.1)


def test_sanitize_string_success():
    """Test successful string sanitization."""
    assert sanitize_string("  hello  ") == "hello"
    assert sanitize_string("normal string") == "normal string"


def test_sanitize_string_removes_null_bytes():
    """Test that null bytes are removed."""
    assert sanitize_string("hello\x00world") == "helloworld"


def test_sanitize_string_too_long():
    """Test string sanitization with too long string."""
    with pytest.raises(ValidationError):
        sanitize_string("a" * 1001, max_length=1000)
