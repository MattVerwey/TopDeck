#!/usr/bin/env python3
"""
Network Graph Demo for TopDeck

Demonstrates network graph relationships with Azure resources:
- AKS (Azure Kubernetes Service)
- Entra ID (Managed Identity & Service Principal)
- Application Gateway
- Storage Account
- VM Scale Set
- Applications on AKS (Pods & Namespaces)

This script creates sample data showing real-world relationships between these resources.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from neo4j import GraphDatabase


class NetworkGraphDemo:
    """Demo for network graph relationships with Azure resources."""

    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.subscription_id = "12345678-1234-1234-1234-123456789abc"
        self.resource_group = "rg-demo-prod"
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

    def create_aks_cluster(self) -> str:
        """Create AKS cluster node."""
        print("🔷 Creating AKS Cluster...")
        
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
                'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.ContainerService/managedClusters/aks-demo-prod",
                'name': 'aks-demo-prod',
                'region': self.region,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'properties': json.dumps({
                    'kubernetes_version': '1.28.0',
                    'node_count': 3,
                    'node_pools': ['system', 'user'],
                    'network_plugin': 'azure',
                    'dns_prefix': 'aks-demo'
                })
            })
            
            record = result.single()
            print(f"   ✅ Created AKS: aks-demo-prod")
            return record['resource_id']

    def create_namespaces(self, aks_id: str) -> List[str]:
        """Create Kubernetes namespaces."""
        print("\n📦 Creating Kubernetes Namespaces...")
        
        namespaces = [
            {
                'name': 'frontend',
                'labels': {'app': 'web', 'tier': 'frontend'}
            },
            {
                'name': 'backend',
                'labels': {'app': 'api', 'tier': 'backend'}
            },
            {
                'name': 'data',
                'labels': {'app': 'database', 'tier': 'data'}
            }
        ]
        
        namespace_ids = []
        
        with self.driver.session() as session:
            for ns in namespaces:
                result = session.run("""
                    CREATE (ns:Namespace {
                        id: $id,
                        name: $name,
                        cluster_id: $cluster_id,
                        labels: $labels,
                        created_at: datetime(),
                        demo: true
                    })
                    RETURN elementId(ns) as node_id, ns.id as namespace_id
                """, {
                    'id': f"{aks_id}/namespaces/{ns['name']}",
                    'name': ns['name'],
                    'cluster_id': aks_id,
                    'labels': json.dumps(ns['labels'])
                })
                
                record = result.single()
                namespace_ids.append(record['namespace_id'])
                print(f"   ✅ Created Namespace: {ns['name']}")
                
                # Link namespace to AKS
                session.run("""
                    MATCH (aks:Resource {id: $aks_id})
                    MATCH (ns:Namespace {id: $ns_id})
                    CREATE (aks)-[:CONTAINS]->(ns)
                """, {
                    'aks_id': aks_id,
                    'ns_id': record['namespace_id']
                })
        
        return namespace_ids

    def create_pods(self, namespace_ids: List[str]) -> List[str]:
        """Create Kubernetes pods."""
        print("\n🐳 Creating Kubernetes Pods...")
        
        pods = [
            {
                'name': 'frontend-web-1',
                'namespace_idx': 0,  # frontend namespace
                'image': 'webapp:v1.2.3',
                'replicas': 3
            },
            {
                'name': 'backend-api-1',
                'namespace_idx': 1,  # backend namespace
                'image': 'api:v2.1.0',
                'replicas': 5
            },
            {
                'name': 'backend-worker-1',
                'namespace_idx': 1,  # backend namespace
                'image': 'worker:v2.1.0',
                'replicas': 2
            }
        ]
        
        pod_ids = []
        
        with self.driver.session() as session:
            for pod in pods:
                ns_id = namespace_ids[pod['namespace_idx']]
                
                result = session.run("""
                    CREATE (pod:Pod {
                        id: $id,
                        name: $name,
                        namespace: $namespace,
                        cluster_id: $cluster_id,
                        phase: 'Running',
                        image: $image,
                        replicas: $replicas,
                        created_at: datetime(),
                        demo: true
                    })
                    RETURN elementId(pod) as node_id, pod.id as pod_id
                """, {
                    'id': f"{ns_id}/pods/{pod['name']}",
                    'name': pod['name'],
                    'namespace': ns_id,
                    'cluster_id': namespace_ids[0].split('/namespaces/')[0],
                    'image': pod['image'],
                    'replicas': pod['replicas']
                })
                
                record = result.single()
                pod_ids.append(record['pod_id'])
                print(f"   ✅ Created Pod: {pod['name']} (replicas: {pod['replicas']})")
                
                # Link pod to namespace
                session.run("""
                    MATCH (ns:Namespace {id: $ns_id})
                    MATCH (pod:Pod {id: $pod_id})
                    CREATE (ns)-[:CONTAINS]->(pod)
                """, {
                    'ns_id': ns_id,
                    'pod_id': record['pod_id']
                })
        
        return pod_ids

    def create_application_gateway(self) -> str:
        """Create Application Gateway node."""
        print("\n🌐 Creating Application Gateway...")
        
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
                    environment: 'prod',
                    properties: $properties,
                    discovered_at: datetime(),
                    last_seen: datetime(),
                    demo: true
                })
                RETURN elementId(appgw) as node_id, appgw.id as resource_id
            """, {
                'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/applicationGateways/appgw-demo",
                'name': 'appgw-demo',
                'region': self.region,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'properties': json.dumps({
                    'sku': 'WAF_v2',
                    'tier': 'WAF_v2',
                    'capacity': 2,
                    'frontend_port': 443,
                    'protocol': 'https',
                    'backend_pools': ['aks-backend']
                })
            })
            
            record = result.single()
            print(f"   ✅ Created Application Gateway: appgw-demo")
            return record['resource_id']

    def create_storage_account(self) -> str:
        """Create Storage Account node."""
        print("\n💾 Creating Storage Account...")
        
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
                    environment: 'prod',
                    properties: $properties,
                    discovered_at: datetime(),
                    last_seen: datetime(),
                    demo: true
                })
                RETURN elementId(storage) as node_id, storage.id as resource_id
            """, {
                'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Storage/storageAccounts/stdemoprod001",
                'name': 'stdemoprod001',
                'region': self.region,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'properties': json.dumps({
                    'sku': 'Standard_LRS',
                    'kind': 'StorageV2',
                    'access_tier': 'Hot',
                    'https_only': True,
                    'containers': ['uploads', 'backups', 'logs']
                })
            })
            
            record = result.single()
            print(f"   ✅ Created Storage Account: stdemoprod001")
            return record['resource_id']

    def create_vm_scale_set(self) -> str:
        """Create VM Scale Set node."""
        print("\n🖥️  Creating VM Scale Set...")
        
        with self.driver.session() as session:
            result = session.run("""
                CREATE (vmss:Resource:VMSS {
                    id: $id,
                    cloud_provider: 'azure',
                    resource_type: 'vm_scale_set',
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
                RETURN elementId(vmss) as node_id, vmss.id as resource_id
            """, {
                'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Compute/virtualMachineScaleSets/vmss-workers",
                'name': 'vmss-workers',
                'region': self.region,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'properties': json.dumps({
                    'sku': 'Standard_D2s_v3',
                    'capacity': 5,
                    'upgrade_policy': 'Automatic',
                    'os': 'Ubuntu 22.04',
                    'os_disk_size_gb': 128
                })
            })
            
            record = result.single()
            print(f"   ✅ Created VM Scale Set: vmss-workers")
            return record['resource_id']

    def create_managed_identity(self, aks_id: str) -> str:
        """Create Managed Identity for AKS."""
        print("\n🔐 Creating Managed Identity (Entra ID)...")
        
        with self.driver.session() as session:
            result = session.run("""
                CREATE (mi:ManagedIdentity {
                    id: $id,
                    name: $name,
                    identity_type: 'SystemAssigned',
                    principal_id: $principal_id,
                    client_id: $client_id,
                    tenant_id: $tenant_id,
                    region: $region,
                    resource_group: $resource_group,
                    subscription_id: $subscription_id,
                    assigned_to_resource_id: $assigned_to,
                    assigned_to_resource_type: 'aks',
                    created_at: datetime(),
                    last_seen: datetime(),
                    demo: true
                })
                RETURN elementId(mi) as node_id, mi.id as identity_id
            """, {
                'id': f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-aks-demo",
                'name': 'id-aks-demo',
                'principal_id': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
                'client_id': 'bbbbbbbb-cccc-dddd-eeee-ffffffffffff',
                'tenant_id': 'cccccccc-dddd-eeee-ffff-000000000000',
                'region': self.region,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'assigned_to': aks_id
            })
            
            record = result.single()
            print(f"   ✅ Created Managed Identity: id-aks-demo")
            return record['identity_id']

    def create_service_principal(self) -> str:
        """Create Service Principal for automation."""
        print("\n👤 Creating Service Principal (Entra ID)...")
        
        with self.driver.session() as session:
            result = session.run("""
                CREATE (sp:ServicePrincipal {
                    id: $id,
                    app_id: $app_id,
                    display_name: $display_name,
                    tenant_id: $tenant_id,
                    service_principal_type: 'Application',
                    password_credentials_count: 1,
                    key_credentials_count: 0,
                    enabled: true,
                    created_at: datetime(),
                    last_seen: datetime(),
                    demo: true
                })
                RETURN elementId(sp) as node_id, sp.id as sp_id
            """, {
                'id': 'dddddddd-eeee-ffff-0000-111111111111',
                'app_id': 'eeeeeeee-ffff-0000-1111-222222222222',
                'display_name': 'sp-demo-deployment',
                'tenant_id': 'cccccccc-dddd-eeee-ffff-000000000000'
            })
            
            record = result.single()
            print(f"   ✅ Created Service Principal: sp-demo-deployment")
            return record['sp_id']

    def create_relationships(
        self,
        aks_id: str,
        appgw_id: str,
        storage_id: str,
        vmss_id: str,
        mi_id: str,
        sp_id: str,
        namespace_ids: List[str],
        pod_ids: List[str]
    ):
        """Create relationships between all resources."""
        print("\n🔗 Creating Resource Relationships...")
        
        with self.driver.session() as session:
            # Application Gateway routes to AKS
            session.run("""
                MATCH (appgw:Resource {id: $appgw_id})
                MATCH (aks:Resource {id: $aks_id})
                CREATE (appgw)-[:ROUTES_TO {
                    protocol: 'https',
                    port: 443,
                    backend_pool: 'aks-backend',
                    routing_rule: 'default',
                    created_at: datetime()
                }]->(aks)
            """, {'appgw_id': appgw_id, 'aks_id': aks_id})
            print("   ✅ Application Gateway -> AKS (ROUTES_TO)")
            
            # AKS authenticates with Managed Identity
            session.run("""
                MATCH (aks:Resource {id: $aks_id})
                MATCH (mi:ManagedIdentity {id: $mi_id})
                CREATE (aks)-[:AUTHENTICATES_WITH {
                    identity_type: 'SystemAssigned',
                    created_at: datetime()
                }]->(mi)
            """, {'aks_id': aks_id, 'mi_id': mi_id})
            print("   ✅ AKS -> Managed Identity (AUTHENTICATES_WITH)")
            
            # Managed Identity accesses Storage Account
            session.run("""
                MATCH (mi:ManagedIdentity {id: $mi_id})
                MATCH (storage:Resource {id: $storage_id})
                CREATE (mi)-[:ACCESSES {
                    permission: 'Storage Blob Data Contributor',
                    scope: 'container',
                    created_at: datetime()
                }]->(storage)
            """, {'mi_id': mi_id, 'storage_id': storage_id})
            print("   ✅ Managed Identity -> Storage Account (ACCESSES)")
            
            # Service Principal has role on AKS
            session.run("""
                MATCH (sp:ServicePrincipal {id: $sp_id})
                MATCH (aks:Resource {id: $aks_id})
                CREATE (sp)-[:HAS_ROLE {
                    role: 'Azure Kubernetes Service Cluster Admin Role',
                    scope: 'cluster',
                    created_at: datetime()
                }]->(aks)
            """, {'sp_id': sp_id, 'aks_id': aks_id})
            print("   ✅ Service Principal -> AKS (HAS_ROLE)")
            
            # Service Principal has role on VMSS
            session.run("""
                MATCH (sp:ServicePrincipal {id: $sp_id})
                MATCH (vmss:Resource {id: $vmss_id})
                CREATE (sp)-[:HAS_ROLE {
                    role: 'Virtual Machine Contributor',
                    scope: 'resource',
                    created_at: datetime()
                }]->(vmss)
            """, {'sp_id': sp_id, 'vmss_id': vmss_id})
            print("   ✅ Service Principal -> VM Scale Set (HAS_ROLE)")
            
            # Pods depend on Storage Account (backend namespace pods)
            if len(pod_ids) >= 2:
                # Backend API pod uses storage
                session.run("""
                    MATCH (pod:Pod {id: $pod_id})
                    MATCH (storage:Resource {id: $storage_id})
                    CREATE (pod)-[:DEPENDS_ON {
                        category: 'storage',
                        strength: 0.8,
                        dependency_type: 'required',
                        mount_path: '/data',
                        created_at: datetime()
                    }]->(storage)
                """, {'pod_id': pod_ids[1], 'storage_id': storage_id})
                print("   ✅ Backend API Pod -> Storage Account (DEPENDS_ON)")
            
            # Frontend pods depend on backend pods (HTTP calls)
            if len(pod_ids) >= 2:
                session.run("""
                    MATCH (frontend:Pod {id: $frontend_id})
                    MATCH (backend:Pod {id: $backend_id})
                    CREATE (frontend)-[:DEPENDS_ON {
                        category: 'network',
                        strength: 0.95,
                        dependency_type: 'required',
                        protocol: 'http',
                        port: 8080,
                        created_at: datetime()
                    }]->(backend)
                """, {'frontend_id': pod_ids[0], 'backend_id': pod_ids[1]})
                print("   ✅ Frontend Pod -> Backend Pod (DEPENDS_ON)")
            
            # AKS connects to VMSS for worker nodes
            session.run("""
                MATCH (aks:Resource {id: $aks_id})
                MATCH (vmss:Resource {id: $vmss_id})
                CREATE (aks)-[:USES {
                    purpose: 'compute',
                    node_pool: 'user',
                    created_at: datetime()
                }]->(vmss)
            """, {'aks_id': aks_id, 'vmss_id': vmss_id})
            print("   ✅ AKS -> VM Scale Set (USES)")

    def create_applications(self, namespace_ids: List[str]) -> List[str]:
        """Create Application nodes representing apps on AKS."""
        print("\n📱 Creating Applications...")
        
        applications = [
            {
                'name': 'web-frontend',
                'namespace_idx': 0,
                'deployment_method': 'aks',
                'health_score': 95.5,
                'repository_url': 'https://github.com/company/web-frontend'
            },
            {
                'name': 'api-backend',
                'namespace_idx': 1,
                'deployment_method': 'aks',
                'health_score': 98.2,
                'repository_url': 'https://github.com/company/api-backend'
            }
        ]
        
        app_ids = []
        
        with self.driver.session() as session:
            for app in applications:
                ns_id = namespace_ids[app['namespace_idx']]
                
                result = session.run("""
                    CREATE (app:Application {
                        id: $id,
                        name: $name,
                        description: $description,
                        owner_team: 'Platform Team',
                        deployment_method: $deployment_method,
                        environment: 'prod',
                        health_score: $health_score,
                        repository_url: $repository_url,
                        version: '1.0.0',
                        created_at: datetime(),
                        demo: true
                    })
                    RETURN elementId(app) as node_id, app.id as app_id
                """, {
                    'id': f"app-{app['name']}",
                    'name': app['name'],
                    'description': f"{app['name']} application",
                    'deployment_method': app['deployment_method'],
                    'health_score': app['health_score'],
                    'repository_url': app['repository_url']
                })
                
                record = result.single()
                app_ids.append(record['app_id'])
                print(f"   ✅ Created Application: {app['name']}")
                
                # Link application to namespace (deployed to)
                session.run("""
                    MATCH (app:Application {id: $app_id})
                    MATCH (ns:Namespace {id: $ns_id})
                    CREATE (app)-[:DEPLOYED_TO {
                        deployed_at: datetime(),
                        version: '1.0.0'
                    }]->(ns)
                """, {
                    'app_id': record['app_id'],
                    'ns_id': ns_id
                })
        
        return app_ids

    def print_summary(self):
        """Print summary of created resources and relationships."""
        print("\n" + "=" * 80)
        print("📊 NETWORK GRAPH SUMMARY")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Count nodes
            result = session.run("""
                MATCH (n) WHERE n.demo = true
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n📦 Resources Created:")
            for record in result:
                label = record['label']
                count = record['count']
                print(f"   • {label}: {count}")
            
            # Count relationships
            result = session.run("""
                MATCH (n)-[r]->(m) WHERE n.demo = true AND m.demo = true
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\n🔗 Relationships Created:")
            for record in result:
                rel_type = record['rel_type']
                count = record['count']
                print(f"   • {rel_type}: {count}")

    def run_demo(self):
        """Run the complete demo."""
        print("\n" + "=" * 80)
        print("🚀 TOPDECK NETWORK GRAPH DEMO")
        print("=" * 80)
        print("\nThis demo creates a sample network graph with:")
        print("  • AKS Cluster with namespaces and pods")
        print("  • Application Gateway (ingress)")
        print("  • Storage Account (persistent data)")
        print("  • VM Scale Set (compute nodes)")
        print("  • Managed Identity (Entra ID)")
        print("  • Service Principal (Entra ID)")
        print("  • Applications deployed on AKS")
        print("\n" + "=" * 80 + "\n")
        
        try:
            # Clear existing demo data
            self.clear_demo_data()
            
            # Create resources
            aks_id = self.create_aks_cluster()
            namespace_ids = self.create_namespaces(aks_id)
            pod_ids = self.create_pods(namespace_ids)
            appgw_id = self.create_application_gateway()
            storage_id = self.create_storage_account()
            vmss_id = self.create_vm_scale_set()
            mi_id = self.create_managed_identity(aks_id)
            sp_id = self.create_service_principal()
            app_ids = self.create_applications(namespace_ids)
            
            # Create relationships
            self.create_relationships(
                aks_id, appgw_id, storage_id, vmss_id,
                mi_id, sp_id, namespace_ids, pod_ids
            )
            
            # Print summary
            self.print_summary()
            
            print("\n" + "=" * 80)
            print("✅ DEMO COMPLETE")
            print("=" * 80)
            print("\nYou can now:")
            print("  1. Open Neo4j Browser at http://localhost:7474")
            print("  2. Run queries to explore the graph:")
            print("     MATCH (n) WHERE n.demo = true RETURN n LIMIT 100")
            print("     MATCH path = (n)-[r]->(m) WHERE n.demo = true RETURN path")
            print("\n" + "=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error running demo: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    # Configuration
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "topdeck123"
    
    demo = NetworkGraphDemo(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        success = demo.run_demo()
        sys.exit(0 if success else 1)
    finally:
        demo.close()


if __name__ == "__main__":
    main()
