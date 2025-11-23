"""
Alerting engine for TopDeck.

Provides rule-based alerting for service health, anomalies, and traffic patterns.
Supports multiple notification channels: Email, Slack, PagerDuty, custom webhooks.
Now supports persistent storage via Neo4j.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Optional

import aiohttp
import aiosmtplib
from email.message import EmailMessage

from topdeck.monitoring.live_diagnostics import LiveDiagnosticsService

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertDestinationType(str, Enum):
    """Types of alert destinations."""
    
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"


class TriggerType(str, Enum):
    """Types of alert triggers."""
    
    HEALTH_SCORE_DROP = "health_score_drop"
    CRITICAL_ANOMALY = "critical_anomaly"
    MULTIPLE_SERVICES_DEGRADED = "multiple_services_degraded"
    TRAFFIC_PATTERN_ANOMALY = "traffic_pattern_anomaly"
    SERVICE_FAILURE = "service_failure"


@dataclass
class AlertRule:
    """Configuration for an alert rule."""
    
    id: str
    name: str
    trigger_type: TriggerType
    enabled: bool = True
    threshold: Optional[float] = None
    duration_minutes: int = 5
    severity: AlertSeverity = AlertSeverity.WARNING
    destinations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertDestination:
    """Configuration for an alert destination."""
    
    id: str
    name: str
    type: AlertDestinationType
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """An active or historical alert."""
    
    id: str
    rule_id: str
    trigger_type: TriggerType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    resource_id: Optional[str] = None
    triggered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AlertingEngine:
    """
    Alerting engine that evaluates rules and sends notifications.
    
    Features:
    - Rule-based alert triggers
    - Multiple notification channels
    - Alert deduplication
    - Alert history and acknowledgment
    - Persistent storage via Neo4j (optional, falls back to in-memory)
    """
    
    def __init__(
        self,
        diagnostics_service: LiveDiagnosticsService,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_from_address: Optional[str] = None,
        persistence: Optional[Any] = None,  # AlertPersistence
    ):
        """
        Initialize the alerting engine.
        
        Args:
            diagnostics_service: Live diagnostics service for health data
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            smtp_from_address: From address for emails
            persistence: Optional AlertPersistence instance for persistent storage
        """
        self.diagnostics_service = diagnostics_service
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_from_address = smtp_from_address
        self.persistence = persistence
        
        # In-memory storage (used when persistence is not available, or as cache)
        self.rules: dict[str, AlertRule] = {}
        self.destinations: dict[str, AlertDestination] = {}
        self.alerts: dict[str, Alert] = {}
        self.active_alerts: dict[str, Alert] = {}
        
        # Alert deduplication tracking
        self.last_alert_times: dict[str, datetime] = {}
    
    async def add_rule(self, rule: AlertRule) -> None:
        """Add or update an alert rule."""
        if self.persistence:
            await self.persistence.save_rule(rule)
        
        self.rules[rule.id] = rule
        logger.info(f"Alert rule added/updated: {rule.name} ({rule.id})")
    
    async def remove_rule(self, rule_id: str) -> None:
        """Remove an alert rule."""
        if self.persistence:
            await self.persistence.delete_rule(rule_id)
        
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Alert rule removed: {rule_id}")
    
    async def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get an alert rule by ID."""
        if self.persistence:
            return await self.persistence.get_rule(rule_id)
        return self.rules.get(rule_id)
    
    async def list_rules(self, enabled_only: bool = False) -> list[AlertRule]:
        """List all alert rules."""
        if self.persistence:
            return await self.persistence.list_rules(enabled_only=enabled_only)
        
        rules = list(self.rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return rules
    
    async def add_destination(self, destination: AlertDestination) -> None:
        """Add or update an alert destination."""
        if self.persistence:
            await self.persistence.save_destination(destination)
        
        self.destinations[destination.id] = destination
        logger.info(f"Alert destination added/updated: {destination.name} ({destination.id})")
    
    async def remove_destination(self, destination_id: str) -> None:
        """Remove an alert destination."""
        if self.persistence:
            await self.persistence.delete_destination(destination_id)
        
        if destination_id in self.destinations:
            del self.destinations[destination_id]
            logger.info(f"Alert destination removed: {destination_id}")
    
    async def get_destination(self, destination_id: str) -> Optional[AlertDestination]:
        """Get an alert destination by ID."""
        if self.persistence:
            return await self.persistence.get_destination(destination_id)
        return self.destinations.get(destination_id)
    
    async def list_destinations(self, enabled_only: bool = False) -> list[AlertDestination]:
        """List all alert destinations."""
        if self.persistence:
            return await self.persistence.list_destinations(enabled_only=enabled_only)
        
        destinations = list(self.destinations.values())
        if enabled_only:
            destinations = [d for d in destinations if d.enabled]
        return destinations
    
    async def evaluate_rules(self, duration_hours: int = 1) -> list[Alert]:
        """
        Evaluate all enabled alert rules.
        
        Args:
            duration_hours: Time window for evaluation
            
        Returns:
            List of newly triggered alerts
        """
        new_alerts = []
        
        # Get rules from persistence or in-memory storage
        rules = await self.list_rules(enabled_only=True)
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            try:
                triggered = await self._evaluate_rule(rule, duration_hours)
                if triggered:
                    alert = await self._create_alert(rule, triggered)
                    new_alerts.append(alert)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}", exc_info=True)
        
        return new_alerts
    
    async def _evaluate_rule(
        self,
        rule: AlertRule,
        duration_hours: int,
    ) -> Optional[dict[str, Any]]:
        """
        Evaluate a single alert rule.
        
        Returns:
            Trigger context if rule triggered, None otherwise
        """
        # Check deduplication - don't re-trigger too soon
        last_time = self.last_alert_times.get(rule.id)
        if last_time:
            time_since = datetime.now(UTC) - last_time
            if time_since < timedelta(minutes=rule.duration_minutes):
                return None
        
        if rule.trigger_type == TriggerType.HEALTH_SCORE_DROP:
            return await self._check_health_score_drop(rule, duration_hours)
        elif rule.trigger_type == TriggerType.CRITICAL_ANOMALY:
            return await self._check_critical_anomaly(rule, duration_hours)
        elif rule.trigger_type == TriggerType.MULTIPLE_SERVICES_DEGRADED:
            return await self._check_multiple_degraded(rule, duration_hours)
        elif rule.trigger_type == TriggerType.TRAFFIC_PATTERN_ANOMALY:
            return await self._check_traffic_anomaly(rule, duration_hours)
        elif rule.trigger_type == TriggerType.SERVICE_FAILURE:
            return await self._check_service_failure(rule, duration_hours)
        
        return None
    
    async def _check_health_score_drop(
        self,
        rule: AlertRule,
        duration_hours: int,
    ) -> Optional[dict[str, Any]]:
        """Check if any service health score dropped below threshold."""
        threshold = rule.threshold or 50.0
        
        try:
            snapshot = await self.diagnostics_service.get_live_snapshot(duration_hours)
            
            for service in snapshot.services:
                if service.health_score < threshold:
                    return {
                        "service_id": service.resource_id,
                        "service_name": service.resource_name,
                        "health_score": service.health_score,
                        "threshold": threshold,
                    }
        except Exception as e:
            logger.error(f"Error checking health score: {e}")
        
        return None
    
    async def _check_critical_anomaly(
        self,
        rule: AlertRule,
        duration_hours: int,
    ) -> Optional[dict[str, Any]]:
        """Check for critical anomalies."""
        try:
            anomalies = await self.diagnostics_service.detect_anomalies(
                duration_hours=duration_hours,
                severity="critical",
                limit=1,
            )
            
            if anomalies:
                anomaly = anomalies[0]
                return {
                    "service_id": anomaly.resource_id,
                    "service_name": anomaly.resource_name,
                    "metric_name": anomaly.metric_name,
                    "severity": anomaly.severity,
                    "deviation": anomaly.deviation,
                }
        except Exception as e:
            logger.error(f"Error checking critical anomalies: {e}")
        
        return None
    
    async def _check_multiple_degraded(
        self,
        rule: AlertRule,
        duration_hours: int,
    ) -> Optional[dict[str, Any]]:
        """Check if multiple services are degraded."""
        threshold_count = int(rule.threshold or 3)
        
        try:
            snapshot = await self.diagnostics_service.get_live_snapshot(duration_hours)
            
            degraded = [s for s in snapshot.services if s.status in ["degraded", "critical"]]
            
            if len(degraded) >= threshold_count:
                return {
                    "degraded_count": len(degraded),
                    "threshold": threshold_count,
                    "services": [s.resource_name for s in degraded[:5]],
                }
        except Exception as e:
            logger.error(f"Error checking multiple degraded services: {e}")
        
        return None
    
    async def _check_traffic_anomaly(
        self,
        rule: AlertRule,
        duration_hours: int,
    ) -> Optional[dict[str, Any]]:
        """Check for abnormal traffic patterns."""
        try:
            patterns = await self.diagnostics_service.analyze_traffic_patterns(
                duration_hours=duration_hours,
                abnormal_only=True,
            )
            
            if patterns:
                pattern = patterns[0]
                return {
                    "source": pattern.source,
                    "target": pattern.target,
                    "request_rate": pattern.request_rate,
                    "error_rate": pattern.error_rate,
                }
        except Exception as e:
            logger.error(f"Error checking traffic anomalies: {e}")
        
        return None
    
    async def _check_service_failure(
        self,
        rule: AlertRule,
        duration_hours: int,
    ) -> Optional[dict[str, Any]]:
        """Check for service failures."""
        try:
            snapshot = await self.diagnostics_service.get_live_snapshot(duration_hours)
            
            failed = [s for s in snapshot.services if s.status == "critical"]
            
            if failed:
                service = failed[0]
                return {
                    "service_id": service.resource_id,
                    "service_name": service.resource_name,
                    "status": service.status,
                    "health_score": service.health_score,
                }
        except Exception as e:
            logger.error(f"Error checking service failures: {e}")
        
        return None
    
    async def _create_alert(
        self,
        rule: AlertRule,
        context: dict[str, Any],
    ) -> Alert:
        """Create an alert from a triggered rule."""
        alert_id = f"{rule.id}-{int(datetime.now(UTC).timestamp())}"
        
        # Create alert message
        title, message = self._format_alert_message(rule, context)
        
        alert = Alert(
            id=alert_id,
            rule_id=rule.id,
            trigger_type=rule.trigger_type,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            title=title,
            message=message,
            resource_id=context.get("service_id"),
            metadata=context,
        )
        
        # Store alert
        if self.persistence:
            await self.persistence.save_alert(alert)
        
        self.alerts[alert_id] = alert
        self.active_alerts[alert_id] = alert
        
        # Update deduplication tracking
        self.last_alert_times[rule.id] = alert.triggered_at
        
        # Send notifications
        await self._send_notifications(alert, rule)
        
        logger.info(f"Alert created: {alert.title} ({alert_id})")
        
        return alert
    
    def _format_alert_message(
        self,
        rule: AlertRule,
        context: dict[str, Any],
    ) -> tuple[str, str]:
        """Format alert title and message."""
        if rule.trigger_type == TriggerType.HEALTH_SCORE_DROP:
            title = f"Health Score Drop: {context.get('service_name', 'Unknown')}"
            message = (
                f"Service {context.get('service_name')} health score dropped to "
                f"{context.get('health_score', 0):.1f} (threshold: {context.get('threshold', 0):.1f})"
            )
        elif rule.trigger_type == TriggerType.CRITICAL_ANOMALY:
            title = f"Critical Anomaly: {context.get('service_name', 'Unknown')}"
            message = (
                f"Critical anomaly detected in {context.get('service_name')} - "
                f"Metric: {context.get('metric_name')}, "
                f"Deviation: {context.get('deviation', 0):.2f}"
            )
        elif rule.trigger_type == TriggerType.MULTIPLE_SERVICES_DEGRADED:
            title = f"Multiple Services Degraded"
            message = (
                f"{context.get('degraded_count', 0)} services are degraded or critical. "
                f"Services: {', '.join(context.get('services', []))}"
            )
        elif rule.trigger_type == TriggerType.TRAFFIC_PATTERN_ANOMALY:
            title = f"Traffic Pattern Anomaly"
            message = (
                f"Abnormal traffic pattern detected: {context.get('source')} → {context.get('target')} - "
                f"Request rate: {context.get('request_rate', 0):.1f}, "
                f"Error rate: {context.get('error_rate', 0):.1%}"
            )
        elif rule.trigger_type == TriggerType.SERVICE_FAILURE:
            title = f"Service Failure: {context.get('service_name', 'Unknown')}"
            message = (
                f"Service {context.get('service_name')} has failed. "
                f"Health score: {context.get('health_score', 0):.1f}"
            )
        else:
            title = f"Alert: {rule.name}"
            message = f"Alert triggered for rule: {rule.name}"
        
        return title, message
    
    async def _send_notifications(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert notifications to configured destinations."""
        for dest_id in rule.destinations:
            # Get destination from persistence or in-memory storage
            destination = await self.get_destination(dest_id)
            if not destination or not destination.enabled:
                continue
            
            try:
                if destination.type == AlertDestinationType.EMAIL:
                    await self._send_email(alert, destination)
                elif destination.type == AlertDestinationType.SLACK:
                    await self._send_slack(alert, destination)
                elif destination.type == AlertDestinationType.PAGERDUTY:
                    await self._send_pagerduty(alert, destination)
                elif destination.type == AlertDestinationType.WEBHOOK:
                    await self._send_webhook(alert, destination)
            except Exception as e:
                logger.error(f"Error sending notification to {destination.name}: {e}", exc_info=True)
    
    async def _send_email(self, alert: Alert, destination: AlertDestination) -> None:
        """Send email notification."""
        if not self.smtp_host or not self.smtp_from_address:
            logger.warning("SMTP not configured, skipping email notification")
            return
        
        to_addresses = destination.config.get("to_addresses", [])
        if not to_addresses:
            logger.warning(f"No email addresses configured for {destination.name}")
            return
        
        msg = EmailMessage()
        msg["Subject"] = f"[TopDeck Alert] {alert.title}"
        msg["From"] = self.smtp_from_address
        msg["To"] = ", ".join(to_addresses)
        
        body = f"""
TopDeck Alert

Severity: {alert.severity.upper()}
Triggered: {alert.triggered_at.isoformat()}

{alert.message}

---
Alert ID: {alert.id}
Rule ID: {alert.rule_id}
"""
        msg.set_content(body)
        
        async with aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port) as smtp:
            if self.smtp_username and self.smtp_password:
                await smtp.login(self.smtp_username, self.smtp_password)
            await smtp.send_message(msg)
        
        logger.info(f"Email sent to {to_addresses}")
    
    async def _send_slack(self, alert: Alert, destination: AlertDestination) -> None:
        """Send Slack notification."""
        webhook_url = destination.config.get("webhook_url")
        if not webhook_url:
            logger.warning(f"No Slack webhook URL configured for {destination.name}")
            return
        
        # Color based on severity
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#cc0000",
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#808080"),
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.upper(), "short": True},
                        {"title": "Status", "value": alert.status.value, "short": True},
                        {"title": "Time", "value": alert.triggered_at.isoformat(), "short": False},
                    ],
                    "footer": "TopDeck Alerting",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Slack webhook failed: {response.status}")
                else:
                    logger.info(f"Slack notification sent")
    
    async def _send_pagerduty(self, alert: Alert, destination: AlertDestination) -> None:
        """Send PagerDuty notification."""
        api_key = destination.config.get("api_key")
        routing_key = destination.config.get("routing_key")
        
        if not api_key or not routing_key:
            logger.warning(f"PagerDuty not fully configured for {destination.name}")
            return
        
        # Severity mapping
        severity_map = {
            AlertSeverity.INFO: "info",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "error",
            AlertSeverity.CRITICAL: "critical",
        }
        
        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "dedup_key": alert.id,
            "payload": {
                "summary": alert.title,
                "severity": severity_map.get(alert.severity, "error"),
                "source": "TopDeck",
                "timestamp": alert.triggered_at.isoformat(),
                "custom_details": alert.metadata,
            },
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 202:
                    logger.error(f"PagerDuty API failed: {response.status}")
                else:
                    logger.info(f"PagerDuty notification sent")
    
    async def _send_webhook(self, alert: Alert, destination: AlertDestination) -> None:
        """Send custom webhook notification."""
        webhook_url = destination.config.get("url")
        if not webhook_url:
            logger.warning(f"No webhook URL configured for {destination.name}")
            return
        
        payload = {
            "alert_id": alert.id,
            "rule_id": alert.rule_id,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "title": alert.title,
            "message": alert.message,
            "resource_id": alert.resource_id,
            "triggered_at": alert.triggered_at.isoformat(),
            "metadata": alert.metadata,
        }
        
        headers = destination.config.get("headers", {})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, headers=headers) as response:
                if response.status not in (200, 201, 202, 204):
                    logger.error(f"Webhook failed: {response.status}")
                else:
                    logger.info(f"Webhook notification sent to {webhook_url}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Optional[Alert]:
        """Acknowledge an alert."""
        # Try to get alert from persistence first
        if self.persistence:
            alert = await self.persistence.get_alert(alert_id)
        else:
            alert = self.active_alerts.get(alert_id)
        
        if not alert:
            return None
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(UTC)
        alert.acknowledged_by = acknowledged_by
        
        # Update in persistence
        if self.persistence:
            await self.persistence.save_alert(alert)
        
        # Update in-memory cache
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id] = alert
        if alert_id in self.alerts:
            self.alerts[alert_id] = alert
        
        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        
        return alert
    
    async def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Resolve an alert."""
        # Try to get alert from persistence first
        if self.persistence:
            alert = await self.persistence.get_alert(alert_id)
        else:
            alert = self.active_alerts.get(alert_id)
        
        if not alert:
            return None
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(UTC)
        
        # Update in persistence
        if self.persistence:
            await self.persistence.save_alert(alert)
        
        # Remove from active alerts
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
        
        # Keep in alert history
        if alert_id in self.alerts:
            self.alerts[alert_id] = alert
        
        logger.info(f"Alert resolved: {alert_id}")
        
        return alert
    
    async def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        resource_id: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> list[Alert]:
        """Get alerts with optional filtering."""
        # Use persistence if available
        if self.persistence:
            return await self.persistence.list_alerts(
                status=status,
                severity=severity,
                resource_id=resource_id,
                hours=hours,
                limit=limit,
            )
        
        # Fall back to in-memory storage
        alerts = list(self.alerts.values())
        
        # Filter by time
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        alerts = [a for a in alerts if a.triggered_at >= cutoff]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resource_id:
            alerts = [a for a in alerts if a.resource_id == resource_id]
        
        # Sort by triggered time (newest first)
        alerts.sort(key=lambda a: a.triggered_at, reverse=True)
        
        return alerts[:limit]
    
    async def get_alert_history(
        self,
        resource_id: str,
        hours: int = 168,  # 7 days default
    ) -> list[Alert]:
        """Get alert history for a specific resource."""
        # Use persistence if available
        if self.persistence:
            return await self.persistence.get_resource_alert_history(
                resource_id=resource_id,
                hours=hours,
            )
        
        # Fall back to in-memory storage
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        
        return [
            alert for alert in self.alerts.values()
            if alert.resource_id == resource_id and alert.triggered_at >= cutoff
        ]
