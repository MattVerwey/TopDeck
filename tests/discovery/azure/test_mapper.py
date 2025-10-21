"""
Tests for Azure resource mapper.
"""

from topdeck.discovery.azure.mapper import AzureResourceMapper
from topdeck.discovery.models import CloudProvider, ResourceStatus


class TestAzureResourceMapper:
    """Test Azure resource mapping functionality"""

    def test_map_resource_type_vm(self):
        """Test mapping virtual machine type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Compute/virtualMachines")
        assert result == "virtual_machine"

    def test_map_resource_type_app_service(self):
        """Test mapping app service type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Web/sites")
        assert result == "app_service"

    def test_map_resource_type_aks(self):
        """Test mapping AKS type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.ContainerService/managedClusters")
        assert result == "aks"

    def test_map_resource_type_unknown(self):
        """Test mapping unknown resource type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Unknown/resource")
        assert result == "unknown"

    def test_extract_resource_group(self):
        """Test extracting resource group from resource ID"""
        resource_id = (
            "/subscriptions/12345/resourceGroups/my-rg/"
            "providers/Microsoft.Compute/virtualMachines/vm1"
        )
        result = AzureResourceMapper.extract_resource_group(resource_id)
        assert result == "my-rg"

    def test_extract_resource_group_case_insensitive(self):
        """Test resource group extraction is case insensitive"""
        resource_id = (
            "/subscriptions/12345/ResourceGroups/My-RG/"
            "providers/Microsoft.Compute/virtualMachines/vm1"
        )
        result = AzureResourceMapper.extract_resource_group(resource_id)
        assert result == "My-RG"

    def test_extract_resource_group_none(self):
        """Test resource group extraction with invalid ID"""
        result = AzureResourceMapper.extract_resource_group("/invalid/id")
        assert result is None

    def test_extract_subscription_id(self):
        """Test extracting subscription ID from resource ID"""
        resource_id = (
            "/subscriptions/12345678-1234-1234-1234-123456789abc/"
            "resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/vm1"
        )
        result = AzureResourceMapper.extract_subscription_id(resource_id)
        assert result == "12345678-1234-1234-1234-123456789abc"

    def test_extract_subscription_id_none(self):
        """Test subscription ID extraction with invalid ID"""
        result = AzureResourceMapper.extract_subscription_id("/invalid/id")
        assert result is None

    def test_map_provisioning_state_succeeded(self):
        """Test mapping succeeded state"""
        result = AzureResourceMapper.map_provisioning_state_to_status("Succeeded")
        assert result == ResourceStatus.RUNNING

    def test_map_provisioning_state_failed(self):
        """Test mapping failed state"""
        result = AzureResourceMapper.map_provisioning_state_to_status("Failed")
        assert result == ResourceStatus.ERROR

    def test_map_provisioning_state_stopped(self):
        """Test mapping stopped state"""
        result = AzureResourceMapper.map_provisioning_state_to_status("Stopped")
        assert result == ResourceStatus.STOPPED

    def test_map_provisioning_state_updating(self):
        """Test mapping updating state"""
        result = AzureResourceMapper.map_provisioning_state_to_status("Updating")
        assert result == ResourceStatus.DEGRADED

    def test_map_provisioning_state_none(self):
        """Test mapping None state"""
        result = AzureResourceMapper.map_provisioning_state_to_status(None)
        assert result == ResourceStatus.UNKNOWN

    def test_extract_environment_from_tags_lowercase(self):
        """Test extracting environment from tags"""
        tags = {"environment": "prod", "owner": "team-a"}
        result = AzureResourceMapper.extract_environment_from_tags(tags)
        assert result == "prod"

    def test_extract_environment_from_tags_uppercase(self):
        """Test extracting environment from uppercase tags"""
        tags = {"Environment": "STAGING", "owner": "team-a"}
        result = AzureResourceMapper.extract_environment_from_tags(tags)
        assert result == "staging"

    def test_extract_environment_from_tags_env(self):
        """Test extracting environment from 'env' tag"""
        tags = {"env": "dev", "owner": "team-a"}
        result = AzureResourceMapper.extract_environment_from_tags(tags)
        assert result == "dev"

    def test_extract_environment_from_tags_none(self):
        """Test extracting environment with no tags"""
        result = AzureResourceMapper.extract_environment_from_tags(None)
        assert result is None

    def test_extract_environment_from_tags_missing(self):
        """Test extracting environment with no environment tag"""
        tags = {"owner": "team-a", "cost-center": "engineering"}
        result = AzureResourceMapper.extract_environment_from_tags(tags)
        assert result is None

    def test_map_azure_resource_complete(self):
        """Test mapping a complete Azure resource"""
        resource_id = (
            "/subscriptions/12345678-1234-1234-1234-123456789abc/"
            "resourceGroups/rg-prod/providers/Microsoft.Web/sites/my-app"
        )

        result = AzureResourceMapper.map_azure_resource(
            resource_id=resource_id,
            resource_name="my-app",
            resource_type="Microsoft.Web/sites",
            location="eastus",
            tags={"environment": "prod", "team": "platform"},
            properties={"sku": "Standard S1"},
            provisioning_state="Succeeded",
        )

        assert result.id == resource_id
        assert result.name == "my-app"
        assert result.resource_type == "app_service"
        assert result.cloud_provider == CloudProvider.AZURE
        assert result.region == "eastus"
        assert result.resource_group == "rg-prod"
        assert result.subscription_id == "12345678-1234-1234-1234-123456789abc"
        assert result.status == ResourceStatus.RUNNING
        assert result.environment == "prod"
        assert result.tags == {"environment": "prod", "team": "platform"}
        assert result.properties == {"sku": "Standard S1"}

    def test_map_azure_resource_minimal(self):
        """Test mapping a minimal Azure resource"""
        resource_id = (
            "/subscriptions/12345/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1"
        )

        result = AzureResourceMapper.map_azure_resource(
            resource_id=resource_id,
            resource_name="vm1",
            resource_type="Microsoft.Compute/virtualMachines",
            location="westus",
        )

        assert result.id == resource_id
        assert result.name == "vm1"
        assert result.resource_type == "virtual_machine"
        assert result.cloud_provider == CloudProvider.AZURE
        assert result.region == "westus"
        assert result.tags == {}
        assert result.properties == {}
        assert result.status == ResourceStatus.UNKNOWN
