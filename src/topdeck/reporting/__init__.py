"""
Reporting module for TopDeck.

Provides comprehensive reporting functionality to generate reports with charts
and images based on resources or services, showing:
- Changes that affected resources/services
- Code changes and deployment timeline
- When resources became unstable or started erroring
- Correlation between errors and changes
"""

from topdeck.reporting.models import (
    Report,
    ReportFormat,
    ReportMetadata,
    ReportSection,
    ReportStatus,
    ReportType,
)

__all__ = [
    "Report",
    "ReportFormat",
    "ReportMetadata",
    "ReportSection",
    "ReportStatus",
    "ReportType",
    "ReportingService",
]


def __getattr__(name):
    """Lazy import for ReportingService to avoid requiring Neo4j at import time."""
    if name == "ReportingService":
        from topdeck.reporting.service import ReportingService

        return ReportingService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
