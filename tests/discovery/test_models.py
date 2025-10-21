"""
Tests for discovery data models.
"""

from topdeck.discovery.models import (
    Application,
    AppRegistration,
    CloudProvider,
    Deployment,
    DiscoveredResource,
    DiscoveryResult,
    ManagedIdentity,
    Namespace,
    Pod,
    Repository,
    ServicePrincipal,
)


class TestDiscoveredResource:
    """Tests for DiscoveredResource model"""

    def test_create_resource(self):
        """Test creating a discovered resource"""
        resource = DiscoveredResource(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            name="vm1",
            resource_type="virtual_machine",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            resource_group="rg",
            subscription_id="123",
        )

        assert (
            resource.id
            == "/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1"
        )
        assert resource.name == "vm1"
        assert resource.resource_type == "virtual_machine"
        assert resource.cloud_provider == CloudProvider.AZURE
        assert resource.region == "eastus"

    def test_to_neo4j_properties(self):
        """Test converting resource to Neo4j properties"""
        import json

        resource = DiscoveredResource(
            id="test-id",
            name="test-resource",
            resource_type="test_type",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            tags={"env": "prod"},
        )

        props = resource.to_neo4j_properties()

        assert props["id"] == "test-id"
        assert props["name"] == "test-resource"
        assert props["resource_type"] == "test_type"
        assert props["cloud_provider"] == "azure"
        assert props["region"] == "eastus"
        # Tags should be serialized as JSON string
        assert isinstance(props["tags"], str)
        assert json.loads(props["tags"]) == {"env": "prod"}
        assert "discovered_at" in props
        assert "last_seen" in props


class TestApplication:
    """Tests for Application model"""

    def test_create_application(self):
        """Test creating an application"""
        app = Application(
            id="app-myapp-prod",
            name="myapp",
            environment="prod",
            owner_team="platform-team",
        )

        assert app.id == "app-myapp-prod"
        assert app.name == "myapp"
        assert app.environment == "prod"
        assert app.owner_team == "platform-team"

    def test_to_neo4j_properties(self):
        """Test converting application to Neo4j properties"""
        app = Application(
            id="app-test",
            name="test-app",
            environment="dev",
            deployment_method="aks",
            current_version="v1.0.0",
        )

        props = app.to_neo4j_properties()

        assert props["id"] == "app-test"
        assert props["name"] == "test-app"
        assert props["environment"] == "dev"
        assert props["deployment_method"] == "aks"
        assert props["current_version"] == "v1.0.0"
        assert "discovered_at" in props


class TestRepository:
    """Tests for Repository model"""

    def test_create_repository(self):
        """Test creating a repository"""
        repo = Repository(
            id="repo-123",
            platform="azure_devops",
            url="https://dev.azure.com/org/project/_git/repo",
            name="repo",
        )

        assert repo.id == "repo-123"
        assert repo.platform == "azure_devops"
        assert repo.url == "https://dev.azure.com/org/project/_git/repo"
        assert repo.name == "repo"

    def test_to_neo4j_properties(self):
        """Test converting repository to Neo4j properties"""
        repo = Repository(
            id="repo-test",
            platform="github",
            url="https://github.com/org/repo",
            name="repo",
            default_branch="main",
            language="python",
        )

        props = repo.to_neo4j_properties()

        assert props["id"] == "repo-test"
        assert props["platform"] == "github"
        assert props["url"] == "https://github.com/org/repo"
        assert props["name"] == "repo"
        assert props["default_branch"] == "main"
        assert props["language"] == "python"


class TestDeployment:
    """Tests for Deployment model"""

    def test_create_deployment(self):
        """Test creating a deployment"""
        deployment = Deployment(
            id="deploy-123",
            pipeline_id="pipeline-456",
            version="v1.0.0",
            status="success",
            environment="prod",
        )

        assert deployment.id == "deploy-123"
        assert deployment.pipeline_id == "pipeline-456"
        assert deployment.version == "v1.0.0"
        assert deployment.status == "success"
        assert deployment.environment == "prod"

    def test_to_neo4j_properties(self):
        """Test converting deployment to Neo4j properties"""
        deployment = Deployment(
            id="deploy-test",
            pipeline_id="pipeline-123",
            version="v2.0.0",
            status="success",
            environment="staging",
            commit_sha="abc123",
            deployed_by="user@example.com",
        )

        props = deployment.to_neo4j_properties()

        assert props["id"] == "deploy-test"
        assert props["pipeline_id"] == "pipeline-123"
        assert props["version"] == "v2.0.0"
        assert props["status"] == "success"
        assert props["environment"] == "staging"
        assert props["commit_sha"] == "abc123"
        assert props["deployed_by"] == "user@example.com"


class TestDiscoveryResult:
    """Tests for DiscoveryResult model"""

    def test_create_empty_result(self):
        """Test creating an empty discovery result"""
        result = DiscoveryResult()

        assert result.resource_count == 0
        assert result.dependency_count == 0
        assert result.application_count == 0
        assert result.repository_count == 0
        assert result.deployment_count == 0
        assert not result.has_errors

    def test_add_resources(self):
        """Test adding resources to discovery result"""
        result = DiscoveryResult()

        resource = DiscoveredResource(
            id="test-id",
            name="test",
            resource_type="test_type",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
        )

        result.add_resource(resource)

        assert result.resource_count == 1
        assert result.resources[0].id == "test-id"

    def test_add_applications(self):
        """Test adding applications to discovery result"""
        result = DiscoveryResult()

        app = Application(id="app-1", name="test-app")
        result.add_application(app)

        assert result.application_count == 1
        assert result.applications[0].name == "test-app"

    def test_add_repositories(self):
        """Test adding repositories to discovery result"""
        result = DiscoveryResult()

        repo = Repository(
            id="repo-1",
            platform="github",
            url="https://github.com/test/repo",
            name="repo",
        )
        result.add_repository(repo)

        assert result.repository_count == 1
        assert result.repositories[0].name == "repo"

    def test_add_deployments(self):
        """Test adding deployments to discovery result"""
        result = DiscoveryResult()

        deployment = Deployment(id="deploy-1", status="success")
        result.add_deployment(deployment)

        assert result.deployment_count == 1
        assert result.deployments[0].status == "success"

    def test_summary(self):
        """Test discovery result summary"""
        result = DiscoveryResult()

        result.add_resource(
            DiscoveredResource(
                id="r1",
                name="r1",
                resource_type="test",
                cloud_provider=CloudProvider.AZURE,
                region="eastus",
            )
        )
        result.add_application(Application(id="a1", name="a1"))
        result.add_error("Test error")
        result.complete()

        summary = result.summary()

        assert "1 resources" in summary
        assert "1 applications" in summary
        assert "1 errors" in summary
        assert "duration:" in summary


class TestNamespace:
    """Tests for Namespace model"""

    def test_create_namespace(self):
        """Test creating a namespace"""
        namespace = Namespace(
            id="cluster-123:production",
            name="production",
            cluster_id="cluster-123",
            labels={"env": "prod"},
        )

        assert namespace.id == "cluster-123:production"
        assert namespace.name == "production"
        assert namespace.cluster_id == "cluster-123"
        assert namespace.labels == {"env": "prod"}

    def test_to_neo4j_properties(self):
        """Test converting namespace to Neo4j properties"""
        import json

        namespace = Namespace(
            id="cluster-1:default",
            name="default",
            cluster_id="cluster-1",
            labels={"name": "default"},
            annotations={"test": "value"},
        )

        props = namespace.to_neo4j_properties()

        assert props["id"] == "cluster-1:default"
        assert props["name"] == "default"
        assert props["cluster_id"] == "cluster-1"
        # Labels and annotations should be JSON strings
        assert isinstance(props["labels"], str)
        assert json.loads(props["labels"]) == {"name": "default"}
        assert isinstance(props["annotations"], str)
        assert json.loads(props["annotations"]) == {"test": "value"}
        assert "discovered_at" in props


class TestPod:
    """Tests for Pod model"""

    def test_create_pod(self):
        """Test creating a pod"""
        pod = Pod(
            id="pod-123",
            name="my-app-pod",
            namespace="production",
            cluster_id="cluster-123",
            phase="Running",
        )

        assert pod.id == "pod-123"
        assert pod.name == "my-app-pod"
        assert pod.namespace == "production"
        assert pod.cluster_id == "cluster-123"
        assert pod.phase == "Running"

    def test_to_neo4j_properties(self):
        """Test converting pod to Neo4j properties"""
        import json

        pod = Pod(
            id="pod-1",
            name="nginx-pod",
            namespace="default",
            cluster_id="cluster-1",
            phase="Running",
            pod_ip="10.0.0.1",
            node_name="node-1",
            labels={"app": "nginx"},
        )

        props = pod.to_neo4j_properties()

        assert props["id"] == "pod-1"
        assert props["name"] == "nginx-pod"
        assert props["namespace"] == "default"
        assert props["cluster_id"] == "cluster-1"
        assert props["phase"] == "Running"
        assert props["pod_ip"] == "10.0.0.1"
        assert props["node_name"] == "node-1"
        # Labels should be JSON string
        assert isinstance(props["labels"], str)
        assert json.loads(props["labels"]) == {"app": "nginx"}


class TestManagedIdentity:
    """Tests for ManagedIdentity model"""

    def test_create_managed_identity(self):
        """Test creating a managed identity"""
        identity = ManagedIdentity(
            id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/my-identity",
            name="my-identity",
            identity_type="UserAssigned",
            principal_id="principal-123",
            client_id="client-456",
        )

        assert identity.name == "my-identity"
        assert identity.identity_type == "UserAssigned"
        assert identity.principal_id == "principal-123"
        assert identity.client_id == "client-456"

    def test_to_neo4j_properties(self):
        """Test converting managed identity to Neo4j properties"""
        identity = ManagedIdentity(
            id="identity-1",
            name="app-identity",
            identity_type="SystemAssigned",
            principal_id="principal-123",
            assigned_to_resource_id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Web/sites/myapp",
            assigned_to_resource_type="app_service",
        )

        props = identity.to_neo4j_properties()

        assert props["id"] == "identity-1"
        assert props["name"] == "app-identity"
        assert props["identity_type"] == "SystemAssigned"
        assert props["principal_id"] == "principal-123"
        assert props["assigned_to_resource_type"] == "app_service"


class TestServicePrincipal:
    """Tests for ServicePrincipal model"""

    def test_create_service_principal(self):
        """Test creating a service principal"""
        sp = ServicePrincipal(
            id="sp-object-id-123",
            app_id="app-id-456",
            display_name="MyApp Service Principal",
            service_principal_type="Application",
        )

        assert sp.id == "sp-object-id-123"
        assert sp.app_id == "app-id-456"
        assert sp.display_name == "MyApp Service Principal"
        assert sp.service_principal_type == "Application"

    def test_to_neo4j_properties(self):
        """Test converting service principal to Neo4j properties"""
        sp = ServicePrincipal(
            id="sp-1",
            app_id="app-1",
            display_name="Automation Service Principal",
            enabled=True,
            password_credentials_count=2,
            key_credentials_count=1,
        )

        props = sp.to_neo4j_properties()

        assert props["id"] == "sp-1"
        assert props["app_id"] == "app-1"
        assert props["display_name"] == "Automation Service Principal"
        assert props["enabled"] is True
        assert props["password_credentials_count"] == 2
        assert props["key_credentials_count"] == 1


class TestAppRegistration:
    """Tests for AppRegistration model"""

    def test_create_app_registration(self):
        """Test creating an app registration"""
        app_reg = AppRegistration(
            id="app-object-id-123",
            app_id="app-id-456",
            display_name="My Application",
            sign_in_audience="AzureADMyOrg",
        )

        assert app_reg.id == "app-object-id-123"
        assert app_reg.app_id == "app-id-456"
        assert app_reg.display_name == "My Application"
        assert app_reg.sign_in_audience == "AzureADMyOrg"

    def test_to_neo4j_properties(self):
        """Test converting app registration to Neo4j properties"""
        import json

        app_reg = AppRegistration(
            id="app-1",
            app_id="app-client-id-1",
            display_name="Web Application",
            identifier_uris=["api://myapp"],
            redirect_uris=["https://myapp.com/auth"],
            password_credentials_count=1,
        )

        props = app_reg.to_neo4j_properties()

        assert props["id"] == "app-1"
        assert props["app_id"] == "app-client-id-1"
        assert props["display_name"] == "Web Application"
        # URIs should be JSON strings
        assert isinstance(props["identifier_uris"], str)
        assert json.loads(props["identifier_uris"]) == ["api://myapp"]
        assert isinstance(props["redirect_uris"], str)
        assert json.loads(props["redirect_uris"]) == ["https://myapp.com/auth"]
        assert props["password_credentials_count"] == 1


class TestDiscoveryResultExtended:
    """Additional tests for DiscoveryResult with new node types"""

    def test_add_namespaces(self):
        """Test adding namespaces to discovery result"""
        result = DiscoveryResult()

        namespace = Namespace(
            id="cluster-1:default",
            name="default",
            cluster_id="cluster-1",
        )
        result.add_namespace(namespace)

        assert result.namespace_count == 1
        assert result.namespaces[0].name == "default"

    def test_add_pods(self):
        """Test adding pods to discovery result"""
        result = DiscoveryResult()

        pod = Pod(
            id="pod-1",
            name="my-pod",
            namespace="default",
            cluster_id="cluster-1",
        )
        result.add_pod(pod)

        assert result.pod_count == 1
        assert result.pods[0].name == "my-pod"

    def test_add_managed_identities(self):
        """Test adding managed identities to discovery result"""
        result = DiscoveryResult()

        identity = ManagedIdentity(
            id="identity-1",
            name="my-identity",
            identity_type="UserAssigned",
        )
        result.add_managed_identity(identity)

        assert result.managed_identity_count == 1
        assert result.managed_identities[0].name == "my-identity"

    def test_add_service_principals(self):
        """Test adding service principals to discovery result"""
        result = DiscoveryResult()

        sp = ServicePrincipal(
            id="sp-1",
            app_id="app-1",
            display_name="My SP",
        )
        result.add_service_principal(sp)

        assert result.service_principal_count == 1
        assert result.service_principals[0].display_name == "My SP"

    def test_add_app_registrations(self):
        """Test adding app registrations to discovery result"""
        result = DiscoveryResult()

        app_reg = AppRegistration(
            id="app-1",
            app_id="app-client-1",
            display_name="My App",
        )
        result.add_app_registration(app_reg)

        assert result.app_registration_count == 1
        assert result.app_registrations[0].display_name == "My App"

    def test_summary_with_new_types(self):
        """Test discovery result summary with new types"""
        result = DiscoveryResult()

        result.add_resource(
            DiscoveredResource(
                id="r1",
                name="r1",
                resource_type="test",
                cloud_provider=CloudProvider.AZURE,
                region="eastus",
            )
        )
        result.add_namespace(Namespace(id="ns-1", name="default", cluster_id="c1"))
        result.add_pod(Pod(id="p1", name="pod1", namespace="default", cluster_id="c1"))
        result.add_managed_identity(
            ManagedIdentity(id="mi1", name="identity1", identity_type="UserAssigned")
        )
        result.complete()

        summary = result.summary()

        assert "1 resources" in summary
        assert "1 namespaces" in summary
        assert "1 pods" in summary
        assert "1 managed identities" in summary
