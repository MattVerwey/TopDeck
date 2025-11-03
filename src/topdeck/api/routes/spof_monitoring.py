"""
SPOF Monitoring API endpoints.

Provides API endpoints for accessing SPOF monitoring data, metrics, and history.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from topdeck.common.scheduler import get_scheduler

router = APIRouter(prefix="/monitoring/spof", tags=["SPOF Monitoring"])


class SPOFResponse(BaseModel):
    """Response model for SPOF information."""

    resource_id: str
    resource_name: str
    resource_type: str
    dependents_count: int
    blast_radius: int
    risk_score: float
    recommendations: list[str]


class SPOFChangeResponse(BaseModel):
    """Response model for SPOF change information."""

    change_type: str
    resource_id: str
    resource_name: str
    resource_type: str
    detected_at: str
    risk_score: float
    blast_radius: int


class SPOFStatisticsResponse(BaseModel):
    """Response model for SPOF statistics."""

    status: str
    last_scan: str | None = None
    total_spofs: int | None = None
    high_risk_spofs: int | None = None
    by_resource_type: dict[str, int] | None = None
    total_changes: int | None = None
    recent_changes: dict[str, int] | None = None
    message: str | None = None


@router.get("/current", response_model=list[SPOFResponse])
async def get_current_spofs() -> list[SPOFResponse]:
    """
    Get current single points of failure.

    Returns:
        List of currently detected SPOFs with risk scores and recommendations
    """
    scheduler = get_scheduler()
    
    if not scheduler.spof_monitor:
        raise HTTPException(
            status_code=503,
            detail="SPOF monitor not initialized",
        )
    
    spofs = scheduler.spof_monitor.get_current_spofs()
    
    return [
        SPOFResponse(
            resource_id=spof["resource_id"],
            resource_name=spof["resource_name"],
            resource_type=spof["resource_type"],
            dependents_count=spof["dependents_count"],
            blast_radius=spof["blast_radius"],
            risk_score=spof["risk_score"],
            recommendations=spof["recommendations"],
        )
        for spof in spofs
    ]


@router.get("/history", response_model=list[SPOFChangeResponse])
async def get_spof_history(
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of changes to return")
) -> list[SPOFChangeResponse]:
    """
    Get SPOF change history.

    Args:
        limit: Maximum number of changes to return (default: 50, min: 1, max: 1000)

    Returns:
        List of recent SPOF changes (new SPOFs detected, SPOFs resolved)
    """
    scheduler = get_scheduler()
    
    if not scheduler.spof_monitor:
        raise HTTPException(
            status_code=503,
            detail="SPOF monitor not initialized",
        )
    
    changes = scheduler.spof_monitor.get_recent_changes(limit=limit)
    
    return [
        SPOFChangeResponse(
            change_type=change["change_type"],
            resource_id=change["resource_id"],
            resource_name=change["resource_name"],
            resource_type=change["resource_type"],
            detected_at=change["detected_at"],
            risk_score=change["risk_score"],
            blast_radius=change["blast_radius"],
        )
        for change in changes
    ]


@router.get("/statistics", response_model=dict[str, Any])
async def get_spof_statistics() -> dict[str, Any]:
    """
    Get SPOF monitoring statistics.

    Returns:
        Statistics about SPOF monitoring including counts, trends, and status
    """
    scheduler = get_scheduler()
    
    if not scheduler.spof_monitor:
        raise HTTPException(
            status_code=503,
            detail="SPOF monitor not initialized",
        )
    
    return scheduler.spof_monitor.get_statistics()


@router.post("/scan")
async def trigger_spof_scan() -> dict[str, Any]:
    """
    Trigger a manual SPOF scan.

    Returns:
        Status of the scan request
    """
    scheduler = get_scheduler()
    
    if not scheduler.spof_monitor:
        raise HTTPException(
            status_code=503,
            detail="SPOF monitor not initialized",
        )
    
    result = await scheduler.trigger_manual_spof_scan()
    return result


@router.get("/metrics")
async def get_spof_metrics() -> dict[str, Any]:
    """
    Get SPOF metrics in a format suitable for external monitoring systems.

    This endpoint provides metrics compatible with Prometheus and other
    monitoring tools.

    Returns:
        Dictionary with metric values
    """
    scheduler = get_scheduler()
    
    if not scheduler.spof_monitor:
        raise HTTPException(
            status_code=503,
            detail="SPOF monitor not initialized",
        )
    
    stats = scheduler.spof_monitor.get_statistics()
    
    if stats.get("status") == "not_scanned":
        return {
            "status": "not_scanned",
            "metrics": {},
        }
    
    return {
        "status": "active",
        "last_scan": stats.get("last_scan"),
        "metrics": {
            "spof_total": stats.get("total_spofs", 0),
            "spof_high_risk": stats.get("high_risk_spofs", 0),
            "spof_by_type": stats.get("by_resource_type", {}),
            "spof_changes_new": stats.get("recent_changes", {}).get("new", 0),
            "spof_changes_resolved": stats.get("recent_changes", {}).get("resolved", 0),
        },
    }
