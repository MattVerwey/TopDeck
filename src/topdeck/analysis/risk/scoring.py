"""
Risk scoring algorithms.

Enhanced risk scoring based on research:
- Resource type impacts vary significantly (API gateways vs storage vs compute)
- Risk = Likelihood × Impact (industry standard)
- Different resource categories need different treatment
- Considers: blast radius, data sensitivity, recovery complexity, cascading failures
"""

import logging
from enum import Enum
from typing import Any

from .models import RiskLevel

logger = logging.getLogger(__name__)


class ResourceImpactCategory(str, Enum):
    """
    Categories of resource impact types based on failure mode.
    
    Different resource types have different failure characteristics:
    - Entry points: Block access to all downstream services
    - Data stores: Data loss, compliance, recovery time
    - Infrastructure: Cascade to all hosted workloads
    - Integration: Transaction integrity, message loss
    """
    ENTRY_POINT = "entry_point"  # API gateways, load balancers - block downstream access
    DATA_STORE = "data_store"  # Databases, caches - data availability/integrity
    INFRASTRUCTURE = "infrastructure"  # AKS, VM hosts - cascade to workloads
    MESSAGING = "messaging"  # Service Bus, queues - message loss, async communication
    COMPUTE = "compute"  # VMs, containers, functions - service availability
    SECURITY = "security"  # Key Vault, auth - credential/access impact
    NETWORKING = "networking"  # VNets, NSGs - connectivity
    STORAGE = "storage"  # Blob, file - data availability


class RiskScorer:
    """
    Calculates risk scores for resources based on multiple factors.
    """

    # Default weights for risk factors (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "dependency_count": 0.25,  # How many services depend on this
        "criticality": 0.30,  # How critical is this service
        "failure_rate": 0.20,  # Historical failure rate
        "time_since_change": -0.10,  # Longer = less risky (negative weight)
        "redundancy": -0.15,  # More redundancy = less risky (negative weight)
    }

    # Criticality factors for different resource types
    # Based on research: Risk = Likelihood × Impact
    # Factors consider: blast radius, data sensitivity, recovery complexity, user impact
    CRITICALITY_FACTORS = {
        # CRITICAL TIER (35-45): Authentication, Security, Critical Data Stores
        # These affect security posture and/or contain sensitive data
        "key_vault": 45,  # Credential leaks affect entire infrastructure
        "authentication": 45,  # Auth failures block all user access
        "active_directory": 40,  # Identity provider - affects all services
        "identity_provider": 40,  # Same as AD
        
        # HIGH TIER (28-35): Databases, Entry Points, Core Infrastructure
        # Data stores with business-critical data
        "database": 35,  # Generic database - business data at risk
        "sql_database": 35,  # Structured business data
        "sql_server": 33,  # Host for multiple databases
        "cosmos_db": 35,  # NoSQL - often mission-critical data
        "postgresql_server": 33,
        "postgresql_flexible_server": 33,
        "mysql_server": 33,
        "mysql_flexible_server": 33,
        "mariadb_server": 30,
        
        # Entry points - failure blocks access to all downstream services
        "api_gateway": 35,  # Central entry point - bottleneck for all APIs
        "app_gateway": 35,  # Application delivery - affects all backend services
        "application_gateway": 35,
        "front_door": 33,  # Global entry point
        "traffic_manager": 30,  # DNS-level routing
        
        # Messaging & Queuing - async communication backbone
        "servicebus_namespace": 32,  # Message infrastructure
        "servicebus_topic": 30,  # Pub/sub messaging
        "servicebus_queue": 30,  # Point-to-point messaging
        "event_hub": 30,  # Event streaming platform
        "event_grid": 28,  # Event routing
        "servicebus_subscription": 22,  # Individual subscriber
        
        # Container orchestration - hosts multiple workloads
        "aks": 32,  # Kubernetes - multiple services depend on cluster health
        "eks": 32,  # AWS Kubernetes
        "gke_cluster": 32,  # GCP Kubernetes
        "kubernetes": 32,
        "kubernetes_cluster": 32,
        
        # MEDIUM-HIGH TIER (20-28): Caches, Load Balancers, Compute
        # Caching layer - performance impact but usually has fallback
        "cache": 28,  # Generic cache
        "redis_cache": 28,  # In-memory cache - performance degradation
        "redis_enterprise": 28,
        
        # Load balancing - traffic routing for backend services
        "load_balancer": 26,  # Network load balancer - single point for traffic
        "application_load_balancer": 28,  # Application-aware routing
        
        # Compute resources running business logic
        "web_app": 22,  # User-facing web application
        "app_service": 22,  # Azure App Service
        "function_app": 20,  # Serverless functions
        "logic_app": 20,  # Workflow automation
        "container_instance": 18,  # Containerized workload
        "pod": 18,  # Kubernetes pod
        
        # MEDIUM TIER (12-20): Supporting Infrastructure
        # Container infrastructure
        "container_registry": 18,  # Image registry - deployment dependency
        
        # Storage services - data availability but usually backed up
        "storage_account": 16,  # Azure storage - varies by use case
        "blob_storage": 16,  # Object storage
        "file_service": 15,  # File shares
        "table_service": 14,  # NoSQL tables
        "queue_service": 14,  # Simple queues
        "data_lake_store": 18,  # Analytics data
        
        # Compute infrastructure
        "vm": 15,  # Virtual machine
        "virtual_machine": 15,
        "vm_scale_set": 18,  # Auto-scaling VM group
        
        # LOW TIER (5-12): Networking, Monitoring, Non-Critical
        # Network infrastructure - usually redundant
        "virtual_network": 8,  # Network isolation
        "vnet": 8,
        "subnet": 6,  # Network segment
        "network_security_group": 10,  # Firewall rules
        "network_interface": 8,  # NIC
        "public_ip": 8,  # Public IP address
        "route_table": 7,  # Routing rules
        "nat_gateway": 10,  # NAT for outbound traffic
        
        # VPN and connectivity - usually has alternatives
        "vpn_gateway": 12,  # VPN connectivity
        "express_route_circuit": 15,  # Dedicated connection
        "vpn_connection": 10,
        
        # Supporting services
        "dns_zone": 12,  # DNS - affects discoverability
        "cdn_profile": 10,  # Content delivery - performance not availability
        "cdn_endpoint": 10,
    }

    # Infrastructure types that host multiple services and require HA/redundancy
    # These get additional criticality boost when lacking redundancy
    # Research shows: Infrastructure failures have cascading impact on all hosted services
    INFRASTRUCTURE_TYPES = frozenset([
        "aks", "eks", "gke_cluster", "kubernetes", "kubernetes_cluster",
        "load_balancer", "application_load_balancer", "cluster",
        "app_gateway", "application_gateway", "api_gateway",
        "front_door", "traffic_manager"
    ])
    
    # Resource impact category mapping
    # Determines the primary failure mode and downstream effect pattern
    IMPACT_CATEGORY_MAP = {
        # Entry points - failure blocks ALL downstream access
        ResourceImpactCategory.ENTRY_POINT: [
            "api_gateway", "app_gateway", "application_gateway",
            "front_door", "traffic_manager", "load_balancer",
            "application_load_balancer"
        ],
        
        # Data stores - data availability, integrity, compliance risk
        ResourceImpactCategory.DATA_STORE: [
            "database", "sql_database", "sql_server", "cosmos_db",
            "postgresql_server", "postgresql_flexible_server",
            "mysql_server", "mysql_flexible_server", "mariadb_server",
            "cache", "redis_cache", "redis_enterprise"
        ],
        
        # Infrastructure - hosts workloads, cascading failures
        ResourceImpactCategory.INFRASTRUCTURE: [
            "aks", "eks", "gke_cluster", "kubernetes", "kubernetes_cluster",
            "vm_scale_set", "availability_set", "cluster"
        ],
        
        # Messaging - async communication, message loss, transaction integrity
        ResourceImpactCategory.MESSAGING: [
            "servicebus_namespace", "servicebus_topic", "servicebus_queue",
            "event_hub", "event_grid", "servicebus_subscription",
            "queue_service"
        ],
        
        # Security - credential leaks, access control failures
        ResourceImpactCategory.SECURITY: [
            "key_vault", "authentication", "active_directory",
            "identity_provider"
        ],
        
        # Compute - service availability
        ResourceImpactCategory.COMPUTE: [
            "web_app", "app_service", "function_app", "logic_app",
            "vm", "virtual_machine", "pod", "container_instance"
        ],
        
        # Storage - data availability (usually backed up)
        ResourceImpactCategory.STORAGE: [
            "storage_account", "blob_storage", "file_service",
            "table_service", "data_lake_store"
        ],
        
        # Networking - connectivity issues
        ResourceImpactCategory.NETWORKING: [
            "virtual_network", "vnet", "subnet", "network_security_group",
            "network_interface", "public_ip", "route_table", "nat_gateway",
            "vpn_gateway", "express_route_circuit", "vpn_connection"
        ]
    }

    def __init__(self, weights: dict[str, float] | None = None):
        """
        Initialize risk scorer.

        Args:
            weights: Custom weights for risk factors (optional)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def calculate_risk_score(
        self,
        dependency_count: int,
        dependents_count: int,
        resource_type: str,
        is_single_point_of_failure: bool,
        deployment_failure_rate: float = 0.0,
        time_since_last_change_hours: float | None = None,
        has_redundancy: bool = False,
        **kwargs: Any,
    ) -> float:
        """
        Calculate overall risk score for a resource.

        Args:
            dependency_count: Number of resources this depends on
            dependents_count: Number of resources depending on this
            resource_type: Type of resource
            is_single_point_of_failure: Whether this is a SPOF
            deployment_failure_rate: Historical failure rate (0-1)
            time_since_last_change_hours: Hours since last deployment
            has_redundancy: Whether resource has redundant alternatives
            **kwargs: Additional factors

        Returns:
            Risk score from 0-100
        """
        # Start with criticality as the base score (this ensures different resource types 
        # have different base risk levels)
        criticality = self._calculate_criticality(
            resource_type, is_single_point_of_failure, dependents_count, has_redundancy
        )
        # Criticality contributes its full value (30% weight applied later)
        base_score = criticality
        
        # Factor 1: Dependency impact (more dependents = higher risk)
        # Normalize to 0-100 scale (assume max 50 dependents is very high risk)
        dependency_impact = min(100, (dependents_count / 50) * 100)
        dependency_contribution = dependency_impact * (self.weights["dependency_count"] / self.weights["criticality"])

        # Factor 2: Historical failure rate
        # Already normalized to 0-1, scale to 0-100
        failure_impact = deployment_failure_rate * 100
        failure_contribution = failure_impact * (self.weights["failure_rate"] / self.weights["criticality"])

        # Factor 3: Time since last change (recent changes increase risk)
        time_contribution = 0.0
        if time_since_last_change_hours is not None:
            # Normalize: 0 hours = 100 (maximum risk from recency), 720+ hours (30 days) = 0 (no risk from recency)
            # Recent changes add risk, old changes add minimal risk
            recency_risk_factor = max(0, min(100, 100 - (time_since_last_change_hours / 720) * 100))
            # Use absolute value of weight since we want this to ADD to risk for recent changes
            time_contribution = recency_risk_factor * (abs(self.weights["time_since_change"]) / self.weights["criticality"])

        # Factor 4: Redundancy (reduces risk)
        # Instead of a negative contribution, treat lack of redundancy as a multiplier
        if not has_redundancy:
            # No redundancy increases risk by 20%
            redundancy_multiplier = 1.2
        else:
            # Having redundancy reduces risk by 15%
            redundancy_multiplier = 0.85
        
        # Calculate total score: base score modified by other factors and redundancy
        score = (base_score + dependency_contribution + failure_contribution + time_contribution) * redundancy_multiplier
        
        # Store individual contributions for debugging
        criticality_contribution = base_score
        redundancy_contribution = (redundancy_multiplier - 1.0) * (base_score + dependency_contribution + failure_contribution + time_contribution)

        # Log score calculation breakdown for debugging
        logger.debug(
            f"Risk score breakdown for {resource_type}: "
            f"total={score:.2f}, dep_contrib={dependency_contribution:.2f}, "
            f"crit_contrib={criticality_contribution:.2f}, fail_contrib={failure_contribution:.2f}, "
            f"time_contrib={time_contribution:.2f}, redund_contrib={redundancy_contribution:.2f}"
        )

        # Ensure score is within bounds
        return max(0.0, min(100.0, score))

    def _calculate_criticality(
        self, resource_type: str, is_spof: bool, dependents_count: int, has_redundancy: bool = False
    ) -> float:
        """
        Calculate criticality score for a resource.
        
        Enhanced to consider:
        - Base criticality from resource type
        - Impact category (entry point, data store, etc.)
        - SPOF status
        - Number of dependents
        - Infrastructure redundancy requirements

        Args:
            resource_type: Type of resource
            is_spof: Whether this is a single point of failure
            dependents_count: Number of dependents
            has_redundancy: Whether resource has redundant alternatives

        Returns:
            Criticality score (0-100)
        """
        # Base criticality from resource type
        base_criticality = self.CRITICALITY_FACTORS.get(
            resource_type.lower(), 10  # Default for unknown types
        )

        # Get impact category for this resource type
        impact_category = self._get_impact_category(resource_type)
        
        # Impact category modifiers based on research
        # Entry points and security have highest impact multiplier
        category_multipliers = {
            ResourceImpactCategory.ENTRY_POINT: 1.3,  # Blocks ALL downstream services
            ResourceImpactCategory.SECURITY: 1.25,  # Affects entire infrastructure
            ResourceImpactCategory.DATA_STORE: 1.15,  # Data loss, compliance
            ResourceImpactCategory.INFRASTRUCTURE: 1.2,  # Cascades to workloads
            ResourceImpactCategory.MESSAGING: 1.1,  # Transaction integrity
            ResourceImpactCategory.COMPUTE: 1.0,  # Service availability
            ResourceImpactCategory.STORAGE: 0.9,  # Usually backed up
            ResourceImpactCategory.NETWORKING: 0.85,  # Usually redundant
        }
        
        multiplier = category_multipliers.get(impact_category, 1.0)
        base_criticality *= multiplier

        # Boost if it's a SPOF
        if is_spof:
            base_criticality += 15
        
        # Infrastructure components (AKS, EKS, load balancers, clusters) without HA/redundancy
        # should have higher criticality since they can bring down many services
        # Note: resource_type is converted to lowercase for case-insensitive comparison
        if resource_type.lower() in self.INFRASTRUCTURE_TYPES and not has_redundancy:
            # Significant boost for infrastructure without HA - these are critical
            base_criticality += 20

        # Boost based on number of dependents
        if dependents_count > 10:
            base_criticality += 20
        elif dependents_count > 5:
            base_criticality += 10
        elif dependents_count > 0:
            base_criticality += 5

        return min(100.0, float(base_criticality))
    
    def _get_impact_category(self, resource_type: str) -> ResourceImpactCategory:
        """
        Determine the impact category for a resource type.
        
        This helps understand the primary failure mode and downstream effects.
        
        Args:
            resource_type: Type of resource
            
        Returns:
            ResourceImpactCategory enum value
        """
        resource_type_lower = resource_type.lower()
        
        # Check each category mapping
        for category, types in self.IMPACT_CATEGORY_MAP.items():
            if resource_type_lower in types:
                return category
        
        # Default to compute if not found
        return ResourceImpactCategory.COMPUTE

    def get_risk_level(self, risk_score: float) -> RiskLevel:
        """
        Convert numeric risk score to categorical level.

        Args:
            risk_score: Numeric score (0-100)

        Returns:
            RiskLevel enum
        """
        if risk_score >= 75:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def generate_recommendations(
        self,
        risk_score: float,
        is_spof: bool,
        has_redundancy: bool,
        dependents_count: int,
        deployment_failure_rate: float,
    ) -> list[str]:
        """
        Generate risk mitigation recommendations.

        Args:
            risk_score: Current risk score
            is_spof: Whether this is a SPOF
            has_redundancy: Whether resource has redundancy
            dependents_count: Number of dependents
            deployment_failure_rate: Historical failure rate

        Returns:
            List of recommendations
        """
        recommendations = []

        # High risk recommendations
        if risk_score >= 75:
            recommendations.append("⚠️ CRITICAL RISK: Deploy only during maintenance windows")
            recommendations.append("Implement comprehensive monitoring and alerting")
            recommendations.append("Prepare detailed rollback procedures")

        # SPOF recommendations
        if is_spof:
            recommendations.append(
                "🔴 Single Point of Failure: Add redundancy or failover capability"
            )
            if not has_redundancy:
                recommendations.append(
                    "Consider deploying redundant instances across availability zones"
                )

        # High dependency recommendations
        if dependents_count > 10:
            recommendations.append(
                f"High dependency count ({dependents_count} dependents): "
                "Implement circuit breakers and fallback mechanisms"
            )

        # Failure rate recommendations
        if deployment_failure_rate > 0.2:  # > 20% failure rate
            recommendations.append(
                f"High failure rate ({deployment_failure_rate:.1%}): "
                "Review deployment process and add more comprehensive testing"
            )

        # General recommendations
        if risk_score >= 50:
            recommendations.append("Implement canary deployments to minimize blast radius")
            recommendations.append("Ensure all dependencies are properly health-checked")

        # Default recommendation if none generated
        if not recommendations and risk_score > 25:
            recommendations.append("Monitor deployment closely and be prepared to rollback")

        return recommendations
