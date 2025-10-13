"""
Risk Analysis API endpoints.

Provides API endpoints for risk assessment, blast radius calculation,
failure simulation, and single point of failure detection.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.analysis.risk import (
    RiskAnalyzer,
    RiskAssessment,
    BlastRadius,
    FailureSimulation,
    SinglePointOfFailure,
    RiskLevel,
    ImpactLevel,
)
from topdeck.storage.neo4j_client import Neo4jClient
from topdeck.common.config import settings


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
    time_since_last_change: Optional[float]
    recommendations: List[str]
    factors: dict
    assessed_at: str


class BlastRadiusResponse(BaseModel):
    """Response model for blast radius."""
    
    resource_id: str
    resource_name: str
    directly_affected: List[dict]
    indirectly_affected: List[dict]
    total_affected: int
    user_impact: str
    estimated_downtime_seconds: int
    critical_path: List[str]
    affected_services: dict


class FailureSimulationResponse(BaseModel):
    """Response model for failure simulation."""
    
    resource_id: str
    resource_name: str
    scenario: str
    blast_radius: BlastRadiusResponse
    cascade_depth: int
    recovery_steps: List[str]
    mitigation_strategies: List[str]
    similar_past_incidents: List[dict]


class SinglePointOfFailureResponse(BaseModel):
    """Response model for single point of failure."""
    
    resource_id: str
    resource_name: str
    resource_type: str
    dependents_count: int
    blast_radius: int
    risk_score: float
    recommendations: List[str]


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
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze resource: {str(e)}"
        )


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
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate blast radius: {str(e)}"
        )


@router.post("/simulate", response_model=FailureSimulationResponse)
async def simulate_failure(
    resource_id: str = Query(..., description="Resource ID to simulate failure for"),
    scenario: str = Query(
        "Complete service outage",
        description="Failure scenario description"
    )
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
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to simulate failure: {str(e)}"
        )


@router.get("/spof", response_model=List[SinglePointOfFailureResponse])
async def get_single_points_of_failure() -> List[SinglePointOfFailureResponse]:
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to identify SPOFs: {str(e)}"
        )


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
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get risk score: {str(e)}"
        )
