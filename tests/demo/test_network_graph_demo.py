"""Tests for network graph demo."""

import pytest
from neo4j import GraphDatabase


@pytest.fixture(scope="module")
def neo4j_connection():
    """Create Neo4j connection for tests."""
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "topdeck123"

    driver = GraphDatabase.driver(uri, auth=(username, password))
    yield driver
    driver.close()


def test_demo_resources_created(neo4j_connection):
    """Test that demo resources were created."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (n) WHERE n.demo = true
            RETURN count(n) as count
        """
        )

        record = result.single()
        assert record["count"] > 0, "Demo resources should be created"


def test_aks_cluster_exists(neo4j_connection):
    """Test that AKS cluster exists."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (aks:Resource:AKS {demo: true})
            RETURN aks.name as name, aks.resource_type as type
        """
        )

        record = result.single()
        assert record is not None, "AKS cluster should exist"
        assert record["name"] == "aks-demo-prod"
        assert record["type"] == "aks"


def test_namespaces_exist(neo4j_connection):
    """Test that Kubernetes namespaces exist."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (ns:Namespace {demo: true})
            RETURN count(ns) as count
        """
        )

        record = result.single()
        assert record["count"] == 3, "Should have 3 namespaces (frontend, backend, data)"


def test_pods_exist(neo4j_connection):
    """Test that pods exist."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (pod:Pod {demo: true})
            RETURN count(pod) as count
        """
        )

        record = result.single()
        assert record["count"] == 3, "Should have 3 pods"


def test_application_gateway_exists(neo4j_connection):
    """Test that Application Gateway exists."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (appgw:Resource:ApplicationGateway {demo: true})
            RETURN appgw.name as name
        """
        )

        record = result.single()
        assert record is not None, "Application Gateway should exist"
        assert record["name"] == "appgw-demo"


def test_storage_account_exists(neo4j_connection):
    """Test that Storage Account exists."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (storage:Resource:StorageAccount {demo: true})
            RETURN storage.name as name
        """
        )

        record = result.single()
        assert record is not None, "Storage Account should exist"
        assert record["name"] == "stdemoprod001"


def test_vmss_exists(neo4j_connection):
    """Test that VM Scale Set exists."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (vmss:Resource:VMSS {demo: true})
            RETURN vmss.name as name
        """
        )

        record = result.single()
        assert record is not None, "VM Scale Set should exist"
        assert record["name"] == "vmss-workers"


def test_managed_identity_exists(neo4j_connection):
    """Test that Managed Identity exists."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (mi:ManagedIdentity {demo: true})
            RETURN mi.name as name, mi.identity_type as type
        """
        )

        record = result.single()
        assert record is not None, "Managed Identity should exist"
        assert record["name"] == "id-aks-demo"
        assert record["type"] == "SystemAssigned"


def test_service_principal_exists(neo4j_connection):
    """Test that Service Principal exists."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (sp:ServicePrincipal {demo: true})
            RETURN sp.display_name as name
        """
        )

        record = result.single()
        assert record is not None, "Service Principal should exist"
        assert record["name"] == "sp-demo-deployment"


def test_applications_exist(neo4j_connection):
    """Test that applications exist."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (app:Application {demo: true})
            RETURN count(app) as count
        """
        )

        record = result.single()
        assert record["count"] == 2, "Should have 2 applications"


def test_routes_to_relationship(neo4j_connection):
    """Test Application Gateway routes to AKS."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (appgw:Resource:ApplicationGateway {demo: true})
                  -[r:ROUTES_TO]->
                  (aks:Resource:AKS {demo: true})
            RETURN r.protocol as protocol, r.port as port
        """
        )

        record = result.single()
        assert record is not None, "ROUTES_TO relationship should exist"
        assert record["protocol"] == "https"
        assert record["port"] == 443


def test_authenticates_with_relationship(neo4j_connection):
    """Test AKS authenticates with Managed Identity."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (aks:Resource:AKS {demo: true})
                  -[r:AUTHENTICATES_WITH]->
                  (mi:ManagedIdentity {demo: true})
            RETURN r.identity_type as type
        """
        )

        record = result.single()
        assert record is not None, "AUTHENTICATES_WITH relationship should exist"
        assert record["type"] == "SystemAssigned"


def test_accesses_relationship(neo4j_connection):
    """Test Managed Identity accesses Storage Account."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (mi:ManagedIdentity {demo: true})
                  -[r:ACCESSES]->
                  (storage:Resource:StorageAccount {demo: true})
            RETURN r.permission as permission
        """
        )

        record = result.single()
        assert record is not None, "ACCESSES relationship should exist"
        assert "Storage Blob Data Contributor" in record["permission"]


def test_has_role_relationship(neo4j_connection):
    """Test Service Principal has role on AKS."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (sp:ServicePrincipal {demo: true})
                  -[r:HAS_ROLE]->
                  (aks:Resource:AKS {demo: true})
            RETURN r.role as role
        """
        )

        record = result.single()
        assert record is not None, "HAS_ROLE relationship should exist"
        assert "Admin" in record["role"]


def test_depends_on_relationship(neo4j_connection):
    """Test pods have DEPENDS_ON relationships."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (pod:Pod {demo: true})
                  -[r:DEPENDS_ON]->
                  (target)
            WHERE target.demo = true
            RETURN count(r) as count
        """
        )

        record = result.single()
        assert record["count"] >= 2, "Should have at least 2 DEPENDS_ON relationships"


def test_contains_relationship(neo4j_connection):
    """Test AKS contains namespaces and namespaces contain pods."""
    with neo4j_connection.session() as session:
        # Test AKS contains namespaces
        result = session.run(
            """
            MATCH (aks:Resource:AKS {demo: true})
                  -[:CONTAINS]->
                  (ns:Namespace {demo: true})
            RETURN count(ns) as count
        """
        )

        record = result.single()
        assert record["count"] == 3, "AKS should contain 3 namespaces"

        # Test namespaces contain pods
        result = session.run(
            """
            MATCH (ns:Namespace {demo: true})
                  -[:CONTAINS]->
                  (pod:Pod {demo: true})
            RETURN count(pod) as count
        """
        )

        record = result.single()
        assert record["count"] == 3, "Namespaces should contain 3 pods total"


def test_deployed_to_relationship(neo4j_connection):
    """Test applications are deployed to namespaces."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (app:Application {demo: true})
                  -[:DEPLOYED_TO]->
                  (ns:Namespace {demo: true})
            RETURN count(app) as count
        """
        )

        record = result.single()
        assert record["count"] == 2, "Should have 2 applications deployed to namespaces"


def test_uses_relationship(neo4j_connection):
    """Test AKS uses VM Scale Set."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (aks:Resource:AKS {demo: true})
                  -[r:USES]->
                  (vmss:Resource:VMSS {demo: true})
            RETURN r.purpose as purpose
        """
        )

        record = result.single()
        assert record is not None, "USES relationship should exist"
        assert record["purpose"] == "compute"


def test_network_topology_path(neo4j_connection):
    """Test complete network topology path exists."""
    with neo4j_connection.session() as session:
        # Test: Application Gateway -> AKS -> Namespace -> Pod
        result = session.run(
            """
            MATCH path = (appgw:Resource:ApplicationGateway {demo: true})
                  -[:ROUTES_TO]->
                  (aks:Resource:AKS {demo: true})
                  -[:CONTAINS]->
                  (ns:Namespace {demo: true})
                  -[:CONTAINS]->
                  (pod:Pod {demo: true})
            RETURN count(path) as count
        """
        )

        record = result.single()
        assert record["count"] > 0, "Complete path from App Gateway to Pods should exist"


def test_identity_access_chain(neo4j_connection):
    """Test identity access chain exists."""
    with neo4j_connection.session() as session:
        # Test: AKS -> Managed Identity -> Storage
        result = session.run(
            """
            MATCH path = (aks:Resource:AKS {demo: true})
                  -[:AUTHENTICATES_WITH]->
                  (mi:ManagedIdentity {demo: true})
                  -[:ACCESSES]->
                  (storage:Resource:StorageAccount {demo: true})
            RETURN count(path) as count
        """
        )

        record = result.single()
        assert record["count"] == 1, "Identity access chain should exist"


def test_resource_properties(neo4j_connection):
    """Test that resources have proper properties."""
    with neo4j_connection.session() as session:
        result = session.run(
            """
            MATCH (r:Resource {demo: true})
            WHERE r.cloud_provider IS NOT NULL
              AND r.resource_type IS NOT NULL
              AND r.region IS NOT NULL
              AND r.status IS NOT NULL
            RETURN count(r) as count
        """
        )

        record = result.single()
        assert record["count"] == 4, "All resources should have required properties"
