"""Tests for Loki collector."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from topdeck.monitoring.collectors.loki import (
    LokiCollector,
    LogEntry,
)


@pytest.fixture
def loki_collector():
    """Create a Loki collector instance."""
    return LokiCollector("http://loki:3100")


@pytest.mark.asyncio
async def test_loki_collector_initialization(loki_collector):
    """Test Loki collector initialization."""
    assert loki_collector.loki_url == "http://loki:3100"
    assert loki_collector.timeout == 30
    await loki_collector.close()


@pytest.mark.asyncio
async def test_close(loki_collector):
    """Test closing the collector."""
    await loki_collector.close()
    # No assertion needed, just ensure it doesn't raise


def test_extract_log_level_fatal(loki_collector):
    """Test log level extraction for fatal."""
    level = loki_collector._extract_log_level("FATAL: System crash")
    assert level == "fatal"


def test_extract_log_level_error(loki_collector):
    """Test log level extraction for error."""
    level = loki_collector._extract_log_level("ERROR: Connection failed")
    assert level == "error"


def test_extract_log_level_warn(loki_collector):
    """Test log level extraction for warn."""
    level = loki_collector._extract_log_level("WARN: High memory usage")
    assert level == "warn"


def test_extract_log_level_info(loki_collector):
    """Test log level extraction for info."""
    level = loki_collector._extract_log_level("INFO: Service started")
    assert level == "info"


def test_extract_log_level_debug(loki_collector):
    """Test log level extraction for debug."""
    level = loki_collector._extract_log_level("DEBUG: Request received")
    assert level == "debug"


def test_extract_log_level_unknown(loki_collector):
    """Test log level extraction for unknown."""
    level = loki_collector._extract_log_level("Something happened")
    assert level == "unknown"


def test_extract_error_type_timeout(loki_collector):
    """Test error type extraction for timeout."""
    error_type = loki_collector._extract_error_type("Request timeout after 30s")
    assert error_type == "TimeoutError"


def test_extract_error_type_connection(loki_collector):
    """Test error type extraction for connection."""
    error_type = loki_collector._extract_error_type("Connection refused")
    assert error_type == "ConnectionError"


def test_extract_error_type_database(loki_collector):
    """Test error type extraction for database."""
    error_type = loki_collector._extract_error_type("SQL query failed")
    assert error_type == "DatabaseError"


def test_extract_error_type_authentication(loki_collector):
    """Test error type extraction for authentication."""
    error_type = loki_collector._extract_error_type("Authentication failed")
    assert error_type == "AuthenticationError"


def test_extract_error_type_permission(loki_collector):
    """Test error type extraction for permission."""
    error_type = loki_collector._extract_error_type("Permission denied")
    assert error_type == "PermissionError"


def test_extract_error_type_not_found(loki_collector):
    """Test error type extraction for not found."""
    error_type = loki_collector._extract_error_type("Resource not found")
    assert error_type == "NotFoundError"


def test_extract_error_type_internal_server(loki_collector):
    """Test error type extraction for internal server error."""
    error_type = loki_collector._extract_error_type("500 Internal Server Error")
    assert error_type == "InternalServerError"


def test_extract_error_type_unknown(loki_collector):
    """Test error type extraction for unknown."""
    error_type = loki_collector._extract_error_type("Something went wrong")
    assert error_type == "UnknownError"
