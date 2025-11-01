"""Tests for Tempo collector."""

import pytest

from topdeck.monitoring.collectors.tempo import TempoCollector


@pytest.fixture
def tempo_collector():
    """Create a Tempo collector instance."""
    return TempoCollector("http://tempo:3200")


@pytest.mark.asyncio
async def test_tempo_collector_initialization(tempo_collector):
    """Test Tempo collector initialization."""
    assert tempo_collector.tempo_url == "http://tempo:3200"
    assert tempo_collector.timeout == 30
    await tempo_collector.close()


@pytest.mark.asyncio
async def test_close(tempo_collector):
    """Test closing the collector."""
    await tempo_collector.close()
    # No assertion needed, just ensure it doesn't raise


def test_get_service_name(tempo_collector):
    """Test extracting service name from resource attributes."""
    resource = {
        "attributes": [
            {"key": "service.name", "value": {"stringValue": "test-service"}}
        ]
    }
    
    service_name = tempo_collector._get_service_name(resource)
    assert service_name == "test-service"


def test_get_service_name_missing(tempo_collector):
    """Test extracting service name when not present."""
    resource = {"attributes": []}
    
    service_name = tempo_collector._get_service_name(resource)
    assert service_name == "unknown"


def test_parse_span(tempo_collector):
    """Test parsing a span from Tempo API response."""
    span_data = {
        "spanID": "abc123",
        "parentSpanID": "parent123",
        "name": "GET /api/users",
        "startTimeUnixNano": 1000000000000000000,  # 1 second from epoch in nanoseconds
        "endTimeUnixNano": 1000100000000000000,    # 1.1 seconds from epoch in nanoseconds
        "attributes": [
            {"key": "http.method", "value": {"stringValue": "GET"}},
            {"key": "http.status_code", "value": {"intValue": 200}},
        ],
        "events": [
            {
                "timeUnixNano": 1000050000000000000,
                "name": "cache_hit",
                "attributes": [],
            }
        ],
        "status": {"code": 0},  # OK
    }
    
    span = tempo_collector._parse_span(span_data, "test-service", "trace123")
    
    assert span.trace_id == "trace123"
    assert span.span_id == "abc123"
    assert span.parent_span_id == "parent123"
    assert span.operation_name == "GET /api/users"
    assert span.service_name == "test-service"
    assert span.duration_ms == 100.0  # 100ms
    assert span.tags["http.method"] == "GET"
    assert span.tags["http.status_code"] == 200
    assert len(span.logs) == 1
    assert span.status == "ok"


def test_parse_span_error_status(tempo_collector):
    """Test parsing a span with error status."""
    span_data = {
        "spanID": "abc123",
        "name": "GET /api/users",
        "startTimeUnixNano": 1000000000000000000,
        "endTimeUnixNano": 1000100000000000000,
        "attributes": [],
        "events": [],
        "status": {"code": 2},  # ERROR
    }
    
    span = tempo_collector._parse_span(span_data, "test-service", "trace123")
    assert span.status == "error"


def test_parse_trace(tempo_collector):
    """Test parsing a complete trace from Tempo API response."""
    trace_data = {
        "traceID": "trace123",
        "batches": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "api-gateway"}}
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "spanID": "span1",
                                "name": "handle_request",
                                "startTimeUnixNano": 1000000000000000000,
                                "endTimeUnixNano": 1000200000000000000,
                                "attributes": [],
                                "events": [],
                                "status": {"code": 0},
                            },
                            {
                                "spanID": "span2",
                                "parentSpanID": "span1",
                                "name": "query_database",
                                "startTimeUnixNano": 1000050000000000000,
                                "endTimeUnixNano": 1000150000000000000,
                                "attributes": [],
                                "events": [],
                                "status": {"code": 2},  # ERROR
                            },
                        ]
                    }
                ],
            }
        ],
    }
    
    trace = tempo_collector._parse_trace(trace_data)
    
    assert trace.trace_id == "trace123"
    assert len(trace.spans) == 2
    assert trace.service_count == 1
    assert trace.error_count == 1
    assert trace.root_service == "api-gateway"
    assert trace.duration_ms == 200.0


def test_parse_trace_multiple_services(tempo_collector):
    """Test parsing a trace with multiple services."""
    trace_data = {
        "traceID": "trace123",
        "batches": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "api-gateway"}}
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "spanID": "span1",
                                "name": "handle_request",
                                "startTimeUnixNano": 1000000000000000000,
                                "endTimeUnixNano": 1000100000000000000,
                                "attributes": [],
                                "events": [],
                                "status": {"code": 0},
                            }
                        ]
                    }
                ],
            },
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "user-service"}}
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "spanID": "span2",
                                "parentSpanID": "span1",
                                "name": "get_user",
                                "startTimeUnixNano": 1000020000000000000,
                                "endTimeUnixNano": 1000080000000000000,
                                "attributes": [],
                                "events": [],
                                "status": {"code": 0},
                            }
                        ]
                    }
                ],
            },
        ],
    }
    
    trace = tempo_collector._parse_trace(trace_data)
    
    assert trace.service_count == 2
    assert len(trace.spans) == 2
    assert trace.error_count == 0
