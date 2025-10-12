"""
Data models for resource discovery.

These models represent discovered cloud resources and relationships
in a cloud-agnostic format before they are stored in Neo4j.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"


class ResourceStatus(str, Enum):
    """Resource operational status"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class DependencyCategory(str, Enum):
    """Dependency category types"""
    NETWORK = "network"
    DATA = "data"
    CONFIGURATION = "configuration"
    COMPUTE = "compute"


class DependencyType(str, Enum):
    """Dependency strength types"""
    REQUIRED = "required"
    OPTIONAL = "optional"
    STRONG = "strong"
    WEAK = "weak"


@dataclass
class DiscoveredResource:
    """
    Represents a discovered cloud resource.
    This is the internal representation before mapping to Neo4j.
    """
    
    # Core identification
    id: str  # Cloud provider resource ID (e.g., Azure ARM ID, AWS ARN)
    name: str
    resource_type: str  # TopDeck normalized type (e.g., 'virtual_machine', 'aks')
    cloud_provider: CloudProvider
    
    # Location and organization
    region: str
    resource_group: Optional[str] = None
    subscription_id: Optional[str] = None
    
    # Status and metadata
    status: ResourceStatus = ResourceStatus.UNKNOWN
    environment: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    # Cloud-specific properties (stored as JSON in Neo4j)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Discovery tracking
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_method: str = "discovery"
    
    # Optional cost information
    cost_per_day: Optional[float] = None
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json
        
        return {
            'id': self.id,
            'name': self.name,
            'resource_type': self.resource_type,
            'cloud_provider': self.cloud_provider.value,
            'region': self.region,
            'resource_group': self.resource_group,
            'subscription_id': self.subscription_id,
            'status': self.status.value,
            'environment': self.environment,
            'tags': self.tags,
            'properties': json.dumps(self.properties),
            'discovered_at': self.discovered_at.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'discovered_method': self.discovered_method,
            'cost_per_day': self.cost_per_day,
        }


@dataclass
class ResourceDependency:
    """
    Represents a dependency between two resources.
    """
    
    source_id: str  # Resource ID that depends on target
    target_id: str  # Resource ID that is depended upon
    
    # Dependency characteristics
    category: DependencyCategory
    dependency_type: DependencyType
    strength: float = 0.5  # 0.0 (weak) to 1.0 (critical)
    
    # Discovery metadata
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    discovered_method: str = "configuration"
    description: Optional[str] = None
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert to Neo4j relationship properties"""
        return {
            'category': self.category.value,
            'dependency_type': self.dependency_type.value,
            'strength': self.strength,
            'discovered_at': self.discovered_at.isoformat(),
            'discovered_method': self.discovered_method,
            'description': self.description,
        }


@dataclass
class DiscoveryResult:
    """
    Results from a resource discovery operation.
    """
    
    resources: List[DiscoveredResource] = field(default_factory=list)
    dependencies: List[ResourceDependency] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    subscription_id: Optional[str] = None
    discovery_started_at: datetime = field(default_factory=datetime.utcnow)
    discovery_completed_at: Optional[datetime] = None
    
    @property
    def resource_count(self) -> int:
        """Total resources discovered"""
        return len(self.resources)
    
    @property
    def dependency_count(self) -> int:
        """Total dependencies discovered"""
        return len(self.dependencies)
    
    @property
    def has_errors(self) -> bool:
        """Check if discovery had errors"""
        return len(self.errors) > 0
    
    def add_resource(self, resource: DiscoveredResource) -> None:
        """Add a discovered resource"""
        self.resources.append(resource)
    
    def add_dependency(self, dependency: ResourceDependency) -> None:
        """Add a discovered dependency"""
        self.dependencies.append(dependency)
    
    def add_error(self, error: str) -> None:
        """Add an error message"""
        self.errors.append(error)
    
    def complete(self) -> None:
        """Mark discovery as completed"""
        self.discovery_completed_at = datetime.utcnow()
    
    def summary(self) -> str:
        """Get a summary of discovery results"""
        duration = "N/A"
        if self.discovery_completed_at:
            delta = self.discovery_completed_at - self.discovery_started_at
            duration = f"{delta.total_seconds():.2f}s"
        
        return (
            f"Discovery Result: {self.resource_count} resources, "
            f"{self.dependency_count} dependencies, "
            f"{len(self.errors)} errors, "
            f"duration: {duration}"
        )
