"""
Reporting API endpoints.

Provides API endpoints for generating and retrieving reports with charts
and analysis showing resource health, changes, errors, and correlations.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from topdeck.common.config import settings
from topdeck.reporting import (
    ReportFormat,
    ReportingService,
    ReportType,
)
from topdeck.reporting.models import ReportConfig
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


# Pydantic models for API requests/responses


class GenerateReportRequest(BaseModel):
    """Request model for generating a report."""

    report_type: ReportType
    report_format: ReportFormat = Field(default=ReportFormat.JSON)
    resource_id: str | None = None
    service_name: str | None = None
    time_range_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 7 days
    include_charts: bool = True
    include_error_details: bool = True
    include_change_details: bool = True
    include_code_changes: bool = True
    max_errors: int = Field(default=50, ge=1, le=500)
    max_changes: int = Field(default=20, ge=1, le=100)


class ReportResponse(BaseModel):
    """Response model for a report."""

    metadata: dict[str, Any]
    title: str
    summary: str
    sections: list[dict[str, Any]]
    status: str
    error_message: str | None = None


class ReportListResponse(BaseModel):
    """Response model for listing reports."""

    reports: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


# Dependency for Neo4j client
def get_neo4j_client():
    """Get Neo4j client instance with proper lifecycle management."""
    client = Neo4jClient(
        uri=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
    )
    try:
        yield client
    finally:
        client.close()


# Dependency for reporting service
def get_reporting_service(neo4j_client: Neo4jClient = Depends(get_neo4j_client)) -> ReportingService:
    """Get reporting service instance."""
    return ReportingService(neo4j_client)


# API Endpoints


@router.post("/generate", response_model=None)
async def generate_report(
    request: GenerateReportRequest,
    reporting_service: ReportingService = Depends(get_reporting_service),
) -> Response | dict[str, Any]:
    """
    Generate a new report based on the specified parameters.

    This endpoint generates comprehensive reports with charts and analysis showing:
    - Resource health metrics and status
    - Changes that affected resources/services
    - Error timeline and patterns
    - Code changes and deployment correlation
    - When resources became unstable or started erroring

    Args:
        request: Report generation parameters

    Returns:
        Generated report with all sections and charts (JSON format)
        or PDF document (when report_format is 'pdf')

    Example:
        ```
        POST /api/v1/reports/generate
        {
            "report_type": "comprehensive",
            "resource_id": "resource-123",
            "time_range_hours": 48,
            "include_charts": true,
            "report_format": "json"
        }
        ```

        For PDF export:
        ```
        POST /api/v1/reports/generate
        {
            "report_type": "comprehensive",
            "resource_id": "resource-123",
            "time_range_hours": 48,
            "report_format": "pdf"
        }
        ```
    """
    try:
        # Create report config from request
        config = ReportConfig(
            resource_id=request.resource_id,
            service_name=request.service_name,
            time_range_hours=request.time_range_hours,
            include_charts=request.include_charts,
            include_error_details=request.include_error_details,
            include_change_details=request.include_change_details,
            include_code_changes=request.include_code_changes,
            max_errors=request.max_errors,
            max_changes=request.max_changes,
        )

        # Generate report
        report = reporting_service.generate_report(
            report_type=request.report_type,
            report_format=request.report_format,
            config=config,
        )

        # Return PDF if requested
        if request.report_format == ReportFormat.PDF:
            pdf_bytes = reporting_service.export_report_as_pdf(report)
            filename = f"{request.report_type.value}_{report.metadata.report_id}.pdf"
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        return report.to_dict()

    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/types", response_model=list[str])
async def get_report_types() -> list[str]:
    """
    Get available report types.

    Returns:
        List of available report types

    Report Types:
    - resource_health: Health metrics and status for a resource
    - change_impact: Analysis of changes and their impact
    - error_timeline: Timeline of errors and their patterns
    - code_deployment_correlation: Correlation between deployments and errors
    - comprehensive: Combined report with all information
    """
    return [t.value for t in ReportType]


@router.get("/formats", response_model=list[str])
async def get_report_formats() -> list[str]:
    """
    Get available report output formats.

    Returns:
        List of available report formats

    Formats:
    - json: JSON format (structured data)
    - html: HTML format (for web display)
    - markdown: Markdown format (for documentation)
    - pdf: PDF format (for printing and archival)
    """
    return [f.value for f in ReportFormat]


@router.post("/resource/{resource_id}", response_model=None)
async def generate_resource_report(
    resource_id: str,
    reporting_service: ReportingService = Depends(get_reporting_service),
    report_type: ReportType = Query(
        default=ReportType.COMPREHENSIVE, description="Type of report to generate"
    ),
    report_format: ReportFormat = Query(
        default=ReportFormat.JSON, description="Output format for the report"
    ),
    time_range_hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    include_charts: bool = Query(default=True, description="Include charts in report"),
) -> Response | dict[str, Any]:
    """
    Generate a report for a specific resource.

    This is a convenience endpoint for quickly generating reports for a resource
    without specifying all parameters.

    Args:
        resource_id: ID of the resource to report on
        report_type: Type of report to generate
        report_format: Output format (json, html, markdown, pdf)
        time_range_hours: Time range in hours (1-168)
        include_charts: Whether to include charts

    Returns:
        Generated report (JSON format or PDF document)

    Example:
        ```
        POST /api/v1/reports/resource/resource-123?report_type=comprehensive&time_range_hours=48
        ```

        For PDF export:
        ```
        POST /api/v1/reports/resource/resource-123?report_format=pdf&report_type=comprehensive
        ```
    """
    try:
        config = ReportConfig(
            resource_id=resource_id,
            time_range_hours=time_range_hours,
            include_charts=include_charts,
        )

        report = reporting_service.generate_report(
            report_type=report_type,
            report_format=report_format,
            config=config,
        )

        # Return PDF if requested
        if report_format == ReportFormat.PDF:
            pdf_bytes = reporting_service.export_report_as_pdf(report)
            filename = f"{report_type.value}_{resource_id}_{report.metadata.report_id}.pdf"
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        return report.to_dict()

    except Exception as e:
        logger.error(f"Failed to generate resource report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate resource report: {str(e)}"
        )


@router.get("/health")
async def health_check(neo4j_client: Neo4jClient = Depends(get_neo4j_client)) -> dict[str, str]:
    """
    Health check endpoint for the reporting service.

    Returns:
        Health status
    """
    try:
        # Test Neo4j connection
        neo4j_client.execute_query("RETURN 1", {})
        return {"status": "healthy", "service": "reporting"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "service": "reporting", "error": str(e)}
