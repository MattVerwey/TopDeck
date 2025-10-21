"""
Tests for Neo4j serialization of complex data structures.

These tests ensure that complex nested objects in tags and properties
are properly serialized to JSON strings for Neo4j compatibility.
"""

import json

from topdeck.discovery.models import (
    AppRegistration,
    CloudProvider,
    Deployment,
    DiscoveredResource,
    ManagedIdentity,
    Namespace,
    Pod,
    Repository,
    ServicePrincipal,
)


class TestDiscoveredResourceSerialization:
    """Test serialization of DiscoveredResource with complex data"""

    def test_simple_tags_and_properties(self):
        """Test that simple tags and properties are serialized correctly"""
        resource = DiscoveredResource(
            id="test-id",
            name="test-resource",
            resource_type="test_type",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            tags={"env": "prod", "owner": "team-a"},
            properties={"size": "large", "tier": "premium"},
        )

        props = resource.to_neo4j_properties()

        # Tags and properties should be JSON strings
        assert isinstance(props["tags"], str)
        assert isinstance(props["properties"], str)

        # Verify they can be deserialized back
        tags = json.loads(props["tags"])
        assert tags == {"env": "prod", "owner": "team-a"}

        properties = json.loads(props["properties"])
        assert properties == {"size": "large", "tier": "premium"}

    def test_complex_nested_tags(self):
        """Test that complex nested tags are properly serialized"""
        resource = DiscoveredResource(
            id="test-id",
            name="test-resource",
            resource_type="test_type",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            tags={
                "Product Name": "Azure Kubernetes Service",
                "Value Stream": "Shared",
                "runningPattern": "officeHours",
                "dates": {
                    "creationDate": "2025-09-10T09:05:19Z",
                    "reviewDate": "2025-10-10T09:05:19Z",
                },
                "owners": {
                    "businessOwner": "user@company.com",
                    "technicalOwner": "dev@company.com",
                },
            },
        )

        props = resource.to_neo4j_properties()

        # Tags should be a JSON string
        assert isinstance(props["tags"], str)

        # Verify complex structure is preserved
        tags = json.loads(props["tags"])
        assert tags["Product Name"] == "Azure Kubernetes Service"
        assert tags["Value Stream"] == "Shared"
        assert isinstance(tags["dates"], dict)
        assert tags["dates"]["creationDate"] == "2025-09-10T09:05:19Z"
        assert isinstance(tags["owners"], dict)
        assert tags["owners"]["businessOwner"] == "user@company.com"

    def test_complex_nested_properties(self):
        """Test that complex nested properties are properly serialized"""
        resource = DiscoveredResource(
            id="test-id",
            name="test-resource",
            resource_type="aks",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            properties={
                "kubernetesVersion": "1.27.3",
                "networkProfile": {
                    "networkPlugin": "azure",
                    "serviceCidr": "10.0.0.0/16",
                    "dnsServiceIP": "10.0.0.10",
                    "loadBalancerSku": "standard",
                },
                "agentPoolProfiles": [
                    {
                        "name": "nodepool1",
                        "count": 3,
                        "vmSize": "Standard_DS2_v2",
                        "osType": "Linux",
                    },
                    {
                        "name": "nodepool2",
                        "count": 2,
                        "vmSize": "Standard_DS3_v2",
                        "osType": "Linux",
                    },
                ],
            },
        )

        props = resource.to_neo4j_properties()

        # Properties should be a JSON string
        assert isinstance(props["properties"], str)

        # Verify complex structure is preserved
        properties = json.loads(props["properties"])
        assert properties["kubernetesVersion"] == "1.27.3"
        assert isinstance(properties["networkProfile"], dict)
        assert properties["networkProfile"]["networkPlugin"] == "azure"
        assert isinstance(properties["agentPoolProfiles"], list)
        assert len(properties["agentPoolProfiles"]) == 2
        assert properties["agentPoolProfiles"][0]["name"] == "nodepool1"

    def test_empty_tags_and_properties(self):
        """Test that empty tags and properties are handled correctly"""
        resource = DiscoveredResource(
            id="test-id",
            name="test-resource",
            resource_type="test_type",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        props = resource.to_neo4j_properties()

        # Empty dicts should be serialized to empty JSON objects
        assert props["tags"] == "{}"
        assert props["properties"] == "{}"


class TestNamespaceSerialization:
    """Test serialization of Namespace with dict properties"""

    def test_namespace_with_labels_and_annotations(self):
        """Test that namespace labels and annotations are serialized"""
        namespace = Namespace(
            id="cluster-1:production",
            name="production",
            cluster_id="cluster-1",
            labels={"env": "prod", "tier": "critical"},
            annotations={"managed-by": "kubernetes", "version": "1.0"},
        )

        props = namespace.to_neo4j_properties()

        # Labels and annotations should be JSON strings
        assert isinstance(props["labels"], str)
        assert isinstance(props["annotations"], str)

        # Verify they can be deserialized
        labels = json.loads(props["labels"])
        assert labels == {"env": "prod", "tier": "critical"}

        annotations = json.loads(props["annotations"])
        assert annotations == {"managed-by": "kubernetes", "version": "1.0"}


class TestPodSerialization:
    """Test serialization of Pod with lists and dicts"""

    def test_pod_with_containers_and_volumes(self):
        """Test that pod containers and volumes are serialized"""
        pod = Pod(
            id="pod-1",
            name="nginx-pod",
            namespace="default",
            cluster_id="cluster-1",
            containers=[
                {
                    "name": "nginx",
                    "image": "nginx:1.21",
                    "ports": [{"containerPort": 80}],
                }
            ],
            volumes=[{"name": "config", "configMap": {"name": "nginx-config"}}],
            labels={"app": "nginx"},
            annotations={"prometheus.io/scrape": "true"},
        )

        props = pod.to_neo4j_properties()

        # Lists and dicts should be JSON strings
        assert isinstance(props["containers"], str)
        assert isinstance(props["volumes"], str)
        assert isinstance(props["labels"], str)
        assert isinstance(props["annotations"], str)

        # Verify deserialization
        containers = json.loads(props["containers"])
        assert len(containers) == 1
        assert containers[0]["name"] == "nginx"

        volumes = json.loads(props["volumes"])
        assert len(volumes) == 1
        assert volumes[0]["name"] == "config"


class TestManagedIdentitySerialization:
    """Test serialization of ManagedIdentity with tags"""

    def test_managed_identity_with_tags(self):
        """Test that managed identity tags are serialized"""
        identity = ManagedIdentity(
            id="identity-1",
            name="app-identity",
            identity_type="UserAssigned",
            tags={"env": "prod", "app": "myapp"},
        )

        props = identity.to_neo4j_properties()

        # Tags should be a JSON string
        assert isinstance(props["tags"], str)

        tags = json.loads(props["tags"])
        assert tags == {"env": "prod", "app": "myapp"}


class TestServicePrincipalSerialization:
    """Test serialization of ServicePrincipal with lists"""

    def test_service_principal_with_roles_and_permissions(self):
        """Test that service principal roles and permissions are serialized"""
        sp = ServicePrincipal(
            id="sp-1",
            app_id="app-1",
            display_name="MyApp SP",
            app_roles=[
                {"id": "role-1", "value": "Admin"},
                {"id": "role-2", "value": "Reader"},
            ],
            oauth2_permissions=[
                {"id": "perm-1", "value": "user.read"},
            ],
            tags=["production", "critical"],
        )

        props = sp.to_neo4j_properties()

        # Lists should be JSON strings
        assert isinstance(props["app_roles"], str)
        assert isinstance(props["oauth2_permissions"], str)
        assert isinstance(props["tags"], str)

        # Verify deserialization
        app_roles = json.loads(props["app_roles"])
        assert len(app_roles) == 2
        assert app_roles[0]["value"] == "Admin"

        oauth2_permissions = json.loads(props["oauth2_permissions"])
        assert len(oauth2_permissions) == 1
        assert oauth2_permissions[0]["value"] == "user.read"

        tags = json.loads(props["tags"])
        assert tags == ["production", "critical"]


class TestAppRegistrationSerialization:
    """Test serialization of AppRegistration with lists"""

    def test_app_registration_with_uris(self):
        """Test that app registration URIs are serialized"""
        app_reg = AppRegistration(
            id="app-1",
            app_id="app-client-id",
            display_name="MyApp",
            identifier_uris=["api://myapp", "https://myapp.com"],
            redirect_uris=["https://myapp.com/callback", "https://myapp.com/auth"],
            tags=["web", "api"],
        )

        props = app_reg.to_neo4j_properties()

        # Lists should be JSON strings
        assert isinstance(props["identifier_uris"], str)
        assert isinstance(props["redirect_uris"], str)
        assert isinstance(props["tags"], str)

        # Verify deserialization
        identifier_uris = json.loads(props["identifier_uris"])
        assert identifier_uris == ["api://myapp", "https://myapp.com"]

        redirect_uris = json.loads(props["redirect_uris"])
        assert len(redirect_uris) == 2


class TestRepositorySerialization:
    """Test serialization of Repository with list properties"""

    def test_repository_with_topics(self):
        """Test that repository topics are serialized"""
        repo = Repository(
            id="repo-1",
            platform="github",
            url="https://github.com/org/repo",
            name="repo",
            topics=["python", "kubernetes", "devops"],
        )

        props = repo.to_neo4j_properties()

        # Topics should be a JSON string
        assert isinstance(props["topics"], str)

        topics = json.loads(props["topics"])
        assert topics == ["python", "kubernetes", "devops"]


class TestDeploymentSerialization:
    """Test serialization of Deployment with list properties"""

    def test_deployment_with_target_resources(self):
        """Test that deployment target resources are serialized"""
        deployment = Deployment(
            id="deploy-1",
            status="success",
            target_resources=["/subscriptions/123/resource1", "/subscriptions/123/resource2"],
            approvers=["user1@company.com", "user2@company.com"],
        )

        props = deployment.to_neo4j_properties()

        # Lists should be JSON strings
        assert isinstance(props["target_resources"], str)
        assert isinstance(props["approvers"], str)

        # Verify deserialization
        target_resources = json.loads(props["target_resources"])
        assert len(target_resources) == 2

        approvers = json.loads(props["approvers"])
        assert len(approvers) == 2


class TestRealWorldScenario:
    """Test with real-world Azure resource data"""

    def test_aks_resource_with_complex_tags(self):
        """Test AKS resource with the exact complex tags from the issue"""
        resource = DiscoveredResource(
            id="/subscriptions/abc123/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/sisexternalaksdata000001",
            name="sisexternalaksdata000001",
            resource_type="aks",
            cloud_provider=CloudProvider.AZURE,
            region="uksouth",
            resource_group="rg",
            subscription_id="abc123",
            tags={
                "Product Name": "Azure Kubernetes Service",
                "Value Stream": "Shared",
            },
            properties={
                "kubernetesVersion": "1.27.3",
                "provisioningState": "Succeeded",
            },
        )

        props = resource.to_neo4j_properties()

        # Both tags and properties should be JSON strings
        assert isinstance(props["tags"], str)
        assert isinstance(props["properties"], str)

        # Verify no nested Maps in the output
        for key, value in props.items():
            if key in ("tags", "properties"):
                assert isinstance(value, str), f"{key} should be a string, got {type(value)}"
            else:
                # Other values should be primitives or None
                assert value is None or isinstance(
                    value, (str, int, float, bool)
                ), f"{key} should be primitive, got {type(value)}"

    def test_app_service_with_nested_owners(self):
        """Test App Service with deeply nested owner information"""
        resource = DiscoveredResource(
            id="/subscriptions/abc123/resourceGroups/rg/providers/Microsoft.Web/sites/editor-dev-uks-as",
            name="editor-dev-uks-as",
            resource_type="app_service",
            cloud_provider=CloudProvider.AZURE,
            region="uksouth",
            resource_group="rg",
            subscription_id="abc123",
            tags={
                "environment": "dev",
                "runningPattern": "officeHours",
                "dates": {
                    "creationDate": "2025-09-10T09:05:19Z",
                    "reviewDate": "2025-10-10T09:05:19Z",
                },
                "owners": {
                    "businessOwner": "user@company.com",
                    "technicalOwner": "dev@company.com",
                },
                "serviceDetails": {
                    "tier": "premium",
                    "sku": "P1v2",
                    "instances": 2,
                },
            },
        )

        props = resource.to_neo4j_properties()

        # Verify tags is a JSON string
        assert isinstance(props["tags"], str)

        # Verify the nested structure is preserved after deserialization
        tags = json.loads(props["tags"])
        assert tags["environment"] == "dev"
        assert isinstance(tags["dates"], dict)
        assert tags["dates"]["creationDate"] == "2025-09-10T09:05:19Z"
        assert isinstance(tags["owners"], dict)
        assert tags["owners"]["businessOwner"] == "user@company.com"
        assert isinstance(tags["serviceDetails"], dict)
        assert tags["serviceDetails"]["tier"] == "premium"
        assert tags["serviceDetails"]["instances"] == 2
