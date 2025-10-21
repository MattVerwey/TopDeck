"""
Logging configuration for structured logging.

Provides JSON-formatted logging with correlation IDs and context.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import Any

# Context variable for correlation ID
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs log records as JSON for easy parsing and aggregation.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class ContextLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds context to log messages.

    Automatically includes correlation ID and custom context.
    """

    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None):
        """
        Initialize context logger.

        Args:
            logger: Base logger
            context: Additional context to include in logs
        """
        super().__init__(logger, context or {})

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple:
        """
        Process log message to add context.

        Args:
            msg: Log message
            kwargs: Keyword arguments

        Returns:
            Tuple of (message, kwargs)
        """
        # Add correlation ID
        correlation_id = correlation_id_var.get()
        if correlation_id:
            if "extra" not in kwargs:
                kwargs["extra"] = {}
            kwargs["extra"]["correlation_id"] = correlation_id

        # Add custom context
        if self.extra:
            if "extra" not in kwargs:
                kwargs["extra"] = {}
            kwargs["extra"].update(self.extra)

        return msg, kwargs


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
):
    """
    Set up application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON format
        log_file: Optional file path for logging
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str, context: dict[str, Any] | None = None) -> ContextLogger:
    """
    Get a context-aware logger.

    Args:
        name: Logger name
        context: Additional context for this logger

    Returns:
        ContextLogger instance
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, context)


def set_correlation_id(correlation_id: str):
    """
    Set correlation ID for current context.

    Args:
        correlation_id: Unique identifier for request/operation
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str | None:
    """
    Get current correlation ID.

    Returns:
        Correlation ID or None
    """
    return correlation_id_var.get()


class LoggingContext:
    """
    Context manager for temporary logging context.

    Usage:
        with LoggingContext(operation="discovery", resource_type="vm"):
            logger.info("Discovering resources")
    """

    def __init__(self, **context):
        """
        Initialize logging context.

        Args:
            **context: Key-value pairs to add to log context
        """
        self.context = context
        self.original_factory = None

    def __enter__(self):
        """Enter context."""
        # Store old factory
        self.original_factory = logging.getLogRecordFactory()

        # Create new factory with context
        old_factory = self.original_factory
        context = self.context

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            if not hasattr(record, "extra_data"):
                record.extra_data = {}
            record.extra_data.update(context)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        # Restore original factory
        if self.original_factory:
            logging.setLogRecordFactory(self.original_factory)


def log_operation_metrics(
    operation: str,
    duration: float,
    success: bool,
    items_processed: int = 0,
    errors: int = 0,
    **extra,
):
    """
    Log operation metrics for monitoring.

    Args:
        operation: Name of the operation
        duration: Duration in seconds
        success: Whether operation succeeded
        items_processed: Number of items processed
        errors: Number of errors encountered
        **extra: Additional metrics
    """
    logger = logging.getLogger("topdeck.metrics")

    metrics = {
        "operation": operation,
        "duration_seconds": round(duration, 3),
        "success": success,
        "items_processed": items_processed,
        "errors": errors,
        **extra,
    }

    logger.info(f"Operation metrics: {operation}", extra={"extra_data": metrics})
