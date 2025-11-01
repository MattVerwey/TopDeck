"""
Change Management Service.

Provides business logic for change requests, impact assessment,
and integration with external change management systems.
"""

from datetime import datetime, timedelta, timezone
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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
                risk_assessment = self.risk_analyzer.assess_resource_risk(res_id)
                
                # Add to directly affected
                directly_affected.append({
                    "resource_id": res_id,
                    "name": risk_assessment.resource_name,
                    "type": risk_assessment.resource_type,
                    "risk_score": risk_assessment.risk_score,
                    "blast_radius": risk_assessment.blast_radius,
                })
                
                total_risk_score += risk_assessment.risk_score
                
                # Check if single point of failure
                if risk_assessment.single_point_of_failure:
                    critical_path = True
                
                # Get dependencies (indirectly affected)
                dependents = self._get_resource_dependents(res_id)
                for dep in dependents:
                    if dep["id"] not in [d["resource_id"] for d in indirectly_affected]:
                        indirectly_affected.append({
                            "resource_id": dep["id"],
                            "name": dep.get("name", "Unknown"),
                            "type": dep.get("resource_type", "Unknown"),
                        })
                
                # Estimate downtime based on change type
                estimated_downtime = self._estimate_downtime(change_request.change_type)
                max_downtime = max(max_downtime, estimated_downtime)
                
            except Exception as e:
                # Resource not found or error - log and continue with others
                import logging
                logging.warning(f"Failed to assess resource {res_id}: {e}")
                continue

        # Calculate overall metrics
        total_affected = len(directly_affected) + len(indirectly_affected)
        avg_risk_score = total_risk_score / len(directly_affected) if directly_affected else 0.0
        
        # Determine user impact level
        user_impact = self._determine_user_impact(
            total_affected, avg_risk_score, critical_path
        )
        
        # Determine recommended window
        recommended_window = self._determine_recommended_window(
            change_request.change_type, avg_risk_score, critical_path
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            change_request, total_affected, avg_risk_score, critical_path
        )

        # Create assessment
        assessment = ChangeImpactAssessment(
            change_id=change_request.id,
            directly_affected_resources=directly_affected,
            indirectly_affected_resources=indirectly_affected,
            total_affected_count=total_affected,
            overall_risk_score=avg_risk_score,
            performance_degradation_pct=self._estimate_performance_impact(avg_risk_score),
            estimated_downtime_seconds=max_downtime,
            user_impact_level=user_impact,
            critical_path_affected=critical_path,
            recommended_window=recommended_window,
            rollback_plan_required=avg_risk_score > 60 or critical_path,
            approval_required=avg_risk_score > 70 or critical_path,
            breakdown={
                "direct_dependents": len(directly_affected),
                "indirect_dependents": len(indirectly_affected),
                "critical_path": critical_path,
            },
            recommendations=recommendations,
            assessed_at=datetime.now(timezone.utc),
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
            start_date = datetime.utcnow()
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
                changes.append({
                    "id": change_node["id"],
                    "title": change_node["title"],
                    "change_type": change_node["change_type"],
                    "status": change_node["status"],
                    "risk_level": change_node["risk_level"],
                    "scheduled_start": change_node["scheduled_start"],
                    "scheduled_end": change_node["scheduled_end"],
                    "requester": change_node.get("requester"),
                })
        
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
                scheduled_start=change_request.scheduled_start.isoformat()
                if change_request.scheduled_start
                else None,
                scheduled_end=change_request.scheduled_end.isoformat()
                if change_request.scheduled_end
                else None,
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

    def _estimate_downtime(self, change_type: ChangeType) -> int:
        """Estimate downtime in seconds based on change type"""
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
        """Estimate performance degradation percentage"""
        # Simple linear mapping: risk_score 0-100 -> 0-25% degradation
        return min(25.0, risk_score * 0.25)

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
