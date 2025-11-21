"""
Risk Analysis API endpoints.

Provides API endpoints for risk assessment, blast radius calculation,
failure simulation, and single point of failure detection.
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from topdeck.analysis.risk import (
    RiskAnalyzer,
)
from topdeck.common.config import settings
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


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
    misconfigurations: list[dict]
    misconfiguration_count: int
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


class CategorizedResourceResponse(BaseModel):
    """Response model for categorized resource."""

    resource_id: str
    resource_name: str
    resource_type: str
    category: str
    relationship_type: str
    impact_severity: str
    is_critical: bool


class DownstreamImpactResponse(BaseModel):
    """Response model for downstream impact analysis."""

    resource_id: str
    resource_name: str
    total_affected: int
    affected_by_category: dict[str, list[CategorizedResourceResponse]]
    critical_services_affected: list[CategorizedResourceResponse]
    client_apps_affected: list[CategorizedResourceResponse]
    user_facing_impact: str
    backend_impact: str
    data_impact: str
    estimated_users_affected: int
    business_impact_summary: str


class UpstreamDependencyHealthResponse(BaseModel):
    """Response model for upstream dependency health."""

    resource_id: str
    resource_name: str
    total_dependencies: int
    dependencies_by_category: dict[str, list[CategorizedResourceResponse]]
    unhealthy_dependencies: list[CategorizedResourceResponse]
    single_points_of_failure: list[CategorizedResourceResponse]
    high_risk_dependencies: list[CategorizedResourceResponse]
    dependency_health_score: float
    recommendations: list[str]


class WhatIfAnalysisResponse(BaseModel):
    """Response model for what-if analysis."""

    resource_id: str
    resource_name: str
    scenario_type: str
    downstream_impact: DownstreamImpactResponse
    upstream_dependencies: UpstreamDependencyHealthResponse
    timeline_minutes: int
    severity: str
    mitigation_available: bool
    mitigation_steps: list[str]
    rollback_possible: bool
    rollback_steps: list[str]


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


@router.get("/all", response_model=list[RiskAssessmentResponse])
async def get_all_risk_assessments() -> list[RiskAssessmentResponse]:
    """
    Get risk assessments for all resources.
    
    Returns a list of risk assessments for all resources in the infrastructure.
    """
    try:
        analyzer = get_risk_analyzer()
        # Get all resources from Neo4j
        query = """
        MATCH (r:Resource)
        RETURN r.id as id
        """
        
        assessments = []
        with analyzer.neo4j_client.session() as session:
            result = session.run(query)
            for record in result:
                resource_id = record["id"]
                try:
                    assessment = analyzer.analyze_resource(resource_id)
                    assessments.append(RiskAssessmentResponse(
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
                        misconfigurations=assessment.misconfigurations,
                        misconfiguration_count=assessment.misconfiguration_count,
                        assessed_at=assessment.assessed_at.isoformat(),
                    ))
                except Exception as e:
                    # Skip resources that fail to analyze
                    logger.warning(f"Failed to analyze resource {resource_id}: {str(e)}")
                    continue
        
        return assessments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get all risk assessments: {str(e)}") from e


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
            misconfigurations=assessment.misconfigurations,
            misconfiguration_count=assessment.misconfiguration_count,
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
    resource_id: str | None = Query(
        None, description="Specific resource to check, or all if omitted"
    )
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
            "recommendations": (
                [
                    "Break circular dependencies by introducing event-driven architecture",
                    "Use dependency injection to decouple components",
                    "Consider using mediator pattern to manage complex interactions",
                    "Refactor to establish clear dependency hierarchy",
                ]
                if cycles
                else ["No circular dependencies detected - dependency graph is healthy"]
            ),
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

        # Limit to 50 resources to prevent performance issues
        if len(ids) > 50:
            raise HTTPException(
                status_code=400, detail=f"Too many resources requested ({len(ids)}). Maximum is 50."
            )

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
    ),
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


@router.get("/resources/{resource_id}/time-aware-risk")
async def get_time_aware_risk(
    resource_id: str,
    deployment_time: str | None = Query(None, description="ISO format deployment time (defaults to now)"),
) -> dict:
    """
    Get time-aware risk assessment for a deployment.

    Adjusts risk scores based on deployment timing - business hours,
    weekends, maintenance windows, etc.

    Args:
        resource_id: Resource to assess
        deployment_time: Planned deployment time in ISO format

    Returns:
        Risk assessment with time-based adjustments
    """
    try:
        from datetime import datetime
        from topdeck.analysis.risk import TimeAwareRiskScorer, adjust_risk_score_for_timing

        analyzer = get_risk_analyzer()
        base_assessment = analyzer.analyze_resource(resource_id)

        # Parse deployment time if provided
        dt = None
        if deployment_time:
            dt = datetime.fromisoformat(deployment_time.replace('Z', '+00:00'))

        # Get time-aware risk adjustment
        time_aware_scorer = TimeAwareRiskScorer()
        adjusted_risk = adjust_risk_score_for_timing(
            base_assessment.risk_score,
            dt,
            time_aware_scorer
        )

        # Get optimal deployment windows
        optimal_windows = time_aware_scorer.suggest_optimal_deployment_window(dt, days_ahead=7)

        return {
            "resource_id": resource_id,
            "resource_name": base_assessment.resource_name,
            "base_risk_score": base_assessment.risk_score,
            "adjusted_risk_score": adjusted_risk["adjusted_risk_score"],
            "time_multiplier": adjusted_risk["time_multiplier"],
            "timing_factors": adjusted_risk["timing_factors"],
            "recommendation": adjusted_risk["recommendation"],
            "day_type": adjusted_risk["day_type"],
            "time_window": adjusted_risk["time_window"],
            "optimal_deployment_windows": optimal_windows,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate time-aware risk: {str(e)}"
        ) from e


@router.get("/resources/{resource_id}/cost-impact")
async def get_cost_impact(
    resource_id: str,
    downtime_hours: float = Query(1.0, ge=0.1, description="Expected downtime in hours"),
    affected_users: int = Query(1000, ge=0, description="Number of affected users"),
    is_revenue_generating: bool = Query(True, description="Whether resource generates revenue"),
    has_sla: bool = Query(False, description="Whether SLA penalties apply"),
    industry: str = Query("default", description="Industry type for cost multipliers"),
    annual_revenue: float | None = Query(None, ge=0, description="Annual revenue for SLA calculations"),
) -> dict:
    """
    Estimate financial impact of a resource failure.

    Calculates costs including revenue loss, engineering time, support costs,
    SLA penalties, and reputation damage.

    Args:
        resource_id: Resource to analyze
        downtime_hours: Expected downtime duration
        affected_users: Number of users affected
        is_revenue_generating: Whether resource directly generates revenue
        has_sla: Whether SLA penalties apply
        industry: Industry type (ecommerce, fintech, saas, healthcare, gaming, media, enterprise, default)
        annual_revenue: Annual revenue for SLA penalty calculations

    Returns:
        Cost impact analysis with detailed breakdown
    """
    try:
        from topdeck.analysis.risk import CostImpactAnalyzer

        analyzer = get_risk_analyzer()
        resource = analyzer._get_resource_details(resource_id)

        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        cost_analyzer = CostImpactAnalyzer(
            industry=industry,
            annual_revenue=annual_revenue,
        )

        cost_impact = cost_analyzer.calculate_cost_impact(
            resource_id=resource_id,
            resource_name=resource["name"],
            resource_type=resource["resource_type"],
            downtime_hours=downtime_hours,
            affected_users=affected_users,
            is_revenue_generating=is_revenue_generating,
            has_sla=has_sla,
        )

        # Calculate annual risk cost
        # Assume 1% failure probability per year for example
        annual_risk = cost_analyzer.estimate_annual_risk_cost(
            hourly_impact_rate=cost_impact.hourly_impact_rate,
            failure_probability_per_year=0.01,
            mean_time_to_recovery_hours=downtime_hours,
        )

        return {
            "resource_id": cost_impact.resource_id,
            "resource_name": cost_impact.resource_name,
            "total_cost": cost_impact.total_cost,
            "cost_breakdown": cost_impact.cost_breakdown,
            "hourly_impact_rate": cost_impact.hourly_impact_rate,
            "affected_users": cost_impact.affected_users,
            "confidence_level": cost_impact.confidence_level,
            "assumptions": cost_impact.assumptions,
            "annual_risk_cost": annual_risk,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate cost impact: {str(e)}"
        ) from e


@router.post("/resources/{resource_id}/trend-snapshot")
async def add_risk_snapshot(
    resource_id: str,
) -> dict:
    """
    Create a risk snapshot for trend analysis.

    Captures current risk state for tracking changes over time.

    Args:
        resource_id: Resource to snapshot

    Returns:
        Snapshot details
    """
    try:
        from datetime import datetime, timezone
        from topdeck.analysis.risk import RiskSnapshot

        analyzer = get_risk_analyzer()
        assessment = analyzer.analyze_resource(resource_id)

        snapshot = RiskSnapshot(
            timestamp=datetime.now(timezone.utc),
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            factors=assessment.factors,
        )

        return {
            "resource_id": resource_id,
            "snapshot": {
                "timestamp": snapshot.timestamp.isoformat(),
                "risk_score": snapshot.risk_score,
                "risk_level": snapshot.risk_level,
                "factors": snapshot.factors,
            },
            "message": "Snapshot created successfully. Store this for trend analysis.",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create snapshot: {str(e)}"
        ) from e


class SnapshotRequest(BaseModel):
    """Request model for trend analysis."""

    snapshots: list[dict]


@router.post("/resources/{resource_id}/analyze-trend")
async def analyze_risk_trend(
    resource_id: str,
    request: SnapshotRequest,
) -> dict:
    """
    Analyze risk trend from historical snapshots.

    Identifies whether risk is improving, degrading, stable, or volatile.

    Args:
        resource_id: Resource to analyze
        request: Request containing list of historical risk snapshots

    Returns:
        Trend analysis with recommendations
    """
    try:
        from datetime import datetime
        from topdeck.analysis.risk import RiskSnapshot, RiskTrendAnalyzer

        analyzer = get_risk_analyzer()
        resource = analyzer._get_resource_details(resource_id)

        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        # Convert dict snapshots to RiskSnapshot objects
        snapshot_objects = [
            RiskSnapshot(
                timestamp=datetime.fromisoformat(s["timestamp"].replace('Z', '+00:00')),
                risk_score=s["risk_score"],
                risk_level=s["risk_level"],
                factors=s.get("factors", {}),
            )
            for s in request.snapshots
        ]

        trend_analyzer = RiskTrendAnalyzer()
        trend = trend_analyzer.analyze_trend(
            resource_id=resource_id,
            resource_name=resource["name"],
            snapshots=snapshot_objects,
        )

        # Detect anomalies
        anomalies = trend_analyzer.detect_anomalies(snapshot_objects)

        # Predict future risk
        prediction = trend_analyzer.predict_future_risk(snapshot_objects, days_ahead=7)

        return {
            "resource_id": trend.resource_id,
            "resource_name": trend.resource_name,
            "current_risk_score": trend.current_risk_score,
            "previous_risk_score": trend.previous_risk_score,
            "trend_direction": trend.trend_direction.value,
            "trend_severity": trend.trend_severity.value,
            "change_percentage": trend.change_percentage,
            "contributing_factors": trend.contributing_factors,
            "recommendations": trend.recommendations,
            "anomalies": anomalies,
            "prediction": prediction,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze trend: {str(e)}"
        ) from e


@router.get("/resources/{resource_id}/downstream-impact", response_model=DownstreamImpactResponse)
async def get_downstream_impact(resource_id: str) -> DownstreamImpactResponse:
    """
    Analyze what services and clients will be affected if this resource fails.

    This endpoint answers: "What will be brought down if this fails?"

    Returns:
        - Breakdown of affected resources by category (user-facing, backend, data, etc.)
        - Critical services that will fail
        - Client applications that will be impacted
        - User-facing impact summary
        - Business impact summary
    """
    try:
        analyzer = get_risk_analyzer()
        impact = analyzer.analyze_downstream_impact(resource_id)

        # Convert categorized resources to response format
        def convert_categorized_resources(resources: list) -> list[CategorizedResourceResponse]:
            return [
                CategorizedResourceResponse(
                    resource_id=r.resource_id,
                    resource_name=r.resource_name,
                    resource_type=r.resource_type,
                    category=r.category.value,
                    relationship_type=r.relationship_type,
                    impact_severity=r.impact_severity.value,
                    is_critical=r.is_critical,
                )
                for r in resources
            ]

        # Convert affected_by_category dict
        affected_by_category_response = {}
        for category, resources in impact.affected_by_category.items():
            affected_by_category_response[category.value] = convert_categorized_resources(resources)

        return DownstreamImpactResponse(
            resource_id=impact.resource_id,
            resource_name=impact.resource_name,
            total_affected=impact.total_affected,
            affected_by_category=affected_by_category_response,
            critical_services_affected=convert_categorized_resources(
                impact.critical_services_affected
            ),
            client_apps_affected=convert_categorized_resources(impact.client_apps_affected),
            user_facing_impact=impact.user_facing_impact,
            backend_impact=impact.backend_impact,
            data_impact=impact.data_impact,
            estimated_users_affected=impact.estimated_users_affected,
            business_impact_summary=impact.business_impact_summary,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze downstream impact: {str(e)}"
        ) from e


@router.get(
    "/resources/{resource_id}/upstream-dependencies", response_model=UpstreamDependencyHealthResponse
)
async def get_upstream_dependencies(resource_id: str) -> UpstreamDependencyHealthResponse:
    """
    Analyze what this resource depends on and the health of those dependencies.

    This endpoint answers: "What does this app depend on and what are the risks?"

    Returns:
        - Breakdown of dependencies by category
        - Unhealthy dependencies
        - Single points of failure in dependencies
        - High-risk dependencies
        - Overall dependency health score
        - Recommendations for improving dependency health
    """
    try:
        analyzer = get_risk_analyzer()
        health = analyzer.analyze_upstream_dependencies(resource_id)

        # Convert categorized resources to response format
        def convert_categorized_resources(resources: list) -> list[CategorizedResourceResponse]:
            return [
                CategorizedResourceResponse(
                    resource_id=r.resource_id,
                    resource_name=r.resource_name,
                    resource_type=r.resource_type,
                    category=r.category.value,
                    relationship_type=r.relationship_type,
                    impact_severity=r.impact_severity.value,
                    is_critical=r.is_critical,
                )
                for r in resources
            ]

        # Convert dependencies_by_category dict
        dependencies_by_category_response = {}
        for category, resources in health.dependencies_by_category.items():
            dependencies_by_category_response[category.value] = convert_categorized_resources(
                resources
            )

        return UpstreamDependencyHealthResponse(
            resource_id=health.resource_id,
            resource_name=health.resource_name,
            total_dependencies=health.total_dependencies,
            dependencies_by_category=dependencies_by_category_response,
            unhealthy_dependencies=convert_categorized_resources(health.unhealthy_dependencies),
            single_points_of_failure=convert_categorized_resources(
                health.single_points_of_failure
            ),
            high_risk_dependencies=convert_categorized_resources(health.high_risk_dependencies),
            dependency_health_score=health.dependency_health_score,
            recommendations=health.recommendations,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze upstream dependencies: {str(e)}"
        ) from e


@router.get("/resources/{resource_id}/what-if", response_model=WhatIfAnalysisResponse)
async def get_what_if_analysis(
    resource_id: str,
    scenario_type: str = Query(
        default="failure",
        description="Type of scenario to analyze (failure, maintenance, update, etc.)",
    ),
) -> WhatIfAnalysisResponse:
    """
    Comprehensive "what if" analysis for a resource.

    This endpoint answers: "What will happen if this resource fails or is changed?"

    Args:
        resource_id: ID of the resource to analyze
        scenario_type: Type of scenario (failure, maintenance, update, etc.)

    Returns:
        - Complete downstream impact analysis
        - Upstream dependency health analysis
        - Timeline for impact
        - Overall severity
        - Mitigation steps if available
        - Rollback steps if applicable
    """
    try:
        analyzer = get_risk_analyzer()
        analysis = analyzer.analyze_what_if_scenario(resource_id, scenario_type)

        # Convert categorized resources helper
        def convert_categorized_resources(resources: list) -> list[CategorizedResourceResponse]:
            return [
                CategorizedResourceResponse(
                    resource_id=r.resource_id,
                    resource_name=r.resource_name,
                    resource_type=r.resource_type,
                    category=r.category.value,
                    relationship_type=r.relationship_type,
                    impact_severity=r.impact_severity.value,
                    is_critical=r.is_critical,
                )
                for r in resources
            ]

        # Convert downstream impact
        downstream = analysis.downstream_impact
        affected_by_category_response = {}
        for category, resources in downstream.affected_by_category.items():
            affected_by_category_response[category.value] = convert_categorized_resources(resources)

        downstream_response = DownstreamImpactResponse(
            resource_id=downstream.resource_id,
            resource_name=downstream.resource_name,
            total_affected=downstream.total_affected,
            affected_by_category=affected_by_category_response,
            critical_services_affected=convert_categorized_resources(
                downstream.critical_services_affected
            ),
            client_apps_affected=convert_categorized_resources(downstream.client_apps_affected),
            user_facing_impact=downstream.user_facing_impact,
            backend_impact=downstream.backend_impact,
            data_impact=downstream.data_impact,
            estimated_users_affected=downstream.estimated_users_affected,
            business_impact_summary=downstream.business_impact_summary,
        )

        # Convert upstream dependencies
        upstream = analysis.upstream_dependencies
        dependencies_by_category_response = {}
        for category, resources in upstream.dependencies_by_category.items():
            dependencies_by_category_response[category.value] = convert_categorized_resources(
                resources
            )

        upstream_response = UpstreamDependencyHealthResponse(
            resource_id=upstream.resource_id,
            resource_name=upstream.resource_name,
            total_dependencies=upstream.total_dependencies,
            dependencies_by_category=dependencies_by_category_response,
            unhealthy_dependencies=convert_categorized_resources(upstream.unhealthy_dependencies),
            single_points_of_failure=convert_categorized_resources(
                upstream.single_points_of_failure
            ),
            high_risk_dependencies=convert_categorized_resources(upstream.high_risk_dependencies),
            dependency_health_score=upstream.dependency_health_score,
            recommendations=upstream.recommendations,
        )

        return WhatIfAnalysisResponse(
            resource_id=analysis.resource_id,
            resource_name=analysis.resource_name,
            scenario_type=analysis.scenario_type,
            downstream_impact=downstream_response,
            upstream_dependencies=upstream_response,
            timeline_minutes=analysis.timeline_minutes,
            severity=analysis.severity.value,
            mitigation_available=analysis.mitigation_available,
            mitigation_steps=analysis.mitigation_steps,
            rollback_possible=analysis.rollback_possible,
            rollback_steps=analysis.rollback_steps,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze what-if scenario: {str(e)}"
        ) from e
