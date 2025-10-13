#!/usr/bin/env python3
"""
Visualize the demo network graph.

This script queries the Neo4j database and provides visualizations
and query examples for exploring the network graph.
"""

import sys
import json
from neo4j import GraphDatabase


def visualize_graph():
    """Visualize the demo network graph."""
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "topdeck123"
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    print("\n" + "=" * 80)
    print("🎨 NETWORK GRAPH VISUALIZATION")
    print("=" * 80 + "\n")
    
    try:
        with driver.session() as session:
            # Query 1: All demo nodes
            print("Query 1: All Demo Resources")
            print("-" * 80)
            print("Cypher: MATCH (n) WHERE n.demo = true RETURN n LIMIT 25")
            print()
            
            result = session.run("""
                MATCH (n) WHERE n.demo = true 
                RETURN labels(n) as labels, n.name as name, n.id as id
                ORDER BY labels[0], name
            """)
            
            print("Resources:")
            for record in result:
                label = record['labels'][0] if record['labels'] else 'Unknown'
                name = record.get('name', 'N/A')
                print(f"  • [{label}] {name}")
            
            # Query 2: Full topology graph
            print("\n" + "-" * 80)
            print("\nQuery 2: Full Network Topology")
            print("-" * 80)
            print("Cypher: MATCH path = (n)-[r]->(m) WHERE n.demo = true AND m.demo = true")
            print("        RETURN path")
            print()
            
            result = session.run("""
                MATCH path = (n)-[r]->(m) 
                WHERE n.demo = true AND m.demo = true
                RETURN n.name as source, type(r) as relationship, m.name as target
                ORDER BY source, relationship
            """)
            
            print("Relationships:")
            for record in result:
                source = record.get('source', 'N/A')
                rel = record['relationship']
                target = record.get('target', 'N/A')
                print(f"  • {source} -[{rel}]-> {target}")
            
            # Query 3: AKS Cluster Hierarchy
            print("\n" + "-" * 80)
            print("\nQuery 3: AKS Cluster Hierarchy (AKS → Namespaces → Pods)")
            print("-" * 80)
            print("Cypher: MATCH path = (aks:AKS)-[:CONTAINS*]->(child)")
            print("        WHERE aks.demo = true RETURN path")
            print()
            
            result = session.run("""
                MATCH (aks:Resource:AKS {demo: true})
                      -[:CONTAINS]->
                      (ns:Namespace)
                      -[:CONTAINS]->
                      (pod:Pod)
                RETURN aks.name as aks, ns.name as namespace, pod.name as pod, pod.replicas as replicas
            """)
            
            print("Hierarchy:")
            current_ns = None
            for record in result:
                aks = record['aks']
                ns = record['namespace']
                pod = record['pod']
                replicas = record['replicas']
                
                if current_ns != ns:
                    print(f"\n  {aks}")
                    print(f"    └── {ns} namespace")
                    current_ns = ns
                
                print(f"        └── {pod} (x{replicas} replicas)")
            
            # Query 4: Identity and Access
            print("\n" + "-" * 80)
            print("\nQuery 4: Identity & Access Chain")
            print("-" * 80)
            print("Cypher: MATCH path = (aks:AKS)-[:AUTHENTICATES_WITH]->(mi:ManagedIdentity)")
            print("                     -[:ACCESSES]->(storage:StorageAccount)")
            print("        RETURN path")
            print()
            
            result = session.run("""
                MATCH (aks:Resource:AKS {demo: true})
                      -[:AUTHENTICATES_WITH]->
                      (mi:ManagedIdentity)
                      -[:ACCESSES]->
                      (storage:Resource:StorageAccount)
                RETURN aks.name as aks, mi.name as identity, storage.name as storage
            """)
            
            print("Access Chain:")
            for record in result:
                aks = record['aks']
                identity = record['identity']
                storage = record['storage']
                print(f"  {aks} → {identity} → {storage}")
            
            # Query 5: Service Principal Roles
            print("\n" + "-" * 80)
            print("\nQuery 5: Service Principal Roles")
            print("-" * 80)
            print("Cypher: MATCH (sp:ServicePrincipal)-[r:HAS_ROLE]->(resource)")
            print("        WHERE sp.demo = true RETURN sp, r, resource")
            print()
            
            result = session.run("""
                MATCH (sp:ServicePrincipal {demo: true})
                      -[r:HAS_ROLE]->
                      (resource)
                RETURN sp.display_name as sp, r.role as role, 
                       labels(resource)[0] as resource_type, resource.name as resource_name
            """)
            
            print("Roles:")
            for record in result:
                sp = record['sp']
                role = record['role']
                resource_type = record['resource_type']
                resource_name = record['resource_name']
                print(f"  • {sp}")
                print(f"    Role: {role}")
                print(f"    On: [{resource_type}] {resource_name}")
                print()
            
            # Query 6: Application Gateway to Pods
            print("-" * 80)
            print("\nQuery 6: Traffic Flow (App Gateway → AKS → Pods)")
            print("-" * 80)
            print("Cypher: MATCH path = (appgw:ApplicationGateway)-[:ROUTES_TO]->(aks:AKS)")
            print("                     -[:CONTAINS*]->(pod:Pod)")
            print("        RETURN path")
            print()
            
            result = session.run("""
                MATCH (appgw:Resource:ApplicationGateway {demo: true})
                      -[r:ROUTES_TO]->
                      (aks:Resource:AKS)
                RETURN appgw.name as gateway, r.protocol as protocol, 
                       r.port as port, aks.name as aks
            """)
            
            print("Traffic Flow:")
            for record in result:
                gateway = record['gateway']
                protocol = record['protocol']
                port = record['port']
                aks = record['aks']
                print(f"  {gateway} -[{protocol}:{port}]-> {aks}")
                
                # Get pods
                pod_result = session.run("""
                    MATCH (aks:Resource:AKS {demo: true})
                          -[:CONTAINS]->
                          (ns:Namespace)
                          -[:CONTAINS]->
                          (pod:Pod)
                    RETURN ns.name as namespace, pod.name as pod
                """)
                
                for pod_record in pod_result:
                    ns = pod_record['namespace']
                    pod = pod_record['pod']
                    print(f"    → {ns}/{pod}")
            
            # Query 7: Pod Dependencies
            print("\n" + "-" * 80)
            print("\nQuery 7: Pod Dependencies")
            print("-" * 80)
            print("Cypher: MATCH (pod:Pod)-[r:DEPENDS_ON]->(target)")
            print("        WHERE pod.demo = true RETURN pod, r, target")
            print()
            
            result = session.run("""
                MATCH (pod:Pod {demo: true})
                      -[r:DEPENDS_ON]->
                      (target)
                WHERE target.demo = true
                RETURN pod.name as pod, r.category as category, 
                       r.dependency_type as dep_type,
                       labels(target)[0] as target_type, target.name as target_name
            """)
            
            print("Dependencies:")
            for record in result:
                pod = record['pod']
                category = record['category']
                dep_type = record['dep_type']
                target_type = record['target_type']
                target_name = record['target_name']
                print(f"  • {pod} depends on [{target_type}] {target_name}")
                print(f"    Category: {category}, Type: {dep_type}")
            
            # Query 8: Applications
            print("\n" + "-" * 80)
            print("\nQuery 8: Applications Deployed on AKS")
            print("-" * 80)
            print("Cypher: MATCH (app:Application)-[:DEPLOYED_TO]->(ns:Namespace)")
            print("        WHERE app.demo = true RETURN app, ns")
            print()
            
            result = session.run("""
                MATCH (app:Application {demo: true})
                      -[:DEPLOYED_TO]->
                      (ns:Namespace)
                RETURN app.name as app, app.health_score as health, 
                       app.repository_url as repo, ns.name as namespace
            """)
            
            print("Applications:")
            for record in result:
                app = record['app']
                health = record['health']
                repo = record['repo']
                namespace = record['namespace']
                print(f"  • {app}")
                print(f"    Health Score: {health}")
                print(f"    Namespace: {namespace}")
                print(f"    Repository: {repo}")
                print()
            
            # Summary Statistics
            print("=" * 80)
            print("\n📊 GRAPH STATISTICS")
            print("=" * 80 + "\n")
            
            # Node counts by type
            result = session.run("""
                MATCH (n) WHERE n.demo = true
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """)
            
            print("Node Counts:")
            total_nodes = 0
            for record in result:
                node_type = record['type']
                count = record['count']
                total_nodes += count
                print(f"  • {node_type}: {count}")
            print(f"\nTotal Nodes: {total_nodes}")
            
            # Relationship counts
            result = session.run("""
                MATCH (n)-[r]->(m) 
                WHERE n.demo = true AND m.demo = true
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\nRelationship Counts:")
            total_rels = 0
            for record in result:
                rel_type = record['type']
                count = record['count']
                total_rels += count
                print(f"  • {rel_type}: {count}")
            print(f"\nTotal Relationships: {total_rels}")
            
            # Graph summary
            print("\n" + "=" * 80)
            print("✅ VISUALIZATION COMPLETE")
            print("=" * 80)
            print("\nTo explore the graph in Neo4j Browser:")
            print("  1. Open http://localhost:7474")
            print("  2. Login with username: neo4j, password: topdeck123")
            print("  3. Try these queries:")
            print()
            print("     # View all demo resources")
            print("     MATCH (n) WHERE n.demo = true RETURN n LIMIT 100")
            print()
            print("     # View full topology")
            print("     MATCH path = (n)-[r]->(m)")
            print("     WHERE n.demo = true AND m.demo = true")
            print("     RETURN path")
            print()
            print("     # View AKS hierarchy")
            print("     MATCH path = (aks:AKS)-[:CONTAINS*]->(child)")
            print("     WHERE aks.demo = true")
            print("     RETURN path")
            print()
            print("=" * 80 + "\n")
            
    except Exception as e:
        print(f"\n❌ Error visualizing graph: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        driver.close()
    
    return True


if __name__ == "__main__":
    success = visualize_graph()
    sys.exit(0 if success else 1)
