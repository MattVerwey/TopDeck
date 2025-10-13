#!/usr/bin/env python3
"""
Risk Analysis Demo with Network Graph Test Data

This script demonstrates the complete risk analysis workflow using
the test data from network graph demo, showing:
1. Dependencies found in code, portal, and AKS nodes
2. SPOF detection
3. Blast radius calculation
4. Risk scoring
5. End-to-end risk assessment

Usage:
    python scripts/demo_risk_analysis.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from topdeck.storage.neo4j_client import Neo4jClient
from topdeck.analysis.risk.analyzer import RiskAnalyzer


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"🎯 {text}")
    print("=" * 80 + "\n")


def print_section(text: str):
    """Print formatted section."""
    print("\n" + "-" * 80)
    print(f"📊 {text}")
    print("-" * 80 + "\n")


def check_demo_data(client: Neo4jClient) -> bool:
    """Check if demo data exists."""
    print_section("Checking Demo Data")
    
    with client.session() as session:
        result = session.run("""
            MATCH (n) WHERE n.demo = true
            RETURN count(n) as count
        """)
        record = result.single()
        count = record['count'] if record else 0
        
        if count > 0:
            print(f"✅ Found {count} demo resources in Neo4j")
            return True
        else:
            print("❌ No demo data found!")
            print("\nPlease run the network graph demo first:")
            print("   python scripts/demo_network_graph.py")
            return False


def show_demo_resources(client: Neo4jClient):
    """Show all demo resources."""
    print_section("Demo Resources")
    
    with client.session() as session:
        result = session.run("""
            MATCH (n) WHERE n.demo = true
            RETURN labels(n) as labels, n.name as name, n.id as id
            ORDER BY labels[0], name
            LIMIT 20
        """)
        
        print("Available resources:")
        for record in result:
            label = record['labels'][0] if record['labels'] else 'Unknown'
            name = record['name']
            print(f"  • {label:20s} {name}")


def show_dependencies(client: Neo4jClient):
    """Show dependency relationships in demo data."""
    print_section("Dependency Analysis")
    
    with client.session() as session:
        # Show DEPENDS_ON relationships
        result = session.run("""
            MATCH (source)-[r:DEPENDS_ON]->(target)
            WHERE source.demo = true AND target.demo = true
            RETURN 
                labels(source)[0] as source_type,
                source.name as source_name,
                labels(target)[0] as target_type,
                target.name as target_name,
                r.protocol as protocol,
                r.port as port
        """)
        
        print("🔗 DEPENDS_ON Relationships:")
        count = 0
        for record in result:
            count += 1
            source_type = record['source_type']
            source_name = record['source_name']
            target_type = record['target_type']
            target_name = record['target_name']
            protocol = record.get('protocol', 'N/A')
            port = record.get('port', 'N/A')
            
            print(f"\n  {count}. {source_type}: {source_name}")
            print(f"     └─> {target_type}: {target_name}")
            if protocol != 'N/A':
                print(f"         Protocol: {protocol}, Port: {port}")
        
        print(f"\n✅ Found {count} dependency relationships")
        
        # Show other relationships
        result = session.run("""
            MATCH (source)-[r]->(target)
            WHERE source.demo = true AND target.demo = true
            AND type(r) <> 'DEPENDS_ON'
            RETURN 
                type(r) as rel_type,
                labels(source)[0] as source_type,
                source.name as source_name,
                labels(target)[0] as target_type,
                target.name as target_name
            LIMIT 10
        """)
        
        print("\n🔗 Other Relationships:")
        count = 0
        for record in result:
            count += 1
            rel_type = record['rel_type']
            source_type = record['source_type']
            source_name = record['source_name']
            target_type = record['target_type']
            target_name = record['target_name']
            
            print(f"\n  {count}. {source_type}: {source_name}")
            print(f"     --[{rel_type}]--> {target_type}: {target_name}")
        
        print(f"\n✅ Found {count} other relationships")


def test_risk_analysis_on_aks(client: Neo4jClient, analyzer: RiskAnalyzer):
    """Test risk analysis on AKS cluster."""
    print_section("Risk Analysis: AKS Cluster")
    
    # Find AKS cluster
    with client.session() as session:
        result = session.run("""
            MATCH (aks:Resource:AKS {demo: true})
            RETURN aks.id as id, aks.name as name
            LIMIT 1
        """)
        record = result.single()
        
        if not record:
            print("❌ AKS cluster not found")
            return
        
        aks_id = record['id']
        aks_name = record['name']
        
    print(f"Analyzing: {aks_name}")
    print(f"ID: {aks_id}")
    
    try:
        # Perform risk analysis
        assessment = analyzer.analyze_resource(aks_id)
        
        print(f"\n📊 Risk Assessment Results:")
        print(f"   Risk Score: {assessment.risk_score}/100")
        print(f"   Risk Level: {assessment.risk_level}")
        print(f"   Criticality: {assessment.criticality_score}/100")
        print(f"   Single Point of Failure: {'Yes ⚠️' if assessment.single_point_of_failure else 'No ✅'}")
        print(f"   Blast Radius: {assessment.blast_radius} resources")
        print(f"   Dependencies: {assessment.dependency_count}")
        print(f"   Dependents: {assessment.dependents_count}")
        
        if assessment.recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(assessment.recommendations, 1):
                print(f"   {i}. {rec}")
        
        return True
    except Exception as e:
        print(f"❌ Error analyzing AKS: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_analysis_on_pods(client: Neo4jClient, analyzer: RiskAnalyzer):
    """Test risk analysis on pods."""
    print_section("Risk Analysis: Pods")
    
    # Find pods
    with client.session() as session:
        result = session.run("""
            MATCH (pod:Pod {demo: true})
            RETURN pod.id as id, pod.name as name
            ORDER BY pod.name
            LIMIT 3
        """)
        
        pods = [dict(record) for record in result]
        
        if not pods:
            print("❌ No pods found")
            return
        
    print(f"Found {len(pods)} pods to analyze\n")
    
    for pod in pods:
        pod_id = pod['id']
        pod_name = pod['name']
        
        print(f"\n🔍 Analyzing: {pod_name}")
        print(f"   ID: {pod_id}")
        
        try:
            assessment = analyzer.analyze_resource(pod_id)
            
            print(f"   Risk Score: {assessment.risk_score}/100")
            print(f"   Risk Level: {assessment.risk_level}")
            print(f"   SPOF: {'Yes ⚠️' if assessment.single_point_of_failure else 'No ✅'}")
            print(f"   Blast Radius: {assessment.blast_radius}")
            print(f"   Dependencies: {assessment.dependency_count}")
            print(f"   Dependents: {assessment.dependents_count}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


def test_spof_detection(analyzer: RiskAnalyzer):
    """Test single point of failure detection."""
    print_section("Single Point of Failure Detection")
    
    try:
        spofs = analyzer.identify_single_points_of_failure()
        
        if spofs:
            print(f"⚠️  Found {len(spofs)} Single Points of Failure:\n")
            
            for i, spof in enumerate(spofs, 1):
                print(f"{i}. {spof.resource_name} ({spof.resource_type})")
                print(f"   Risk Score: {spof.risk_score}/100")
                print(f"   Dependents: {spof.dependents_count}")
                print(f"   Blast Radius: {spof.blast_radius}")
                print(f"   Recommendations:")
                for rec in spof.recommendations[:2]:
                    print(f"      • {rec}")
                print()
        else:
            print("✅ No single points of failure detected")
            print("   This is great! Your infrastructure has redundancy.")
        
        return True
    except Exception as e:
        print(f"❌ Error detecting SPOFs: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_blast_radius(client: Neo4jClient, analyzer: RiskAnalyzer):
    """Test blast radius calculation."""
    print_section("Blast Radius Calculation")
    
    # Find a resource with dependents
    with client.session() as session:
        result = session.run("""
            MATCH (r:Resource {demo: true})<-[:DEPENDS_ON]-(dependent)
            WITH r, count(dependent) as dep_count
            WHERE dep_count > 0
            RETURN r.id as id, r.name as name, dep_count
            ORDER BY dep_count DESC
            LIMIT 1
        """)
        record = result.single()
        
        if not record:
            print("❌ No resources with dependents found")
            return
        
        resource_id = record['id']
        resource_name = record['name']
        
    print(f"Calculating blast radius for: {resource_name}")
    print(f"ID: {resource_id}\n")
    
    try:
        blast_radius = analyzer.calculate_blast_radius(resource_id)
        
        print(f"💥 Blast Radius Analysis:")
        print(f"   Total Affected: {blast_radius.total_affected} resources")
        print(f"   Directly Affected: {len(blast_radius.directly_affected)}")
        print(f"   Indirectly Affected: {len(blast_radius.indirectly_affected)}")
        print(f"   Estimated Downtime: {blast_radius.estimated_downtime_seconds}s")
        print(f"   User Impact: {blast_radius.user_impact}")
        
        if blast_radius.directly_affected:
            print(f"\n   Directly Affected Resources:")
            for resource in blast_radius.directly_affected[:5]:
                print(f"      • {resource['name']} ({resource['type']})")
        
        if blast_radius.indirectly_affected:
            print(f"\n   Indirectly Affected Resources:")
            for resource in blast_radius.indirectly_affected[:5]:
                print(f"      • {resource['name']} ({resource['type']})")
        
        if blast_radius.affected_services:
            print(f"\n   Affected Services:")
            for service, count in blast_radius.affected_services.items():
                print(f"      • {service}: {count}")
        
        return True
    except Exception as e:
        print(f"❌ Error calculating blast radius: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the complete risk analysis demo."""
    print_header("TOPDECK RISK ANALYSIS DEMO")
    print("This demo shows risk analysis working with network graph test data")
    print("including dependencies in code, portal, and AKS nodes.\n")
    
    # Connect to Neo4j
    print("🔌 Connecting to Neo4j...")
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "topdeck123"
    
    try:
        client = Neo4jClient(uri, username, password)
        client.connect()
        print("✅ Connected to Neo4j\n")
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        print("\nPlease ensure Neo4j is running:")
        print("   docker-compose up -d neo4j")
        return False
    
    try:
        # Check demo data
        if not check_demo_data(client):
            return False
        
        # Show resources
        show_demo_resources(client)
        
        # Show dependencies
        show_dependencies(client)
        
        # Create risk analyzer
        print_section("Initializing Risk Analyzer")
        analyzer = RiskAnalyzer(client)
        print("✅ Risk Analyzer initialized")
        
        # Test risk analysis on AKS
        test_risk_analysis_on_aks(client, analyzer)
        
        # Test risk analysis on pods
        test_risk_analysis_on_pods(client, analyzer)
        
        # Test SPOF detection
        test_spof_detection(analyzer)
        
        # Test blast radius
        test_blast_radius(client, analyzer)
        
        # Summary
        print_header("DEMO COMPLETE")
        print("✅ Risk analysis demonstrated successfully!")
        print("\nKey Features Demonstrated:")
        print("   1. ✅ Dependency detection (code, portal, AKS nodes)")
        print("   2. ✅ Risk scoring and assessment")
        print("   3. ✅ Single Point of Failure detection")
        print("   4. ✅ Blast radius calculation")
        print("   5. ✅ Risk recommendations")
        
        print("\n📚 Next Steps:")
        print("   1. View data in Neo4j Browser: http://localhost:7474")
        print("   2. Run API server: python -m topdeck")
        print("   3. Try API endpoints: http://localhost:8000/api/docs")
        print("   4. See PHASE_3_README.md for more examples")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        client.close()
        print("\n🔌 Neo4j connection closed")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
