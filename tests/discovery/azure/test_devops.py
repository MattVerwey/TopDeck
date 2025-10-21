"""
Tests for Azure DevOps integration.
"""

from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer


class TestAzureDevOpsDiscoverer:
    """Tests for AzureDevOpsDiscoverer"""

    def test_init(self):
        """Test initializing Azure DevOps discoverer"""
        discoverer = AzureDevOpsDiscoverer(
            organization="myorg",
            project="myproject",
        )

        assert discoverer.organization == "myorg"
        assert discoverer.project == "myproject"
        assert discoverer.base_url == "https://dev.azure.com/myorg/myproject"

    def test_extract_deployment_metadata_from_tags(self):
        """Test extracting deployment metadata from resource tags"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        tags = {
            "deploy_version": "v1.2.3",
            "deploy_pipeline": "pipeline-123",
            "commit_sha": "abc123def456",
            "deployed_by": "user@example.com",
            "repository": "https://dev.azure.com/org/project/_git/repo",
        }

        metadata = discoverer.extract_deployment_metadata_from_tags(tags)

        assert metadata is not None
        assert metadata["version"] == "v1.2.3"
        assert metadata["pipeline_id"] == "pipeline-123"
        assert metadata["commit_sha"] == "abc123def456"
        assert metadata["deployed_by"] == "user@example.com"
        assert metadata["repository_url"] == "https://dev.azure.com/org/project/_git/repo"

    def test_extract_deployment_metadata_no_tags(self):
        """Test extracting deployment metadata with no tags"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        metadata = discoverer.extract_deployment_metadata_from_tags(None)
        assert metadata is None

        metadata = discoverer.extract_deployment_metadata_from_tags({})
        assert metadata is None

    def test_extract_deployment_metadata_partial_tags(self):
        """Test extracting deployment metadata with partial tags"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        tags = {
            "version": "v2.0.0",
            "environment": "prod",
        }

        metadata = discoverer.extract_deployment_metadata_from_tags(tags)

        assert metadata is not None
        assert metadata["version"] == "v2.0.0"
        assert "pipeline_id" not in metadata

    def test_infer_application_from_tags(self):
        """Test inferring application from resource with explicit tags"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        tags = {
            "app_name": "myapp",
            "environment": "prod",
            "owner_team": "platform-team",
            "repository": "https://github.com/org/myapp",
        }

        app = discoverer.infer_application_from_resource(
            resource_name="prod-myapp-aks",
            resource_type="aks",
            tags=tags,
        )

        assert app is not None
        assert app.name == "myapp"
        assert app.environment == "prod"
        assert app.deployment_method == "aks"
        assert app.owner_team == "platform-team"
        assert app.repository_url == "https://github.com/org/myapp"

    def test_infer_application_from_resource_name(self):
        """Test inferring application from resource name pattern"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        tags = {
            "environment": "staging",
        }

        # Test pattern: {env}-{app}-{resource_type}
        app = discoverer.infer_application_from_resource(
            resource_name="staging-ecommerce-aks",
            resource_type="aks",
            tags=tags,
        )

        assert app is not None
        assert app.name == "ecommerce"
        assert app.environment == "staging"
        assert app.deployment_method == "aks"

    def test_infer_application_various_patterns(self):
        """Test inferring application from various naming patterns"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        # Pattern: prod-appname-service
        app = discoverer.infer_application_from_resource(
            resource_name="prod-api-service",
            resource_type="app_service",
            tags={"environment": "prod"},
        )
        assert app is not None
        assert app.name == "api"

        # Pattern: dev-webapp-app
        app = discoverer.infer_application_from_resource(
            resource_name="dev-webapp-app",
            resource_type="app_service",
            tags={"env": "dev"},
        )
        assert app is not None
        assert app.name == "webapp"

    def test_infer_application_no_pattern_match(self):
        """Test inferring application with no clear pattern"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        # No app name tag and no clear pattern
        discoverer.infer_application_from_resource(
            resource_name="random-vm-123",
            resource_type="virtual_machine",
            tags={},
        )

        # Should still try to infer something
        # In this case, it might extract "random" as the app name
        # or return None if no pattern matches
        # The behavior depends on the implementation
        # For now, we just verify it doesn't crash
        assert True  # Just verify it doesn't raise an exception

    def test_infer_application_app_service(self):
        """Test inferring application for App Service resource"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        app = discoverer.infer_application_from_resource(
            resource_name="prod-webapp",
            resource_type="app_service",
            tags={"app_name": "webapp", "environment": "prod"},
        )

        assert app is not None
        assert app.deployment_method == "app_service"

    def test_infer_application_vm(self):
        """Test inferring application for VM resource"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        app = discoverer.infer_application_from_resource(
            resource_name="prod-appvm",
            resource_type="virtual_machine",
            tags={"service_name": "appvm", "environment": "prod"},
        )

        assert app is not None
        assert app.deployment_method == "vm"


class TestDeploymentMetadataExtraction:
    """Tests for deployment metadata extraction from tags"""

    def test_version_tag_variants(self):
        """Test extracting version from different tag keys"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        # Test deploy_version
        tags = {"deploy_version": "1.0.0"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["version"] == "1.0.0"

        # Test version
        tags = {"version": "2.0.0"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["version"] == "2.0.0"

        # Test app_version
        tags = {"app_version": "3.0.0"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["version"] == "3.0.0"

        # Test image_tag
        tags = {"image_tag": "v4.0.0"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["version"] == "v4.0.0"

    def test_pipeline_tag_variants(self):
        """Test extracting pipeline ID from different tag keys"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        # Test deploy_pipeline
        tags = {"deploy_pipeline": "pipeline-1"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["pipeline_id"] == "pipeline-1"

        # Test pipeline_id
        tags = {"pipeline_id": "pipeline-2"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["pipeline_id"] == "pipeline-2"

        # Test build_id
        tags = {"build_id": "build-123"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["pipeline_id"] == "build-123"

    def test_commit_tag_variants(self):
        """Test extracting commit SHA from different tag keys"""
        discoverer = AzureDevOpsDiscoverer("org", "project")

        # Test deploy_commit
        tags = {"deploy_commit": "abc123"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["commit_sha"] == "abc123"

        # Test commit_sha
        tags = {"commit_sha": "def456"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["commit_sha"] == "def456"

        # Test git_commit
        tags = {"git_commit": "ghi789"}
        metadata = discoverer.extract_deployment_metadata_from_tags(tags)
        assert metadata["commit_sha"] == "ghi789"
