"""
Alert grouping and aggregation functionality.

Provides intelligent grouping of related alerts to reduce alert fatigue:
- Group by resource
- Group by severity
- Group by time window
- Aggregate similar alerts
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Optional

from topdeck.monitoring.alerting import Alert, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)


class GroupingStrategy(str, Enum):
    """Alert grouping strategies."""
    
    BY_RESOURCE = "by_resource"
    BY_SEVERITY = "by_severity"
    BY_TYPE = "by_type"
    BY_TIME_WINDOW = "by_time_window"
    BY_RULE = "by_rule"


@dataclass
class AlertGroup:
    """A group of related alerts."""
    
    id: str
    name: str
    grouping_strategy: GroupingStrategy
    alerts: list[Alert] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Aggregated information
    highest_severity: AlertSeverity = AlertSeverity.INFO
    active_count: int = 0
    acknowledged_count: int = 0
    resolved_count: int = 0
    affected_resources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_alert(self, alert: Alert) -> None:
        """Add an alert to the group and update aggregated info."""
        self.alerts.append(alert)
        self.updated_at = datetime.now(UTC)
        
        # Update counts
        if alert.status == AlertStatus.ACTIVE:
            self.active_count += 1
        elif alert.status == AlertStatus.ACKNOWLEDGED:
            self.acknowledged_count += 1
        elif alert.status == AlertStatus.RESOLVED:
            self.resolved_count += 1
        
        # Update highest severity
        severity_order = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.ERROR: 2,
            AlertSeverity.CRITICAL: 3,
        }
        if severity_order[alert.severity] > severity_order[self.highest_severity]:
            self.highest_severity = alert.severity
        
        # Update affected resources
        if alert.resource_id and alert.resource_id not in self.affected_resources:
            self.affected_resources.append(alert.resource_id)
    
    def get_summary(self) -> str:
        """Get a summary of the alert group."""
        total = len(self.alerts)
        return (
            f"{self.name}: {total} alert(s) "
            f"(Active: {self.active_count}, "
            f"Acknowledged: {self.acknowledged_count}, "
            f"Resolved: {self.resolved_count})"
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "grouping_strategy": self.grouping_strategy.value,
            "alert_count": len(self.alerts),
            "highest_severity": self.highest_severity.value,
            "active_count": self.active_count,
            "acknowledged_count": self.acknowledged_count,
            "resolved_count": self.resolved_count,
            "affected_resources": self.affected_resources,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "summary": self.get_summary(),
            "metadata": self.metadata,
        }


class AlertGrouper:
    """
    Groups and aggregates alerts based on various strategies.
    
    Features:
    - Multiple grouping strategies
    - Time-based aggregation
    - Smart alert deduplication
    - Summary generation
    """
    
    def __init__(self):
        """Initialize the alert grouper."""
        self.groups: dict[str, AlertGroup] = {}
    
    def group_alerts(
        self,
        alerts: list[Alert],
        strategy: GroupingStrategy = GroupingStrategy.BY_RESOURCE,
        time_window_minutes: int = 60,
    ) -> list[AlertGroup]:
        """
        Group alerts based on the specified strategy.
        
        Args:
            alerts: List of alerts to group
            strategy: Grouping strategy to use
            time_window_minutes: Time window for time-based grouping
            
        Returns:
            List of AlertGroup objects
        """
        if strategy == GroupingStrategy.BY_RESOURCE:
            return self._group_by_resource(alerts)
        elif strategy == GroupingStrategy.BY_SEVERITY:
            return self._group_by_severity(alerts)
        elif strategy == GroupingStrategy.BY_TYPE:
            return self._group_by_type(alerts)
        elif strategy == GroupingStrategy.BY_TIME_WINDOW:
            return self._group_by_time_window(alerts, time_window_minutes)
        elif strategy == GroupingStrategy.BY_RULE:
            return self._group_by_rule(alerts)
        else:
            logger.warning(f"Unknown grouping strategy: {strategy}")
            return []
    
    def _group_by_resource(self, alerts: list[Alert]) -> list[AlertGroup]:
        """Group alerts by affected resource."""
        groups_dict: dict[str, list[Alert]] = defaultdict(list)
        
        for alert in alerts:
            resource_id = alert.resource_id or "unknown"
            groups_dict[resource_id].append(alert)
        
        groups = []
        for resource_id, resource_alerts in groups_dict.items():
            group_id = f"resource-{resource_id}"
            resource_name = resource_alerts[0].metadata.get("service_name", resource_id)
            
            group = AlertGroup(
                id=group_id,
                name=f"Alerts for {resource_name}",
                grouping_strategy=GroupingStrategy.BY_RESOURCE,
                metadata={"resource_id": resource_id},
            )
            
            for alert in resource_alerts:
                group.add_alert(alert)
            
            groups.append(group)
        
        return groups
    
    def _group_by_severity(self, alerts: list[Alert]) -> list[AlertGroup]:
        """Group alerts by severity level."""
        groups_dict: dict[AlertSeverity, list[Alert]] = defaultdict(list)
        
        for alert in alerts:
            groups_dict[alert.severity].append(alert)
        
        groups = []
        for severity, severity_alerts in groups_dict.items():
            group_id = f"severity-{severity.value}"
            
            group = AlertGroup(
                id=group_id,
                name=f"{severity.value.upper()} Alerts",
                grouping_strategy=GroupingStrategy.BY_SEVERITY,
                metadata={"severity": severity.value},
            )
            
            for alert in severity_alerts:
                group.add_alert(alert)
            
            groups.append(group)
        
        # Sort by severity (critical first)
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.ERROR: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 3,
        }
        groups.sort(key=lambda g: severity_order[g.highest_severity])
        
        return groups
    
    def _group_by_type(self, alerts: list[Alert]) -> list[AlertGroup]:
        """Group alerts by trigger type."""
        groups_dict: dict[str, list[Alert]] = defaultdict(list)
        
        for alert in alerts:
            trigger_type = alert.trigger_type.value
            groups_dict[trigger_type].append(alert)
        
        groups = []
        for trigger_type, type_alerts in groups_dict.items():
            group_id = f"type-{trigger_type}"
            
            # Friendly names for trigger types
            type_names = {
                "health_score_drop": "Health Score Drops",
                "critical_anomaly": "Critical Anomalies",
                "multiple_services_degraded": "Multiple Service Failures",
                "traffic_pattern_anomaly": "Traffic Pattern Anomalies",
                "service_failure": "Service Failures",
            }
            
            group = AlertGroup(
                id=group_id,
                name=type_names.get(trigger_type, trigger_type.replace("_", " ").title()),
                grouping_strategy=GroupingStrategy.BY_TYPE,
                metadata={"trigger_type": trigger_type},
            )
            
            for alert in type_alerts:
                group.add_alert(alert)
            
            groups.append(group)
        
        return groups
    
    def _group_by_time_window(
        self,
        alerts: list[Alert],
        window_minutes: int,
    ) -> list[AlertGroup]:
        """Group alerts by time window."""
        # Sort alerts by time
        sorted_alerts = sorted(alerts, key=lambda a: a.triggered_at)
        
        groups = []
        current_group: Optional[AlertGroup] = None
        window_start: Optional[datetime] = None
        
        for alert in sorted_alerts:
            # Start a new group if needed
            if current_group is None or (
                window_start is not None
                and alert.triggered_at > window_start + timedelta(minutes=window_minutes)
            ):
                if current_group:
                    groups.append(current_group)
                
                window_start = alert.triggered_at
                window_end = window_start + timedelta(minutes=window_minutes)
                
                group_id = f"time-{int(window_start.timestamp())}"
                group = AlertGroup(
                    id=group_id,
                    name=f"Alerts {window_start.strftime('%Y-%m-%d %H:%M')} - {window_end.strftime('%H:%M')}",
                    grouping_strategy=GroupingStrategy.BY_TIME_WINDOW,
                    metadata={
                        "window_start": window_start.isoformat(),
                        "window_end": window_end.isoformat(),
                    },
                )
                current_group = group
            
            if current_group:
                current_group.add_alert(alert)
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _group_by_rule(self, alerts: list[Alert]) -> list[AlertGroup]:
        """Group alerts by the rule that triggered them."""
        groups_dict: dict[str, list[Alert]] = defaultdict(list)
        
        for alert in alerts:
            rule_id = alert.rule_id
            groups_dict[rule_id].append(alert)
        
        groups = []
        for rule_id, rule_alerts in groups_dict.items():
            group_id = f"rule-{rule_id}"
            
            # Get rule name from first alert's metadata or use rule_id
            rule_name = rule_alerts[0].metadata.get("rule_name", rule_id)
            
            group = AlertGroup(
                id=group_id,
                name=f"Rule: {rule_name}",
                grouping_strategy=GroupingStrategy.BY_RULE,
                metadata={"rule_id": rule_id},
            )
            
            for alert in rule_alerts:
                group.add_alert(alert)
            
            groups.append(group)
        
        return groups
    
    def deduplicate_alerts(
        self,
        alerts: list[Alert],
        similarity_threshold: float = 0.8,
    ) -> list[Alert]:
        """
        Deduplicate similar alerts.
        
        Args:
            alerts: List of alerts to deduplicate
            similarity_threshold: Similarity threshold (0-1)
            
        Returns:
            Deduplicated list of alerts
        """
        if not alerts:
            return []
        
        unique_alerts = []
        seen_signatures = set()
        
        for alert in alerts:
            # Create a signature based on key attributes
            signature = (
                alert.resource_id or "none",
                alert.trigger_type.value,
                alert.severity.value,
            )
            
            if signature not in seen_signatures:
                unique_alerts.append(alert)
                seen_signatures.add(signature)
            else:
                # Update the existing alert with newer information
                for existing_alert in unique_alerts:
                    existing_signature = (
                        existing_alert.resource_id or "none",
                        existing_alert.trigger_type.value,
                        existing_alert.severity.value,
                    )
                    if existing_signature == signature:
                        # Keep the most recent alert
                        if alert.triggered_at > existing_alert.triggered_at:
                            unique_alerts.remove(existing_alert)
                            unique_alerts.append(alert)
                        break
        
        logger.info(f"Deduplicated {len(alerts)} alerts to {len(unique_alerts)}")
        
        return unique_alerts
    
    def create_digest(
        self,
        alerts: list[Alert],
        strategy: GroupingStrategy = GroupingStrategy.BY_RESOURCE,
    ) -> dict[str, Any]:
        """
        Create a digest summary of alerts.
        
        Args:
            alerts: List of alerts
            strategy: Grouping strategy for the digest
            
        Returns:
            Dictionary containing the digest
        """
        groups = self.group_alerts(alerts, strategy)
        
        digest = {
            "total_alerts": len(alerts),
            "total_groups": len(groups),
            "grouping_strategy": strategy.value,
            "generated_at": datetime.now(UTC).isoformat(),
            "groups": [group.to_dict() for group in groups],
            "summary": {
                "active": sum(g.active_count for g in groups),
                "acknowledged": sum(g.acknowledged_count for g in groups),
                "resolved": sum(g.resolved_count for g in groups),
                "critical": sum(1 for g in groups if g.highest_severity == AlertSeverity.CRITICAL),
                "high": sum(1 for g in groups if g.highest_severity == AlertSeverity.ERROR),
                "medium": sum(1 for g in groups if g.highest_severity == AlertSeverity.WARNING),
                "low": sum(1 for g in groups if g.highest_severity == AlertSeverity.INFO),
            },
        }
        
        return digest
