/**
 * Mock topology data for demonstration and testing
 */

import type { TopologyGraph } from '../types';

export const mockTopologyData: TopologyGraph = {
  nodes: [
    // Frontend Layer
    {
      id: 'app-gateway-1',
      resource_type: 'application_gateway',
      name: 'AppGateway-Prod',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        backend_pools: 2,
      },
      metadata: {
        importance: 3,
      },
    },
    {
      id: 'load-balancer-1',
      resource_type: 'load_balancer',
      name: 'LB-Frontend',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
      },
      metadata: {
        importance: 2,
      },
    },

    // Application Layer
    {
      id: 'aks-cluster-1',
      resource_type: 'aks_cluster',
      name: 'AKS-Prod-Cluster',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        node_count: 5,
        cluster: 'AKS-Prod-Cluster',
      },
      metadata: {
        importance: 3,
      },
    },
    {
      id: 'pod-api-1',
      resource_type: 'pod',
      name: 'api-service-pod-1',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        namespace: 'production',
        cluster: 'AKS-Prod-Cluster',
      },
      metadata: {
        importance: 2,
      },
    },
    {
      id: 'pod-api-2',
      resource_type: 'pod',
      name: 'api-service-pod-2',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        namespace: 'production',
        cluster: 'AKS-Prod-Cluster',
      },
      metadata: {
        importance: 2,
      },
    },
    {
      id: 'pod-worker-1',
      resource_type: 'pod',
      name: 'worker-pod-1',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'degraded',
        namespace: 'production',
        cluster: 'AKS-Prod-Cluster',
      },
      metadata: {
        importance: 1,
      },
    },
    {
      id: 'app-service-1',
      resource_type: 'app_service',
      name: 'WebApp-Frontend',
      cloud_provider: 'azure',
      region: 'westus',
      properties: {
        health_status: 'healthy',
      },
      metadata: {
        importance: 2,
      },
    },

    // Data Layer
    {
      id: 'sql-db-1',
      resource_type: 'sql_database',
      name: 'SQL-Primary',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        size: '100GB',
      },
      metadata: {
        importance: 3,
      },
    },
    {
      id: 'cosmos-db-1',
      resource_type: 'cosmosdb',
      name: 'CosmosDB-Cache',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
      },
      metadata: {
        importance: 2,
      },
    },
    {
      id: 'storage-1',
      resource_type: 'storage',
      name: 'BlobStorage-Assets',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
      },
      metadata: {
        importance: 1,
      },
    },
    {
      id: 'cache-1',
      resource_type: 'cache',
      name: 'Redis-Session',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
      },
      metadata: {
        importance: 2,
      },
    },

    // AWS Services
    {
      id: 'rds-1',
      resource_type: 'database',
      name: 'RDS-Analytics',
      cloud_provider: 'aws',
      region: 'us-east-1',
      properties: {
        health_status: 'healthy',
      },
      metadata: {
        importance: 2,
      },
    },
    {
      id: 'lambda-1',
      resource_type: 'function_app',
      name: 'Lambda-DataProcessor',
      cloud_provider: 'aws',
      region: 'us-east-1',
      properties: {
        health_status: 'healthy',
      },
      metadata: {
        importance: 1,
      },
    },

    // Messaging Layer (Service Bus)
    {
      id: 'servicebus-ns-1',
      resource_type: 'servicebus_namespace',
      name: 'SB-Prod-Namespace',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        sku: 'Standard',
      },
      metadata: {
        importance: 3,
      },
    },
    {
      id: 'servicebus-topic-1',
      resource_type: 'servicebus_topic',
      name: 'orders-topic',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        namespace: 'SB-Prod-Namespace',
      },
      metadata: {
        importance: 2,
      },
    },
    {
      id: 'servicebus-topic-2',
      resource_type: 'servicebus_topic',
      name: 'events-topic',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        namespace: 'SB-Prod-Namespace',
      },
      metadata: {
        importance: 2,
      },
    },
    {
      id: 'servicebus-sub-1',
      resource_type: 'servicebus_subscription',
      name: 'order-processing-sub',
      cloud_provider: 'azure',
      region: 'eastus',
      properties: {
        health_status: 'healthy',
        namespace: 'SB-Prod-Namespace',
        topic: 'orders-topic',
      },
      metadata: {
        importance: 1,
      },
    },
  ],
  edges: [
    // Network flow: Gateway -> Load Balancer
    {
      source_id: 'app-gateway-1',
      target_id: 'load-balancer-1',
      relationship_type: 'routes_to',
      flow_type: 'https',
      properties: {
        port: 443,
        protocol: 'HTTPS',
      },
    },

    // Load Balancer -> AKS Cluster
    {
      source_id: 'load-balancer-1',
      target_id: 'aks-cluster-1',
      relationship_type: 'routes_to',
      flow_type: 'http',
      properties: {
        port: 80,
      },
    },

    // AKS -> API Pods
    {
      source_id: 'aks-cluster-1',
      target_id: 'pod-api-1',
      relationship_type: 'deployed_to',
      properties: {},
    },
    {
      source_id: 'aks-cluster-1',
      target_id: 'pod-api-2',
      relationship_type: 'deployed_to',
      properties: {},
    },
    {
      source_id: 'aks-cluster-1',
      target_id: 'pod-worker-1',
      relationship_type: 'deployed_to',
      properties: {},
    },

    // Gateway -> App Service (alternative path)
    {
      source_id: 'app-gateway-1',
      target_id: 'app-service-1',
      relationship_type: 'routes_to',
      flow_type: 'https',
      properties: {
        port: 443,
      },
    },

    // API Pods -> SQL Database
    {
      source_id: 'pod-api-1',
      target_id: 'sql-db-1',
      relationship_type: 'accesses',
      flow_type: 'database',
      properties: {
        protocol: 'SQL',
      },
    },
    {
      source_id: 'pod-api-2',
      target_id: 'sql-db-1',
      relationship_type: 'accesses',
      flow_type: 'database',
      properties: {
        protocol: 'SQL',
      },
    },

    // API Pods -> Cosmos DB
    {
      source_id: 'pod-api-1',
      target_id: 'cosmos-db-1',
      relationship_type: 'accesses',
      flow_type: 'database',
      properties: {},
    },

    // API Pods -> Cache
    {
      source_id: 'pod-api-1',
      target_id: 'cache-1',
      relationship_type: 'uses',
      flow_type: 'cache',
      properties: {},
    },
    {
      source_id: 'pod-api-2',
      target_id: 'cache-1',
      relationship_type: 'uses',
      flow_type: 'cache',
      properties: {},
    },

    // Worker Pod -> Storage
    {
      source_id: 'pod-worker-1',
      target_id: 'storage-1',
      relationship_type: 'stores_in',
      flow_type: 'storage',
      properties: {},
    },

    // Worker Pod -> SQL Database
    {
      source_id: 'pod-worker-1',
      target_id: 'sql-db-1',
      relationship_type: 'accesses',
      flow_type: 'database',
      properties: {},
    },

    // App Service -> RDS (cross-cloud)
    {
      source_id: 'app-service-1',
      target_id: 'rds-1',
      relationship_type: 'accesses',
      flow_type: 'database',
      properties: {
        cross_cloud: true,
      },
    },

    // Lambda -> SQL Database (cross-cloud)
    {
      source_id: 'lambda-1',
      target_id: 'sql-db-1',
      relationship_type: 'accesses',
      flow_type: 'database',
      properties: {
        cross_cloud: true,
      },
    },

    // Worker -> Lambda
    {
      source_id: 'pod-worker-1',
      target_id: 'lambda-1',
      relationship_type: 'uses',
      flow_type: 'https',
      properties: {},
    },

    // Service Bus Topology
    // Namespace contains topics
    {
      source_id: 'servicebus-ns-1',
      target_id: 'servicebus-topic-1',
      relationship_type: 'contains',
      flow_type: 'message_queue',
      properties: {},
    },
    {
      source_id: 'servicebus-ns-1',
      target_id: 'servicebus-topic-2',
      relationship_type: 'contains',
      flow_type: 'message_queue',
      properties: {},
    },

    // Topic has subscription
    {
      source_id: 'servicebus-topic-1',
      target_id: 'servicebus-sub-1',
      relationship_type: 'contains',
      flow_type: 'message_queue',
      properties: {},
    },

    // API pods publish to Service Bus topics
    {
      source_id: 'pod-api-1',
      target_id: 'servicebus-topic-1',
      relationship_type: 'publishes_to',
      flow_type: 'message_queue',
      properties: {},
    },
    {
      source_id: 'pod-api-2',
      target_id: 'servicebus-topic-2',
      relationship_type: 'publishes_to',
      flow_type: 'message_queue',
      properties: {},
    },

    // Worker pod subscribes from Service Bus
    {
      source_id: 'servicebus-sub-1',
      target_id: 'pod-worker-1',
      relationship_type: 'subscribes_from',
      flow_type: 'message_queue',
      properties: {},
    },
  ],
  metadata: {
    total_nodes: 17,
    total_edges: 26,
  },
};
