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
class Application:
    """
    Represents a deployed application or service.
    """
    
    # Core identification
    id: str  # Unique identifier
    name: str
    description: Optional[str] = None
    
    # Ownership & Organization
    owner_team: Optional[str] = None
    owner_email: Optional[str] = None
    business_unit: Optional[str] = None
    cost_center: Optional[str] = None
    
    # Code & Deployment
    repository_url: Optional[str] = None
    repository_id: Optional[str] = None  # Link to Repository node
    deployment_method: Optional[str] = None  # "aks" | "app_service" | "vm" | "container_instance"
    environment: Optional[str] = None  # "prod" | "staging" | "dev"
    
    # Health & Metrics
    health_score: Optional[float] = None  # 0-100 overall health score
    availability: Optional[float] = None  # 0-100 uptime percentage
    error_rate: Optional[float] = None  # Errors per minute
    response_time_avg: Optional[float] = None  # Average response time in ms
    
    # Version & Deployment
    current_version: Optional[str] = None  # Current deployed version
    last_deployed: Optional[datetime] = None  # Last deployment time
    last_deployed_by: Optional[str] = None  # User who deployed
    deployment_frequency: Optional[float] = None  # Deployments per day
    
    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert to Neo4j node properties"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_team': self.owner_team,
            'owner_email': self.owner_email,
            'business_unit': self.business_unit,
            'cost_center': self.cost_center,
            'repository_url': self.repository_url,
            'repository_id': self.repository_id,
            'deployment_method': self.deployment_method,
            'environment': self.environment,
            'health_score': self.health_score,
            'availability': self.availability,
            'error_rate': self.error_rate,
            'response_time_avg': self.response_time_avg,
            'current_version': self.current_version,
            'last_deployed': self.last_deployed.isoformat() if self.last_deployed else None,
            'last_deployed_by': self.last_deployed_by,
            'deployment_frequency': self.deployment_frequency,
            'last_seen': self.last_seen.isoformat(),
            'discovered_at': self.discovered_at.isoformat(),
        }


@dataclass
class Repository:
    """
    Represents a code repository (GitHub, Azure DevOps, GitLab).
    """
    
    # Core identification
    id: str  # Unique identifier
    platform: str  # "github" | "azure_devops" | "gitlab"
    url: str  # Repository URL
    name: str  # Repository name
    full_name: Optional[str] = None  # org/repo format
    
    # Branch & Commit Info
    default_branch: Optional[str] = None  # Usually "main" or "master"
    last_commit_sha: Optional[str] = None
    last_commit_message: Optional[str] = None
    last_commit_date: Optional[datetime] = None
    last_commit_author: Optional[str] = None
    
    # Repository Metadata
    description: Optional[str] = None
    language: Optional[str] = None  # Primary language
    topics: List[str] = field(default_factory=list)  # Tags/topics
    is_private: Optional[bool] = None
    is_archived: Optional[bool] = None
    
    # Activity Metrics
    stars: Optional[int] = None
    forks: Optional[int] = None
    open_issues: Optional[int] = None
    contributors_count: Optional[int] = None
    last_activity: Optional[datetime] = None
    
    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert to Neo4j node properties"""
        return {
            'id': self.id,
            'platform': self.platform,
            'url': self.url,
            'name': self.name,
            'full_name': self.full_name,
            'default_branch': self.default_branch,
            'last_commit_sha': self.last_commit_sha,
            'last_commit_message': self.last_commit_message,
            'last_commit_date': self.last_commit_date.isoformat() if self.last_commit_date else None,
            'last_commit_author': self.last_commit_author,
            'description': self.description,
            'language': self.language,
            'topics': self.topics,
            'is_private': self.is_private,
            'is_archived': self.is_archived,
            'stars': self.stars,
            'forks': self.forks,
            'open_issues': self.open_issues,
            'contributors_count': self.contributors_count,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'last_seen': self.last_seen.isoformat(),
            'discovered_at': self.discovered_at.isoformat(),
        }


@dataclass
class Deployment:
    """
    Represents a deployment event or pipeline run.
    """
    
    # Core identification
    id: str  # Unique identifier
    pipeline_id: Optional[str] = None  # CI/CD pipeline identifier
    pipeline_name: Optional[str] = None
    run_number: Optional[int] = None  # Build/run number
    
    # Version & Artifact
    version: Optional[str] = None  # Deployed version (tag, commit, etc.)
    artifact_url: Optional[str] = None  # URL to deployment artifact
    commit_sha: Optional[str] = None  # Git commit SHA
    
    # Deployment Details
    deployed_at: datetime = field(default_factory=datetime.utcnow)
    deployed_by: Optional[str] = None  # User or service principal
    deployment_duration: Optional[int] = None  # Duration in seconds
    status: str = "in_progress"  # "success" | "failed" | "in_progress" | "cancelled"
    
    # Environment
    environment: Optional[str] = None  # Target environment
    target_resources: List[str] = field(default_factory=list)  # Resource IDs where deployed
    
    # Change Information
    change_ticket_id: Optional[str] = None  # Change management ticket
    approval_status: Optional[str] = None  # "approved" | "rejected" | "pending"
    approvers: List[str] = field(default_factory=list)
    
    # Metadata
    notes: Optional[str] = None  # Deployment notes
    rollback_available: Optional[bool] = None
    previous_version: Optional[str] = None
    
    # Discovery
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert to Neo4j node properties"""
        return {
            'id': self.id,
            'pipeline_id': self.pipeline_id,
            'pipeline_name': self.pipeline_name,
            'run_number': self.run_number,
            'version': self.version,
            'artifact_url': self.artifact_url,
            'commit_sha': self.commit_sha,
            'deployed_at': self.deployed_at.isoformat(),
            'deployed_by': self.deployed_by,
            'deployment_duration': self.deployment_duration,
            'status': self.status,
            'environment': self.environment,
            'target_resources': self.target_resources,
            'change_ticket_id': self.change_ticket_id,
            'approval_status': self.approval_status,
            'approvers': self.approvers,
            'notes': self.notes,
            'rollback_available': self.rollback_available,
            'previous_version': self.previous_version,
            'discovered_at': self.discovered_at.isoformat(),
        }


@dataclass
class DiscoveryResult:
    """
    Results from a resource discovery operation.
    """
    
    resources: List[DiscoveredResource] = field(default_factory=list)
    dependencies: List[ResourceDependency] = field(default_factory=list)
    applications: List[Application] = field(default_factory=list)
    repositories: List[Repository] = field(default_factory=list)
    deployments: List[Deployment] = field(default_factory=list)
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
    def application_count(self) -> int:
        """Total applications discovered"""
        return len(self.applications)
    
    @property
    def repository_count(self) -> int:
        """Total repositories discovered"""
        return len(self.repositories)
    
    @property
    def deployment_count(self) -> int:
        """Total deployments discovered"""
        return len(self.deployments)
    
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
    
    def add_application(self, application: Application) -> None:
        """Add a discovered application"""
        self.applications.append(application)
    
    def add_repository(self, repository: Repository) -> None:
        """Add a discovered repository"""
        self.repositories.append(repository)
    
    def add_deployment(self, deployment: Deployment) -> None:
        """Add a discovered deployment"""
        self.deployments.append(deployment)
    
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
            f"{self.application_count} applications, "
            f"{self.repository_count} repositories, "
            f"{self.deployment_count} deployments, "
            f"{len(self.errors)} errors, "
            f"duration: {duration}"
        )
