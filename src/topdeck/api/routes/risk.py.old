"""
Risk Analysis API endpoints.

Provides API endpoints for risk assessment and change impact analysis.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from topdeck.storage.neo4j_client import Neo4jClient
from topdeck.common.config import settings


# Pydantic models for API responses
class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment."""
    
    resource_id: str
    risk_score: float
    criticality: str
    dependencies_count: int
    dependents_count: int
    blast_radius: int
    single_point_of_failure: bool
    recommendations: List[str] = Field(default_factory=list)


class ChangeImpactRequest(BaseModel):
    """Request model for change impact analysis."""
    
    service_id: str
    change_type: str


class ChangeImpactResponse(BaseModel):
    """Response model for change impact analysis."""
    
    service_id: str
    affected_services: List[str] = Field(default_factory=list)
    performance_degradation: float
    estimated_downtime: float
    user_impact: str
    recommendations: List[str] = Field(default_factory=list)


# Create router
router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client instance."""
    client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
    )
    client.connect()
    return client


def calculate_risk_score(dependencies_count: int, dependents_count: int) -> float:
    """Calculate risk score based on dependencies."""
    # Simple risk score calculation
    # More dependencies and dependents = higher risk
    base_score = min((dependencies_count + dependents_count) * 10, 100)
    return base_score / 100.0


def get_criticality(risk_score: float, dependents_count: int) -> str:
    """Determine criticality level."""
    if dependents_count > 10 or risk_score > 0.8:
        return "critical"
    elif dependents_count > 5 or risk_score > 0.6:
        return "high"
    elif risk_score > 0.3:
        return "medium"
    else:
        return "low"


@router.get("/resources/{resource_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(resource_id: str) -> RiskAssessmentResponse:
    """
    Get risk assessment for a specific resource.
    
    Returns risk score, criticality, dependencies, and recommendations.
    """
    try:
        client = get_neo4j_client()
        
        try:
            # Get resource dependencies
            query = """
            MATCH (r:Resource {id: $resource_id})
            OPTIONAL MATCH (r)-[:DEPENDS_ON]->(upstream)
            OPTIONAL MATCH (downstream)-[:DEPENDS_ON]->(r)
            RETURN r, 
                   count(DISTINCT upstream) as dependencies_count,
                   count(DISTINCT downstream) as dependents_count
            """
            
            with client.session() as session:
                result = session.run(query, {"resource_id": resource_id})
                record = result.single()
                
                if not record:
                    raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
                
                dependencies_count = record["dependencies_count"]
                dependents_count = record["dependents_count"]
            
            # Calculate risk metrics
            risk_score = calculate_risk_score(dependencies_count, dependents_count)
            criticality = get_criticality(risk_score, dependents_count)
            
            # Estimate blast radius (simplified)
            blast_radius = dependents_count
            
            # Check if single point of failure
            single_point_of_failure = dependents_count > 5
            
            # Generate recommendations
            recommendations = []
            if single_point_of_failure:
                recommendations.append("Consider adding redundancy for this resource")
            if dependencies_count > 5:
                recommendations.append("High number of dependencies - review and simplify if possible")
            if criticality in ["high", "critical"]:
                recommendations.append("Implement monitoring and alerting")
                recommendations.append("Document recovery procedures")
            
            return RiskAssessmentResponse(
                resource_id=resource_id,
                risk_score=risk_score,
                criticality=criticality,
                dependencies_count=dependencies_count,
                dependents_count=dependents_count,
                blast_radius=blast_radius,
                single_point_of_failure=single_point_of_failure,
                recommendations=recommendations,
            )
            
        finally:
            client.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get risk assessment: {str(e)}"
        )


@router.get("/all", response_model=List[RiskAssessmentResponse])
async def get_all_risks() -> List[RiskAssessmentResponse]:
    """
    Get risk assessments for all resources.
    
    Returns a list of risk assessments for all resources in the system.
    """
    try:
        client = get_neo4j_client()
        
        try:
            # Get all resources with their dependencies
            query = """
            MATCH (r:Resource)
            OPTIONAL MATCH (r)-[:DEPENDS_ON]->(upstream)
            OPTIONAL MATCH (downstream)-[:DEPENDS_ON]->(r)
            RETURN r.id as resource_id,
                   count(DISTINCT upstream) as dependencies_count,
                   count(DISTINCT downstream) as dependents_count
            """
            
            with client.session() as session:
                result = session.run(query)
                results = list(result)
            
                risk_assessments = []
                for record in results:
                    resource_id = record["resource_id"]
                    dependencies_count = record["dependencies_count"]
                    dependents_count = record["dependents_count"]
                
                # Calculate risk metrics
                risk_score = calculate_risk_score(dependencies_count, dependents_count)
                criticality = get_criticality(risk_score, dependents_count)
                blast_radius = dependents_count
                single_point_of_failure = dependents_count > 5
                
                # Generate recommendations
                recommendations = []
                if single_point_of_failure:
                    recommendations.append("Consider adding redundancy for this resource")
                if criticality in ["high", "critical"]:
                    recommendations.append("Implement monitoring and alerting")
                
                    risk_assessments.append(RiskAssessmentResponse(
                        resource_id=resource_id,
                        risk_score=risk_score,
                        criticality=criticality,
                        dependencies_count=dependencies_count,
                        dependents_count=dependents_count,
                        blast_radius=blast_radius,
                        single_point_of_failure=single_point_of_failure,
                        recommendations=recommendations,
                    ))
                
                return risk_assessments
            
        finally:
            client.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get risk assessments: {str(e)}"
        )


@router.post("/impact", response_model=ChangeImpactResponse)
async def get_change_impact(request: ChangeImpactRequest = Body(...)) -> ChangeImpactResponse:
    """
    Analyze the impact of a change to a service.
    
    Returns affected services, performance impact, and recommendations.
    """
    try:
        client = get_neo4j_client()
        
        try:
            # Get all downstream dependencies (affected services)
            query = """
            MATCH path = (r:Resource {id: $service_id})<-[:DEPENDS_ON*]-(affected)
            RETURN DISTINCT affected.id as affected_id
            """
            
            with client.session() as session:
                result = session.run(query, {"service_id": request.service_id})
                results = list(result)
                
                affected_services = [record["affected_id"] for record in results]
                affected_count = len(affected_services)
                
                # Estimate impact based on change type and affected services
                if request.change_type.lower() in ["update", "patch"]:
                    performance_degradation = min(affected_count * 5, 30)
                    estimated_downtime = min(affected_count * 2, 15)
                elif request.change_type.lower() in ["deploy", "deployment"]:
                    performance_degradation = min(affected_count * 10, 50)
                    estimated_downtime = min(affected_count * 5, 30)
                elif request.change_type.lower() in ["restart", "reboot"]:
                    performance_degradation = min(affected_count * 15, 70)
                    estimated_downtime = min(affected_count * 3, 20)
                else:
                    performance_degradation = min(affected_count * 8, 40)
                    estimated_downtime = min(affected_count * 3, 20)
                
                # Determine user impact
                if affected_count > 10:
                    user_impact = "high"
                elif affected_count > 5:
                    user_impact = "medium"
                else:
                    user_impact = "low"
                
                # Generate recommendations
                recommendations = []
                if user_impact == "high":
                    recommendations.append("Schedule change during maintenance window")
                    recommendations.append("Notify users in advance")
                    recommendations.append("Have rollback plan ready")
                elif user_impact == "medium":
                    recommendations.append("Monitor affected services closely")
                    recommendations.append("Have rollback plan ready")
                else:
                    recommendations.append("Standard change procedures apply")
                
                if estimated_downtime > 10:
                    recommendations.append("Consider implementing blue-green deployment")
                
                return ChangeImpactResponse(
                    service_id=request.service_id,
                    affected_services=affected_services,
                    performance_degradation=performance_degradation,
                    estimated_downtime=estimated_downtime,
                    user_impact=user_impact,
                    recommendations=recommendations,
                )
            
        finally:
            client.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze change impact: {str(e)}"
        )
