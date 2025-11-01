"""
Tests for Azure Service Bus discovery.
"""

import pytest

from topdeck.discovery.azure.mapper import AzureResourceMapper
from topdeck.discovery.azure.resources import (
    detect_servicebus_dependencies,
    parse_servicebus_connection_string,
)
from topdeck.discovery.models import (
    CloudProvider,
    DependencyCategory,
    DiscoveredResource,
    ResourceStatus,
)


class TestServiceBusMapper:
    """Test Azure Service Bus resource mapping"""

    def test_map_servicebus_namespace(self):
        """Test mapping Service Bus namespace type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.ServiceBus/namespaces")
        assert result == "servicebus_namespace"

    def test_map_servicebus_topic(self):
        """Test mapping Service Bus topic type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.ServiceBus/namespaces/topics")
        assert result == "servicebus_topic"

    def test_map_servicebus_queue(self):
        """Test mapping Service Bus queue type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.ServiceBus/namespaces/queues")
        assert result == "servicebus_queue"

    def test_map_servicebus_subscription(self):
        """Test mapping Service Bus subscription type"""
        result = AzureResourceMapper.map_resource_type(
            "Microsoft.ServiceBus/namespaces/topics/subscriptions"
        )
        assert result == "servicebus_subscription"


class TestServiceBusDependencies:
    """Test Service Bus dependency detection"""

    @pytest.mark.asyncio
    async def test_namespace_to_topic_dependency(self):
        """Test dependency detection from namespace to topic"""
        namespace = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1",
            name="ns1",
            resource_type="servicebus_namespace",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
        )

        topic = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1/topics/topic1",
            name="topic1",
            resource_type="servicebus_topic",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
            properties={"namespace": "ns1"},
        )

        resources = [namespace, topic]
        dependencies = await detect_servicebus_dependencies(resources)

        # Should find namespace -> topic dependency
        assert len(dependencies) > 0
        ns_to_topic = [
            d for d in dependencies if d.source_id == namespace.id and d.target_id == topic.id
        ]
        assert len(ns_to_topic) == 1
        assert ns_to_topic[0].category == DependencyCategory.CONFIGURATION
        assert ns_to_topic[0].strength == 1.0

    @pytest.mark.asyncio
    async def test_namespace_to_queue_dependency(self):
        """Test dependency detection from namespace to queue"""
        namespace = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1",
            name="ns1",
            resource_type="servicebus_namespace",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
        )

        queue = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1/queues/queue1",
            name="queue1",
            resource_type="servicebus_queue",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
            properties={"namespace": "ns1"},
        )

        resources = [namespace, queue]
        dependencies = await detect_servicebus_dependencies(resources)

        # Should find namespace -> queue dependency
        assert len(dependencies) > 0
        ns_to_queue = [
            d for d in dependencies if d.source_id == namespace.id and d.target_id == queue.id
        ]
        assert len(ns_to_queue) == 1
        assert ns_to_queue[0].category == DependencyCategory.CONFIGURATION

    @pytest.mark.asyncio
    async def test_topic_to_subscription_dependency(self):
        """Test dependency detection from topic to subscription"""
        namespace = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1",
            name="ns1",
            resource_type="servicebus_namespace",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
        )

        topic = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1/topics/topic1",
            name="topic1",
            resource_type="servicebus_topic",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
            properties={"namespace": "ns1"},
        )

        subscription = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1/topics/topic1/subscriptions/sub1",
            name="sub1",
            resource_type="servicebus_subscription",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
            properties={"namespace": "ns1", "topic": "topic1"},
        )

        resources = [namespace, topic, subscription]
        dependencies = await detect_servicebus_dependencies(resources)

        # Should find topic -> subscription dependency
        topic_to_sub = [
            d for d in dependencies if d.source_id == topic.id and d.target_id == subscription.id
        ]
        assert len(topic_to_sub) == 1
        assert topic_to_sub[0].category == DependencyCategory.CONFIGURATION
        assert topic_to_sub[0].strength == 1.0

    @pytest.mark.asyncio
    async def test_app_to_servicebus_heuristic_dependency(self):
        """Test heuristic dependency detection from app to Service Bus"""
        namespace = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1",
            name="ns1",
            resource_type="servicebus_namespace",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
        )

        app_service = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Web/sites/app1",
            name="app1",
            resource_type="app_service",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
        )

        resources = [namespace, app_service]
        dependencies = await detect_servicebus_dependencies(resources)

        # Should find heuristic app -> namespace dependency
        app_to_ns = [
            d for d in dependencies if d.source_id == app_service.id and d.target_id == namespace.id
        ]
        assert len(app_to_ns) == 1
        assert app_to_ns[0].category == DependencyCategory.DATA
        assert app_to_ns[0].discovered_method == "heuristic_colocation"

    @pytest.mark.asyncio
    async def test_complete_servicebus_topology(self):
        """Test complete Service Bus topology with namespace, topics, queues, and subscriptions"""
        namespace = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1",
            name="ns1",
            resource_type="servicebus_namespace",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
        )

        topic1 = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1/topics/topic1",
            name="topic1",
            resource_type="servicebus_topic",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
            properties={"namespace": "ns1"},
        )

        subscription1 = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1/topics/topic1/subscriptions/sub1",
            name="sub1",
            resource_type="servicebus_subscription",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
            properties={"namespace": "ns1", "topic": "topic1"},
        )

        queue1 = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/ns1/queues/queue1",
            name="queue1",
            resource_type="servicebus_queue",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg1",
            status=ResourceStatus.RUNNING,
            properties={"namespace": "ns1"},
        )

        resources = [namespace, topic1, subscription1, queue1]
        dependencies = await detect_servicebus_dependencies(resources)

        # Should find:
        # 1. namespace -> topic1
        # 2. namespace -> queue1
        # 3. topic1 -> subscription1
        assert len(dependencies) == 3

        # Verify each dependency type
        ns_to_topic = [
            d for d in dependencies if d.source_id == namespace.id and d.target_id == topic1.id
        ]
        assert len(ns_to_topic) == 1

        ns_to_queue = [
            d for d in dependencies if d.source_id == namespace.id and d.target_id == queue1.id
        ]
        assert len(ns_to_queue) == 1

        topic_to_sub = [
            d for d in dependencies if d.source_id == topic1.id and d.target_id == subscription1.id
        ]
        assert len(topic_to_sub) == 1


class TestServiceBusConnectionParsing:
    """Test Service Bus connection string parsing"""

    def test_parse_valid_connection_string(self):
        """Test parsing a valid Service Bus connection string"""
        conn_str = "Endpoint=sb://myns.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=abc123"
        result = parse_servicebus_connection_string(conn_str)

        assert result is not None
        assert result["namespace"] == "myns"
        assert "sb://myns.servicebus.windows.net/" in result["endpoint"]

    def test_parse_connection_string_with_entity(self):
        """Test parsing connection string with entity path"""
        conn_str = "Endpoint=sb://prodns.servicebus.windows.net/;SharedAccessKeyName=SendPolicy;SharedAccessKey=xyz789;EntityPath=mytopic"
        result = parse_servicebus_connection_string(conn_str)

        assert result is not None
        assert result["namespace"] == "prodns"

    def test_parse_non_servicebus_connection_string(self):
        """Test that non-Service Bus connection strings return None"""
        conn_str = "Server=tcp:myserver.database.windows.net,1433;Database=mydb"
        result = parse_servicebus_connection_string(conn_str)

        assert result is None

    def test_parse_empty_connection_string(self):
        """Test parsing empty connection string"""
        result = parse_servicebus_connection_string("")
        assert result is None

    def test_parse_none_connection_string(self):
        """Test parsing None connection string"""
        result = parse_servicebus_connection_string(None)
        assert result is None

    def test_parse_malformed_connection_string(self):
        """Test parsing malformed connection string"""
        conn_str = "Endpoint=sb://;something=wrong"
        result = parse_servicebus_connection_string(conn_str)  # noqa: F841 - testing no exception
        # Should handle gracefully - implementation may return None or partial result
        # The test passes if no exception is raised
