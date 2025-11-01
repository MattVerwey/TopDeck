"""
Audit logging for TopDeck.

Tracks all security-relevant events and user actions.
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_CREATED = "auth.token.created"
    TOKEN_REVOKED = "auth.token.revoked"

    # Authorization events
    PERMISSION_GRANTED = "authz.permission.granted"
    PERMISSION_DENIED = "authz.permission.denied"
    ROLE_ASSIGNED = "authz.role.assigned"
    ROLE_REVOKED = "authz.role.revoked"

    # Resource access events
    RESOURCE_VIEWED = "resource.viewed"
    RESOURCE_CREATED = "resource.created"
    RESOURCE_UPDATED = "resource.updated"
    RESOURCE_DELETED = "resource.deleted"

    # Discovery events
    DISCOVERY_STARTED = "discovery.started"
    DISCOVERY_COMPLETED = "discovery.completed"
    DISCOVERY_FAILED = "discovery.failed"

    # Risk analysis events
    RISK_ANALYZED = "risk.analyzed"
    RISK_ASSESSMENT_VIEWED = "risk.assessment.viewed"

    # Configuration events
    CONFIG_VIEWED = "config.viewed"
    CONFIG_UPDATED = "config.updated"

    # User management events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_DISABLED = "user.disabled"
    USER_ENABLED = "user.enabled"

    # Integration events
    INTEGRATION_CONFIGURED = "integration.configured"
    INTEGRATION_REMOVED = "integration.removed"

    # Security events
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"


class AuditLevel(str, Enum):
    """Severity level for audit events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Audit event model."""

    event_id: str = Field(default_factory=lambda: f"audit-{datetime.now(UTC).timestamp()}")
    event_type: AuditEventType
    level: AuditLevel = AuditLevel.INFO
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    username: str | None = None
    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    action: str | None = None
    result: str | None = None  # success, failure, denied
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_log_dict(self) -> dict[str, Any]:
        """Convert audit event to dictionary for logging."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "level": self.level.value,
            "timestamp": self.timestamp.isoformat(),
            "username": self.username,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "result": self.result,
            "message": self.message,
            **self.metadata,
        }


class AuditLogger:
    """
    Audit logger for recording security events.

    In production, this should write to:
    - A dedicated audit log file
    - A separate audit database
    - A SIEM system (e.g., Splunk, ELK)
    """

    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger("topdeck.audit")
        # Set up a separate audit log handler
        # In production, configure this to write to a secure, append-only storage

    def log(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: The audit event to log
        """
        log_dict = event.to_log_dict()

        # Log based on level
        if event.level == AuditLevel.CRITICAL:
            self.logger.critical(f"AUDIT: {event.message}", extra=log_dict)
        elif event.level == AuditLevel.ERROR:
            self.logger.error(f"AUDIT: {event.message}", extra=log_dict)
        elif event.level == AuditLevel.WARNING:
            self.logger.warning(f"AUDIT: {event.message}", extra=log_dict)
        else:
            self.logger.info(f"AUDIT: {event.message}", extra=log_dict)

        # In production, also write to:
        # 1. Dedicated audit log file (immutable, append-only)
        # 2. Audit database table in Neo4j
        # 3. SIEM system if available

    def log_login(self, username: str, success: bool, ip_address: str | None = None) -> None:
        """Log a login attempt."""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
            level=AuditLevel.INFO if success else AuditLevel.WARNING,
            username=username,
            ip_address=ip_address,
            result="success" if success else "failure",
            message=f"Login {'succeeded' if success else 'failed'} for user {username}",
        )
        self.log(event)

    def log_permission_check(
        self, username: str, permission: str, granted: bool, resource_id: str | None = None
    ) -> None:
        """Log a permission check."""
        event = AuditEvent(
            event_type=(
                AuditEventType.PERMISSION_GRANTED if granted else AuditEventType.PERMISSION_DENIED
            ),
            level=AuditLevel.INFO if granted else AuditLevel.WARNING,
            username=username,
            resource_id=resource_id,
            action=permission,
            result="granted" if granted else "denied",
            message=f"Permission {permission} {'granted' if granted else 'denied'} for {username}",
        )
        self.log(event)

    def log_resource_access(
        self, username: str, resource_type: str, resource_id: str, action: str
    ) -> None:
        """Log resource access."""
        event_type_map = {
            "view": AuditEventType.RESOURCE_VIEWED,
            "create": AuditEventType.RESOURCE_CREATED,
            "update": AuditEventType.RESOURCE_UPDATED,
            "delete": AuditEventType.RESOURCE_DELETED,
        }

        event = AuditEvent(
            event_type=event_type_map.get(action, AuditEventType.RESOURCE_VIEWED),
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result="success",
            message=f"User {username} {action}ed {resource_type} {resource_id}",
        )
        self.log(event)

    def log_config_change(
        self, username: str, config_key: str, old_value: Any, new_value: Any
    ) -> None:
        """Log a configuration change."""
        event = AuditEvent(
            event_type=AuditEventType.CONFIG_UPDATED,
            level=AuditLevel.WARNING,  # Config changes are important
            username=username,
            action="config_update",
            message=f"Configuration changed by {username}: {config_key}",
            metadata={
                "config_key": config_key,
                "old_value": str(old_value),
                "new_value": str(new_value),
            },
        )
        self.log(event)

    def log_suspicious_activity(
        self, username: str | None, activity: str, ip_address: str | None = None
    ) -> None:
        """Log suspicious activity."""
        event = AuditEvent(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            level=AuditLevel.CRITICAL,
            username=username,
            ip_address=ip_address,
            message=f"Suspicious activity detected: {activity}",
            metadata={"activity": activity},
        )
        self.log(event)


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions
def log_login(username: str, success: bool, ip_address: str | None = None) -> None:
    """Log a login attempt."""
    audit_logger.log_login(username, success, ip_address)


def log_permission_check(
    username: str, permission: str, granted: bool, resource_id: str | None = None
) -> None:
    """Log a permission check."""
    audit_logger.log_permission_check(username, permission, granted, resource_id)


def log_resource_access(username: str, resource_type: str, resource_id: str, action: str) -> None:
    """Log resource access."""
    audit_logger.log_resource_access(username, resource_type, resource_id, action)


def log_config_change(username: str, config_key: str, old_value: Any, new_value: Any) -> None:
    """Log a configuration change."""
    audit_logger.log_config_change(username, config_key, old_value, new_value)


def log_suspicious_activity(
    username: str | None, activity: str, ip_address: str | None = None
) -> None:
    """Log suspicious activity."""
    audit_logger.log_suspicious_activity(username, activity, ip_address)
