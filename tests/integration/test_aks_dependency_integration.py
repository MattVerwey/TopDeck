"""
Integration test for AKS resource dependency discovery.

This test validates that the complete flow from AKS cluster discovery
to dependency creation and topology representation works correctly.
"""

import pytest
from unittest.mock import MagicMock, patch
from topdeck.discovery.models import DiscoveredResource
from topdeck.discovery.azure.discoverer import AzureDiscoverer


@pytest.mark.asyncio
class TestAKSDependencyIntegration:
    """Integration tests for AKS dependency discovery."""

    @patch('topdeck.discovery.azure.resources.get_aks_resource_connections')
    async def test_full_dependency_discovery_flow(self, mock_get_connections):
        """Test full flow from resource discovery to dependency detection."""
        # Mock the AKS connection discovery to return multiple connection types
        mock_connections = {
            "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1": {
                "sql": [
                    {
                        "host": "myserver.database.windows.net",
                        "port": 1433,
                        "database": "mydb",
                        "key": "SQL_CONNECTION",
                        "source": "secret",
                        "protocol": "tcp",
                        "service_type": "sql",
                        "full_endpoint": "myserver.database.windows.net:1433/mydb"
                    }
                ],
                "redis": [
                    {
                        "host": "mycache.redis.cache.windows.net",
                        "port": 6380,
                        "database": "0",
                        "key": "REDIS_URL",
                        "source": "env_var",
                        "protocol": "redis",
                        "service_type": "redis",
                        "full_endpoint": "mycache.redis.cache.windows.net:6380/0"
                    }
                ],
                "storage": [
                    {
                        "host": "mystorage.blob.core.windows.net",
                        "port": 443,
                        "database": None,
                        "key": "STORAGE_CONN",
                        "source": "configmap",
                        "protocol": "https",
                        "service_type": "storage",
                        "full_endpoint": "https://mystorage.blob.core.windows.net"
                    }
                ],
                "servicebus": [
                    {
                        "namespace": "mybus",
                        "key": "SB_CONN",
                        "source": "secret",
                        "endpoint": "sb://mybus.servicebus.windows.net/"
                    }
                ]
            }
        }
        mock_get_connections.return_value = mock_connections

        # Create mock resources
        resources = [
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1",
                name="aks1",
                resource_type="aks",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/myserver",
                name="myserver",
                resource_type="sql_server",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Cache/Redis/mycache",
                name="mycache",
                resource_type="redis",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/mystorage",
                name="mystorage",
                resource_type="storage_account",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/mybus",
                name="mybus",
                resource_type="servicebus_namespace",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
        ]

        # Create discoverer with mocked credential
        mock_credential = MagicMock()
        discoverer = AzureDiscoverer(
            subscription_id="sub1",
            credential=mock_credential,
        )

        # Call dependency discovery
        dependencies = await discoverer._discover_dependencies(resources)

        # Verify dependencies were discovered for all connection types
        # Filter to only AKS dependencies (source is AKS cluster)
        aks_deps = [
            dep for dep in dependencies
            if dep.source_id == "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1"
        ]

        # Should have at least 4 dependencies (SQL, Redis, Storage, Service Bus)
        # Note: May have more due to heuristic dependencies
        assert len(aks_deps) >= 4

        # Verify each dependency type exists
        target_ids = {dep.target_id for dep in aks_deps}
        
        assert "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/myserver" in target_ids
        assert "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Cache/Redis/mycache" in target_ids
        assert "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/mystorage" in target_ids
        assert "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/mybus" in target_ids

        # Verify dependency properties for one of them
        sql_dep = next(
            dep for dep in aks_deps
            if dep.target_id == "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/myserver"
            and "kubernetes_secret" in dep.discovered_method
        )
        assert sql_dep is not None
        assert sql_dep.strength == 0.9
        assert "myserver" in sql_dep.description
        assert "mydb" in sql_dep.description

    @patch('topdeck.discovery.azure.resources.get_aks_resource_connections')
    async def test_no_false_positives(self, mock_get_connections):
        """Test that no dependencies are created when no connections are found."""
        # Mock no connections found
        mock_get_connections.return_value = {}

        resources = [
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1",
                name="aks1",
                resource_type="aks",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/myserver",
                name="myserver",
                resource_type="sql_server",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
        ]

        mock_credential = MagicMock()
        discoverer = AzureDiscoverer(
            subscription_id="sub1",
            credential=mock_credential,
        )

        dependencies = await discoverer._discover_dependencies(resources)

        # Filter to only AKS dependencies from our new detection method
        aks_config_deps = [
            dep for dep in dependencies
            if dep.source_id == "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1"
            and "kubernetes_" in dep.discovered_method
        ]

        # Should have no dependencies from Kubernetes config since no connections were found
        assert len(aks_config_deps) == 0

    @patch('topdeck.discovery.azure.resources.get_aks_resource_connections')
    async def test_multiple_aks_clusters(self, mock_get_connections):
        """Test discovery with multiple AKS clusters."""
        # Mock connections for two different AKS clusters
        mock_get_connections.return_value = {
            "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1": {
                "sql": [
                    {
                        "host": "server1.database.windows.net",
                        "port": 1433,
                        "database": "db1",
                        "key": "SQL_CONN",
                        "source": "secret",
                        "protocol": "tcp",
                        "service_type": "sql",
                        "full_endpoint": "server1.database.windows.net:1433/db1"
                    }
                ]
            },
            "/subscriptions/sub1/resourceGroups/rg2/providers/Microsoft.ContainerService/managedClusters/aks2": {
                "redis": [
                    {
                        "host": "cache2.redis.cache.windows.net",
                        "port": 6380,
                        "database": "0",
                        "key": "REDIS_URL",
                        "source": "env_var",
                        "protocol": "redis",
                        "service_type": "redis",
                        "full_endpoint": "cache2.redis.cache.windows.net:6380/0"
                    }
                ]
            }
        }

        resources = [
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1",
                name="aks1",
                resource_type="aks",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg2/providers/Microsoft.ContainerService/managedClusters/aks2",
                name="aks2",
                resource_type="aks",
                cloud_provider="azure",
                region="westus",
                resource_group="rg2",
            ),
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/server1",
                name="server1",
                resource_type="sql_server",
                cloud_provider="azure",
                region="eastus",
                resource_group="rg1",
            ),
            DiscoveredResource(
                id="/subscriptions/sub1/resourceGroups/rg2/providers/Microsoft.Cache/Redis/cache2",
                name="cache2",
                resource_type="redis",
                cloud_provider="azure",
                region="westus",
                resource_group="rg2",
            ),
        ]

        mock_credential = MagicMock()
        discoverer = AzureDiscoverer(
            subscription_id="sub1",
            credential=mock_credential,
        )

        dependencies = await discoverer._discover_dependencies(resources)

        # Verify each AKS cluster has its own dependencies
        aks1_deps = [
            dep for dep in dependencies
            if dep.source_id == "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1"
            and "kubernetes_" in dep.discovered_method
        ]

        aks2_deps = [
            dep for dep in dependencies
            if dep.source_id == "/subscriptions/sub1/resourceGroups/rg2/providers/Microsoft.ContainerService/managedClusters/aks2"
            and "kubernetes_" in dep.discovered_method
        ]

        assert len(aks1_deps) >= 1  # Should have SQL dependency
        assert len(aks2_deps) >= 1  # Should have Redis dependency

        # Verify correct targets
        aks1_targets = {dep.target_id for dep in aks1_deps}
        aks2_targets = {dep.target_id for dep in aks2_deps}

        assert "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/server1" in aks1_targets
        assert "/subscriptions/sub1/resourceGroups/rg2/providers/Microsoft.Cache/Redis/cache2" in aks2_targets
