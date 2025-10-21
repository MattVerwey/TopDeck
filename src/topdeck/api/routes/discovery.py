"""
Discovery API endpoints.

Provides API endpoints for managing automated resource discovery.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from topdeck.common.scheduler import get_scheduler


# Pydantic models for API responses
class DiscoveryStatusResponse(BaseModel):
    """Response model for discovery status."""

    scheduler_running: bool
    discovery_in_progress: bool
    last_discovery_time: str | None
    interval_hours: int
    enabled_providers: dict[str, bool]


class DiscoveryTriggerResponse(BaseModel):
    """Response model for manual discovery trigger."""

    status: str
    message: str
    last_run: str | None = None


# Create router
router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


@router.get("/status", response_model=DiscoveryStatusResponse)
async def get_discovery_status() -> DiscoveryStatusResponse:
    """
    Get the status of the automated discovery scheduler.

    Returns information about:
    - Whether the scheduler is running
    - Whether discovery is currently in progress
    - When the last discovery ran
    - The configured scan interval
    - Which cloud providers are enabled and have credentials
    """
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()

        return DiscoveryStatusResponse(
            scheduler_running=status["scheduler_running"],
            discovery_in_progress=status["discovery_in_progress"],
            last_discovery_time=status["last_discovery_time"],
            interval_hours=status["interval_hours"],
            enabled_providers=status["enabled_providers"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get discovery status: {str(e)}"
        ) from e


@router.post("/trigger", response_model=DiscoveryTriggerResponse)
async def trigger_discovery() -> DiscoveryTriggerResponse:
    """
    Manually trigger a resource discovery scan.

    This will start a discovery scan immediately, regardless of the schedule.
    If a discovery is already in progress, this will return an error.
    """
    try:
        scheduler = get_scheduler()
        result = await scheduler.trigger_manual_discovery()

        return DiscoveryTriggerResponse(
            status=result["status"],
            message=result["message"],
            last_run=result.get("last_run"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger discovery: {str(e)}") from e
