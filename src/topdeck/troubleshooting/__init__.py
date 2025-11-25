"""
Troubleshooting module for TopDeck.

This module provides advanced troubleshooting capabilities to fill critical
market gaps in SRE tooling:

- Log Correlation Engine: Correlate logs across distributed services
- Error Context Aggregation: Capture complete error context automatically
- Dependency Health Dashboard: Real-time dependency health monitoring

These features address the most requested SRE needs based on market research.
"""

from .log_correlation import (
    CorrelatedLogs,
    ErrorChain,
    LogCorrelationEngine,
    TransactionTimeline,
)
from .error_context import (
    ErrorContext,
    ErrorContextAggregator,
    ContextSnapshot,
)
from .dependency_health import (
    DependencyHealthMonitor,
    DependencyHealthReport,
    DependencyStatus,
    ConnectionPoolStatus,
)

__all__ = [
    # Log Correlation
    "LogCorrelationEngine",
    "CorrelatedLogs",
    "ErrorChain",
    "TransactionTimeline",
    # Error Context
    "ErrorContextAggregator",
    "ErrorContext",
    "ContextSnapshot",
    # Dependency Health
    "DependencyHealthMonitor",
    "DependencyHealthReport",
    "DependencyStatus",
    "ConnectionPoolStatus",
]
