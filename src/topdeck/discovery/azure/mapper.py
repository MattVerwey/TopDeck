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
        # Compute Resources
        "Microsoft.Compute/virtualMachines": "virtual_machine",
        "Microsoft.Compute/virtualMachineScaleSets": "vm_scale_set",
        "Microsoft.Compute/availabilitySets": "availability_set",
        "Microsoft.Compute/disks": "managed_disk",
        "Microsoft.Compute/snapshots": "disk_snapshot",
        "Microsoft.Compute/images": "vm_image",
        "Microsoft.Compute/galleries": "shared_image_gallery",
        "Microsoft.Compute/cloudServices": "cloud_service",
        
        # Web & App Services
        "Microsoft.Web/sites": "app_service",
        "Microsoft.Web/serverfarms": "app_service_plan",
        "Microsoft.Web/sites/slots": "app_service_slot",
        "Microsoft.Web/staticSites": "static_web_app",
        "Microsoft.Web/certificates": "app_service_certificate",
        "Microsoft.Web/hostingEnvironments": "app_service_environment",
        
        # Container Services
        "Microsoft.ContainerService/managedClusters": "aks",
        "Microsoft.ContainerInstance/containerGroups": "container_instance",
        "Microsoft.ContainerRegistry/registries": "container_registry",
        
        # Database Services - SQL
        "Microsoft.Sql/servers": "sql_server",
        "Microsoft.Sql/servers/databases": "sql_database",
        "Microsoft.Sql/managedInstances": "sql_managed_instance",
        "Microsoft.Sql/managedInstances/databases": "sql_managed_instance_database",
        "Microsoft.Sql/servers/elasticPools": "sql_elastic_pool",
        
        # Database Services - PostgreSQL
        "Microsoft.DBforPostgreSQL/servers": "postgresql_server",
        "Microsoft.DBforPostgreSQL/flexibleServers": "postgresql_flexible_server",
        "Microsoft.DBforPostgreSQL/serverGroupsv2": "postgresql_hyperscale",
        
        # Database Services - MySQL
        "Microsoft.DBforMySQL/servers": "mysql_server",
        "Microsoft.DBforMySQL/flexibleServers": "mysql_flexible_server",
        
        # Database Services - MariaDB
        "Microsoft.DBforMariaDB/servers": "mariadb_server",
        
        # Database Services - NoSQL & Cache
        "Microsoft.DocumentDB/databaseAccounts": "cosmos_db",
        "Microsoft.Cache/redis": "redis_cache",
        "Microsoft.Cache/redisEnterprise": "redis_enterprise",
        
        # Storage Services
        "Microsoft.Storage/storageAccounts": "storage_account",
        "Microsoft.Storage/storageAccounts/blobServices": "blob_service",
        "Microsoft.Storage/storageAccounts/fileServices": "file_service",
        "Microsoft.Storage/storageAccounts/queueServices": "queue_service",
        "Microsoft.Storage/storageAccounts/tableServices": "table_service",
        "Microsoft.DataLakeStore/accounts": "data_lake_store",
        "Microsoft.DataLakeAnalytics/accounts": "data_lake_analytics",
        
        # Networking - Core
        "Microsoft.Network/virtualNetworks": "virtual_network",
        "Microsoft.Network/virtualNetworks/subnets": "subnet",
        "Microsoft.Network/networkInterfaces": "network_interface",
        "Microsoft.Network/networkSecurityGroups": "network_security_group",
        "Microsoft.Network/publicIPAddresses": "public_ip",
        "Microsoft.Network/publicIPPrefixes": "public_ip_prefix",
        "Microsoft.Network/routeTables": "route_table",
        "Microsoft.Network/natGateways": "nat_gateway",
        
        # Networking - Load Balancing & Application Delivery
        "Microsoft.Network/loadBalancers": "load_balancer",
        "Microsoft.Network/applicationGateways": "application_gateway",
        "Microsoft.Network/frontDoors": "front_door",
        "Microsoft.Network/trafficManagerProfiles": "traffic_manager",
        
        # Networking - Connectivity
        "Microsoft.Network/virtualNetworkGateways": "vpn_gateway",
        "Microsoft.Network/localNetworkGateways": "local_network_gateway",
        "Microsoft.Network/connections": "vpn_connection",
        "Microsoft.Network/expressRouteCircuits": "express_route_circuit",
        "Microsoft.Network/expressRouteGateways": "express_route_gateway",
        "Microsoft.Network/virtualWans": "virtual_wan",
        "Microsoft.Network/vpnGateways": "vpn_gateway_v2",
        "Microsoft.Network/vpnSites": "vpn_site",
        
        # Networking - DNS & Firewall
        "Microsoft.Network/dnsZones": "dns_zone",
        "Microsoft.Network/privateDnsZones": "private_dns_zone",
        "Microsoft.Network/azureFirewalls": "azure_firewall",
        "Microsoft.Network/firewallPolicies": "firewall_policy",
        "Microsoft.Network/ddosProtectionPlans": "ddos_protection",
        
        # Networking - Private Connectivity
        "Microsoft.Network/privateEndpoints": "private_endpoint",
        "Microsoft.Network/privateLinkServices": "private_link_service",
        "Microsoft.Network/serviceEndpointPolicies": "service_endpoint_policy",
        
        # Networking - Monitoring
        "Microsoft.Network/networkWatchers": "network_watcher",
        "Microsoft.Network/networkWatchers/connectionMonitors": "connection_monitor",
        
        # Identity & Access Management
        "Microsoft.ManagedIdentity/userAssignedIdentities": "managed_identity",
        "Microsoft.Authorization/roleAssignments": "role_assignment",
        "Microsoft.Authorization/roleDefinitions": "role_definition",
        "Microsoft.Authorization/policyAssignments": "policy_assignment",
        "Microsoft.Authorization/policyDefinitions": "policy_definition",
        
        # Key Management & Secrets
        "Microsoft.KeyVault/vaults": "key_vault",
        "Microsoft.KeyVault/managedHSMs": "managed_hsm",
        
        # Messaging & Event Services
        "Microsoft.ServiceBus/namespaces": "servicebus_namespace",
        "Microsoft.ServiceBus/namespaces/topics": "servicebus_topic",
        "Microsoft.ServiceBus/namespaces/queues": "servicebus_queue",
        "Microsoft.ServiceBus/namespaces/topics/subscriptions": "servicebus_subscription",
        "Microsoft.EventHub/namespaces": "eventhub_namespace",
        "Microsoft.EventHub/namespaces/eventhubs": "eventhub",
        "Microsoft.EventGrid/topics": "eventgrid_topic",
        "Microsoft.EventGrid/domains": "eventgrid_domain",
        "Microsoft.EventGrid/systemTopics": "eventgrid_system_topic",
        "Microsoft.NotificationHubs/namespaces": "notification_hub_namespace",
        "Microsoft.NotificationHubs/namespaces/notificationHubs": "notification_hub",
        
        # Integration Services
        "Microsoft.Logic/workflows": "logic_app",
        "Microsoft.ApiManagement/service": "api_management",
        "Microsoft.DataFactory/factories": "data_factory",
        "Microsoft.DataFactory/factories/pipelines": "data_factory_pipeline",
        "Microsoft.ServiceBus/namespaces/hybridConnections": "hybrid_connection",
        "Microsoft.Relay/namespaces": "relay_namespace",
        
        # Analytics & Big Data
        "Microsoft.Synapse/workspaces": "synapse_workspace",
        "Microsoft.Databricks/workspaces": "databricks_workspace",
        "Microsoft.HDInsight/clusters": "hdinsight_cluster",
        "Microsoft.StreamAnalytics/streamingjobs": "stream_analytics",
        "Microsoft.Kusto/clusters": "data_explorer_cluster",
        "Microsoft.AnalysisServices/servers": "analysis_services",
        "Microsoft.PowerBIDedicated/capacities": "power_bi_embedded",
        
        # AI & Machine Learning
        "Microsoft.CognitiveServices/accounts": "cognitive_services",
        "Microsoft.MachineLearningServices/workspaces": "ml_workspace",
        "Microsoft.BotService/botServices": "bot_service",
        
        # IoT Services
        "Microsoft.Devices/IotHubs": "iot_hub",
        "Microsoft.Devices/provisioningServices": "iot_dps",
        "Microsoft.IoTCentral/IoTApps": "iot_central",
        "Microsoft.TimeSeriesInsights/environments": "time_series_insights",
        
        # Monitoring & Management
        "Microsoft.Insights/components": "application_insights",
        "Microsoft.OperationalInsights/workspaces": "log_analytics_workspace",
        "Microsoft.Insights/actionGroups": "action_group",
        "Microsoft.Insights/metricAlerts": "metric_alert",
        "Microsoft.Insights/activityLogAlerts": "activity_log_alert",
        "Microsoft.Insights/scheduledQueryRules": "log_alert",
        "Microsoft.Monitor/accounts": "azure_monitor_workspace",
        "Microsoft.Automation/automationAccounts": "automation_account",
        
        # DevOps & Deployment
        "Microsoft.Resources/deployments": "arm_deployment",
        "Microsoft.Resources/resourceGroups": "resource_group",
        "Microsoft.ManagedServices/registrationDefinitions": "lighthouse_definition",
        
        # Media Services
        "Microsoft.Media/mediaservices": "media_services",
        
        # Search & Cognitive
        "Microsoft.Search/searchServices": "cognitive_search",
        
        # Backup & Recovery
        "Microsoft.RecoveryServices/vaults": "recovery_services_vault",
        "Microsoft.DataProtection/backupVaults": "backup_vault",
        
        # Migration Services
        "Microsoft.Migrate/assessmentProjects": "migrate_project",
        "Microsoft.Migrate/migrateProjects": "azure_migrate",
        
        # Batch & HPC
        "Microsoft.Batch/batchAccounts": "batch_account",
        
        # Blockchain
        "Microsoft.Blockchain/blockchainMembers": "blockchain_service",
        
        # Security
        "Microsoft.Security/securityContacts": "security_contact",
        "Microsoft.Security/assessments": "security_assessment",
        
        # Hybrid & Multi-Cloud
        "Microsoft.HybridCompute/machines": "arc_server",
        "Microsoft.Kubernetes/connectedClusters": "arc_kubernetes",
        "Microsoft.AzureStackHCI/clusters": "azure_stack_hci",
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
    def map_resource(azure_resource: Any) -> DiscoveredResource:
        """
        Map an Azure SDK resource object to a DiscoveredResource.

        This is a convenience method that extracts common properties from
        Azure SDK resource objects and calls map_azure_resource.

        Args:
            azure_resource: Azure SDK resource object (from Azure Management SDKs)

        Returns:
            DiscoveredResource instance
        """
        # Extract properties from Azure SDK resource object
        resource_id = azure_resource.id if hasattr(azure_resource, "id") else ""
        resource_name = azure_resource.name if hasattr(azure_resource, "name") else ""
        resource_type = azure_resource.type if hasattr(azure_resource, "type") else ""
        location = azure_resource.location if hasattr(azure_resource, "location") else ""
        tags = azure_resource.tags if hasattr(azure_resource, "tags") else None
        provisioning_state = (
            azure_resource.provisioning_state
            if hasattr(azure_resource, "provisioning_state")
            else None
        )

        # Extract additional properties specific to the resource
        properties: dict[str, Any] = {}

        # Call the main mapping method
        return AzureResourceMapper.map_azure_resource(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
            location=location,
            tags=tags,
            properties=properties,
            provisioning_state=provisioning_state,
        )

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
    def normalize_resource_name(name: str) -> str:
        """
        Normalize a resource name for comparison.
        
        Extracts the base name from FQDNs and hostnames.
        For example:
        - "myservicebus.servicebus.windows.net" -> "myservicebus"
        - "mystorage.blob.core.windows.net" -> "mystorage"
        - "myvm" -> "myvm"
        
        Args:
            name: Resource name, hostname, or FQDN
            
        Returns:
            Normalized base name
        """
        if not name:
            return ""
        
        # Remove common Azure service suffixes
        azure_suffixes = [
            ".servicebus.windows.net",
            ".blob.core.windows.net",
            ".queue.core.windows.net",
            ".table.core.windows.net",
            ".file.core.windows.net",
            ".database.windows.net",
            ".redis.cache.windows.net",
            ".azurewebsites.net",
            ".vault.azure.net",
            ".documents.azure.com",
        ]
        
        name_lower = name.lower()
        for suffix in azure_suffixes:
            if name_lower.endswith(suffix):
                return name[:len(name) - len(suffix)]
        
        # If it looks like a FQDN, extract the first part
        if "." in name and not name.replace(".", "").replace("-", "").isdigit():
            # Not an IP address, likely a hostname
            parts = name.split(".")
            return parts[0]
        
        return name
    
    @staticmethod
    def extract_hostname_from_endpoint(endpoint: str) -> str | None:
        """
        Extract hostname from an endpoint URL.
        
        Args:
            endpoint: Endpoint URL (e.g., "sb://mybus.servicebus.windows.net/")
            
        Returns:
            Extracted hostname or None
        """
        if not endpoint:
            return None
        
        # Remove protocol if present
        if "://" in endpoint:
            endpoint = endpoint.split("://", 1)[1]
        
        # Remove path if present
        if "/" in endpoint:
            endpoint = endpoint.split("/", 1)[0]
        
        # Remove port if present
        if ":" in endpoint:
            endpoint = endpoint.split(":", 1)[0]
        
        return endpoint if endpoint else None
    
    @staticmethod
    def names_match(name1: str, name2: str) -> bool:
        """
        Check if two resource names match, accounting for different formats.
        
        This handles cases where resources may be referenced by:
        - Short name (e.g., "myresource")
        - FQDN (e.g., "myresource.servicebus.windows.net")
        - Endpoint URL (e.g., "sb://myresource.servicebus.windows.net/")
        
        Args:
            name1: First name to compare
            name2: Second name to compare
            
        Returns:
            True if names match, False otherwise
        """
        if not name1 or not name2:
            return False
        
        # Direct match
        if name1 == name2:
            return True
        
        # Normalize and compare
        normalized1 = AzureResourceMapper.normalize_resource_name(name1)
        normalized2 = AzureResourceMapper.normalize_resource_name(name2)
        
        return normalized1.lower() == normalized2.lower()

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
