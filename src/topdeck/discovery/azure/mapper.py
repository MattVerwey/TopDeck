"""
Azure Resource Mapper.

Maps Azure SDK resource objects to TopDeck's normalized DiscoveredResource model.
"""

import re
from typing import Any

from ..connection_parser import ConnectionStringParser
from ..models import CloudProvider, DiscoveredResource, ResourceDependency, ResourceStatus


class AzureResourceMapper:
    """
    Maps Azure resources to TopDeck's normalized resource model.
    """

    # Mapping from Azure resource types to TopDeck resource types
    RESOURCE_TYPE_MAP = {
        # Compute
        "Microsoft.Compute/virtualMachines": "virtual_machine",
        "Microsoft.Web/sites": "app_service",
        "Microsoft.ContainerService/managedClusters": "aks",
        # Databases
        "Microsoft.Sql/servers/databases": "sql_database",
        "Microsoft.Sql/servers": "sql_server",
        "Microsoft.DBforPostgreSQL/servers": "postgresql_server",
        "Microsoft.DBforMySQL/servers": "mysql_server",
        "Microsoft.DocumentDB/databaseAccounts": "cosmos_db",
        # Storage
        "Microsoft.Storage/storageAccounts": "storage_account",
        # Networking
        "Microsoft.Network/loadBalancers": "load_balancer",
        "Microsoft.Network/applicationGateways": "application_gateway",
        "Microsoft.Network/virtualNetworks": "virtual_network",
        "Microsoft.Network/networkSecurityGroups": "network_security_group",
        "Microsoft.Network/publicIPAddresses": "public_ip",
        # Configuration & Secrets
        "Microsoft.KeyVault/vaults": "key_vault",
        "Microsoft.Cache/redis": "redis_cache",
        # Identity & Access
        "Microsoft.ManagedIdentity/userAssignedIdentities": "managed_identity",
        # Messaging
        "Microsoft.ServiceBus/namespaces": "servicebus_namespace",
        "Microsoft.ServiceBus/namespaces/topics": "servicebus_topic",
        "Microsoft.ServiceBus/namespaces/queues": "servicebus_queue",
        "Microsoft.ServiceBus/namespaces/topics/subscriptions": "servicebus_subscription",
    }

    @staticmethod
    def map_resource_type(azure_type: str) -> str:
        """
        Map Azure resource type to TopDeck resource type.

        Args:
            azure_type: Azure resource type (e.g., "Microsoft.Compute/virtualMachines")

        Returns:
            Normalized resource type (e.g., "virtual_machine")
        """
        return AzureResourceMapper.RESOURCE_TYPE_MAP.get(azure_type, "unknown")

    @staticmethod
    def extract_resource_group(resource_id: str) -> str | None:
        """
        Extract resource group name from Azure resource ID.

        Args:
            resource_id: Azure ARM resource ID

        Returns:
            Resource group name or None
        """
        match = re.search(r"/resourceGroups/([^/]+)", resource_id, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def extract_subscription_id(resource_id: str) -> str | None:
        """
        Extract subscription ID from Azure resource ID.

        Args:
            resource_id: Azure ARM resource ID

        Returns:
            Subscription ID or None
        """
        match = re.search(r"/subscriptions/([^/]+)", resource_id, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def map_provisioning_state_to_status(provisioning_state: str | None) -> ResourceStatus:
        """
        Map Azure provisioning state to TopDeck resource status.

        Args:
            provisioning_state: Azure provisioning state (e.g., "Succeeded", "Failed")

        Returns:
            Normalized resource status
        """
        if not provisioning_state:
            return ResourceStatus.UNKNOWN

        state_lower = provisioning_state.lower()

        if state_lower in ("succeeded", "running", "ready"):
            return ResourceStatus.RUNNING
        elif state_lower in ("stopped", "deallocated"):
            return ResourceStatus.STOPPED
        elif state_lower in ("failed", "error"):
            return ResourceStatus.ERROR
        elif state_lower in ("updating", "creating", "deleting"):
            return ResourceStatus.DEGRADED
        else:
            return ResourceStatus.UNKNOWN

    @staticmethod
    def extract_environment_from_tags(tags: dict[str, str] | None) -> str | None:
        """
        Extract environment from resource tags.

        Looks for common tag keys: environment, env, Environment, Env

        Args:
            tags: Resource tags dictionary

        Returns:
            Environment name (e.g., "prod", "staging", "dev") or None
        """
        if not tags:
            return None

        # Check common environment tag keys
        for key in ("environment", "env", "Environment", "Env", "ENVIRONMENT"):
            if key in tags:
                return tags[key].lower()

        return None

    @staticmethod
    def map_azure_resource(
        resource_id: str,
        resource_name: str,
        resource_type: str,
        location: str,
        tags: dict[str, str] | None = None,
        properties: dict[str, Any] | None = None,
        provisioning_state: str | None = None,
    ) -> DiscoveredResource:
        """
        Map an Azure resource to a DiscoveredResource.

        Args:
            resource_id: Azure ARM resource ID
            resource_name: Resource name
            resource_type: Azure resource type
            location: Azure location/region
            tags: Resource tags
            properties: Azure-specific properties
            provisioning_state: Resource provisioning state

        Returns:
            DiscoveredResource instance
        """
        return DiscoveredResource(
            id=resource_id,
            name=resource_name,
            resource_type=AzureResourceMapper.map_resource_type(resource_type),
            cloud_provider=CloudProvider.AZURE,
            region=location,
            resource_group=AzureResourceMapper.extract_resource_group(resource_id),
            subscription_id=AzureResourceMapper.extract_subscription_id(resource_id),
            status=AzureResourceMapper.map_provisioning_state_to_status(provisioning_state),
            environment=AzureResourceMapper.extract_environment_from_tags(tags),
            tags=tags or {},
            properties=properties or {},
        )

    @staticmethod
    def extract_connection_strings_from_properties(
        resource_id: str, resource_type: str, properties: dict[str, Any]
    ) -> list[ResourceDependency]:
        """
        Extract connection string-based dependencies from resource properties.

        Args:
            resource_id: Source resource ID
            resource_type: Azure resource type
            properties: Resource properties

        Returns:
            List of ResourceDependency objects discovered from connection strings
        """
        dependencies = []
        parser = ConnectionStringParser()

        # Handle different resource types
        if resource_type == "Microsoft.Web/sites":
            # App Service - check app settings for connection strings
            app_settings = properties.get("siteConfig", {}).get("appSettings", [])
            for setting in app_settings:
                if isinstance(setting, dict):
                    value = setting.get("value", "")
                    # Common connection string setting names
                    if any(
                        key in setting.get("name", "").lower()
                        for key in ["connection", "database", "storage", "redis", "cache"]
                    ):
                        conn_info = parser.parse_connection_string(value)
                        if conn_info and conn_info.host:
                            target_id = parser.extract_host_from_connection_info(conn_info)
                            if target_id:
                                dep = parser.create_dependency_from_connection(
                                    source_id=resource_id,
                                    target_id=target_id,
                                    conn_info=conn_info,
                                    description=f"App Service connection: {setting.get('name')}",
                                )
                                dependencies.append(dep)

            # Connection strings section
            connection_strings = properties.get("siteConfig", {}).get("connectionStrings", [])
            for conn_str in connection_strings:
                if isinstance(conn_str, dict):
                    value = conn_str.get("value", "")
                    conn_info = parser.parse_connection_string(value)
                    if conn_info and conn_info.host:
                        target_id = parser.extract_host_from_connection_info(conn_info)
                        if target_id:
                            dep = parser.create_dependency_from_connection(
                                source_id=resource_id,
                                target_id=target_id,
                                conn_info=conn_info,
                                description=f"Connection string: {conn_str.get('name')}",
                            )
                            dependencies.append(dep)

        elif resource_type == "Microsoft.Compute/virtualMachines":
            # VM - check extensions and custom data
            extensions = properties.get("extensions", [])
            for ext in extensions:
                if isinstance(ext, dict):
                    settings = ext.get("settings", {})
                    # Check for database or storage connections
                    for _key, value in settings.items():
                        if isinstance(value, str) and any(
                            pattern in value.lower()
                            for pattern in ["://", "database", "storage", "cache"]
                        ):
                            conn_info = parser.parse_connection_string(value)
                            if conn_info and conn_info.host:
                                target_id = parser.extract_host_from_connection_info(conn_info)
                                if target_id:
                                    dep = parser.create_dependency_from_connection(
                                        source_id=resource_id,
                                        target_id=target_id,
                                        conn_info=conn_info,
                                    )
                                    dependencies.append(dep)

        elif resource_type == "Microsoft.ContainerService/managedClusters":
            # AKS - check add-ons and configurations
            addon_profiles = properties.get("addonProfiles", {})
            for addon_name, addon_config in addon_profiles.items():
                if isinstance(addon_config, dict):
                    config = addon_config.get("config", {})
                    for _key, value in config.items():
                        if isinstance(value, str) and "://" in value:
                            conn_info = parser.parse_connection_string(value)
                            if conn_info and conn_info.host:
                                target_id = parser.extract_host_from_connection_info(conn_info)
                                if target_id:
                                    dep = parser.create_dependency_from_connection(
                                        source_id=resource_id,
                                        target_id=target_id,
                                        conn_info=conn_info,
                                        description=f"AKS addon: {addon_name}",
                                    )
                                    dependencies.append(dep)

        return dependencies
