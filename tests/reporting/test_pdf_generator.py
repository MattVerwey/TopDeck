"""
Tests for PDF Generator.

Tests the PDF generation functionality for reports.
"""

from datetime import UTC, datetime

import pytest

from topdeck.reporting.models import (
    Report,
    ReportFormat,
    ReportMetadata,
    ReportSection,
    ReportStatus,
    ReportType,
)
from topdeck.reporting.pdf_generator import PDFGenerator


@pytest.fixture
def sample_report() -> Report:
    """Create a sample report for testing."""
    metadata = ReportMetadata(
        report_id="test-report-123",
        report_type=ReportType.COMPREHENSIVE,
        report_format=ReportFormat.PDF,
        generated_at=datetime.now(UTC),
        resource_id="test-resource-456",
        resource_name="Test Resource",
    )

    sections = [
        ReportSection(
            title="Overview",
            content="This is a test report overview with **bold text** and bullet points:\n- Item 1\n- Item 2\n- Item 3",
            section_type="text",
            order=1,
        ),
        ReportSection(
            title="Error Summary",
            content="| Time | Severity | Message |\n|------|----------|----------|\n| 2024-01-01 | high | Error 1 |\n| 2024-01-02 | medium | Error 2 |",
            section_type="table",
            order=2,
        ),
        ReportSection(
            title="Chart Data",
            content="Performance metrics over time",
            section_type="chart",
            charts=[
                {
                    "type": "line",
                    "title": "Error Timeline",
                    "data": {
                        "labels": ["10:00", "11:00", "12:00"],
                        "datasets": [
                            {
                                "label": "Errors",
                                "data": [5, 12, 8],
                            }
                        ],
                    },
                }
            ],
            order=3,
        ),
    ]

    return Report(
        metadata=metadata,
        title="Test Comprehensive Report",
        summary="This is a test report summary covering the last 24 hours.",
        sections=sections,
        status=ReportStatus.COMPLETED,
    )


def test_pdf_generator_initialization():
    """Test PDF generator can be initialized."""
    generator = PDFGenerator()
    assert generator is not None
    assert generator.page_size is not None


def test_generate_pdf_basic(sample_report):
    """Test basic PDF generation."""
    generator = PDFGenerator()
    pdf_bytes = generator.generate_pdf(sample_report)

    # Verify we got a PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

    # Check PDF magic bytes
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_pdf_with_sections(sample_report):
    """Test PDF generation includes all sections."""
    generator = PDFGenerator()
    pdf_bytes = generator.generate_pdf(sample_report)

    # Verify PDF was created
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000  # Should be substantial with content


def test_generate_pdf_with_empty_report():
    """Test PDF generation with minimal report."""
    metadata = ReportMetadata(
        report_id="empty-report",
        report_type=ReportType.RESOURCE_HEALTH,
        report_format=ReportFormat.PDF,
        generated_at=datetime.now(UTC),
    )

    report = Report(
        metadata=metadata,
        title="Empty Report",
        summary="",
        sections=[],
        status=ReportStatus.COMPLETED,
    )

    generator = PDFGenerator()
    pdf_bytes = generator.generate_pdf(report)

    # Should still generate a valid PDF
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_pdf_with_failed_status(sample_report):
    """Test PDF generation for failed report."""
    sample_report.status = ReportStatus.FAILED
    sample_report.error_message = "Test error message"

    generator = PDFGenerator()
    pdf_bytes = generator.generate_pdf(sample_report)

    # Should still generate PDF with error info
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"


def test_format_content():
    """Test content formatting."""
    generator = PDFGenerator()

    # Test bold text
    result = generator._format_content("This is **bold** text")
    assert "<b>bold</b>" in result

    # Test bullets
    result = generator._format_content("- Item 1\n- Item 2")
    assert "•" in result


def test_extract_table_data():
    """Test table data extraction from markdown."""
    generator = PDFGenerator()

    section = ReportSection(
        title="Test Table",
        content="| Header 1 | Header 2 |\n|----------|----------|\n| Value 1  | Value 2  |",
        section_type="table",
        order=1,
    )

    table_data = generator._extract_table_data(section)

    assert table_data is not None
    assert len(table_data) >= 2  # Header + at least one data row
    assert "Header 1" in table_data[0]


def test_summarize_chart_data():
    """Test chart data summarization."""
    generator = PDFGenerator()

    chart_data = {
        "labels": ["A", "B", "C"],
        "datasets": [{"label": "Test Data", "data": [10, 20, 30]}],
    }

    summary = generator._summarize_chart_data(chart_data, "bar")

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "Test Data" in summary


def test_pdf_generator_custom_page_size():
    """Test PDF generator with custom page size."""
    from reportlab.lib.pagesizes import A4

    generator = PDFGenerator(page_size=A4)
    assert generator.page_size == A4
