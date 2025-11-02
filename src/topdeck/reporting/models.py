"""
Data models for reporting.

Represents reports, report metadata, sections, and configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ReportType(str, Enum):
    """Type of report to generate."""

    RESOURCE_HEALTH = "resource_health"
    CHANGE_IMPACT = "change_impact"
    ERROR_TIMELINE = "error_timeline"
    CODE_DEPLOYMENT_CORRELATION = "code_deployment_correlation"
    COMPREHENSIVE = "comprehensive"


class ReportFormat(str, Enum):
    """Output format for reports."""

    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"


class ReportStatus(str, Enum):
    """Status of report generation."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReportMetadata:
    """Metadata about a report."""

    report_id: str
    report_type: ReportType
    report_format: ReportFormat
    generated_at: datetime
    generated_by: str | None = None
    resource_id: str | None = None
    resource_name: str | None = None
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "report_format": self.report_format.value,
            "generated_at": self.generated_at.isoformat(),
            "generated_by": self.generated_by,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "time_range_start": self.time_range_start.isoformat() if self.time_range_start else None,
            "time_range_end": self.time_range_end.isoformat() if self.time_range_end else None,
            "tags": self.tags,
        }


@dataclass
class ReportSection:
    """A section within a report."""

    title: str
    content: str
    section_type: str  # 'text', 'chart', 'table', 'image'
    data: dict[str, Any] = field(default_factory=dict)
    charts: list[dict[str, Any]] = field(default_factory=list)
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "title": self.title,
            "content": self.content,
            "section_type": self.section_type,
            "data": self.data,
            "charts": self.charts,
            "order": self.order,
        }


@dataclass
class Report:
    """Complete report with all sections and metadata."""

    metadata: ReportMetadata
    title: str
    summary: str
    sections: list[ReportSection] = field(default_factory=list)
    status: ReportStatus = ReportStatus.PENDING
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "metadata": self.metadata.to_dict(),
            "title": self.title,
            "summary": self.summary,
            "sections": [section.to_dict() for section in self.sections],
            "status": self.status.value,
            "error_message": self.error_message,
        }


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    resource_id: str | None = None
    service_name: str | None = None
    time_range_hours: int = 24
    include_charts: bool = True
    include_error_details: bool = True
    include_change_details: bool = True
    include_code_changes: bool = True
    max_errors: int = 50
    max_changes: int = 20
