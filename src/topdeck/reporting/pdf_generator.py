"""
PDF Generator for Reports.

Provides functionality to convert reports into PDF format with charts and formatting.
"""

import io
import logging
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from topdeck.reporting.models import Report, ReportSection

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generator for creating PDF reports."""

    def __init__(self, page_size: tuple[float, float] = letter) -> None:
        """
        Initialize PDF generator.

        Args:
            page_size: Page size tuple (width, height). Default is letter size.
        """
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles for the PDF."""
        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=30,
                alignment=1,  # Center
            )
        )

        # Section heading style
        self.styles.add(
            ParagraphStyle(
                name="SectionHeading",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=12,
                spaceBefore=20,
            )
        )

        # Subsection style
        self.styles.add(
            ParagraphStyle(
                name="SubsectionHeading",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#34495e"),
                spaceAfter=10,
                spaceBefore=15,
            )
        )

        # Metadata style
        self.styles.add(
            ParagraphStyle(
                name="Metadata",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#7f8c8d"),
                spaceAfter=20,
            )
        )

    def generate_pdf(self, report: Report) -> bytes:
        """
        Generate a PDF document from a Report object.

        Args:
            report: Report object to convert to PDF

        Returns:
            PDF document as bytes
        """
        buffer = io.BytesIO()

        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build the story (content)
        story = []

        # Add title
        story.append(Paragraph(report.title, self.styles["CustomTitle"]))
        story.append(Spacer(1, 12))

        # Add metadata
        metadata_text = self._format_metadata(report.metadata.to_dict())
        story.append(Paragraph(metadata_text, self.styles["Metadata"]))
        story.append(Spacer(1, 12))

        # Add summary
        if report.summary:
            story.append(Paragraph("<b>Summary</b>", self.styles["SectionHeading"]))
            story.append(Paragraph(report.summary, self.styles["Normal"]))
            story.append(Spacer(1, 20))

        # Add sections
        for section in sorted(report.sections, key=lambda s: s.order):
            story.extend(self._generate_section(section))

        # Add status footer if not completed
        if report.status.value != "completed":
            story.append(Spacer(1, 20))
            status_text = f"<b>Report Status:</b> {report.status.value.upper()}"
            if report.error_message:
                status_text += f"<br/><b>Error:</b> {report.error_message}"
            story.append(Paragraph(status_text, self.styles["Normal"]))

        # Build PDF
        doc.build(story)

        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _format_metadata(self, metadata: dict[str, Any]) -> str:
        """Format metadata for display in PDF."""
        parts = []

        if metadata.get("generated_at"):
            try:
                # Handle ISO format with 'Z' suffix and microseconds
                dt_str = metadata["generated_at"]
                if isinstance(dt_str, str):
                    # Replace 'Z' with '+00:00' for ISO format compatibility
                    dt_str = dt_str.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(dt_str)
                    parts.append(f"Generated: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                else:
                    parts.append(f"Generated: {metadata['generated_at']}")
            except (ValueError, TypeError, AttributeError):
                parts.append(f"Generated: {metadata['generated_at']}")

        if metadata.get("report_type"):
            parts.append(f"Type: {metadata['report_type'].replace('_', ' ').title()}")

        if metadata.get("resource_id"):
            parts.append(f"Resource ID: {metadata['resource_id']}")

        if metadata.get("time_range_start") and metadata.get("time_range_end"):
            parts.append(
                f"Time Range: {metadata['time_range_start']} to {metadata['time_range_end']}"
            )

        return " | ".join(parts)

    def _generate_section(self, section: ReportSection) -> list:
        """
        Generate PDF elements for a report section.

        Args:
            section: ReportSection to render

        Returns:
            List of reportlab elements
        """
        elements = []

        # Section title
        elements.append(Paragraph(section.title, self.styles["SectionHeading"]))
        elements.append(Spacer(1, 6))

        # Handle tables first if section is table type
        if section.section_type == "table":
            table_data = self._extract_table_data(section)
            if table_data:
                elements.extend(self._create_table(table_data))
            elif section.content:
                # If no table found in content, render as normal text
                content = self._format_content(section.content)
                elements.append(Paragraph(content, self.styles["Normal"]))
                elements.append(Spacer(1, 12))
        elif section.content:
            # Convert markdown-style content to formatted text
            content = self._format_content(section.content)
            elements.append(Paragraph(content, self.styles["Normal"]))
            elements.append(Spacer(1, 12))

        # Handle charts
        if section.charts:
            for chart in section.charts:
                elements.extend(self._generate_chart_section(chart))

        elements.append(Spacer(1, 20))

        return elements

    def _format_content(self, content: str) -> str:
        """
        Format markdown-style content for PDF display.

        Args:
            content: Raw content string (may include markdown)

        Returns:
            HTML-formatted string for Paragraph rendering
        """
        # Replace markdown bold with HTML bold
        # Split by ** and alternate between opening and closing tags
        parts = content.split("**")
        formatted = []
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Odd indices are bold text
                formatted.append(f"<b>{part}</b>")
            else:
                formatted.append(part)
        content = "".join(formatted)

        # Replace markdown bullets with HTML
        lines = content.split("\n")
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith("- "):
                formatted_lines.append(f"• {line[2:]}")
            elif line.startswith("• "):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        return "<br/>".join(formatted_lines)

    def _extract_table_data(self, section: ReportSection) -> list[list[str]] | None:
        """
        Extract table data from section for rendering.

        Args:
            section: Section containing table data

        Returns:
            Table data as list of rows, or None if no table data
        """
        # Check if content contains a markdown table
        if section.content and "|" in section.content:
            lines = [line.strip() for line in section.content.split("\n") if line.strip()]
            table_lines = [line for line in lines if line.startswith("|")]

            if len(table_lines) >= 2:  # At least header and separator
                table_data = []
                for i, line in enumerate(table_lines):
                    # Skip separator line (usually second line)
                    if i == 1 and all(c in "|-: " for c in line):
                        continue

                    # Split by | and clean up
                    cells = [cell.strip() for cell in line.split("|")]
                    # Remove empty first and last elements from split
                    cells = [cell for cell in cells if cell]
                    if cells:
                        table_data.append(cells)

                return table_data if len(table_data) > 1 else None

        return None

    def _create_table(self, data: list[list[str]]) -> list:
        """
        Create a formatted table.

        Args:
            data: Table data as list of rows

        Returns:
            List of reportlab elements
        """
        elements = []

        # Create table
        table = Table(data, hAlign="LEFT")

        # Style the table
        table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    # Data rows
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 12))

        return elements

    def _generate_chart_section(self, chart: dict[str, Any]) -> list:
        """
        Generate chart section in PDF.

        Note: This provides a text-based representation of chart data.
        For actual chart images, integration with a charting library
        (like matplotlib) would be needed.

        Args:
            chart: Chart data dictionary

        Returns:
            List of reportlab elements
        """
        elements = []

        chart_title = chart.get("title", "Chart")
        elements.append(Paragraph(f"<b>{chart_title}</b>", self.styles["SubsectionHeading"]))

        chart_type = chart.get("type", "unknown")
        elements.append(Paragraph(f"<i>Chart Type: {chart_type}</i>", self.styles["Normal"]))

        # Add chart data summary
        data = chart.get("data", {})
        if data:
            summary = self._summarize_chart_data(data, chart_type)
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(summary, self.styles["Normal"]))

        elements.append(Spacer(1, 12))

        return elements

    def _summarize_chart_data(self, data: dict[str, Any], chart_type: str) -> str:
        """
        Create a text summary of chart data.

        Args:
            data: Chart data dictionary
            chart_type: Type of chart

        Returns:
            Text summary of the data
        """
        summary_parts = []

        labels = data.get("labels", [])
        datasets = data.get("datasets", [])

        if chart_type == "pie":
            # For pie charts, show distribution
            for i, dataset in enumerate(datasets):
                dataset_label = dataset.get("label", f"Dataset {i+1}")
                dataset_data = dataset.get("data", [])

                summary_parts.append(f"<b>{dataset_label}:</b>")
                for j, value in enumerate(dataset_data):
                    label = labels[j] if j < len(labels) else f"Item {j+1}"
                    summary_parts.append(f"  • {label}: {value}")

        elif chart_type in ["line", "bar"]:
            # For line/bar charts, show data points
            for i, dataset in enumerate(datasets):
                dataset_label = dataset.get("label", f"Dataset {i+1}")
                dataset_data = dataset.get("data", [])

                summary_parts.append(f"<b>{dataset_label}:</b>")

                # Show first few and last few data points if many
                if len(dataset_data) > 10:
                    # Show first 3
                    for j in range(min(3, len(dataset_data))):
                        label = labels[j] if j < len(labels) else f"Point {j+1}"
                        summary_parts.append(f"  • {label}: {dataset_data[j]}")
                    summary_parts.append(f"  • ... ({len(dataset_data) - 6} more points)")
                    # Show last 3
                    for j in range(max(3, len(dataset_data) - 3), len(dataset_data)):
                        label = labels[j] if j < len(labels) else f"Point {j+1}"
                        summary_parts.append(f"  • {label}: {dataset_data[j]}")
                else:
                    # Show all points
                    for j, value in enumerate(dataset_data):
                        label = labels[j] if j < len(labels) else f"Point {j+1}"
                        summary_parts.append(f"  • {label}: {value}")

        else:
            # Generic summary
            summary_parts.append(f"Data contains {len(datasets)} dataset(s)")
            if labels:
                summary_parts.append(f"with {len(labels)} data points")

        return "<br/>".join(summary_parts)
