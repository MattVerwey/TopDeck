"""
Risk scoring algorithms.
"""

from typing import Any

from .models import RiskLevel


class RiskScorer:
    """
    Calculates risk scores for resources based on multiple factors.
    """

    # Default weights for risk factors (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "dependency_count": 0.25,  # How many services depend on this
        "criticality": 0.30,  # How critical is this service
        "failure_rate": 0.20,  # Historical failure rate
        "time_since_change": -0.10,  # Longer = less risky (negative weight)
        "redundancy": -0.15,  # More redundancy = less risky (negative weight)
    }

    # Criticality factors for different resource types
    CRITICALITY_FACTORS = {
        # High criticality
        "database": 30,
        "sql_database": 30,
        "cosmos_db": 30,
        "cache": 25,
        "redis_cache": 25,
        # Authentication/Security
        "key_vault": 40,
        "authentication": 40,
        # Messaging (high criticality - async communication backbone)
        "servicebus_namespace": 28,
        "servicebus_topic": 26,
        "servicebus_queue": 26,
        "servicebus_subscription": 18,
        # Medium-high criticality
        "load_balancer": 20,
        "api_gateway": 20,
        "app_gateway": 20,
        # Medium criticality
        "web_app": 15,
        "function_app": 15,
        "pod": 15,
        "aks": 15,
        "eks": 15,
        "gke_cluster": 15,
        # Lower criticality
        "storage_account": 10,
        "blob_storage": 10,
        "vm": 10,
        "vnet": 5,
    }

    def __init__(self, weights: dict[str, float] | None = None):
        """
        Initialize risk scorer.

        Args:
            weights: Custom weights for risk factors (optional)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def calculate_risk_score(
        self,
        dependency_count: int,
        dependents_count: int,
        resource_type: str,
        is_single_point_of_failure: bool,
        deployment_failure_rate: float = 0.0,
        time_since_last_change_hours: float | None = None,
        has_redundancy: bool = False,
        **kwargs: Any,
    ) -> float:
        """
        Calculate overall risk score for a resource.

        Args:
            dependency_count: Number of resources this depends on
            dependents_count: Number of resources depending on this
            resource_type: Type of resource
            is_single_point_of_failure: Whether this is a SPOF
            deployment_failure_rate: Historical failure rate (0-1)
            time_since_last_change_hours: Hours since last deployment
            has_redundancy: Whether resource has redundant alternatives
            **kwargs: Additional factors

        Returns:
            Risk score from 0-100
        """
        score = 0.0

        # Factor 1: Dependency impact (more dependents = higher risk)
        # Normalize to 0-100 scale (assume max 50 dependents is very high risk)
        dependency_impact = min(100, (dependents_count / 50) * 100)
        score += dependency_impact * self.weights["dependency_count"]

        # Factor 2: Criticality based on resource type
        criticality = self._calculate_criticality(
            resource_type, is_single_point_of_failure, dependents_count
        )
        score += criticality * self.weights["criticality"]

        # Factor 3: Historical failure rate
        # Already normalized to 0-1, scale to 0-100
        failure_impact = deployment_failure_rate * 100
        score += failure_impact * self.weights["failure_rate"]

        # Factor 4: Time since last change (reduces risk over time)
        if time_since_last_change_hours is not None:
            # Normalize: 0 hours = full risk, 720+ hours (30 days) = minimal risk
            time_factor = max(0, min(100, 100 - (time_since_last_change_hours / 720) * 100))
            score += time_factor * self.weights["time_since_change"]

        # Factor 5: Redundancy (reduces risk)
        redundancy_factor = 0 if has_redundancy else 100
        score += redundancy_factor * self.weights["redundancy"]

        # Ensure score is within bounds
        return max(0.0, min(100.0, score))

    def _calculate_criticality(
        self, resource_type: str, is_spof: bool, dependents_count: int
    ) -> float:
        """
        Calculate criticality score for a resource.

        Args:
            resource_type: Type of resource
            is_spof: Whether this is a single point of failure
            dependents_count: Number of dependents

        Returns:
            Criticality score (0-100)
        """
        # Base criticality from resource type
        base_criticality = self.CRITICALITY_FACTORS.get(
            resource_type.lower(), 10  # Default for unknown types
        )

        # Boost if it's a SPOF
        if is_spof:
            base_criticality += 15

        # Boost based on number of dependents
        if dependents_count > 10:
            base_criticality += 20
        elif dependents_count > 5:
            base_criticality += 10
        elif dependents_count > 0:
            base_criticality += 5

        return min(100.0, float(base_criticality))

    def get_risk_level(self, risk_score: float) -> RiskLevel:
        """
        Convert numeric risk score to categorical level.

        Args:
            risk_score: Numeric score (0-100)

        Returns:
            RiskLevel enum
        """
        if risk_score >= 75:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def generate_recommendations(
        self,
        risk_score: float,
        is_spof: bool,
        has_redundancy: bool,
        dependents_count: int,
        deployment_failure_rate: float,
    ) -> list[str]:
        """
        Generate risk mitigation recommendations.

        Args:
            risk_score: Current risk score
            is_spof: Whether this is a SPOF
            has_redundancy: Whether resource has redundancy
            dependents_count: Number of dependents
            deployment_failure_rate: Historical failure rate

        Returns:
            List of recommendations
        """
        recommendations = []

        # High risk recommendations
        if risk_score >= 75:
            recommendations.append("⚠️ CRITICAL RISK: Deploy only during maintenance windows")
            recommendations.append("Implement comprehensive monitoring and alerting")
            recommendations.append("Prepare detailed rollback procedures")

        # SPOF recommendations
        if is_spof:
            recommendations.append(
                "🔴 Single Point of Failure: Add redundancy or failover capability"
            )
            if not has_redundancy:
                recommendations.append(
                    "Consider deploying redundant instances across availability zones"
                )

        # High dependency recommendations
        if dependents_count > 10:
            recommendations.append(
                f"High dependency count ({dependents_count} dependents): "
                "Implement circuit breakers and fallback mechanisms"
            )

        # Failure rate recommendations
        if deployment_failure_rate > 0.2:  # > 20% failure rate
            recommendations.append(
                f"High failure rate ({deployment_failure_rate:.1%}): "
                "Review deployment process and add more comprehensive testing"
            )

        # General recommendations
        if risk_score >= 50:
            recommendations.append("Implement canary deployments to minimize blast radius")
            recommendations.append("Ensure all dependencies are properly health-checked")

        # Default recommendation if none generated
        if not recommendations and risk_score > 25:
            recommendations.append("Monitor deployment closely and be prepared to rollback")

        return recommendations
