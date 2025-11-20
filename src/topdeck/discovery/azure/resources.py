"""
Azure Resource Discovery Functions.

Specialized resource discovery for detailed property extraction.
"""

import base64
import logging

try:
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.containerservice import ContainerServiceClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.servicebus import ServiceBusManagementClient
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.web import WebSiteManagementClient
except ImportError:
    ComputeManagementClient = None
    ContainerServiceClient = None
    NetworkManagementClient = None
    StorageManagementClient = None
    WebSiteManagementClient = None
    ServiceBusManagementClient = None

try:
    from kubernetes import client as k8s_client
    from kubernetes import config as k8s_config
except ImportError:
    k8s_client = None
    k8s_config = None

from ..models import DiscoveredResource, ResourceDependency
from .mapper import AzureResourceMapper

logger = logging.getLogger(__name__)


async def discover_compute_resources(
    subscription_id: str,
    credential,
    resource_group: str | None = None,
) -> list[DiscoveredResource]:
    """
    Discover compute resources (VMs, App Services, AKS) with detailed properties.

    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        resource_group: Optional resource group filter

    Returns:
        List of DiscoveredResource objects with detailed properties
    """
    resources = []
    mapper = AzureResourceMapper()

    if ComputeManagementClient is None:
        logger.warning("Azure Compute SDK not available, skipping compute discovery")
        return resources

    try:
        compute_client = ComputeManagementClient(credential, subscription_id)

        # Discover Virtual Machines
        if resource_group:
            vms = compute_client.virtual_machines.list(resource_group)
        else:
            vms = compute_client.virtual_machines.list_all()

        for vm in vms:
            try:
                # Map basic resource
                resource = mapper.map_resource(vm)

                # Add detailed VM properties
                if hasattr(vm, "hardware_profile") and vm.hardware_profile:
                    resource.properties["vm_size"] = vm.hardware_profile.vm_size

                if hasattr(vm, "storage_profile") and vm.storage_profile:
                    if vm.storage_profile.os_disk:
                        resource.properties["os_disk_size_gb"] = (
                            vm.storage_profile.os_disk.disk_size_gb
                        )
                        resource.properties["os_type"] = vm.storage_profile.os_disk.os_type
                    if vm.storage_profile.image_reference:
                        resource.properties["image_publisher"] = (
                            vm.storage_profile.image_reference.publisher
                        )
                        resource.properties["image_offer"] = (
                            vm.storage_profile.image_reference.offer
                        )

                if hasattr(vm, "network_profile") and vm.network_profile:
                    if vm.network_profile.network_interfaces:
                        resource.properties["network_interface_ids"] = [
                            nic.id for nic in vm.network_profile.network_interfaces
                        ]

                resources.append(resource)

            except Exception as e:
                logger.error(f"Error discovering VM {vm.name}: {e}")

        logger.info(f"Discovered {len(resources)} compute resources")

    except Exception as e:
        logger.error(f"Error discovering compute resources: {e}")

    return resources


async def discover_networking_resources(
    subscription_id: str,
    credential,
    resource_group: str | None = None,
) -> list[DiscoveredResource]:
    """
    Discover networking resources (VNets, Load Balancers, NSGs) with detailed properties.

    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        resource_group: Optional resource group filter

    Returns:
        List of DiscoveredResource objects with detailed properties
    """
    resources = []
    mapper = AzureResourceMapper()

    if NetworkManagementClient is None:
        logger.warning("Azure Network SDK not available, skipping network discovery")
        return resources

    try:
        network_client = NetworkManagementClient(credential, subscription_id)

        # Discover Virtual Networks
        if resource_group:
            vnets = network_client.virtual_networks.list(resource_group)
        else:
            vnets = network_client.virtual_networks.list_all()

        for vnet in vnets:
            try:
                resource = mapper.map_resource(vnet)

                # Add detailed VNet properties
                if hasattr(vnet, "address_space") and vnet.address_space:
                    resource.properties["address_prefixes"] = vnet.address_space.address_prefixes

                if hasattr(vnet, "subnets") and vnet.subnets:
                    resource.properties["subnet_count"] = len(vnet.subnets)
                    resource.properties["subnets"] = [
                        {
                            "name": subnet.name,
                            "address_prefix": subnet.address_prefix,
                            "id": subnet.id,
                        }
                        for subnet in vnet.subnets
                    ]

                if hasattr(vnet, "enable_ddos_protection"):
                    resource.properties["ddos_protection_enabled"] = vnet.enable_ddos_protection

                resources.append(resource)

            except Exception as e:
                logger.error(f"Error discovering VNet {vnet.name}: {e}")

        # Discover Load Balancers
        if resource_group:
            lbs = network_client.load_balancers.list(resource_group)
        else:
            lbs = network_client.load_balancers.list_all()

        for lb in lbs:
            try:
                resource = mapper.map_resource(lb)

                # Add detailed Load Balancer properties
                if hasattr(lb, "frontend_ip_configurations") and lb.frontend_ip_configurations:
                    resource.properties["frontend_ip_count"] = len(lb.frontend_ip_configurations)

                if hasattr(lb, "backend_address_pools") and lb.backend_address_pools:
                    resource.properties["backend_pool_count"] = len(lb.backend_address_pools)
                    resource.properties["backend_pools"] = [
                        {"name": pool.name, "id": pool.id} for pool in lb.backend_address_pools
                    ]

                if hasattr(lb, "load_balancing_rules") and lb.load_balancing_rules:
                    resource.properties["rule_count"] = len(lb.load_balancing_rules)

                resources.append(resource)

            except Exception as e:
                logger.error(f"Error discovering Load Balancer {lb.name}: {e}")

        logger.info(f"Discovered {len(resources)} networking resources")

    except Exception as e:
        logger.error(f"Error discovering networking resources: {e}")

    return resources


async def discover_data_resources(
    subscription_id: str,
    credential,
    resource_group: str | None = None,
) -> list[DiscoveredResource]:
    """
    Discover data resources (SQL, Cosmos DB, Storage) with detailed properties.

    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        resource_group: Optional resource group filter

    Returns:
        List of DiscoveredResource objects with detailed properties
    """
    resources = []
    mapper = AzureResourceMapper()

    if StorageManagementClient is None:
        logger.warning("Azure Storage SDK not available, skipping storage discovery")
        return resources

    try:
        storage_client = StorageManagementClient(credential, subscription_id)

        # Discover Storage Accounts
        if resource_group:
            storage_accounts = storage_client.storage_accounts.list_by_resource_group(
                resource_group
            )
        else:
            storage_accounts = storage_client.storage_accounts.list()

        for storage in storage_accounts:
            try:
                resource = mapper.map_resource(storage)

                # Add detailed Storage properties
                if hasattr(storage, "sku") and storage.sku:
                    resource.properties["sku_name"] = storage.sku.name
                    resource.properties["sku_tier"] = storage.sku.tier

                if hasattr(storage, "kind"):
                    resource.properties["kind"] = storage.kind

                if hasattr(storage, "enable_https_traffic_only"):
                    resource.properties["https_only"] = storage.enable_https_traffic_only

                if hasattr(storage, "encryption") and storage.encryption:
                    resource.properties["encryption_enabled"] = True
                    if storage.encryption.services:
                        resource.properties["encrypted_services"] = []
                        if storage.encryption.services.blob:
                            resource.properties["encrypted_services"].append("blob")
                        if storage.encryption.services.file:
                            resource.properties["encrypted_services"].append("file")

                if hasattr(storage, "primary_endpoints") and storage.primary_endpoints:
                    resource.properties["blob_endpoint"] = storage.primary_endpoints.blob
                    resource.properties["queue_endpoint"] = storage.primary_endpoints.queue
                    resource.properties["table_endpoint"] = storage.primary_endpoints.table
                    resource.properties["file_endpoint"] = storage.primary_endpoints.file

                resources.append(resource)

            except Exception as e:
                logger.error(f"Error discovering Storage Account {storage.name}: {e}")

        logger.info(f"Discovered {len(resources)} data resources")

    except Exception as e:
        logger.error(f"Error discovering data resources: {e}")

    return resources


async def discover_config_resources(
    subscription_id: str,
    credential,
    resource_group: str | None = None,
) -> list[DiscoveredResource]:
    """
    Discover configuration resources (Key Vault, App Configuration) with detailed properties.

    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        resource_group: Optional resource group filter

    Returns:
        List of DiscoveredResource objects with detailed properties
    """
    resources = []

    # Key Vault discovery would require azure-mgmt-keyvault
    # App Configuration would require azure-mgmt-appconfiguration
    # For now, return empty list as these are optional SDKs

    logger.info("Config resource discovery not yet implemented")
    return resources


async def discover_messaging_resources(
    subscription_id: str,
    credential,
    resource_group: str | None = None,
) -> list[DiscoveredResource]:
    """
    Discover Service Bus namespaces, topics, queues, and subscriptions.

    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        resource_group: Optional resource group filter

    Returns:
        List of DiscoveredResource objects with detailed properties
    """
    # DIAGNOSTIC: Print to stdout to verify function is being called
    print("=" * 80)
    print("DIAGNOSTIC: discover_messaging_resources() CALLED")
    print(f"DIAGNOSTIC: subscription_id={subscription_id}")
    print(f"DIAGNOSTIC: resource_group={resource_group}")
    print(f"DIAGNOSTIC: ServiceBusManagementClient={ServiceBusManagementClient}")
    print("=" * 80)
    
    resources = []
    mapper = AzureResourceMapper()

    if ServiceBusManagementClient is None:
        logger.warning("Azure Service Bus SDK not available, skipping messaging discovery")
        print("DIAGNOSTIC: ServiceBusManagementClient is None, returning early")
        return resources

    logger.info("Starting Service Bus discovery...")
    print("DIAGNOSTIC: Starting Service Bus discovery...")
    try:
        servicebus_client = ServiceBusManagementClient(credential, subscription_id)
        print("DIAGNOSTIC: ServiceBusManagementClient created successfully")

        # Discover Service Bus namespaces
        if resource_group:
            namespaces = servicebus_client.namespaces.list_by_resource_group(resource_group)
        else:
            namespaces = servicebus_client.namespaces.list()
        
        print("DIAGNOSTIC: Namespace list retrieved, iterating...")
        namespace_count = 0
        for namespace in namespaces:
            namespace_count += 1
            print(f"DIAGNOSTIC: Processing namespace {namespace_count}: {namespace.name}")
            try:
                # Map namespace resource
                # Discover topics and queues in this namespace
                namespace_rg = mapper.extract_resource_group(namespace.id)
                print(f"DIAGNOSTIC: Namespace ID: {namespace.id}")
                print(f"DIAGNOSTIC: Extracted RG: {namespace_rg}")
                
                topics_list = []
                queues_list = []
                
                if namespace_rg:
                    print(f"DIAGNOSTIC: RG is valid, proceeding with topic/queue discovery")
                    logger.info(f"Discovering topics/queues for Service Bus namespace: {namespace.name} in RG: {namespace_rg}")
                    
                    # Discover topics
                    try:
                        logger.info(f"Attempting to list topics in namespace {namespace.name}...")
                        topics = servicebus_client.topics.list_by_namespace(
                            namespace_rg, namespace.name
                        )
                        topic_list = list(topics)
                        logger.info(f"Successfully retrieved {len(topic_list)} topics")
                        for topic in topic_list:
                            try:
                                topic_data = {
                                    "name": topic.name,
                                    "id": topic.id,
                                    "max_size_in_mb": (
                                        topic.max_size_in_megabytes
                                        if hasattr(topic, "max_size_in_megabytes")
                                        else None
                                    ),
                                    "requires_duplicate_detection": (
                                        topic.requires_duplicate_detection
                                        if hasattr(topic, "requires_duplicate_detection")
                                        else None
                                    ),
                                    "support_ordering": (
                                        topic.support_ordering
                                        if hasattr(topic, "support_ordering")
                                        else None
                                    ),
                                    "status": topic.status if hasattr(topic, "status") else None,
                                    "subscriptions": []
                                }
                                
                                # Discover subscriptions for this topic
                                try:
                                    subscriptions = servicebus_client.subscriptions.list_by_topic(
                                        namespace_rg, namespace.name, topic.name
                                    )
                                    for subscription in subscriptions:
                                        topic_data["subscriptions"].append({
                                            "name": subscription.name,
                                            "id": subscription.id,
                                            "max_delivery_count": (
                                                subscription.max_delivery_count
                                                if hasattr(subscription, "max_delivery_count")
                                                else None
                                            ),
                                            "requires_session": (
                                                subscription.requires_session
                                                if hasattr(subscription, "requires_session")
                                                else None
                                            ),
                                            "status": (
                                                subscription.status
                                                if hasattr(subscription, "status")
                                                else None
                                            ),
                                        })
                                except Exception as e:
                                    logger.error(f"Error discovering subscriptions for topic {topic.name}: {e}")
                                
                                topics_list.append(topic_data)
                            except Exception as e:
                                logger.error(f"Error discovering topic {topic.name}: {e}")
                        
                        logger.info(f"Discovered {len(topics_list)} topics in namespace {namespace.name}")
                    except Exception as e:
                        logger.error(f"Error listing topics for namespace {namespace.name}: {e}", exc_info=True)
                        logger.error(f"This may be a permissions issue. Service principal needs 'Azure Service Bus Data Receiver' or 'Service Bus Data Owner' role.")

                    # Discover queues in this namespace
                    try:
                        logger.info(f"Attempting to list queues in namespace {namespace.name}...")
                        queues = servicebus_client.queues.list_by_namespace(
                            namespace_rg, namespace.name
                        )
                        queue_list = list(queues)
                        logger.info(f"Successfully retrieved {len(queue_list)} queues")
                        for queue in queue_list:
                            try:
                                queues_list.append({
                                    "name": queue.name,
                                    "id": queue.id,
                                    "max_size_in_mb": (
                                        queue.max_size_in_megabytes
                                        if hasattr(queue, "max_size_in_megabytes")
                                        else None
                                    ),
                                    "requires_duplicate_detection": (
                                        queue.requires_duplicate_detection
                                        if hasattr(queue, "requires_duplicate_detection")
                                        else None
                                    ),
                                    "requires_session": (
                                        queue.requires_session
                                        if hasattr(queue, "requires_session")
                                        else None
                                    ),
                                    "max_delivery_count": (
                                        queue.max_delivery_count
                                        if hasattr(queue, "max_delivery_count")
                                        else None
                                    ),
                                    "status": queue.status if hasattr(queue, "status") else None,
                                })
                            except Exception as e:
                                logger.error(f"Error discovering queue {queue.name}: {e}")
                        
                        logger.info(f"Discovered {len(queues_list)} queues in namespace {namespace.name}")
                    except Exception as e:
                        logger.error(f"Error listing queues for namespace {namespace.name}: {e}", exc_info=True)
                        logger.error(f"This may be a permissions issue. Service principal needs 'Azure Service Bus Data Receiver' or 'Service Bus Data Owner' role.")
                
                # Create namespace resource with topics/queues as nested properties
                namespace_resource = mapper.map_azure_resource(
                    resource_id=namespace.id,
                    resource_name=namespace.name,
                    resource_type=namespace.type,
                    location=namespace.location,
                    tags=namespace.tags,
                    properties={
                        "sku": namespace.sku.name if namespace.sku else None,
                        "tier": namespace.sku.tier if namespace.sku else None,
                        "endpoint": (
                            namespace.service_bus_endpoint
                            if hasattr(namespace, "service_bus_endpoint")
                            else None
                        ),
                        "status": namespace.status if hasattr(namespace, "status") else None,
                        "topics": topics_list,
                        "queues": queues_list,
                        "topics_count": len(topics_list),
                        "queues_count": len(queues_list),
                    },
                    provisioning_state=(
                        namespace.provisioning_state
                        if hasattr(namespace, "provisioning_state")
                        else None
                    ),
                )
                resources.append(namespace_resource)

            except Exception as e:
                logger.error(f"Error discovering Service Bus namespace {namespace.name}: {e}")

        logger.info(f"Discovered {len(resources)} messaging resources")

    except Exception as e:
        logger.error(f"Error discovering messaging resources: {e}", exc_info=True)

    return resources


def parse_servicebus_connection_string(connection_string: str) -> dict[str, str] | None:
    """
    Parse Service Bus connection string to extract namespace information.

    Args:
        connection_string: Service Bus connection string

    Returns:
        Dictionary with 'namespace' and 'endpoint' keys, or None if not a Service Bus connection
    """
    if not connection_string or "servicebus" not in connection_string.lower():
        return None

    try:
        # Service Bus connection strings look like:
        # Endpoint=sb://namespace.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...
        parts = {}
        for part in connection_string.split(";"):
            if "=" in part:
                key, value = part.split("=", 1)
                parts[key.lower()] = value

        endpoint = parts.get("endpoint", "")
        if "sb://" in endpoint:
            # Extract namespace from endpoint: sb://namespace.servicebus.windows.net/
            namespace = endpoint.replace("sb://", "").split(".")[0]
            return {"namespace": namespace, "endpoint": endpoint}

    except Exception as e:
        logger.debug(f"Error parsing connection string: {e}")

    return None


async def get_app_service_servicebus_connections(
    subscription_id: str,
    credential,
    app_service_resources: list[DiscoveredResource],
) -> dict[str, list[str]]:
    """
    Get Service Bus connections from App Service application settings and connection strings.

    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        app_service_resources: List of App Service resources

    Returns:
        Dictionary mapping app service resource ID to list of Service Bus namespace names
    """
    connections = {}

    if WebSiteManagementClient is None:
        logger.warning("Azure Web SDK not available, skipping App Service config parsing")
        return connections

    try:
        web_client = WebSiteManagementClient(credential, subscription_id)

        for app in app_service_resources:
            app_connections = set()

            try:
                # Extract resource group and app name from resource ID
                resource_group = app.resource_group
                if not resource_group:
                    continue

                # Get application settings
                try:
                    app_settings = web_client.web_apps.list_application_settings(
                        resource_group, app.name
                    )
                    if hasattr(app_settings, "properties"):
                        for _key, value in app_settings.properties.items():
                            if value and isinstance(value, str):
                                sb_info = parse_servicebus_connection_string(value)
                                if sb_info:
                                    app_connections.add(sb_info["namespace"])
                except Exception as e:
                    logger.debug(f"Error getting app settings for {app.name}: {e}")

                # Get connection strings
                try:
                    conn_strings = web_client.web_apps.list_connection_strings(
                        resource_group, app.name
                    )
                    if hasattr(conn_strings, "properties"):
                        for _key, conn in conn_strings.properties.items():
                            if hasattr(conn, "value") and conn.value:
                                sb_info = parse_servicebus_connection_string(conn.value)
                                if sb_info:
                                    app_connections.add(sb_info["namespace"])
                except Exception as e:
                    logger.debug(f"Error getting connection strings for {app.name}: {e}")

                if app_connections:
                    connections[app.id] = list(app_connections)
                    logger.info(
                        f"Found {len(app_connections)} Service Bus connections for {app.name}"
                    )

            except Exception as e:
                logger.error(f"Error processing App Service {app.name}: {e}")

    except Exception as e:
        logger.error(f"Error getting App Service Service Bus connections: {e}")

    return connections


async def get_aks_resource_connections(
    subscription_id: str,
    credential,
    aks_resources: list[DiscoveredResource],
) -> dict[str, dict[str, list[dict]]]:
    """
    Get all resource connections from AKS cluster ConfigMaps, Secrets, and environment variables.

    Discovers connections to:
    - Service Bus (namespaces, topics, queues)
    - SQL Databases (Azure SQL, PostgreSQL, MySQL)
    - Redis Cache
    - Storage Accounts
    - Any other services via connection strings

    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        aks_resources: List of AKS cluster resources

    Returns:
        Dictionary mapping AKS resource ID to dict of resource types and their connection details
        Format: {aks_id: {resource_type: [connection_info_dict, ...]}}
    """
    from ..connection_parser import ConnectionStringParser

    connections = {}

    if ContainerServiceClient is None or k8s_client is None:
        logger.warning(
            "Azure Container or Kubernetes SDK not available, skipping AKS config parsing"
        )
        return connections

    try:
        container_client = ContainerServiceClient(credential, subscription_id)
        parser = ConnectionStringParser()

        for aks in aks_resources:
            aks_resource_connections = {}

            try:
                resource_group = aks.resource_group
                if not resource_group:
                    continue

                # Get cluster credentials
                try:
                    creds = container_client.managed_clusters.list_cluster_admin_credentials(
                        resource_group, aks.name
                    )

                    if not hasattr(creds, "kubeconfigs") or not creds.kubeconfigs:
                        continue

                    # Load kubeconfig
                    kubeconfig = creds.kubeconfigs[0].value.decode("utf-8")

                    # Load configuration from kubeconfig string
                    import yaml

                    kubeconfig_dict = yaml.safe_load(kubeconfig)
                    api_client = k8s_config.new_client_from_config(config_dict=kubeconfig_dict)

                    # Create Kubernetes API clients
                    v1 = k8s_client.CoreV1Api(api_client=api_client)
                    apps_v1 = k8s_client.AppsV1Api(api_client=api_client)

                    # Get all namespaces
                    namespaces = v1.list_namespace()

                    for ns in namespaces.items:
                        ns_name = ns.metadata.name

                        # Get ConfigMaps
                        try:
                            configmaps = v1.list_namespaced_config_map(ns_name)
                            for cm in configmaps.items:
                                if cm.data:
                                    for key, value in cm.data.items():
                                        if value and isinstance(value, str):
                                            _process_connection_string(
                                                value, key, aks_resource_connections, parser, "configmap"
                                            )
                        except Exception as e:
                            logger.debug(f"Error reading ConfigMaps in {ns_name}: {e}")

                        # Get Secrets
                        try:
                            secrets = v1.list_namespaced_secret(ns_name)
                            for secret in secrets.items:
                                if secret.data:
                                    for key, value_bytes in secret.data.items():
                                        if value_bytes:
                                            try:
                                                value = base64.b64decode(value_bytes).decode(
                                                    "utf-8"
                                                )
                                                _process_connection_string(
                                                    value, key, aks_resource_connections, parser, "secret"
                                                )
                                            except Exception as e:
                                                logger.debug(f"Error processing secret key '{key}' in {ns_name}: {e}")
                        except Exception as e:
                            logger.debug(f"Error reading Secrets in {ns_name}: {e}")

                        # Get Deployments and their environment variables
                        try:
                            deployments = apps_v1.list_namespaced_deployment(ns_name)
                            for deployment in deployments.items:
                                if deployment.spec and deployment.spec.template.spec:
                                    for container in deployment.spec.template.spec.containers:
                                        if container.env:
                                            for env_var in container.env:
                                                if env_var.value:
                                                    _process_connection_string(
                                                        env_var.value,
                                                        env_var.name,
                                                        aks_resource_connections,
                                                        parser,
                                                        "env_var"
                                                    )
                        except Exception as e:
                            logger.debug(f"Error reading Deployments in {ns_name}: {e}")

                        # Get StatefulSets and their environment variables
                        try:
                            statefulsets = apps_v1.list_namespaced_stateful_set(ns_name)
                            for sts in statefulsets.items:
                                if sts.spec and sts.spec.template.spec:
                                    for container in sts.spec.template.spec.containers:
                                        if container.env:
                                            for env_var in container.env:
                                                if env_var.value:
                                                    _process_connection_string(
                                                        env_var.value,
                                                        env_var.name,
                                                        aks_resource_connections,
                                                        parser,
                                                        "env_var"
                                                    )
                        except Exception as e:
                            logger.debug(f"Error reading StatefulSets in {ns_name}: {e}")

                    if aks_resource_connections:
                        connections[aks.id] = aks_resource_connections
                        total_connections = sum(
                            len(conns) for conns in aks_resource_connections.values()
                        )
                        logger.info(
                            f"Found {total_connections} resource connections for AKS {aks.name} "
                            f"across {len(aks_resource_connections)} resource types"
                        )

                except Exception as e:
                    logger.debug(f"Error getting AKS credentials for {aks.name}: {e}")

            except Exception as e:
                logger.error(f"Error processing AKS cluster {aks.name}: {e}")

    except Exception as e:
        logger.error(f"Error getting AKS resource connections: {e}")

    return connections


def _process_connection_string(
    value: str,
    key: str,
    connections_dict: dict,
    parser: "ConnectionStringParser",
    source: str
) -> None:
    """
    Process a potential connection string and add to connections dict.

    Args:
        value: String value to parse
        key: Key/name of the configuration item
        connections_dict: Dictionary to add connections to
        parser: ConnectionStringParser instance
        source: Source of the connection string (configmap, secret, env_var)
    """
    # First try Service Bus (existing logic)
    sb_info = parse_servicebus_connection_string(value)
    if sb_info:
        if "servicebus" not in connections_dict:
            connections_dict["servicebus"] = []
        connections_dict["servicebus"].append({
            "namespace": sb_info["namespace"],
            "key": key,
            "source": source,
            "endpoint": sb_info.get("endpoint")
        })
        return

    # Try generic connection string parsing
    conn_info = parser.parse_connection_string(value)
    if conn_info:
        resource_type = conn_info.service_type
        if resource_type:
            if resource_type not in connections_dict:
                connections_dict[resource_type] = []
            connections_dict[resource_type].append({
                "host": conn_info.host,
                "port": conn_info.port,
                "database": conn_info.database,
                "key": key,
                "source": source,
                "protocol": conn_info.protocol,
                "service_type": conn_info.service_type,
                "full_endpoint": conn_info.full_endpoint
            })


async def get_aks_servicebus_connections(
    subscription_id: str,
    credential,
    aks_resources: list[DiscoveredResource],
) -> dict[str, list[str]]:
    """
    Get Service Bus connections from AKS cluster ConfigMaps and Secrets.

    DEPRECATED: Use get_aks_resource_connections for comprehensive connection discovery.
    This function is kept for backward compatibility.

    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        aks_resources: List of AKS cluster resources

    Returns:
        Dictionary mapping AKS resource ID to list of Service Bus namespace names
    """
    all_connections = await get_aks_resource_connections(
        subscription_id, credential, aks_resources
    )

    # Extract just Service Bus namespaces for backward compatibility
    servicebus_connections = {}
    for aks_id, resource_connections in all_connections.items():
        if "servicebus" in resource_connections:
            namespaces = [conn["namespace"] for conn in resource_connections["servicebus"]]
            servicebus_connections[aks_id] = namespaces

    return servicebus_connections


async def discover_aks_pods_and_storage(
    subscription_id: str,
    credential,
    aks_resources: list[DiscoveredResource],
) -> tuple[list[DiscoveredResource], list[ResourceDependency]]:
    """
    Discover Kubernetes pods and their storage dependencies from AKS clusters.
    
    Detects:
    - Pods running in AKS clusters
    - PersistentVolumeClaims (PVCs) used by pods
    - StorageClass configurations
    - Azure Disk CSI and Azure Blob CSI storage providers
    - Pod -> Storage Account dependencies via CSI drivers
    
    LIMITATIONS:
    - Storage account dependencies use placeholder IDs based on CSI provisioner and StorageClass
    - Actual storage account resource ID resolution requires additional PV inspection or SC parameters
    - Dependencies must be matched with discovered storage accounts in post-processing
    
    Args:
        subscription_id: Azure subscription ID
        credential: Azure credential object
        aks_resources: List of AKS cluster resources
        
    Returns:
        Tuple of (discovered pods as DiscoveredResource, storage dependencies)
    """
    from ..models import DependencyCategory, DependencyType
    
    pods = []
    dependencies = []
    mapper = AzureResourceMapper()
    
    if ContainerServiceClient is None or k8s_client is None:
        logger.warning("Kubernetes client not available, skipping pod discovery")
        return pods, dependencies
        
    try:
        container_client = ContainerServiceClient(credential, subscription_id)
        
        for aks in aks_resources:
            try:
                resource_group = aks.resource_group
                if not resource_group:
                    continue
                    
                # Get cluster credentials
                try:
                    creds = container_client.managed_clusters.list_cluster_admin_credentials(
                        resource_group, aks.name
                    )
                    
                    if not hasattr(creds, "kubeconfigs") or not creds.kubeconfigs:
                        continue
                        
                    # Load kubeconfig
                    kubeconfig = creds.kubeconfigs[0].value.decode("utf-8")
                    
                    import yaml
                    kubeconfig_dict = yaml.safe_load(kubeconfig)
                    api_client = k8s_config.new_client_from_config(config_dict=kubeconfig_dict)
                    
                    # Create Kubernetes API clients
                    v1 = k8s_client.CoreV1Api(api_client=api_client)
                    storage_v1 = k8s_client.StorageV1Api(api_client=api_client)
                    
                    # Get all storage classes to map provisioners to storage accounts
                    storage_classes = {}
                    try:
                        sc_list = storage_v1.list_storage_class()
                        for sc in sc_list.items:
                            storage_classes[sc.metadata.name] = {
                                "provisioner": sc.provisioner,
                                "parameters": sc.parameters or {},
                            }
                    except Exception as e:
                        logger.debug(f"Error listing storage classes: {e}")
                    
                    # Get all namespaces
                    namespaces = v1.list_namespace()
                    
                    for ns in namespaces.items:
                        ns_name = ns.metadata.name
                        
                        # Skip system namespaces unless they have app workloads
                        if ns_name in ("kube-system", "kube-public", "kube-node-lease"):
                            continue
                        
                        # Get PVCs in this namespace
                        pvcs = {}
                        try:
                            pvc_list = v1.list_namespaced_persistent_volume_claim(ns_name)
                            for pvc in pvc_list.items:
                                pvcs[pvc.metadata.name] = {
                                    "storage_class": pvc.spec.storage_class_name,
                                    "volume_name": pvc.spec.volume_name,
                                    "capacity": pvc.status.capacity.get("storage") if pvc.status and pvc.status.capacity else None,
                                }
                        except Exception as e:
                            logger.debug(f"Error listing PVCs in {ns_name}: {e}")
                        
                        # Get pods in this namespace
                        try:
                            pod_list = v1.list_namespaced_pod(ns_name)
                            for pod in pod_list.items:
                                try:
                                    # Extract pod information
                                    pod_id = f"{aks.id}/namespaces/{ns_name}/pods/{pod.metadata.name}"
                                    
                                    # Extract container information
                                    containers = []
                                    if pod.spec and pod.spec.containers:
                                        for container in pod.spec.containers:
                                            containers.append({
                                                "name": container.name,
                                                "image": container.image,
                                            })
                                    
                                    # Extract volume information
                                    volumes = []
                                    volume_pvc_map = {}  # Maps volume name to PVC name
                                    if pod.spec and pod.spec.volumes:
                                        for volume in pod.spec.volumes:
                                            volume_info = {"name": volume.name}
                                            if volume.persistent_volume_claim:
                                                pvc_name = volume.persistent_volume_claim.claim_name
                                                volume_info["pvc"] = pvc_name
                                                volume_pvc_map[volume.name] = pvc_name
                                            volumes.append(volume_info)
                                    
                                    # Create pod resource
                                    pod_resource = mapper.map_azure_resource(
                                        resource_id=pod_id,
                                        resource_name=pod.metadata.name,
                                        resource_type="Microsoft.ContainerService/pod",
                                        location=aks.region,
                                        tags={},
                                        properties={
                                            "namespace": ns_name,
                                            "cluster": aks.name,
                                            "cluster_id": aks.id,
                                            "phase": pod.status.phase if pod.status else "Unknown",
                                            "pod_ip": pod.status.pod_ip if pod.status else None,
                                            "node_name": pod.spec.node_name if pod.spec else None,
                                            "containers": containers,
                                            "volumes": volumes,
                                        },
                                        provisioning_state="Succeeded" if pod.status and pod.status.phase == "Running" else "Failed",
                                    )
                                    pods.append(pod_resource)
                                    
                                    # Detect storage dependencies via PVCs
                                    for volume_name, pvc_name in volume_pvc_map.items():
                                        if pvc_name in pvcs:
                                            pvc_info = pvcs[pvc_name]
                                            storage_class_name = pvc_info.get("storage_class")
                                            
                                            if storage_class_name and storage_class_name in storage_classes:
                                                sc_info = storage_classes[storage_class_name]
                                                provisioner = sc_info.get("provisioner", "")
                                                
                                                # Check if it's an Azure CSI driver
                                                if "disk.csi.azure.com" in provisioner or "blob.csi.azure.com" in provisioner:
                                                    # Extract storage account from parameters if available
                                                    # Note: In real scenarios, storage account might be in SC parameters
                                                    # or we need to query the PV to get the actual storage account
                                                    # For now, we create a generic dependency that can be enriched later
                                                    
                                                    # We'll need to match this with discovered storage accounts
                                                    # This is a placeholder for the dependency - it will be matched
                                                    # during the dependency resolution phase
                                                    dep = ResourceDependency(
                                                        source_id=pod_id,
                                                        target_id=f"storage_csi_{provisioner}_{storage_class_name}",
                                                        category=DependencyCategory.DATA,
                                                        dependency_type=DependencyType.REQUIRED,
                                                        strength=0.9,
                                                        discovered_method="kubernetes_pvc_csi",
                                                        description=f"Pod {pod.metadata.name} uses {provisioner} via PVC {pvc_name}",
                                                        properties={
                                                            "pvc_name": pvc_name,
                                                            "storage_class": storage_class_name,
                                                            "provisioner": provisioner,
                                                            "volume_name": volume_name,
                                                        },
                                                    )
                                                    dependencies.append(dep)
                                                    
                                except Exception as e:
                                    logger.error(f"Error discovering pod {pod.metadata.name}: {e}")
                                    
                        except Exception as e:
                            logger.debug(f"Error listing pods in {ns_name}: {e}")
                            
                except Exception as e:
                    logger.debug(f"Error getting AKS credentials for {aks.name}: {e}")
                    
            except Exception as e:
                logger.error(f"Error processing AKS cluster {aks.name}: {e}")
                
        logger.info(f"Discovered {len(pods)} pods and {len(dependencies)} storage dependencies")
        
    except Exception as e:
        logger.error(f"Error discovering AKS pods and storage: {e}")
        
    return pods, dependencies


async def detect_servicebus_dependencies(
    resources: list[DiscoveredResource],
    subscription_id: str | None = None,
    credential=None,
) -> list[ResourceDependency]:
    """
    Detect Service Bus messaging dependencies.

    Creates relationships between:
    - Service Bus namespaces and their topics/queues
    - Topics and their subscriptions
    - Applications and the topics/queues they publish to or subscribe from

    Args:
        resources: List of discovered resources

    Returns:
        List of ResourceDependency objects representing messaging patterns
    """
    from ..models import DependencyCategory, DependencyType

    dependencies = []

    # Create lookup maps for Service Bus resources
    namespaces = {r.id: r for r in resources if r.resource_type == "servicebus_namespace"}
    topics = [r for r in resources if r.resource_type == "servicebus_topic"]
    queues = [r for r in resources if r.resource_type == "servicebus_queue"]
    subscriptions = [r for r in resources if r.resource_type == "servicebus_subscription"]

    # Create namespace → topic/queue dependencies
    for topic in topics:
        namespace_name = topic.properties.get("namespace")
        if namespace_name:
            # Find the namespace resource using name matching that handles different formats
            for ns_id, namespace in namespaces.items():
                if AzureResourceMapper.names_match(namespace.name, namespace_name):
                    dep = ResourceDependency(
                        source_id=ns_id,
                        target_id=topic.id,
                        category=DependencyCategory.CONFIGURATION,
                        dependency_type=DependencyType.STRONG,
                        strength=1.0,
                        discovered_method="servicebus_structure",
                        description=f"Service Bus namespace contains topic {topic.name}",
                    )
                    dependencies.append(dep)
                    break

    for queue in queues:
        namespace_name = queue.properties.get("namespace")
        if namespace_name:
            # Find the namespace resource using name matching that handles different formats
            for ns_id, namespace in namespaces.items():
                if AzureResourceMapper.names_match(namespace.name, namespace_name):
                    dep = ResourceDependency(
                        source_id=ns_id,
                        target_id=queue.id,
                        category=DependencyCategory.CONFIGURATION,
                        dependency_type=DependencyType.STRONG,
                        strength=1.0,
                        discovered_method="servicebus_structure",
                        description=f"Service Bus namespace contains queue {queue.name}",
                    )
                    dependencies.append(dep)
                    break

    # Create topic → subscription dependencies
    for subscription in subscriptions:
        topic_name = subscription.properties.get("topic")
        namespace_name = subscription.properties.get("namespace")
        if topic_name and namespace_name:
            # Find the topic resource using name matching that handles different formats
            for topic in topics:
                if (
                    AzureResourceMapper.names_match(topic.name, topic_name)
                    and AzureResourceMapper.names_match(topic.properties.get("namespace", ""), namespace_name)
                ):
                    dep = ResourceDependency(
                        source_id=topic.id,
                        target_id=subscription.id,
                        category=DependencyCategory.CONFIGURATION,
                        dependency_type=DependencyType.STRONG,
                        strength=1.0,
                        discovered_method="servicebus_structure",
                        description=f"Topic {topic_name} has subscription {subscription.name}",
                    )
                    dependencies.append(dep)
                    break

    # Detect app → Service Bus dependencies via connection strings and app settings
    app_services = [r for r in resources if r.resource_type == "app_service"]
    aks_clusters = [r for r in resources if r.resource_type == "aks"]

    # Phase 1: Parse actual configuration (strong dependencies)
    if subscription_id and credential:
        # Get App Service connections from application settings and connection strings
        app_service_connections = await get_app_service_servicebus_connections(
            subscription_id, credential, app_services
        )

        for app_id, namespace_names in app_service_connections.items():
            app = next((r for r in app_services if r.id == app_id), None)
            if not app:
                continue

            for namespace_name in namespace_names:
                # Find the namespace resource using name matching that handles different formats
                for ns_id, namespace in namespaces.items():
                    if AzureResourceMapper.names_match(namespace.name, namespace_name):
                        dep = ResourceDependency(
                            source_id=app_id,
                            target_id=ns_id,
                            category=DependencyCategory.DATA,
                            dependency_type=DependencyType.REQUIRED,
                            strength=0.9,
                            discovered_method="app_service_config",
                            description=f"App Service {app.name} uses Service Bus {namespace_name} (from app settings)",
                        )
                        dependencies.append(dep)
                        break

        # Get AKS connections from ConfigMaps and Secrets
        aks_connections = await get_aks_servicebus_connections(
            subscription_id, credential, aks_clusters
        )

        for aks_id, namespace_names in aks_connections.items():
            aks = next((r for r in aks_clusters if r.id == aks_id), None)
            if not aks:
                continue

            for namespace_name in namespace_names:
                # Find the namespace resource using name matching that handles different formats
                for ns_id, namespace in namespaces.items():
                    if AzureResourceMapper.names_match(namespace.name, namespace_name):
                        dep = ResourceDependency(
                            source_id=aks_id,
                            target_id=ns_id,
                            category=DependencyCategory.DATA,
                            dependency_type=DependencyType.REQUIRED,
                            strength=0.9,
                            discovered_method="kubernetes_config",
                            description=f"AKS cluster {aks.name} uses Service Bus {namespace_name} (from ConfigMaps/Secrets)",
                        )
                        dependencies.append(dep)
                        break

    # Phase 2: Fallback to heuristics for apps without found connections
    # This catches cases where we couldn't access configs or for additional weak signals
    detected_app_ids = set()
    for dep in dependencies:
        if dep.discovered_method in ("app_service_config", "kubernetes_config"):
            detected_app_ids.add(dep.source_id)

    for app in app_services + aks_clusters:
        # Skip apps where we already found strong connections
        if app.id in detected_app_ids:
            continue

        # Use heuristic for remaining apps
        for namespace in namespaces.values():
            if namespace.resource_group == app.resource_group:
                dep = ResourceDependency(
                    source_id=app.id,
                    target_id=namespace.id,
                    category=DependencyCategory.DATA,
                    dependency_type=DependencyType.OPTIONAL,
                    strength=0.3,
                    discovered_method="heuristic_colocation",
                    description=f"Application {app.name} may use Service Bus {namespace.name} (same RG)",
                )
                dependencies.append(dep)

    logger.info(f"Detected {len(dependencies)} Service Bus dependencies")
    return dependencies


async def detect_aks_resource_dependencies(
    resources: list[DiscoveredResource],
    subscription_id: str | None = None,
    credential=None,
) -> list[ResourceDependency]:
    """
    Detect comprehensive resource dependencies from AKS clusters.

    Discovers connections from AKS ConfigMaps, Secrets, and environment variables to:
    - Service Bus (namespaces, topics, queues)
    - SQL Databases (Azure SQL, PostgreSQL, MySQL)
    - Redis Cache
    - Storage Accounts
    - Any other services via connection strings

    Args:
        resources: List of discovered resources
        subscription_id: Azure subscription ID (optional, required for actual parsing)
        credential: Azure credential (optional, required for actual parsing)

    Returns:
        List of ResourceDependency objects representing AKS to resource connections
    """
    from ..models import DependencyCategory, DependencyType

    dependencies = []
    
    if not subscription_id or not credential:
        logger.info("Skipping AKS resource dependency detection (no credentials provided)")
        return dependencies

    # Get all AKS clusters
    aks_clusters = [r for r in resources if r.resource_type == "aks"]
    if not aks_clusters:
        return dependencies

    # Get all potential target resources indexed by type and name
    sql_servers = {r.name: r for r in resources if r.resource_type == "sql_server"}
    redis_caches = {r.name: r for r in resources if r.resource_type == "redis"}
    storage_accounts = {r.name: r for r in resources if r.resource_type == "storage_account"}
    servicebus_namespaces = {r.name: r for r in resources if r.resource_type == "servicebus_namespace"}

    # Get comprehensive AKS connections
    try:
        aks_connections = await get_aks_resource_connections(
            subscription_id, credential, aks_clusters
        )

        def _create_sql_dependency(aks, aks_id, conn_info, sql_servers, db_type):
            """Helper to create SQL-type dependencies."""
            host = conn_info.get("host", "")
            server_name = host.split(".")[0] if host else None
            if not server_name:
                return None
            
            for sql_name, sql_server in sql_servers.items():
                if AzureResourceMapper.names_match(sql_name, server_name):
                    return ResourceDependency(
                        source_id=aks_id,
                        target_id=sql_server.id,
                        category=DependencyCategory.DATA,
                        dependency_type=DependencyType.REQUIRED,
                        strength=0.9,
                        discovered_method=f"kubernetes_{conn_info['source']}",
                        description=(
                            f"AKS cluster {aks.name} connects to {db_type} {server_name} "
                            f"(database: {conn_info.get('database', 'N/A')}, "
                            f"from {conn_info['source']}: {conn_info['key']})"
                        ),
                    )
            return None

        for aks_id, resource_connections in aks_connections.items():
            aks = next((r for r in aks_clusters if r.id == aks_id), None)
            if not aks:
                continue

            # Process Service Bus connections
            if "servicebus" in resource_connections:
                for conn_info in resource_connections["servicebus"]:
                    namespace_name = conn_info["namespace"]
                    # Find matching Service Bus namespace
                    for ns_name, namespace in servicebus_namespaces.items():
                        if AzureResourceMapper.names_match(ns_name, namespace_name):
                            dep = ResourceDependency(
                                source_id=aks_id,
                                target_id=namespace.id,
                                category=DependencyCategory.DATA,
                                dependency_type=DependencyType.REQUIRED,
                                strength=0.9,
                                discovered_method=f"kubernetes_{conn_info['source']}",
                                description=(
                                    f"AKS cluster {aks.name} uses Service Bus {namespace_name} "
                                    f"(from {conn_info['source']}: {conn_info['key']})"
                                ),
                            )
                            dependencies.append(dep)
                            break

            # Process SQL connections
            if "sql" in resource_connections:
                for conn_info in resource_connections["sql"]:
                    dep = _create_sql_dependency(aks, aks_id, conn_info, sql_servers, "SQL Server")
                    if dep:
                        dependencies.append(dep)

            # Process PostgreSQL connections
            if "postgresql" in resource_connections:
                for conn_info in resource_connections["postgresql"]:
                    dep = _create_sql_dependency(aks, aks_id, conn_info, sql_servers, "PostgreSQL")
                    if dep:
                        dependencies.append(dep)

            # Process MySQL connections
            if "mysql" in resource_connections:
                for conn_info in resource_connections["mysql"]:
                    dep = _create_sql_dependency(aks, aks_id, conn_info, sql_servers, "MySQL")
                    if dep:
                        dependencies.append(dep)

            # Process Redis connections
            if "redis" in resource_connections:
                for conn_info in resource_connections["redis"]:
                    host = conn_info.get("host", "")
                    # Extract cache name from host (e.g., mycache.redis.cache.windows.net -> mycache)
                    cache_name = host.split(".")[0] if host else None
                    if cache_name:
                        # Find matching Redis cache
                        for redis_name, redis_cache in redis_caches.items():
                            if AzureResourceMapper.names_match(redis_name, cache_name):
                                dep = ResourceDependency(
                                    source_id=aks_id,
                                    target_id=redis_cache.id,
                                    category=DependencyCategory.DATA,
                                    dependency_type=DependencyType.REQUIRED,
                                    strength=0.9,
                                    discovered_method=f"kubernetes_{conn_info['source']}",
                                    description=(
                                        f"AKS cluster {aks.name} connects to Redis Cache {cache_name} "
                                        f"(from {conn_info['source']}: {conn_info['key']})"
                                    ),
                                )
                                dependencies.append(dep)
                                break

            # Process Storage connections
            if "storage" in resource_connections:
                for conn_info in resource_connections["storage"]:
                    host = conn_info.get("host", "")
                    # Extract account name from host (e.g., myaccount.blob.core.windows.net -> myaccount)
                    account_name = host.split(".")[0] if host else None
                    if account_name:
                        # Find matching Storage account
                        for storage_name, storage_account in storage_accounts.items():
                            if AzureResourceMapper.names_match(storage_name, account_name):
                                dep = ResourceDependency(
                                    source_id=aks_id,
                                    target_id=storage_account.id,
                                    category=DependencyCategory.DATA,
                                    dependency_type=DependencyType.REQUIRED,
                                    strength=0.9,
                                    discovered_method=f"kubernetes_{conn_info['source']}",
                                    description=(
                                        f"AKS cluster {aks.name} connects to Storage Account {account_name} "
                                        f"(from {conn_info['source']}: {conn_info['key']})"
                                    ),
                                )
                                dependencies.append(dep)
                                break

        logger.info(f"Detected {len(dependencies)} AKS resource dependencies")

    except Exception as e:
        logger.error(f"Error detecting AKS resource dependencies: {e}")

    return dependencies


async def detect_advanced_dependencies(
    resources: list[DiscoveredResource],
) -> list[ResourceDependency]:
    """
    Detect advanced dependencies between resources.

    Analyzes:
    - Network connections (VNet peering, subnets)
    - Load balancer backend pools
    - Private endpoints
    - App Service connection strings

    Args:
        resources: List of discovered resources

    Returns:
        List of ResourceDependency objects
    """
    dependencies = []
    {r.id: r for r in resources}

    for resource in resources:
        try:
            # Detect network dependencies
            if resource.resource_type == "virtual_machine":
                # VM to VNet/Subnet dependencies
                nic_ids = resource.properties.get("network_interface_ids", [])
                for _nic_id in nic_ids:
                    # NICs connect VMs to VNets (simplified - would need NIC discovery)
                    pass

            elif resource.resource_type == "load_balancer":
                # Load Balancer to backend pool resources
                backend_pools = resource.properties.get("backend_pools", [])
                for _pool in backend_pools:
                    # Would need to resolve pool members to VMs/VMSS
                    pass

            elif resource.resource_type == "app_service":
                # App Service to data/config dependencies
                # Would parse connection strings and app settings
                pass

        except Exception as e:
            logger.error(f"Error detecting dependencies for {resource.id}: {e}")

    logger.info(f"Detected {len(dependencies)} advanced dependencies")
    return dependencies
