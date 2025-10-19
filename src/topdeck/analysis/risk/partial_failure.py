"""
Partial and degraded failure scenario analysis.

This module analyzes non-catastrophic failure scenarios such as:
- Degraded performance (slow responses)
- Intermittent failures (occasional errors)
- Partial outages (some endpoints/regions affected)
"""

from typing import List, Dict, Any

from .models import (
    PartialFailureScenario,
    FailureOutcome,
    FailureType,
    OutcomeType,
    ImpactLevel,
)


class PartialFailureAnalyzer:
    """
    Analyzes partial and degraded failure scenarios.
    
    Unlike complete outage analysis, this focuses on realistic
    degradation scenarios that are more common in production.
    """
    
    # Resource type to typical degraded performance symptoms
    DEGRADATION_PATTERNS = {
        "database": {
            "symptoms": ["Slow queries", "Connection pool exhaustion", "Lock contention"],
            "outcomes": [
                (OutcomeType.DEGRADED, 0.6, 1800, 60),  # 60% affected for 30min
                (OutcomeType.TIMEOUT, 0.3, 900, 30),    # 30% timeouts for 15min
                (OutcomeType.BLIP, 0.1, 300, 10),       # 10% brief issues for 5min
            ]
        },
        "redis_cache": {
            "symptoms": ["Cache miss rate increase", "Memory pressure", "Eviction spikes"],
            "outcomes": [
                (OutcomeType.DEGRADED, 0.7, 600, 80),   # 80% affected for 10min
                (OutcomeType.BLIP, 0.3, 180, 20),       # 20% brief issues for 3min
            ]
        },
        "web_app": {
            "symptoms": ["Increased response time", "Thread pool exhaustion", "Memory leaks"],
            "outcomes": [
                (OutcomeType.DEGRADED, 0.5, 1200, 70),  # 70% affected for 20min
                (OutcomeType.TIMEOUT, 0.3, 600, 40),    # 40% timeouts for 10min
                (OutcomeType.ERROR_RATE, 0.2, 300, 15), # 15% errors for 5min
            ]
        },
        "load_balancer": {
            "symptoms": ["Unhealthy backend targets", "Request queuing", "SSL handshake delays"],
            "outcomes": [
                (OutcomeType.DEGRADED, 0.4, 900, 50),   # 50% affected for 15min
                (OutcomeType.TIMEOUT, 0.4, 600, 30),    # 30% timeouts for 10min
                (OutcomeType.DOWNTIME, 0.2, 300, 100),  # Complete for 5min
            ]
        },
        "api_gateway": {
            "symptoms": ["Rate limit exhaustion", "Route lookup delays", "Auth service latency"],
            "outcomes": [
                (OutcomeType.ERROR_RATE, 0.5, 600, 25), # 25% errors for 10min
                (OutcomeType.TIMEOUT, 0.3, 900, 40),    # 40% timeouts for 15min
                (OutcomeType.DEGRADED, 0.2, 1200, 60),  # 60% affected for 20min
            ]
        },
        "aks": {
            "symptoms": ["Node pressure", "Pod evictions", "DNS resolution delays"],
            "outcomes": [
                (OutcomeType.DEGRADED, 0.5, 1800, 40),  # 40% affected for 30min
                (OutcomeType.BLIP, 0.3, 600, 20),       # 20% brief issues for 10min
                (OutcomeType.PARTIAL_OUTAGE, 0.2, 900, 30), # 30% down for 15min
            ]
        },
        "default": {
            "symptoms": ["Resource saturation", "Network latency", "Configuration issues"],
            "outcomes": [
                (OutcomeType.DEGRADED, 0.6, 900, 50),
                (OutcomeType.BLIP, 0.3, 300, 20),
                (OutcomeType.TIMEOUT, 0.1, 600, 30),
            ]
        }
    }
    
    def analyze_degraded_performance(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        current_load: float = 0.7,  # Current load percentage (0-1)
    ) -> PartialFailureScenario:
        """
        Analyze degraded performance scenario.
        
        This models what happens when a resource is under stress but not failed.
        More realistic than complete failure for most production issues.
        
        Args:
            resource_id: Resource to analyze
            resource_name: Name of the resource
            resource_type: Type of resource
            current_load: Current load factor (0-1)
            
        Returns:
            PartialFailureScenario with degraded performance analysis
        """
        pattern = self.DEGRADATION_PATTERNS.get(
            resource_type.lower(),
            self.DEGRADATION_PATTERNS["default"]
        )
        
        outcomes = []
        for outcome_type, base_prob, duration, affected_pct in pattern["outcomes"]:
            # Adjust probability based on current load
            # Higher load = higher probability of degradation
            probability = min(1.0, base_prob * (0.5 + current_load))
            
            # Adjust affected percentage based on load
            adjusted_affected = min(100.0, affected_pct * (0.8 + current_load * 0.4))
            
            outcome = FailureOutcome(
                outcome_type=outcome_type,
                probability=probability,
                duration_seconds=duration,
                affected_percentage=adjusted_affected,
                user_impact_description=self._get_user_impact_description(
                    outcome_type, adjusted_affected
                ),
                technical_details=f"{resource_type} {pattern['symptoms'][0].lower()}"
            )
            outcomes.append(outcome)
        
        # Determine overall impact
        overall_impact = self._calculate_overall_impact(outcomes)
        
        # Generate mitigation strategies
        mitigation = self._generate_degradation_mitigation(resource_type, outcomes)
        
        # Generate monitoring recommendations
        monitoring = self._generate_monitoring_recommendations(resource_type, pattern)
        
        return PartialFailureScenario(
            resource_id=resource_id,
            resource_name=resource_name,
            failure_type=FailureType.DEGRADED_PERFORMANCE,
            outcomes=outcomes,
            overall_impact=overall_impact,
            mitigation_strategies=mitigation,
            monitoring_recommendations=monitoring,
        )
    
    def analyze_intermittent_failure(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        failure_frequency: float = 0.05,  # % of requests that fail
    ) -> PartialFailureScenario:
        """
        Analyze intermittent failure scenario (occasional errors).
        
        Args:
            resource_id: Resource to analyze
            resource_name: Name of the resource
            resource_type: Type of resource
            failure_frequency: Percentage of requests failing (0-1)
            
        Returns:
            PartialFailureScenario with intermittent failure analysis
        """
        outcomes = [
            FailureOutcome(
                outcome_type=OutcomeType.BLIP,
                probability=0.7,
                duration_seconds=120,  # 2 minutes
                affected_percentage=failure_frequency * 100,
                user_impact_description=(
                    f"Users experience occasional errors (~{failure_frequency*100:.1f}% of requests). "
                    "Most retries succeed. UX is degraded but service remains available."
                ),
                technical_details=f"Intermittent {resource_type} errors, likely race conditions or resource contention"
            ),
            FailureOutcome(
                outcome_type=OutcomeType.ERROR_RATE,
                probability=0.3,
                duration_seconds=300,  # 5 minutes
                affected_percentage=failure_frequency * 100 * 2,  # Can spike to 2x
                user_impact_description=(
                    f"Error rate spikes to ~{failure_frequency*200:.1f}%. "
                    "Users experience frequent failures requiring retries."
                ),
                technical_details=f"Cascading failures from {resource_type} instability"
            ),
        ]
        
        overall_impact = ImpactLevel.LOW if failure_frequency < 0.1 else ImpactLevel.MEDIUM
        
        mitigation = [
            "Implement retry logic with exponential backoff",
            "Add circuit breakers to prevent cascade failures",
            "Enable request hedging for critical operations",
            "Implement chaos engineering to identify fragile components",
            f"Add detailed logging around {resource_type} operations",
            "Consider implementing a bulkhead pattern to isolate failures",
        ]
        
        monitoring = [
            "Set up alerting on error rate thresholds (>1%, >5%, >10%)",
            "Track P95 and P99 latency metrics",
            "Monitor retry rates and success rates",
            "Implement distributed tracing to identify error sources",
            f"Create dashboards for {resource_type} health metrics",
        ]
        
        return PartialFailureScenario(
            resource_id=resource_id,
            resource_name=resource_name,
            failure_type=FailureType.INTERMITTENT_FAILURE,
            outcomes=outcomes,
            overall_impact=overall_impact,
            mitigation_strategies=mitigation,
            monitoring_recommendations=monitoring,
        )
    
    def analyze_partial_outage(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        affected_zones: List[str] = None,
    ) -> PartialFailureScenario:
        """
        Analyze partial outage scenario (some instances/regions down).
        
        Args:
            resource_id: Resource to analyze
            resource_name: Name of the resource
            resource_type: Type of resource
            affected_zones: List of affected availability zones
            
        Returns:
            PartialFailureScenario with partial outage analysis
        """
        affected_zones = affected_zones or ["zone-a"]
        total_zones = 3  # Assume 3 zones typically
        affected_percentage = (len(affected_zones) / total_zones) * 100
        
        outcomes = [
            FailureOutcome(
                outcome_type=OutcomeType.PARTIAL_OUTAGE,
                probability=0.8,
                duration_seconds=900,  # 15 minutes
                affected_percentage=affected_percentage,
                user_impact_description=(
                    f"{affected_percentage:.0f}% of capacity lost. "
                    f"Service degraded but operational on remaining zones. "
                    f"Some users routed to failed zones experience errors."
                ),
                technical_details=f"{resource_type} in zones {', '.join(affected_zones)} unavailable"
            ),
            FailureOutcome(
                outcome_type=OutcomeType.DEGRADED,
                probability=0.2,
                duration_seconds=1800,  # 30 minutes
                affected_percentage=100 - affected_percentage,
                user_impact_description=(
                    f"Remaining {100-affected_percentage:.0f}% capacity handling "
                    "100% of traffic. Increased latency and occasional timeouts."
                ),
                technical_details=f"Overload on healthy {resource_type} instances"
            ),
        ]
        
        overall_impact = (
            ImpactLevel.HIGH if affected_percentage > 50
            else ImpactLevel.MEDIUM if affected_percentage > 30
            else ImpactLevel.LOW
        )
        
        mitigation = [
            "Implement multi-zone redundancy with automatic failover",
            "Configure health checks to remove failed instances",
            "Set up auto-scaling to compensate for lost capacity",
            "Use DNS-based routing to redirect traffic from failed zones",
            f"Deploy {resource_type} across at least 3 availability zones",
            "Implement graceful degradation when capacity is reduced",
        ]
        
        monitoring = [
            "Monitor per-zone health and traffic distribution",
            "Set up alerts for zone-level failures",
            "Track capacity utilization per zone",
            "Monitor failover success rates",
            "Set up cross-zone latency monitoring",
        ]
        
        return PartialFailureScenario(
            resource_id=resource_id,
            resource_name=resource_name,
            failure_type=FailureType.PARTIAL_OUTAGE,
            outcomes=outcomes,
            overall_impact=overall_impact,
            mitigation_strategies=mitigation,
            monitoring_recommendations=monitoring,
        )
    
    def _get_user_impact_description(
        self,
        outcome_type: OutcomeType,
        affected_percentage: float
    ) -> str:
        """Generate user-facing impact description."""
        if outcome_type == OutcomeType.DOWNTIME:
            return f"Complete service unavailability affecting {affected_percentage:.0f}% of users"
        elif outcome_type == OutcomeType.DEGRADED:
            return f"Slow response times affecting {affected_percentage:.0f}% of requests. Users experience delays but service works."
        elif outcome_type == OutcomeType.BLIP:
            return f"Brief intermittent issues affecting {affected_percentage:.0f}% of requests. Most users won't notice."
        elif outcome_type == OutcomeType.TIMEOUT:
            return f"Request timeouts affecting {affected_percentage:.0f}% of operations. Users need to retry."
        elif outcome_type == OutcomeType.ERROR_RATE:
            return f"Increased error rate affecting {affected_percentage:.0f}% of requests. Users see error messages."
        else:
            return f"Service impact affecting {affected_percentage:.0f}% of operations"
    
    def _calculate_overall_impact(self, outcomes: List[FailureOutcome]) -> ImpactLevel:
        """Calculate overall impact from multiple outcomes."""
        # Weight by probability and severity
        severity_weights = {
            OutcomeType.DOWNTIME: 5.0,
            OutcomeType.ERROR_RATE: 3.0,
            OutcomeType.TIMEOUT: 3.0,
            OutcomeType.DEGRADED: 2.0,
            OutcomeType.BLIP: 1.0,
            OutcomeType.PARTIAL_OUTAGE: 4.0,
        }
        
        weighted_score = sum(
            o.probability * severity_weights.get(o.outcome_type, 2.0) * (o.affected_percentage / 100)
            for o in outcomes
        )
        
        if weighted_score >= 3.5:
            return ImpactLevel.SEVERE
        elif weighted_score >= 2.5:
            return ImpactLevel.HIGH
        elif weighted_score >= 1.5:
            return ImpactLevel.MEDIUM
        elif weighted_score >= 0.5:
            return ImpactLevel.LOW
        else:
            return ImpactLevel.MINIMAL
    
    def _generate_degradation_mitigation(
        self,
        resource_type: str,
        outcomes: List[FailureOutcome]
    ) -> List[str]:
        """Generate mitigation strategies for degradation."""
        strategies = []
        
        # Resource-specific mitigations
        if "database" in resource_type.lower():
            strategies.extend([
                "Implement connection pooling with proper limits",
                "Add read replicas to distribute load",
                "Set up query timeouts to prevent long-running queries",
                "Enable slow query logging and optimize problematic queries",
                "Consider implementing caching layer (Redis/Memcached)",
            ])
        elif "cache" in resource_type.lower():
            strategies.extend([
                "Implement cache warming strategies",
                "Set appropriate TTLs to balance freshness and hit rate",
                "Monitor and tune eviction policies",
                "Consider multi-tier caching (L1/L2)",
                "Implement graceful degradation when cache is unavailable",
            ])
        elif "web" in resource_type.lower() or "app" in resource_type.lower():
            strategies.extend([
                "Implement auto-scaling based on CPU/memory/request rate",
                "Add CDN for static content",
                "Optimize application code for efficiency",
                "Implement request rate limiting",
                "Use asynchronous processing for heavy operations",
            ])
        
        # General strategies
        strategies.extend([
            "Set up comprehensive performance monitoring",
            "Implement load testing to identify capacity limits",
            "Create runbooks for performance degradation incidents",
            "Establish SLOs and alert on SLO violations",
        ])
        
        return strategies
    
    def _generate_monitoring_recommendations(
        self,
        resource_type: str,
        pattern: Dict[str, Any]
    ) -> List[str]:
        """Generate monitoring recommendations."""
        recommendations = [
            "Monitor key performance indicators (latency, throughput, errors)",
            "Set up alerts on P95/P99 latency thresholds",
            "Track resource utilization (CPU, memory, connections)",
            "Implement health check endpoints",
        ]
        
        # Add symptom-specific monitoring
        for symptom in pattern["symptoms"]:
            if "slow" in symptom.lower() or "query" in symptom.lower():
                recommendations.append("Monitor query execution times and slow query counts")
            elif "connection" in symptom.lower():
                recommendations.append("Monitor connection pool metrics and saturation")
            elif "memory" in symptom.lower():
                recommendations.append("Monitor memory usage and garbage collection metrics")
            elif "eviction" in symptom.lower():
                recommendations.append("Track cache eviction rates and hit/miss ratios")
        
        return recommendations
