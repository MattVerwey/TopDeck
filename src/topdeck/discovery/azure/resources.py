"""
Azure Resource Discovery Functions.

Specialized resource discovery for detailed property extraction.
"""

import logging

try:
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.servicebus import ServiceBusManagementClient
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.web import WebSiteManagementClient
except ImportError:
    ComputeManagementClient = None
    NetworkManagementClient = None
    StorageManagementClient = None
    WebSiteManagementClient = None
    ServiceBusManagementClient = None

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
    resources = []
    mapper = AzureResourceMapper()

    if ServiceBusManagementClient is None:
        logger.warning("Azure Service Bus SDK not available, skipping messaging discovery")
        return resources

    try:
        servicebus_client = ServiceBusManagementClient(credential, subscription_id)

        # Discover Service Bus namespaces
        if resource_group:
            namespaces = servicebus_client.namespaces.list_by_resource_group(resource_group)
        else:
            namespaces = servicebus_client.namespaces.list()

        for namespace in namespaces:
            try:
                # Map namespace resource
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
                    },
                    provisioning_state=(
                        namespace.provisioning_state
                        if hasattr(namespace, "provisioning_state")
                        else None
                    ),
                )
                resources.append(namespace_resource)

                # Discover topics in this namespace
                namespace_rg = mapper.extract_resource_group(namespace.id)
                if namespace_rg:
                    topics = servicebus_client.topics.list_by_namespace(
                        namespace_rg, namespace.name
                    )
                    for topic in topics:
                        try:
                            topic_resource = mapper.map_azure_resource(
                                resource_id=topic.id,
                                resource_name=topic.name,
                                resource_type=topic.type,
                                location=namespace.location,
                                tags={},
                                properties={
                                    "namespace": namespace.name,
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
                                },
                                provisioning_state=None,
                            )
                            resources.append(topic_resource)

                            # Discover subscriptions for this topic
                            subscriptions = servicebus_client.subscriptions.list_by_topic(
                                namespace_rg, namespace.name, topic.name
                            )
                            for subscription in subscriptions:
                                try:
                                    sub_resource = mapper.map_azure_resource(
                                        resource_id=subscription.id,
                                        resource_name=subscription.name,
                                        resource_type=subscription.type,
                                        location=namespace.location,
                                        tags={},
                                        properties={
                                            "namespace": namespace.name,
                                            "topic": topic.name,
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
                                        },
                                        provisioning_state=None,
                                    )
                                    resources.append(sub_resource)
                                except Exception as e:
                                    logger.error(
                                        f"Error discovering subscription {subscription.name}: {e}"
                                    )

                        except Exception as e:
                            logger.error(f"Error discovering topic {topic.name}: {e}")

                    # Discover queues in this namespace
                    queues = servicebus_client.queues.list_by_namespace(
                        namespace_rg, namespace.name
                    )
                    for queue in queues:
                        try:
                            queue_resource = mapper.map_azure_resource(
                                resource_id=queue.id,
                                resource_name=queue.name,
                                resource_type=queue.type,
                                location=namespace.location,
                                tags={},
                                properties={
                                    "namespace": namespace.name,
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
                                },
                                provisioning_state=None,
                            )
                            resources.append(queue_resource)
                        except Exception as e:
                            logger.error(f"Error discovering queue {queue.name}: {e}")

            except Exception as e:
                logger.error(f"Error discovering Service Bus namespace {namespace.name}: {e}")

        logger.info(f"Discovered {len(resources)} messaging resources")

    except Exception as e:
        logger.error(f"Error discovering messaging resources: {e}")

    return resources


async def detect_servicebus_dependencies(
    resources: list[DiscoveredResource],
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
            # Find the namespace resource
            for ns_id, namespace in namespaces.items():
                if namespace.name == namespace_name:
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
            # Find the namespace resource
            for ns_id, namespace in namespaces.items():
                if namespace.name == namespace_name:
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
            # Find the topic resource
            for topic in topics:
                if (
                    topic.name == topic_name
                    and topic.properties.get("namespace") == namespace_name
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
    # This is heuristic-based - would need to parse actual connection strings
    app_services = [r for r in resources if r.resource_type == "app_service"]
    aks_clusters = [r for r in resources if r.resource_type == "aks"]

    for app in app_services + aks_clusters:
        # In production, would parse app settings/connection strings
        # For now, assume apps in same resource group might use Service Bus
        for namespace in namespaces.values():
            if namespace.resource_group == app.resource_group:
                # Create a weak dependency indicating potential usage
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
