"""
Data models for change management.

Represents change requests, approvals, and impact assessments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ChangeStatus(str, Enum):
    """Status of a change request"""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class ChangeType(str, Enum):
    """Type of change"""

    DEPLOYMENT = "deployment"
    CONFIGURATION = "configuration"
    SCALING = "scaling"
    RESTART = "restart"
    UPDATE = "update"
    PATCH = "patch"
    INFRASTRUCTURE = "infrastructure"
    EMERGENCY = "emergency"


class ChangeRiskLevel(str, Enum):
    """Risk level of a change"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChangeRequest:
    """
    Represents a change request in the system.
    Can be created internally or synced from ServiceNow/Jira.
    """

    # Core identification
    id: str  # Internal ID or external ticket ID
    title: str
    description: str
    change_type: ChangeType

    # Status tracking
    status: ChangeStatus = ChangeStatus.DRAFT
    risk_level: ChangeRiskLevel = ChangeRiskLevel.MEDIUM

    # People and teams
    requester: str | None = None
    assignee: str | None = None
    approvers: list[str] = field(default_factory=list)

    # Scheduling
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None

    # Impact tracking
    affected_resources: list[str] = field(default_factory=list)
    affected_services_count: int = 0
    estimated_downtime_seconds: int = 0

    # External system integration
    external_system: str | None = None  # "servicenow", "jira", etc.
    external_id: str | None = None
    external_url: str | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: dict[str, str] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "change_type": self.change_type.value,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "requester": self.requester,
            "assignee": self.assignee,
            "approvers": self.approvers,
            "scheduled_start": self.scheduled_start.isoformat() if self.scheduled_start else None,
            "scheduled_end": self.scheduled_end.isoformat() if self.scheduled_end else None,
            "actual_start": self.actual_start.isoformat() if self.actual_start else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end else None,
            "affected_resources": self.affected_resources,
            "affected_services_count": self.affected_services_count,
            "estimated_downtime_seconds": self.estimated_downtime_seconds,
            "external_system": self.external_system,
            "external_id": self.external_id,
            "external_url": self.external_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "properties": self.properties,
        }


@dataclass
class ChangeImpactAssessment:
    """
    Impact assessment for a change request.
    Calculated based on topology and risk analysis.
    """

    change_id: str
    
    # Direct and indirect impact
    directly_affected_resources: list[dict[str, Any]] = field(default_factory=list)
    indirectly_affected_resources: list[dict[str, Any]] = field(default_factory=list)
    total_affected_count: int = 0
    
    # Risk assessment
    overall_risk_score: float = 0.0
    performance_degradation_pct: float = 0.0
    estimated_downtime_seconds: int = 0
    
    # User impact
    user_impact_level: str = "low"  # low, medium, high
    critical_path_affected: bool = False
    
    # Recommendations
    recommended_window: str = "standard"  # standard, maintenance, emergency
    rollback_plan_required: bool = False
    approval_required: bool = False
    
    # Details
    breakdown: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    
    assessed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "change_id": self.change_id,
            "directly_affected_resources": self.directly_affected_resources,
            "indirectly_affected_resources": self.indirectly_affected_resources,
            "total_affected_count": self.total_affected_count,
            "overall_risk_score": self.overall_risk_score,
            "performance_degradation_pct": self.performance_degradation_pct,
            "estimated_downtime_seconds": self.estimated_downtime_seconds,
            "user_impact_level": self.user_impact_level,
            "critical_path_affected": self.critical_path_affected,
            "recommended_window": self.recommended_window,
            "rollback_plan_required": self.rollback_plan_required,
            "approval_required": self.approval_required,
            "breakdown": self.breakdown,
            "recommendations": self.recommendations,
            "assessed_at": self.assessed_at.isoformat(),
        }
