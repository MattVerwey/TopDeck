#!/usr/bin/env python3
"""
Modernized Demo Data for TopDeck

Creates test resources with diverse, interesting names like:
- chocolate-cookie-api (microservice)
- victoria-sponge-db (database)
- rainbow-cupcake-gateway (load balancer)
- etc.

This provides more engaging and memorable test data instead of generic names.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from neo4j import GraphDatabase


class ModernDemoData:
    """Create modernized demo data with interesting names."""

    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.subscription_id = "12345678-1234-1234-1234-123456789abc"
        self.resource_group = "rg-bakery-prod"
        self.region = "eastus"

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()

    def clear_demo_data(self):
        """Clear existing demo data."""
        print("🧹 Clearing existing demo data...")
        with self.driver.session() as session:
            session.run("MATCH (n) WHERE n.demo = true DETACH DELETE n")
        print("   ✅ Demo data cleared\n")

    def create_modern_aks_cluster(self) -> str:
        """Create AKS cluster with modern name."""
        print("🔷 Creating Modern AKS Cluster...")
        
        with self.driver.session() as session:
            result = session.run("""
                CREATE (aks:Resource:AKS {
                    id: $id,
                    cloud_provider: 'azure',
                    resource_type: 'aks',
                    name: $name,
                    region: $region,
                    resource_group: $resource_group,
                    subscription_id: $subscription_id,
                    status: 'running',
                    environment: 'prod',
                    properties: $properties,
                    discovered_at: datetime(),
                    last_seen: datetime(),
                    demo: true
                })
                RETURN elementId(aks) as node_id, aks.id as resource_id
            """, {
                'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.ContainerService/managedClusters/sweet-treats-cluster",
                'name': 'sweet-treats-cluster',
                'region': self.region,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'properties': json.dumps({
                    'kubernetes_version': '1.28.0',
                    'node_count': 5,
                    'node_pools': ['system', 'bakery-apps'],
                    'network_plugin': 'azure',
                    'dns_prefix': 'sweet-treats'
                })
            })
            
            record = result.single()
            print(f"   ✅ Created AKS: sweet-treats-cluster")
            return record['resource_id']

    def create_modern_namespaces(self, aks_id: str) -> List[str]:
        """Create Kubernetes namespaces with modern names."""
        print("\n📦 Creating Modern Kubernetes Namespaces...")
        
        namespaces = [
            {
                'name': 'chocolate-factory',
                'labels': {'app': 'web', 'tier': 'frontend', 'flavor': 'chocolate'}
            },
            {
                'name': 'bakery-api',
                'labels': {'app': 'api', 'tier': 'backend', 'type': 'microservices'}
            },
            {
                'name': 'sweet-storage',
                'labels': {'app': 'data', 'tier': 'data', 'type': 'databases'}
            },
        ]
        
        namespace_ids = []
        
        with self.driver.session() as session:
            for ns in namespaces:
                result = session.run("""
                    CREATE (ns:Namespace {
                        name: $name,
                        cluster_id: $cluster_id,
                        labels: $labels,
                        created_at: datetime(),
                        demo: true
                    })
                    RETURN elementId(ns) as node_id
                """, {
                    'name': ns['name'],
                    'cluster_id': aks_id,
                    'labels': json.dumps(ns['labels'])
                })
                
                record = result.single()
                namespace_ids.append(record['node_id'])
                print(f"   ✅ Created namespace: {ns['name']}")
                
                # Link namespace to AKS
                session.run("""
                    MATCH (aks:Resource:AKS {id: $aks_id})
                    MATCH (ns:Namespace) WHERE elementId(ns) = $ns_id
                    CREATE (aks)-[:CONTAINS]->(ns)
                """, {'aks_id': aks_id, 'ns_id': record['node_id']})
        
        return namespace_ids

    def create_modern_pods(self, namespace_ids: List[str]) -> List[str]:
        """Create pods with fun, modern names."""
        print("\n🐳 Creating Modern Application Pods...")
        
        pods = [
            {
                'name': 'chocolate-cookie-api',
                'namespace_idx': 1,  # bakery-api
                'image': 'acr.io/chocolate-api:v2.1',
                'replicas': 3,
                'description': 'Chocolate cookie recipe API'
            },
            {
                'name': 'victoria-sponge-web',
                'namespace_idx': 0,  # chocolate-factory
                'image': 'acr.io/victoria-web:v1.8',
                'replicas': 2,
                'description': 'Victoria sponge cake ordering frontend'
            },
            {
                'name': 'rainbow-cupcake-processor',
                'namespace_idx': 1,  # bakery-api
                'image': 'acr.io/cupcake-processor:v3.0',
                'replicas': 4,
                'description': 'Rainbow cupcake order processor'
            },
            {
                'name': 'butter-cream-cache',
                'namespace_idx': 2,  # sweet-storage
                'image': 'redis:7.0',
                'replicas': 1,
                'description': 'Redis cache for recipe data'
            },
        ]
        
        pod_ids = []
        
        with self.driver.session() as session:
            for pod in pods:
                result = session.run("""
                    CREATE (pod:Pod {
                        name: $name,
                        image: $image,
                        replicas: $replicas,
                        description: $description,
                        status: 'running',
                        created_at: datetime(),
                        demo: true
                    })
                    RETURN elementId(pod) as node_id
                """, {
                    'name': pod['name'],
                    'image': pod['image'],
                    'replicas': pod['replicas'],
                    'description': pod['description']
                })
                
                record = result.single()
                pod_ids.append(record['node_id'])
                print(f"   ✅ Created pod: {pod['name']}")
                
                # Link pod to namespace
                ns_id = namespace_ids[pod['namespace_idx']]
                session.run("""
                    MATCH (ns:Namespace) WHERE elementId(ns) = $ns_id
                    MATCH (pod:Pod) WHERE elementId(pod) = $pod_id
                    CREATE (ns)-[:CONTAINS]->(pod)
                """, {'ns_id': ns_id, 'pod_id': record['node_id']})
        
        return pod_ids

    def create_modern_gateway(self) -> str:
        """Create Application Gateway with modern name."""
        print("\n🌐 Creating Modern Application Gateway...")
        
        with self.driver.session() as session:
            result = session.run("""
                CREATE (appgw:Resource:ApplicationGateway {
                    id: $id,
                    cloud_provider: 'azure',
                    resource_type: 'application_gateway',
                    name: $name,
                    region: $region,
                    resource_group: $resource_group,
                    subscription_id: $subscription_id,
                    status: 'running',
                    properties: $properties,
                    discovered_at: datetime(),
                    last_seen: datetime(),
                    demo: true
                })
                RETURN elementId(appgw) as node_id, appgw.id as resource_id
            """, {
                'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/applicationGateways/sweet-gateway",
                'name': 'sweet-gateway',
                'region': self.region,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'properties': json.dumps({
                    'sku': 'WAF_v2',
                    'tier': 'WAF_v2',
                    'capacity': 2,
                    'public_ip': '20.1.2.3',
                    'backend_pools': ['bakery-pool']
                })
            })
            
            record = result.single()
            print(f"   ✅ Created Application Gateway: sweet-gateway")
            return record['resource_id']

    def create_modern_databases(self) -> List[str]:
        """Create databases with modern names."""
        print("\n💾 Creating Modern Databases...")
        
        databases = [
            {
                'name': 'victoria-sponge-db',
                'type': 'postgresql',
                'description': 'Recipe and order database'
            },
            {
                'name': 'cookie-inventory-db',
                'type': 'cosmos_db',
                'description': 'Cookie inventory and stock tracking'
            },
        ]
        
        db_ids = []
        
        with self.driver.session() as session:
            for db in databases:
                result = session.run("""
                    CREATE (db:Resource:Database {
                        id: $id,
                        cloud_provider: 'azure',
                        resource_type: $type,
                        name: $name,
                        region: $region,
                        resource_group: $resource_group,
                        subscription_id: $subscription_id,
                        description: $description,
                        status: 'running',
                        discovered_at: datetime(),
                        last_seen: datetime(),
                        demo: true
                    })
                    RETURN elementId(db) as node_id, db.id as resource_id
                """, {
                    'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Database/{db['name']}",
                    'name': db['name'],
                    'type': db['type'],
                    'region': self.region,
                    'resource_group': self.resource_group,
                    'subscription_id': self.subscription_id,
                    'description': db['description']
                })
                
                record = result.single()
                db_ids.append(record['resource_id'])
                print(f"   ✅ Created database: {db['name']}")
        
        return db_ids

    def create_modern_storage(self) -> str:
        """Create Storage Account with modern name."""
        print("\n📦 Creating Modern Storage Account...")
        
        with self.driver.session() as session:
            result = session.run("""
                CREATE (storage:Resource:StorageAccount {
                    id: $id,
                    cloud_provider: 'azure',
                    resource_type: 'storage_account',
                    name: $name,
                    region: $region,
                    resource_group: $resource_group,
                    subscription_id: $subscription_id,
                    status: 'running',
                    properties: $properties,
                    discovered_at: datetime(),
                    last_seen: datetime(),
                    demo: true
                })
                RETURN elementId(storage) as node_id, storage.id as resource_id
            """, {
                'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Storage/storageAccounts/sweetimages001",
                'name': 'sweetimages001',
                'region': self.region,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'properties': json.dumps({
                    'sku': 'Standard_LRS',
                    'kind': 'StorageV2',
                    'containers': ['product-images', 'recipe-photos']
                })
            })
            
            record = result.single()
            print(f"   ✅ Created Storage Account: sweetimages001")
            return record['resource_id']

    def create_relationships(self, aks_id: str, gateway_id: str, db_ids: List[str], storage_id: str):
        """Create relationships between resources."""
        print("\n🔗 Creating Resource Relationships...")
        
        with self.driver.session() as session:
            # Gateway routes to AKS
            session.run("""
                MATCH (appgw:Resource:ApplicationGateway {id: $gateway_id})
                MATCH (aks:Resource:AKS {id: $aks_id})
                CREATE (appgw)-[:ROUTES_TO {
                    protocol: 'https',
                    port: 443,
                    backend_pool: 'bakery-pool'
                }]->(aks)
            """, {'gateway_id': gateway_id, 'aks_id': aks_id})
            print("   ✅ Gateway routes to AKS")
            
            # Pods depend on databases
            session.run("""
                MATCH (pod:Pod {name: 'chocolate-cookie-api', demo: true})
                MATCH (db:Resource:Database {name: 'victoria-sponge-db', demo: true})
                CREATE (pod)-[:DEPENDS_ON {
                    connection_type: 'postgresql',
                    purpose: 'recipe_data'
                }]->(db)
            """)
            print("   ✅ chocolate-cookie-api depends on victoria-sponge-db")
            
            session.run("""
                MATCH (pod:Pod {name: 'rainbow-cupcake-processor', demo: true})
                MATCH (db:Resource:Database {name: 'cookie-inventory-db', demo: true})
                CREATE (pod)-[:DEPENDS_ON {
                    connection_type: 'cosmos_db',
                    purpose: 'inventory_tracking'
                }]->(db)
            """)
            print("   ✅ rainbow-cupcake-processor depends on cookie-inventory-db")
            
            # Pods access storage
            session.run("""
                MATCH (pod:Pod {name: 'victoria-sponge-web', demo: true})
                MATCH (storage:Resource:StorageAccount {id: $storage_id})
                CREATE (pod)-[:ACCESSES {
                    container: 'product-images',
                    permission: 'read'
                }]->(storage)
            """, {'storage_id': storage_id})
            print("   ✅ victoria-sponge-web accesses sweetimages001")
            
            # Cache used by API
            session.run("""
                MATCH (api:Pod {name: 'chocolate-cookie-api', demo: true})
                MATCH (cache:Pod {name: 'butter-cream-cache', demo: true})
                CREATE (api)-[:USES {
                    purpose: 'caching',
                    connection_type: 'redis'
                }]->(cache)
            """)
            print("   ✅ chocolate-cookie-api uses butter-cream-cache")

    def run(self):
        """Run the complete demo data creation."""
        try:
            print("\n" + "=" * 70)
            print(" TOPDECK MODERNIZED DEMO DATA")
            print("=" * 70)
            print("\nCreating test resources with fun, memorable names!")
            print("Like chocolate-cookie-api, victoria-sponge-db, and more...\n")
            
            self.clear_demo_data()
            
            # Create resources
            aks_id = self.create_modern_aks_cluster()
            namespace_ids = self.create_modern_namespaces(aks_id)
            pod_ids = self.create_modern_pods(namespace_ids)
            gateway_id = self.create_modern_gateway()
            db_ids = self.create_modern_databases()
            storage_id = self.create_modern_storage()
            
            # Create relationships
            self.create_relationships(aks_id, gateway_id, db_ids, storage_id)
            
            print("\n" + "=" * 70)
            print(" ✅ MODERNIZED DEMO DATA CREATED SUCCESSFULLY")
            print("=" * 70)
            print("\nResources created:")
            print("  • 1 AKS Cluster (sweet-treats-cluster)")
            print("  • 3 Namespaces (chocolate-factory, bakery-api, sweet-storage)")
            print("  • 4 Pods (chocolate-cookie-api, victoria-sponge-web, etc.)")
            print("  • 1 Application Gateway (sweet-gateway)")
            print("  • 2 Databases (victoria-sponge-db, cookie-inventory-db)")
            print("  • 1 Storage Account (sweetimages001)")
            print("\nAll resources have fun, memorable names! 🎉")
            print("=" * 70 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    # Neo4j connection details
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "topdeck123"
    
    demo = ModernDemoData(uri, username, password)
    try:
        demo.run()
    finally:
        demo.close()


if __name__ == "__main__":
    main()
