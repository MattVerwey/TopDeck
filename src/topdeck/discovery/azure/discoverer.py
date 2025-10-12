"""
Azure Resource Discoverer.

Main orchestrator for discovering Azure resources across subscriptions.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.core.exceptions import AzureError

from ..models import DiscoveryResult, DiscoveredResource, ResourceDependency, Application, Repository, Deployment
from .mapper import AzureResourceMapper
from .devops import AzureDevOpsDiscoverer
from .resources import (
    discover_compute_resources,
    discover_networking_resources,
    discover_data_resources,
    discover_config_resources,
)


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
        credential: Optional[Any] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize Azure discoverer.
        
        Args:
            subscription_id: Azure subscription ID
            credential: Azure credential (if None, uses DefaultAzureCredential)
            tenant_id: Azure tenant ID (for service principal auth)
            client_id: Azure client ID (for service principal auth)
            client_secret: Azure client secret (for service principal auth)
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
    
    async def discover_all_resources(
        self,
        resource_groups: Optional[List[str]] = None,
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
            print(f"🔍 Discovering resources in subscription {self.subscription_id}...")
            
            resources_iterator = self.resource_client.resources.list()
            all_resources = []
            
            for resource in resources_iterator:
                # Filter by resource group if specified
                if resource_groups:
                    resource_rg = self.mapper.extract_resource_group(resource.id)
                    if resource_rg not in resource_groups:
                        continue
                
                all_resources.append(resource)
            
            print(f"   Found {len(all_resources)} resources")
            
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
                    print(f"   ⚠️  {error_msg}")
            
            # Discover dependencies
            print("🔗 Analyzing dependencies...")
            dependencies = await self._discover_dependencies(result.resources)
            for dep in dependencies:
                result.add_dependency(dep)
            
            print(f"   Found {len(dependencies)} dependencies")
            
            # Infer applications from resources
            print("📱 Inferring applications from resources...")
            applications = await self._infer_applications(result.resources)
            for app in applications:
                result.add_application(app)
            
            print(f"   Found {len(applications)} applications")
            
        except AzureError as e:
            error_msg = f"Azure API error: {e}"
            result.add_error(error_msg)
            print(f"❌ {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            result.add_error(error_msg)
            print(f"❌ {error_msg}")
        
        result.complete()
        print(f"\n✅ {result.summary()}")
        
        return result
    
    async def _discover_dependencies(
        self,
        resources: List[DiscoveredResource],
    ) -> List[ResourceDependency]:
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
        dependencies = []
        
        # Create resource lookup by ID
        resource_by_id = {r.id: r for r in resources}
        
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
                            ResourceDependency,
                            DependencyCategory,
                            DependencyType,
                        )
                        
                        dep = ResourceDependency(
                            source_id=resource.id,
                            target_id=other.id,
                            category=DependencyCategory.DATA,
                            dependency_type=DependencyType.REQUIRED,
                            strength=0.9,
                            discovered_method="heuristic",
                            description=f"App Service likely depends on SQL Database in same RG",
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
                            ResourceDependency,
                            DependencyCategory,
                            DependencyType,
                        )
                        
                        dep = ResourceDependency(
                            source_id=resource.id,
                            target_id=other.id,
                            category=DependencyCategory.DATA,
                            dependency_type=DependencyType.OPTIONAL,
                            strength=0.6,
                            discovered_method="heuristic",
                            description=f"AKS may use Storage Account for persistent volumes",
                        )
                        dependencies.append(dep)
        
        return dependencies
    
    async def _infer_applications(
        self,
        resources: List[DiscoveredResource],
    ) -> List[Application]:
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
                'aks', 'app_service', 'virtual_machine', 
                'container_instance', 'function_app'
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
                    if 'version' in deployment_metadata:
                        app.current_version = deployment_metadata['version']
                    if 'deployed_at' in deployment_metadata:
                        if isinstance(deployment_metadata['deployed_at'], datetime):
                            app.last_deployed = deployment_metadata['deployed_at']
                    if 'deployed_by' in deployment_metadata:
                        app.last_deployed_by = deployment_metadata['deployed_by']
                    if 'repository_url' in deployment_metadata:
                        app.repository_url = deployment_metadata['repository_url']
                
                applications.append(app)
                seen_app_ids.add(app.id)
        
        return applications
    
    async def discover_with_devops(
        self,
        organization: str,
        project: str,
        personal_access_token: Optional[str] = None,
        resource_groups: Optional[List[str]] = None,
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
            print(f"📚 Discovering repositories from Azure DevOps...")
            repositories = await self.devops_discoverer.discover_repositories()
            for repo in repositories:
                result.add_repository(repo)
            print(f"   Found {len(repositories)} repositories")
            
            print(f"🚀 Discovering deployments from Azure DevOps...")
            deployments = await self.devops_discoverer.discover_deployments()
            for deployment in deployments:
                result.add_deployment(deployment)
            print(f"   Found {len(deployments)} deployments")
            
            print(f"📱 Discovering applications from Azure DevOps...")
            devops_applications = await self.devops_discoverer.discover_applications()
            for app in devops_applications:
                result.add_application(app)
            print(f"   Found {len(devops_applications)} applications from DevOps")
            
        except Exception as e:
            error_msg = f"Failed to discover from Azure DevOps: {e}"
            result.add_error(error_msg)
            print(f"   ⚠️  {error_msg}")
        
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
