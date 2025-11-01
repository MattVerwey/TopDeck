"""
GCP Resource Mapper.

Maps GCP SDK resource objects to TopDeck's normalized DiscoveredResource model.
"""

import re
from typing import Any

from ..connection_parser import ConnectionStringParser
from ..models import CloudProvider, DiscoveredResource, ResourceDependency, ResourceStatus


class GCPResourceMapper:
    """
    Maps GCP resources to TopDeck's normalized resource model.
    """

    # Mapping from GCP resource types to TopDeck resource types
    RESOURCE_TYPE_MAP = {
        # Compute
        "compute.googleapis.com/Instance": "compute_instance",
        "container.googleapis.com/Cluster": "gke_cluster",
        "run.googleapis.com/Service": "cloud_run_service",
        "cloudfunctions.googleapis.com/CloudFunction": "cloud_function",
        "appengine.googleapis.com/Application": "app_engine_app",
        # Databases
        "sqladmin.googleapis.com/Instance": "cloud_sql_instance",
        "spanner.googleapis.com/Instance": "spanner_instance",
        "firestore.googleapis.com/Database": "firestore_database",
        "redis.googleapis.com/Instance": "memorystore_redis",
        # Storage
        "storage.googleapis.com/Bucket": "storage_bucket",
        "bigquery.googleapis.com/Dataset": "bigquery_dataset",
        # Networking
        "compute.googleapis.com/Network": "vpc_network",
        "compute.googleapis.com/Subnetwork": "subnet",
        "compute.googleapis.com/Firewall": "firewall_rule",
        "compute.googleapis.com/ForwardingRule": "forwarding_rule",
        "compute.googleapis.com/TargetHttpProxy": "http_proxy",
        "compute.googleapis.com/TargetHttpsProxy": "https_proxy",
        # Configuration & Secrets
        "secretmanager.googleapis.com/Secret": "secret_manager_secret",
        "cloudkms.googleapis.com/CryptoKey": "kms_key",
    }

    @staticmethod
    def map_resource_type(gcp_type: str) -> str:
        """
        Map GCP resource type to TopDeck resource type.

        Args:
            gcp_type: GCP resource type (e.g., "compute.googleapis.com/Instance")

        Returns:
            Normalized resource type (e.g., "compute_instance")
        """
        return GCPResourceMapper.RESOURCE_TYPE_MAP.get(gcp_type, "unknown")

    @staticmethod
    def extract_project_id(resource_name: str) -> str | None:
        """
        Extract project ID from GCP resource name.

        Args:
            resource_name: GCP resource name (e.g., "projects/my-project/...")

        Returns:
            Project ID or None
        """
        # GCP resource name format: projects/{project}/...
        match = re.search(r"projects/([^/]+)", resource_name)
        return match.group(1) if match else None

    @staticmethod
    def extract_zone_or_region(resource_name: str) -> str | None:
        """
        Extract zone or region from GCP resource name.

        Args:
            resource_name: GCP resource name

        Returns:
            Zone or region name, or None
        """
        # Try to extract zone first (e.g., zones/us-central1-a)
        match = re.search(r"zones/([^/]+)", resource_name)
        if match:
            zone = match.group(1)
            # Convert zone to region (e.g., us-central1-a -> us-central1)
            region_match = re.match(r"([a-z]+-[a-z]+\d+)", zone)
            return region_match.group(1) if region_match else zone

        # Try to extract region (e.g., regions/us-central1)
        match = re.search(r"regions/([^/]+)", resource_name)
        if match:
            return match.group(1)

        # Try to extract location (e.g., locations/us-central1)
        match = re.search(r"locations/([^/]+)", resource_name)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def map_state_to_status(state: str | None) -> ResourceStatus:
        """
        Map GCP resource state to TopDeck resource status.

        Args:
            state: GCP resource state (e.g., "RUNNING", "TERMINATED", "PROVISIONING")

        Returns:
            Normalized resource status
        """
        if not state:
            return ResourceStatus.UNKNOWN

        state_upper = state.upper()

        if state_upper in ("RUNNING", "READY", "ACTIVE"):
            return ResourceStatus.RUNNING
        elif state_upper in ("TERMINATED", "STOPPED", "SUSPENDED"):
            return ResourceStatus.STOPPED
        elif state_upper in ("FAILED", "ERROR", "UNHEALTHY"):
            return ResourceStatus.ERROR
        elif state_upper in ("PROVISIONING", "STAGING", "STOPPING", "SUSPENDING", "DEGRADED"):
            return ResourceStatus.DEGRADED
        else:
            return ResourceStatus.UNKNOWN

    @staticmethod
    def extract_environment_from_labels(labels: dict[str, str] | None) -> str | None:
        """
        Extract environment from GCP resource labels.

        GCP uses labels (key-value pairs) similar to tags.
        Looks for common label keys: environment, env

        Args:
            labels: GCP resource labels dictionary

        Returns:
            Environment name (e.g., "prod", "staging", "dev") or None
        """
        if not labels:
            return None

        # Check common environment label keys
        for key in ("environment", "env", "Environment", "Env", "ENVIRONMENT"):
            if key in labels:
                return labels[key].lower()

        return None

    @staticmethod
    def normalize_labels(labels: dict[str, str] | None) -> dict[str, str]:
        """
        Normalize GCP labels to a simple dict format for Neo4j.

        GCP labels are already in dict format, so this is a simple passthrough
        with validation.

        Args:
            labels: GCP resource labels dictionary

        Returns:
            Normalized labels dictionary
        """
        if not labels:
            return {}

        if isinstance(labels, dict):
            return labels

        return {}

    @staticmethod
    def map_gcp_resource(
        resource_name: str,
        display_name: str,
        resource_type: str,
        region: str | None = None,
        labels: dict[str, str] | None = None,
        properties: dict[str, Any] | None = None,
        state: str | None = None,
    ) -> DiscoveredResource:
        """
        Map a GCP resource to a DiscoveredResource.

        Args:
            resource_name: GCP resource full name (e.g., "projects/.../zones/.../instances/...")
            display_name: Human-readable resource name
            resource_type: GCP resource type
            region: GCP region (if not in resource_name)
            labels: GCP resource labels (dict format)
            properties: GCP-specific properties
            state: Resource state

        Returns:
            DiscoveredResource instance formatted for Neo4j
        """
        # Extract region from resource name if not provided
        if not region:
            region = GCPResourceMapper.extract_zone_or_region(resource_name) or "global"

        normalized_labels = GCPResourceMapper.normalize_labels(labels)

        return DiscoveredResource(
            id=resource_name,
            name=display_name,
            resource_type=GCPResourceMapper.map_resource_type(resource_type),
            cloud_provider=CloudProvider.GCP,
            region=region,
            resource_group=None,  # GCP doesn't have resource groups
            subscription_id=GCPResourceMapper.extract_project_id(resource_name),
            status=GCPResourceMapper.map_state_to_status(state),
            environment=GCPResourceMapper.extract_environment_from_labels(labels),
            tags=normalized_labels,
            properties=properties or {},
        )

    @staticmethod
    def extract_connection_strings_from_properties(
        resource_name: str, resource_type: str, properties: dict[str, Any]
    ) -> list[ResourceDependency]:
        """
        Extract connection string-based dependencies from resource properties.

        Args:
            resource_name: Source resource name
            resource_type: GCP resource type
            properties: Resource properties

        Returns:
            List of ResourceDependency objects discovered from connection strings
        """
        dependencies = []
        parser = ConnectionStringParser()

        # Handle different resource types
        if resource_type == "cloudfunctions.googleapis.com/CloudFunction":
            # Cloud Function - check environment variables
            env_vars = properties.get("environmentVariables", {})
            for var_name, var_value in env_vars.items():
                if isinstance(var_value, str) and any(
                    key in var_name.upper()
                    for key in ["CONNECTION", "DATABASE", "DB", "ENDPOINT", "URL", "REDIS", "CACHE"]
                ):
                    conn_info = parser.parse_connection_string(var_value)
                    if conn_info and conn_info.host:
                        target_id = parser.extract_host_from_connection_info(conn_info)
                        if target_id:
                            dep = parser.create_dependency_from_connection(
                                source_id=resource_name,
                                target_id=target_id,
                                conn_info=conn_info,
                                description=f"Cloud Function environment: {var_name}",
                            )
                            dependencies.append(dep)

        elif resource_type == "run.googleapis.com/Service":
            # Cloud Run - check environment variables
            template = properties.get("template", {})
            containers = template.get("containers", [])
            for container in containers:
                env_vars = container.get("env", [])
                for env_var in env_vars:
                    var_name = env_var.get("name", "")
                    var_value = env_var.get("value", "")
                    if any(
                        key in var_name.upper()
                        for key in ["CONNECTION", "DATABASE", "DB", "ENDPOINT", "URL"]
                    ):
                        conn_info = parser.parse_connection_string(var_value)
                        if conn_info and conn_info.host:
                            target_id = parser.extract_host_from_connection_info(conn_info)
                            if target_id:
                                dep = parser.create_dependency_from_connection(
                                    source_id=resource_name,
                                    target_id=target_id,
                                    conn_info=conn_info,
                                    description=f"Cloud Run environment: {var_name}",
                                )
                                dependencies.append(dep)

        elif resource_type == "compute.googleapis.com/Instance":
            # Compute Instance - check metadata
            metadata = properties.get("metadata", {})
            items = metadata.get("items", [])
            for item in items:
                key = item.get("key", "")
                value = item.get("value", "")
                if any(
                    pattern in key.lower() for pattern in ["connection", "database", "endpoint"]
                ):
                    conn_info = parser.parse_connection_string(value)
                    if conn_info and conn_info.host:
                        target_id = parser.extract_host_from_connection_info(conn_info)
                        if target_id:
                            dep = parser.create_dependency_from_connection(
                                source_id=resource_name,
                                target_id=target_id,
                                conn_info=conn_info,
                                description=f"Instance metadata: {key}",
                            )
                            dependencies.append(dep)

        return dependencies
