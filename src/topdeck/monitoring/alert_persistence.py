"""
Alert persistence layer for storing alerts, rules, and destinations in Neo4j.

This module replaces the in-memory storage in AlertingEngine with persistent
Neo4j storage, addressing a key limitation of Phase 7.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any, Optional

from topdeck.monitoring.alerting import (
    Alert,
    AlertDestination,
    AlertDestinationType,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    TriggerType,
)
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class AlertPersistence:
    """
    Manages persistent storage of alerts, rules, and destinations in Neo4j.
    
    Features:
    - Alert rule persistence with full CRUD
    - Alert destination persistence
    - Alert history tracking
    - Efficient querying and filtering
    - Automatic cleanup of old alerts
    """
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize alert persistence.
        
        Args:
            neo4j_client: Neo4j client for database operations
        """
        self.neo4j = neo4j_client
    
    async def initialize_schema(self) -> None:
        """
        Initialize Neo4j schema for alerts.
        
        Creates indexes and constraints for optimal performance.
        """
        # Create constraints for unique IDs
        constraints = [
            "CREATE CONSTRAINT alert_rule_id IF NOT EXISTS FOR (r:AlertRule) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT alert_destination_id IF NOT EXISTS FOR (d:AlertDestination) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT alert_id IF NOT EXISTS FOR (a:Alert) REQUIRE a.id IS UNIQUE",
        ]
        
        # Create indexes for common queries
        indexes = [
            "CREATE INDEX alert_status_idx IF NOT EXISTS FOR (a:Alert) ON (a.status)",
            "CREATE INDEX alert_triggered_at_idx IF NOT EXISTS FOR (a:Alert) ON (a.triggered_at)",
            "CREATE INDEX alert_severity_idx IF NOT EXISTS FOR (a:Alert) ON (a.severity)",
            "CREATE INDEX alert_resource_idx IF NOT EXISTS FOR (a:Alert) ON (a.resource_id)",
            "CREATE INDEX rule_enabled_idx IF NOT EXISTS FOR (r:AlertRule) ON (r.enabled)",
        ]
        
        for statement in constraints + indexes:
            try:
                await self.neo4j.execute_query(statement)
            except Exception as e:
                logger.warning(f"Schema initialization warning: {e}")
    
    # Alert Rule Methods
    
    async def save_rule(self, rule: AlertRule) -> None:
        """
        Save or update an alert rule.
        
        Args:
            rule: AlertRule to save
        """
        query = """
        MERGE (r:AlertRule {id: $id})
        SET r.name = $name,
            r.trigger_type = $trigger_type,
            r.enabled = $enabled,
            r.threshold = $threshold,
            r.duration_minutes = $duration_minutes,
            r.severity = $severity,
            r.destinations = $destinations,
            r.metadata = $metadata,
            r.updated_at = datetime()
        WITH r
        WHERE NOT EXISTS(r.created_at)
        SET r.created_at = datetime()
        """
        
        params = {
            "id": rule.id,
            "name": rule.name,
            "trigger_type": rule.trigger_type.value,
            "enabled": rule.enabled,
            "threshold": rule.threshold,
            "duration_minutes": rule.duration_minutes,
            "severity": rule.severity.value,
            "destinations": json.dumps(rule.destinations),
            "metadata": json.dumps(rule.metadata),
        }
        
        await self.neo4j.execute_query(query, params)
        logger.info(f"Saved alert rule: {rule.id}")
    
    async def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """
        Get an alert rule by ID.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            AlertRule if found, None otherwise
        """
        query = """
        MATCH (r:AlertRule {id: $id})
        RETURN r
        """
        
        results = await self.neo4j.execute_query(query, {"id": rule_id})
        
        if not results:
            return None
        
        return self._node_to_rule(results[0]["r"])
    
    async def list_rules(self, enabled_only: bool = False) -> list[AlertRule]:
        """
        List all alert rules.
        
        Args:
            enabled_only: If True, only return enabled rules
            
        Returns:
            List of AlertRule objects
        """
        query = """
        MATCH (r:AlertRule)
        WHERE $enabled_only = false OR r.enabled = true
        RETURN r
        ORDER BY r.created_at DESC
        """
        
        results = await self.neo4j.execute_query(query, {"enabled_only": enabled_only})
        
        return [self._node_to_rule(row["r"]) for row in results]
    
    async def delete_rule(self, rule_id: str) -> bool:
        """
        Delete an alert rule.
        
        Args:
            rule_id: Rule ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (r:AlertRule {id: $id})
        DELETE r
        RETURN count(r) as deleted
        """
        
        results = await self.neo4j.execute_query(query, {"id": rule_id})
        deleted = results[0]["deleted"] if results else 0
        
        if deleted:
            logger.info(f"Deleted alert rule: {rule_id}")
        
        return deleted > 0
    
    # Alert Destination Methods
    
    async def save_destination(self, destination: AlertDestination) -> None:
        """
        Save or update an alert destination.
        
        Args:
            destination: AlertDestination to save
        """
        query = """
        MERGE (d:AlertDestination {id: $id})
        SET d.name = $name,
            d.type = $type,
            d.enabled = $enabled,
            d.config = $config,
            d.updated_at = datetime()
        WITH d
        WHERE NOT EXISTS(d.created_at)
        SET d.created_at = datetime()
        """
        
        params = {
            "id": destination.id,
            "name": destination.name,
            "type": destination.type.value,
            "enabled": destination.enabled,
            "config": json.dumps(destination.config),
        }
        
        await self.neo4j.execute_query(query, params)
        logger.info(f"Saved alert destination: {destination.id}")
    
    async def get_destination(self, destination_id: str) -> Optional[AlertDestination]:
        """
        Get an alert destination by ID.
        
        Args:
            destination_id: Destination ID
            
        Returns:
            AlertDestination if found, None otherwise
        """
        query = """
        MATCH (d:AlertDestination {id: $id})
        RETURN d
        """
        
        results = await self.neo4j.execute_query(query, {"id": destination_id})
        
        if not results:
            return None
        
        return self._node_to_destination(results[0]["d"])
    
    async def list_destinations(self, enabled_only: bool = False) -> list[AlertDestination]:
        """
        List all alert destinations.
        
        Args:
            enabled_only: If True, only return enabled destinations
            
        Returns:
            List of AlertDestination objects
        """
        query = """
        MATCH (d:AlertDestination)
        WHERE $enabled_only = false OR d.enabled = true
        RETURN d
        ORDER BY d.created_at DESC
        """
        
        results = await self.neo4j.execute_query(query, {"enabled_only": enabled_only})
        
        return [self._node_to_destination(row["d"]) for row in results]
    
    async def delete_destination(self, destination_id: str) -> bool:
        """
        Delete an alert destination.
        
        Args:
            destination_id: Destination ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (d:AlertDestination {id: $id})
        DELETE d
        RETURN count(d) as deleted
        """
        
        results = await self.neo4j.execute_query(query, {"id": destination_id})
        deleted = results[0]["deleted"] if results else 0
        
        if deleted:
            logger.info(f"Deleted alert destination: {destination_id}")
        
        return deleted > 0
    
    # Alert Methods
    
    async def save_alert(self, alert: Alert) -> None:
        """
        Save or update an alert.
        
        Args:
            alert: Alert to save
        """
        query = """
        MERGE (a:Alert {id: $id})
        SET a.rule_id = $rule_id,
            a.trigger_type = $trigger_type,
            a.severity = $severity,
            a.status = $status,
            a.title = $title,
            a.message = $message,
            a.resource_id = $resource_id,
            a.triggered_at = $triggered_at,
            a.acknowledged_at = $acknowledged_at,
            a.resolved_at = $resolved_at,
            a.acknowledged_by = $acknowledged_by,
            a.metadata = $metadata,
            a.updated_at = datetime()
        WITH a
        WHERE NOT EXISTS(a.created_at)
        SET a.created_at = datetime()
        """
        
        params = {
            "id": alert.id,
            "rule_id": alert.rule_id,
            "trigger_type": alert.trigger_type.value,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "title": alert.title,
            "message": alert.message,
            "resource_id": alert.resource_id,
            "triggered_at": alert.triggered_at.isoformat(),
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "acknowledged_by": alert.acknowledged_by,
            "metadata": json.dumps(alert.metadata),
        }
        
        await self.neo4j.execute_query(query, params)
        logger.debug(f"Saved alert: {alert.id}")
    
    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Get an alert by ID.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Alert if found, None otherwise
        """
        query = """
        MATCH (a:Alert {id: $id})
        RETURN a
        """
        
        results = await self.neo4j.execute_query(query, {"id": alert_id})
        
        if not results:
            return None
        
        return self._node_to_alert(results[0]["a"])
    
    async def list_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        resource_id: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> list[Alert]:
        """
        List alerts with optional filtering.
        
        Args:
            status: Filter by alert status
            severity: Filter by severity
            resource_id: Filter by resource ID
            hours: Only return alerts from last N hours
            limit: Maximum number of alerts to return
            
        Returns:
            List of Alert objects
        """
        query = """
        MATCH (a:Alert)
        WHERE datetime(a.triggered_at) >= datetime() - duration({hours: $hours})
          AND ($status IS NULL OR a.status = $status)
          AND ($severity IS NULL OR a.severity = $severity)
          AND ($resource_id IS NULL OR a.resource_id = $resource_id)
        RETURN a
        ORDER BY a.triggered_at DESC
        LIMIT $limit
        """
        
        params = {
            "status": status.value if status else None,
            "severity": severity.value if severity else None,
            "resource_id": resource_id,
            "hours": hours,
            "limit": limit,
        }
        
        results = await self.neo4j.execute_query(query, params)
        
        return [self._node_to_alert(row["a"]) for row in results]
    
    async def get_active_alerts(self) -> list[Alert]:
        """
        Get all active (non-resolved) alerts.
        
        Returns:
            List of active Alert objects
        """
        query = """
        MATCH (a:Alert)
        WHERE a.status IN ['active', 'acknowledged']
        RETURN a
        ORDER BY a.triggered_at DESC
        """
        
        results = await self.neo4j.execute_query(query)
        
        return [self._node_to_alert(row["a"]) for row in results]
    
    async def get_resource_alert_history(
        self,
        resource_id: str,
        hours: int = 24,
    ) -> list[Alert]:
        """
        Get alert history for a specific resource.
        
        Args:
            resource_id: Resource ID
            hours: Look back period in hours
            
        Returns:
            List of Alert objects for the resource
        """
        return await self.list_alerts(resource_id=resource_id, hours=hours)
    
    async def cleanup_old_alerts(self, days: int = 30) -> int:
        """
        Delete resolved alerts older than specified days.
        
        Args:
            days: Delete alerts older than this many days
            
        Returns:
            Number of alerts deleted
        """
        query = """
        MATCH (a:Alert)
        WHERE a.status = 'resolved'
          AND datetime(a.resolved_at) < datetime() - duration({days: $days})
        DELETE a
        RETURN count(a) as deleted
        """
        
        results = await self.neo4j.execute_query(query, {"days": days})
        deleted = results[0]["deleted"] if results else 0
        
        if deleted:
            logger.info(f"Cleaned up {deleted} old alerts")
        
        return deleted
    
    # Helper Methods
    
    def _node_to_rule(self, node: dict[str, Any]) -> AlertRule:
        """Convert Neo4j node to AlertRule."""
        return AlertRule(
            id=node["id"],
            name=node["name"],
            trigger_type=TriggerType(node["trigger_type"]),
            enabled=node["enabled"],
            threshold=node.get("threshold"),
            duration_minutes=node["duration_minutes"],
            severity=AlertSeverity(node["severity"]),
            destinations=json.loads(node.get("destinations", "[]")),
            metadata=json.loads(node.get("metadata", "{}")),
        )
    
    def _node_to_destination(self, node: dict[str, Any]) -> AlertDestination:
        """Convert Neo4j node to AlertDestination."""
        return AlertDestination(
            id=node["id"],
            name=node["name"],
            type=AlertDestinationType(node["type"]),
            enabled=node["enabled"],
            config=json.loads(node.get("config", "{}")),
        )
    
    def _node_to_alert(self, node: dict[str, Any]) -> Alert:
        """Convert Neo4j node to Alert."""
        return Alert(
            id=node["id"],
            rule_id=node["rule_id"],
            trigger_type=TriggerType(node["trigger_type"]),
            severity=AlertSeverity(node["severity"]),
            status=AlertStatus(node["status"]),
            title=node["title"],
            message=node["message"],
            resource_id=node.get("resource_id"),
            triggered_at=datetime.fromisoformat(node["triggered_at"]),
            acknowledged_at=datetime.fromisoformat(node["acknowledged_at"]) if node.get("acknowledged_at") else None,
            resolved_at=datetime.fromisoformat(node["resolved_at"]) if node.get("resolved_at") else None,
            acknowledged_by=node.get("acknowledged_by"),
            metadata=json.loads(node.get("metadata", "{}")),
        )
