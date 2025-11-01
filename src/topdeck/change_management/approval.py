"""
Change Approval Workflow.

Manages approval workflows for change requests based on risk level.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ApprovalStatus(str, Enum):
    """Status of an approval"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApproverRole(str, Enum):
    """Role of an approver"""

    CHANGE_MANAGER = "change_manager"
    TECHNICAL_LEAD = "technical_lead"
    SECURITY_REVIEWER = "security_reviewer"
    BUSINESS_OWNER = "business_owner"
    EMERGENCY_APPROVER = "emergency_approver"


@dataclass
class Approval:
    """Represents an approval request"""

    id: str
    change_id: str
    approver: str
    approver_role: ApproverRole
    status: ApprovalStatus = ApprovalStatus.PENDING
    comments: str | None = None
    approved_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ApprovalWorkflow:
    """Manages change approval workflows"""

    def __init__(self) -> None:
        """Initialize approval workflow"""
        self.approvals: dict[str, list[Approval]] = {}

    def determine_required_approvers(
        self,
        change_type: str,
        risk_score: float,
        critical_path: bool,
        affected_count: int,
    ) -> list[ApproverRole]:
        """
        Determine which approvers are required based on change characteristics.

        Args:
            change_type: Type of change
            risk_score: Overall risk score (0-100)
            critical_path: Whether critical infrastructure is affected
            affected_count: Number of affected resources

        Returns:
            List of required approver roles
        """
        required_approvers = []

        # Always require change manager for non-emergency changes
        if change_type != "emergency":
            required_approvers.append(ApproverRole.CHANGE_MANAGER)

        # Technical lead for moderate+ changes
        if risk_score > 50 or affected_count > 5:
            required_approvers.append(ApproverRole.TECHNICAL_LEAD)

        # Security review for high-risk changes
        if risk_score > 70 or change_type in ["infrastructure", "update", "patch"]:
            required_approvers.append(ApproverRole.SECURITY_REVIEWER)

        # Business owner for critical path changes
        if critical_path or risk_score > 80:
            required_approvers.append(ApproverRole.BUSINESS_OWNER)

        # Emergency approver for emergency changes
        if change_type == "emergency":
            required_approvers.append(ApproverRole.EMERGENCY_APPROVER)

        return required_approvers

    def create_approval_requests(
        self,
        change_id: str,
        required_approvers: list[ApproverRole],
        approver_mapping: dict[ApproverRole, str],
    ) -> list[Approval]:
        """
        Create approval requests for a change.

        Args:
            change_id: ID of the change request
            required_approvers: List of required approver roles
            approver_mapping: Mapping of roles to actual approver usernames

        Returns:
            List of created Approval objects
        """
        approvals = []

        for role in required_approvers:
            approver = approver_mapping.get(role)
            if approver:
                approval = Approval(
                    id=f"{change_id}-{role.value}",
                    change_id=change_id,
                    approver=approver,
                    approver_role=role,
                )
                approvals.append(approval)

        self.approvals[change_id] = approvals
        return approvals

    def approve_change(
        self, change_id: str, approver: str, comments: str | None = None
    ) -> Approval | None:
        """
        Approve a change request.

        Args:
            change_id: ID of the change request
            approver: Username of the approver
            comments: Optional approval comments

        Returns:
            Updated Approval object or None if not found
        """
        if change_id not in self.approvals:
            return None

        for approval in self.approvals[change_id]:
            if approval.approver == approver and approval.status == ApprovalStatus.PENDING:
                approval.status = ApprovalStatus.APPROVED
                approval.comments = comments
                approval.approved_at = datetime.now(UTC)
                return approval

        return None

    def reject_change(self, change_id: str, approver: str, reason: str) -> Approval | None:
        """
        Reject a change request.

        Args:
            change_id: ID of the change request
            approver: Username of the approver
            reason: Reason for rejection

        Returns:
            Updated Approval object or None if not found
        """
        if change_id not in self.approvals:
            return None

        for approval in self.approvals[change_id]:
            if approval.approver == approver and approval.status == ApprovalStatus.PENDING:
                approval.status = ApprovalStatus.REJECTED
                approval.comments = reason
                approval.approved_at = datetime.now(UTC)
                return approval

        return None

    def is_fully_approved(self, change_id: str) -> bool:
        """
        Check if all required approvals are granted.

        Args:
            change_id: ID of the change request

        Returns:
            True if all approvals are granted, False otherwise
        """
        if change_id not in self.approvals:
            return False

        approvals = self.approvals[change_id]
        return all(approval.status == ApprovalStatus.APPROVED for approval in approvals)

    def has_rejections(self, change_id: str) -> bool:
        """
        Check if any approval was rejected.

        Args:
            change_id: ID of the change request

        Returns:
            True if any approval is rejected, False otherwise
        """
        if change_id not in self.approvals:
            return False

        approvals = self.approvals[change_id]
        return any(approval.status == ApprovalStatus.REJECTED for approval in approvals)

    def get_approval_summary(self, change_id: str) -> dict[str, Any]:
        """
        Get approval summary for a change.

        Args:
            change_id: ID of the change request

        Returns:
            Dictionary with approval summary
        """
        if change_id not in self.approvals:
            return {
                "total_required": 0,
                "approved": 0,
                "rejected": 0,
                "pending": 0,
                "fully_approved": False,
                "has_rejections": False,
                "approvals": [],
            }

        approvals = self.approvals[change_id]
        approved = sum(1 for a in approvals if a.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for a in approvals if a.status == ApprovalStatus.REJECTED)
        pending = sum(1 for a in approvals if a.status == ApprovalStatus.PENDING)

        return {
            "total_required": len(approvals),
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "fully_approved": self.is_fully_approved(change_id),
            "has_rejections": self.has_rejections(change_id),
            "approvals": [
                {
                    "id": a.id,
                    "approver": a.approver,
                    "role": a.approver_role.value,
                    "status": a.status.value,
                    "comments": a.comments,
                    "approved_at": a.approved_at.isoformat() if a.approved_at else None,
                }
                for a in approvals
            ],
        }
