"""Tests for reporting models."""

from datetime import UTC, datetime

import pytest

from topdeck.reporting.models import (
    Report,
    ReportConfig,
    ReportFormat,
    ReportMetadata,
    ReportSection,
    ReportStatus,
    ReportType,
)


def test_report_metadata_creation():
    """Test creating report metadata."""
    metadata = ReportMetadata(
        report_id="test-123",
        report_type=ReportType.RESOURCE_HEALTH,
        report_format=ReportFormat.JSON,
        generated_at=datetime.now(UTC),
        resource_id="resource-456",
    )

    assert metadata.report_id == "test-123"
    assert metadata.report_type == ReportType.RESOURCE_HEALTH
    assert metadata.report_format == ReportFormat.JSON
    assert metadata.resource_id == "resource-456"


def test_report_metadata_to_dict():
    """Test converting report metadata to dictionary."""
    now = datetime.now(UTC)
    metadata = ReportMetadata(
        report_id="test-123",
        report_type=ReportType.CHANGE_IMPACT,
        report_format=ReportFormat.HTML,
        generated_at=now,
        resource_id="resource-456",
        resource_name="Test Resource",
    )

    metadata_dict = metadata.to_dict()

    assert metadata_dict["report_id"] == "test-123"
    assert metadata_dict["report_type"] == "change_impact"
    assert metadata_dict["report_format"] == "html"
    assert metadata_dict["resource_id"] == "resource-456"
    assert metadata_dict["resource_name"] == "Test Resource"
    assert metadata_dict["generated_at"] == now.isoformat()


def test_report_section_creation():
    """Test creating report section."""
    section = ReportSection(
        title="Test Section",
        content="Test content",
        section_type="text",
        data={"key": "value"},
        order=1,
    )

    assert section.title == "Test Section"
    assert section.content == "Test content"
    assert section.section_type == "text"
    assert section.data == {"key": "value"}
    assert section.order == 1


def test_report_section_to_dict():
    """Test converting report section to dictionary."""
    section = ReportSection(
        title="Chart Section",
        content="Chart description",
        section_type="chart",
        data={"values": [1, 2, 3]},
        charts=[{"type": "line"}],
        order=2,
    )

    section_dict = section.to_dict()

    assert section_dict["title"] == "Chart Section"
    assert section_dict["content"] == "Chart description"
    assert section_dict["section_type"] == "chart"
    assert section_dict["data"] == {"values": [1, 2, 3]}
    assert section_dict["charts"] == [{"type": "line"}]
    assert section_dict["order"] == 2


def test_report_creation():
    """Test creating a complete report."""
    metadata = ReportMetadata(
        report_id="test-123",
        report_type=ReportType.COMPREHENSIVE,
        report_format=ReportFormat.JSON,
        generated_at=datetime.now(UTC),
    )

    sections = [
        ReportSection(
            title="Section 1",
            content="Content 1",
            section_type="text",
            order=1,
        ),
        ReportSection(
            title="Section 2",
            content="Content 2",
            section_type="chart",
            order=2,
        ),
    ]

    report = Report(
        metadata=metadata,
        title="Test Report",
        summary="Test summary",
        sections=sections,
        status=ReportStatus.COMPLETED,
    )

    assert report.metadata == metadata
    assert report.title == "Test Report"
    assert report.summary == "Test summary"
    assert len(report.sections) == 2
    assert report.status == ReportStatus.COMPLETED
    assert report.error_message is None


def test_report_to_dict():
    """Test converting report to dictionary."""
    metadata = ReportMetadata(
        report_id="test-123",
        report_type=ReportType.ERROR_TIMELINE,
        report_format=ReportFormat.JSON,
        generated_at=datetime.now(UTC),
    )

    section = ReportSection(
        title="Errors",
        content="Error list",
        section_type="table",
        order=1,
    )

    report = Report(
        metadata=metadata,
        title="Error Report",
        summary="Error summary",
        sections=[section],
        status=ReportStatus.COMPLETED,
    )

    report_dict = report.to_dict()

    assert report_dict["title"] == "Error Report"
    assert report_dict["summary"] == "Error summary"
    assert report_dict["status"] == "completed"
    assert len(report_dict["sections"]) == 1
    assert report_dict["sections"][0]["title"] == "Errors"
    assert report_dict["error_message"] is None


def test_report_config_defaults():
    """Test report config default values."""
    config = ReportConfig()

    assert config.resource_id is None
    assert config.service_name is None
    assert config.time_range_hours == 24
    assert config.include_charts is True
    assert config.include_error_details is True
    assert config.include_change_details is True
    assert config.include_code_changes is True
    assert config.max_errors == 50
    assert config.max_changes == 20


def test_report_config_custom():
    """Test report config with custom values."""
    config = ReportConfig(
        resource_id="resource-123",
        service_name="my-service",
        time_range_hours=48,
        include_charts=False,
        max_errors=100,
    )

    assert config.resource_id == "resource-123"
    assert config.service_name == "my-service"
    assert config.time_range_hours == 48
    assert config.include_charts is False
    assert config.max_errors == 100


def test_report_types_enum():
    """Test ReportType enum values."""
    assert ReportType.RESOURCE_HEALTH.value == "resource_health"
    assert ReportType.CHANGE_IMPACT.value == "change_impact"
    assert ReportType.ERROR_TIMELINE.value == "error_timeline"
    assert ReportType.CODE_DEPLOYMENT_CORRELATION.value == "code_deployment_correlation"
    assert ReportType.COMPREHENSIVE.value == "comprehensive"


def test_report_formats_enum():
    """Test ReportFormat enum values."""
    assert ReportFormat.JSON.value == "json"
    assert ReportFormat.HTML.value == "html"
    assert ReportFormat.MARKDOWN.value == "markdown"


def test_report_status_enum():
    """Test ReportStatus enum values."""
    assert ReportStatus.PENDING.value == "pending"
    assert ReportStatus.GENERATING.value == "generating"
    assert ReportStatus.COMPLETED.value == "completed"
    assert ReportStatus.FAILED.value == "failed"
