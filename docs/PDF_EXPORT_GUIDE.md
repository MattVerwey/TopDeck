# PDF Export Guide

TopDeck now supports exporting reports as PDF documents for printing, archival, and sharing.

## Overview

Reports can be generated in multiple formats:
- **JSON**: Structured data for programmatic access
- **HTML**: Web display
- **Markdown**: Documentation
- **PDF**: Professional documents for printing and archival ✨ **NEW**

## Quick Start

### Generate PDF via API

Generate a comprehensive PDF report for a resource:

```bash
curl -X POST "http://localhost:8000/api/v1/reports/resource/your-resource-id?report_format=pdf&report_type=comprehensive" \
  -o comprehensive-report.pdf
```

### Using the Full Generate Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "comprehensive",
    "resource_id": "api-gateway-prod",
    "time_range_hours": 48,
    "report_format": "pdf"
  }' \
  -o report.pdf
```

## PDF Features

### Included in PDF Reports

- **Professional Layout**: Clean, readable document with proper spacing and typography
- **Report Metadata**: Generated date, report type, resource information, time range
- **Summary Section**: High-level overview of the report
- **All Report Sections**: Complete content from the report
- **Table Formatting**: Markdown tables converted to formatted PDF tables
- **Chart Summaries**: Text-based representation of chart data
- **Status Information**: Report generation status and any error messages

### Formatting Features

- **Bold Text**: Markdown bold (`**text**`) is converted to PDF bold
- **Bullet Lists**: Markdown bullets (`-` or `•`) are properly formatted
- **Tables**: Markdown tables with styled headers and alternating row colors
- **Section Headers**: Hierarchical heading styles for easy navigation
- **Page Breaks**: Automatic pagination for long reports
- **Professional Styling**: Blue headers, grey metadata, clean fonts

## API Endpoints

### Generate Report (POST /api/v1/reports/generate)

Generate a report with full control over all parameters.

**Request Body:**
```json
{
  "report_type": "comprehensive",
  "report_format": "pdf",
  "resource_id": "resource-123",
  "time_range_hours": 48,
  "include_charts": true,
  "include_error_details": true,
  "include_change_details": true,
  "max_errors": 50,
  "max_changes": 20
}
```

**Response:**
- PDF document (binary) with `Content-Type: application/pdf`
- Filename in `Content-Disposition` header

### Generate Resource Report (POST /api/v1/reports/resource/{resource_id})

Quick endpoint for generating resource-specific reports.

**Query Parameters:**
- `report_format`: Output format (default: `json`, options: `json`, `html`, `markdown`, `pdf`)
- `report_type`: Type of report (default: `comprehensive`)
- `time_range_hours`: Time range in hours (default: 24, range: 1-168)
- `include_charts`: Include charts (default: `true`)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/reports/resource/db-prod-001?report_format=pdf&time_range_hours=72" \
  -o database-report.pdf
```

## Python Integration

### Basic Usage

```python
import requests

def download_pdf_report(resource_id: str, hours: int = 24) -> str:
    """Download PDF report for a resource."""
    response = requests.post(
        "http://localhost:8000/api/v1/reports/generate",
        json={
            "report_type": "comprehensive",
            "resource_id": resource_id,
            "time_range_hours": hours,
            "report_format": "pdf"
        }
    )
    
    filename = f"report_{resource_id}.pdf"
    with open(filename, "wb") as f:
        f.write(response.content)
    
    return filename

# Generate and save PDF
filename = download_pdf_report("api-gateway-prod", 48)
print(f"PDF saved to {filename}")
```

### Advanced Usage with Report Service

```python
from topdeck.reporting import ReportingService, ReportType, ReportFormat
from topdeck.reporting.models import ReportConfig
from topdeck.storage.neo4j_client import Neo4jClient

# Initialize service
neo4j_client = Neo4jClient(uri="bolt://localhost:7687", username="neo4j", password="password")
reporting_service = ReportingService(neo4j_client)

# Generate report
config = ReportConfig(
    resource_id="api-gateway-prod",
    time_range_hours=48,
    include_charts=True
)

report = reporting_service.generate_report(
    report_type=ReportType.COMPREHENSIVE,
    report_format=ReportFormat.PDF,
    config=config
)

# Export to PDF
pdf_bytes = reporting_service.export_report_as_pdf(report)

# Save to file
with open("comprehensive-report.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## Report Types

All report types support PDF export:

1. **comprehensive**: All-in-one report with complete analysis
2. **resource_health**: Health metrics and status tracking
3. **change_impact**: Changes and their impact analysis
4. **error_timeline**: Error patterns and timeline
5. **code_deployment_correlation**: Deployment and stability analysis

## Use Cases

### Post-Incident Reports

Generate comprehensive incident reports in PDF for documentation:

```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "comprehensive",
    "resource_id": "failed-service-id",
    "time_range_hours": 24,
    "report_format": "pdf",
    "include_error_details": true
  }' \
  -o incident-report-$(date +%Y%m%d).pdf
```

### Monthly Health Reports

Generate monthly health reports for management:

```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "resource_health",
    "resource_id": "production-db",
    "time_range_hours": 720,
    "report_format": "pdf"
  }' \
  -o monthly-health-report.pdf
```

### Deployment Validation Reports

Document deployment outcomes:

```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "code_deployment_correlation",
    "resource_id": "api-service",
    "time_range_hours": 48,
    "report_format": "pdf"
  }' \
  -o deployment-validation.pdf
```

## Customization

### Custom Page Size

The PDF generator uses letter size by default. To customize:

```python
from reportlab.lib.pagesizes import A4
from topdeck.reporting.pdf_generator import PDFGenerator

# Create generator with A4 page size
pdf_generator = PDFGenerator(page_size=A4)

# Use in reporting service
reporting_service.pdf_generator = pdf_generator
```

## Limitations

### Chart Representation

PDF reports include text-based summaries of chart data rather than rendered chart images. This keeps the implementation simple and dependency-free while still providing valuable insights.

**Example Chart Summary:**
```
Error Timeline (line chart)
Total Errors:
  • 10:00: 5
  • 11:00: 12
  • 12:00: 8
```

For visual charts, use the HTML or JSON formats and render charts client-side.

### Large Datasets

For reports with very large datasets (hundreds of errors or changes), consider:
- Using pagination parameters (`max_errors`, `max_changes`)
- Filtering by time range
- Generating multiple focused reports instead of one comprehensive report

## Troubleshooting

### PDF Generation Fails

**Problem**: Error when generating PDF

**Solution**: Ensure ReportLab is installed:
```bash
pip install reportlab==4.0.7
```

### Large File Size

**Problem**: PDF file is too large

**Solution**: Reduce the scope of the report:
- Decrease `time_range_hours`
- Lower `max_errors` and `max_changes` values
- Use specific report types instead of comprehensive

### Missing Content

**Problem**: Some report sections are missing in PDF

**Solution**: Check that the data exists in Neo4j and the report was generated successfully. Verify the report status in the JSON response first.

## Performance Considerations

- PDF generation adds ~200-500ms to report generation time
- Memory usage increases with report size
- Consider async generation for large reports in production

## Best Practices

1. **Use Appropriate Time Ranges**: Don't request unnecessarily long time ranges
2. **Limit Data Volume**: Use `max_errors` and `max_changes` parameters
3. **Cache Reports**: Generate and cache PDFs for frequently requested reports
4. **Automate Generation**: Schedule PDF report generation during off-peak hours
5. **Archive Old Reports**: Implement a retention policy for generated PDFs

## API Reference

See the complete API documentation at http://localhost:8000/api/docs when the TopDeck server is running.

## Examples

Run the reporting examples to see PDF generation in action:

```bash
python examples/reporting_example.py
```

## Support

For issues or questions about PDF export:
- Check [REPORTING_GUIDE.md](REPORTING_GUIDE.md) for general reporting documentation
- See [REPORTING_QUICK_REF.md](REPORTING_QUICK_REF.md) for quick reference
- Open an issue on GitHub for bugs or feature requests
