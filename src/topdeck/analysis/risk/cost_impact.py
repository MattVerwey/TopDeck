"""
Cost impact analysis for risk assessment.

Estimates the financial impact of failures and downtime.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# Constants
MONTHS_PER_YEAR = 12


class CostCategory(str, Enum):
    """Categories of costs associated with incidents."""

    REVENUE_LOSS = "revenue_loss"
    SLA_PENALTIES = "sla_penalties"
    ENGINEERING_TIME = "engineering_time"
    CUSTOMER_SUPPORT = "customer_support"
    REPUTATION_DAMAGE = "reputation_damage"
    RECOVERY_COSTS = "recovery_costs"


@dataclass
class CostImpact:
    """
    Financial impact assessment for a failure scenario.

    Attributes:
        resource_id: ID of the resource
        resource_name: Name of the resource
        total_cost: Total estimated cost in USD
        cost_breakdown: Breakdown by cost category
        hourly_impact_rate: Cost per hour of downtime
        affected_users: Estimated number of affected users
        confidence_level: Confidence in estimate (low, medium, high)
        assumptions: List of assumptions made in calculation
    """

    resource_id: str
    resource_name: str
    total_cost: float
    cost_breakdown: dict[str, float] = field(default_factory=dict)
    hourly_impact_rate: float = 0.0
    affected_users: int = 0
    confidence_level: str = "medium"
    assumptions: list[str] = field(default_factory=list)


class CostImpactAnalyzer:
    """
    Analyzes the financial impact of resource failures.

    Uses industry benchmarks and configurable rates to estimate costs.
    """

    # Default cost rates (can be customized per organization)
    DEFAULT_RATES = {
        # Revenue per user per hour (e.g., e-commerce, SaaS)
        "revenue_per_user_hour": 0.50,
        # Engineering cost per hour for incident response
        "engineering_hour_rate": 150.0,
        # Customer support cost per hour
        "support_hour_rate": 50.0,
        # Average engineers responding to incident
        "avg_engineers_per_incident": 3,
        # Average support staff per incident
        "avg_support_per_incident": 2,
        # SLA penalty rate (percentage of contract value per hour)
        "sla_penalty_rate_per_hour": 0.01,
        # Reputation damage multiplier (intangible costs)
        "reputation_damage_multiplier": 0.3,
    }

    # Industry-specific cost factors
    INDUSTRY_MULTIPLIERS = {
        "ecommerce": 2.0,  # High revenue dependency
        "fintech": 3.0,  # Regulatory and trust issues
        "saas": 1.5,  # Subscription-based impact
        "healthcare": 2.5,  # Critical systems, compliance
        "gaming": 1.8,  # User engagement critical
        "media": 1.3,  # Content delivery
        "enterprise": 1.2,  # B2B impacts
        "default": 1.0,
    }

    def __init__(
        self,
        rates: dict[str, float] | None = None,
        industry: str = "default",
        annual_revenue: float | None = None,
    ):
        """
        Initialize cost impact analyzer.

        Args:
            rates: Custom cost rates (overrides defaults)
            industry: Industry type for applying multipliers
            annual_revenue: Annual revenue for SLA penalty calculations
        """
        self.rates = {**self.DEFAULT_RATES, **(rates or {})}
        self.industry = industry
        self.annual_revenue = annual_revenue
        self.industry_multiplier = self.INDUSTRY_MULTIPLIERS.get(industry, 1.0)

    def calculate_cost_impact(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        downtime_hours: float,
        affected_users: int,
        is_revenue_generating: bool = True,
        has_sla: bool = False,
    ) -> CostImpact:
        """
        Calculate comprehensive cost impact of a failure.

        Args:
            resource_id: Resource identifier
            resource_name: Resource name
            resource_type: Type of resource
            downtime_hours: Expected downtime in hours
            affected_users: Number of users affected
            is_revenue_generating: Whether resource directly generates revenue
            has_sla: Whether SLA penalties apply

        Returns:
            CostImpact with detailed breakdown
        """
        cost_breakdown: dict[str, float] = {}
        assumptions = []

        # 1. Revenue loss
        if is_revenue_generating and affected_users > 0:
            revenue_loss = (
                affected_users
                * downtime_hours
                * self.rates["revenue_per_user_hour"]
                * self.industry_multiplier
            )
            cost_breakdown[CostCategory.REVENUE_LOSS.value] = revenue_loss
            assumptions.append(
                f"Revenue loss based on {affected_users} users "
                f"at ${self.rates['revenue_per_user_hour']}/user/hour"
            )

        # 2. Engineering time for incident response
        engineering_cost = (
            self.rates["avg_engineers_per_incident"]
            * downtime_hours
            * self.rates["engineering_hour_rate"]
        )
        cost_breakdown[CostCategory.ENGINEERING_TIME.value] = engineering_cost
        assumptions.append(
            f"Engineering cost based on {self.rates['avg_engineers_per_incident']} "
            f"engineers at ${self.rates['engineering_hour_rate']}/hour"
        )

        # 3. Customer support costs
        support_cost = (
            self.rates["avg_support_per_incident"]
            * downtime_hours
            * self.rates["support_hour_rate"]
        )
        cost_breakdown[CostCategory.CUSTOMER_SUPPORT.value] = support_cost
        assumptions.append(
            f"Support cost based on {self.rates['avg_support_per_incident']} "
            f"staff at ${self.rates['support_hour_rate']}/hour"
        )

        # 4. SLA penalties (if applicable)
        if has_sla and self.annual_revenue:
            sla_penalty = (
                self.annual_revenue * self.rates["sla_penalty_rate_per_hour"] * downtime_hours
            )
            cost_breakdown[CostCategory.SLA_PENALTIES.value] = sla_penalty
            assumptions.append(
                f"SLA penalty at {self.rates['sla_penalty_rate_per_hour']*100}% "
                f"of annual revenue per hour"
            )

        # 5. Reputation damage (intangible)
        # Calculated as a percentage of other costs
        tangible_costs = sum(cost_breakdown.values())
        reputation_damage = tangible_costs * self.rates["reputation_damage_multiplier"]
        cost_breakdown[CostCategory.REPUTATION_DAMAGE.value] = reputation_damage
        assumptions.append(
            f"Reputation damage estimated at {self.rates['reputation_damage_multiplier']*100}% "
            "of tangible costs"
        )

        # 6. Recovery costs (infrastructure, data restoration)
        # Estimate based on severity and resource type
        recovery_cost = self._estimate_recovery_cost(resource_type, downtime_hours)
        cost_breakdown[CostCategory.RECOVERY_COSTS.value] = recovery_cost
        assumptions.append(f"Recovery costs estimated for {resource_type}")

        total_cost = sum(cost_breakdown.values())
        hourly_impact_rate = total_cost / downtime_hours if downtime_hours > 0 else 0

        # Determine confidence level
        confidence = self._determine_confidence_level(
            is_revenue_generating, has_sla, affected_users
        )

        return CostImpact(
            resource_id=resource_id,
            resource_name=resource_name,
            total_cost=round(total_cost, 2),
            cost_breakdown={k: round(v, 2) for k, v in cost_breakdown.items()},
            hourly_impact_rate=round(hourly_impact_rate, 2),
            affected_users=affected_users,
            confidence_level=confidence,
            assumptions=assumptions,
        )

    def estimate_annual_risk_cost(
        self,
        hourly_impact_rate: float,
        failure_probability_per_year: float,
        mean_time_to_recovery_hours: float,
    ) -> dict[str, Any]:
        """
        Estimate annual cost due to risk.

        Args:
            hourly_impact_rate: Cost per hour of downtime
            failure_probability_per_year: Probability of failure in a year (0-1)
            mean_time_to_recovery_hours: Average recovery time

        Returns:
            Dictionary with annual risk cost analysis
        """
        # Expected annual downtime
        expected_downtime_hours = failure_probability_per_year * mean_time_to_recovery_hours

        # Expected annual cost
        expected_annual_cost = hourly_impact_rate * expected_downtime_hours

        # Calculate range (with confidence intervals)
        # Assume +/- 50% for uncertainty
        min_cost = expected_annual_cost * 0.5
        max_cost = expected_annual_cost * 1.5

        return {
            "expected_annual_cost": round(expected_annual_cost, 2),
            "min_annual_cost": round(min_cost, 2),
            "max_annual_cost": round(max_cost, 2),
            "expected_downtime_hours": round(expected_downtime_hours, 2),
            "hourly_impact_rate": hourly_impact_rate,
            "recommendations": self._generate_cost_recommendations(
                expected_annual_cost, hourly_impact_rate
            ),
        }

    def compare_mitigation_costs(
        self,
        current_risk_cost: float,
        mitigation_options: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Compare cost of mitigations vs. risk cost.

        Args:
            current_risk_cost: Current expected annual risk cost
            mitigation_options: List of mitigation strategies with costs

        Returns:
            List of options with ROI analysis
        """
        results = []

        for option in mitigation_options:
            implementation_cost = option.get("implementation_cost", 0)
            annual_operational_cost = option.get("annual_operational_cost", 0)
            risk_reduction = option.get("risk_reduction_percentage", 0) / 100

            # Calculate savings
            annual_savings = current_risk_cost * risk_reduction
            total_first_year_cost = implementation_cost + annual_operational_cost

            # Calculate ROI
            if total_first_year_cost > 0:
                roi = ((annual_savings - total_first_year_cost) / total_first_year_cost) * 100
                payback_months = (implementation_cost / (annual_savings / MONTHS_PER_YEAR)) if annual_savings > 0 else float('inf')
            else:
                roi = float('inf')
                payback_months = 0

            results.append(
                {
                    "mitigation": option.get("name", "Unknown"),
                    "implementation_cost": implementation_cost,
                    "annual_operational_cost": annual_operational_cost,
                    "annual_savings": round(annual_savings, 2),
                    "roi_percentage": round(roi, 2),
                    "payback_months": round(payback_months, 1) if payback_months != float('inf') else "N/A",
                    "net_benefit_year_1": round(annual_savings - total_first_year_cost, 2),
                    "recommended": annual_savings > total_first_year_cost,
                }
            )

        # Sort by ROI
        results.sort(key=lambda x: x["roi_percentage"], reverse=True)
        return results

    def _estimate_recovery_cost(self, resource_type: str, downtime_hours: float) -> float:
        """Estimate recovery costs based on resource type."""
        # Base recovery cost per hour
        base_costs = {
            "database": 200.0,  # Data restoration is expensive
            "sql_database": 200.0,
            "cosmos_db": 250.0,
            "cache": 50.0,  # Cache can be rebuilt
            "redis_cache": 50.0,
            "web_app": 100.0,
            "api_gateway": 150.0,
            "load_balancer": 75.0,
            "storage_account": 100.0,
            "default": 100.0,
        }

        base_cost = base_costs.get(resource_type.lower(), base_costs["default"])

        # Non-linear scaling (longer downtime = higher complexity)
        if downtime_hours > 4:
            multiplier = 1 + (downtime_hours - 4) * 0.2
        else:
            multiplier = 1.0

        return base_cost * downtime_hours * multiplier

    def _determine_confidence_level(
        self, is_revenue_generating: bool, has_sla: bool, affected_users: int
    ) -> str:
        """Determine confidence level in cost estimate."""
        if is_revenue_generating and has_sla and affected_users > 100:
            return "high"
        elif (is_revenue_generating or has_sla) and affected_users > 10:
            return "medium"
        else:
            return "low"

    def _generate_cost_recommendations(
        self, expected_annual_cost: float, hourly_impact_rate: float
    ) -> list[str]:
        """Generate cost-based recommendations."""
        recommendations = []

        if expected_annual_cost > 100000:
            recommendations.append(
                "💰 High annual risk cost ($100K+): Prioritize redundancy and failover capabilities"
            )

        if hourly_impact_rate > 10000:
            recommendations.append(
                "⚠️ High hourly impact ($10K+/hour): Implement 24/7 monitoring and on-call rotation"
            )

        if expected_annual_cost > 50000:
            recommendations.append(
                "📊 Consider cost-benefit analysis of high-availability architecture"
            )

        if hourly_impact_rate > 5000:
            recommendations.append(
                "🔄 Implement automated failover to minimize recovery time"
            )

        return recommendations
