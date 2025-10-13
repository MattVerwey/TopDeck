"""
Data models for risk analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(str, Enum):
    """Risk level classification."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImpactLevel(str, Enum):
    """Impact level classification."""
    
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe"


@dataclass
class RiskAssessment:
    """
    Complete risk assessment for a resource.
    
    Attributes:
        resource_id: Unique identifier of the resource
        resource_name: Human-readable name
        resource_type: Type of resource (e.g., 'database', 'web_app')
        risk_score: Numeric risk score (0-100)
        risk_level: Categorical risk level
        criticality_score: How critical this resource is (0-100)
        dependencies_count: Number of resources this depends on
        dependents_count: Number of resources depending on this
        blast_radius: Number of resources affected if this fails
        single_point_of_failure: Whether this is a SPOF
        deployment_failure_rate: Historical failure rate (0-1)
        time_since_last_change: Hours since last change
        recommendations: List of recommended actions
        factors: Detailed breakdown of risk factors
        assessed_at: When this assessment was performed
    """
    
    resource_id: str
    resource_name: str
    resource_type: str
    risk_score: float
    risk_level: RiskLevel
    criticality_score: float
    dependencies_count: int
    dependents_count: int
    blast_radius: int
    single_point_of_failure: bool
    deployment_failure_rate: float = 0.0
    time_since_last_change: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)
    factors: Dict[str, Any] = field(default_factory=dict)
    assessed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BlastRadius:
    """
    Analysis of what would be affected if a resource fails.
    
    Attributes:
        resource_id: ID of the failing resource
        resource_name: Name of the failing resource
        directly_affected: Resources with direct dependency
        indirectly_affected: Resources affected via cascade
        total_affected: Total number of affected resources
        user_impact: Estimated impact on users
        estimated_downtime_seconds: Estimated recovery time
        critical_path: Most critical dependency path
        affected_services: Breakdown by service type
    """
    
    resource_id: str
    resource_name: str
    directly_affected: List[Dict[str, Any]]
    indirectly_affected: List[Dict[str, Any]]
    total_affected: int
    user_impact: ImpactLevel
    estimated_downtime_seconds: int
    critical_path: List[str] = field(default_factory=list)
    affected_services: Dict[str, int] = field(default_factory=dict)


@dataclass
class FailureSimulation:
    """
    Results of a failure simulation.
    
    Attributes:
        resource_id: ID of the simulated failure
        resource_name: Name of the resource
        scenario: Description of the failure scenario
        blast_radius: Blast radius analysis
        cascade_depth: How many levels the failure cascades
        recovery_steps: Recommended recovery steps
        mitigation_strategies: Ways to reduce impact
        similar_past_incidents: Historical similar incidents
    """
    
    resource_id: str
    resource_name: str
    scenario: str
    blast_radius: BlastRadius
    cascade_depth: int
    recovery_steps: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    similar_past_incidents: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SinglePointOfFailure:
    """
    Represents a single point of failure in the infrastructure.
    
    Attributes:
        resource_id: ID of the SPOF
        resource_name: Name of the SPOF
        resource_type: Type of resource
        dependents_count: Number of resources depending on this
        blast_radius: Number affected if this fails
        risk_score: Risk score for this SPOF
        recommendations: How to eliminate this SPOF
    """
    
    resource_id: str
    resource_name: str
    resource_type: str
    dependents_count: int
    blast_radius: int
    risk_score: float
    recommendations: List[str] = field(default_factory=list)
