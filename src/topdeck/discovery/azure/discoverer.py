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

from ..models import DiscoveryResult, DiscoveredResource, ResourceDependency
from .mapper import AzureResourceMapper
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
