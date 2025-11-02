"""
Example script demonstrating TopDeck reporting functionality.

This example shows how to generate various types of reports programmatically.
"""

import json
import os
import sys

# Add src to path for imports, relative to this file's location
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from topdeck.reporting.models import ReportConfig


def print_section_divider(title: str) -> None:
    """Print a section divider."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_report_types() -> None:
    """Show available report types."""
    print_section_divider("Available Report Types")

    report_types = [
        ("resource_health", "Track health metrics and status over time"),
        ("change_impact", "Analyze what changes affected resources"),
        ("error_timeline", "Visualize when resources became unstable"),
        (
            "code_deployment_correlation",
            "Correlate code changes with stability",
        ),
        ("comprehensive", "All-in-one view with complete analysis"),
    ]

    for report_type, description in report_types:
        print(f"• {report_type:35} - {description}")


def example_report_config() -> None:
    """Show how to configure reports."""
    print_section_divider("Report Configuration Examples")

    # Basic config
    print("1. Basic Configuration:")
    config1 = ReportConfig(
        resource_id="api-gateway-prod",
        time_range_hours=24,
    )
    print(f"   Resource: {config1.resource_id}")
    print(f"   Time Range: {config1.time_range_hours} hours")
    print(f"   Include Charts: {config1.include_charts}")

    # Custom config
    print("\n2. Custom Configuration:")
    config2 = ReportConfig(
        resource_id="database-prod",
        time_range_hours=48,
        include_charts=True,
        include_error_details=True,
        max_errors=100,
        max_changes=30,
    )
    print(f"   Resource: {config2.resource_id}")
    print(f"   Time Range: {config2.time_range_hours} hours")
    print(f"   Max Errors: {config2.max_errors}")
    print(f"   Max Changes: {config2.max_changes}")

    # System-wide report (no resource ID)
    print("\n3. System-Wide Report Configuration:")
    config3 = ReportConfig(
        time_range_hours=168,  # 1 week
        include_charts=True,
    )
    print(f"   Resource: All resources (resource_id is None)")
    print(f"   Time Range: {config3.time_range_hours} hours (1 week)")


def example_api_usage() -> None:
    """Show example API usage with curl commands."""
    print_section_divider("API Usage Examples")

    examples = [
        (
            "Generate Comprehensive Report (JSON)",
            """curl -X POST http://localhost:8000/api/v1/reports/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "report_type": "comprehensive",
    "resource_id": "api-gateway-prod",
    "time_range_hours": 48,
    "include_charts": true,
    "report_format": "json"
  }'""",
        ),
        (
            "Generate PDF Report",
            """curl -X POST http://localhost:8000/api/v1/reports/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "report_type": "comprehensive",
    "resource_id": "api-gateway-prod",
    "time_range_hours": 48,
    "report_format": "pdf"
  }' \\
  -o report.pdf""",
        ),
        (
            "Quick Resource Health Report",
            'curl -X POST "http://localhost:8000/api/v1/reports/resource/db-prod?report_type=resource_health&time_range_hours=24"',
        ),
        (
            "Quick PDF Export for Resource",
            'curl -X POST "http://localhost:8000/api/v1/reports/resource/db-prod?report_format=pdf&report_type=comprehensive" -o db-report.pdf',
        ),
        (
            "Error Timeline Report",
            """curl -X POST http://localhost:8000/api/v1/reports/generate \\
  -d '{"report_type":"error_timeline","resource_id":"web-app","time_range_hours":72}'""",
        ),
        (
            "List Available Report Types",
            """curl http://localhost:8000/api/v1/reports/types""",
        ),
        (
            "List Available Report Formats",
            """curl http://localhost:8000/api/v1/reports/formats""",
        ),
    ]

    for i, (title, command) in enumerate(examples, 1):
        print(f"{i}. {title}:")
        print(f"   {command}\n")


def example_python_usage() -> None:
    """Show example Python usage."""
    print_section_divider("Python Integration Example")

    code = """
import requests

def generate_incident_report(resource_id: str, hours: int = 24, as_pdf: bool = False):
    \"\"\"Generate comprehensive incident report.\"\"\"
    response = requests.post(
        "http://localhost:8000/api/v1/reports/generate",
        json={
            "report_type": "comprehensive",
            "resource_id": resource_id,
            "time_range_hours": hours,
            "include_charts": True,
            "report_format": "pdf" if as_pdf else "json"
        }
    )
    
    if as_pdf:
        # Save PDF to file
        with open(f"report_{resource_id}.pdf", "wb") as f:
            f.write(response.content)
        return f"PDF saved to report_{resource_id}.pdf"
    else:
        return response.json()

# Generate JSON report
report = generate_incident_report("api-gateway-prod", 48, as_pdf=False)

# Print report summary
print(f"Report: {report['title']}")
print(f"Summary: {report['summary']}")
print(f"Status: {report['status']}")
print(f"Sections: {len(report['sections'])}")

# Process sections
for section in report['sections']:
    print(f"\\n{section['title']}")
    print(section['content'])
    
    # Render charts
    if section.get('charts'):
        for chart in section['charts']:
            print(f"  Chart: {chart['title']} ({chart['type']})")

# Generate PDF report
pdf_result = generate_incident_report("api-gateway-prod", 48, as_pdf=True)
print(pdf_result)
"""
    print(code)


def example_use_cases() -> None:
    """Show common use cases."""
    print_section_divider("Common Use Cases")

    use_cases = [
        (
            "Post-Incident Analysis",
            "comprehensive",
            24,
            "Get complete timeline of what happened during an incident",
        ),
        (
            "Deployment Validation",
            "code_deployment_correlation",
            8,
            "Check if recent deployment caused stability issues",
        ),
        (
            "Daily Health Check",
            "resource_health",
            24,
            "Monitor critical resource health daily",
        ),
        (
            "Weekly Change Review",
            "change_impact",
            168,
            "Review all changes made during the week",
        ),
        (
            "Error Investigation",
            "error_timeline",
            72,
            "Investigate error patterns over 3 days",
        ),
    ]

    for i, (use_case, report_type, hours, description) in enumerate(
        use_cases, 1
    ):
        print(f"{i}. {use_case}")
        print(f"   Report Type: {report_type}")
        print(f"   Time Range: {hours} hours")
        print(f"   Purpose: {description}\n")


def example_chart_data() -> None:
    """Show example chart data structure."""
    print_section_divider("Chart Data Format")

    chart_example = {
        "type": "line",
        "title": "Error Timeline",
        "x_label": "Time",
        "y_label": "Error Count",
        "data": {
            "labels": [
                "2024-11-01 10:00",
                "2024-11-01 11:00",
                "2024-11-01 12:00",
            ],
            "datasets": [
                {
                    "label": "Total Errors",
                    "data": [5, 12, 8],
                    "color": "red",
                },
                {
                    "label": "Critical Severity",
                    "data": [2, 5, 3],
                    "color": "#dc3545",
                },
            ],
        },
    }

    print("Example chart data structure:")
    print(json.dumps(chart_example, indent=2))

    print("\n\nChart types supported:")
    chart_types = [
        ("line", "Time series data (errors, metrics over time)"),
        ("bar", "Categorical data (changes by type)"),
        ("pie", "Distribution data (risk levels)"),
        ("combo", "Mixed types (deployments + errors)"),
    ]
    for chart_type, description in chart_types:
        print(f"  • {chart_type:10} - {description}")


def main() -> None:
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "TopDeck Reporting Examples" + " " * 32 + "║")
    print("╚" + "═" * 78 + "╝")

    # Show all examples
    example_report_types()
    example_report_config()
    example_api_usage()
    example_python_usage()
    example_use_cases()
    example_chart_data()

    # Summary
    print_section_divider("Next Steps")
    print("1. Start the TopDeck API server:")
    print("   make run")
    print("\n2. Generate your first report:")
    print(
        '   curl -X POST "http://localhost:8000/api/v1/reports/resource/YOUR-RESOURCE-ID?report_type=comprehensive&time_range_hours=24"'
    )
    print("\n3. Read the full documentation:")
    print("   • docs/REPORTING_GUIDE.md")
    print("   • docs/REPORTING_QUICK_REF.md")
    print("\n4. Explore the API documentation:")
    print("   http://localhost:8000/api/docs")
    print("\n")


if __name__ == "__main__":
    main()
