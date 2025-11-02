#!/usr/bin/env python3
"""
Test script for PDF export functionality.

This script tests the PDF export feature without requiring a running server
or database connection. It creates a sample report and exports it as PDF.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from topdeck.reporting.models import (
    Report,
    ReportFormat,
    ReportMetadata,
    ReportSection,
    ReportStatus,
    ReportType,
)
from topdeck.reporting.pdf_generator import PDFGenerator


def create_sample_report() -> Report:
    """Create a sample report for testing."""
    metadata = ReportMetadata(
        report_id="test-pdf-123",
        report_type=ReportType.COMPREHENSIVE,
        report_format=ReportFormat.PDF,
        generated_at=datetime.now(UTC),
        resource_id="test-api-gateway",
        resource_name="API Gateway Production",
        time_range_start=datetime(2024, 11, 1, 0, 0, 0),
        time_range_end=datetime(2024, 11, 2, 12, 0, 0),
    )

    sections = [
        ReportSection(
            title="Executive Summary",
            content=(
                "This comprehensive report covers a 36-hour period of the API Gateway Production resource. "
                "The analysis includes **15 changes**, **23 errors**, and **8 deployments**.\n\n"
                "**Key Findings:**\n"
                "- Resource health remained stable with 99.5% uptime\n"
                "- 3 high-severity errors detected during peak traffic\n"
                "- Deployment success rate: 87.5%\n"
                "- 2 potential single points of failure identified"
            ),
            section_type="text",
            order=1,
        ),
        ReportSection(
            title="Resource Overview",
            content=(
                "**Resource Name**: API Gateway Production\n"
                "**Type**: Azure Application Gateway\n"
                "**Status**: Healthy\n"
                "**Region**: East US\n"
                "**Resource ID**: test-api-gateway\n\n"
                "The resource is a critical component serving 15 downstream services."
            ),
            section_type="text",
            order=2,
        ),
        ReportSection(
            title="Error Summary",
            content=(
                "| Time | Severity | Message | Type |\n"
                "|------|----------|---------|------|\n"
                "| 2024-11-01 14:23:15 | high | Connection timeout to backend | timeout |\n"
                "| 2024-11-01 15:45:22 | high | SSL certificate validation failed | ssl_error |\n"
                "| 2024-11-01 16:12:08 | medium | Rate limit exceeded | rate_limit |\n"
                "| 2024-11-02 09:33:41 | high | Backend service unavailable | service_unavailable |\n"
                "| 2024-11-02 10:15:19 | low | Slow response time | performance |"
            ),
            section_type="table",
            order=3,
        ),
        ReportSection(
            title="Change Impact Analysis",
            content=(
                "**Total Changes**: 15\n\n"
                "**By Type**:\n"
                "- Configuration: 8\n"
                "- Deployment: 5\n"
                "- Infrastructure: 2\n\n"
                "**By Risk Level**:\n"
                "- High: 3\n"
                "- Medium: 7\n"
                "- Low: 5\n\n"
                "The majority of changes were routine configuration updates. "
                "Three high-risk changes were properly reviewed and approved."
            ),
            section_type="text",
            order=4,
        ),
        ReportSection(
            title="Performance Metrics",
            content="CPU usage, memory consumption, and request throughput over the analysis period.",
            section_type="chart",
            charts=[
                {
                    "type": "line",
                    "title": "Request Throughput (requests/sec)",
                    "data": {
                        "labels": [
                            "00:00",
                            "04:00",
                            "08:00",
                            "12:00",
                            "16:00",
                            "20:00",
                            "24:00",
                        ],
                        "datasets": [
                            {
                                "label": "Throughput",
                                "data": [1200, 800, 1500, 2800, 3200, 2500, 1800],
                            }
                        ],
                    },
                },
                {
                    "type": "line",
                    "title": "Error Rate Over Time",
                    "data": {
                        "labels": [
                            "Nov 1 10:00",
                            "Nov 1 14:00",
                            "Nov 1 18:00",
                            "Nov 2 00:00",
                            "Nov 2 06:00",
                            "Nov 2 10:00",
                        ],
                        "datasets": [
                            {
                                "label": "Total Errors",
                                "data": [2, 8, 5, 3, 1, 4],
                                "color": "red",
                            },
                            {
                                "label": "High Severity",
                                "data": [1, 3, 2, 0, 0, 2],
                                "color": "#dc3545",
                            },
                        ],
                    },
                },
            ],
            order=5,
        ),
        ReportSection(
            title="Deployment Timeline",
            content=(
                "**Total Deployments**: 8\n\n"
                "**By Status**:\n"
                "- Success: 7\n"
                "- Failed: 1\n\n"
                "**Recent Deployments**:\n\n"
                "**1. Deployment deploy-v2.3.1**\n"
                "- Version: v2.3.1\n"
                "- Commit: abc123def456\n"
                "- Repository: api-gateway-repo\n"
                "- Status: Success\n"
                "- Deployed: 2024-11-02 08:15:30\n\n"
                "**2. Deployment deploy-v2.3.0**\n"
                "- Version: v2.3.0\n"
                "- Commit: def789ghi012\n"
                "- Repository: api-gateway-repo\n"
                "- Status: Failed\n"
                "- Deployed: 2024-11-01 16:45:12"
            ),
            section_type="text",
            order=6,
        ),
        ReportSection(
            title="Stability Analysis",
            content=(
                "**Stability Metrics**\n\n"
                "- Deployment Success Rate: 87.5%\n"
                "- Errors Per Deployment: 2.88\n"
                "- Post-Deployment Error Rate: 1.75\n\n"
                "**Unstable Periods Detected**:\n"
                "- 2024-11-01 14:00 (8 errors)\n"
                "- 2024-11-01 16:00 (6 errors)\n\n"
                "The system experienced two unstable periods coinciding with "
                "high traffic and a failed deployment. Post-deployment monitoring "
                "detected elevated error rates within the first hour after deployment."
            ),
            section_type="text",
            order=7,
        ),
        ReportSection(
            title="Recommendations",
            content=(
                "Based on the analysis, the following recommendations are suggested:\n\n"
                "**Immediate Actions**:\n"
                "- Investigate and resolve SSL certificate validation issues\n"
                "- Review rate limiting configuration for peak traffic periods\n"
                "- Implement automated rollback for failed deployments\n\n"
                "**Short-term Improvements**:\n"
                "- Add redundancy to eliminate single points of failure\n"
                "- Implement pre-deployment health checks\n"
                "- Enhance monitoring for backend service availability\n\n"
                "**Long-term Strategy**:\n"
                "- Implement gradual rollout for deployments\n"
                "- Add capacity planning based on traffic patterns\n"
                "- Establish SLA/SLO metrics and tracking"
            ),
            section_type="text",
            order=8,
        ),
    ]

    return Report(
        metadata=metadata,
        title="Comprehensive Report: API Gateway Production",
        summary=(
            "Comprehensive report covering resource health, 15 changes, 23 errors, "
            "and 8 deployments in the last 36 hours."
        ),
        sections=sections,
        status=ReportStatus.COMPLETED,
    )


def main():
    """Main test function."""
    print("TopDeck PDF Export Test")
    print("=" * 80)
    print()

    # Create sample report
    print("Creating sample report...")
    report = create_sample_report()
    print(f"✓ Report created: {report.title}")
    print(f"  - Sections: {len(report.sections)}")
    print(f"  - Status: {report.status.value}")
    print()

    # Initialize PDF generator
    print("Initializing PDF generator...")
    pdf_generator = PDFGenerator()
    print("✓ PDF generator initialized")
    print()

    # Generate PDF
    print("Generating PDF...")
    try:
        pdf_bytes = pdf_generator.generate_pdf(report)
        print(f"✓ PDF generated successfully")
        print(f"  - Size: {len(pdf_bytes):,} bytes")
        print()

        # Verify PDF
        if pdf_bytes[:4] == b"%PDF":
            print("✓ PDF file signature verified")
        else:
            print("✗ Invalid PDF file signature")
            return 1

        # Save PDF
        output_file = Path(__file__).parent.parent / "test_report.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_bytes)
        print(f"✓ PDF saved to: {output_file}")
        print()

        print("=" * 80)
        print("SUCCESS: PDF export test completed successfully!")
        print()
        print(f"Open the PDF: {output_file}")
        return 0

    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
