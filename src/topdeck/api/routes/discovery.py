"""
Discovery API endpoints.

Provides API endpoints for managing automated resource discovery.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from topdeck.common.logging_config import get_logger
from topdeck.common.scheduler import get_scheduler

logger = get_logger(__name__)


# Pydantic models for API responses
class DiscoveryStatusResponse(BaseModel):
    """Response model for discovery status."""

    scheduler_running: bool
    discovery_in_progress: bool
    last_discovery_time: str | None
    interval_hours: int
    enabled_providers: dict[str, bool]


class DiscoveryTriggerResponse(BaseModel):
    """Response model for manual discovery trigger."""

    status: str
    message: str
    last_run: str | None = None


# Create router
router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


@router.get("/status", response_model=DiscoveryStatusResponse)
async def get_discovery_status() -> DiscoveryStatusResponse:
    """
    Get the status of the automated discovery scheduler.

    Returns information about:
    - Whether the scheduler is running
    - Whether discovery is currently in progress
    - When the last discovery ran
    - The configured scan interval
    - Which cloud providers are enabled and have credentials
    """
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()

        return DiscoveryStatusResponse(
            scheduler_running=status["scheduler_running"],
            discovery_in_progress=status["discovery_in_progress"],
            last_discovery_time=status["last_discovery_time"],
            interval_hours=status["interval_hours"],
            enabled_providers=status["enabled_providers"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get discovery status: {str(e)}"
        ) from e


@router.post("/trigger", response_model=DiscoveryTriggerResponse)
async def trigger_discovery() -> DiscoveryTriggerResponse:
    """
    Manually trigger a resource discovery scan.

    This will start a discovery scan immediately, regardless of the schedule.
    If a discovery is already in progress, this will return an error.
    """
    try:
        scheduler = get_scheduler()
        result = await scheduler.trigger_manual_discovery()

        return DiscoveryTriggerResponse(
            status=result["status"],
            message=result["message"],
            last_run=result.get("last_run"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger discovery: {str(e)}") from e


class RepositoryScanResponse(BaseModel):
    """Response model for repository scanning."""

    status: str
    message: str
    projects_scanned: list[str] | None = None
    repositories_scanned: int
    dependencies_created: int
    namespaces_found: list[str]
    topics_found: list[str]


@router.post("/scan-repositories", response_model=RepositoryScanResponse)
async def scan_repositories(scan_all_projects: bool = False) -> RepositoryScanResponse:
    """
    Scan Azure DevOps repositories for Service Bus and resource dependencies.

    This endpoint:
    1. Retrieves repositories from Azure DevOps (single project or all projects)
    2. Scans configuration files (appsettings.json, .env, etc.) for connection strings
    3. Finds Service Bus topics/queues referenced in code
    4. Creates dependencies between App Services and Service Bus resources
    5. Only matches against resources already discovered in your subscription

    Args:
        scan_all_projects: If True, scans all projects in the organization.
                          If False, only scans the configured project.

    Requires Azure DevOps credentials to be configured in environment variables.
    """
    try:
        from topdeck.common.config import settings
        from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer
        from topdeck.discovery.azure.code_scanner import CodeRepositoryScanner
        from topdeck.storage.neo4j_client import Neo4jClient

        # Validate Azure DevOps configuration
        org_required = settings.azure_devops_organization
        pat_required = settings.azure_devops_pat
        
        if not org_required:
            raise HTTPException(
                status_code=400,
                detail="Azure DevOps organization not configured. Set AZURE_DEVOPS_ORGANIZATION."
            )
        
        if not pat_required:
            raise HTTPException(
                status_code=400,
                detail="Azure DevOps PAT not configured. Set AZURE_DEVOPS_PAT."
            )

        # Project is only required if not scanning all projects
        if not scan_all_projects and not settings.azure_devops_project:
            raise HTTPException(
                status_code=400,
                detail="Azure DevOps project not configured. Set AZURE_DEVOPS_PROJECT or use scan_all_projects=true."
            )

        # Get discovered resources from Neo4j
        neo4j_client = Neo4jClient(
            settings.neo4j_uri,
            settings.neo4j_username,
            settings.neo4j_password
        )
        
        with neo4j_client.session() as session:
            # Get all resources
            result = session.run(
                """
                MATCH (r:Resource)
                RETURN r.id as id, r.name as name, r.resource_type as resource_type, 
                       r.properties as properties
                """
            )
            
            discovered_resources = {}
            app_services = []
            aks_clusters = []
            all_namespaces = set()
            all_topics = set()
            
            for record in result:
                # properties might be a dict or JSON string from Neo4j
                props = record["properties"] if record["properties"] else {}
                # If it's a string, parse it as JSON
                if isinstance(props, str):
                    import json
                    props = json.loads(props) if props else {}
                resource_obj = type('Resource', (), {
                    'id': record["id"],
                    'name': record["name"],
                    'resource_type': record["resource_type"],
                    'properties': props
                })()
                
                discovered_resources[record["id"]] = resource_obj
                
                # Track App Services for linking
                if record["resource_type"] == "app_service":
                    app_services.append(resource_obj)
                
                # Track AKS clusters for linking (most IaC deploys to AKS)
                if record["resource_type"] == "aks":
                    aks_clusters.append(resource_obj)
                
                # Track Service Bus resources for reporting
                if record["resource_type"] == "servicebus_namespace":
                    all_namespaces.add(record["name"])
                    # Get topics from properties if available
                    # properties might be a dict or JSON string from Neo4j
                    namespace_props = record["properties"] if record["properties"] else {}
                    if isinstance(namespace_props, str):
                        import json
                        namespace_props = json.loads(namespace_props) if namespace_props else {}
                    if "topics" in namespace_props:
                        topics = namespace_props.get("topics", [])
                        if isinstance(topics, list):
                            for topic in topics:
                                if isinstance(topic, dict):
                                    all_topics.add(topic.get("name", ""))

        # Scan repositories based on mode
        dependencies = []
        projects_scanned = []
        
        if scan_all_projects:
            # Scan all projects in the organization
            scanner = CodeRepositoryScanner(
                organization=settings.azure_devops_organization,
                project=None,  # None means scan all projects
                personal_access_token=settings.azure_devops_pat,
            )
            
            # Get scan results
            scan_results = await scanner.scan_all_projects_for_servicebus(
                discovered_resources=discovered_resources
            )
            
            projects_scanned = scan_results.get("projects_scanned", [])
            
            # Create dependencies from scan results
            # For each repository that found Service Bus references
            for repo_result in scan_results.get("repository_scan_results", []):
                project_name = repo_result["project"]
                repo_id = repo_result["repository_id"]
                repo_name = repo_result["repository_name"]
                repo_scan_results = repo_result["scan_results"]
                
                # Try to find matching compute resource (App Service or AKS) for this repository
                compute_resource_id = None
                compute_resource_name = None
                compute_resource_type = None
                repo_name_lower = repo_name.lower()
                
                # First try to match App Services
                for app in app_services:
                    app_name_lower = app.name.lower()
                    # Match by name similarity
                    if repo_name_lower in app_name_lower or app_name_lower in repo_name_lower:
                        compute_resource_id = app.id
                        compute_resource_name = app.name
                        compute_resource_type = "App Service"
                        logger.info(f"Matched repository {project_name}/{repo_name} to App Service {app.name}")
                        break
                
                # If no App Service match, try AKS clusters (most IaC deploys to AKS)
                if not compute_resource_id:
                    for aks in aks_clusters:
                        aks_name_lower = aks.name.lower()
                        # Match by name similarity
                        if repo_name_lower in aks_name_lower or aks_name_lower in repo_name_lower:
                            compute_resource_id = aks.id
                            compute_resource_name = aks.name
                            compute_resource_type = "AKS Cluster"
                            logger.info(f"Matched repository {project_name}/{repo_name} to AKS cluster {aks.name}")
                            break
                
                # If we found a matching compute resource, create dependencies
                if compute_resource_id:
                    repo_dependencies = await scanner.create_dependencies_from_scan(
                        repository_id=repo_id,
                        app_resource_id=compute_resource_id,  # Works for both App Service and AKS
                        scan_results=repo_scan_results,
                        discovered_resources=discovered_resources,
                    )
                    dependencies.extend(repo_dependencies)
                    logger.info(
                        f"Created {len(repo_dependencies)} dependencies from {project_name}/{repo_name} "
                        f"to {compute_resource_type} {compute_resource_name}"
                    )
                else:
                    logger.info(
                        f"No matching compute resource (App Service or AKS) found for repository {project_name}/{repo_name} "
                        f"(found {len(repo_scan_results.get('namespaces', []))} Service Bus namespaces)"
                    )
            
            scanner.close()
            
        else:
            # Scan single project (original behavior)
            devops = AzureDevOpsDiscoverer(
                organization=settings.azure_devops_organization,
                project=settings.azure_devops_project,
                personal_access_token=settings.azure_devops_pat,
            )
            
            # Combine App Services and AKS clusters for linking
            compute_resources = app_services + aks_clusters
            
            dependencies = await devops.scan_repositories_for_dependencies(
                discovered_resources=discovered_resources,
                app_service_resources=compute_resources,  # Now includes both App Services and AKS
            )
            
            projects_scanned = [settings.azure_devops_project] if settings.azure_devops_project else []

        # Store dependencies in Neo4j
        repos_scanned = 0
        if dependencies:
            with neo4j_client.session() as session:
                for dep in dependencies:
                    # Check if dependency already exists
                    existing = session.run(
                        """
                        MATCH (source:Resource {id: $source_id})
                        MATCH (target:Resource {id: $target_id})
                        MATCH (source)-[r:DEPENDS_ON]->(target)
                        WHERE r.discovered_method = $method
                        RETURN r
                        """,
                        source_id=dep.source_id,
                        target_id=dep.target_id,
                        method=dep.discovered_method,
                    ).single()
                    
                    if not existing:
                        # Create new dependency
                        session.run(
                            """
                            MATCH (source:Resource {id: $source_id})
                            MATCH (target:Resource {id: $target_id})
                            MERGE (source)-[r:DEPENDS_ON]->(target)
                            SET r.category = $category,
                                r.dependency_type = $dependency_type,
                                r.strength = $strength,
                                r.discovered_method = $discovered_method,
                                r.description = $description,
                                r.discovered_at = datetime()
                            """,
                            source_id=dep.source_id,
                            target_id=dep.target_id,
                            category=dep.category.value if hasattr(dep.category, 'value') else str(dep.category),
                            dependency_type=dep.dependency_type.value if hasattr(dep.dependency_type, 'value') else str(dep.dependency_type),
                            strength=dep.strength,
                            discovered_method=dep.discovered_method,
                            description=dep.description,
                        )
                        repos_scanned += 1

        return RepositoryScanResponse(
            status="success",
            message=f"Scanned {len(projects_scanned)} project(s) and created {len(dependencies)} new dependencies",
            projects_scanned=projects_scanned if scan_all_projects else None,
            repositories_scanned=repos_scanned,
            dependencies_created=len(dependencies),
            namespaces_found=list(all_namespaces),
            topics_found=list(all_topics)[:20],  # Limit to first 20 for response size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan repositories: {str(e)}"
        ) from e
