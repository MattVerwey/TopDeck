#!/usr/bin/env python3
"""
Standalone test runner for network graph demo.
This script runs tests without needing the full test infrastructure.
"""

import sys
from neo4j import GraphDatabase


def run_tests():
    """Run all demo tests."""
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "topdeck123"
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    tests_passed = 0
    tests_failed = 0
    
    print("\n" + "=" * 80)
    print("🧪 RUNNING NETWORK GRAPH DEMO TESTS")
    print("=" * 80 + "\n")
    
    try:
        with driver.session() as session:
            # Test 1: Demo resources created
            print("Test 1: Demo resources created...")
            result = session.run("MATCH (n) WHERE n.demo = true RETURN count(n) as count")
            record = result.single()
            if record['count'] > 0:
                print(f"   ✅ PASS - Found {record['count']} demo resources\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - No demo resources found\n")
                tests_failed += 1
            
            # Test 2: AKS cluster exists
            print("Test 2: AKS cluster exists...")
            result = session.run("""
                MATCH (aks:Resource:AKS {demo: true})
                RETURN aks.name as name, aks.resource_type as type
            """)
            record = result.single()
            if record and record['name'] == 'aks-demo-prod' and record['type'] == 'aks':
                print(f"   ✅ PASS - AKS cluster 'aks-demo-prod' found\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - AKS cluster not found or incorrect\n")
                tests_failed += 1
            
            # Test 3: Namespaces exist
            print("Test 3: Kubernetes namespaces exist...")
            result = session.run("MATCH (ns:Namespace {demo: true}) RETURN count(ns) as count")
            record = result.single()
            if record['count'] == 3:
                print(f"   ✅ PASS - Found 3 namespaces\n")
                tests_passed += 1
            else:
                print(f"   ❌ FAIL - Expected 3 namespaces, found {record['count']}\n")
                tests_failed += 1
            
            # Test 4: Pods exist
            print("Test 4: Pods exist...")
            result = session.run("MATCH (pod:Pod {demo: true}) RETURN count(pod) as count")
            record = result.single()
            if record['count'] == 3:
                print(f"   ✅ PASS - Found 3 pods\n")
                tests_passed += 1
            else:
                print(f"   ❌ FAIL - Expected 3 pods, found {record['count']}\n")
                tests_failed += 1
            
            # Test 5: Application Gateway exists
            print("Test 5: Application Gateway exists...")
            result = session.run("""
                MATCH (appgw:Resource:ApplicationGateway {demo: true})
                RETURN appgw.name as name
            """)
            record = result.single()
            if record and record['name'] == 'appgw-demo':
                print(f"   ✅ PASS - Application Gateway 'appgw-demo' found\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Application Gateway not found\n")
                tests_failed += 1
            
            # Test 6: Storage Account exists
            print("Test 6: Storage Account exists...")
            result = session.run("""
                MATCH (storage:Resource:StorageAccount {demo: true})
                RETURN storage.name as name
            """)
            record = result.single()
            if record and record['name'] == 'stdemoprod001':
                print(f"   ✅ PASS - Storage Account 'stdemoprod001' found\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Storage Account not found\n")
                tests_failed += 1
            
            # Test 7: VM Scale Set exists
            print("Test 7: VM Scale Set exists...")
            result = session.run("""
                MATCH (vmss:Resource:VMSS {demo: true})
                RETURN vmss.name as name
            """)
            record = result.single()
            if record and record['name'] == 'vmss-workers':
                print(f"   ✅ PASS - VM Scale Set 'vmss-workers' found\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - VM Scale Set not found\n")
                tests_failed += 1
            
            # Test 8: Managed Identity exists
            print("Test 8: Managed Identity exists...")
            result = session.run("""
                MATCH (mi:ManagedIdentity {demo: true})
                RETURN mi.name as name, mi.identity_type as type
            """)
            record = result.single()
            if record and record['name'] == 'id-aks-demo' and record['type'] == 'SystemAssigned':
                print(f"   ✅ PASS - Managed Identity 'id-aks-demo' found\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Managed Identity not found\n")
                tests_failed += 1
            
            # Test 9: Service Principal exists
            print("Test 9: Service Principal exists...")
            result = session.run("""
                MATCH (sp:ServicePrincipal {demo: true})
                RETURN sp.display_name as name
            """)
            record = result.single()
            if record and record['name'] == 'sp-demo-deployment':
                print(f"   ✅ PASS - Service Principal 'sp-demo-deployment' found\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Service Principal not found\n")
                tests_failed += 1
            
            # Test 10: Applications exist
            print("Test 10: Applications exist...")
            result = session.run("MATCH (app:Application {demo: true}) RETURN count(app) as count")
            record = result.single()
            if record['count'] == 2:
                print(f"   ✅ PASS - Found 2 applications\n")
                tests_passed += 1
            else:
                print(f"   ❌ FAIL - Expected 2 applications, found {record['count']}\n")
                tests_failed += 1
            
            # Test 11: ROUTES_TO relationship
            print("Test 11: Application Gateway routes to AKS...")
            result = session.run("""
                MATCH (appgw:Resource:ApplicationGateway {demo: true})
                      -[r:ROUTES_TO]->
                      (aks:Resource:AKS {demo: true})
                RETURN r.protocol as protocol, r.port as port
            """)
            record = result.single()
            if record and record['protocol'] == 'https' and record['port'] == 443:
                print(f"   ✅ PASS - ROUTES_TO relationship exists (https:443)\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - ROUTES_TO relationship not found or incorrect\n")
                tests_failed += 1
            
            # Test 12: AUTHENTICATES_WITH relationship
            print("Test 12: AKS authenticates with Managed Identity...")
            result = session.run("""
                MATCH (aks:Resource:AKS {demo: true})
                      -[r:AUTHENTICATES_WITH]->
                      (mi:ManagedIdentity {demo: true})
                RETURN r.identity_type as type
            """)
            record = result.single()
            if record and record['type'] == 'SystemAssigned':
                print(f"   ✅ PASS - AUTHENTICATES_WITH relationship exists\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - AUTHENTICATES_WITH relationship not found\n")
                tests_failed += 1
            
            # Test 13: ACCESSES relationship
            print("Test 13: Managed Identity accesses Storage...")
            result = session.run("""
                MATCH (mi:ManagedIdentity {demo: true})
                      -[r:ACCESSES]->
                      (storage:Resource:StorageAccount {demo: true})
                RETURN r.permission as permission
            """)
            record = result.single()
            if record and 'Storage Blob Data Contributor' in record['permission']:
                print(f"   ✅ PASS - ACCESSES relationship exists\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - ACCESSES relationship not found\n")
                tests_failed += 1
            
            # Test 14: HAS_ROLE relationship
            print("Test 14: Service Principal has role on AKS...")
            result = session.run("""
                MATCH (sp:ServicePrincipal {demo: true})
                      -[r:HAS_ROLE]->
                      (aks:Resource:AKS {demo: true})
                RETURN r.role as role
            """)
            record = result.single()
            if record and 'Admin' in record['role']:
                print(f"   ✅ PASS - HAS_ROLE relationship exists\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - HAS_ROLE relationship not found\n")
                tests_failed += 1
            
            # Test 15: Network topology path
            print("Test 15: Complete network topology path...")
            result = session.run("""
                MATCH path = (appgw:Resource:ApplicationGateway {demo: true})
                      -[:ROUTES_TO]->
                      (aks:Resource:AKS {demo: true})
                      -[:CONTAINS]->
                      (ns:Namespace {demo: true})
                      -[:CONTAINS]->
                      (pod:Pod {demo: true})
                RETURN count(path) as count
            """)
            record = result.single()
            if record['count'] > 0:
                print(f"   ✅ PASS - Found {record['count']} complete paths from App Gateway to Pods\n")
                tests_passed += 1
            else:
                print("   ❌ FAIL - No complete topology paths found\n")
                tests_failed += 1
            
            # Test 16: Identity access chain
            print("Test 16: Identity access chain...")
            result = session.run("""
                MATCH path = (aks:Resource:AKS {demo: true})
                      -[:AUTHENTICATES_WITH]->
                      (mi:ManagedIdentity {demo: true})
                      -[:ACCESSES]->
                      (storage:Resource:StorageAccount {demo: true})
                RETURN count(path) as count
            """)
            record = result.single()
            if record['count'] == 1:
                print(f"   ✅ PASS - Identity access chain exists\n")
                tests_passed += 1
            else:
                print(f"   ❌ FAIL - Identity access chain not found\n")
                tests_failed += 1
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        driver.close()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    total_tests = tests_passed + tests_failed
    print(f"\nTotal Tests:  {total_tests}")
    print(f"Passed:       {tests_passed} ✅")
    print(f"Failed:       {tests_failed} ❌")
    print(f"Success Rate: {(tests_passed / total_tests * 100):.1f}%")
    print("=" * 80 + "\n")
    
    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
