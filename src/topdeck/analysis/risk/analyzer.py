"""
Main risk analysis orchestrator.
"""

from typing import Any

from topdeck.storage.neo4j_client import Neo4jClient

from .dependency import DependencyAnalyzer
from .dependency_scanner import DependencyScanner
from .impact import ImpactAnalyzer
from .models import (
    BlastRadius,
    DependencyVulnerability,
    FailureSimulation,
    PartialFailureScenario,
    RiskAssessment,
    SinglePointOfFailure,
)
from .partial_failure import PartialFailureAnalyzer
from .scoring import RiskScorer
from .simulation import FailureSimulator


class RiskAnalyzer:
    """
    Main orchestrator for risk analysis operations.

    Coordinates dependency analysis, risk scoring, impact assessment,
    and failure simulation to provide comprehensive risk insights.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize risk analyzer.

        Args:
            neo4j_client: Neo4j client for graph database access
        """
        self.neo4j_client = neo4j_client

        # Initialize component analyzers
        self.dependency_analyzer = DependencyAnalyzer(neo4j_client)
        self.risk_scorer = RiskScorer()
        self.impact_analyzer = ImpactAnalyzer(self.dependency_analyzer)
        self.failure_simulator = FailureSimulator(self.impact_analyzer)
        self.partial_failure_analyzer = PartialFailureAnalyzer()
        self.dependency_scanner = DependencyScanner()

    def analyze_resource(self, resource_id: str) -> RiskAssessment:
        """
        Perform complete risk assessment for a resource.

        Args:
            resource_id: Resource to analyze

        Returns:
            RiskAssessment with complete analysis

        Raises:
            ValueError: If resource not found
        """
        # Get resource details
        resource = self._get_resource_details(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        # Get dependency counts
        dependencies_count, dependents_count = self.dependency_analyzer.get_dependency_counts(
            resource_id
        )

        # Check if SPOF
        is_spof = self.dependency_analyzer.is_single_point_of_failure(resource_id)

        # Calculate blast radius
        blast_radius = self.impact_analyzer.calculate_blast_radius(resource_id, resource["name"])

        # Check for redundancy
        has_redundancy = self._check_redundancy(resource_id)

        # Get deployment history (placeholder - would be from real data)
        deployment_failure_rate = 0.0  # Would be calculated from actual deployments
        time_since_last_change = None  # Would be from deployment tracking

        # Calculate risk score
        risk_score = self.risk_scorer.calculate_risk_score(
            dependency_count=dependencies_count,
            dependents_count=dependents_count,
            resource_type=resource["resource_type"],
            is_single_point_of_failure=is_spof,
            deployment_failure_rate=deployment_failure_rate,
            time_since_last_change_hours=time_since_last_change,
            has_redundancy=has_redundancy,
        )

        # Get risk level
        risk_level = self.risk_scorer.get_risk_level(risk_score)

        # Calculate criticality
        criticality_score = self.risk_scorer._calculate_criticality(
            resource["resource_type"], is_spof, dependents_count
        )

        # Generate recommendations
        recommendations = self.risk_scorer.generate_recommendations(
            risk_score=risk_score,
            is_spof=is_spof,
            has_redundancy=has_redundancy,
            dependents_count=dependents_count,
            deployment_failure_rate=deployment_failure_rate,
        )

        # Build factor breakdown
        factors = {
            "dependencies_count": dependencies_count,
            "dependents_count": dependents_count,
            "is_spof": is_spof,
            "has_redundancy": has_redundancy,
            "blast_radius_size": blast_radius.total_affected,
            "user_impact": blast_radius.user_impact.value,
            "deployment_failure_rate": deployment_failure_rate,
        }

        return RiskAssessment(
            resource_id=resource_id,
            resource_name=resource["name"],
            resource_type=resource["resource_type"],
            risk_score=risk_score,
            risk_level=risk_level,
            criticality_score=criticality_score,
            dependencies_count=dependencies_count,
            dependents_count=dependents_count,
            blast_radius=blast_radius.total_affected,
            single_point_of_failure=is_spof,
            deployment_failure_rate=deployment_failure_rate,
            time_since_last_change=time_since_last_change,
            recommendations=recommendations,
            factors=factors,
        )

    def calculate_blast_radius(self, resource_id: str) -> BlastRadius:
        """
        Calculate blast radius for a resource failure.

        Args:
            resource_id: Resource to analyze

        Returns:
            BlastRadius analysis

        Raises:
            ValueError: If resource not found
        """
        resource = self._get_resource_details(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        return self.impact_analyzer.calculate_blast_radius(resource_id, resource["name"])

    def simulate_failure(
        self, resource_id: str, scenario: str = "Complete service outage"
    ) -> FailureSimulation:
        """
        Simulate a failure scenario.

        Args:
            resource_id: Resource to simulate failure for
            scenario: Description of failure scenario

        Returns:
            FailureSimulation with complete analysis

        Raises:
            ValueError: If resource not found
        """
        resource = self._get_resource_details(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        return self.failure_simulator.simulate_failure(
            resource_id=resource_id,
            resource_name=resource["name"],
            resource_type=resource["resource_type"],
            scenario=scenario,
        )

    def identify_single_points_of_failure(self) -> list[SinglePointOfFailure]:
        """
        Find all single points of failure in the infrastructure.

        Returns:
            List of SinglePointOfFailure resources
        """
        query = """
        MATCH (r)
        WHERE r.id IS NOT NULL
        AND EXISTS {
            MATCH (r)<-[:DEPENDS_ON]-(dependent)
            WHERE dependent.id IS NOT NULL
        }
        AND NOT EXISTS {
            MATCH (r)-[:REDUNDANT_WITH]->(alt)
            WHERE alt.id IS NOT NULL
        }
        WITH r
        OPTIONAL MATCH (r)<-[:DEPENDS_ON]-(dependent)
        WHERE dependent.id IS NOT NULL
        WITH r, COUNT(DISTINCT dependent) as dependents_count
        WHERE dependents_count > 0
        RETURN r.id as id,
               r.name as name,
               COALESCE(r.resource_type, labels(r)[0]) as resource_type,
               dependents_count
        ORDER BY dependents_count DESC
        """

        spofs = []
        with self.neo4j_client.session() as session:
            result = session.run(query)
            for record in result:
                resource_id = record["id"]

                # Get blast radius for this SPOF
                blast_radius = self.calculate_blast_radius(resource_id)

                # Calculate risk score
                risk_score = self.risk_scorer.calculate_risk_score(
                    dependency_count=0,  # Don't need for SPOF scoring
                    dependents_count=record["dependents_count"],
                    resource_type=record["resource_type"],
                    is_single_point_of_failure=True,
                    has_redundancy=False,
                )

                # Generate recommendations
                recommendations = [
                    "⚠️ This is a Single Point of Failure",
                    "Add redundant instances across availability zones",
                    "Implement automatic failover mechanisms",
                    "Increase monitoring and alerting priority",
                ]

                spofs.append(
                    SinglePointOfFailure(
                        resource_id=resource_id,
                        resource_name=record["name"],
                        resource_type=record["resource_type"],
                        dependents_count=record["dependents_count"],
                        blast_radius=blast_radius.total_affected,
                        risk_score=risk_score,
                        recommendations=recommendations,
                    )
                )

        return spofs

    def get_change_risk_score(self, resource_id: str) -> float:
        """
        Get risk score for changing/deploying to this resource.

        This is a convenience method that returns just the risk score
        without the full assessment.

        Args:
            resource_id: Resource to analyze

        Returns:
            Risk score (0-100)
        """
        assessment = self.analyze_resource(resource_id)
        return assessment.risk_score

    def _get_resource_details(self, resource_id: str) -> dict | None:
        """
        Get basic resource details from Neo4j.

        Args:
            resource_id: Resource ID

        Returns:
            Dictionary with resource details or None if not found
        """
        query = """
        MATCH (r {id: $id})
        RETURN r.id as id,
               r.name as name,
               COALESCE(r.resource_type, labels(r)[0]) as resource_type,
               r.cloud_provider as cloud_provider,
               r.region as region
        """

        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            record = result.single()
            if record:
                return {
                    "id": record["id"],
                    "name": record["name"],
                    "resource_type": record["resource_type"] or "unknown",
                    "cloud_provider": (
                        record["cloud_provider"]
                        if "cloud_provider" in record and record["cloud_provider"] is not None
                        else "azure"
                    ),
                    "region": (
                        record["region"]
                        if "region" in record and record["region"] is not None
                        else "unknown"
                    ),
                }

        return None

    def _check_redundancy(self, resource_id: str) -> bool:
        """
        Check if resource has redundant alternatives.

        Args:
            resource_id: Resource to check

        Returns:
            True if redundancy exists
        """
        query = """
        MATCH (r {id: $id})-[:REDUNDANT_WITH]->(alt)
        WHERE alt.id IS NOT NULL
        RETURN COUNT(alt) as redundant_count
        """

        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            record = result.single()
            if record:
                return record["redundant_count"] > 0

        return False

    def analyze_degraded_performance(
        self, resource_id: str, current_load: float = 0.7
    ) -> PartialFailureScenario:
        """
        Analyze degraded performance scenario.

        This provides more realistic failure analysis than complete outage.
        Most production issues are degradation, not total failure.

        Args:
            resource_id: Resource to analyze
            current_load: Current load percentage (0-1)

        Returns:
            PartialFailureScenario with degraded performance analysis

        Raises:
            ValueError: If resource not found
        """
        resource = self._get_resource_details(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        return self.partial_failure_analyzer.analyze_degraded_performance(
            resource_id=resource_id,
            resource_name=resource["name"],
            resource_type=resource["resource_type"],
            current_load=current_load,
        )

    def analyze_intermittent_failure(
        self, resource_id: str, failure_frequency: float = 0.05
    ) -> PartialFailureScenario:
        """
        Analyze intermittent failure scenario (service blips).

        Args:
            resource_id: Resource to analyze
            failure_frequency: Percentage of requests failing (0-1)

        Returns:
            PartialFailureScenario with intermittent failure analysis

        Raises:
            ValueError: If resource not found
        """
        resource = self._get_resource_details(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        return self.partial_failure_analyzer.analyze_intermittent_failure(
            resource_id=resource_id,
            resource_name=resource["name"],
            resource_type=resource["resource_type"],
            failure_frequency=failure_frequency,
        )

    def analyze_partial_outage(
        self, resource_id: str, affected_zones: list[str] = None
    ) -> PartialFailureScenario:
        """
        Analyze partial outage scenario.

        Args:
            resource_id: Resource to analyze
            affected_zones: List of affected availability zones

        Returns:
            PartialFailureScenario with partial outage analysis

        Raises:
            ValueError: If resource not found
        """
        resource = self._get_resource_details(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        return self.partial_failure_analyzer.analyze_partial_outage(
            resource_id=resource_id,
            resource_name=resource["name"],
            resource_type=resource["resource_type"],
            affected_zones=affected_zones,
        )

    def scan_dependency_vulnerabilities(
        self, project_path: str, resource_id: str = "unknown"
    ) -> list[DependencyVulnerability]:
        """
        Scan project dependencies for known vulnerabilities.

        Checks package dependencies (npm, pip, maven, etc.) for security issues.

        Args:
            project_path: Path to project root directory
            resource_id: ID of resource using these dependencies

        Returns:
            List of vulnerabilities found
        """
        return self.dependency_scanner.scan_all_dependencies(
            project_path=project_path,
            resource_id=resource_id,
        )

    def get_comprehensive_risk_analysis(
        self, resource_id: str, project_path: str | None = None, current_load: float = 0.7
    ) -> dict[str, Any]:
        """
        Get comprehensive risk analysis including all failure scenarios.

        This is the most in-depth analysis, covering:
        - Complete outage scenario
        - Degraded performance scenario
        - Intermittent failure scenario
        - Dependency vulnerabilities (if project_path provided)

        Args:
            resource_id: Resource to analyze
            project_path: Optional path to project for dependency scanning
            current_load: Current load factor (0-1)

        Returns:
            Dictionary with complete risk analysis

        Raises:
            ValueError: If resource not found
        """
        # Standard risk assessment
        risk_assessment = self.analyze_resource(resource_id)

        # Partial failure scenarios
        degraded_scenario = self.analyze_degraded_performance(resource_id, current_load)
        intermittent_scenario = self.analyze_intermittent_failure(
            resource_id, failure_frequency=0.05
        )

        # Dependency vulnerabilities
        vulnerabilities = []
        vuln_risk_score = 0.0
        if project_path:
            vulnerabilities = self.scan_dependency_vulnerabilities(project_path, resource_id)
            vuln_risk_score = self.dependency_scanner.get_vulnerability_risk_score(vulnerabilities)

        # Combined risk score (weighted average)
        combined_risk = (
            risk_assessment.risk_score * 0.5  # Infrastructure risk
            + vuln_risk_score * 0.3  # Dependency vulnerabilities
            + self._scenario_to_risk_score(degraded_scenario) * 0.2  # Degradation risk
        )

        return {
            "resource_id": resource_id,
            "combined_risk_score": combined_risk,
            "standard_assessment": risk_assessment,
            "degraded_performance_scenario": degraded_scenario,
            "intermittent_failure_scenario": intermittent_scenario,
            "dependency_vulnerabilities": vulnerabilities,
            "vulnerability_risk_score": vuln_risk_score,
            "all_recommendations": self._combine_recommendations(
                risk_assessment,
                degraded_scenario,
                intermittent_scenario,
                vulnerabilities,
            ),
        }

    def _scenario_to_risk_score(self, scenario: PartialFailureScenario) -> float:
        """Convert partial failure scenario to risk score."""
        impact_scores = {
            "minimal": 10,
            "low": 25,
            "medium": 50,
            "high": 75,
            "severe": 95,
        }
        return float(impact_scores.get(scenario.overall_impact.value, 50))

    def _combine_recommendations(
        self,
        assessment: RiskAssessment,
        degraded: PartialFailureScenario,
        intermittent: PartialFailureScenario,
        vulnerabilities: list[DependencyVulnerability],
    ) -> list[str]:
        """Combine and deduplicate recommendations."""
        all_recommendations = set()

        # Add from standard assessment
        all_recommendations.update(assessment.recommendations)

        # Add from degraded scenario
        all_recommendations.update(degraded.mitigation_strategies[:3])
        all_recommendations.update(degraded.monitoring_recommendations[:2])

        # Add from intermittent scenario
        all_recommendations.update(intermittent.mitigation_strategies[:3])

        # Add vulnerability recommendations
        if vulnerabilities:
            vuln_recs = self.dependency_scanner.generate_vulnerability_recommendations(
                vulnerabilities
            )
            all_recommendations.update(vuln_recs[:3])

        return sorted(all_recommendations)
