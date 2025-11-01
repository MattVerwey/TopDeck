"""
Webhook API endpoints for external integrations.

Provides webhook receivers for ServiceNow, Jira, and other systems.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from topdeck.change_management.service import ChangeManagementService
from topdeck.common.config import settings
from topdeck.integration.jira import JiraWebhookHandler
from topdeck.integration.servicenow import ServiceNowWebhookHandler
from topdeck.storage.neo4j_client import Neo4jClient


# Create router
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class WebhookResponse(BaseModel):
    """Response model for webhook"""

    success: bool
    message: str
    change_id: str | None = None


def get_change_service() -> ChangeManagementService:
    """Get change management service instance"""
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    return ChangeManagementService(neo4j_client)


@router.post("/servicenow", response_model=WebhookResponse)
async def servicenow_webhook(
    payload: dict[str, Any],
    x_servicenow_signature: str | None = Header(None),
) -> WebhookResponse:
    """
    Webhook endpoint for ServiceNow change requests.

    Receives change request notifications from ServiceNow and creates
    or updates change requests in TopDeck.
    
    Args:
        payload: ServiceNow webhook payload
        x_servicenow_signature: Optional signature for webhook verification
    """
    try:
        # TODO: Implement webhook signature verification for security
        # Verify HMAC signature against configured secret

        service = get_change_service()
        handler = ServiceNowWebhookHandler(service)
        
        # Process webhook
        change_request = handler.process_webhook(payload)
        
        return WebhookResponse(
            success=True,
            message="ServiceNow change request processed successfully",
            change_id=change_request.id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process ServiceNow webhook: {str(e)}",
        ) from e


@router.post("/jira", response_model=WebhookResponse)
async def jira_webhook(
    payload: dict[str, Any],
    x_hub_signature: str | None = Header(None),
) -> WebhookResponse:
    """
    Webhook endpoint for Jira issues.

    Receives issue notifications from Jira and creates or updates
    change requests in TopDeck.
    
    Args:
        payload: Jira webhook payload
        x_hub_signature: Optional signature for webhook verification
    """
    try:
        # TODO: Implement webhook signature verification for security
        # Verify HMAC signature against configured secret

        service = get_change_service()
        handler = JiraWebhookHandler(service)
        
        # Process webhook
        change_request = handler.process_webhook(payload)
        
        return WebhookResponse(
            success=True,
            message="Jira issue processed successfully",
            change_id=change_request.id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process Jira webhook: {str(e)}",
        ) from e


@router.get("/health")
async def webhooks_health() -> dict[str, str]:
    """Health check for webhook endpoints"""
    return {"status": "healthy", "service": "webhooks"}
