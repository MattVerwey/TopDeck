"""
ServiceNow integration for change management.

Handles webhooks and API interactions with ServiceNow for change requests.
"""

import logging
from datetime import datetime
from typing import Any

from topdeck.change_management.models import ChangeRequest, ChangeStatus, ChangeType
from topdeck.change_management.service import ChangeManagementService

logger = logging.getLogger(__name__)


class ServiceNowWebhookHandler:
    """Handler for ServiceNow webhooks"""

    def __init__(self, change_service: ChangeManagementService) -> None:
        """Initialize ServiceNow webhook handler"""
        self.change_service = change_service

    def process_webhook(self, payload: dict[str, Any]) -> ChangeRequest:
        """
        Process incoming ServiceNow webhook.

        Args:
            payload: Webhook payload from ServiceNow

        Returns:
            Created or updated ChangeRequest
        """
        # Extract change request data from ServiceNow payload
        # ServiceNow change request structure varies, this is a simplified example
        change_number = payload.get("number", "")
        short_description = payload.get("short_description", "")
        description = payload.get("description", "")
        state = payload.get("state", "")
        change_type = payload.get("type", "")

        # Map ServiceNow state to our status and change type to our type
        self._map_servicenow_state(state)
        mapped_change_type = self._map_servicenow_type(change_type)

        # Parse scheduled times
        scheduled_start = None
        scheduled_end = None

        if payload.get("start_date"):
            try:
                scheduled_start = datetime.fromisoformat(payload["start_date"].replace(" ", "T"))
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse start_date from ServiceNow: {e}")
                pass

        if payload.get("end_date"):
            try:
                scheduled_end = datetime.fromisoformat(payload["end_date"].replace(" ", "T"))
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse end_date from ServiceNow: {e}")
                pass

        # Extract affected resources from payload or configuration items
        affected_resources = []
        if "cmdb_ci" in payload and payload["cmdb_ci"]:
            # ServiceNow Configuration Items - map to our resource IDs
            affected_resources = [payload["cmdb_ci"]]

        # Create change request with mapped status
        change_request = self.change_service.create_change_request(
            title=short_description or change_number,
            description=description or short_description,
            change_type=mapped_change_type,
            affected_resources=affected_resources,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            requester=payload.get("requested_by", {}).get("name"),
            external_system="servicenow",
            external_id=change_number,
        )
        # Note: Status from mapped_status can be used for future status updates

        return change_request

    def _map_servicenow_state(self, state: str) -> ChangeStatus:
        """Map ServiceNow state to internal status"""
        state_map = {
            "new": ChangeStatus.DRAFT,
            "assess": ChangeStatus.PENDING_APPROVAL,
            "authorize": ChangeStatus.PENDING_APPROVAL,
            "scheduled": ChangeStatus.SCHEDULED,
            "implement": ChangeStatus.IN_PROGRESS,
            "review": ChangeStatus.COMPLETED,
            "closed": ChangeStatus.COMPLETED,
            "cancelled": ChangeStatus.CANCELLED,
        }
        return state_map.get(state.lower(), ChangeStatus.DRAFT)

    def _map_servicenow_type(self, change_type: str) -> ChangeType:
        """Map ServiceNow change type to internal type"""
        type_map = {
            "standard": ChangeType.DEPLOYMENT,
            "normal": ChangeType.DEPLOYMENT,
            "emergency": ChangeType.EMERGENCY,
            "expedited": ChangeType.EMERGENCY,
        }
        return type_map.get(change_type.lower(), ChangeType.DEPLOYMENT)
