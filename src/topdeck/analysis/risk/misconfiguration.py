"""
Misconfiguration detection for infrastructure resources.

Identifies common security and reliability misconfigurations like:
- Missing availability zones
- No replication configured
- Missing backups
- Firewall not enabled
- Other cloud provider best practices
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MisconfigurationIssue:
    """
    Represents a misconfiguration found in a resource.
    
    Attributes:
        issue_type: Type of misconfiguration (e.g., "no_availability_zone")
        severity: Severity level (low, medium, high, critical)
        title: Short description of the issue
        description: Detailed description of the misconfiguration
        recommendation: How to fix the issue
        affected_property: The resource property that has the issue
    """
    issue_type: str
    severity: str
    title: str
    description: str
    recommendation: str
    affected_property: str | None = None


@dataclass
class MisconfigurationReport:
    """
    Report of all misconfigurations found for a resource.
    
    Attributes:
        resource_id: ID of the resource
        resource_name: Name of the resource
        resource_type: Type of resource
        issues: List of misconfiguration issues found
        severity_counts: Count of issues by severity
        risk_score_impact: How much these issues increase risk score (0-100)
    """
    resource_id: str
    resource_name: str
    resource_type: str
    issues: list[MisconfigurationIssue] = field(default_factory=list)
    severity_counts: dict[str, int] = field(default_factory=dict)
    risk_score_impact: float = 0.0
    
    def __post_init__(self):
        """Calculate severity counts and risk score impact."""
        self.severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        
        severity_weights = {
            "critical": 25.0,
            "high": 15.0,
            "medium": 8.0,
            "low": 3.0,
        }
        
        total_impact = 0.0
        for issue in self.issues:
            severity = issue.severity.lower()
            if severity in self.severity_counts:
                self.severity_counts[severity] += 1
                total_impact += severity_weights.get(severity, 0.0)
        
        # Cap the risk score impact at 50 points
        self.risk_score_impact = min(total_impact, 50.0)


class MisconfigurationDetector:
    """
    Detects common infrastructure misconfigurations.
    
    Analyzes resource properties to identify security and reliability issues.
    """
    
    def detect_misconfigurations(
        self, 
        resource_id: str, 
        resource_name: str,
        resource_type: str, 
        properties: dict[str, Any]
    ) -> MisconfigurationReport:
        """
        Detect misconfigurations in a resource.
        
        Args:
            resource_id: Unique resource identifier
            resource_name: Human-readable resource name
            resource_type: Type of resource
            properties: Dictionary of resource properties
            
        Returns:
            MisconfigurationReport with all detected issues
        """
        issues: list[MisconfigurationIssue] = []
        
        # Normalize resource type for consistent checking
        normalized_type = resource_type.lower().replace(" ", "_")
        
        # Check for availability zone issues
        issues.extend(self._check_availability_zones(normalized_type, properties))
        
        # Check for replication configuration
        issues.extend(self._check_replication(normalized_type, properties))
        
        # Check for backup configuration
        issues.extend(self._check_backup(normalized_type, properties))
        
        # Check for firewall/security rules
        issues.extend(self._check_firewall(normalized_type, properties))
        
        # Check for encryption
        issues.extend(self._check_encryption(normalized_type, properties))
        
        # Check for redundancy
        issues.extend(self._check_redundancy(normalized_type, properties))
        
        # Check for monitoring
        issues.extend(self._check_monitoring(normalized_type, properties))
        
        return MisconfigurationReport(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
            issues=issues,
        )
    
    def _check_availability_zones(
        self, resource_type: str, properties: dict[str, Any]
    ) -> list[MisconfigurationIssue]:
        """Check for availability zone configuration."""
        issues = []
        
        # Resources that should have availability zone redundancy
        az_critical_types = [
            "database", "sql_server", "mysql_server", "postgresql_server",
            "cosmos_db", "virtual_machine", "vm", "kubernetes_cluster",
            "aks_cluster", "load_balancer", "storage_account"
        ]
        
        if resource_type not in az_critical_types:
            return issues
        
        # Check various property names for AZ configuration
        az_properties = ["availability_zones", "zones", "zone_redundant", "zone_redundancy"]
        has_az = False
        
        for prop in az_properties:
            if prop in properties:
                value = properties[prop]
                # Check if AZ is configured
                if value and (
                    (isinstance(value, list) and len(value) > 1) or
                    (isinstance(value, bool) and value) or
                    (isinstance(value, str) and value.lower() in ["true", "enabled", "yes"])
                ):
                    has_az = True
                    break
        
        if not has_az:
            issues.append(MisconfigurationIssue(
                issue_type="no_availability_zone",
                severity="high",
                title="No Availability Zone Redundancy",
                description=f"This {resource_type} is not configured with availability zone redundancy, "
                           "making it vulnerable to zone-level failures.",
                recommendation="Enable multi-availability zone deployment to improve resilience "
                              "and protect against zone failures.",
                affected_property="availability_zones",
            ))
        
        return issues
    
    def _check_replication(
        self, resource_type: str, properties: dict[str, Any]
    ) -> list[MisconfigurationIssue]:
        """Check for replication configuration."""
        issues = []
        
        # Resources that should have replication
        replication_types = [
            "database", "sql_server", "mysql_server", "postgresql_server",
            "cosmos_db", "storage_account", "redis_cache"
        ]
        
        if resource_type not in replication_types:
            return issues
        
        # Check for replication settings
        replication_properties = [
            "replication_enabled", "geo_replication", "replicas", 
            "replica_count", "replication_factor", "replication_type",
            "geo_redundant", "redundancy"
        ]
        
        has_replication = False
        for prop in replication_properties:
            if prop in properties:
                value = properties[prop]
                if value and (
                    (isinstance(value, bool) and value) or
                    (isinstance(value, int) and value > 0) or
                    (isinstance(value, str) and value.lower() not in ["none", "disabled", "false", ""])
                ):
                    has_replication = True
                    break
        
        if not has_replication:
            issues.append(MisconfigurationIssue(
                issue_type="no_replication",
                severity="high",
                title="No Replication Configured",
                description=f"This {resource_type} does not have replication enabled, "
                           "risking data loss and service availability.",
                recommendation="Enable geo-replication or configure read replicas to improve "
                              "data durability and availability.",
                affected_property="replication_enabled",
            ))
        
        return issues
    
    def _check_backup(
        self, resource_type: str, properties: dict[str, Any]
    ) -> list[MisconfigurationIssue]:
        """Check for backup configuration."""
        issues = []
        
        # Resources that should have backups
        backup_types = [
            "database", "sql_server", "mysql_server", "postgresql_server",
            "cosmos_db", "storage_account", "virtual_machine", "vm"
        ]
        
        if resource_type not in backup_types:
            return issues
        
        # Check for backup settings
        backup_properties = [
            "backup_enabled", "backup_policy", "backup_retention_days",
            "automated_backups", "backup_configuration", "backup_vault"
        ]
        
        has_backup = False
        for prop in backup_properties:
            if prop in properties:
                value = properties[prop]
                if value and (
                    (isinstance(value, bool) and value) or
                    (isinstance(value, int) and value > 0) or
                    (isinstance(value, dict) and len(value) > 0) or
                    (isinstance(value, str) and value.lower() not in ["none", "disabled", "false", ""])
                ):
                    has_backup = True
                    break
        
        if not has_backup:
            issues.append(MisconfigurationIssue(
                issue_type="no_backup",
                severity="critical",
                title="No Backup Configured",
                description=f"This {resource_type} does not have automated backups configured, "
                           "risking permanent data loss in case of failure or corruption.",
                recommendation="Enable automated backups with appropriate retention policies "
                              "to protect against data loss.",
                affected_property="backup_enabled",
            ))
        
        return issues
    
    def _check_firewall(
        self, resource_type: str, properties: dict[str, Any]
    ) -> list[MisconfigurationIssue]:
        """Check for firewall/security rules."""
        issues = []
        
        # Resources that should have firewall rules
        firewall_types = [
            "database", "sql_server", "mysql_server", "postgresql_server",
            "virtual_machine", "vm", "storage_account", "virtual_network",
            "subnet", "app_service", "web_app", "function_app"
        ]
        
        if resource_type not in firewall_types:
            return issues
        
        # Check for firewall/security settings
        firewall_properties = [
            "firewall_enabled", "firewall_rules", "network_security_group",
            "security_rules", "access_policies", "ip_rules", "network_acls"
        ]
        
        has_firewall = False
        for prop in firewall_properties:
            if prop in properties:
                value = properties[prop]
                if value and (
                    (isinstance(value, bool) and value) or
                    (isinstance(value, list) and len(value) > 0) or
                    (isinstance(value, dict) and len(value) > 0) or
                    (isinstance(value, str) and value.lower() not in ["none", "disabled", "false", ""])
                ):
                    has_firewall = True
                    break
        
        if not has_firewall:
            issues.append(MisconfigurationIssue(
                issue_type="no_firewall",
                severity="critical",
                title="No Firewall Rules Configured",
                description=f"This {resource_type} does not have firewall rules or network "
                           "security groups configured, exposing it to unauthorized access.",
                recommendation="Configure firewall rules or network security groups to restrict "
                              "access to only authorized sources.",
                affected_property="firewall_rules",
            ))
        
        return issues
    
    def _check_encryption(
        self, resource_type: str, properties: dict[str, Any]
    ) -> list[MisconfigurationIssue]:
        """Check for encryption configuration."""
        issues = []
        
        # Resources that should have encryption
        encryption_types = [
            "database", "sql_server", "mysql_server", "postgresql_server",
            "cosmos_db", "storage_account", "virtual_machine", "vm"
        ]
        
        if resource_type not in encryption_types:
            return issues
        
        # Check for encryption settings
        encryption_properties = [
            "encryption_enabled", "encrypted", "encryption_at_rest",
            "tde_enabled", "transparent_data_encryption"
        ]
        
        has_encryption = False
        for prop in encryption_properties:
            if prop in properties:
                value = properties[prop]
                if value and (
                    (isinstance(value, bool) and value) or
                    (isinstance(value, str) and value.lower() in ["true", "enabled", "yes"])
                ):
                    has_encryption = True
                    break
        
        if not has_encryption:
            issues.append(MisconfigurationIssue(
                issue_type="no_encryption",
                severity="high",
                title="Encryption Not Enabled",
                description=f"This {resource_type} does not have encryption enabled, "
                           "exposing sensitive data to potential breaches.",
                recommendation="Enable encryption at rest to protect sensitive data from "
                              "unauthorized access.",
                affected_property="encryption_enabled",
            ))
        
        return issues
    
    def _check_redundancy(
        self, resource_type: str, properties: dict[str, Any]
    ) -> list[MisconfigurationIssue]:
        """Check for redundancy configuration."""
        issues = []
        
        # Resources that should have redundancy
        redundancy_types = [
            "load_balancer", "application_gateway", "api_gateway",
            "virtual_network", "kubernetes_cluster", "aks_cluster"
        ]
        
        if resource_type not in redundancy_types:
            return issues
        
        # Check for redundancy settings
        redundancy_properties = [
            "redundancy_enabled", "redundant_instances", "instance_count",
            "min_instances", "replica_count"
        ]
        
        has_redundancy = False
        for prop in redundancy_properties:
            if prop in properties:
                value = properties[prop]
                if value and (
                    (isinstance(value, bool) and value) or
                    (isinstance(value, int) and value > 1)
                ):
                    has_redundancy = True
                    break
        
        if not has_redundancy:
            issues.append(MisconfigurationIssue(
                issue_type="no_redundancy",
                severity="medium",
                title="No Redundancy Configured",
                description=f"This {resource_type} does not have redundant instances, "
                           "creating a single point of failure.",
                recommendation="Configure multiple instances or enable redundancy to improve "
                              "availability and fault tolerance.",
                affected_property="instance_count",
            ))
        
        return issues
    
    def _check_monitoring(
        self, resource_type: str, properties: dict[str, Any]
    ) -> list[MisconfigurationIssue]:
        """Check for monitoring configuration."""
        issues = []
        
        # All production resources should have monitoring
        # Check for monitoring settings
        monitoring_properties = [
            "monitoring_enabled", "diagnostics_enabled", "logs_enabled",
            "metrics_enabled", "alerts_configured"
        ]
        
        has_monitoring = False
        for prop in monitoring_properties:
            if prop in properties:
                value = properties[prop]
                if value and (
                    (isinstance(value, bool) and value) or
                    (isinstance(value, str) and value.lower() in ["true", "enabled", "yes"])
                ):
                    has_monitoring = True
                    break
        
        if not has_monitoring:
            issues.append(MisconfigurationIssue(
                issue_type="no_monitoring",
                severity="medium",
                title="Monitoring Not Configured",
                description=f"This {resource_type} does not have monitoring or diagnostics enabled, "
                           "limiting visibility into performance and issues.",
                recommendation="Enable monitoring, diagnostics, and alerting to detect issues "
                              "early and improve operational visibility.",
                affected_property="monitoring_enabled",
            ))
        
        return issues
