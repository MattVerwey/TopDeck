"""
Tests for enhanced AKS resource connection discovery.

Tests the ability to discover connections from AKS clusters to various
Azure resources (SQL, Redis, Storage, Service Bus) via ConfigMaps,
Secrets, and environment variables.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from topdeck.discovery.azure.resources import (
    _process_connection_string,
    get_aks_resource_connections,
    detect_aks_resource_dependencies,
)
from topdeck.discovery.connection_parser import ConnectionStringParser
from topdeck.discovery.models import (
    DiscoveredResource,
    DependencyCategory,
    DependencyType,
)


class TestProcessConnectionString:
    """Test the _process_connection_string helper function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ConnectionStringParser()
        self.connections_dict = {}

    def test_process_servicebus_connection(self):
        """Test processing Service Bus connection string."""
        conn_str = "Endpoint=sb://mynamespace.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=mykey"
        
        _process_connection_string(
            conn_str, "SERVICEBUS_CONN", self.connections_dict, self.parser, "secret"
        )

        assert "servicebus" in self.connections_dict
        assert len(self.connections_dict["servicebus"]) == 1
        assert self.connections_dict["servicebus"][0]["namespace"] == "mynamespace"
        assert self.connections_dict["servicebus"][0]["key"] == "SERVICEBUS_CONN"
        assert self.connections_dict["servicebus"][0]["source"] == "secret"

    def test_process_sql_connection(self):
        """Test processing SQL Server connection string."""
        conn_str = "Server=tcp:myserver.database.windows.net,1433;Database=mydb;User ID=admin;Password=pass;"
        
        _process_connection_string(
            conn_str, "SQL_CONNECTION", self.connections_dict, self.parser, "configmap"
        )

        assert "sql" in self.connections_dict
        assert len(self.connections_dict["sql"]) == 1
        assert self.connections_dict["sql"][0]["host"] == "myserver.database.windows.net"
        assert self.connections_dict["sql"][0]["port"] == 1433
        assert self.connections_dict["sql"][0]["database"] == "mydb"
        assert self.connections_dict["sql"][0]["key"] == "SQL_CONNECTION"
        assert self.connections_dict["sql"][0]["source"] == "configmap"

    def test_process_redis_connection(self):
        """Test processing Redis connection string."""
        conn_str = "redis://mycache.redis.cache.windows.net:6380/0"
        
        _process_connection_string(
            conn_str, "REDIS_URL", self.connections_dict, self.parser, "env_var"
        )

        assert "redis" in self.connections_dict
        assert len(self.connections_dict["redis"]) == 1
        assert self.connections_dict["redis"][0]["host"] == "mycache.redis.cache.windows.net"
        assert self.connections_dict["redis"][0]["port"] == 6380
        assert self.connections_dict["redis"][0]["key"] == "REDIS_URL"
        assert self.connections_dict["redis"][0]["source"] == "env_var"

    def test_process_postgresql_connection(self):
        """Test processing PostgreSQL connection string."""
        conn_str = "postgresql://admin:pass@mypostgres.postgres.database.azure.com:5432/mydb"
        
        _process_connection_string(
            conn_str, "DATABASE_URL", self.connections_dict, self.parser, "secret"
        )

        assert "postgresql" in self.connections_dict
        assert len(self.connections_dict["postgresql"]) == 1
        assert self.connections_dict["postgresql"][0]["host"] == "mypostgres.postgres.database.azure.com"
        assert self.connections_dict["postgresql"][0]["database"] == "mydb"

    def test_process_storage_connection(self):
        """Test processing Azure Storage connection string."""
        conn_str = "DefaultEndpointsProtocol=https;AccountName=mystorageaccount;AccountKey=key123=="
        
        _process_connection_string(
            conn_str, "STORAGE_CONN", self.connections_dict, self.parser, "configmap"
        )

        assert "storage" in self.connections_dict
        assert len(self.connections_dict["storage"]) == 1
        assert "mystorageaccount" in self.connections_dict["storage"][0]["host"]

    def test_process_multiple_connections(self):
        """Test processing multiple connection strings of different types."""
        conn_strings = [
            ("Server=tcp:sql.database.windows.net,1433;Database=db1;", "SQL_CONN", "secret"),
            ("redis://cache.redis.cache.windows.net:6379/0", "REDIS_URL", "env_var"),
            ("Endpoint=sb://sb.servicebus.windows.net/;", "SB_CONN", "configmap"),
        ]

        for conn_str, key, source in conn_strings:
            _process_connection_string(
                conn_str, key, self.connections_dict, self.parser, source
            )

        assert len(self.connections_dict) == 3
        assert "sql" in self.connections_dict
        assert "redis" in self.connections_dict
        assert "servicebus" in self.connections_dict

    def test_process_invalid_connection_string(self):
        """Test processing an invalid connection string (should not add anything)."""
        conn_str = "just some random text that is not a connection string"
        
        _process_connection_string(
            conn_str, "RANDOM_VAR", self.connections_dict, self.parser, "env_var"
        )

        assert len(self.connections_dict) == 0


@pytest.mark.asyncio
class TestDetectAKSResourceDependencies:
    """Test AKS resource dependency detection."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock AKS resource
        self.aks_resource = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ContainerService/managedClusters/aks1",
            name="aks1",
            resource_type="aks",
            cloud_provider="azure",
            region="eastus",
            resource_group="rg1",
        )

        # Create mock target resources
        self.sql_server = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/myserver",
            name="myserver",
            resource_type="sql_server",
            cloud_provider="azure",
            region="eastus",
            resource_group="rg1",
        )

        self.redis_cache = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Cache/Redis/mycache",
            name="mycache",
            resource_type="redis",
            cloud_provider="azure",
            region="eastus",
            resource_group="rg1",
        )

        self.storage_account = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/mystorage",
            name="mystorage",
            resource_type="storage_account",
            cloud_provider="azure",
            region="eastus",
            resource_group="rg1",
        )

        self.servicebus_namespace = DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.ServiceBus/namespaces/mybus",
            name="mybus",
            resource_type="servicebus_namespace",
            cloud_provider="azure",
            region="eastus",
            resource_group="rg1",
        )

    async def test_detect_no_credentials(self):
        """Test detection with no credentials returns empty list."""
        resources = [self.aks_resource, self.sql_server]
        
        dependencies = await detect_aks_resource_dependencies(
            resources, subscription_id=None, credential=None
        )

        assert len(dependencies) == 0

    async def test_detect_no_aks_clusters(self):
        """Test detection with no AKS clusters returns empty list."""
        resources = [self.sql_server, self.redis_cache]
        
        dependencies = await detect_aks_resource_dependencies(
            resources, subscription_id="sub1", credential=MagicMock()
        )

        assert len(dependencies) == 0

    @patch('topdeck.discovery.azure.resources.get_aks_resource_connections')
    async def test_detect_sql_dependency(self, mock_get_connections):
        """Test detecting SQL Server dependency from AKS."""
        # Mock the connection discovery to return SQL connection
        mock_get_connections.return_value = {
            self.aks_resource.id: {
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
                ]
            }
        }

        resources = [self.aks_resource, self.sql_server]
        
        dependencies = await detect_aks_resource_dependencies(
            resources, subscription_id="sub1", credential=MagicMock()
        )

        assert len(dependencies) == 1
        dep = dependencies[0]
        assert dep.source_id == self.aks_resource.id
        assert dep.target_id == self.sql_server.id
        assert dep.category == DependencyCategory.DATA
        assert dep.dependency_type == DependencyType.REQUIRED
        assert dep.strength == 0.9
        assert "kubernetes_secret" in dep.discovered_method
        assert "myserver" in dep.description
        assert "mydb" in dep.description

    @patch('topdeck.discovery.azure.resources.get_aks_resource_connections')
    async def test_detect_redis_dependency(self, mock_get_connections):
        """Test detecting Redis cache dependency from AKS."""
        mock_get_connections.return_value = {
            self.aks_resource.id: {
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
                ]
            }
        }

        resources = [self.aks_resource, self.redis_cache]
        
        dependencies = await detect_aks_resource_dependencies(
            resources, subscription_id="sub1", credential=MagicMock()
        )

        assert len(dependencies) == 1
        dep = dependencies[0]
        assert dep.source_id == self.aks_resource.id
        assert dep.target_id == self.redis_cache.id
        assert dep.category == DependencyCategory.DATA
        assert "kubernetes_env_var" in dep.discovered_method
        assert "mycache" in dep.description

    @patch('topdeck.discovery.azure.resources.get_aks_resource_connections')
    async def test_detect_storage_dependency(self, mock_get_connections):
        """Test detecting Storage Account dependency from AKS."""
        mock_get_connections.return_value = {
            self.aks_resource.id: {
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
                ]
            }
        }

        resources = [self.aks_resource, self.storage_account]
        
        dependencies = await detect_aks_resource_dependencies(
            resources, subscription_id="sub1", credential=MagicMock()
        )

        assert len(dependencies) == 1
        dep = dependencies[0]
        assert dep.source_id == self.aks_resource.id
        assert dep.target_id == self.storage_account.id
        assert "kubernetes_configmap" in dep.discovered_method
        assert "mystorage" in dep.description

    @patch('topdeck.discovery.azure.resources.get_aks_resource_connections')
    async def test_detect_multiple_dependencies(self, mock_get_connections):
        """Test detecting multiple dependencies of different types."""
        mock_get_connections.return_value = {
            self.aks_resource.id: {
                "sql": [
                    {
                        "host": "myserver.database.windows.net",
                        "port": 1433,
                        "database": "mydb",
                        "key": "SQL_CONN",
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

        resources = [
            self.aks_resource,
            self.sql_server,
            self.redis_cache,
            self.servicebus_namespace,
        ]
        
        dependencies = await detect_aks_resource_dependencies(
            resources, subscription_id="sub1", credential=MagicMock()
        )

        assert len(dependencies) == 3
        
        # Verify all target types are present
        target_ids = {dep.target_id for dep in dependencies}
        assert self.sql_server.id in target_ids
        assert self.redis_cache.id in target_ids
        assert self.servicebus_namespace.id in target_ids

    @patch('topdeck.discovery.azure.resources.get_aks_resource_connections')
    async def test_no_matching_resources(self, mock_get_connections):
        """Test when connections are found but no matching resources exist."""
        mock_get_connections.return_value = {
            self.aks_resource.id: {
                "sql": [
                    {
                        "host": "nonexistent.database.windows.net",
                        "port": 1433,
                        "database": "db",
                        "key": "SQL_CONN",
                        "source": "secret",
                        "protocol": "tcp",
                        "service_type": "sql",
                        "full_endpoint": "nonexistent.database.windows.net:1433/db"
                    }
                ]
            }
        }

        resources = [self.aks_resource, self.sql_server]
        
        dependencies = await detect_aks_resource_dependencies(
            resources, subscription_id="sub1", credential=MagicMock()
        )

        # Should not create dependency if no matching resource found
        assert len(dependencies) == 0
