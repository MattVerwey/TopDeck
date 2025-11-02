"""
Tests for Azure resource matching and duplicate prevention.

This module tests critical functionality for Azure resource discovery:
- Resource name normalization (FQDN to short name)
- Flexible name matching across different Azure name formats
- Duplicate prevention for resources and dependencies
- Integration scenarios for Service Bus, Storage, and parallel discovery
"""

import pytest

from topdeck.discovery.azure.mapper import AzureResourceMapper
from topdeck.discovery.models import (
    CloudProvider,
    DependencyCategory,
    DependencyType,
    DiscoveredResource,
    DiscoveryResult,
    ResourceDependency,
    ResourceStatus,
)


class TestResourceNameNormalization:
    """Tests for resource name normalization"""

    def test_normalize_simple_name(self):
        """Test normalizing a simple resource name"""
        result = AzureResourceMapper.normalize_resource_name("myresource")
        assert result == "myresource"

    def test_normalize_servicebus_fqdn(self):
        """Test normalizing Service Bus FQDN"""
        result = AzureResourceMapper.normalize_resource_name(
            "myservicebus.servicebus.windows.net"
        )
        assert result == "myservicebus"

    def test_normalize_storage_blob_fqdn(self):
        """Test normalizing Storage blob endpoint"""
        result = AzureResourceMapper.normalize_resource_name("mystorage.blob.core.windows.net")
        assert result == "mystorage"

    def test_normalize_sql_fqdn(self):
        """Test normalizing SQL database FQDN"""
        result = AzureResourceMapper.normalize_resource_name("myserver.database.windows.net")
        assert result == "myserver"

    def test_normalize_redis_fqdn(self):
        """Test normalizing Redis cache FQDN"""
        result = AzureResourceMapper.normalize_resource_name("myredis.redis.cache.windows.net")
        assert result == "myredis"

    def test_normalize_app_service_fqdn(self):
        """Test normalizing App Service FQDN"""
        result = AzureResourceMapper.normalize_resource_name("myapp.azurewebsites.net")
        assert result == "myapp"

    def test_normalize_key_vault_fqdn(self):
        """Test normalizing Key Vault FQDN"""
        result = AzureResourceMapper.normalize_resource_name("myvault.vault.azure.net")
        assert result == "myvault"

    def test_normalize_cosmos_db_fqdn(self):
        """Test normalizing Cosmos DB FQDN"""
        result = AzureResourceMapper.normalize_resource_name("mycosmosdb.documents.azure.com")
        assert result == "mycosmosdb"

    def test_normalize_generic_hostname(self):
        """Test normalizing a generic hostname"""
        result = AzureResourceMapper.normalize_resource_name("server.example.com")
        assert result == "server"

    def test_normalize_empty_string(self):
        """Test normalizing an empty string"""
        result = AzureResourceMapper.normalize_resource_name("")
        assert result == ""

    def test_normalize_case_insensitive(self):
        """Test normalization handles case properly"""
        result1 = AzureResourceMapper.normalize_resource_name(
            "MyServiceBus.servicebus.windows.net"
        )
        result2 = AzureResourceMapper.normalize_resource_name(
            "myservicebus.SERVICEBUS.WINDOWS.NET"
        )
        assert result1 == "MyServiceBus"
        assert result2 == "myservicebus"


class TestExtractHostnameFromEndpoint:
    """Tests for extracting hostname from endpoint URLs"""

    def test_extract_from_sb_protocol(self):
        """Test extracting from Service Bus protocol URL"""
        result = AzureResourceMapper.extract_hostname_from_endpoint(
            "sb://mybus.servicebus.windows.net/"
        )
        assert result == "mybus.servicebus.windows.net"

    def test_extract_from_https(self):
        """Test extracting from HTTPS URL"""
        result = AzureResourceMapper.extract_hostname_from_endpoint(
            "https://myapp.azurewebsites.net/api"
        )
        assert result == "myapp.azurewebsites.net"

    def test_extract_with_port(self):
        """Test extracting with port number"""
        result = AzureResourceMapper.extract_hostname_from_endpoint("https://myserver.com:443/path")
        assert result == "myserver.com"

    def test_extract_without_protocol(self):
        """Test extracting without protocol"""
        result = AzureResourceMapper.extract_hostname_from_endpoint("myserver.example.com/path")
        assert result == "myserver.example.com"

    def test_extract_empty_string(self):
        """Test extracting from empty string"""
        result = AzureResourceMapper.extract_hostname_from_endpoint("")
        assert result is None

    def test_extract_none(self):
        """Test extracting from None"""
        result = AzureResourceMapper.extract_hostname_from_endpoint(None)
        assert result is None


class TestNamesMatch:
    """Tests for resource name matching"""

    def test_exact_match(self):
        """Test exact name match"""
        assert AzureResourceMapper.names_match("myresource", "myresource")

    def test_fqdn_to_short_name(self):
        """Test matching FQDN to short name"""
        assert AzureResourceMapper.names_match(
            "myservicebus.servicebus.windows.net", "myservicebus"
        )

    def test_short_name_to_fqdn(self):
        """Test matching short name to FQDN"""
        assert AzureResourceMapper.names_match(
            "myservicebus", "myservicebus.servicebus.windows.net"
        )

    def test_different_azure_suffixes(self):
        """Test matching with different Azure service suffixes"""
        assert AzureResourceMapper.names_match(
            "mystorage.blob.core.windows.net", "mystorage.queue.core.windows.net"
        )

    def test_case_insensitive(self):
        """Test case-insensitive matching"""
        assert AzureResourceMapper.names_match("MyResource", "myresource")

    def test_case_insensitive_fqdn(self):
        """Test case-insensitive FQDN matching"""
        assert AzureResourceMapper.names_match(
            "MyServiceBus.SERVICEBUS.WINDOWS.NET", "myservicebus"
        )

    def test_no_match(self):
        """Test non-matching names"""
        assert not AzureResourceMapper.names_match("resource1", "resource2")

    def test_empty_strings(self):
        """Test matching with empty strings"""
        assert not AzureResourceMapper.names_match("", "myresource")
        assert not AzureResourceMapper.names_match("myresource", "")
        assert not AzureResourceMapper.names_match("", "")

    def test_none_values(self):
        """Test matching with None values"""
        assert not AzureResourceMapper.names_match(None, "myresource")
        assert not AzureResourceMapper.names_match("myresource", None)
        assert not AzureResourceMapper.names_match(None, None)


class TestMapResource:
    """Tests for map_resource method"""

    def test_map_resource_with_sdk_object(self):
        """Test mapping an Azure SDK resource object"""

        # Create a mock Azure resource object
        class MockAzureResource:
            def __init__(self):
                self.id = "/subscriptions/12345/resourceGroups/rg/providers/Microsoft.Web/sites/myapp"
                self.name = "myapp"
                self.type = "Microsoft.Web/sites"
                self.location = "eastus"
                self.tags = {"env": "prod"}
                self.provisioning_state = "Succeeded"

        mock_resource = MockAzureResource()
        result = AzureResourceMapper.map_resource(mock_resource)

        assert result.id == mock_resource.id
        assert result.name == "myapp"
        assert result.resource_type == "app_service"
        assert result.cloud_provider == CloudProvider.AZURE
        assert result.region == "eastus"
        assert result.status == ResourceStatus.RUNNING

    def test_map_resource_minimal(self):
        """Test mapping a minimal Azure SDK resource object"""

        class MinimalResource:
            def __init__(self):
                self.id = "/subscriptions/12345/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/mystorage"
                self.name = "mystorage"
                self.type = "Microsoft.Storage/storageAccounts"
                self.location = "westus"

        minimal = MinimalResource()
        result = AzureResourceMapper.map_resource(minimal)

        assert result.name == "mystorage"
        assert result.resource_type == "storage_account"
        assert result.region == "westus"
        assert result.tags == {}
        assert result.status == ResourceStatus.UNKNOWN


class TestDuplicatePrevention:
    """Tests for duplicate prevention in DiscoveryResult"""

    def test_add_resource_no_duplicate(self):
        """Test adding resources without duplicates"""
        result = DiscoveryResult()

        resource1 = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            name="vm1",
            resource_type="virtual_machine",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        resource2 = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm2",
            name="vm2",
            resource_type="virtual_machine",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        result.add_resource(resource1)
        result.add_resource(resource2)

        assert len(result.resources) == 2

    def test_add_resource_with_duplicate(self):
        """Test that duplicate resources are not added"""
        result = DiscoveryResult()

        resource1 = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            name="vm1",
            resource_type="virtual_machine",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        # Same resource with same ID
        resource2 = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            name="vm1",
            resource_type="virtual_machine",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        result.add_resource(resource1)
        result.add_resource(resource2)

        # Should only have one resource
        assert len(result.resources) == 1

    def test_add_resource_multiple_duplicates(self):
        """Test that multiple attempts to add the same resource are handled"""
        result = DiscoveryResult()

        resource = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            name="vm1",
            resource_type="virtual_machine",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        # Add the same resource 5 times
        for _ in range(5):
            result.add_resource(resource)

        # Should only have one resource
        assert len(result.resources) == 1

    def test_add_dependency_no_duplicate(self):
        """Test adding dependencies without duplicates"""
        result = DiscoveryResult()

        dep1 = ResourceDependency(
            source_id="resource1",
            target_id="resource2",
            category=DependencyCategory.DATA,
            dependency_type=DependencyType.REQUIRED,
        )

        dep2 = ResourceDependency(
            source_id="resource2",
            target_id="resource3",
            category=DependencyCategory.DATA,
            dependency_type=DependencyType.REQUIRED,
        )

        result.add_dependency(dep1)
        result.add_dependency(dep2)

        assert len(result.dependencies) == 2

    def test_add_dependency_with_duplicate(self):
        """Test that duplicate dependencies are not added"""
        result = DiscoveryResult()

        dep1 = ResourceDependency(
            source_id="resource1",
            target_id="resource2",
            category=DependencyCategory.DATA,
            dependency_type=DependencyType.REQUIRED,
        )

        # Same dependency (same source and target)
        dep2 = ResourceDependency(
            source_id="resource1",
            target_id="resource2",
            category=DependencyCategory.NETWORK,
            dependency_type=DependencyType.OPTIONAL,
        )

        result.add_dependency(dep1)
        result.add_dependency(dep2)

        # Should only have one dependency
        assert len(result.dependencies) == 1

    def test_add_dependency_reverse_not_duplicate(self):
        """Test that reverse dependencies are not considered duplicates"""
        result = DiscoveryResult()

        dep1 = ResourceDependency(
            source_id="resource1",
            target_id="resource2",
            category=DependencyCategory.DATA,
            dependency_type=DependencyType.REQUIRED,
        )

        # Reverse dependency (different source and target)
        dep2 = ResourceDependency(
            source_id="resource2",
            target_id="resource1",
            category=DependencyCategory.DATA,
            dependency_type=DependencyType.REQUIRED,
        )

        result.add_dependency(dep1)
        result.add_dependency(dep2)

        # Should have both dependencies (they're different)
        assert len(result.dependencies) == 2


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""

    def test_servicebus_namespace_matching(self):
        """Test Service Bus namespace matching with different name formats"""
        result = DiscoveryResult()

        # Add a Service Bus namespace
        namespace = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.ServiceBus/namespaces/mybus",
            name="mybus",
            resource_type="servicebus_namespace",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            properties={
                "endpoint": "sb://mybus.servicebus.windows.net/",
            },
        )

        result.add_resource(namespace)

        # Test that we can match by FQDN
        assert AzureResourceMapper.names_match("mybus", "mybus.servicebus.windows.net")
        assert AzureResourceMapper.names_match(
            namespace.name, "mybus.servicebus.windows.net"
        )

    def test_parallel_discovery_deduplication(self):
        """Test that parallel discovery doesn't create duplicates"""
        result = DiscoveryResult()

        # Simulate two discovery methods finding the same resource
        resource_from_general = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Web/sites/myapp",
            name="myapp",
            resource_type="app_service",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        resource_from_specialized = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Web/sites/myapp",
            name="myapp",
            resource_type="app_service",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        result.add_resource(resource_from_general)
        result.add_resource(resource_from_specialized)

        # Should only have one resource
        assert len(result.resources) == 1
