"""
Tests for GCP Resource Discoverer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from topdeck.discovery.gcp.discoverer import GCPDiscoverer
from topdeck.discovery.models import DiscoveredResource


class TestGCPDiscoverer:
    """Test suite for GCPDiscoverer."""

    @pytest.fixture
    def discoverer(self):
        """Create a GCPDiscoverer instance for testing."""
        return GCPDiscoverer(
            project_id="test-project",
            credentials_path="/path/to/credentials.json",
        )

    def test_initialization(self, discoverer):
        """Test that discoverer initializes correctly."""
        assert discoverer.project_id == "test-project"
        assert discoverer.credentials_path == "/path/to/credentials.json"
        assert discoverer.mapper is not None

    @pytest.mark.asyncio
    async def test_discover_all_resources_without_gcp_sdk(self):
        """Test discovery when GCP SDK is not available."""
        with patch("topdeck.discovery.gcp.discoverer.GCP_AVAILABLE", False):
            discoverer = GCPDiscoverer(project_id="test-project")
            result = await discoverer.discover_all_resources()

            assert result.cloud_provider == "gcp"
            assert len(result.resources) == 0
            assert len(result.errors) == 1
            assert "GCP SDK not available" in result.errors[0]

    @pytest.mark.asyncio
    async def test_discover_compute_instances(self, discoverer):
        """Test Compute Engine instance discovery."""
        # Mock Compute Engine client
        mock_instance = MagicMock()
        mock_instance.name = "test-instance"
        mock_instance.machine_type = "n1-standard-1"
        mock_instance.status = "RUNNING"
        mock_instance.labels = {"env": "dev", "team": "platform"}

        mock_instances_client = MagicMock()
        mock_instances_client.list.return_value = [mock_instance]

        with patch("topdeck.discovery.gcp.discoverer.compute_v1.InstancesClient") as mock_client_class:
            mock_client_class.return_value = mock_instances_client
            resources = await discoverer._discover_compute_instances("us-central1")

            assert len(resources) == 1
            resource = resources[0]
            assert resource.resource_type == "compute_engine"
            assert "machine_type" in resource.properties
            assert resource.properties["status"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_discover_gke_clusters(self, discoverer):
        """Test GKE cluster discovery."""
        # Mock GKE cluster
        mock_cluster = MagicMock()
        mock_cluster.name = "test-cluster"
        mock_cluster.status = "RUNNING"
        mock_cluster.current_node_count = 3
        mock_cluster.endpoint = "https://test-cluster.gke.io"
        mock_cluster.resource_labels = {"env": "prod"}

        mock_response = MagicMock()
        mock_response.clusters = [mock_cluster]

        mock_cluster_client = MagicMock()
        mock_cluster_client.list_clusters.return_value = mock_response

        with patch("topdeck.discovery.gcp.discoverer.container_v1.ClusterManagerClient") as mock_client_class:
            mock_client_class.return_value = mock_cluster_client
            resources = await discoverer._discover_gke_clusters("us-central1")

            assert len(resources) == 1
            resource = resources[0]
            assert resource.resource_type == "gke_cluster"
            assert resource.properties["status"] == "RUNNING"
            assert resource.properties["current_node_count"] == 3

    @pytest.mark.asyncio
    async def test_discover_cloud_sql_instances(self, discoverer):
        """Test Cloud SQL instance discovery."""
        # Cloud SQL discovery is a placeholder for now
        resources = await discoverer._discover_cloud_sql_instances("us-central1")
        
        # Should return empty list for now (placeholder implementation)
        assert isinstance(resources, list)

    @pytest.mark.asyncio
    async def test_discover_storage_buckets(self, discoverer):
        """Test Cloud Storage bucket discovery."""
        # Mock Storage client
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_bucket.location = "US-CENTRAL1"
        mock_bucket.storage_class = "STANDARD"
        mock_bucket.location_type = "regional"
        mock_bucket.labels = {"project": "test"}

        mock_storage_client = MagicMock()
        mock_storage_client.list_buckets.return_value = [mock_bucket]

        with patch("topdeck.discovery.gcp.discoverer.storage.Client") as mock_client_class:
            mock_client_class.return_value = mock_storage_client
            resources = await discoverer._discover_storage_buckets()

            assert len(resources) == 1
            resource = resources[0]
            assert resource.resource_type == "cloud_storage"
            assert resource.properties["storage_class"] == "STANDARD"

    @pytest.mark.asyncio
    async def test_discover_cloud_functions(self, discoverer):
        """Test Cloud Functions discovery."""
        # Cloud Functions discovery is a placeholder for now
        resources = await discoverer._discover_cloud_functions("us-central1")
        
        # Should return empty list for now (placeholder implementation)
        assert isinstance(resources, list)

    @pytest.mark.asyncio
    async def test_discover_cloud_run_services(self, discoverer):
        """Test Cloud Run service discovery."""
        # Cloud Run discovery is a placeholder for now
        resources = await discoverer._discover_cloud_run_services("us-central1")
        
        # Should return empty list for now (placeholder implementation)
        assert isinstance(resources, list)

    @pytest.mark.asyncio
    async def test_discover_vpcs(self, discoverer):
        """Test VPC network discovery."""
        # Mock VPC network
        mock_network = MagicMock()
        mock_network.name = "test-network"
        mock_network.auto_create_subnetworks = True
        mock_network.routing_config = MagicMock()
        mock_network.routing_config.routing_mode = "REGIONAL"

        mock_networks_client = MagicMock()
        mock_networks_client.list.return_value = [mock_network]

        with patch("topdeck.discovery.gcp.discoverer.compute_v1.NetworksClient") as mock_client_class:
            mock_client_class.return_value = mock_networks_client
            resources = await discoverer._discover_vpcs("us-central1")

            assert len(resources) == 1
            resource = resources[0]
            assert resource.resource_type == "vpc_network"
            assert resource.properties["auto_create_subnetworks"] is True

    @pytest.mark.asyncio
    async def test_discover_dependencies(self, discoverer):
        """Test dependency discovery between resources."""
        # Create mock resources
        vpc_resource = DiscoveredResource(
            id="projects/test-project/global/networks/test-network",
            name="test-network",
            resource_type="vpc_network",
            cloud_provider="gcp",
            region="global",
        )

        compute_resource = DiscoveredResource(
            id="projects/test-project/zones/us-central1-a/instances/test-instance",
            name="test-instance",
            resource_type="compute_engine",
            cloud_provider="gcp",
            region="us-central1",
        )

        resources = [vpc_resource, compute_resource]

        dependencies = await discoverer._discover_dependencies(resources)

        # GCP dependency detection is basic for now
        assert isinstance(dependencies, list)

    @pytest.mark.asyncio
    async def test_infer_applications(self, discoverer):
        """Test application inference from resources."""
        # Create resources with application labels
        resource1 = DiscoveredResource(
            id="projects/test-project/zones/us-central1-a/instances/web-1",
            name="web-1",
            resource_type="compute_engine",
            cloud_provider="gcp",
            region="us-central1",
            tags={"app": "web-app"},
        )

        resource2 = DiscoveredResource(
            id="projects/test-project/zones/us-central1-a/instances/web-2",
            name="web-2",
            resource_type="compute_engine",
            cloud_provider="gcp",
            region="us-central1",
            tags={"app": "web-app"},
        )

        resources = [resource1, resource2]

        applications = await discoverer._infer_applications(resources)

        assert len(applications) == 1
        app = applications[0]
        assert app.name == "web-app"

    def test_get_project_number_without_gcp_sdk(self):
        """Test getting project number when GCP SDK is not available."""
        with patch("topdeck.discovery.gcp.discoverer.GCP_AVAILABLE", False):
            discoverer = GCPDiscoverer(project_id="test-project")
            project_number = discoverer.get_project_number()
            assert project_number is None

    @pytest.mark.asyncio
    async def test_multi_region_discovery(self, discoverer):
        """Test discovery across multiple regions."""
        with patch.object(discoverer, "_discover_compute_instances", new_callable=AsyncMock) as mock_compute:
            with patch.object(discoverer, "_discover_gke_clusters", new_callable=AsyncMock) as mock_gke:
                with patch.object(discoverer, "_discover_cloud_sql_instances", new_callable=AsyncMock) as mock_sql:
                    with patch.object(discoverer, "_discover_vpcs", new_callable=AsyncMock) as mock_vpcs:
                        with patch.object(discoverer, "_discover_cloud_functions", new_callable=AsyncMock) as mock_functions:
                            with patch.object(discoverer, "_discover_cloud_run_services", new_callable=AsyncMock) as mock_run:
                                with patch.object(discoverer, "_discover_storage_buckets", new_callable=AsyncMock) as mock_storage:
                                    with patch.object(discoverer, "_discover_dependencies", new_callable=AsyncMock) as mock_deps:
                                        with patch.object(discoverer, "_infer_applications", new_callable=AsyncMock) as mock_apps:
                                            # Set return values
                                            mock_compute.return_value = []
                                            mock_gke.return_value = []
                                            mock_sql.return_value = []
                                            mock_vpcs.return_value = []
                                            mock_functions.return_value = []
                                            mock_run.return_value = []
                                            mock_storage.return_value = []
                                            mock_deps.return_value = []
                                            mock_apps.return_value = []

                                            regions = ["us-central1", "us-east1"]
                                            result = await discoverer.discover_all_resources(regions=regions)

                                            # Should call each discovery method once per region
                                            assert mock_compute.call_count == 2
                                            assert mock_gke.call_count == 2
                                            assert result.cloud_provider == "gcp"

    @pytest.mark.asyncio
    async def test_error_handling_in_discovery(self, discoverer):
        """Test that errors during discovery are captured and logged."""
        with patch.object(discoverer, "_discover_compute_instances", new_callable=AsyncMock) as mock_compute:
            # Make the method raise an exception
            mock_compute.side_effect = Exception("Test error")
            
            with patch.object(discoverer, "_discover_gke_clusters", new_callable=AsyncMock) as mock_gke:
                with patch.object(discoverer, "_discover_cloud_sql_instances", new_callable=AsyncMock) as mock_sql:
                    with patch.object(discoverer, "_discover_vpcs", new_callable=AsyncMock) as mock_vpcs:
                        with patch.object(discoverer, "_discover_cloud_functions", new_callable=AsyncMock) as mock_functions:
                            with patch.object(discoverer, "_discover_cloud_run_services", new_callable=AsyncMock) as mock_run:
                                with patch.object(discoverer, "_discover_storage_buckets", new_callable=AsyncMock) as mock_storage:
                                    with patch.object(discoverer, "_discover_dependencies", new_callable=AsyncMock) as mock_deps:
                                        with patch.object(discoverer, "_infer_applications", new_callable=AsyncMock) as mock_apps:
                                            # Set return values for other methods
                                            mock_gke.return_value = []
                                            mock_sql.return_value = []
                                            mock_vpcs.return_value = []
                                            mock_functions.return_value = []
                                            mock_run.return_value = []
                                            mock_storage.return_value = []
                                            mock_deps.return_value = []
                                            mock_apps.return_value = []

                                            result = await discoverer.discover_all_resources(regions=["us-central1"])

                                            # Should have error in result
                                            assert len(result.errors) > 0
                                            assert any("Test error" in error for error in result.errors)
