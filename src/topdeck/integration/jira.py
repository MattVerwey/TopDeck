"""
Jira integration for change management.

Handles webhooks and API interactions with Jira for change requests.
"""

import logging
from datetime import datetime
from typing import Any

from topdeck.change_management.models import ChangeRequest, ChangeStatus, ChangeType

logger = logging.getLogger(__name__)
from topdeck.change_management.service import ChangeManagementService


class JiraWebhookHandler:
    """Handler for Jira webhooks"""

    def __init__(self, change_service: ChangeManagementService) -> None:
        """Initialize Jira webhook handler"""
        self.change_service = change_service

    def process_webhook(self, payload: dict[str, Any]) -> ChangeRequest:
        """
        Process incoming Jira webhook.
        
        Args:
            payload: Webhook payload from Jira
            
        Returns:
            Created or updated ChangeRequest
        """
        # Extract issue data from Jira webhook payload
        issue = payload.get("issue", {})
        fields = issue.get("fields", {})
        
        issue_key = issue.get("key", "")
        summary = fields.get("summary", "")
        description = fields.get("description", "")
        status = fields.get("status", {}).get("name", "")
        issue_type = fields.get("issuetype", {}).get("name", "")
        
        # Map Jira issue type to our change type
        mapped_change_type = self._map_jira_issue_type(issue_type)
        
        # Parse scheduled times from custom fields or labels
        scheduled_start = None
        scheduled_end = None
        
        # Jira custom fields for change management
        # These would be configured based on your Jira setup
        if fields.get("customfield_10100"):  # Example: Start date field
            try:
                scheduled_start = datetime.fromisoformat(
                    fields["customfield_10100"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError, KeyError) as e:
                logger.warning(f"Failed to parse start date from Jira custom field: {e}")
                pass
                
        if fields.get("customfield_10101"):  # Example: End date field
            try:
                scheduled_end = datetime.fromisoformat(
                    fields["customfield_10101"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError, KeyError) as e:
                logger.warning(f"Failed to parse end date from Jira custom field: {e}")
                pass

        # Extract affected resources from labels or custom fields
        affected_resources = []
        labels = fields.get("labels", [])
        for label in labels:
            if label.startswith("resource:"):
                resource_id = label.replace("resource:", "")
                affected_resources.append(resource_id)

        # Create change request
        change_request = self.change_service.create_change_request(
            title=summary or issue_key,
            description=description or summary,
            change_type=mapped_change_type,
            affected_resources=affected_resources,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            requester=fields.get("reporter", {}).get("displayName"),
            external_system="jira",
            external_id=issue_key,
        )

        return change_request

    def _map_jira_status(self, status: str) -> ChangeStatus:
        """Map Jira status to internal status"""
        status_map = {
            "to do": ChangeStatus.DRAFT,
            "in progress": ChangeStatus.IN_PROGRESS,
            "in review": ChangeStatus.PENDING_APPROVAL,
            "approved": ChangeStatus.APPROVED,
            "scheduled": ChangeStatus.SCHEDULED,
            "done": ChangeStatus.COMPLETED,
            "cancelled": ChangeStatus.CANCELLED,
            "closed": ChangeStatus.COMPLETED,
        }
        return status_map.get(status.lower(), ChangeStatus.DRAFT)

    def _map_jira_issue_type(self, issue_type: str) -> ChangeType:
        """Map Jira issue type to internal change type"""
        type_map = {
            "change": ChangeType.DEPLOYMENT,
            "deployment": ChangeType.DEPLOYMENT,
            "release": ChangeType.DEPLOYMENT,
            "hotfix": ChangeType.EMERGENCY,
            "incident": ChangeType.EMERGENCY,
            "task": ChangeType.CONFIGURATION,
        }
        return type_map.get(issue_type.lower(), ChangeType.DEPLOYMENT)
