"""
Tests for the Log Correlation Engine.

Tests the functionality that addresses Market Gap #1:
Log Correlation Across Distributed Systems.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from topdeck.troubleshooting.log_correlation import (
    CorrelatedLogEntry,
    CorrelatedLogs,
    ErrorChain,
    ErrorChainLink,
    LogCorrelationEngine,
    LogLevel,
    TransactionTimeline,
    TransactionTimelineEvent,
)


class TestCorrelatedLogEntry:
    """Tests for CorrelatedLogEntry dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        entry = CorrelatedLogEntry(
            timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            message="Test message",
            level=LogLevel.ERROR,
            service_id="service-1",
            service_name="Test Service",
            correlation_id="corr-123",
            trace_id="trace-456",
            span_id="span-789",
            properties={"key": "value"},
        )

        result = entry.to_dict()

        assert result["message"] == "Test message"
        assert result["level"] == "error"
        assert result["service_id"] == "service-1"
        assert result["correlation_id"] == "corr-123"
        assert result["properties"]["key"] == "value"


class TestCorrelatedLogs:
    """Tests for CorrelatedLogs dataclass."""

    def test_to_dict_with_entries(self):
        """Test conversion to dictionary with entries."""
        now = datetime.now(UTC)
        entries = [
            CorrelatedLogEntry(
                timestamp=now,
                message="Entry 1",
                level=LogLevel.INFO,
                service_id="svc-1",
                service_name="Service 1",
                correlation_id="corr-123",
                trace_id=None,
                span_id=None,
            ),
            CorrelatedLogEntry(
                timestamp=now + timedelta(seconds=1),
                message="Entry 2",
                level=LogLevel.ERROR,
                service_id="svc-2",
                service_name="Service 2",
                correlation_id="corr-123",
                trace_id=None,
                span_id=None,
            ),
        ]

        logs = CorrelatedLogs(
            correlation_id="corr-123",
            start_time=now,
            end_time=now + timedelta(seconds=1),
            entries=entries,
            services_involved=["svc-1", "svc-2"],
            error_count=1,
            warning_count=0,
        )

        result = logs.to_dict()

        assert result["correlation_id"] == "corr-123"
        assert len(result["entries"]) == 2
        assert result["error_count"] == 1
        assert result["duration_ms"] == 1000


class TestErrorChain:
    """Tests for ErrorChain dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        chain = ErrorChain(
            error_id="err-123",
            root_cause_service="db-service",
            root_cause_error="Connection timeout",
            affected_services=["db-service", "api-service", "web-service"],
            propagation_path=[
                ErrorChainLink(
                    service_id="db-service",
                    service_name="Database Service",
                    error_message="Connection timeout",
                    timestamp=now,
                    level=LogLevel.ERROR,
                    is_root_cause=True,
                ),
                ErrorChainLink(
                    service_id="api-service",
                    service_name="API Service",
                    error_message="Failed to connect to database",
                    timestamp=now + timedelta(milliseconds=50),
                    level=LogLevel.ERROR,
                    is_root_cause=False,
                    downstream_service="web-service",
                ),
            ],
            total_duration_ms=100,
            confidence_score=0.85,
        )

        result = chain.to_dict()

        assert result["error_id"] == "err-123"
        assert result["root_cause_service"] == "db-service"
        assert len(result["propagation_path"]) == 2
        assert result["confidence_score"] == 0.85


class TestLogCorrelationEngine:
    """Tests for LogCorrelationEngine."""

    @pytest.fixture
    def engine(self):
        """Create engine with mocked dependencies."""
        return LogCorrelationEngine(
            loki_collector=None,
            elasticsearch_collector=None,
            azure_log_collector=None,
            neo4j_client=None,
        )

    def test_extract_correlation_id(self, engine):
        """Test extraction of correlation ID from log message."""
        # Test various patterns
        messages = [
            ("correlation_id=abc-123 error occurred", "abc-123"),
            ("request-id: def-456", "def-456"),
            ("trace_id=ghi-789 some log", "ghi-789"),
            ("X-Request-ID: jkl-012", "jkl-012"),
            ("no correlation id here", None),
        ]

        for message, expected in messages:
            result = engine._extract_correlation_id(message)
            assert result == expected, f"Failed for message: {message}"

    def test_parse_log_level(self, engine):
        """Test parsing of log levels."""
        test_cases = [
            ("debug", LogLevel.DEBUG),
            ("DEBUG", LogLevel.DEBUG),
            ("trace", LogLevel.DEBUG),
            ("info", LogLevel.INFO),
            ("INFO", LogLevel.INFO),
            ("information", LogLevel.INFO),
            ("warn", LogLevel.WARNING),
            ("WARNING", LogLevel.WARNING),
            ("error", LogLevel.ERROR),
            ("ERROR", LogLevel.ERROR),
            ("critical", LogLevel.CRITICAL),
            ("FATAL", LogLevel.CRITICAL),
            ("unknown", LogLevel.INFO),  # Default
        ]

        for level_str, expected in test_cases:
            result = engine._parse_log_level(level_str)
            assert result == expected, f"Failed for level: {level_str}"

    def test_determine_event_type(self, engine):
        """Test determination of event type from log entry."""
        now = datetime.now(UTC)

        # Test request detection
        entry = CorrelatedLogEntry(
            timestamp=now,
            message="Request received from client",
            level=LogLevel.INFO,
            service_id="svc-1",
            service_name="Service 1",
            correlation_id="corr-123",
            trace_id=None,
            span_id=None,
        )
        assert engine._determine_event_type(entry) == "request"

        # Test response detection
        entry.message = "Response completed successfully"
        assert engine._determine_event_type(entry) == "response"

        # Test error detection
        entry.message = "Processing failed"
        entry.level = LogLevel.ERROR
        assert engine._determine_event_type(entry) == "error"

        # Test default log type
        entry.message = "Some informational log"
        entry.level = LogLevel.INFO
        assert engine._determine_event_type(entry) == "log"

    def test_calculate_chain_confidence(self, engine):
        """Test confidence calculation for error chain."""
        now = datetime.now(UTC)

        # Test with sequential timestamps
        path = [
            ErrorChainLink(
                service_id="svc-1",
                service_name="Service 1",
                error_message="Error 1",
                timestamp=now,
                level=LogLevel.ERROR,
                is_root_cause=True,
                downstream_service="svc-2",
            ),
            ErrorChainLink(
                service_id="svc-2",
                service_name="Service 2",
                error_message="Error 2",
                timestamp=now + timedelta(seconds=1),
                level=LogLevel.ERROR,
                is_root_cause=False,
            ),
        ]

        # With known dependencies
        confidence = engine._calculate_chain_confidence(path, ["svc-1", "svc-2"])
        assert confidence >= 0.7  # Should have decent confidence

        # Without known dependencies
        confidence = engine._calculate_chain_confidence(path, [])
        assert confidence >= 0.5  # Still should have base confidence

        # Empty path
        confidence = engine._calculate_chain_confidence([], [])
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_correlate_by_correlation_id_no_collectors(self, engine):
        """Test correlation when no collectors are available."""
        result = await engine.correlate_by_correlation_id(
            correlation_id="test-123",
            time_window_minutes=30,
        )

        assert result.correlation_id == "test-123"
        assert len(result.entries) == 0
        assert len(result.services_involved) == 0

    @pytest.mark.asyncio
    async def test_correlate_with_loki(self):
        """Test correlation with Loki collector."""
        # Create mock Loki collector
        mock_loki = AsyncMock()
        mock_stream = MagicMock()
        mock_stream.labels = {"service": "test-service", "job": "test-job"}
        mock_stream.entries = [
            MagicMock(
                timestamp=datetime.now(UTC),
                message="Test log entry",
                level="error",
            )
        ]
        mock_loki.query.return_value = [mock_stream]

        engine = LogCorrelationEngine(
            loki_collector=mock_loki,
        )

        result = await engine.correlate_by_correlation_id(
            correlation_id="test-123",
            time_window_minutes=30,
        )

        assert result.correlation_id == "test-123"
        assert len(result.entries) == 1
        assert "test-service" in result.services_involved

    @pytest.mark.asyncio
    async def test_find_error_chain_no_errors(self, engine):
        """Test error chain when no errors found."""
        result = await engine.find_error_chain(
            error_id="test-123",
            depth=5,
        )

        assert result.error_id == "test-123"
        assert result.root_cause_service == "unknown"
        assert len(result.propagation_path) == 0
        assert result.confidence_score == 0.0

    @pytest.mark.asyncio
    async def test_get_transaction_timeline_empty(self, engine):
        """Test transaction timeline with no data."""
        result = await engine.get_transaction_timeline(
            transaction_id="tx-123",
            time_window_minutes=30,
        )

        assert result.transaction_id == "tx-123"
        assert len(result.events) == 0
        assert result.success is True  # No errors = success


class TestTransactionTimeline:
    """Tests for TransactionTimeline dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(UTC)
        timeline = TransactionTimeline(
            transaction_id="tx-123",
            start_time=now,
            end_time=now + timedelta(seconds=5),
            total_duration_ms=5000,
            events=[
                TransactionTimelineEvent(
                    timestamp=now,
                    service_id="svc-1",
                    service_name="Service 1",
                    event_type="request",
                    message="Request received",
                )
            ],
            services_path=["svc-1", "svc-2"],
            success=True,
            error_message=None,
        )

        result = timeline.to_dict()

        assert result["transaction_id"] == "tx-123"
        assert result["total_duration_ms"] == 5000
        assert len(result["events"]) == 1
        assert result["success"] is True
