"""
Tests for comprehensive dependency detection across cloud providers.

This test suite validates that the dependency discovery logic correctly identifies
all relevant dependencies between resources, not just a few hardcoded patterns.
"""
import pytest

from topdeck.discovery.azure.discoverer import AzureDiscoverer
from topdeck.discovery.aws.discoverer import AWSDiscoverer
from topdeck.discovery.gcp.discoverer import GCPDiscoverer
from topdeck.discovery.models import (
    CloudProvider,
    DiscoveredResource,
    ResourceStatus,
)


@pytest.mark.asyncio
async def test_azure_comprehensive_dependencies():
    """Test that Azure discoverer detects multiple dependency types."""
    resources = [
        # Web application
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Web/sites/webapp1",
            name="webapp1",
            resource_type="app_service",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
        # Database
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/srv1/databases/db1",
            name="db1",
            resource_type="sql_database",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
        # Storage
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/storage1",
            name="storage1",
            resource_type="storage_account",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
        # Cache
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Cache/redis/cache1",
            name="cache1",
            resource_type="redis_cache",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
    ]

    discoverer = AzureDiscoverer(subscription_id="test-sub")
    dependencies = await discoverer._discover_dependencies(resources)

    # Should find at least 3 dependencies for the app service
    # (database, storage, cache)
    assert len(dependencies) >= 3, f"Expected at least 3 dependencies, got {len(dependencies)}"

    # Verify app service has dependencies
    webapp_deps = [d for d in dependencies if d.source_id == resources[0].id]
    assert len(webapp_deps) >= 3, "App Service should have multiple dependencies"

    # Verify specific dependency types exist
    dep_targets = [d.target_id for d in webapp_deps]
    assert any("db1" in t for t in dep_targets), "Should depend on database"
    assert any("storage1" in t for t in dep_targets), "Should depend on storage"
    assert any("cache1" in t for t in dep_targets), "Should depend on cache"


@pytest.mark.asyncio
async def test_azure_hierarchical_dependencies():
    """Test that Azure discoverer detects hierarchical relationships precisely."""
    resources = [
        # SQL Server (parent)
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/sqlserver1",
            name="sqlserver1",
            resource_type="sql_server",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
        # SQL Database (child)
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/sqlserver1/databases/db1",
            name="db1",
            resource_type="sql_database",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
    ]

    discoverer = AzureDiscoverer(subscription_id="test-sub")
    dependencies = await discoverer._discover_dependencies(resources)

    # Should find the hierarchical relationship
    hierarchical_deps = [d for d in dependencies if d.discovered_method == "resource_hierarchy"]
    assert len(hierarchical_deps) > 0, "Should detect hierarchical relationship"

    # Verify the database -> server relationship
    db_to_server = [
        d
        for d in hierarchical_deps
        if d.source_id == resources[1].id and d.target_id == resources[0].id
    ]
    assert len(db_to_server) == 1, "Should have DB -> Server relationship"
    assert db_to_server[0].strength == 1.0, "Hierarchical relationship should have strength 1.0"


@pytest.mark.asyncio
async def test_aws_comprehensive_dependencies():
    """Test that AWS discoverer detects multiple dependency types."""
    resources = [
        # Lambda function
        DiscoveredResource(
            id="arn:aws:lambda:us-east-1:123456789012:function:my-function",
            name="my-function",
            resource_type="lambda",
            cloud_provider=CloudProvider.AWS,
            region="us-east-1",
            status=ResourceStatus.RUNNING,
            tags={},
            properties={},
        ),
        # RDS database
        DiscoveredResource(
            id="arn:aws:rds:us-east-1:123456789012:db:mydb",
            name="mydb",
            resource_type="rds",
            cloud_provider=CloudProvider.AWS,
            region="us-east-1",
            status=ResourceStatus.RUNNING,
            tags={},
            properties={},
        ),
        # S3 bucket
        DiscoveredResource(
            id="arn:aws:s3:::my-bucket",
            name="my-bucket",
            resource_type="s3",
            cloud_provider=CloudProvider.AWS,
            region="us-east-1",
            status=ResourceStatus.RUNNING,
            tags={},
            properties={},
        ),
    ]

    discoverer = AWSDiscoverer(region="us-east-1")
    dependencies = await discoverer._discover_dependencies(resources)

    # Should find lambda dependencies to RDS and S3
    assert len(dependencies) >= 2, f"Expected at least 2 dependencies, got {len(dependencies)}"

    lambda_deps = [d for d in dependencies if "lambda" in d.source_id]
    assert len(lambda_deps) >= 2, "Lambda should have multiple dependencies"


@pytest.mark.asyncio
async def test_gcp_comprehensive_dependencies():
    """Test that GCP discoverer detects multiple dependency types."""
    resources = [
        # Cloud Run service
        DiscoveredResource(
            id="projects/my-project/locations/us-central1/services/my-service",
            name="my-service",
            resource_type="cloud_run",
            cloud_provider=CloudProvider.GCP,
            region="us-central1",
            status=ResourceStatus.RUNNING,
            tags={},
            properties={},
        ),
        # Cloud SQL
        DiscoveredResource(
            id="projects/my-project/instances/my-sql",
            name="my-sql",
            resource_type="cloud_sql",
            cloud_provider=CloudProvider.GCP,
            region="us-central1",
            status=ResourceStatus.RUNNING,
            tags={},
            properties={},
        ),
        # Cloud Storage
        DiscoveredResource(
            id="projects/my-project/buckets/my-bucket",
            name="my-bucket",
            resource_type="cloud_storage",
            cloud_provider=CloudProvider.GCP,
            region="us-central1",
            status=ResourceStatus.RUNNING,
            tags={},
            properties={},
        ),
    ]

    discoverer = GCPDiscoverer(project_id="my-project")
    dependencies = await discoverer._discover_dependencies(resources)

    # Should find Cloud Run dependencies
    assert len(dependencies) >= 2, f"Expected at least 2 dependencies, got {len(dependencies)}"

    cloud_run_deps = [d for d in dependencies if "my-service" in d.source_id]
    assert len(cloud_run_deps) >= 2, "Cloud Run should have multiple dependencies"


@pytest.mark.asyncio
async def test_no_dependencies_across_resource_groups():
    """Test that dependencies are not created across different resource groups."""
    resources = [
        # App in RG1
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Web/sites/webapp1",
            name="webapp1",
            resource_type="app_service",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
        # Database in RG2
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg2/providers/Microsoft.Sql/servers/srv1/databases/db1",
            name="db1",
            resource_type="sql_database",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg2",
            tags={},
            properties={},
        ),
    ]

    discoverer = AzureDiscoverer(subscription_id="test-sub")
    dependencies = await discoverer._discover_dependencies(resources)

    # Should not create dependencies across resource groups
    cross_rg_deps = [
        d
        for d in dependencies
        if d.source_id == resources[0].id and d.target_id == resources[1].id
    ]
    assert len(cross_rg_deps) == 0, "Should not create dependencies across resource groups"


@pytest.mark.asyncio
async def test_multiple_resources_depend_on_same_target():
    """Test that multiple resources can depend on the same target."""
    resources = [
        # App 1
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Web/sites/webapp1",
            name="webapp1",
            resource_type="app_service",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
        # App 2
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Web/sites/webapp2",
            name="webapp2",
            resource_type="app_service",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
        # Shared database
        DiscoveredResource(
            id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Sql/servers/srv1/databases/db1",
            name="db1",
            resource_type="sql_database",
            cloud_provider=CloudProvider.AZURE,
            region="eastus",
            status=ResourceStatus.RUNNING,
            resource_group="rg1",
            tags={},
            properties={},
        ),
    ]

    discoverer = AzureDiscoverer(subscription_id="test-sub")
    dependencies = await discoverer._discover_dependencies(resources)

    # Both apps should depend on the database
    webapp1_to_db = [
        d for d in dependencies if d.source_id == resources[0].id and "db1" in d.target_id
    ]
    webapp2_to_db = [
        d for d in dependencies if d.source_id == resources[1].id and "db1" in d.target_id
    ]

    assert len(webapp1_to_db) > 0, "webapp1 should depend on database"
    assert len(webapp2_to_db) > 0, "webapp2 should depend on database"
