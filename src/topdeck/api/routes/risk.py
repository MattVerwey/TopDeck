"""
Risk Analysis API endpoints.

Provides API endpoints for risk assessment, blast radius calculation,
failure simulation, and single point of failure detection.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from topdeck.analysis.risk import (
    RiskAnalyzer,
)
from topdeck.common.config import settings
from topdeck.storage.neo4j_client import Neo4jClient


# Pydantic models for API responses
class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment."""

    resource_id: str
    resource_name: str
    resource_type: str
    risk_score: float
    risk_level: str
    criticality_score: float
    dependencies_count: int
    dependents_count: int
    blast_radius: int
    single_point_of_failure: bool
    deployment_failure_rate: float
    time_since_last_change: float | None
    recommendations: list[str]
    factors: dict
    assessed_at: str


class BlastRadiusResponse(BaseModel):
    """Response model for blast radius."""

    resource_id: str
    resource_name: str
    directly_affected: list[dict]
    indirectly_affected: list[dict]
    total_affected: int
    user_impact: str
    estimated_downtime_seconds: int
    critical_path: list[str]
    affected_services: dict


class FailureSimulationResponse(BaseModel):
    """Response model for failure simulation."""

    resource_id: str
    resource_name: str
    scenario: str
    blast_radius: BlastRadiusResponse
    cascade_depth: int
    recovery_steps: list[str]
    mitigation_strategies: list[str]
    similar_past_incidents: list[dict]


class SinglePointOfFailureResponse(BaseModel):
    """Response model for single point of failure."""

    resource_id: str
    resource_name: str
    resource_type: str
    dependents_count: int
    blast_radius: int
    risk_score: float
    recommendations: list[str]


class FailureOutcomeResponse(BaseModel):
    """Response model for failure outcome."""

    outcome_type: str
    probability: float
    duration_seconds: int
    affected_percentage: float
    user_impact_description: str
    technical_details: str


class PartialFailureScenarioResponse(BaseModel):
    """Response model for partial failure scenario."""

    resource_id: str
    resource_name: str
    failure_type: str
    outcomes: list[FailureOutcomeResponse]
    overall_impact: str
    mitigation_strategies: list[str]
    monitoring_recommendations: list[str]


class DependencyVulnerabilityResponse(BaseModel):
    """Response model for dependency vulnerability."""

    package_name: str
    current_version: str
    vulnerability_id: str
    severity: str
    description: str
    fixed_version: str | None = None
    exploit_available: bool = False
    affected_resources: list[str]


class ComprehensiveRiskAnalysisResponse(BaseModel):
    """Response model for comprehensive risk analysis."""

    resource_id: str
    combined_risk_score: float
    standard_assessment: RiskAssessmentResponse
    degraded_performance_scenario: PartialFailureScenarioResponse
    intermittent_failure_scenario: PartialFailureScenarioResponse
    dependency_vulnerabilities: list[DependencyVulnerabilityResponse]
    vulnerability_risk_score: float
    all_recommendations: list[str]


# Create router
router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


def get_risk_analyzer() -> RiskAnalyzer:
    """Get risk analyzer instance."""
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
    )
    neo4j_client.connect()
    return RiskAnalyzer(neo4j_client)


@router.get("/resources/{resource_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(resource_id: str) -> RiskAssessmentResponse:
    """
    Get complete risk assessment for a resource.

    Analyzes dependencies, calculates risk score, identifies single points
    of failure, and provides recommendations.
    """
    try:
        analyzer = get_risk_analyzer()
        assessment = analyzer.analyze_resource(resource_id)

        return RiskAssessmentResponse(
            resource_id=assessment.resource_id,
            resource_name=assessment.resource_name,
            resource_type=assessment.resource_type,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            criticality_score=assessment.criticality_score,
            dependencies_count=assessment.dependencies_count,
            dependents_count=assessment.dependents_count,
            blast_radius=assessment.blast_radius,
            single_point_of_failure=assessment.single_point_of_failure,
            deployment_failure_rate=assessment.deployment_failure_rate,
            time_since_last_change=assessment.time_since_last_change,
            recommendations=assessment.recommendations,
            factors=assessment.factors,
            assessed_at=assessment.assessed_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze resource: {str(e)}") from e


@router.get("/blast-radius/{resource_id}", response_model=BlastRadiusResponse)
async def get_blast_radius(resource_id: str) -> BlastRadiusResponse:
    """
    Calculate blast radius for a resource failure.

    Shows what would be affected if this resource fails, including
    direct and cascading impacts.
    """
    try:
        analyzer = get_risk_analyzer()
        blast_radius = analyzer.calculate_blast_radius(resource_id)

        return BlastRadiusResponse(
            resource_id=blast_radius.resource_id,
            resource_name=blast_radius.resource_name,
            directly_affected=blast_radius.directly_affected,
            indirectly_affected=blast_radius.indirectly_affected,
            total_affected=blast_radius.total_affected,
            user_impact=blast_radius.user_impact.value,
            estimated_downtime_seconds=blast_radius.estimated_downtime_seconds,
            critical_path=blast_radius.critical_path,
            affected_services=blast_radius.affected_services,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate blast radius: {str(e)}"
        ) from e


@router.post("/simulate", response_model=FailureSimulationResponse)
async def simulate_failure(
    resource_id: str = Query(..., description="Resource ID to simulate failure for"),
    scenario: str = Query("Complete service outage", description="Failure scenario description"),
) -> FailureSimulationResponse:
    """
    Simulate a failure scenario.

    Predicts the impact of a resource failure, provides recovery steps,
    and suggests mitigation strategies.
    """
    try:
        analyzer = get_risk_analyzer()
        simulation = analyzer.simulate_failure(resource_id, scenario)

        return FailureSimulationResponse(
            resource_id=simulation.resource_id,
            resource_name=simulation.resource_name,
            scenario=simulation.scenario,
            blast_radius=BlastRadiusResponse(
                resource_id=simulation.blast_radius.resource_id,
                resource_name=simulation.blast_radius.resource_name,
                directly_affected=simulation.blast_radius.directly_affected,
                indirectly_affected=simulation.blast_radius.indirectly_affected,
                total_affected=simulation.blast_radius.total_affected,
                user_impact=simulation.blast_radius.user_impact.value,
                estimated_downtime_seconds=simulation.blast_radius.estimated_downtime_seconds,
                critical_path=simulation.blast_radius.critical_path,
                affected_services=simulation.blast_radius.affected_services,
            ),
            cascade_depth=simulation.cascade_depth,
            recovery_steps=simulation.recovery_steps,
            mitigation_strategies=simulation.mitigation_strategies,
            similar_past_incidents=simulation.similar_past_incidents,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to simulate failure: {str(e)}") from e


@router.get("/spof", response_model=list[SinglePointOfFailureResponse])
async def get_single_points_of_failure() -> list[SinglePointOfFailureResponse]:
    """
    Identify all single points of failure.

    Returns resources that have dependents but no redundancy,
    making them critical risks.
    """
    try:
        analyzer = get_risk_analyzer()
        spofs = analyzer.identify_single_points_of_failure()

        return [
            SinglePointOfFailureResponse(
                resource_id=spof.resource_id,
                resource_name=spof.resource_name,
                resource_type=spof.resource_type,
                dependents_count=spof.dependents_count,
                blast_radius=spof.blast_radius,
                risk_score=spof.risk_score,
                recommendations=spof.recommendations,
            )
            for spof in spofs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to identify SPOFs: {str(e)}") from e


@router.get("/resources/{resource_id}/score", response_model=dict)
async def get_change_risk_score(resource_id: str) -> dict:
    """
    Get risk score for deploying changes to a resource.

    Returns a simple risk score (0-100) without full assessment.
    Useful for quick checks in CI/CD pipelines.
    """
    try:
        analyzer = get_risk_analyzer()
        score = analyzer.get_change_risk_score(resource_id)
        risk_level = analyzer.risk_scorer.get_risk_level(score)

        return {
            "resource_id": resource_id,
            "risk_score": score,
            "risk_level": risk_level.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get risk score: {str(e)}") from e


@router.get(
    "/resources/{resource_id}/degraded-performance", response_model=PartialFailureScenarioResponse
)
async def analyze_degraded_performance(
    resource_id: str,
    current_load: float = Query(0.7, ge=0.0, le=1.0, description="Current load factor (0-1)"),
) -> PartialFailureScenarioResponse:
    """
    Analyze degraded performance scenario for a resource.

    This provides realistic analysis of what happens when a resource is under
    stress but not completely failed. More common in production than total outages.

    Args:
        resource_id: Resource to analyze
        current_load: Current load percentage (0-1, default 0.7)

    Returns:
        Partial failure scenario with multiple possible outcomes
    """
    try:
        analyzer = get_risk_analyzer()
        scenario = analyzer.analyze_degraded_performance(resource_id, current_load)

        return PartialFailureScenarioResponse(
            resource_id=scenario.resource_id,
            resource_name=scenario.resource_name,
            failure_type=scenario.failure_type.value,
            outcomes=[
                FailureOutcomeResponse(
                    outcome_type=o.outcome_type.value,
                    probability=o.probability,
                    duration_seconds=o.duration_seconds,
                    affected_percentage=o.affected_percentage,
                    user_impact_description=o.user_impact_description,
                    technical_details=o.technical_details,
                )
                for o in scenario.outcomes
            ],
            overall_impact=scenario.overall_impact.value,
            mitigation_strategies=scenario.mitigation_strategies,
            monitoring_recommendations=scenario.monitoring_recommendations,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze degraded performance: {str(e)}"
        ) from e


@router.get(
    "/resources/{resource_id}/intermittent-failure", response_model=PartialFailureScenarioResponse
)
async def analyze_intermittent_failure(
    resource_id: str,
    failure_frequency: float = Query(
        0.05, ge=0.0, le=1.0, description="Percentage of requests that fail (0-1)"
    ),
) -> PartialFailureScenarioResponse:
    """
    Analyze intermittent failure scenario (service blips).

    Analyzes what happens when a service has occasional errors rather than
    complete failure. Common in distributed systems.

    Args:
        resource_id: Resource to analyze
        failure_frequency: Percentage of requests that fail (0-1, default 0.05)

    Returns:
        Partial failure scenario with blip/error rate outcomes
    """
    try:
        analyzer = get_risk_analyzer()
        scenario = analyzer.analyze_intermittent_failure(resource_id, failure_frequency)

        return PartialFailureScenarioResponse(
            resource_id=scenario.resource_id,
            resource_name=scenario.resource_name,
            failure_type=scenario.failure_type.value,
            outcomes=[
                FailureOutcomeResponse(
                    outcome_type=o.outcome_type.value,
                    probability=o.probability,
                    duration_seconds=o.duration_seconds,
                    affected_percentage=o.affected_percentage,
                    user_impact_description=o.user_impact_description,
                    technical_details=o.technical_details,
                )
                for o in scenario.outcomes
            ],
            overall_impact=scenario.overall_impact.value,
            mitigation_strategies=scenario.mitigation_strategies,
            monitoring_recommendations=scenario.monitoring_recommendations,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze intermittent failure: {str(e)}"
        ) from e


@router.get(
    "/resources/{resource_id}/partial-outage", response_model=PartialFailureScenarioResponse
)
async def analyze_partial_outage(
    resource_id: str,
    affected_zones: str | None = Query(None, description="Comma-separated list of affected zones"),
) -> PartialFailureScenarioResponse:
    """
    Analyze partial outage scenario (some instances/zones down).

    Analyzes impact when only some availability zones or instances fail,
    rather than complete service outage.

    Args:
        resource_id: Resource to analyze
        affected_zones: Comma-separated list of affected zones (e.g., "zone-a,zone-b")

    Returns:
        Partial failure scenario with zone-specific outcomes
    """
    try:
        analyzer = get_risk_analyzer()
        zones_list = affected_zones.split(",") if affected_zones else None
        scenario = analyzer.analyze_partial_outage(resource_id, zones_list)

        return PartialFailureScenarioResponse(
            resource_id=scenario.resource_id,
            resource_name=scenario.resource_name,
            failure_type=scenario.failure_type.value,
            outcomes=[
                FailureOutcomeResponse(
                    outcome_type=o.outcome_type.value,
                    probability=o.probability,
                    duration_seconds=o.duration_seconds,
                    affected_percentage=o.affected_percentage,
                    user_impact_description=o.user_impact_description,
                    technical_details=o.technical_details,
                )
                for o in scenario.outcomes
            ],
            overall_impact=scenario.overall_impact.value,
            mitigation_strategies=scenario.mitigation_strategies,
            monitoring_recommendations=scenario.monitoring_recommendations,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze partial outage: {str(e)}"
        ) from e


@router.get(
    "/resources/{resource_id}/comprehensive", response_model=ComprehensiveRiskAnalysisResponse
)
async def get_comprehensive_risk_analysis(
    resource_id: str,
    project_path: str | None = Query(None, description="Path to project for dependency scanning"),
    current_load: float = Query(0.7, ge=0.0, le=1.0, description="Current load factor (0-1)"),
) -> ComprehensiveRiskAnalysisResponse:
    """
    Get comprehensive risk analysis including all failure scenarios.

    This is the most in-depth analysis available, covering:
    - Standard risk assessment (SPOF, blast radius, etc.)
    - Degraded performance scenario
    - Intermittent failure scenario
    - Dependency vulnerabilities (if project_path provided)

    Args:
        resource_id: Resource to analyze
        project_path: Optional path to project directory for dependency scanning
        current_load: Current load factor (0-1)

    Returns:
        Comprehensive risk analysis with all scenarios and combined risk score
    """
    try:
        analyzer = get_risk_analyzer()
        analysis = analyzer.get_comprehensive_risk_analysis(resource_id, project_path, current_load)

        return ComprehensiveRiskAnalysisResponse(
            resource_id=analysis["resource_id"],
            combined_risk_score=analysis["combined_risk_score"],
            standard_assessment=RiskAssessmentResponse(
                resource_id=analysis["standard_assessment"].resource_id,
                resource_name=analysis["standard_assessment"].resource_name,
                resource_type=analysis["standard_assessment"].resource_type,
                risk_score=analysis["standard_assessment"].risk_score,
                risk_level=analysis["standard_assessment"].risk_level.value,
                criticality_score=analysis["standard_assessment"].criticality_score,
                dependencies_count=analysis["standard_assessment"].dependencies_count,
                dependents_count=analysis["standard_assessment"].dependents_count,
                blast_radius=analysis["standard_assessment"].blast_radius,
                single_point_of_failure=analysis["standard_assessment"].single_point_of_failure,
                deployment_failure_rate=analysis["standard_assessment"].deployment_failure_rate,
                time_since_last_change=analysis["standard_assessment"].time_since_last_change,
                recommendations=analysis["standard_assessment"].recommendations,
                factors=analysis["standard_assessment"].factors,
                assessed_at=analysis["standard_assessment"].assessed_at.isoformat(),
            ),
            degraded_performance_scenario=PartialFailureScenarioResponse(
                resource_id=analysis["degraded_performance_scenario"].resource_id,
                resource_name=analysis["degraded_performance_scenario"].resource_name,
                failure_type=analysis["degraded_performance_scenario"].failure_type.value,
                outcomes=[
                    FailureOutcomeResponse(
                        outcome_type=o.outcome_type.value,
                        probability=o.probability,
                        duration_seconds=o.duration_seconds,
                        affected_percentage=o.affected_percentage,
                        user_impact_description=o.user_impact_description,
                        technical_details=o.technical_details,
                    )
                    for o in analysis["degraded_performance_scenario"].outcomes
                ],
                overall_impact=analysis["degraded_performance_scenario"].overall_impact.value,
                mitigation_strategies=analysis[
                    "degraded_performance_scenario"
                ].mitigation_strategies,
                monitoring_recommendations=analysis[
                    "degraded_performance_scenario"
                ].monitoring_recommendations,
            ),
            intermittent_failure_scenario=PartialFailureScenarioResponse(
                resource_id=analysis["intermittent_failure_scenario"].resource_id,
                resource_name=analysis["intermittent_failure_scenario"].resource_name,
                failure_type=analysis["intermittent_failure_scenario"].failure_type.value,
                outcomes=[
                    FailureOutcomeResponse(
                        outcome_type=o.outcome_type.value,
                        probability=o.probability,
                        duration_seconds=o.duration_seconds,
                        affected_percentage=o.affected_percentage,
                        user_impact_description=o.user_impact_description,
                        technical_details=o.technical_details,
                    )
                    for o in analysis["intermittent_failure_scenario"].outcomes
                ],
                overall_impact=analysis["intermittent_failure_scenario"].overall_impact.value,
                mitigation_strategies=analysis[
                    "intermittent_failure_scenario"
                ].mitigation_strategies,
                monitoring_recommendations=analysis[
                    "intermittent_failure_scenario"
                ].monitoring_recommendations,
            ),
            dependency_vulnerabilities=[
                DependencyVulnerabilityResponse(
                    package_name=v.package_name,
                    current_version=v.current_version,
                    vulnerability_id=v.vulnerability_id,
                    severity=v.severity,
                    description=v.description,
                    fixed_version=v.fixed_version,
                    exploit_available=v.exploit_available,
                    affected_resources=v.affected_resources,
                )
                for v in analysis["dependency_vulnerabilities"]
            ],
            vulnerability_risk_score=analysis["vulnerability_risk_score"],
            all_recommendations=analysis["all_recommendations"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get comprehensive risk analysis: {str(e)}"
        ) from e


@router.get("/dependencies/circular")
async def detect_circular_dependencies(
    resource_id: str | None = Query(None, description="Specific resource to check, or all if omitted")
) -> dict:
    """
    Detect circular dependencies in infrastructure.

    Circular dependencies can cause cascading failures and deployment deadlocks.
    This endpoint finds all cycles in the dependency graph.

    Args:
        resource_id: Optional resource ID to check. If omitted, checks entire graph.

    Returns:
        Dictionary with detected circular dependency paths
    """
    try:
        analyzer = get_risk_analyzer()
        cycles = analyzer.dependency_analyzer.detect_circular_dependencies(resource_id)

        return {
            "resource_id": resource_id,
            "circular_dependencies_found": len(cycles),
            "cycles": cycles,
            "severity": "critical" if len(cycles) > 0 else "none",
            "recommendations": [
                "Break circular dependencies by introducing event-driven architecture",
                "Use dependency injection to decouple components",
                "Consider using mediator pattern to manage complex interactions",
                "Refactor to establish clear dependency hierarchy"
            ] if cycles else ["No circular dependencies detected - dependency graph is healthy"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to detect circular dependencies: {str(e)}"
        ) from e


@router.get("/dependencies/{resource_id}/health")
async def get_dependency_health(resource_id: str) -> dict:
    """
    Get health score for a resource's dependencies.

    Analyzes dependency quality considering:
    - Number of dependencies (coupling)
    - Circular dependencies
    - Single points of failure in dependency chain
    - Depth of dependency tree

    Args:
        resource_id: Resource to analyze

    Returns:
        Dictionary with health score (0-100) and recommendations
    """
    try:
        analyzer = get_risk_analyzer()
        health_data = analyzer.dependency_analyzer.get_dependency_health_score(resource_id)
        return health_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate dependency health: {str(e)}"
        ) from e


@router.get("/compare")
async def compare_risk_scores(
    resource_ids: str = Query(..., description="Comma-separated list of resource IDs")
) -> dict:
    """
    Compare risk scores across multiple resources.

    Useful for:
    - Prioritizing which resources need attention
    - Comparing similar resources (e.g., multiple database instances)
    - Identifying patterns in high-risk resources

    Args:
        resource_ids: Comma-separated resource IDs (e.g., "id1,id2,id3")

    Returns:
        Dictionary with comparison analysis and insights
    """
    try:
        ids = [rid.strip() for rid in resource_ids.split(",") if rid.strip()]
        if not ids:
            raise HTTPException(status_code=400, detail="At least one resource ID required")

        analyzer = get_risk_analyzer()
        comparison = analyzer.compare_risk_scores(ids)
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compare risk scores: {str(e)}"
        ) from e


@router.get("/cascading-failure/{resource_id}")
async def analyze_cascading_failure(
    resource_id: str,
    initial_probability: float = Query(
        1.0, ge=0.0, le=1.0, description="Initial failure probability (0-1)"
    )
) -> dict:
    """
    Calculate cascading failure probability.

    Models how a failure propagates through dependencies with
    decreasing probability at each level (accounting for circuit
    breakers, retries, and fallbacks).

    Args:
        resource_id: Starting resource
        initial_probability: Probability of initial failure (0-1)

    Returns:
        Dictionary with cascading failure analysis
    """
    try:
        analyzer = get_risk_analyzer()
        analysis = analyzer.calculate_cascading_failure_probability(
            resource_id, initial_probability
        )
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze cascading failure: {str(e)}"
        ) from e
