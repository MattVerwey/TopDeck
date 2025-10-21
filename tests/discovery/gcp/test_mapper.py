"""
Tests for GCP Resource Mapper.
"""

from topdeck.discovery.gcp.mapper import GCPResourceMapper
from topdeck.discovery.models import CloudProvider, ResourceStatus


class TestGCPResourceMapper:
    """Tests for GCPResourceMapper"""

    def test_map_resource_type_known(self):
        """Test mapping known GCP resource types"""
        assert (
            GCPResourceMapper.map_resource_type("compute.googleapis.com/Instance")
            == "compute_instance"
        )
        assert (
            GCPResourceMapper.map_resource_type("container.googleapis.com/Cluster") == "gke_cluster"
        )
        assert (
            GCPResourceMapper.map_resource_type("sqladmin.googleapis.com/Instance")
            == "cloud_sql_instance"
        )
        assert (
            GCPResourceMapper.map_resource_type("storage.googleapis.com/Bucket") == "storage_bucket"
        )

    def test_map_resource_type_unknown(self):
        """Test mapping unknown GCP resource type"""
        assert GCPResourceMapper.map_resource_type("unknown.googleapis.com/Resource") == "unknown"

    def test_extract_project_id(self):
        """Test extracting project ID from GCP resource name"""
        name = "projects/my-project-123/zones/us-central1-a/instances/my-vm"
        assert GCPResourceMapper.extract_project_id(name) == "my-project-123"

    def test_extract_project_id_invalid(self):
        """Test extracting project ID from invalid resource name"""
        assert GCPResourceMapper.extract_project_id("not-a-resource-name") is None

    def test_extract_zone_or_region_from_zone(self):
        """Test extracting region from zone"""
        name = "projects/my-project/zones/us-central1-a/instances/my-vm"
        assert GCPResourceMapper.extract_zone_or_region(name) == "us-central1"

    def test_extract_zone_or_region_from_region(self):
        """Test extracting region from region"""
        name = "projects/my-project/regions/us-central1/addresses/my-ip"
        assert GCPResourceMapper.extract_zone_or_region(name) == "us-central1"

    def test_extract_zone_or_region_from_location(self):
        """Test extracting region from location"""
        name = "projects/my-project/locations/us-central1/services/my-service"
        assert GCPResourceMapper.extract_zone_or_region(name) == "us-central1"

    def test_extract_zone_or_region_global(self):
        """Test extracting region from global resource"""
        name = "projects/my-project/global/networks/my-network"
        assert GCPResourceMapper.extract_zone_or_region(name) is None

    def test_map_state_to_status_running(self):
        """Test mapping running states"""
        assert GCPResourceMapper.map_state_to_status("RUNNING") == ResourceStatus.RUNNING
        assert GCPResourceMapper.map_state_to_status("READY") == ResourceStatus.RUNNING
        assert GCPResourceMapper.map_state_to_status("ACTIVE") == ResourceStatus.RUNNING

    def test_map_state_to_status_stopped(self):
        """Test mapping stopped states"""
        assert GCPResourceMapper.map_state_to_status("TERMINATED") == ResourceStatus.STOPPED
        assert GCPResourceMapper.map_state_to_status("STOPPED") == ResourceStatus.STOPPED
        assert GCPResourceMapper.map_state_to_status("SUSPENDED") == ResourceStatus.STOPPED

    def test_map_state_to_status_error(self):
        """Test mapping error states"""
        assert GCPResourceMapper.map_state_to_status("FAILED") == ResourceStatus.ERROR
        assert GCPResourceMapper.map_state_to_status("ERROR") == ResourceStatus.ERROR
        assert GCPResourceMapper.map_state_to_status("UNHEALTHY") == ResourceStatus.ERROR

    def test_map_state_to_status_degraded(self):
        """Test mapping degraded states"""
        assert GCPResourceMapper.map_state_to_status("PROVISIONING") == ResourceStatus.DEGRADED
        assert GCPResourceMapper.map_state_to_status("STAGING") == ResourceStatus.DEGRADED
        assert GCPResourceMapper.map_state_to_status("STOPPING") == ResourceStatus.DEGRADED

    def test_map_state_to_status_unknown(self):
        """Test mapping unknown states"""
        assert GCPResourceMapper.map_state_to_status(None) == ResourceStatus.UNKNOWN
        assert GCPResourceMapper.map_state_to_status("UNKNOWN_STATE") == ResourceStatus.UNKNOWN

    def test_extract_environment_from_labels(self):
        """Test extracting environment from GCP labels"""
        labels = {"environment": "production", "application": "web"}
        assert GCPResourceMapper.extract_environment_from_labels(labels) == "production"

    def test_extract_environment_from_labels_uppercase(self):
        """Test extracting environment from uppercase label key"""
        labels = {"ENVIRONMENT": "Staging"}
        assert GCPResourceMapper.extract_environment_from_labels(labels) == "staging"

    def test_extract_environment_from_labels_env(self):
        """Test extracting environment from 'env' label"""
        labels = {"env": "dev"}
        assert GCPResourceMapper.extract_environment_from_labels(labels) == "dev"

    def test_extract_environment_from_labels_none(self):
        """Test extracting environment when no environment label exists"""
        labels = {"application": "web"}
        assert GCPResourceMapper.extract_environment_from_labels(labels) is None

    def test_extract_environment_from_labels_empty(self):
        """Test extracting environment from empty labels"""
        assert GCPResourceMapper.extract_environment_from_labels({}) is None
        assert GCPResourceMapper.extract_environment_from_labels(None) is None

    def test_normalize_labels_dict(self):
        """Test normalizing GCP labels (dict format)"""
        labels = {"environment": "production", "application": "web"}
        result = GCPResourceMapper.normalize_labels(labels)
        assert result == labels

    def test_normalize_labels_empty(self):
        """Test normalizing empty labels"""
        assert GCPResourceMapper.normalize_labels({}) == {}
        assert GCPResourceMapper.normalize_labels(None) == {}

    def test_map_gcp_resource_complete(self):
        """Test mapping a complete GCP resource"""
        resource_name = "projects/my-project-123/zones/us-central1-a/instances/web-server-01"
        labels = {"environment": "production", "application": "web"}

        resource = GCPResourceMapper.map_gcp_resource(
            resource_name=resource_name,
            display_name="web-server-01",
            resource_type="compute.googleapis.com/Instance",
            region="us-central1",
            labels=labels,
            properties={"machineType": "n1-standard-2"},
            state="RUNNING",
        )

        assert resource.id == resource_name
        assert resource.name == "web-server-01"
        assert resource.resource_type == "compute_instance"
        assert resource.cloud_provider == CloudProvider.GCP
        assert resource.region == "us-central1"
        assert resource.subscription_id == "my-project-123"
        assert resource.status == ResourceStatus.RUNNING
        assert resource.environment == "production"
        assert resource.tags == labels
        assert resource.properties == {"machineType": "n1-standard-2"}

    def test_map_gcp_resource_minimal(self):
        """Test mapping GCP resource with minimal data"""
        resource_name = "projects/my-project/global/buckets/my-bucket"

        resource = GCPResourceMapper.map_gcp_resource(
            resource_name=resource_name,
            display_name="my-bucket",
            resource_type="storage.googleapis.com/Bucket",
        )

        assert resource.id == resource_name
        assert resource.name == "my-bucket"
        assert resource.resource_type == "storage_bucket"
        assert resource.cloud_provider == CloudProvider.GCP
        assert resource.region == "global"  # Default when not specified
        assert resource.subscription_id == "my-project"
        assert resource.tags == {}
        assert resource.properties == {}
        assert resource.status == ResourceStatus.UNKNOWN

    def test_map_gcp_resource_auto_extract_region(self):
        """Test auto-extracting region from resource name"""
        resource_name = "projects/my-project/zones/europe-west1-b/instances/my-vm"

        resource = GCPResourceMapper.map_gcp_resource(
            resource_name=resource_name,
            display_name="my-vm",
            resource_type="compute.googleapis.com/Instance",
            state="RUNNING",
        )

        # Region should be auto-extracted from zone
        assert resource.region == "europe-west1"

    def test_map_gcp_resource_neo4j_format(self):
        """Test Neo4j formatting of mapped GCP resource"""
        resource_name = "projects/my-project/zones/us-west1-a/instances/db-server"
        labels = {"env": "dev", "team": "backend"}

        resource = GCPResourceMapper.map_gcp_resource(
            resource_name=resource_name,
            display_name="db-server",
            resource_type="sqladmin.googleapis.com/Instance",
            labels=labels,
            properties={"databaseVersion": "POSTGRES_15"},
            state="RUNNING",
        )

        neo4j_props = resource.to_neo4j_properties()

        assert neo4j_props["id"] == resource_name
        assert neo4j_props["name"] == "db-server"
        assert neo4j_props["resource_type"] == "cloud_sql_instance"
        assert neo4j_props["cloud_provider"] == "gcp"
        assert neo4j_props["region"] == "us-west1"
        assert neo4j_props["subscription_id"] == "my-project"
        assert neo4j_props["status"] == "running"
        assert neo4j_props["environment"] == "dev"
        assert neo4j_props["tags"] == labels
        assert '"databaseVersion": "POSTGRES_15"' in neo4j_props["properties"]
        assert "discovered_at" in neo4j_props
        assert "last_seen" in neo4j_props

    def test_map_gcp_resource_global_resource(self):
        """Test mapping a global GCP resource"""
        resource_name = "projects/my-project/global/networks/my-vpc"

        resource = GCPResourceMapper.map_gcp_resource(
            resource_name=resource_name,
            display_name="my-vpc",
            resource_type="compute.googleapis.com/Network",
            region="global",
        )

        assert resource.region == "global"
