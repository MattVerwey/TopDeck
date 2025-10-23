"""
Azure Resource Discoverer.

Main orchestrator for discovering Azure resources across subscriptions.
"""

import logging
from datetime import datetime
from typing import Any

from azure.core.exceptions import AzureError
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

from ...common.cache import Cache, CacheConfig
from ...common.worker_pool import WorkerPool, WorkerPoolConfig
from ..models import Application, DiscoveredResource, DiscoveryResult, ResourceDependency
from .devops import AzureDevOpsDiscoverer
from .mapper import AzureResourceMapper
from .resources import (
    discover_compute_resources,
    discover_config_resources,
    discover_data_resources,
    discover_messaging_resources,
    discover_networking_resources,
)

logger = logging.getLogger(__name__)


class AzureDiscoverer:
    """
    Main class for discovering Azure resources.

    Supports:
    - Multiple subscriptions
    - Multiple resource types (compute, networking, data, config)
    - Async/parallel discovery
    - Relationship detection
    """

    def __init__(
        self,
        subscription_id: str,
        credential: Any | None = None,
        tenant_id: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        enable_parallel: bool = True,
        max_workers: int = 5,
        enable_cache: bool = False,
        cache_config: CacheConfig | None = None,
    ):
        """
        Initialize Azure discoverer.

        Args:
            subscription_id: Azure subscription ID
            credential: Azure credential (if None, uses DefaultAzureCredential)
            tenant_id: Azure tenant ID (for service principal auth)
            client_id: Azure client ID (for service principal auth)
            client_secret: Azure client secret (for service principal auth)
            enable_parallel: Enable parallel discovery (default: True)
            max_workers: Maximum concurrent workers for parallel discovery
            enable_cache: Enable Redis caching (default: False)
            cache_config: Optional cache configuration
        """
        self.subscription_id = subscription_id

        # Set up credentials
        if credential:
            self.credential = credential
        elif tenant_id and client_id and client_secret:
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
        else:
            self.credential = DefaultAzureCredential()

        # Initialize resource client
        self.resource_client = ResourceManagementClient(
            self.credential,
            self.subscription_id,
        )

        self.mapper = AzureResourceMapper()
        self.devops_discoverer = None  # Initialized when needed

        # Initialize worker pool for parallel discovery
        self.enable_parallel = enable_parallel
        if enable_parallel:
            worker_config = WorkerPoolConfig(max_workers=max_workers)
            self._worker_pool = WorkerPool(worker_config)
        else:
            self._worker_pool = None

        # Initialize cache
        self.enable_cache = enable_cache
        if enable_cache:
            self._cache = Cache(cache_config)
        else:
            self._cache = None

    async def discover_all_resources(
        self,
        resource_groups: list[str] | None = None,
    ) -> DiscoveryResult:
        """
        Discover all resources in the subscription.

        Args:
            resource_groups: Optional list of resource groups to scan
                           (if None, scans all resource groups)

        Returns:
            DiscoveryResult with discovered resources and dependencies
        """
        result = DiscoveryResult(subscription_id=self.subscription_id)

        try:
            # Get all resources using Azure SDK
            logger.info(f"Discovering resources in subscription {self.subscription_id}...")

            resources_iterator = self.resource_client.resources.list()
            all_resources = []

            for resource in resources_iterator:
                # Filter by resource group if specified
                if resource_groups:
                    resource_rg = self.mapper.extract_resource_group(resource.id)
                    if resource_rg not in resource_groups:
                        continue

                all_resources.append(resource)

            logger.info(f"Found {len(all_resources)} resources")

            # Map Azure resources to DiscoveredResource
            for resource in all_resources:
                try:
                    discovered = self.mapper.map_azure_resource(
                        resource_id=resource.id,
                        resource_name=resource.name,
                        resource_type=resource.type,
                        location=resource.location,
                        tags=resource.tags,
                        properties={},  # Simplified for now
                        provisioning_state=None,
                    )
                    result.add_resource(discovered)
                except Exception as e:
                    error_msg = f"Failed to map resource {resource.id}: {e}"
                    result.add_error(error_msg)
                    logger.warning(error_msg)

            # Discover dependencies
            logger.info("Analyzing dependencies...")
            dependencies = await self._discover_dependencies(result.resources)
            for dep in dependencies:
                result.add_dependency(dep)

            logger.info(f"Found {len(dependencies)} dependencies")

            # Infer applications from resources
            logger.info("Inferring applications from resources...")
            applications = await self._infer_applications(result.resources)
            for app in applications:
                result.add_application(app)

            logger.info(f"Found {len(applications)} applications")

        except AzureError as e:
            error_msg = f"Azure API error: {e}"
            result.add_error(error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            result.add_error(error_msg)
            logger.error(error_msg)

        result.complete()
        logger.info(result.summary())

        return result

    async def _discover_dependencies(
        self,
        resources: list[DiscoveredResource],
    ) -> list[ResourceDependency]:
        """
        Discover dependencies between resources.

        This is a simplified implementation. In production, this would:
        - Parse resource configurations
        - Analyze network connections
        - Check resource relationships in Azure

        Args:
            resources: List of discovered resources

        Returns:
            List of discovered dependencies
        """
        from .resources import detect_servicebus_dependencies

        dependencies = []

        # Create resource lookup by ID
        {r.id: r for r in resources}

        # Simple heuristic-based dependency detection
        # In production, this would use Azure SDK to get detailed configurations

        for resource in resources:
            # Example: App Services typically depend on SQL databases in same resource group
            if resource.resource_type == "app_service":
                for other in resources:
                    if (
                        other.resource_type == "sql_database"
                        and other.resource_group == resource.resource_group
                    ):
                        # Create a dependency
                        from ..models import (
                            DependencyCategory,
                            DependencyType,
                            ResourceDependency,
                        )

                        dep = ResourceDependency(
                            source_id=resource.id,
                            target_id=other.id,
                            category=DependencyCategory.DATA,
                            dependency_type=DependencyType.REQUIRED,
                            strength=0.9,
                            discovered_method="heuristic",
                            description="App Service likely depends on SQL Database in same RG",
                        )
                        dependencies.append(dep)

            # Example: AKS typically depends on storage accounts
            if resource.resource_type == "aks":
                for other in resources:
                    if (
                        other.resource_type == "storage_account"
                        and other.resource_group == resource.resource_group
                    ):
                        from ..models import (
                            DependencyCategory,
                            DependencyType,
                            ResourceDependency,
                        )

                        dep = ResourceDependency(
                            source_id=resource.id,
                            target_id=other.id,
                            category=DependencyCategory.DATA,
                            dependency_type=DependencyType.OPTIONAL,
                            strength=0.6,
                            discovered_method="heuristic",
                            description="AKS may use Storage Account for persistent volumes",
                        )
                        dependencies.append(dep)

        # Detect Service Bus messaging dependencies
        servicebus_deps = await detect_servicebus_dependencies(
            resources, self.subscription_id, self.credential
        )
        dependencies.extend(servicebus_deps)

        return dependencies

    async def _infer_applications(
        self,
        resources: list[DiscoveredResource],
    ) -> list[Application]:
        """
        Infer applications from discovered resources.

        Uses resource naming conventions and tags to identify applications.

        Args:
            resources: List of discovered resources

        Returns:
            List of inferred applications
        """
        applications = []
        seen_app_ids = set()

        # Use a placeholder devops discoverer for metadata extraction
        if not self.devops_discoverer:
            self.devops_discoverer = AzureDevOpsDiscoverer(
                organization="placeholder",
                project="placeholder",
            )

        for resource in resources:
            # Only try to infer applications from deployable resource types
            deployable_types = [
                "aks",
                "app_service",
                "virtual_machine",
                "container_instance",
                "function_app",
            ]

            if resource.resource_type not in deployable_types:
                continue

            # Try to infer application from resource
            app = self.devops_discoverer.infer_application_from_resource(
                resource_name=resource.name,
                resource_type=resource.resource_type,
                tags=resource.tags,
            )

            if app and app.id not in seen_app_ids:
                # Enhance application with deployment metadata from tags
                deployment_metadata = self.devops_discoverer.extract_deployment_metadata_from_tags(
                    resource.tags
                )

                if deployment_metadata:
                    if "version" in deployment_metadata:
                        app.current_version = deployment_metadata["version"]
                    if "deployed_at" in deployment_metadata:
                        if isinstance(deployment_metadata["deployed_at"], datetime):
                            app.last_deployed = deployment_metadata["deployed_at"]
                    if "deployed_by" in deployment_metadata:
                        app.last_deployed_by = deployment_metadata["deployed_by"]
                    if "repository_url" in deployment_metadata:
                        app.repository_url = deployment_metadata["repository_url"]

                applications.append(app)
                seen_app_ids.add(app.id)

        return applications

    async def discover_with_devops(
        self,
        organization: str,
        project: str,
        personal_access_token: str | None = None,
        resource_groups: list[str] | None = None,
    ) -> DiscoveryResult:
        """
        Discover resources along with Azure DevOps repositories and deployments.

        This method combines infrastructure discovery with code repository
        and deployment pipeline discovery to create a complete topology.

        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            personal_access_token: PAT for Azure DevOps authentication
            resource_groups: Optional list of resource groups to scan

        Returns:
            DiscoveryResult with resources, dependencies, applications, and repositories
        """
        # First, discover infrastructure resources
        result = await self.discover_all_resources(resource_groups=resource_groups)

        # Initialize DevOps discoverer
        self.devops_discoverer = AzureDevOpsDiscoverer(
            organization=organization,
            project=project,
            personal_access_token=personal_access_token,
        )

        try:
            logger.info("Discovering repositories from Azure DevOps...")
            repositories = await self.devops_discoverer.discover_repositories()
            for repo in repositories:
                result.add_repository(repo)
            logger.info(f"Found {len(repositories)} repositories")

            logger.info("Discovering deployments from Azure DevOps...")
            deployments = await self.devops_discoverer.discover_deployments()
            for deployment in deployments:
                result.add_deployment(deployment)
            logger.info(f"Found {len(deployments)} deployments")

            logger.info("Discovering applications from Azure DevOps...")
            devops_applications = await self.devops_discoverer.discover_applications()
            for app in devops_applications:
                result.add_application(app)
            logger.info(f"Found {len(devops_applications)} applications from DevOps")

        except Exception as e:
            error_msg = f"Failed to discover from Azure DevOps: {e}"
            result.add_error(error_msg)
            logger.warning(error_msg)

        return result

    async def discover_specialized_resources_parallel(
        self,
        resource_groups: list[str] | None = None,
    ) -> DiscoveryResult:
        """
        Discover specialized resources in parallel for better performance.

        This method uses a worker pool to discover compute, networking, data,
        and config resources concurrently instead of sequentially.

        Args:
            resource_groups: Optional list of resource groups to scan

        Returns:
            DiscoveryResult with discovered resources
        """
        result = DiscoveryResult(subscription_id=self.subscription_id)

        if not self.enable_parallel or not self._worker_pool:
            # Fall back to sequential discovery
            logger.warning("Parallel discovery disabled, using sequential discovery")
            return await self.discover_all_resources(resource_groups)

        logger.info(
            f"Discovering resources in parallel (max {self._worker_pool.config.max_workers} workers)..."
        )

        # Define discovery tasks
        discovery_tasks = [
            discover_compute_resources,
            discover_networking_resources,
            discover_data_resources,
            discover_config_resources,
            discover_messaging_resources,
        ]

        # Prepare arguments for each task
        task_args = [
            (self.subscription_id, self.credential),
            (self.subscription_id, self.credential),
            (self.subscription_id, self.credential),
            (self.subscription_id, self.credential),
            (self.subscription_id, self.credential),
        ]

        # Add resource_group filter to kwargs if specified
        task_kwargs = []
        for _ in discovery_tasks:
            if resource_groups and len(resource_groups) == 1:
                task_kwargs.append({"resource_group": resource_groups[0]})
            else:
                task_kwargs.append({})

        try:
            # Execute discovery tasks in parallel
            results_list = await self._worker_pool.execute(
                discovery_tasks,
                task_args,
                task_kwargs,
            )

            # Combine results
            for resources in results_list:
                for resource in resources:
                    result.add_resource(resource)

            logger.info(f"Discovered {len(result.resources)} resources across all types")

            # Discover dependencies
            logger.info("Analyzing dependencies...")
            dependencies = await self._discover_dependencies(result.resources)
            for dep in dependencies:
                result.add_dependency(dep)
            logger.info(f"Found {len(dependencies)} dependencies")

            # Infer applications
            logger.info("Inferring applications...")
            applications = await self._infer_applications(result.resources)
            for app in applications:
                result.add_application(app)
            logger.info(f"Found {len(applications)} applications")

            # Log worker pool summary
            summary = self._worker_pool.get_summary()
            if summary["failure"] > 0:
                logger.warning(f"{summary['failure']} discovery tasks failed")

        except Exception as e:
            error_msg = f"Parallel discovery error: {e}"
            result.add_error(error_msg)
            logger.error(error_msg)

        result.complete()
        logger.info(result.summary())

        return result

    async def discover_resource_group(
        self,
        resource_group_name: str,
    ) -> DiscoveryResult:
        """
        Discover all resources in a specific resource group.

        Args:
            resource_group_name: Resource group name

        Returns:
            DiscoveryResult with discovered resources
        """
        return await self.discover_all_resources(resource_groups=[resource_group_name])

    async def connect_cache(self) -> None:
        """Connect to cache if enabled."""
        if self.enable_cache and self._cache:
            await self._cache.connect()

    async def close(self) -> None:
        """Close connections and cleanup resources."""
        if self.devops_discoverer:
            await self.devops_discoverer.close()
        if self.enable_cache and self._cache:
            await self._cache.close()
