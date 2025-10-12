"""
Tests for discovery data models.
"""

import pytest
from datetime import datetime

from topdeck.discovery.models import (
    DiscoveredResource,
    ResourceDependency,
    Application,
    Repository,
    Deployment,
    DiscoveryResult,
    CloudProvider,
    ResourceStatus,
    DependencyCategory,
    DependencyType,
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
        
        assert resource.id == "/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1"
        assert resource.name == "vm1"
        assert resource.resource_type == "virtual_machine"
        assert resource.cloud_provider == CloudProvider.AZURE
        assert resource.region == "eastus"
    
    def test_to_neo4j_properties(self):
        """Test converting resource to Neo4j properties"""
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
        assert props["tags"] == {"env": "prod"}
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
        
        result.add_resource(DiscoveredResource(
            id="r1", name="r1", resource_type="test",
            cloud_provider=CloudProvider.AZURE, region="eastus"
        ))
        result.add_application(Application(id="a1", name="a1"))
        result.add_error("Test error")
        result.complete()
        
        summary = result.summary()
        
        assert "1 resources" in summary
        assert "1 applications" in summary
        assert "1 errors" in summary
        assert "duration:" in summary
