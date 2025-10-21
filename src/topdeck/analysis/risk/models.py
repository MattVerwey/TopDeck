"""
Data models for risk analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


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


class FailureType(str, Enum):
    """Type of failure scenario."""

    COMPLETE_OUTAGE = "complete_outage"
    DEGRADED_PERFORMANCE = "degraded_performance"
    INTERMITTENT_FAILURE = "intermittent_failure"
    PARTIAL_OUTAGE = "partial_outage"


class OutcomeType(str, Enum):
    """Type of service outcome impact."""

    DOWNTIME = "downtime"  # Complete service unavailability
    DEGRADED = "degraded"  # Reduced performance/capacity
    BLIP = "blip"  # Brief intermittent issues
    TIMEOUT = "timeout"  # Increased latency/timeouts
    ERROR_RATE = "error_rate"  # Increased error responses
    PARTIAL_OUTAGE = "partial_outage"  # Some instances/regions down


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
    time_since_last_change: float | None = None
    recommendations: list[str] = field(default_factory=list)
    factors: dict[str, Any] = field(default_factory=dict)
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
    directly_affected: list[dict[str, Any]]
    indirectly_affected: list[dict[str, Any]]
    total_affected: int
    user_impact: ImpactLevel
    estimated_downtime_seconds: int
    critical_path: list[str] = field(default_factory=list)
    affected_services: dict[str, int] = field(default_factory=dict)


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
    recovery_steps: list[str] = field(default_factory=list)
    mitigation_strategies: list[str] = field(default_factory=list)
    similar_past_incidents: list[dict[str, Any]] = field(default_factory=list)


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
    recommendations: list[str] = field(default_factory=list)


@dataclass
class FailureOutcome:
    """
    Detailed outcome analysis for a specific failure type.

    Attributes:
        outcome_type: Type of outcome (downtime, degraded, blip, etc.)
        probability: Likelihood of this outcome (0-1)
        duration_seconds: Expected duration of impact
        affected_percentage: Percentage of service affected (0-100)
        user_impact_description: Human-readable impact description
        technical_details: Technical details of the impact
    """

    outcome_type: OutcomeType
    probability: float
    duration_seconds: int
    affected_percentage: float
    user_impact_description: str
    technical_details: str = ""


@dataclass
class PartialFailureScenario:
    """
    Analysis of partial/degraded failure scenarios.

    Attributes:
        resource_id: ID of the resource
        resource_name: Name of the resource
        failure_type: Type of failure being analyzed
        outcomes: List of possible outcomes
        overall_impact: Overall impact level
        mitigation_strategies: Strategies to prevent/reduce impact
        monitoring_recommendations: What to monitor
    """

    resource_id: str
    resource_name: str
    failure_type: FailureType
    outcomes: list[FailureOutcome] = field(default_factory=list)
    overall_impact: ImpactLevel = ImpactLevel.MEDIUM
    mitigation_strategies: list[str] = field(default_factory=list)
    monitoring_recommendations: list[str] = field(default_factory=list)


@dataclass
class DependencyVulnerability:
    """
    Vulnerability found in a package dependency.

    Attributes:
        package_name: Name of the vulnerable package
        current_version: Currently installed version
        vulnerability_id: CVE or vulnerability identifier
        severity: Severity level (low, medium, high, critical)
        description: Vulnerability description
        fixed_version: Version that fixes the vulnerability
        exploit_available: Whether a public exploit exists
        affected_resources: Resources using this dependency
    """

    package_name: str
    current_version: str
    vulnerability_id: str
    severity: str
    description: str
    fixed_version: str | None = None
    exploit_available: bool = False
    affected_resources: list[str] = field(default_factory=list)
