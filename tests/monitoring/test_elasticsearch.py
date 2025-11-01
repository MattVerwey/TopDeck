"""Tests for Elasticsearch collector."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from topdeck.monitoring.collectors.elasticsearch import (
    ElasticsearchCollector,
    ElasticsearchEntry,
    TransactionTrace,
)


@pytest.fixture
def collector():
    """Create an Elasticsearch collector instance."""
    return ElasticsearchCollector(
        url="https://elasticsearch.example.com:9200",
        index_pattern="logs-*",
        api_key="test-api-key",
        timeout=30,
    )


@pytest.fixture
def collector_basic_auth():
    """Create an Elasticsearch collector instance with basic auth."""
    return ElasticsearchCollector(
        url="https://elasticsearch.example.com:9200",
        index_pattern="logs-*",
        username="test-user",
        password="test-password",
        timeout=30,
    )


def test_initialization(collector):
    """Test Elasticsearch collector initialization."""
    assert collector.url == "https://elasticsearch.example.com:9200"
    assert collector.index_pattern == "logs-*"
    assert collector.timeout == 30


def test_initialization_basic_auth(collector_basic_auth):
    """Test Elasticsearch collector initialization with basic auth."""
    assert collector_basic_auth.url == "https://elasticsearch.example.com:9200"
    assert collector_basic_auth.index_pattern == "logs-*"
    assert collector_basic_auth.client.auth == ("test-user", "test-password")


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
    assert collector._normalize_level(7) == "debug"


def test_normalize_level_info(collector):
    """Test log level normalization for info."""
    assert collector._normalize_level("1") == "info"
    assert collector._normalize_level("information") == "info"
    assert collector._normalize_level("info") == "info"
    assert collector._normalize_level("INFO") == "info"
    assert collector._normalize_level(6) == "info"


def test_normalize_level_warning(collector):
    """Test log level normalization for warning."""
    assert collector._normalize_level("2") == "warning"
    assert collector._normalize_level("warning") == "warning"
    assert collector._normalize_level("warn") == "warning"
    assert collector._normalize_level("WARN") == "warning"
    assert collector._normalize_level(4) == "warning"


def test_normalize_level_error(collector):
    """Test log level normalization for error."""
    assert collector._normalize_level("3") == "error"
    assert collector._normalize_level("error") == "error"
    assert collector._normalize_level("err") == "error"
    assert collector._normalize_level("ERROR") == "error"
    assert collector._normalize_level(3) == "error"


def test_normalize_level_critical(collector):
    """Test log level normalization for critical."""
    assert collector._normalize_level("4") == "critical"
    assert collector._normalize_level("critical") == "critical"
    assert collector._normalize_level("fatal") == "critical"
    assert collector._normalize_level("crit") == "critical"
    assert collector._normalize_level("FATAL") == "critical"
    assert collector._normalize_level(0) == "critical"
    assert collector._normalize_level(1) == "critical"


def test_normalize_level_unknown(collector):
    """Test log level normalization for unknown."""
    assert collector._normalize_level("unknown") == "info"
    assert collector._normalize_level("something") == "info"


def test_extract_resource_id(collector):
    """Test resource ID extraction from document."""
    # Test direct resource_id field
    doc = {"resource_id": "my-resource"}
    assert collector._extract_resource_id(doc) == "my-resource"

    # Test nested resource.id field
    doc = {"resource": {"id": "nested-resource"}}
    assert collector._extract_resource_id(doc) == "nested-resource"

    # Test kubernetes pod name
    doc = {"kubernetes": {"pod": {"name": "my-pod"}}}
    assert collector._extract_resource_id(doc) == "my-pod"

    # Test container name
    doc = {"container": {"name": "my-container"}}
    assert collector._extract_resource_id(doc) == "my-container"

    # Test service name
    doc = {"service": {"name": "my-service"}}
    assert collector._extract_resource_id(doc) == "my-service"

    # Test empty document
    doc = {}
    assert collector._extract_resource_id(doc) == ""


def test_extract_correlation_id(collector):
    """Test correlation ID extraction from document."""
    # Test various correlation ID field names
    assert collector._extract_correlation_id({"correlation_id": "corr-123"}) == "corr-123"
    assert collector._extract_correlation_id({"correlationId": "corr-456"}) == "corr-456"
    assert collector._extract_correlation_id({"transaction_id": "txn-789"}) == "txn-789"
    assert collector._extract_correlation_id({"transactionId": "txn-abc"}) == "txn-abc"
    assert collector._extract_correlation_id({"trace_id": "trace-def"}) == "trace-def"
    assert collector._extract_correlation_id({"traceId": "trace-ghi"}) == "trace-ghi"
    assert collector._extract_correlation_id({}) is None


def test_extract_properties(collector):
    """Test properties extraction from document."""
    doc = {
        "@timestamp": "2024-01-01T00:00:00Z",
        "message": "Test message",
        "level": "info",
        "correlation_id": "corr-123",
        "custom_field": "custom_value",
        "another_field": 42,
    }

    props = collector._extract_properties(doc)

    # Should include custom fields
    assert "custom_field" in props
    assert "another_field" in props

    # Should exclude standard fields
    assert "@timestamp" not in props
    assert "message" not in props
    assert "level" not in props
    assert "correlation_id" not in props


def test_parse_timestamp(collector):
    """Test timestamp parsing."""
    # Test ISO format
    timestamp = collector._parse_timestamp("2024-01-01T12:00:00Z")
    assert isinstance(timestamp, datetime)
    assert timestamp.year == 2024
    assert timestamp.month == 1
    assert timestamp.day == 1

    # Test with timezone
    timestamp = collector._parse_timestamp("2024-01-01T12:00:00+00:00")
    assert isinstance(timestamp, datetime)

    # Test invalid timestamp
    timestamp = collector._parse_timestamp("invalid")
    assert isinstance(timestamp, datetime)  # Should return current time

    # Test None
    timestamp = collector._parse_timestamp(None)
    assert isinstance(timestamp, datetime)


@pytest.mark.asyncio
async def test_search_success(collector):
    """Test successful Elasticsearch search."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "hits": {
            "hits": [
                {"_source": {"message": "Log 1", "level": "info"}},
                {"_source": {"message": "Log 2", "level": "error"}},
            ]
        }
    }
    mock_response.raise_for_status = Mock()

    with patch.object(collector.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        query = {"query": {"match_all": {}}}
        results = await collector.search(query)

        assert len(results) == 2
        assert results[0]["message"] == "Log 1"
        assert results[1]["level"] == "error"


@pytest.mark.asyncio
async def test_search_failure(collector):
    """Test Elasticsearch search failure."""
    with patch.object(collector.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection error")

        query = {"query": {"match_all": {}}}
        results = await collector.search(query)

        # Should return empty list on error
        assert results == []


@pytest.mark.asyncio
async def test_get_logs_by_correlation_id(collector):
    """Test getting logs by correlation ID."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "@timestamp": "2024-01-01T12:00:00Z",
                        "message": "Request received",
                        "correlation_id": "test-corr-id",
                        "level": "info",
                        "resource_id": "service-a",
                    }
                },
                {
                    "_source": {
                        "@timestamp": "2024-01-01T12:00:01Z",
                        "message": "Request processed",
                        "correlation_id": "test-corr-id",
                        "level": "info",
                        "resource_id": "service-b",
                    }
                },
            ]
        }
    }
    mock_response.raise_for_status = Mock()

    with patch.object(collector.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        entries = await collector.get_logs_by_correlation_id("test-corr-id")

        assert len(entries) == 2
        assert entries[0].message == "Request received"
        assert entries[0].correlation_id == "test-corr-id"
        assert entries[0].resource_id == "service-a"
        assert entries[1].resource_id == "service-b"


@pytest.mark.asyncio
async def test_trace_transaction_flow(collector):
    """Test tracing transaction flow."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "@timestamp": "2024-01-01T12:00:00Z",
                        "message": "Request start",
                        "correlation_id": "txn-123",
                        "level": "info",
                        "resource_id": "gateway",
                    }
                },
                {
                    "_source": {
                        "@timestamp": "2024-01-01T12:00:01Z",
                        "message": "Processing",
                        "correlation_id": "txn-123",
                        "level": "warning",
                        "resource_id": "api-service",
                    }
                },
                {
                    "_source": {
                        "@timestamp": "2024-01-01T12:00:02Z",
                        "message": "Error occurred",
                        "correlation_id": "txn-123",
                        "level": "error",
                        "resource_id": "database",
                    }
                },
            ]
        }
    }
    mock_response.raise_for_status = Mock()

    with patch.object(collector.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        trace = await collector.trace_transaction_flow("txn-123")

        assert trace is not None
        assert trace.transaction_id == "txn-123"
        assert len(trace.entries) == 3
        assert trace.resource_path == ["gateway", "api-service", "database"]
        assert trace.error_count == 1
        assert trace.warning_count == 1
        assert trace.duration_ms == 2000  # 2 seconds


@pytest.mark.asyncio
async def test_trace_transaction_flow_no_logs(collector):
    """Test tracing transaction flow with no logs."""
    mock_response = Mock()
    mock_response.json.return_value = {"hits": {"hits": []}}
    mock_response.raise_for_status = Mock()

    with patch.object(collector.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        trace = await collector.trace_transaction_flow("nonexistent-id")

        assert trace is None


def test_elasticsearch_entry_creation():
    """Test ElasticsearchEntry creation."""
    timestamp = datetime.now(timezone.utc)
    entry = ElasticsearchEntry(
        timestamp=timestamp,
        message="Test message",
        properties={"key": "value"},
        resource_id="test-resource",
        correlation_id="corr-123",
        operation_name="test-op",
        level="info",
    )

    assert entry.timestamp == timestamp
    assert entry.message == "Test message"
    assert entry.properties == {"key": "value"}
    assert entry.resource_id == "test-resource"
    assert entry.correlation_id == "corr-123"
    assert entry.operation_name == "test-op"
    assert entry.level == "info"


def test_transaction_trace_creation():
    """Test TransactionTrace creation."""
    timestamp = datetime.now(timezone.utc)
    entries = [
        ElasticsearchEntry(
            timestamp=timestamp,
            message="Log 1",
            properties={},
            resource_id="resource-1",
            level="info",
        )
    ]

    trace = TransactionTrace(
        transaction_id="txn-123",
        start_time=timestamp,
        end_time=timestamp,
        duration_ms=100.0,
        entries=entries,
        resource_path=["resource-1"],
        error_count=0,
        warning_count=0,
    )

    assert trace.transaction_id == "txn-123"
    assert trace.duration_ms == 100.0
    assert len(trace.entries) == 1
    assert trace.resource_path == ["resource-1"]
