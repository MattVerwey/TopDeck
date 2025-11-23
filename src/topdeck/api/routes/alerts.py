"""
API routes for alert management.

Endpoints for creating alert rules, managing destinations, and viewing alert history.
"""

import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.monitoring.alerting import (
    AlertDestination,
    AlertDestinationType,
    AlertingEngine,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    TriggerType,
)
from topdeck.monitoring.live_diagnostics import LiveDiagnosticsService
from topdeck.monitoring.prometheus_collector import PrometheusCollector
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

# Initialize services (in production, use dependency injection)
_alerting_engine: Optional[AlertingEngine] = None


def get_alerting_engine() -> AlertingEngine:
    """Get or create alerting engine instance."""
    global _alerting_engine
    
    if _alerting_engine is None:
        # Initialize dependencies
        neo4j_client = Neo4jClient()
        prometheus_collector = PrometheusCollector()
        diagnostics_service = LiveDiagnosticsService(
            neo4j_client=neo4j_client,
            prometheus_collector=prometheus_collector,
        )
        
        # Initialize alerting engine
        # SMTP settings should come from environment variables
        try:
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
        except ValueError:
            smtp_port = 587
            logger.warning("Invalid SMTP_PORT value, using default 587")
        
        _alerting_engine = AlertingEngine(
            diagnostics_service=diagnostics_service,
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=smtp_port,
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            smtp_from_address=os.getenv("SMTP_FROM_ADDRESS"),
        )
        
        # Add some default rules and destinations for demo
        _add_default_config(_alerting_engine)
    
    return _alerting_engine


def _add_default_config(engine: AlertingEngine) -> None:
    """Add default alert rules and destinations."""
    # Default destinations
    email_dest = AlertDestination(
        id="default-email",
        name="Default Email",
        type=AlertDestinationType.EMAIL,
        enabled=False,  # Disabled by default until configured
        config={"to_addresses": []},
    )
    engine.add_destination(email_dest)
    
    slack_dest = AlertDestination(
        id="default-slack",
        name="Default Slack",
        type=AlertDestinationType.SLACK,
        enabled=False,
        config={"webhook_url": ""},
    )
    engine.add_destination(slack_dest)
    
    # Default rules
    health_rule = AlertRule(
        id="health-drop",
        name="Service Health Score Drop",
        trigger_type=TriggerType.HEALTH_SCORE_DROP,
        threshold=50.0,
        severity=AlertSeverity.WARNING,
        destinations=["default-email", "default-slack"],
    )
    engine.add_rule(health_rule)
    
    critical_rule = AlertRule(
        id="critical-anomaly",
        name="Critical Anomaly Detected",
        trigger_type=TriggerType.CRITICAL_ANOMALY,
        severity=AlertSeverity.CRITICAL,
        destinations=["default-email", "default-slack"],
    )
    engine.add_rule(critical_rule)
    
    failure_rule = AlertRule(
        id="service-failure",
        name="Service Failure",
        trigger_type=TriggerType.SERVICE_FAILURE,
        severity=AlertSeverity.CRITICAL,
        destinations=["default-email", "default-slack"],
    )
    engine.add_rule(failure_rule)


# Request/Response Models

class AlertRuleCreate(BaseModel):
    """Request model for creating an alert rule."""
    
    name: str = Field(..., description="Rule name")
    trigger_type: TriggerType = Field(..., description="Type of trigger")
    enabled: bool = Field(True, description="Whether rule is enabled")
    threshold: Optional[float] = Field(None, description="Threshold value for trigger")
    duration_minutes: int = Field(5, description="Minimum time between alerts (minutes)")
    severity: AlertSeverity = Field(AlertSeverity.WARNING, description="Alert severity")
    destinations: list[str] = Field(default_factory=list, description="Destination IDs")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AlertRuleResponse(BaseModel):
    """Response model for an alert rule."""
    
    id: str
    name: str
    trigger_type: TriggerType
    enabled: bool
    threshold: Optional[float]
    duration_minutes: int
    severity: AlertSeverity
    destinations: list[str]
    metadata: dict[str, Any]


class AlertDestinationCreate(BaseModel):
    """Request model for creating an alert destination."""
    
    name: str = Field(..., description="Destination name")
    type: AlertDestinationType = Field(..., description="Type of destination")
    enabled: bool = Field(True, description="Whether destination is enabled")
    config: dict[str, Any] = Field(..., description="Destination configuration")


class AlertDestinationResponse(BaseModel):
    """Response model for an alert destination."""
    
    id: str
    name: str
    type: AlertDestinationType
    enabled: bool
    config: dict[str, Any]


class AlertResponse(BaseModel):
    """Response model for an alert."""
    
    id: str
    rule_id: str
    trigger_type: TriggerType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    resource_id: Optional[str]
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    acknowledged_by: Optional[str]
    metadata: dict[str, Any]


class AcknowledgeAlertRequest(BaseModel):
    """Request model for acknowledging an alert."""
    
    acknowledged_by: str = Field(..., description="User acknowledging the alert")


# API Endpoints

@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(rule: AlertRuleCreate) -> AlertRuleResponse:
    """
    Create a new alert rule.
    
    Args:
        rule: Alert rule configuration
        
    Returns:
        Created alert rule
    """
    engine = get_alerting_engine()
    
    # Generate unique ID
    rule_id = str(uuid.uuid4())
    
    alert_rule = AlertRule(
        id=rule_id,
        name=rule.name,
        trigger_type=rule.trigger_type,
        enabled=rule.enabled,
        threshold=rule.threshold,
        duration_minutes=rule.duration_minutes,
        severity=rule.severity,
        destinations=rule.destinations,
        metadata=rule.metadata,
    )
    
    engine.add_rule(alert_rule)
    
    return AlertRuleResponse(
        id=alert_rule.id,
        name=alert_rule.name,
        trigger_type=alert_rule.trigger_type,
        enabled=alert_rule.enabled,
        threshold=alert_rule.threshold,
        duration_minutes=alert_rule.duration_minutes,
        severity=alert_rule.severity,
        destinations=alert_rule.destinations,
        metadata=alert_rule.metadata,
    )


@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_alert_rules() -> list[AlertRuleResponse]:
    """
    List all alert rules.
    
    Returns:
        List of alert rules
    """
    engine = get_alerting_engine()
    
    return [
        AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            trigger_type=rule.trigger_type,
            enabled=rule.enabled,
            threshold=rule.threshold,
            duration_minutes=rule.duration_minutes,
            severity=rule.severity,
            destinations=rule.destinations,
            metadata=rule.metadata,
        )
        for rule in engine.rules.values()
    ]


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(rule_id: str) -> AlertRuleResponse:
    """
    Get a specific alert rule.
    
    Args:
        rule_id: Alert rule ID
        
    Returns:
        Alert rule
    """
    engine = get_alerting_engine()
    
    rule = engine.rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    return AlertRuleResponse(
        id=rule.id,
        name=rule.name,
        trigger_type=rule.trigger_type,
        enabled=rule.enabled,
        threshold=rule.threshold,
        duration_minutes=rule.duration_minutes,
        severity=rule.severity,
        destinations=rule.destinations,
        metadata=rule.metadata,
    )


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: str, rule: AlertRuleCreate) -> AlertRuleResponse:
    """
    Update an alert rule.
    
    Args:
        rule_id: Alert rule ID
        rule: Updated rule configuration
        
    Returns:
        Updated alert rule
    """
    engine = get_alerting_engine()
    
    if rule_id not in engine.rules:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    alert_rule = AlertRule(
        id=rule_id,
        name=rule.name,
        trigger_type=rule.trigger_type,
        enabled=rule.enabled,
        threshold=rule.threshold,
        duration_minutes=rule.duration_minutes,
        severity=rule.severity,
        destinations=rule.destinations,
        metadata=rule.metadata,
    )
    
    engine.add_rule(alert_rule)
    
    return AlertRuleResponse(
        id=alert_rule.id,
        name=alert_rule.name,
        trigger_type=alert_rule.trigger_type,
        enabled=alert_rule.enabled,
        threshold=alert_rule.threshold,
        duration_minutes=alert_rule.duration_minutes,
        severity=alert_rule.severity,
        destinations=alert_rule.destinations,
        metadata=alert_rule.metadata,
    )


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: str) -> dict[str, str]:
    """
    Delete an alert rule.
    
    Args:
        rule_id: Alert rule ID
        
    Returns:
        Success message
    """
    engine = get_alerting_engine()
    
    if rule_id not in engine.rules:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    engine.remove_rule(rule_id)
    
    return {"message": f"Alert rule {rule_id} deleted"}


@router.post("/destinations", response_model=AlertDestinationResponse)
async def create_alert_destination(
    destination: AlertDestinationCreate,
) -> AlertDestinationResponse:
    """
    Create a new alert destination.
    
    Args:
        destination: Alert destination configuration
        
    Returns:
        Created alert destination
    """
    engine = get_alerting_engine()
    
    # Generate unique ID
    dest_id = str(uuid.uuid4())
    
    alert_dest = AlertDestination(
        id=dest_id,
        name=destination.name,
        type=destination.type,
        enabled=destination.enabled,
        config=destination.config,
    )
    
    engine.add_destination(alert_dest)
    
    return AlertDestinationResponse(
        id=alert_dest.id,
        name=alert_dest.name,
        type=alert_dest.type,
        enabled=alert_dest.enabled,
        config=alert_dest.config,
    )


@router.get("/destinations", response_model=list[AlertDestinationResponse])
async def list_alert_destinations() -> list[AlertDestinationResponse]:
    """
    List all alert destinations.
    
    Returns:
        List of alert destinations
    """
    engine = get_alerting_engine()
    
    return [
        AlertDestinationResponse(
            id=dest.id,
            name=dest.name,
            type=dest.type,
            enabled=dest.enabled,
            config=dest.config,
        )
        for dest in engine.destinations.values()
    ]


@router.get("/destinations/{destination_id}", response_model=AlertDestinationResponse)
async def get_alert_destination(destination_id: str) -> AlertDestinationResponse:
    """
    Get a specific alert destination.
    
    Args:
        destination_id: Alert destination ID
        
    Returns:
        Alert destination
    """
    engine = get_alerting_engine()
    
    dest = engine.destinations.get(destination_id)
    if not dest:
        raise HTTPException(status_code=404, detail="Alert destination not found")
    
    return AlertDestinationResponse(
        id=dest.id,
        name=dest.name,
        type=dest.type,
        enabled=dest.enabled,
        config=dest.config,
    )


@router.put("/destinations/{destination_id}", response_model=AlertDestinationResponse)
async def update_alert_destination(
    destination_id: str,
    destination: AlertDestinationCreate,
) -> AlertDestinationResponse:
    """
    Update an alert destination.
    
    Args:
        destination_id: Alert destination ID
        destination: Updated destination configuration
        
    Returns:
        Updated alert destination
    """
    engine = get_alerting_engine()
    
    if destination_id not in engine.destinations:
        raise HTTPException(status_code=404, detail="Alert destination not found")
    
    alert_dest = AlertDestination(
        id=destination_id,
        name=destination.name,
        type=destination.type,
        enabled=destination.enabled,
        config=destination.config,
    )
    
    engine.add_destination(alert_dest)
    
    return AlertDestinationResponse(
        id=alert_dest.id,
        name=alert_dest.name,
        type=alert_dest.type,
        enabled=alert_dest.enabled,
        config=alert_dest.config,
    )


@router.delete("/destinations/{destination_id}")
async def delete_alert_destination(destination_id: str) -> dict[str, str]:
    """
    Delete an alert destination.
    
    Args:
        destination_id: Alert destination ID
        
    Returns:
        Success message
    """
    engine = get_alerting_engine()
    
    if destination_id not in engine.destinations:
        raise HTTPException(status_code=404, detail="Alert destination not found")
    
    engine.remove_destination(destination_id)
    
    return {"message": f"Alert destination {destination_id} deleted"}


@router.post("/evaluate")
async def evaluate_alert_rules(
    duration_hours: int = Query(1, ge=1, le=24, description="Time window for evaluation"),
) -> dict[str, Any]:
    """
    Manually evaluate all alert rules.
    
    Args:
        duration_hours: Time window for evaluation (1-24 hours)
        
    Returns:
        Evaluation results with newly triggered alerts
    """
    engine = get_alerting_engine()
    
    new_alerts = await engine.evaluate_rules(duration_hours)
    
    return {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "duration_hours": duration_hours,
        "new_alerts_count": len(new_alerts),
        "alerts": [
            AlertResponse(
                id=alert.id,
                rule_id=alert.rule_id,
                trigger_type=alert.trigger_type,
                severity=alert.severity,
                status=alert.status,
                title=alert.title,
                message=alert.message,
                resource_id=alert.resource_id,
                triggered_at=alert.triggered_at,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at,
                acknowledged_by=alert.acknowledged_by,
                metadata=alert.metadata,
            )
            for alert in new_alerts
        ],
    }


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
) -> list[AlertResponse]:
    """
    List alerts with optional filtering.
    
    Args:
        status: Filter by alert status
        severity: Filter by alert severity
        limit: Maximum number of results
        
    Returns:
        List of alerts
    """
    engine = get_alerting_engine()
    
    alerts = engine.get_alerts(status=status, severity=severity, limit=limit)
    
    return [
        AlertResponse(
            id=alert.id,
            rule_id=alert.rule_id,
            trigger_type=alert.trigger_type,
            severity=alert.severity,
            status=alert.status,
            title=alert.title,
            message=alert.message,
            resource_id=alert.resource_id,
            triggered_at=alert.triggered_at,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.resolved_at,
            acknowledged_by=alert.acknowledged_by,
            metadata=alert.metadata,
        )
        for alert in alerts
    ]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str) -> AlertResponse:
    """
    Get a specific alert.
    
    Args:
        alert_id: Alert ID
        
    Returns:
        Alert details
    """
    engine = get_alerting_engine()
    
    alert = engine.alerts.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse(
        id=alert.id,
        rule_id=alert.rule_id,
        trigger_type=alert.trigger_type,
        severity=alert.severity,
        status=alert.status,
        title=alert.title,
        message=alert.message,
        resource_id=alert.resource_id,
        triggered_at=alert.triggered_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        acknowledged_by=alert.acknowledged_by,
        metadata=alert.metadata,
    )


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
) -> AlertResponse:
    """
    Acknowledge an alert.
    
    Args:
        alert_id: Alert ID
        request: Acknowledgment details
        
    Returns:
        Updated alert
    """
    engine = get_alerting_engine()
    
    alert = engine.acknowledge_alert(alert_id, request.acknowledged_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    
    return AlertResponse(
        id=alert.id,
        rule_id=alert.rule_id,
        trigger_type=alert.trigger_type,
        severity=alert.severity,
        status=alert.status,
        title=alert.title,
        message=alert.message,
        resource_id=alert.resource_id,
        triggered_at=alert.triggered_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        acknowledged_by=alert.acknowledged_by,
        metadata=alert.metadata,
    )


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(alert_id: str) -> AlertResponse:
    """
    Resolve an alert.
    
    Args:
        alert_id: Alert ID
        
    Returns:
        Resolved alert
    """
    engine = get_alerting_engine()
    
    alert = engine.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    
    return AlertResponse(
        id=alert.id,
        rule_id=alert.rule_id,
        trigger_type=alert.trigger_type,
        severity=alert.severity,
        status=alert.status,
        title=alert.title,
        message=alert.message,
        resource_id=alert.resource_id,
        triggered_at=alert.triggered_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        acknowledged_by=alert.acknowledged_by,
        metadata=alert.metadata,
    )


@router.get("/resources/{resource_id}/history", response_model=list[AlertResponse])
async def get_resource_alert_history(
    resource_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
) -> list[AlertResponse]:
    """
    Get alert history for a specific resource.
    
    Args:
        resource_id: Resource ID
        days: Number of days to look back
        
    Returns:
        Alert history for the resource
    """
    engine = get_alerting_engine()
    
    alerts = engine.get_alert_history(resource_id, days)
    
    return [
        AlertResponse(
            id=alert.id,
            rule_id=alert.rule_id,
            trigger_type=alert.trigger_type,
            severity=alert.severity,
            status=alert.status,
            title=alert.title,
            message=alert.message,
            resource_id=alert.resource_id,
            triggered_at=alert.triggered_at,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.resolved_at,
            acknowledged_by=alert.acknowledged_by,
            metadata=alert.metadata,
        )
        for alert in alerts
    ]
