# Azure Resource Type Mapping

This document provides a comprehensive reference for Azure resource type mapping in TopDeck.

## Overview

TopDeck's Azure discovery system maps native Azure resource types (e.g., `Microsoft.Compute/virtualMachines`) to normalized, cloud-agnostic resource types (e.g., `virtual_machine`). This normalization allows for consistent handling of resources across multiple cloud providers.

## Mapping Statistics

- **Total Mappings**: 130 resource types
- **Resource Providers Covered**: 56 Azure resource providers
- **Coverage**: Significantly improved from the original 23 mappings

## Supported Resource Types

### Compute Resources (8 types)
- `Microsoft.Compute/virtualMachines` → `virtual_machine`
- `Microsoft.Compute/virtualMachineScaleSets` → `vm_scale_set`
- `Microsoft.Compute/availabilitySets` → `availability_set`
- `Microsoft.Compute/disks` → `managed_disk`
- `Microsoft.Compute/snapshots` → `disk_snapshot`
- `Microsoft.Compute/images` → `vm_image`
- `Microsoft.Compute/galleries` → `shared_image_gallery`
- `Microsoft.Compute/cloudServices` → `cloud_service`

### Web & App Services (6 types)
- `Microsoft.Web/sites` → `app_service`
- `Microsoft.Web/serverfarms` → `app_service_plan`
- `Microsoft.Web/sites/slots` → `app_service_slot`
- `Microsoft.Web/staticSites` → `static_web_app`
- `Microsoft.Web/certificates` → `app_service_certificate`
- `Microsoft.Web/hostingEnvironments` → `app_service_environment`

### Container Services (3 types)
- `Microsoft.ContainerService/managedClusters` → `aks`
- `Microsoft.ContainerInstance/containerGroups` → `container_instance`
- `Microsoft.ContainerRegistry/registries` → `container_registry`

### Database Services

#### SQL (5 types)
- `Microsoft.Sql/servers` → `sql_server`
- `Microsoft.Sql/servers/databases` → `sql_database`
- `Microsoft.Sql/managedInstances` → `sql_managed_instance`
- `Microsoft.Sql/managedInstances/databases` → `sql_managed_instance_database`
- `Microsoft.Sql/servers/elasticPools` → `sql_elastic_pool`

#### PostgreSQL (3 types)
- `Microsoft.DBforPostgreSQL/servers` → `postgresql_server`
- `Microsoft.DBforPostgreSQL/flexibleServers` → `postgresql_flexible_server`
- `Microsoft.DBforPostgreSQL/serverGroupsv2` → `postgresql_hyperscale`

#### MySQL (2 types)
- `Microsoft.DBforMySQL/servers` → `mysql_server`
- `Microsoft.DBforMySQL/flexibleServers` → `mysql_flexible_server`

#### MariaDB (1 type)
- `Microsoft.DBforMariaDB/servers` → `mariadb_server`

#### NoSQL & Cache (3 types)
- `Microsoft.DocumentDB/databaseAccounts` → `cosmos_db`
- `Microsoft.Cache/redis` → `redis_cache`
- `Microsoft.Cache/redisEnterprise` → `redis_enterprise`

### Storage Services (7 types)
- `Microsoft.Storage/storageAccounts` → `storage_account`
- `Microsoft.Storage/storageAccounts/blobServices` → `blob_service`
- `Microsoft.Storage/storageAccounts/fileServices` → `file_service`
- `Microsoft.Storage/storageAccounts/queueServices` → `queue_service`
- `Microsoft.Storage/storageAccounts/tableServices` → `table_service`
- `Microsoft.DataLakeStore/accounts` → `data_lake_store`
- `Microsoft.DataLakeAnalytics/accounts` → `data_lake_analytics`

### Networking (30 types)

#### Core Networking (7 types)
- `Microsoft.Network/virtualNetworks` → `virtual_network`
- `Microsoft.Network/virtualNetworks/subnets` → `subnet`
- `Microsoft.Network/networkInterfaces` → `network_interface`
- `Microsoft.Network/networkSecurityGroups` → `network_security_group`
- `Microsoft.Network/publicIPAddresses` → `public_ip`
- `Microsoft.Network/publicIPPrefixes` → `public_ip_prefix`
- `Microsoft.Network/routeTables` → `route_table`
- `Microsoft.Network/natGateways` → `nat_gateway`

#### Load Balancing (4 types)
- `Microsoft.Network/loadBalancers` → `load_balancer`
- `Microsoft.Network/applicationGateways` → `application_gateway`
- `Microsoft.Network/frontDoors` → `front_door`
- `Microsoft.Network/trafficManagerProfiles` → `traffic_manager`

#### Connectivity (8 types)
- `Microsoft.Network/virtualNetworkGateways` → `vpn_gateway`
- `Microsoft.Network/localNetworkGateways` → `local_network_gateway`
- `Microsoft.Network/connections` → `vpn_connection`
- `Microsoft.Network/expressRouteCircuits` → `express_route_circuit`
- `Microsoft.Network/expressRouteGateways` → `express_route_gateway`
- `Microsoft.Network/virtualWans` → `virtual_wan`
- `Microsoft.Network/vpnGateways` → `vpn_gateway_v2`
- `Microsoft.Network/vpnSites` → `vpn_site`

#### DNS & Security (5 types)
- `Microsoft.Network/dnsZones` → `dns_zone`
- `Microsoft.Network/privateDnsZones` → `private_dns_zone`
- `Microsoft.Network/azureFirewalls` → `azure_firewall`
- `Microsoft.Network/firewallPolicies` → `firewall_policy`
- `Microsoft.Network/ddosProtectionPlans` → `ddos_protection`

#### Private Connectivity (3 types)
- `Microsoft.Network/privateEndpoints` → `private_endpoint`
- `Microsoft.Network/privateLinkServices` → `private_link_service`
- `Microsoft.Network/serviceEndpointPolicies` → `service_endpoint_policy`

#### Monitoring (2 types)
- `Microsoft.Network/networkWatchers` → `network_watcher`
- `Microsoft.Network/networkWatchers/connectionMonitors` → `connection_monitor`

### Identity & Access Management (6 types)
- `Microsoft.ManagedIdentity/userAssignedIdentities` → `managed_identity`
- `Microsoft.Authorization/roleAssignments` → `role_assignment`
- `Microsoft.Authorization/roleDefinitions` → `role_definition`
- `Microsoft.Authorization/policyAssignments` → `policy_assignment`
- `Microsoft.Authorization/policyDefinitions` → `policy_definition`

### Key Management (2 types)
- `Microsoft.KeyVault/vaults` → `key_vault`
- `Microsoft.KeyVault/managedHSMs` → `managed_hsm`

### Messaging & Event Services (10 types)
- `Microsoft.ServiceBus/namespaces` → `servicebus_namespace`
- `Microsoft.ServiceBus/namespaces/topics` → `servicebus_topic`
- `Microsoft.ServiceBus/namespaces/queues` → `servicebus_queue`
- `Microsoft.ServiceBus/namespaces/topics/subscriptions` → `servicebus_subscription`
- `Microsoft.EventHub/namespaces` → `eventhub_namespace`
- `Microsoft.EventHub/namespaces/eventhubs` → `eventhub`
- `Microsoft.EventGrid/topics` → `eventgrid_topic`
- `Microsoft.EventGrid/domains` → `eventgrid_domain`
- `Microsoft.EventGrid/systemTopics` → `eventgrid_system_topic`
- `Microsoft.NotificationHubs/namespaces` → `notification_hub_namespace`
- `Microsoft.NotificationHubs/namespaces/notificationHubs` → `notification_hub`

### Integration Services (6 types)
- `Microsoft.Logic/workflows` → `logic_app`
- `Microsoft.ApiManagement/service` → `api_management`
- `Microsoft.DataFactory/factories` → `data_factory`
- `Microsoft.DataFactory/factories/pipelines` → `data_factory_pipeline`
- `Microsoft.ServiceBus/namespaces/hybridConnections` → `hybrid_connection`
- `Microsoft.Relay/namespaces` → `relay_namespace`

### Analytics & Big Data (7 types)
- `Microsoft.Synapse/workspaces` → `synapse_workspace`
- `Microsoft.Databricks/workspaces` → `databricks_workspace`
- `Microsoft.HDInsight/clusters` → `hdinsight_cluster`
- `Microsoft.StreamAnalytics/streamingjobs` → `stream_analytics`
- `Microsoft.Kusto/clusters` → `data_explorer_cluster`
- `Microsoft.AnalysisServices/servers` → `analysis_services`
- `Microsoft.PowerBIDedicated/capacities` → `power_bi_embedded`

### AI & Machine Learning (3 types)
- `Microsoft.CognitiveServices/accounts` → `cognitive_services`
- `Microsoft.MachineLearningServices/workspaces` → `ml_workspace`
- `Microsoft.BotService/botServices` → `bot_service`

### IoT Services (4 types)
- `Microsoft.Devices/IotHubs` → `iot_hub`
- `Microsoft.Devices/provisioningServices` → `iot_dps`
- `Microsoft.IoTCentral/IoTApps` → `iot_central`
- `Microsoft.TimeSeriesInsights/environments` → `time_series_insights`

### Monitoring & Management (9 types)
- `Microsoft.Insights/components` → `application_insights`
- `Microsoft.OperationalInsights/workspaces` → `log_analytics_workspace`
- `Microsoft.Insights/actionGroups` → `action_group`
- `Microsoft.Insights/metricAlerts` → `metric_alert`
- `Microsoft.Insights/activityLogAlerts` → `activity_log_alert`
- `Microsoft.Insights/scheduledQueryRules` → `log_alert`
- `Microsoft.Monitor/accounts` → `azure_monitor_workspace`
- `Microsoft.Automation/automationAccounts` → `automation_account`

### DevOps & Deployment (3 types)
- `Microsoft.Resources/deployments` → `arm_deployment`
- `Microsoft.Resources/resourceGroups` → `resource_group`
- `Microsoft.ManagedServices/registrationDefinitions` → `lighthouse_definition`

### Other Services (8 types)
- `Microsoft.Media/mediaservices` → `media_services`
- `Microsoft.Search/searchServices` → `cognitive_search`
- `Microsoft.RecoveryServices/vaults` → `recovery_services_vault`
- `Microsoft.DataProtection/backupVaults` → `backup_vault`
- `Microsoft.Migrate/assessmentProjects` → `migrate_project`
- `Microsoft.Migrate/migrateProjects` → `azure_migrate`
- `Microsoft.Batch/batchAccounts` → `batch_account`
- `Microsoft.Blockchain/blockchainMembers` → `blockchain_service`

### Security (2 types)
- `Microsoft.Security/securityContacts` → `security_contact`
- `Microsoft.Security/assessments` → `security_assessment`

### Hybrid & Multi-Cloud (3 types)
- `Microsoft.HybridCompute/machines` → `arc_server`
- `Microsoft.Kubernetes/connectedClusters` → `arc_kubernetes`
- `Microsoft.AzureStackHCI/clusters` → `azure_stack_hci`

## Unknown Resources

Resources with types not in the mapping dictionary are marked as `unknown`. If you encounter many unknown resources in your environment, consider:

1. Checking the Azure resource type in the Azure Portal
2. Adding the mapping to `src/topdeck/discovery/azure/mapper.py`
3. Submitting a pull request to expand the mapping coverage

## Dependency Patterns

The discovery system also includes dependency patterns that detect relationships between resources. These patterns have been expanded to cover the new resource types, including:

- Container Registry → AKS dependencies
- API Management → Application Insights logging
- Logic Apps → Service Bus messaging
- Data Factory → Storage Account and SQL Database connections
- Synapse Analytics → Storage Account requirements
- Event Hub → Storage Account capture
- IoT Hub → Event Hub routing

## Usage

The mapper is used automatically during Azure resource discovery:

```python
from topdeck.discovery.azure import AzureDiscoverer

discoverer = AzureDiscoverer(
    subscription_id="your-subscription-id",
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

result = await discoverer.discover_all_resources()
```

Resources are automatically mapped during discovery, and the normalized type is available in the `resource_type` field of each `DiscoveredResource`.

## Testing

To verify the mappings work correctly, run:

```bash
pytest tests/discovery/azure/test_mapper.py -v
```

## References

- [Azure Resource Manager Resource Providers](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-services-resource-providers)
- [Azure Resource Types Reference](https://learn.microsoft.com/en-us/azure/templates/)
- [Azure Resource Graph Supported Tables](https://learn.microsoft.com/en-us/azure/governance/resource-graph/reference/supported-tables-resources)
