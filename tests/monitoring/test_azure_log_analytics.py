"""Tests for Azure Log Analytics collector."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from topdeck.monitoring.collectors.azure_log_analytics import (
    AzureLogAnalyticsCollector,
    LogAnalyticsEntry,
    TransactionTrace,
)


@pytest.fixture
def mock_credential():
    """Create a mock Azure credential."""
    credential = Mock()
    token = Mock()
    token.token = "mock-token"
    token.expires_on = 9999999999  # Far future
    credential.get_token.return_value = token
    return credential


@pytest.fixture
def collector(mock_credential):
    """Create an Azure Log Analytics collector instance."""
    return AzureLogAnalyticsCollector(
        workspace_id="test-workspace-id", credential=mock_credential, timeout=30
    )


def test_initialization(collector):
    """Test Azure Log Analytics collector initialization."""
    assert collector.workspace_id == "test-workspace-id"
    assert collector.timeout == 30
    assert (
        collector.base_url
        == "https://api.loganalytics.io/v1/workspaces/test-workspace-id/query"
    )


@pytest.mark.asyncio
async def test_close(collector):
    """Test closing the collector."""
    await collector.close()
    # No assertion needed, just ensure it doesn't raise


def test_normalize_level_debug(collector):
    """Test log level normalization for debug."""
    assert collector._normalize_level("0") == "debug"
    assert collector._normalize_level("verbose") == "debug"
    assert collector._normalize_level("trace") == "debug"
    assert collector._normalize_level("debug") == "debug"
    assert collector._normalize_level("DEBUG") == "debug"


def test_normalize_level_info(collector):
    """Test log level normalization for info."""
    assert collector._normalize_level("1") == "info"
    assert collector._normalize_level("information") == "info"
    assert collector._normalize_level("info") == "info"
    assert collector._normalize_level("INFO") == "info"


def test_normalize_level_warning(collector):
    """Test log level normalization for warning."""
    assert collector._normalize_level("2") == "warning"
    assert collector._normalize_level("warning") == "warning"
    assert collector._normalize_level("warn") == "warning"
    assert collector._normalize_level("WARN") == "warning"


def test_normalize_level_error(collector):
    """Test log level normalization for error."""
    assert collector._normalize_level("3") == "error"
    assert collector._normalize_level("error") == "error"
    assert collector._normalize_level("ERROR") == "error"


def test_normalize_level_critical(collector):
    """Test log level normalization for critical."""
    assert collector._normalize_level("4") == "critical"
    assert collector._normalize_level("critical") == "critical"
    assert collector._normalize_level("fatal") == "critical"
    assert collector._normalize_level("FATAL") == "critical"


def test_normalize_level_unknown(collector):
    """Test log level normalization for unknown."""
    assert collector._normalize_level("unknown") == "info"
    assert collector._normalize_level("something") == "info"


def test_log_analytics_entry_creation():
    """Test LogAnalyticsEntry creation."""
    timestamp = datetime.utcnow()
    entry = LogAnalyticsEntry(
        timestamp=timestamp,
        message="Test message",
        properties={"key": "value"},
        resource_id="/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/aks/pods/pod-1",
        correlation_id="test-correlation-id",
        operation_name="test-operation",
        level="info",
    )

    assert entry.timestamp == timestamp
    assert entry.message == "Test message"
    assert entry.properties == {"key": "value"}
    assert entry.correlation_id == "test-correlation-id"
    assert entry.operation_name == "test-operation"
    assert entry.level == "info"


def test_transaction_trace_creation():
    """Test TransactionTrace creation."""
    start_time = datetime.utcnow()
    end_time = datetime.utcnow()

    entry1 = LogAnalyticsEntry(
        timestamp=start_time,
        message="Request started",
        properties={},
        resource_id="resource-1",
        correlation_id="test-id",
        level="info",
    )

    entry2 = LogAnalyticsEntry(
        timestamp=end_time,
        message="Request completed",
        properties={},
        resource_id="resource-2",
        correlation_id="test-id",
        level="info",
    )

    trace = TransactionTrace(
        transaction_id="test-id",
        start_time=start_time,
        end_time=end_time,
        duration_ms=100.0,
        entries=[entry1, entry2],
        resource_path=["resource-1", "resource-2"],
        error_count=0,
        warning_count=0,
    )

    assert trace.transaction_id == "test-id"
    assert trace.start_time == start_time
    assert trace.end_time == end_time
    assert trace.duration_ms == 100.0
    assert len(trace.entries) == 2
    assert trace.resource_path == ["resource-1", "resource-2"]
    assert trace.error_count == 0
    assert trace.warning_count == 0


@pytest.mark.asyncio
async def test_get_access_token(collector, mock_credential):
    """Test getting access token."""
    token = await collector._get_access_token()
    assert token == "mock-token"
    mock_credential.get_token.assert_called_once_with(
        "https://api.loganalytics.io/.default"
    )


@pytest.mark.asyncio
async def test_query_empty_result(collector):
    """Test query with empty result."""
    with patch.object(collector.client, "post") as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {"tables": []}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        results = await collector.query("test query")
        assert results == []


@pytest.mark.asyncio
async def test_query_with_results(collector):
    """Test query with results."""
    with patch.object(collector.client, "post") as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            "tables": [
                {
                    "columns": [
                        {"name": "TimeGenerated"},
                        {"name": "Message"},
                        {"name": "Level"},
                    ],
                    "rows": [
                        ["2024-01-01T00:00:00Z", "Test message", "Information"],
                        ["2024-01-01T00:00:01Z", "Another message", "Error"],
                    ],
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        results = await collector.query("test query")
        assert len(results) == 2
        assert results[0]["TimeGenerated"] == "2024-01-01T00:00:00Z"
        assert results[0]["Message"] == "Test message"
        assert results[0]["Level"] == "Information"
        assert results[1]["TimeGenerated"] == "2024-01-01T00:00:01Z"
        assert results[1]["Message"] == "Another message"
        assert results[1]["Level"] == "Error"


@pytest.mark.asyncio
async def test_query_exception(collector):
    """Test query with exception."""
    with patch.object(collector.client, "post") as mock_post:
        mock_post.side_effect = Exception("Network error")

        results = await collector.query("test query")
        assert results == []
