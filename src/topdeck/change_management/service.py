"""
Change Management Service.

Provides business logic for change requests, impact assessment,
and integration with external change management systems.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from topdeck.analysis.risk import RiskAnalyzer
from topdeck.change_management.models import (
    ChangeImpactAssessment,
    ChangeRequest,
    ChangeStatus,
    ChangeType,
)
from topdeck.storage.neo4j_client import Neo4jClient

# Constants for downtime estimation
MIN_DOWNTIME_SECONDS = 30  # Minimum estimated downtime (30 seconds)
MAX_DOWNTIME_SECONDS = 14400  # Maximum estimated downtime (4 hours)
DEPENDENCY_IMPACT_THRESHOLD = 5  # Number of dependencies that adds 10% to downtime
DEPENDENCY_IMPACT_PERCENTAGE = 0.1  # Percentage increase per threshold


class ChangeManagementService:
    """Service for managing change requests and impact assessments"""

    def __init__(self, neo4j_client: Neo4jClient) -> None:
        """Initialize change management service"""
        self.neo4j_client = neo4j_client
        self.risk_analyzer = RiskAnalyzer(neo4j_client)

    def create_change_request(
        self,
        title: str,
        description: str,
        change_type: ChangeType,
        affected_resources: list[str] | None = None,
        scheduled_start: datetime | None = None,
        scheduled_end: datetime | None = None,
        requester: str | None = None,
        external_system: str | None = None,
        external_id: str | None = None,
    ) -> ChangeRequest:
        """Create a new change request"""
        change_id = str(uuid4())

        change_request = ChangeRequest(
            id=change_id,
            title=title,
            description=description,
            change_type=change_type,
            status=ChangeStatus.DRAFT,
            requester=requester,
            affected_resources=affected_resources or [],
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            external_system=external_system,
            external_id=external_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Store in Neo4j
        self._store_change_request(change_request)

        return change_request

    def assess_change_impact(
        self, change_request: ChangeRequest, resource_id: str | None = None
    ) -> ChangeImpactAssessment:
        """
        Assess the impact of a change request.

        Args:
            change_request: The change request to assess
            resource_id: Optional specific resource ID to analyze

        Returns:
            ChangeImpactAssessment with detailed impact analysis
        """
        # If resource_id is provided, analyze that resource
        # Otherwise, analyze all affected resources in the change request
        if resource_id:
            target_resources = [resource_id]
        else:
            target_resources = change_request.affected_resources

        # Collect impact data
        directly_affected = []
        indirectly_affected = []
        total_risk_score = 0.0
        max_downtime = 0
        critical_path = False

        for res_id in target_resources:
            try:
                # Get risk assessment for this resource
                risk_assessment = self.risk_analyzer.analyze_resource(res_id)

                # Add to directly affected with misconfiguration details
                directly_affected.append(
                    {
                        "resource_id": res_id,
                        "name": risk_assessment.resource_name,
                        "type": risk_assessment.resource_type,
                        "risk_score": risk_assessment.risk_score,
                        "blast_radius": risk_assessment.blast_radius,
                        "misconfigurations": risk_assessment.misconfigurations,
                        "misconfiguration_count": risk_assessment.misconfiguration_count,
                    }
                )

                total_risk_score += risk_assessment.risk_score

                # Check if single point of failure
                if risk_assessment.single_point_of_failure:
                    critical_path = True

                # Get dependencies (indirectly affected)
                dependents = self._get_resource_dependents(res_id)
                for dep in dependents:
                    if dep["id"] not in [d["resource_id"] for d in indirectly_affected]:
                        indirectly_affected.append(
                            {
                                "resource_id": dep["id"],
                                "name": dep.get("name", "Unknown"),
                                "type": dep.get("resource_type", "Unknown"),
                            }
                        )

                # Estimate downtime based on change type AND resource characteristics
                estimated_downtime = self._estimate_downtime_for_resource(
                    change_request.change_type,
                    risk_assessment.resource_type,
                    risk_assessment.risk_score,
                    len(dependents),
                    risk_assessment.single_point_of_failure,
                )
                max_downtime = max(max_downtime, estimated_downtime)

            except Exception as e:
                # Resource not found or error - log and continue with others
                import logging

                logging.warning(f"Failed to assess resource {res_id}: {e}")
                continue

        # Calculate overall metrics
        total_affected = len(directly_affected) + len(indirectly_affected)
        avg_risk_score = total_risk_score / len(directly_affected) if directly_affected else 0.0

        # Adjust risk score based on change type - some changes are inherently riskier
        change_type_risk_multiplier = self._get_change_type_risk_multiplier(change_request.change_type)
        adjusted_risk_score = min(100.0, avg_risk_score * change_type_risk_multiplier)

        # Determine user impact level
        user_impact = self._determine_user_impact(total_affected, adjusted_risk_score, critical_path)

        # Determine recommended window
        recommended_window = self._determine_recommended_window(
            change_request.change_type, adjusted_risk_score, critical_path
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            change_request, total_affected, adjusted_risk_score, critical_path
        )

        # Create assessment
        assessment = ChangeImpactAssessment(
            change_id=change_request.id,
            directly_affected_resources=directly_affected,
            indirectly_affected_resources=indirectly_affected,
            total_affected_count=total_affected,
            overall_risk_score=adjusted_risk_score,
            performance_degradation_pct=self._estimate_performance_impact(adjusted_risk_score),
            estimated_downtime_seconds=max_downtime,
            user_impact_level=user_impact,
            critical_path_affected=critical_path,
            recommended_window=recommended_window,
            rollback_plan_required=adjusted_risk_score > 60 or critical_path,
            approval_required=adjusted_risk_score > 70 or critical_path,
            breakdown={
                "direct_dependents": len(directly_affected),
                "indirect_dependents": len(indirectly_affected),
                "critical_path": critical_path,
            },
            recommendations=recommendations,
            assessed_at=datetime.now(UTC),
        )

        return assessment

    def get_change_calendar(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[dict[str, Any]]:
        """
        Get scheduled changes within a date range.

        Args:
            start_date: Start of date range (defaults to now)
            end_date: End of date range (defaults to 30 days from start)

        Returns:
            List of scheduled changes
        """
        if start_date is None:
            start_date = datetime.now(UTC)
        if end_date is None:
            end_date = start_date + timedelta(days=30)

        # Query Neo4j for scheduled changes
        query = """
        MATCH (c:ChangeRequest)
        WHERE c.scheduled_start >= $start_date
          AND c.scheduled_start <= $end_date
          AND c.status IN ['scheduled', 'approved', 'pending_approval']
        RETURN c
        ORDER BY c.scheduled_start
        """

        with self.neo4j_client.driver.session() as session:
            result = session.run(
                query,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            changes = []
            for record in result:
                change_node = record["c"]
                changes.append(
                    {
                        "id": change_node["id"],
                        "title": change_node["title"],
                        "change_type": change_node["change_type"],
                        "status": change_node["status"],
                        "risk_level": change_node["risk_level"],
                        "scheduled_start": change_node["scheduled_start"],
                        "scheduled_end": change_node["scheduled_end"],
                        "requester": change_node.get("requester"),
                    }
                )

        return changes

    def _store_change_request(self, change_request: ChangeRequest) -> None:
        """Store change request in Neo4j"""
        query = """
        CREATE (c:ChangeRequest {
            id: $id,
            title: $title,
            description: $description,
            change_type: $change_type,
            status: $status,
            risk_level: $risk_level,
            requester: $requester,
            assignee: $assignee,
            scheduled_start: $scheduled_start,
            scheduled_end: $scheduled_end,
            affected_services_count: $affected_services_count,
            estimated_downtime_seconds: $estimated_downtime_seconds,
            external_system: $external_system,
            external_id: $external_id,
            external_url: $external_url,
            created_at: $created_at,
            updated_at: $updated_at
        })
        """

        with self.neo4j_client.driver.session() as session:
            session.run(
                query,
                id=change_request.id,
                title=change_request.title,
                description=change_request.description,
                change_type=change_request.change_type.value,
                status=change_request.status.value,
                risk_level=change_request.risk_level.value,
                requester=change_request.requester,
                assignee=change_request.assignee,
                scheduled_start=(
                    change_request.scheduled_start.isoformat()
                    if change_request.scheduled_start
                    else None
                ),
                scheduled_end=(
                    change_request.scheduled_end.isoformat()
                    if change_request.scheduled_end
                    else None
                ),
                affected_services_count=change_request.affected_services_count,
                estimated_downtime_seconds=change_request.estimated_downtime_seconds,
                external_system=change_request.external_system,
                external_id=change_request.external_id,
                external_url=change_request.external_url,
                created_at=change_request.created_at.isoformat(),
                updated_at=change_request.updated_at.isoformat(),
            )

        # Create relationships to affected resources
        for resource_id in change_request.affected_resources:
            self._link_change_to_resource(change_request.id, resource_id)

    def _link_change_to_resource(self, change_id: str, resource_id: str) -> None:
        """Link a change request to an affected resource"""
        query = """
        MATCH (c:ChangeRequest {id: $change_id})
        MATCH (r:Resource {id: $resource_id})
        MERGE (c)-[:AFFECTS]->(r)
        """

        with self.neo4j_client.driver.session() as session:
            session.run(query, change_id=change_id, resource_id=resource_id)

    def _get_resource_dependents(self, resource_id: str) -> list[dict[str, Any]]:
        """Get resources that depend on the given resource"""
        query = """
        MATCH (r:Resource {id: $resource_id})<-[:DEPENDS_ON]-(dependent:Resource)
        RETURN dependent.id as id, dependent.name as name, dependent.resource_type as resource_type
        LIMIT 50
        """

        with self.neo4j_client.driver.session() as session:
            result = session.run(query, resource_id=resource_id)
            return [dict(record) for record in result]

    def _normalize_resource_type(self, resource_type: str) -> str:
        """
        Normalize resource type string for consistent lookups.

        Converts resource type to lowercase and replaces spaces with underscores.

        Args:
            resource_type: Raw resource type string

        Returns:
            Normalized resource type string
        """
        return resource_type.lower().replace(" ", "_")

    def _estimate_downtime(self, change_type: ChangeType) -> int:
        """Estimate downtime in seconds based on change type (legacy method for backward compatibility)"""
        downtime_map = {
            ChangeType.RESTART: 60,  # 1 minute
            ChangeType.CONFIGURATION: 120,  # 2 minutes
            ChangeType.SCALING: 180,  # 3 minutes
            ChangeType.PATCH: 300,  # 5 minutes
            ChangeType.UPDATE: 600,  # 10 minutes
            ChangeType.DEPLOYMENT: 900,  # 15 minutes
            ChangeType.INFRASTRUCTURE: 1800,  # 30 minutes
            ChangeType.EMERGENCY: 300,  # 5 minutes
        }
        return downtime_map.get(change_type, 300)

    def _estimate_downtime_for_resource(
        self,
        change_type: ChangeType,
        resource_type: str,
        risk_score: float,
        dependent_count: int,
        is_critical: bool,
    ) -> int:
        """
        Estimate downtime in seconds based on change type AND resource characteristics.

        This improved method considers:
        - Change type (deployment, restart, etc.)
        - Resource type (database, web_app, etc.)
        - Risk score of the resource
        - Number of dependent resources
        - Whether the resource is on the critical path

        Args:
            change_type: Type of change being made
            resource_type: Type of resource being changed
            risk_score: Risk score of the resource (0-100)
            dependent_count: Number of resources depending on this one
            is_critical: Whether resource is a single point of failure

        Returns:
            Estimated downtime in seconds
        """
        # Base downtime by change type
        base_downtime = self._estimate_downtime(change_type)

        # Resource type multipliers - different resources have different change complexity
        resource_multipliers = {
            # Data stores - require careful handling, backups, validation
            "database": 2.0,
            "sql_server": 2.0,
            "mysql_server": 2.0,
            "postgresql_server": 2.0,
            "cosmos_db": 1.8,
            "storage_account": 1.5,
            "redis_cache": 1.3,
            # Compute - moderate complexity
            "virtual_machine": 1.5,
            "vm": 1.5,
            "container_instance": 1.2,
            "kubernetes_cluster": 1.8,
            "aks_cluster": 1.8,
            # Application services - typically faster to change
            "app_service": 1.0,
            "web_app": 1.0,
            "function_app": 0.8,
            "logic_app": 0.7,
            # Networking - can be complex, affects many resources
            "virtual_network": 1.6,
            "subnet": 1.4,
            "network_security_group": 1.3,
            "load_balancer": 1.5,
            "application_gateway": 1.4,
            "api_gateway": 1.3,
            # Infrastructure - typically slower to change
            "resource_group": 1.7,
            "subscription": 2.0,
        }

        normalized_type = self._normalize_resource_type(resource_type)
        resource_multiplier = resource_multipliers.get(normalized_type, 1.0)

        # Risk score multiplier (higher risk = more careful, slower changes)
        # Risk scores: 0-100, map to multipliers 1.0-2.0
        risk_multiplier = 1.0 + (risk_score / 100.0)

        # Dependency multiplier (more dependents = more coordination needed)
        dependency_multiplier = (
            1.0 + (dependent_count / DEPENDENCY_IMPACT_THRESHOLD) * DEPENDENCY_IMPACT_PERCENTAGE
        )

        # Critical path multiplier (critical resources need extra care)
        critical_multiplier = 1.5 if is_critical else 1.0

        # Change type + resource type specific adjustments
        # Some combinations are particularly complex
        complexity_adjustments = {
            # Database changes are especially risky
            (ChangeType.UPDATE, "database"): 1.3,
            (ChangeType.PATCH, "database"): 1.2,
            (ChangeType.INFRASTRUCTURE, "database"): 1.4,
            # Infrastructure changes to critical networking
            (ChangeType.INFRASTRUCTURE, "virtual_network"): 1.3,
            (ChangeType.INFRASTRUCTURE, "load_balancer"): 1.2,
            # Kubernetes changes can be complex
            (ChangeType.DEPLOYMENT, "kubernetes_cluster"): 1.2,
            (ChangeType.SCALING, "kubernetes_cluster"): 0.8,  # K8s is good at scaling
            # Function apps scale quickly
            (ChangeType.SCALING, "function_app"): 0.7,
            (ChangeType.DEPLOYMENT, "function_app"): 0.8,
        }

        complexity_key = (change_type, normalized_type)
        complexity_multiplier = complexity_adjustments.get(complexity_key, 1.0)

        # Calculate final downtime
        estimated_downtime = (
            base_downtime
            * resource_multiplier
            * risk_multiplier
            * dependency_multiplier
            * critical_multiplier
            * complexity_multiplier
        )

        # Cap at reasonable bounds
        return max(MIN_DOWNTIME_SECONDS, min(int(estimated_downtime), MAX_DOWNTIME_SECONDS))

    def _get_change_type_risk_multiplier(self, change_type: ChangeType) -> float:
        """
        Get risk multiplier based on change type.

        Different change types have different inherent risk levels:
        - Emergency changes are rushed and higher risk
        - Infrastructure changes are complex and risky
        - Configuration changes can have wide-reaching effects
        - Restarts and scaling are typically lower risk

        Args:
            change_type: Type of change being made

        Returns:
            Risk multiplier (typically 0.8 to 1.5)
        """
        risk_multipliers = {
            ChangeType.EMERGENCY: 1.4,  # Higher risk due to time pressure
            ChangeType.INFRASTRUCTURE: 1.3,  # Complex, affects many resources
            ChangeType.UPDATE: 1.2,  # Version updates can have compatibility issues
            ChangeType.DEPLOYMENT: 1.1,  # New code always carries risk
            ChangeType.PATCH: 1.0,  # Standard risk
            ChangeType.CONFIGURATION: 1.1,  # Config can have unexpected impacts
            ChangeType.SCALING: 0.9,  # Usually well-tested, lower risk
            ChangeType.RESTART: 0.8,  # Lowest risk, well-understood operation
        }
        return risk_multipliers.get(change_type, 1.0)

    def _determine_user_impact(
        self, total_affected: int, risk_score: float, critical_path: bool
    ) -> str:
        """Determine user impact level"""
        if critical_path or risk_score > 80:
            return "high"
        elif total_affected > 10 or risk_score > 60:
            return "medium"
        else:
            return "low"

    def _determine_recommended_window(
        self, change_type: ChangeType, risk_score: float, critical_path: bool
    ) -> str:
        """Determine recommended maintenance window"""
        if change_type == ChangeType.EMERGENCY:
            return "emergency"
        elif critical_path or risk_score > 70:
            return "maintenance"
        else:
            return "standard"

    def _estimate_performance_impact(self, risk_score: float) -> float:
        """
        Estimate performance degradation percentage.

        Uses a non-linear curve to better reflect reality:
        - Low risk scores (0-40) -> minimal degradation (0-5%)
        - Medium risk scores (40-70) -> moderate degradation (5-15%)
        - High risk scores (70-100) -> significant degradation (15-30%)

        Args:
            risk_score: Adjusted risk score (0-100)

        Returns:
            Estimated performance degradation percentage
        """
        if risk_score < 40:
            # Low risk: minimal impact
            return risk_score * 0.125  # 0-5%
        elif risk_score < 70:
            # Medium risk: moderate impact
            # 5% + scaled impact from 5-15%
            return 5.0 + (risk_score - 40) * 0.333  # 5-15%
        else:
            # High risk: significant impact
            # 15% + scaled impact from 15-30%
            return 15.0 + (risk_score - 70) * 0.5  # 15-30%

    def _generate_recommendations(
        self,
        change_request: ChangeRequest,
        total_affected: int,
        risk_score: float,
        critical_path: bool,
    ) -> list[str]:
        """Generate recommendations for the change"""
        recommendations = []

        if critical_path:
            recommendations.append(
                "This change affects critical infrastructure. Ensure rollback plan is in place."
            )

        if risk_score > 70:
            recommendations.append(
                "High risk change. Recommend additional approval and testing before execution."
            )

        if total_affected > 15:
            recommendations.append(
                f"Large blast radius ({total_affected} resources). Consider breaking into smaller changes."
            )

        if change_request.change_type == ChangeType.EMERGENCY:
            recommendations.append(
                "Emergency change. Ensure all stakeholders are notified and post-change review is scheduled."
            )
        else:
            recommendations.append("Schedule during low-traffic maintenance window if possible.")

        recommendations.append("Monitor all affected services during and after the change.")

        return recommendations
