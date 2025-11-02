"""
Data models for resource discovery.

These models represent discovered cloud resources and relationships
in a cloud-agnostic format before they are stored in Neo4j.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


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
    resource_group: str | None = None
    subscription_id: str | None = None

    # Status and metadata
    status: ResourceStatus = ResourceStatus.UNKNOWN
    environment: str | None = None
    tags: dict[str, str] = field(default_factory=dict)

    # Cloud-specific properties (stored as JSON in Neo4j)
    properties: dict[str, Any] = field(default_factory=dict)

    # Discovery tracking
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_method: str = "discovery"

    # Optional cost information
    cost_per_day: float | None = None

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json

        # Convert tags dict to JSON string for Neo4j compatibility
        # Neo4j doesn't accept nested Maps as property values
        tags_json = json.dumps(self.tags) if self.tags else "{}"

        # Convert properties dict to JSON string for Neo4j compatibility
        # Neo4j doesn't accept nested Maps as property values
        properties_json = json.dumps(self.properties) if self.properties else "{}"

        return {
            "id": self.id,
            "name": self.name,
            "resource_type": self.resource_type,
            "cloud_provider": self.cloud_provider.value,
            "region": self.region,
            "resource_group": self.resource_group,
            "subscription_id": self.subscription_id,
            "status": self.status.value,
            "environment": self.environment,
            "tags": tags_json,
            "properties": properties_json,
            "discovered_at": self.discovered_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "discovered_method": self.discovered_method,
            "cost_per_day": self.cost_per_day,
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
    description: str | None = None

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j relationship properties"""
        return {
            "category": self.category.value,
            "dependency_type": self.dependency_type.value,
            "strength": self.strength,
            "discovered_at": self.discovered_at.isoformat(),
            "discovered_method": self.discovered_method,
            "description": self.description,
        }


@dataclass
class Application:
    """
    Represents a deployed application or service.
    """

    # Core identification
    id: str  # Unique identifier
    name: str
    description: str | None = None

    # Ownership & Organization
    owner_team: str | None = None
    owner_email: str | None = None
    business_unit: str | None = None
    cost_center: str | None = None

    # Code & Deployment
    repository_url: str | None = None
    repository_id: str | None = None  # Link to Repository node
    deployment_method: str | None = None  # "aks" | "app_service" | "vm" | "container_instance"
    environment: str | None = None  # "prod" | "staging" | "dev"

    # Health & Metrics
    health_score: float | None = None  # 0-100 overall health score
    availability: float | None = None  # 0-100 uptime percentage
    error_rate: float | None = None  # Errors per minute
    response_time_avg: float | None = None  # Average response time in ms

    # Version & Deployment
    current_version: str | None = None  # Current deployed version
    last_deployed: datetime | None = None  # Last deployment time
    last_deployed_by: str | None = None  # User who deployed
    deployment_frequency: float | None = None  # Deployments per day

    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_team": self.owner_team,
            "owner_email": self.owner_email,
            "business_unit": self.business_unit,
            "cost_center": self.cost_center,
            "repository_url": self.repository_url,
            "repository_id": self.repository_id,
            "deployment_method": self.deployment_method,
            "environment": self.environment,
            "health_score": self.health_score,
            "availability": self.availability,
            "error_rate": self.error_rate,
            "response_time_avg": self.response_time_avg,
            "current_version": self.current_version,
            "last_deployed": self.last_deployed.isoformat() if self.last_deployed else None,
            "last_deployed_by": self.last_deployed_by,
            "deployment_frequency": self.deployment_frequency,
            "last_seen": self.last_seen.isoformat(),
            "discovered_at": self.discovered_at.isoformat(),
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
    full_name: str | None = None  # org/repo format

    # Branch & Commit Info
    default_branch: str | None = None  # Usually "main" or "master"
    last_commit_sha: str | None = None
    last_commit_message: str | None = None
    last_commit_date: datetime | None = None
    last_commit_author: str | None = None

    # Repository Metadata
    description: str | None = None
    language: str | None = None  # Primary language
    topics: list[str] = field(default_factory=list)  # Tags/topics
    is_private: bool | None = None
    is_archived: bool | None = None

    # Activity Metrics
    stars: int | None = None
    forks: int | None = None
    open_issues: int | None = None
    contributors_count: int | None = None
    last_activity: datetime | None = None

    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json

        return {
            "id": self.id,
            "platform": self.platform,
            "url": self.url,
            "name": self.name,
            "full_name": self.full_name,
            "default_branch": self.default_branch,
            "last_commit_sha": self.last_commit_sha,
            "last_commit_message": self.last_commit_message,
            "last_commit_date": (
                self.last_commit_date.isoformat() if self.last_commit_date else None
            ),
            "last_commit_author": self.last_commit_author,
            "description": self.description,
            "language": self.language,
            "topics": json.dumps(self.topics) if self.topics else "[]",
            "is_private": self.is_private,
            "is_archived": self.is_archived,
            "stars": self.stars,
            "forks": self.forks,
            "open_issues": self.open_issues,
            "contributors_count": self.contributors_count,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "last_seen": self.last_seen.isoformat(),
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class Deployment:
    """
    Represents a deployment event or pipeline run.
    """

    # Core identification
    id: str  # Unique identifier
    pipeline_id: str | None = None  # CI/CD pipeline identifier
    pipeline_name: str | None = None
    run_number: int | None = None  # Build/run number

    # Version & Artifact
    version: str | None = None  # Deployed version (tag, commit, etc.)
    artifact_url: str | None = None  # URL to deployment artifact
    commit_sha: str | None = None  # Git commit SHA

    # Deployment Details
    deployed_at: datetime = field(default_factory=datetime.utcnow)
    deployed_by: str | None = None  # User or service principal
    deployment_duration: int | None = None  # Duration in seconds
    status: str = "in_progress"  # "success" | "failed" | "in_progress" | "cancelled"

    # Environment
    environment: str | None = None  # Target environment
    target_resources: list[str] = field(default_factory=list)  # Resource IDs where deployed

    # Change Information
    change_ticket_id: str | None = None  # Change management ticket
    approval_status: str | None = None  # "approved" | "rejected" | "pending"
    approvers: list[str] = field(default_factory=list)

    # Metadata
    notes: str | None = None  # Deployment notes
    rollback_available: bool | None = None
    previous_version: str | None = None

    # Discovery
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json

        return {
            "id": self.id,
            "pipeline_id": self.pipeline_id,
            "pipeline_name": self.pipeline_name,
            "run_number": self.run_number,
            "version": self.version,
            "artifact_url": self.artifact_url,
            "commit_sha": self.commit_sha,
            "deployed_at": self.deployed_at.isoformat(),
            "deployed_by": self.deployed_by,
            "deployment_duration": self.deployment_duration,
            "status": self.status,
            "environment": self.environment,
            "target_resources": (
                json.dumps(self.target_resources) if self.target_resources else "[]"
            ),
            "change_ticket_id": self.change_ticket_id,
            "approval_status": self.approval_status,
            "approvers": json.dumps(self.approvers) if self.approvers else "[]",
            "notes": self.notes,
            "rollback_available": self.rollback_available,
            "previous_version": self.previous_version,
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class Namespace:
    """
    Represents a Kubernetes namespace within a cluster (e.g., AKS).
    """

    # Core identification
    id: str  # Unique identifier (cluster_id:namespace_name)
    name: str
    cluster_id: str  # Parent cluster resource ID

    # Metadata
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None

    # Resource Quotas
    resource_quota: dict[str, Any] | None = None  # CPU/memory quotas
    limit_ranges: dict[str, Any] | None = None

    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json

        return {
            "id": self.id,
            "name": self.name,
            "cluster_id": self.cluster_id,
            "labels": json.dumps(self.labels) if self.labels else "{}",
            "annotations": json.dumps(self.annotations) if self.annotations else "{}",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resource_quota": json.dumps(self.resource_quota) if self.resource_quota else None,
            "limit_ranges": json.dumps(self.limit_ranges) if self.limit_ranges else None,
            "last_seen": self.last_seen.isoformat(),
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class Pod:
    """
    Represents a Kubernetes pod.
    """

    # Core identification
    id: str  # Unique identifier
    name: str
    namespace: str
    cluster_id: str  # Parent cluster resource ID

    # Pod Specification
    containers: list[dict[str, Any]] = field(default_factory=list)  # Container details
    init_containers: list[dict[str, Any]] = field(default_factory=list)
    volumes: list[dict[str, Any]] = field(default_factory=list)
    service_account: str | None = None

    # Status
    phase: str = "Unknown"  # "Pending" | "Running" | "Succeeded" | "Failed" | "Unknown"
    conditions: list[dict[str, Any]] = field(default_factory=list)  # Ready, Initialized, etc.
    pod_ip: str | None = None
    host_ip: str | None = None
    node_name: str | None = None

    # Resource Usage
    cpu_requests: str | None = None
    cpu_limits: str | None = None
    memory_requests: str | None = None
    memory_limits: str | None = None

    # Ownership
    owner_kind: str | None = None  # "Deployment" | "StatefulSet" | "DaemonSet" | "Job"
    owner_name: str | None = None

    # Metadata
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None
    started_at: datetime | None = None

    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json

        return {
            "id": self.id,
            "name": self.name,
            "namespace": self.namespace,
            "cluster_id": self.cluster_id,
            "containers": json.dumps(self.containers),
            "init_containers": json.dumps(self.init_containers),
            "volumes": json.dumps(self.volumes),
            "service_account": self.service_account,
            "phase": self.phase,
            "conditions": json.dumps(self.conditions),
            "pod_ip": self.pod_ip,
            "host_ip": self.host_ip,
            "node_name": self.node_name,
            "cpu_requests": self.cpu_requests,
            "cpu_limits": self.cpu_limits,
            "memory_requests": self.memory_requests,
            "memory_limits": self.memory_limits,
            "owner_kind": self.owner_kind,
            "owner_name": self.owner_name,
            "labels": json.dumps(self.labels) if self.labels else "{}",
            "annotations": json.dumps(self.annotations) if self.annotations else "{}",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_seen": self.last_seen.isoformat(),
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class ManagedIdentity:
    """
    Represents an Azure Managed Identity (system-assigned or user-assigned).
    Used to show how resources authenticate to other resources.
    """

    # Core identification
    id: str  # Azure resource ID
    name: str
    identity_type: str  # "SystemAssigned" | "UserAssigned"

    # Identity details
    principal_id: str | None = None  # Azure AD object ID
    client_id: str | None = None  # Application ID
    tenant_id: str | None = None

    # Location and organization
    region: str | None = None
    resource_group: str | None = None
    subscription_id: str | None = None

    # Associated resource (for system-assigned identities)
    assigned_to_resource_id: str | None = None
    assigned_to_resource_type: str | None = None

    # Metadata
    tags: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None

    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json

        return {
            "id": self.id,
            "name": self.name,
            "identity_type": self.identity_type,
            "principal_id": self.principal_id,
            "client_id": self.client_id,
            "tenant_id": self.tenant_id,
            "region": self.region,
            "resource_group": self.resource_group,
            "subscription_id": self.subscription_id,
            "assigned_to_resource_id": self.assigned_to_resource_id,
            "assigned_to_resource_type": self.assigned_to_resource_type,
            "tags": json.dumps(self.tags) if self.tags else "{}",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat(),
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class ServicePrincipal:
    """
    Represents an Azure Service Principal.
    Used to show how applications and automation authenticate to Azure resources.
    """

    # Core identification
    id: str  # Azure AD object ID
    app_id: str  # Application (client) ID
    display_name: str

    # Identity details
    tenant_id: str | None = None
    app_owner_organization_id: str | None = None

    # Service Principal type
    service_principal_type: str = "Application"  # "Application" | "ManagedIdentity" | "Legacy"

    # Credentials (metadata only, no secrets)
    password_credentials_count: int = 0
    key_credentials_count: int = 0

    # OAuth2 permissions
    app_roles: list[dict[str, Any]] = field(default_factory=list)
    oauth2_permissions: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None

    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json

        return {
            "id": self.id,
            "app_id": self.app_id,
            "display_name": self.display_name,
            "tenant_id": self.tenant_id,
            "app_owner_organization_id": self.app_owner_organization_id,
            "service_principal_type": self.service_principal_type,
            "password_credentials_count": self.password_credentials_count,
            "key_credentials_count": self.key_credentials_count,
            "app_roles": json.dumps(self.app_roles),
            "oauth2_permissions": json.dumps(self.oauth2_permissions),
            "enabled": self.enabled,
            "tags": json.dumps(self.tags) if self.tags else "[]",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat(),
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class AppRegistration:
    """
    Represents an Azure AD App Registration.
    Used to show application identity configuration and how apps access resources.
    """

    # Core identification
    id: str  # Azure AD object ID
    app_id: str  # Application (client) ID
    display_name: str

    # Identity details
    tenant_id: str | None = None
    publisher_domain: str | None = None
    sign_in_audience: str = (
        "AzureADMyOrg"  # "AzureADMyOrg" | "AzureADMultipleOrgs" | "AzureADandPersonalMicrosoftAccount"
    )

    # URIs
    identifier_uris: list[str] = field(default_factory=list)
    redirect_uris: list[str] = field(default_factory=list)
    home_page_url: str | None = None
    logout_url: str | None = None

    # API permissions
    required_resource_access: list[dict[str, Any]] = field(default_factory=list)  # API permissions

    # Credentials (metadata only, no secrets)
    password_credentials_count: int = 0
    key_credentials_count: int = 0

    # Exposed API
    app_roles: list[dict[str, Any]] = field(default_factory=list)
    oauth2_permissions: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None

    # Discovery
    last_seen: datetime = field(default_factory=datetime.utcnow)
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def to_neo4j_properties(self) -> dict[str, Any]:
        """Convert to Neo4j node properties"""
        import json

        return {
            "id": self.id,
            "app_id": self.app_id,
            "display_name": self.display_name,
            "tenant_id": self.tenant_id,
            "publisher_domain": self.publisher_domain,
            "sign_in_audience": self.sign_in_audience,
            "identifier_uris": json.dumps(self.identifier_uris) if self.identifier_uris else "[]",
            "redirect_uris": json.dumps(self.redirect_uris) if self.redirect_uris else "[]",
            "home_page_url": self.home_page_url,
            "logout_url": self.logout_url,
            "required_resource_access": json.dumps(self.required_resource_access),
            "password_credentials_count": self.password_credentials_count,
            "key_credentials_count": self.key_credentials_count,
            "app_roles": json.dumps(self.app_roles),
            "oauth2_permissions": json.dumps(self.oauth2_permissions),
            "tags": json.dumps(self.tags) if self.tags else "[]",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat(),
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class DiscoveryResult:
    """
    Results from a resource discovery operation.
    """

    resources: list[DiscoveredResource] = field(default_factory=list)
    dependencies: list[ResourceDependency] = field(default_factory=list)
    applications: list[Application] = field(default_factory=list)
    repositories: list[Repository] = field(default_factory=list)
    deployments: list[Deployment] = field(default_factory=list)
    namespaces: list[Namespace] = field(default_factory=list)
    pods: list[Pod] = field(default_factory=list)
    managed_identities: list[ManagedIdentity] = field(default_factory=list)
    service_principals: list[ServicePrincipal] = field(default_factory=list)
    app_registrations: list[AppRegistration] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    subscription_id: str | None = None
    discovery_started_at: datetime = field(default_factory=datetime.utcnow)
    discovery_completed_at: datetime | None = None

    # Internal tracking sets for efficient duplicate detection (not serialized)
    _resource_ids: set[str] = field(default_factory=set, init=False, repr=False)
    _dependency_pairs: set[tuple[str, str]] = field(default_factory=set, init=False, repr=False)

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
    def namespace_count(self) -> int:
        """Total namespaces discovered"""
        return len(self.namespaces)

    @property
    def pod_count(self) -> int:
        """Total pods discovered"""
        return len(self.pods)

    @property
    def managed_identity_count(self) -> int:
        """Total managed identities discovered"""
        return len(self.managed_identities)

    @property
    def service_principal_count(self) -> int:
        """Total service principals discovered"""
        return len(self.service_principals)

    @property
    def app_registration_count(self) -> int:
        """Total app registrations discovered"""
        return len(self.app_registrations)

    @property
    def has_errors(self) -> bool:
        """Check if discovery had errors"""
        return len(self.errors) > 0

    def add_resource(self, resource: DiscoveredResource) -> None:
        """
        Add a discovered resource, avoiding duplicates.
        
        A resource is considered a duplicate if another resource with the same ID
        already exists in the result set. Uses an internal set for O(1) duplicate
        detection for better performance with large resource sets.
        
        Args:
            resource: The resource to add
        """
        # Check if resource already exists by ID (O(1) lookup)
        if resource.id in self._resource_ids:
            # Resource already exists, skip adding
            return
        
        self._resource_ids.add(resource.id)
        self.resources.append(resource)

    def add_dependency(self, dependency: ResourceDependency) -> None:
        """
        Add a discovered dependency, avoiding duplicates.
        
        A dependency is considered a duplicate if another dependency with the same
        source_id and target_id already exists. Uses an internal set for O(1) 
        duplicate detection for better performance with large dependency sets.
        
        Args:
            dependency: The dependency to add
        """
        # Check if dependency already exists (O(1) lookup)
        dep_pair = (dependency.source_id, dependency.target_id)
        if dep_pair in self._dependency_pairs:
            # Dependency already exists, skip adding
            return
        
        self._dependency_pairs.add(dep_pair)
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

    def add_namespace(self, namespace: Namespace) -> None:
        """Add a discovered namespace"""
        self.namespaces.append(namespace)

    def add_pod(self, pod: Pod) -> None:
        """Add a discovered pod"""
        self.pods.append(pod)

    def add_managed_identity(self, identity: ManagedIdentity) -> None:
        """Add a discovered managed identity"""
        self.managed_identities.append(identity)

    def add_service_principal(self, principal: ServicePrincipal) -> None:
        """Add a discovered service principal"""
        self.service_principals.append(principal)

    def add_app_registration(self, registration: AppRegistration) -> None:
        """Add a discovered app registration"""
        self.app_registrations.append(registration)

    def add_error(self, error: str) -> None:
        """Add an error message"""
        self.errors.append(error)

    def complete(self) -> None:
        """Mark discovery as completed"""
        self.discovery_completed_at = datetime.now(UTC)

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
            f"{self.namespace_count} namespaces, "
            f"{self.pod_count} pods, "
            f"{self.managed_identity_count} managed identities, "
            f"{self.service_principal_count} service principals, "
            f"{self.app_registration_count} app registrations, "
            f"{len(self.errors)} errors, "
            f"duration: {duration}"
        )
