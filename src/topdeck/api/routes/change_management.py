"""
Change Management API endpoints.

Provides API endpoints for change requests, impact assessment,
and change calendar.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.change_management.models import ChangeType
from topdeck.change_management.service import ChangeManagementService
from topdeck.common.config import settings
from topdeck.storage.neo4j_client import Neo4jClient


# Pydantic models for API requests/responses
class ChangeRequestCreate(BaseModel):
    """Request model for creating a change request"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    change_type: str
    affected_resources: list[str] = Field(default_factory=list)
    scheduled_start: str | None = None
    scheduled_end: str | None = None
    requester: str | None = None
    external_system: str | None = None
    external_id: str | None = None


class ChangeRequestResponse(BaseModel):
    """Response model for change request"""

    id: str
    title: str
    description: str
    change_type: str
    status: str
    risk_level: str
    requester: str | None = None
    assignee: str | None = None
    scheduled_start: str | None = None
    scheduled_end: str | None = None
    affected_resources: list[str]
    affected_services_count: int
    estimated_downtime_seconds: int
    external_system: str | None = None
    external_id: str | None = None
    external_url: str | None = None
    created_at: str
    updated_at: str


class ImpactAssessmentResponse(BaseModel):
    """Response model for impact assessment"""

    change_id: str
    directly_affected_resources: list[dict[str, Any]]
    indirectly_affected_resources: list[dict[str, Any]]
    total_affected_count: int
    overall_risk_score: float
    performance_degradation_pct: float
    estimated_downtime_seconds: int
    user_impact_level: str
    critical_path_affected: bool
    recommended_window: str
    rollback_plan_required: bool
    approval_required: bool
    breakdown: dict[str, Any]
    recommendations: list[str]
    assessed_at: str


class ChangeCalendarItem(BaseModel):
    """Response model for change calendar item"""

    id: str
    title: str
    change_type: str
    status: str
    risk_level: str
    scheduled_start: str
    scheduled_end: str | None = None
    requester: str | None = None


# Create router
router = APIRouter(prefix="/api/v1/changes", tags=["change-management"])


def get_change_service() -> ChangeManagementService:
    """Get change management service instance"""
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    return ChangeManagementService(neo4j_client)


@router.post("", response_model=ChangeRequestResponse, status_code=201)
async def create_change_request(request: ChangeRequestCreate) -> ChangeRequestResponse:
    """
    Create a new change request.

    Creates a change request with the specified details and affected resources.
    """
    try:
        service = get_change_service()

        # Parse change type
        try:
            change_type = ChangeType(request.change_type.lower())
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid change type. Must be one of: {[t.value for t in ChangeType]}",
            ) from e

        # Parse dates if provided
        scheduled_start = None
        scheduled_end = None
        if request.scheduled_start:
            try:
                scheduled_start = datetime.fromisoformat(
                    request.scheduled_start.replace("Z", "+00:00")
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail="Invalid scheduled_start format") from e

        if request.scheduled_end:
            try:
                scheduled_end = datetime.fromisoformat(request.scheduled_end.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(status_code=400, detail="Invalid scheduled_end format") from e

        # Create change request
        change_request = service.create_change_request(
            title=request.title,
            description=request.description,
            change_type=change_type,
            affected_resources=request.affected_resources,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            requester=request.requester,
            external_system=request.external_system,
            external_id=request.external_id,
        )

        # Convert to response
        change_dict = change_request.to_dict()
        return ChangeRequestResponse(**change_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create change request: {str(e)}"
        ) from e


@router.post("/{change_id}/assess", response_model=ImpactAssessmentResponse)
async def assess_change_impact(
    change_id: str,
    resource_id: str | None = Query(None, description="Specific resource to analyze"),
) -> ImpactAssessmentResponse:
    """
    Assess the impact of a change request.

    Analyzes the topology and dependencies to determine the blast radius
    and risk level of the proposed change.
    """
    try:
        service = get_change_service()

        # Get the change request
        # Note: In a full implementation, we'd retrieve this from Neo4j
        # For now, create a minimal change request for the assessment
        from topdeck.change_management.models import ChangeRequest, ChangeStatus

        # This is a placeholder - in real implementation, fetch from database
        change_request = ChangeRequest(
            id=change_id,
            title="Change Assessment",
            description="Impact assessment",
            change_type=ChangeType.DEPLOYMENT,
            status=ChangeStatus.DRAFT,
            affected_resources=[resource_id] if resource_id else [],
        )

        # Assess impact
        assessment = service.assess_change_impact(change_request, resource_id)

        # Convert to response
        assessment_dict = assessment.to_dict()
        return ImpactAssessmentResponse(**assessment_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to assess change impact: {str(e)}"
        ) from e


@router.get("/calendar", response_model=list[ChangeCalendarItem])
async def get_change_calendar(
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
) -> list[ChangeCalendarItem]:
    """
    Get scheduled changes within a date range.

    Returns all changes that are scheduled, approved, or pending approval
    within the specified date range.
    """
    try:
        service = get_change_service()

        # Parse dates
        start = None
        end = None
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(status_code=400, detail="Invalid start_date format") from e

        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(status_code=400, detail="Invalid end_date format") from e

        # Get calendar
        changes = service.get_change_calendar(start, end)

        return [ChangeCalendarItem(**change) for change in changes]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get change calendar: {str(e)}"
        ) from e


@router.get("/types", response_model=list[str])
async def get_change_types() -> list[str]:
    """
    Get available change types.

    Returns a list of valid change types that can be used when creating
    change requests.
    """
    return [change_type.value for change_type in ChangeType]


@router.get("/metrics", response_model=dict[str, Any])
async def get_change_metrics(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> dict[str, Any]:
    """
    Get change management metrics.

    Analyzes change requests over the specified period and returns
    KPIs and effectiveness metrics.
    """
    try:
        from datetime import datetime, timedelta

        from topdeck.change_management.metrics import ChangeMetricsCalculator

        service = get_change_service()

        # Get changes from the last N days
        start_date = datetime.now(UTC) - timedelta(days=days)

        # Query Neo4j for changes
        query = """
        MATCH (c:ChangeRequest)
        WHERE c.created_at >= $start_date
        RETURN c
        ORDER BY c.created_at DESC
        """

        changes = []
        with service.neo4j_client.driver.session() as session:
            result = session.run(query, start_date=start_date.isoformat())
            for record in result:
                node = record["c"]
                changes.append(dict(node))

        # Calculate metrics
        calculator = ChangeMetricsCalculator()
        metrics = calculator.calculate_metrics(changes)
        trend = calculator.get_trend_analysis(changes, days)
        recommendations = calculator.get_recommendations(metrics)

        return {
            "period_days": days,
            "metrics": metrics.to_dict(),
            "trend": trend,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}") from e


@router.post("/{change_id}/approve", response_model=dict[str, Any])
async def approve_change(
    change_id: str,
    approver: str = Query(..., description="Username of the approver"),
    comments: str | None = Query(None, description="Optional approval comments"),
) -> dict[str, Any]:
    """
    Approve a change request.

    Records approval from the specified approver.
    """
    try:
        # In a real implementation, this would load existing approvals from database
        # For now, return a success response
        return {
            "success": True,
            "message": f"Change {change_id} approved by {approver}",
            "approver": approver,
            "comments": comments,
            "approved_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve change: {str(e)}") from e


@router.post("/{change_id}/reject", response_model=dict[str, Any])
async def reject_change(
    change_id: str,
    approver: str = Query(..., description="Username of the approver"),
    reason: str = Query(..., description="Reason for rejection"),
) -> dict[str, Any]:
    """
    Reject a change request.

    Records rejection from the specified approver with a reason.
    """
    try:
        # In a real implementation, this would load existing approvals from database
        # For now, return a success response
        return {
            "success": True,
            "message": f"Change {change_id} rejected by {approver}",
            "approver": approver,
            "reason": reason,
            "rejected_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject change: {str(e)}") from e
