"""SLA/SLO Management API routes."""

import random
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/v1/sla", tags=["SLA/SLO"])


class SLAConfig(BaseModel):
    """SLA configuration model."""

    id: Optional[str] = None
    name: str = Field(..., description="Name of the SLA")
    description: Optional[str] = Field(None, description="Description of the SLA")
    sla_percentage: float = Field(
        default=99.0,
        ge=0.0,
        le=100.0,
        description="SLA uptime percentage (0-100)",
    )
    service_name: str = Field(..., description="Name of the service this SLA applies to")
    resources: list[str] = Field(
        default_factory=list,
        description="List of resource IDs that affect this SLA",
    )
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("sla_percentage")
    @classmethod
    def validate_sla_percentage(cls, v: float) -> float:
        """Validate SLA percentage is reasonable."""
        if v < 0 or v > 100:
            raise ValueError("SLA percentage must be between 0 and 100")
        return v


class SLOCalculation(BaseModel):
    """SLO calculation result."""

    sla_id: str
    sla_percentage: float
    slo_percentage: float
    error_budget_percentage: float
    error_budget_minutes_per_month: float
    error_budget_minutes_per_year: float
    calculated_at: str


class ErrorBudgetStatus(BaseModel):
    """Error budget status for a service."""

    sla_id: str
    service_name: str
    sla_percentage: float
    slo_percentage: float
    current_uptime_percentage: float
    error_budget_percentage: float
    error_budget_remaining_percentage: float
    error_budget_consumed_percentage: float
    is_within_budget: bool
    resources_status: list[dict[str, Any]]
    period_start: str
    period_end: str
    calculated_at: str


class ResourceAvailability(BaseModel):
    """Resource availability metrics."""

    resource_id: str
    resource_name: str
    resource_type: str
    uptime_percentage: float
    downtime_minutes: float
    error_count: int
    success_rate: float
    meets_slo: bool
    period_start: str
    period_end: str


def calculate_slo_from_sla(sla_percentage: float) -> float:
    """
    Calculate SLO from SLA percentage.

    SLO should be stricter than SLA to ensure we meet the SLA target.
    Common practice: Add margin based on SLA level.
    
    For example:
    - SLA 99% -> SLO 99.9% (10x error budget reduction)
    - SLA 99.9% -> SLO 99.95% (5x error budget reduction)
    - SLA 99.99% -> SLO 99.995% (5x error budget reduction)
    """
    error_budget = 100 - sla_percentage
    
    # Apply safety margin based on error budget size
    if error_budget >= 1.0:  # 99% or lower
        # Reduce error budget by 90% for SLO
        slo_error_budget = error_budget * 0.1
    elif error_budget >= 0.1:  # 99.9%
        # Reduce error budget by 80% for SLO
        slo_error_budget = error_budget * 0.2
    else:  # 99.99% or higher
        # Reduce error budget by 80% for SLO
        slo_error_budget = error_budget * 0.2
    
    slo_percentage = 100 - slo_error_budget
    
    # Ensure SLO doesn't exceed practical limits
    return min(slo_percentage, 99.999)


def calculate_error_budget(sla_percentage: float) -> dict[str, float]:
    """
    Calculate error budget in minutes for various time periods.
    
    Error budget = (100 - SLA%) * time_period
    """
    error_budget_pct = 100 - sla_percentage
    
    # Minutes in common time periods
    minutes_per_month = 30 * 24 * 60  # 43,200 minutes
    minutes_per_year = 365 * 24 * 60  # 525,600 minutes
    
    return {
        "error_budget_percentage": error_budget_pct,
        "error_budget_minutes_per_month": (error_budget_pct / 100) * minutes_per_month,
        "error_budget_minutes_per_year": (error_budget_pct / 100) * minutes_per_year,
    }


# In-memory storage for demo purposes
# TODO: Implement persistent storage using Neo4j or another database
# NOTE: Current implementation will lose all SLA configurations on service restart
_sla_configs: dict[str, dict[str, Any]] = {}


@router.post("/configs", response_model=SLAConfig)
async def create_sla_config(config: SLAConfig) -> SLAConfig:
    """
    Create a new SLA configuration.
    
    Defines the SLA for a service and which resources affect it.
    """
    # Generate ID if not provided
    if not config.id:
        config.id = f"sla-{len(_sla_configs) + 1}"
    
    # Set timestamps
    now = datetime.now(UTC).isoformat()
    config.created_at = now
    config.updated_at = now
    
    # Store configuration
    _sla_configs[config.id] = config.model_dump()
    
    return config


@router.get("/configs", response_model=list[SLAConfig])
async def list_sla_configs(
    service_name: Optional[str] = Query(None, description="Filter by service name")
) -> list[SLAConfig]:
    """
    List all SLA configurations.
    
    Optionally filter by service name.
    """
    configs = list(_sla_configs.values())
    
    if service_name:
        configs = [c for c in configs if c.get("service_name") == service_name]
    
    return [SLAConfig(**c) for c in configs]


@router.get("/configs/{sla_id}", response_model=SLAConfig)
async def get_sla_config(sla_id: str) -> SLAConfig:
    """Get a specific SLA configuration by ID."""
    if sla_id not in _sla_configs:
        raise HTTPException(status_code=404, detail=f"SLA configuration {sla_id} not found")
    
    return SLAConfig(**_sla_configs[sla_id])


@router.put("/configs/{sla_id}", response_model=SLAConfig)
async def update_sla_config(sla_id: str, config: SLAConfig) -> SLAConfig:
    """Update an existing SLA configuration."""
    if sla_id not in _sla_configs:
        raise HTTPException(status_code=404, detail=f"SLA configuration {sla_id} not found")
    
    # Preserve original timestamps
    original = _sla_configs[sla_id]
    config.id = sla_id
    config.created_at = original.get("created_at")
    config.updated_at = datetime.now(UTC).isoformat()
    
    _sla_configs[sla_id] = config.model_dump()
    
    return config


@router.delete("/configs/{sla_id}")
async def delete_sla_config(sla_id: str) -> dict[str, str]:
    """Delete an SLA configuration."""
    if sla_id not in _sla_configs:
        raise HTTPException(status_code=404, detail=f"SLA configuration {sla_id} not found")
    
    del _sla_configs[sla_id]
    
    return {"status": "deleted", "sla_id": sla_id}


@router.get("/configs/{sla_id}/slo", response_model=SLOCalculation)
async def calculate_slo(sla_id: str) -> SLOCalculation:
    """
    Calculate SLO for a given SLA configuration.
    
    SLO (Service Level Objective) is stricter than SLA to provide a safety margin.
    """
    if sla_id not in _sla_configs:
        raise HTTPException(status_code=404, detail=f"SLA configuration {sla_id} not found")
    
    config = _sla_configs[sla_id]
    sla_percentage = config["sla_percentage"]
    
    # Calculate SLO
    slo_percentage = calculate_slo_from_sla(sla_percentage)
    
    # Calculate error budgets
    error_budget = calculate_error_budget(sla_percentage)
    
    return SLOCalculation(
        sla_id=sla_id,
        sla_percentage=sla_percentage,
        slo_percentage=slo_percentage,
        error_budget_percentage=error_budget["error_budget_percentage"],
        error_budget_minutes_per_month=error_budget["error_budget_minutes_per_month"],
        error_budget_minutes_per_year=error_budget["error_budget_minutes_per_year"],
        calculated_at=datetime.now(UTC).isoformat(),
    )


@router.get("/configs/{sla_id}/error-budget", response_model=ErrorBudgetStatus)
async def get_error_budget_status(
    sla_id: str,
    period_hours: int = Query(default=24, description="Time period in hours to analyze"),
) -> ErrorBudgetStatus:
    """
    Get current error budget status for an SLA.
    
    Shows how much error budget has been consumed and remaining budget.
    """
    if sla_id not in _sla_configs:
        raise HTTPException(status_code=404, detail=f"SLA configuration {sla_id} not found")
    
    config = _sla_configs[sla_id]
    sla_percentage = config["sla_percentage"]
    slo_percentage = calculate_slo_from_sla(sla_percentage)
    
    # Calculate time period
    now = datetime.now(UTC)
    period_start = now - timedelta(hours=period_hours)
    
    # For demo purposes, simulate resource availability
    # In production, this would query actual metrics from monitoring systems
    resources_status = []
    total_uptime = 0.0
    resource_count = len(config.get("resources", []))
    
    if resource_count > 0:
        # Simulate different resource availability
        random.seed(42)  # For consistent demo results
        
        for resource_id in config["resources"]:
            # Simulate uptime between 95% and 100%
            uptime = 95.0 + random.random() * 5.0
            total_uptime += uptime
            
            resources_status.append({
                "resource_id": resource_id,
                "uptime_percentage": round(uptime, 2),
                "meets_slo": uptime >= slo_percentage,
                "error_count": int((100 - uptime) * 10),
            })
        
        current_uptime = total_uptime / resource_count
    else:
        current_uptime = 100.0
    
    # Calculate error budget consumption
    error_budget_pct = 100 - sla_percentage
    actual_downtime_pct = 100 - current_uptime
    error_budget_consumed_pct = (
        (actual_downtime_pct / error_budget_pct * 100) if error_budget_pct > 0 else 0
    )
    error_budget_remaining_pct = 100 - error_budget_consumed_pct
    
    return ErrorBudgetStatus(
        sla_id=sla_id,
        service_name=config["service_name"],
        sla_percentage=sla_percentage,
        slo_percentage=slo_percentage,
        current_uptime_percentage=round(current_uptime, 4),
        error_budget_percentage=error_budget_pct,
        error_budget_remaining_percentage=max(0, round(error_budget_remaining_pct, 2)),
        error_budget_consumed_percentage=min(100, round(error_budget_consumed_pct, 2)),
        is_within_budget=current_uptime >= sla_percentage,
        resources_status=resources_status,
        period_start=period_start.isoformat(),
        period_end=now.isoformat(),
        calculated_at=now.isoformat(),
    )


@router.get("/resources/{resource_id}/availability", response_model=ResourceAvailability)
async def get_resource_availability(
    resource_id: str,
    period_hours: int = Query(default=24, description="Time period in hours to analyze"),
    slo_percentage: Optional[float] = Query(
        None, description="SLO percentage to check against"
    ),
) -> ResourceAvailability:
    """
    Get availability metrics for a specific resource.
    
    Useful for checking if individual resources meet SLO targets.
    """
    # For demo purposes, simulate resource metrics
    # In production, this would query actual metrics from monitoring systems
    random.seed(hash(resource_id) % 1000)  # Consistent but varied results per resource
    
    # Simulate uptime between 95% and 100%
    uptime = 95.0 + random.random() * 5.0
    
    # Calculate derived metrics
    minutes_in_period = period_hours * 60
    downtime_minutes = (100 - uptime) / 100 * minutes_in_period
    error_count = int((100 - uptime) * 10 * (period_hours / 24))
    success_rate = uptime / 100
    
    # Check if meets SLO
    meets_slo = True
    if slo_percentage is not None:
        meets_slo = uptime >= slo_percentage
    
    now = datetime.now(UTC)
    period_start = now - timedelta(hours=period_hours)
    
    return ResourceAvailability(
        resource_id=resource_id,
        resource_name=f"Resource-{resource_id[-8:]}",
        resource_type="service",
        uptime_percentage=round(uptime, 4),
        downtime_minutes=round(downtime_minutes, 2),
        error_count=error_count,
        success_rate=round(success_rate, 4),
        meets_slo=meets_slo,
        period_start=period_start.isoformat(),
        period_end=now.isoformat(),
    )
