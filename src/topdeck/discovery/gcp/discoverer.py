"""
GCP Resource Discoverer.

Main orchestrator for discovering GCP resources across projects and regions.
"""

import logging
from datetime import datetime
from typing import Any

from ..models import Application, DiscoveredResource, DiscoveryResult, ResourceDependency
from .mapper import GCPResourceMapper

logger = logging.getLogger(__name__)

# Try importing GCP libraries, but make them optional for testing
try:
    from google.cloud import compute_v1, container_v1, storage
    from google.cloud.sql.connector import Connector
    from google.oauth2 import service_account

    GCP_AVAILABLE = True
except ImportError:
    compute_v1 = None
    container_v1 = None
    storage = None
    Connector = None
    service_account = None
    GCP_AVAILABLE = False


class GCPDiscoverer:
    """
    Main class for discovering GCP resources.

    Supports:
    - Multiple projects
    - Multiple regions
    - Multiple resource types (compute, networking, data, config)
    - Async/parallel discovery
    - Relationship detection
    """

    def __init__(
        self,
        project_id: str,
        credentials_path: str | None = None,
    ):
        """
        Initialize GCP discoverer.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON (if None, uses Application Default Credentials)
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.mapper = GCPResourceMapper()

        # Initialize credentials if available
        if GCP_AVAILABLE and credentials_path:
            try:
                self.credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
            except Exception as e:
                logger.warning(f"Failed to load credentials from {credentials_path}: {e}")
                self.credentials = None
        else:
            self.credentials = None

        if not GCP_AVAILABLE:
            logger.warning("GCP SDK not available, GCP discovery will be limited")

    async def discover_all_resources(
        self,
        regions: list[str] | None = None,
        resource_types: list[str] | None = None,
    ) -> DiscoveryResult:
        """
        Discover all GCP resources across specified regions.

        Args:
            regions: List of GCP regions to scan (if None, scans all regions)
            resource_types: List of resource types to discover (if None, discovers all)

        Returns:
            DiscoveryResult containing all discovered resources
        """
        if not GCP_AVAILABLE:
            logger.error("GCP SDK not available, cannot discover GCP resources")
            result = DiscoveryResult(cloud_provider="gcp")
            result.add_error("GCP SDK not available")
            result.complete()
            return result

        # Default to common regions if none specified
        if regions is None:
            regions = ["us-central1", "us-east1", "europe-west1"]

        result = DiscoveryResult(cloud_provider="gcp")

        try:
            logger.info(f"Discovering GCP resources in project {self.project_id}...")

            # Discover resources for each region
            for region_name in regions:
                logger.info(f"Scanning region: {region_name}")

                try:
                    # Discover Compute Engine instances
                    if not resource_types or "compute_engine" in resource_types:
                        compute_resources = await self._discover_compute_instances(region_name)
                        for resource in compute_resources:
                            result.add_resource(resource)

                    # Discover GKE clusters
                    if not resource_types or "gke_cluster" in resource_types:
                        gke_resources = await self._discover_gke_clusters(region_name)
                        for resource in gke_resources:
                            result.add_resource(resource)

                    # Discover Cloud SQL instances
                    if not resource_types or "cloud_sql" in resource_types:
                        sql_resources = await self._discover_cloud_sql_instances(region_name)
                        for resource in sql_resources:
                            result.add_resource(resource)

                    # Discover VPCs (global but we list per region)
                    if not resource_types or "vpc_network" in resource_types:
                        vpc_resources = await self._discover_vpcs(region_name)
                        for resource in vpc_resources:
                            result.add_resource(resource)

                    # Discover Cloud Functions
                    if not resource_types or "cloud_function" in resource_types:
                        function_resources = await self._discover_cloud_functions(region_name)
                        for resource in function_resources:
                            result.add_resource(resource)

                    # Discover Cloud Run services
                    if not resource_types or "cloud_run" in resource_types:
                        run_resources = await self._discover_cloud_run_services(region_name)
                        for resource in run_resources:
                            result.add_resource(resource)

                except Exception as e:
                    error_msg = f"Error discovering resources in region {region_name}: {e}"
                    result.add_error(error_msg)
                    logger.error(error_msg)

            # Discover Cloud Storage buckets (global)
            if not resource_types or "cloud_storage" in resource_types:
                storage_resources = await self._discover_storage_buckets()
                for resource in storage_resources:
                    result.add_resource(resource)

            logger.info(f"Discovered {len(result.resources)} resources")

            # Discover dependencies
            logger.info("Analyzing dependencies...")
            dependencies = await self._discover_dependencies(result.resources)
            for dep in dependencies:
                result.add_dependency(dep)

            logger.info(f"Found {len(dependencies)} dependencies")

            # Infer applications from resources
            logger.info("Inferring applications from resources...")
            applications = await self._infer_applications(result.resources)
            for app in applications:
                result.add_application(app)

            logger.info(f"Found {len(applications)} applications")

        except Exception as e:
            error_msg = f"GCP API error: {e}"
            result.add_error(error_msg)
            logger.error(error_msg)

        result.complete()
        logger.info(result.summary())

        return result

    async def _discover_compute_instances(self, region: str) -> list[DiscoveredResource]:
        """Discover Compute Engine instances in a region."""
        resources = []
        try:
            instances_client = compute_v1.InstancesClient(credentials=self.credentials)

            # List zones in region
            zones = [f"{region}-a", f"{region}-b", f"{region}-c"]

            for zone in zones:
                try:
                    request = compute_v1.ListInstancesRequest(
                        project=self.project_id,
                        zone=zone,
                    )
                    instances = instances_client.list(request=request)

                    for instance in instances:
                        # Build resource name
                        resource_name = (
                            f"projects/{self.project_id}/zones/{zone}/instances/{instance.name}"
                        )

                        # Extract labels (GCP's version of tags)
                        labels = dict(instance.labels) if instance.labels else {}

                        # Map to DiscoveredResource
                        resource = self.mapper.map_resource(
                            resource_id=resource_name,
                            resource_type="compute.googleapis.com/Instance",
                            labels=labels,
                            region=region,
                            project_id=self.project_id,
                        )

                        # Add Compute Engine-specific properties
                        resource.properties["machine_type"] = instance.machine_type
                        resource.properties["status"] = instance.status
                        resource.properties["zone"] = zone

                        resources.append(resource)

                except Exception as e:
                    logger.debug(f"Error discovering instances in zone {zone}: {e}")

        except Exception as e:
            logger.error(f"Error discovering Compute Engine instances in {region}: {e}")

        return resources

    async def _discover_gke_clusters(self, region: str) -> list[DiscoveredResource]:
        """Discover GKE clusters in a region."""
        resources = []
        try:
            cluster_client = container_v1.ClusterManagerClient(credentials=self.credentials)

            # List clusters in region
            parent = f"projects/{self.project_id}/locations/{region}"
            response = cluster_client.list_clusters(parent=parent)

            for cluster in response.clusters:
                # Build resource name
                resource_name = (
                    f"projects/{self.project_id}/locations/{region}/clusters/{cluster.name}"
                )

                # Extract labels
                labels = dict(cluster.resource_labels) if cluster.resource_labels else {}

                # Map to DiscoveredResource
                resource = self.mapper.map_resource(
                    resource_id=resource_name,
                    resource_type="container.googleapis.com/Cluster",
                    labels=labels,
                    region=region,
                    project_id=self.project_id,
                )

                # Add GKE-specific properties
                resource.properties["status"] = cluster.status
                resource.properties["current_node_count"] = cluster.current_node_count
                resource.properties["endpoint"] = cluster.endpoint

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering GKE clusters in {region}: {e}")

        return resources

    async def _discover_cloud_sql_instances(self, region: str) -> list[DiscoveredResource]:
        """Discover Cloud SQL instances in a region."""
        resources = []
        try:
            # Note: Cloud SQL client requires special handling
            # For now, we'll use a simplified approach
            # In production, you'd use google-cloud-sql

            # Placeholder: would use Cloud SQL Admin API
            logger.debug(f"Cloud SQL discovery in {region} - placeholder implementation")

        except Exception as e:
            logger.error(f"Error discovering Cloud SQL instances in {region}: {e}")

        return resources

    async def _discover_storage_buckets(self) -> list[DiscoveredResource]:
        """Discover Cloud Storage buckets (global service)."""
        resources = []
        try:
            storage_client = storage.Client(
                project=self.project_id,
                credentials=self.credentials,
            )

            buckets = storage_client.list_buckets()

            for bucket in buckets:
                # Build resource name
                resource_name = f"projects/{self.project_id}/buckets/{bucket.name}"

                # Extract labels
                labels = dict(bucket.labels) if bucket.labels else {}

                # Map to DiscoveredResource
                resource = self.mapper.map_resource(
                    resource_id=resource_name,
                    resource_type="storage.googleapis.com/Bucket",
                    labels=labels,
                    region=bucket.location.lower(),
                    project_id=self.project_id,
                )

                # Add Storage-specific properties
                resource.properties["storage_class"] = bucket.storage_class
                resource.properties["location_type"] = bucket.location_type

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering Cloud Storage buckets: {e}")

        return resources

    async def _discover_cloud_functions(self, region: str) -> list[DiscoveredResource]:
        """Discover Cloud Functions in a region."""
        resources = []
        try:
            # Note: Cloud Functions v2 client
            # For now, placeholder implementation
            logger.debug(f"Cloud Functions discovery in {region} - placeholder implementation")

        except Exception as e:
            logger.error(f"Error discovering Cloud Functions in {region}: {e}")

        return resources

    async def _discover_cloud_run_services(self, region: str) -> list[DiscoveredResource]:
        """Discover Cloud Run services in a region."""
        resources = []
        try:
            # Note: Cloud Run client
            # For now, placeholder implementation
            logger.debug(f"Cloud Run discovery in {region} - placeholder implementation")

        except Exception as e:
            logger.error(f"Error discovering Cloud Run services in {region}: {e}")

        return resources

    async def _discover_vpcs(self, region: str) -> list[DiscoveredResource]:
        """Discover VPC networks (global but listed per region)."""
        resources = []
        try:
            networks_client = compute_v1.NetworksClient(credentials=self.credentials)

            request = compute_v1.ListNetworksRequest(project=self.project_id)
            networks = networks_client.list(request=request)

            for network in networks:
                # Build resource name
                resource_name = f"projects/{self.project_id}/global/networks/{network.name}"

                # Map to DiscoveredResource (VPCs are global)
                resource = self.mapper.map_resource(
                    resource_id=resource_name,
                    resource_type="compute.googleapis.com/Network",
                    labels={},
                    region="global",
                    project_id=self.project_id,
                )

                # Add VPC-specific properties
                resource.properties["auto_create_subnetworks"] = network.auto_create_subnetworks
                resource.properties["routing_mode"] = network.routing_config.routing_mode

                # Only add once (avoid duplicates across regions)
                if not any(r.id == resource.id for r in resources):
                    resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering VPC networks: {e}")

        return resources

    async def _discover_dependencies(
        self,
        resources: list[DiscoveredResource],
    ) -> list[ResourceDependency]:
        """
        Discover dependencies between GCP resources.

        This analyzes relationships like:
        - Compute instances in VPCs
        - GKE clusters in VPCs
        - Cloud Functions accessing Cloud SQL
        - Cloud Run services accessing Cloud Storage

        Args:
            resources: List of discovered resources

        Returns:
            List of ResourceDependency objects
        """
        dependencies = []

        # Create lookup maps
        resource_by_id = {r.id: r for r in resources}

        # Analyze Compute -> VPC dependencies
        for resource in resources:
            if resource.resource_type == "compute_engine":
                # In GCP, instances are in VPCs by network configuration
                # This is a simplified version
                pass

        # Add more dependency detection as needed
        return dependencies

    async def _infer_applications(
        self,
        resources: list[DiscoveredResource],
    ) -> list[Application]:
        """
        Infer applications from GCP resources based on naming and labeling.

        Args:
            resources: List of discovered resources

        Returns:
            List of Application objects
        """
        applications = []
        app_names = set()

        # Look for application labels
        for resource in resources:
            if "app" in resource.tags or "application" in resource.tags:
                app_name = resource.tags.get("app") or resource.tags.get("application")
                if app_name not in app_names:
                    app_names.add(app_name)
                    app = Application(
                        name=app_name,
                        resource_ids=[resource.id],
                        environment=resource.environment,
                    )
                    applications.append(app)

        return applications

    def get_project_number(self) -> str | None:
        """
        Get the GCP project number for the current project.

        Returns:
            GCP project number or None
        """
        if not GCP_AVAILABLE:
            return None

        try:
            # Would use google-cloud-resource-manager to get project details
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error getting GCP project number: {e}")
            return None
