"""
Integrations API endpoints.

Provides API endpoints for managing integration configurations.
"""

from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from topdeck.common.config import settings


# Pydantic models for API responses
class IntegrationResponse(BaseModel):
    """Response model for integration."""

    id: str
    name: str
    type: str
    enabled: bool
    configured: bool
    last_sync: str | None = None


class IntegrationUpdateRequest(BaseModel):
    """Request model for updating integration."""

    enabled: bool | None = None
    config: dict[str, Any] = Field(default_factory=dict)


# Create router
router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


def get_integrations_data() -> list[dict[str, Any]]:
    """Get integrations data based on configuration."""
    integrations = []

    # Azure DevOps integration
    if settings.enable_azure_devops_integration:
        integrations.append(
            {
                "id": "azure-devops",
                "name": "Azure DevOps",
                "type": "azure-devops",
                "enabled": True,
                "configured": bool(getattr(settings, "azure_devops_org", None)),
                "last_sync": None,
            }
        )

    # GitHub integration
    if settings.enable_github_integration:
        integrations.append(
            {
                "id": "github",
                "name": "GitHub",
                "type": "github",
                "enabled": True,
                "configured": bool(getattr(settings, "github_token", None)),
                "last_sync": None,
            }
        )

    # ServiceNow integration (placeholder)
    integrations.append(
        {
            "id": "servicenow",
            "name": "ServiceNow",
            "type": "servicenow",
            "enabled": False,
            "configured": False,
            "last_sync": None,
        }
    )

    # Jira integration (placeholder)
    integrations.append(
        {
            "id": "jira",
            "name": "Jira",
            "type": "jira",
            "enabled": False,
            "configured": False,
            "last_sync": None,
        }
    )

    # Prometheus integration
    if settings.enable_monitoring:
        integrations.append(
            {
                "id": "prometheus",
                "name": "Prometheus",
                "type": "prometheus",
                "enabled": True,
                "configured": bool(settings.prometheus_url),
                "last_sync": None,
            }
        )

    # Loki integration
    if settings.enable_monitoring:
        integrations.append(
            {
                "id": "loki",
                "name": "Loki",
                "type": "loki",
                "enabled": True,
                "configured": bool(settings.loki_url),
                "last_sync": None,
            }
        )

    return integrations


@router.get("", response_model=list[IntegrationResponse])
async def get_integrations() -> list[IntegrationResponse]:
    """
    Get list of available integrations.

    Returns all integrations with their status and configuration state.
    """
    try:
        integrations_data = get_integrations_data()

        return [
            IntegrationResponse(
                id=integration["id"],
                name=integration["name"],
                type=integration["type"],
                enabled=integration["enabled"],
                configured=integration["configured"],
                last_sync=integration["last_sync"],
            )
            for integration in integrations_data
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integrations: {str(e)}") from e


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str, update: IntegrationUpdateRequest = Body(...)
) -> IntegrationResponse:
    """
    Update integration configuration.

    Allows enabling/disabling integrations and updating their configuration.
    """
    try:
        # Get current integrations
        integrations_data = get_integrations_data()

        # Find the integration to update
        integration = None
        for integ in integrations_data:
            if integ["id"] == integration_id:
                integration = integ
                break

        if not integration:
            raise HTTPException(status_code=404, detail=f"Integration {integration_id} not found")

        # Update the integration
        # Note: In a real implementation, this would update the configuration
        # in a database or configuration file. For now, we just return the updated state.
        if update.enabled is not None:
            integration["enabled"] = update.enabled

        # Update configuration (placeholder - would need real implementation)
        if update.config:
            # In a real implementation, validate and store the configuration
            integration["configured"] = True

        return IntegrationResponse(
            id=integration["id"],
            name=integration["name"],
            type=integration["type"],
            enabled=integration["enabled"],
            configured=integration["configured"],
            last_sync=integration["last_sync"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update integration: {str(e)}"
        ) from e
