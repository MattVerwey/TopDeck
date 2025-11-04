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
    
    def test_map_resource_type_vm_scale_set(self):
        """Test mapping VM scale set type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Compute/virtualMachineScaleSets")
        assert result == "vm_scale_set"
    
    def test_map_resource_type_container_instance(self):
        """Test mapping container instance type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.ContainerInstance/containerGroups")
        assert result == "container_instance"
    
    def test_map_resource_type_container_registry(self):
        """Test mapping container registry type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.ContainerRegistry/registries")
        assert result == "container_registry"
    
    def test_map_resource_type_app_service_plan(self):
        """Test mapping app service plan type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Web/serverfarms")
        assert result == "app_service_plan"
    
    def test_map_resource_type_postgresql_flexible(self):
        """Test mapping PostgreSQL flexible server type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.DBforPostgreSQL/flexibleServers")
        assert result == "postgresql_flexible_server"
    
    def test_map_resource_type_mysql_flexible(self):
        """Test mapping MySQL flexible server type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.DBforMySQL/flexibleServers")
        assert result == "mysql_flexible_server"
    
    def test_map_resource_type_eventhub(self):
        """Test mapping Event Hub type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.EventHub/namespaces")
        assert result == "eventhub_namespace"
    
    def test_map_resource_type_application_insights(self):
        """Test mapping Application Insights type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Insights/components")
        assert result == "application_insights"
    
    def test_map_resource_type_log_analytics(self):
        """Test mapping Log Analytics workspace type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.OperationalInsights/workspaces")
        assert result == "log_analytics_workspace"
    
    def test_map_resource_type_api_management(self):
        """Test mapping API Management type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.ApiManagement/service")
        assert result == "api_management"
    
    def test_map_resource_type_logic_app(self):
        """Test mapping Logic App type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Logic/workflows")
        assert result == "logic_app"
    
    def test_map_resource_type_data_factory(self):
        """Test mapping Data Factory type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.DataFactory/factories")
        assert result == "data_factory"
    
    def test_map_resource_type_synapse(self):
        """Test mapping Synapse workspace type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Synapse/workspaces")
        assert result == "synapse_workspace"
    
    def test_map_resource_type_iot_hub(self):
        """Test mapping IoT Hub type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Devices/IotHubs")
        assert result == "iot_hub"
    
    def test_map_resource_type_cognitive_services(self):
        """Test mapping Cognitive Services type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.CognitiveServices/accounts")
        assert result == "cognitive_services"
    
    def test_map_resource_type_front_door(self):
        """Test mapping Front Door type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Network/frontDoors")
        assert result == "front_door"
    
    def test_map_resource_type_private_endpoint(self):
        """Test mapping Private Endpoint type"""
        result = AzureResourceMapper.map_resource_type("Microsoft.Network/privateEndpoints")
        assert result == "private_endpoint"

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
