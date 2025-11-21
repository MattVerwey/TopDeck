"""
Enhanced impact analysis for comprehensive "what will happen" scenarios.

This module provides detailed analysis of:
- Downstream impacts (what services and clients will be affected)
- Upstream dependency health (what the app depends on)
- Comprehensive "what if" scenarios
"""

import logging
from typing import Any

from topdeck.storage.neo4j_client import Neo4jClient

from .dependency import DependencyAnalyzer
from .models import (
    CategorizedResource,
    DownstreamImpactAnalysis,
    ImpactLevel,
    ResourceCategory,
    UpstreamDependencyHealth,
    WhatIfAnalysis,
)

logger = logging.getLogger(__name__)


class EnhancedImpactAnalyzer:
    """
    Provides enhanced impact analysis with focus on answering:
    - "What services and clients will be affected?"
    - "What does this app depend on?"
    - "What will happen if this fails or changes?"
    """

    def __init__(self, neo4j_client: Neo4jClient, dependency_analyzer: DependencyAnalyzer):
        """
        Initialize enhanced impact analyzer.

        Args:
            neo4j_client: Neo4j client for graph database access
            dependency_analyzer: Dependency analyzer for graph queries
        """
        self.neo4j_client = neo4j_client
        self.dependency_analyzer = dependency_analyzer

    def analyze_downstream_impact(self, resource_id: str, resource_name: str) -> DownstreamImpactAnalysis:
        """
        Analyze what services and clients will be affected if this resource fails.

        This answers: "What will be brought down if this fails?"

        Args:
            resource_id: Resource to analyze
            resource_name: Name of the resource

        Returns:
            DownstreamImpactAnalysis with comprehensive impact breakdown
        """
        # Get all affected resources (both direct and indirect)
        directly_affected, indirectly_affected = self.dependency_analyzer.get_affected_resources(
            resource_id
        )

        all_affected = directly_affected + indirectly_affected

        # Categorize affected resources
        affected_by_category: dict[ResourceCategory, list[CategorizedResource]] = {}
        critical_services = []
        client_apps = []

        for resource in all_affected:
            categorized = self._categorize_resource(resource)

            # Add to category mapping
            if categorized.category not in affected_by_category:
                affected_by_category[categorized.category] = []
            affected_by_category[categorized.category].append(categorized)

            # Track critical services
            if categorized.is_critical:
                critical_services.append(categorized)

            # Track client applications
            if categorized.category == ResourceCategory.CLIENT_APP:
                client_apps.append(categorized)

        # Generate impact summaries
        user_facing_impact = self._generate_user_facing_impact(affected_by_category)
        backend_impact = self._generate_backend_impact(affected_by_category)
        data_impact = self._generate_data_impact(affected_by_category)
        business_impact = self._generate_business_impact(
            len(all_affected), critical_services, client_apps
        )

        # Estimate users affected
        estimated_users = self._estimate_users_affected(affected_by_category)

        return DownstreamImpactAnalysis(
            resource_id=resource_id,
            resource_name=resource_name,
            total_affected=len(all_affected),
            affected_by_category=affected_by_category,
            critical_services_affected=critical_services,
            client_apps_affected=client_apps,
            user_facing_impact=user_facing_impact,
            backend_impact=backend_impact,
            data_impact=data_impact,
            estimated_users_affected=estimated_users,
            business_impact_summary=business_impact,
        )

    def analyze_upstream_dependencies(
        self, resource_id: str, resource_name: str
    ) -> UpstreamDependencyHealth:
        """
        Analyze what this resource depends on and the health of those dependencies.

        This answers: "What does this app depend on and what are the risks?"

        Args:
            resource_id: Resource to analyze
            resource_name: Name of the resource

        Returns:
            UpstreamDependencyHealth with dependency analysis
        """
        # Get all dependencies
        dependencies = self._get_all_dependencies(resource_id)

        # Categorize dependencies
        dependencies_by_category: dict[ResourceCategory, list[CategorizedResource]] = {}
        unhealthy_deps = []
        spof_deps = []
        high_risk_deps = []

        for dep in dependencies:
            categorized = self._categorize_resource(dep)

            # Add to category mapping
            if categorized.category not in dependencies_by_category:
                dependencies_by_category[categorized.category] = []
            dependencies_by_category[categorized.category].append(categorized)

            # Check if dependency is unhealthy or high risk (exclusive categories)
            risk_score = dep.get("risk_score", 0)
            if 70 < risk_score <= 85:
                unhealthy_deps.append(categorized)
            elif risk_score > 85:
                categorized.impact_severity = ImpactLevel.HIGH
                high_risk_deps.append(categorized)

            # Check if dependency is SPOF
            if self._is_dependency_spof(dep.get("id", "")):
                spof_deps.append(categorized)

        # Calculate overall dependency health score
        health_score = self._calculate_dependency_health_score(
            len(dependencies), unhealthy_deps, spof_deps, high_risk_deps
        )

        # Generate recommendations
        recommendations = self._generate_dependency_recommendations(
            unhealthy_deps, spof_deps, high_risk_deps
        )

        return UpstreamDependencyHealth(
            resource_id=resource_id,
            resource_name=resource_name,
            total_dependencies=len(dependencies),
            dependencies_by_category=dependencies_by_category,
            unhealthy_dependencies=unhealthy_deps,
            single_points_of_failure=spof_deps,
            high_risk_dependencies=high_risk_deps,
            dependency_health_score=health_score,
            recommendations=recommendations,
        )

    def analyze_what_if_scenario(
        self, resource_id: str, resource_name: str, scenario_type: str = "failure"
    ) -> WhatIfAnalysis:
        """
        Comprehensive "what if" analysis for a resource.

        This answers: "What will happen if this resource fails or is changed?"

        Args:
            resource_id: Resource to analyze
            resource_name: Name of the resource
            scenario_type: Type of scenario (failure, maintenance, update, etc.)

        Returns:
            WhatIfAnalysis with complete scenario breakdown
        """
        # Get downstream impact
        downstream = self.analyze_downstream_impact(resource_id, resource_name)

        # Get upstream dependencies
        upstream = self.analyze_upstream_dependencies(resource_id, resource_name)

        # Determine overall severity
        severity = self._determine_scenario_severity(downstream, upstream)

        # Estimate timeline
        timeline = self._estimate_impact_timeline(downstream, scenario_type)

        # Generate mitigation steps
        mitigation_available, mitigation_steps = self._generate_mitigation_steps(
            downstream, upstream, scenario_type
        )

        # Determine rollback capability
        rollback_possible, rollback_steps = self._generate_rollback_steps(
            scenario_type, downstream
        )

        return WhatIfAnalysis(
            resource_id=resource_id,
            resource_name=resource_name,
            scenario_type=scenario_type,
            downstream_impact=downstream,
            upstream_dependencies=upstream,
            timeline_minutes=timeline,
            severity=severity,
            mitigation_available=mitigation_available,
            mitigation_steps=mitigation_steps,
            rollback_possible=rollback_possible,
            rollback_steps=rollback_steps,
        )

    def _categorize_resource(self, resource: dict[str, Any]) -> CategorizedResource:
        """
        Categorize a resource based on its type and properties.

        Args:
            resource: Resource dictionary with type and properties

        Returns:
            CategorizedResource with categorization
        """
        resource_type = resource.get("type", "unknown").lower()
        resource_id = resource.get("id", "unknown")
        resource_name = resource.get("name", "Unknown")

        # Determine category based on resource type
        category = ResourceCategory.BACKEND_SERVICE  # Default

        if resource_type in ["web_app", "app_service", "function_app", "api_gateway", "app_gateway"]:
            category = ResourceCategory.USER_FACING
        elif resource_type in ["database", "sql_db", "cosmos_db", "redis", "cache", "storage"]:
            category = ResourceCategory.DATA_STORE
        elif resource_type in ["load_balancer", "vnet", "subnet", "aks", "kubernetes", "cluster"]:
            category = ResourceCategory.INFRASTRUCTURE
        elif resource_type in ["webhook", "api_connection", "external_service"]:
            category = ResourceCategory.INTEGRATION
        elif resource_type in ["client_app", "mobile_app", "desktop_app", "client"]:
            category = ResourceCategory.CLIENT_APP

        # Determine if critical
        is_critical = (
            resource.get("is_critical", False)
            or resource.get("risk_score", 0) > 75
            or category in [ResourceCategory.USER_FACING, ResourceCategory.DATA_STORE]
        )

        # Determine impact severity based on category
        impact_severity = ImpactLevel.MEDIUM
        if category == ResourceCategory.USER_FACING:
            impact_severity = ImpactLevel.HIGH
        elif category == ResourceCategory.DATA_STORE:
            impact_severity = ImpactLevel.HIGH
        elif category == ResourceCategory.INFRASTRUCTURE:
            impact_severity = ImpactLevel.SEVERE

        return CategorizedResource(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
            category=category,
            relationship_type=resource.get("relationship_type", "DEPENDS_ON"),
            impact_severity=impact_severity,
            is_critical=is_critical,
        )

    def _get_all_dependencies(self, resource_id: str) -> list[dict[str, Any]]:
        """
        Get all upstream dependencies for a resource.

        Args:
            resource_id: Resource ID

        Returns:
            List of dependency dictionaries
        """
        query = """
        MATCH (r {id: $id})-[rel]->(dep)
        WHERE dep.id IS NOT NULL
        AND type(rel) IN [
            'DEPENDS_ON', 'USES', 'CONNECTS_TO', 'ROUTES_TO',
            'ACCESSES', 'AUTHENTICATES_WITH', 'READS_FROM', 'WRITES_TO'
        ]
        RETURN DISTINCT dep.id as id,
               dep.name as name,
               COALESCE(dep.resource_type, labels(dep)[0]) as type,
               type(rel) as relationship_type,
               dep.is_critical as is_critical,
               dep.risk_score as risk_score
        """

        dependencies = []
        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            for record in result:
                dependencies.append(dict(record))

        return dependencies

    def _is_unhealthy_dependency(self, dependency: dict[str, Any]) -> bool:
        """
        Check if a dependency is unhealthy.

        Args:
            dependency: Dependency dictionary

        Returns:
            True if unhealthy
        """
        # Check for health indicators (would integrate with monitoring in production)
        # For now, use risk score and known issues
        risk_score = dependency.get("risk_score", 0)
        return risk_score > 70

    def _is_dependency_spof(self, dependency_id: str) -> bool:
        """
        Check if a dependency is a single point of failure.

        Args:
            dependency_id: Dependency resource ID

        Returns:
            True if SPOF
        """
        return self.dependency_analyzer.is_single_point_of_failure(dependency_id)

    def _calculate_dependency_health_score(
        self,
        total_deps: int,
        unhealthy: list[CategorizedResource],
        spofs: list[CategorizedResource],
        high_risk: list[CategorizedResource],
    ) -> float:
        """
        Calculate overall dependency health score.

        Args:
            total_deps: Total number of dependencies
            unhealthy: Unhealthy dependencies
            spofs: SPOF dependencies
            high_risk: High risk dependencies

        Returns:
            Health score (0-100)
        """
        if total_deps == 0:
            return 100.0

        # Start with perfect score
        score = 100.0

        # Deduct for unhealthy dependencies
        score -= (len(unhealthy) / total_deps) * 30

        # Deduct for SPOFs (more severe)
        score -= (len(spofs) / total_deps) * 40

        # Deduct for high risk
        score -= (len(high_risk) / total_deps) * 20

        return max(0.0, score)

    def _generate_user_facing_impact(
        self, affected_by_category: dict[ResourceCategory, list[CategorizedResource]]
    ) -> str:
        """Generate user-facing impact summary."""
        user_facing = affected_by_category.get(ResourceCategory.USER_FACING, [])

        if not user_facing:
            return "No direct user-facing services affected"

        critical_count = sum(1 for r in user_facing if r.is_critical)
        if critical_count > 0:
            return f"{len(user_facing)} user-facing services affected ({critical_count} critical): Users will experience service outages or severe degradation"
        else:
            return f"{len(user_facing)} user-facing services affected: Users may experience degraded performance"

    def _generate_backend_impact(
        self, affected_by_category: dict[ResourceCategory, list[CategorizedResource]]
    ) -> str:
        """Generate backend service impact summary."""
        backend = affected_by_category.get(ResourceCategory.BACKEND_SERVICE, [])

        if not backend:
            return "No backend services affected"

        return f"{len(backend)} backend services affected: Internal service functionality will be impaired"

    def _generate_data_impact(
        self, affected_by_category: dict[ResourceCategory, list[CategorizedResource]]
    ) -> str:
        """Generate data access impact summary."""
        data_stores = affected_by_category.get(ResourceCategory.DATA_STORE, [])

        if not data_stores:
            return "No data stores directly affected"

        critical_count = sum(1 for r in data_stores if r.is_critical)
        if critical_count > 0:
            return f"{len(data_stores)} data stores affected ({critical_count} critical): Data access will be blocked"
        else:
            return f"{len(data_stores)} data stores affected: Some data access may be impaired"

    def _generate_business_impact(
        self, total_affected: int, critical_services: list, client_apps: list
    ) -> str:
        """Generate high-level business impact summary."""
        if total_affected == 0:
            return "Minimal business impact - no dependent services"

        impacts = []

        if critical_services:
            impacts.append(f"{len(critical_services)} critical services will fail")

        if client_apps:
            impacts.append(f"{len(client_apps)} client applications will be impacted")

        if not impacts:
            impacts.append(f"{total_affected} services will be affected")

        return "; ".join(impacts)

    def _estimate_users_affected(
        self, affected_by_category: dict[ResourceCategory, list[CategorizedResource]]
    ) -> int:
        """
        Estimate number of users affected.

        This is a simplified estimate based on affected service types.
        In production, this would integrate with actual user metrics.
        """
        user_facing = affected_by_category.get(ResourceCategory.USER_FACING, [])
        client_apps = affected_by_category.get(ResourceCategory.CLIENT_APP, [])

        # Simple heuristic: estimate users per service
        base_users_per_service = 1000
        estimated_users = len(user_facing) * base_users_per_service
        estimated_users += len(client_apps) * (base_users_per_service // 2)

        return estimated_users

    def _generate_dependency_recommendations(
        self,
        unhealthy: list[CategorizedResource],
        spofs: list[CategorizedResource],
        high_risk: list[CategorizedResource],
    ) -> list[str]:
        """Generate recommendations for improving dependency health."""
        recommendations = []

        if spofs:
            recommendations.append(
                f"⚠️ {len(spofs)} single point(s) of failure detected in dependencies. "
                "Add redundancy or failover capabilities."
            )

        if unhealthy:
            recommendations.append(
                f"🔧 {len(unhealthy)} unhealthy dependencies detected. "
                "Review and remediate issues in dependent services."
            )

        if high_risk:
            recommendations.append(
                f"📊 {len(high_risk)} high-risk dependencies detected. "
                "Consider alternatives or add circuit breakers."
            )

        if not recommendations:
            recommendations.append("✅ All dependencies appear healthy")

        return recommendations

    def _determine_scenario_severity(
        self, downstream: DownstreamImpactAnalysis, upstream: UpstreamDependencyHealth
    ) -> ImpactLevel:
        """Determine overall scenario severity."""
        # Check downstream impact
        if downstream.critical_services_affected:
            return ImpactLevel.SEVERE
        elif downstream.total_affected > 10:
            return ImpactLevel.HIGH
        elif downstream.total_affected > 5:
            return ImpactLevel.MEDIUM
        elif downstream.total_affected > 0:
            return ImpactLevel.LOW
        else:
            return ImpactLevel.MINIMAL

    def _estimate_impact_timeline(
        self, downstream: DownstreamImpactAnalysis, scenario_type: str
    ) -> int:
        """Estimate timeline for impact in minutes."""
        if scenario_type == "failure":
            # Immediate impact
            return 0
        elif scenario_type == "maintenance":
            # Planned, can schedule
            return 60
        elif scenario_type == "update":
            # Rolling update, gradual impact
            return 30
        else:
            return 15

    def _generate_mitigation_steps(
        self,
        downstream: DownstreamImpactAnalysis,
        upstream: UpstreamDependencyHealth,
        scenario_type: str,
    ) -> tuple[bool, list[str]]:
        """Generate mitigation steps for the scenario."""
        steps = []

        if downstream.critical_services_affected:
            steps.append("Enable maintenance mode for affected critical services")
            steps.append("Notify stakeholders and users of planned impact")

        if downstream.total_affected > 0:
            steps.append("Scale up redundant instances before making changes")
            steps.append("Enable circuit breakers to prevent cascade failures")

        if upstream.single_points_of_failure:
            steps.append("Verify backup systems for SPOF dependencies are ready")

        if scenario_type == "update":
            steps.append("Perform rolling update to minimize impact")
            steps.append("Have rollback plan ready")

        return (len(steps) > 0, steps)

    def _generate_rollback_steps(
        self, scenario_type: str, downstream: DownstreamImpactAnalysis
    ) -> tuple[bool, list[str]]:
        """Generate rollback steps if possible."""
        if scenario_type in ["failure", "maintenance"]:
            # Can't rollback a failure or maintenance
            return (False, [])

        steps = [
            "Stop deployment/update process",
            "Revert to previous version",
            "Verify all services are back online",
        ]

        if downstream.total_affected > 0:
            steps.append("Monitor affected services for stability")
            steps.append("Notify stakeholders that rollback is complete")

        return (True, steps)
