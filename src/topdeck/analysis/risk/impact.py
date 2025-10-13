"""
Impact analysis and blast radius calculation.
"""

from typing import Dict, List

from .models import BlastRadius, ImpactLevel
from .dependency import DependencyAnalyzer


class ImpactAnalyzer:
    """
    Analyzes the impact of resource failures.
    """
    
    def __init__(self, dependency_analyzer: DependencyAnalyzer):
        """
        Initialize impact analyzer.
        
        Args:
            dependency_analyzer: Dependency analyzer for graph queries
        """
        self.dependency_analyzer = dependency_analyzer
    
    def calculate_blast_radius(
        self,
        resource_id: str,
        resource_name: str
    ) -> BlastRadius:
        """
        Calculate blast radius for a resource failure.
        
        Args:
            resource_id: Resource to analyze
            resource_name: Name of the resource
            
        Returns:
            BlastRadius with complete impact analysis
        """
        # Get affected resources
        directly_affected, indirectly_affected = \
            self.dependency_analyzer.get_affected_resources(resource_id)
        
        total_affected = len(directly_affected) + len(indirectly_affected)
        
        # Calculate user impact
        user_impact = self._estimate_user_impact(
            resource_id,
            directly_affected,
            indirectly_affected
        )
        
        # Estimate downtime
        estimated_downtime = self._estimate_downtime(
            total_affected,
            user_impact
        )
        
        # Get critical path
        critical_path = self.dependency_analyzer.find_critical_path(resource_id)
        
        # Breakdown affected services by type
        affected_services = self._count_by_service_type(
            directly_affected + indirectly_affected
        )
        
        return BlastRadius(
            resource_id=resource_id,
            resource_name=resource_name,
            directly_affected=directly_affected,
            indirectly_affected=indirectly_affected,
            total_affected=total_affected,
            user_impact=user_impact,
            estimated_downtime_seconds=estimated_downtime,
            critical_path=critical_path,
            affected_services=affected_services,
        )
    
    def _estimate_user_impact(
        self,
        resource_id: str,
        directly_affected: List[Dict],
        indirectly_affected: List[Dict]
    ) -> ImpactLevel:
        """
        Estimate the impact on end users.
        
        Args:
            resource_id: Failing resource
            directly_affected: Directly affected resources
            indirectly_affected: Indirectly affected resources
            
        Returns:
            ImpactLevel enum
        """
        total_affected = len(directly_affected) + len(indirectly_affected)
        
        # Check if any user-facing services are affected
        user_facing_types = {
            "web_app", "api_gateway", "app_gateway",
            "load_balancer", "function_app"
        }
        
        has_user_facing = any(
            r.get("type", "").lower() in user_facing_types
            for r in directly_affected + indirectly_affected
        )
        
        # Determine impact level
        if total_affected == 0:
            return ImpactLevel.MINIMAL
        elif total_affected < 3 and not has_user_facing:
            return ImpactLevel.LOW
        elif total_affected < 10 or (total_affected < 5 and has_user_facing):
            return ImpactLevel.MEDIUM
        elif total_affected < 20 or has_user_facing:
            return ImpactLevel.HIGH
        else:
            return ImpactLevel.SEVERE
    
    def _estimate_downtime(
        self,
        total_affected: int,
        user_impact: ImpactLevel
    ) -> int:
        """
        Estimate recovery time in seconds.
        
        Args:
            total_affected: Number of affected resources
            user_impact: Level of user impact
            
        Returns:
            Estimated downtime in seconds
        """
        # Base recovery time (in seconds)
        base_time = 300  # 5 minutes
        
        # Scale by number of affected resources
        # More affected = longer to identify and fix
        resource_factor = 1 + (total_affected * 0.5)
        
        # Scale by user impact
        impact_factors = {
            ImpactLevel.MINIMAL: 0.5,
            ImpactLevel.LOW: 1.0,
            ImpactLevel.MEDIUM: 1.5,
            ImpactLevel.HIGH: 2.0,
            ImpactLevel.SEVERE: 3.0,
        }
        impact_factor = impact_factors.get(user_impact, 1.0)
        
        estimated = int(base_time * resource_factor * impact_factor)
        
        # Cap at reasonable maximum (24 hours)
        return min(estimated, 86400)
    
    def _count_by_service_type(
        self,
        resources: List[Dict]
    ) -> Dict[str, int]:
        """
        Count affected resources by service type.
        
        Args:
            resources: List of affected resources
            
        Returns:
            Dictionary mapping service type to count
        """
        counts: Dict[str, int] = {}
        
        for resource in resources:
            service_type = resource.get("type", "unknown")
            counts[service_type] = counts.get(service_type, 0) + 1
        
        return counts
