"""
Enhanced dependency enrichment service.

Combines connection string analysis, log analysis, and metrics analysis
to provide comprehensive dependency discovery.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from ..monitoring.collectors.loki import LokiCollector
from ..monitoring.collectors.prometheus import PrometheusCollector
from .connection_parser import ConnectionStringParser
from .models import DiscoveredResource, ResourceDependency
from .monitoring_dependency_discovery import MonitoringDependencyDiscovery


@dataclass
class DependencyEnrichmentResult:
    """Result from dependency enrichment."""

    original_dependency_count: int
    connection_string_dependencies: list[ResourceDependency]
    monitoring_dependencies: list[ResourceDependency]
    total_new_dependencies: int
    enrichment_summary: dict[str, Any]


class EnhancedDependencyEnrichment:
    """
    Service for enriching resource dependencies using multiple methods.

    Combines:
    1. Connection string analysis from resource properties
    2. Log analysis from Loki
    3. Metrics analysis from Prometheus
    """

    def __init__(self, loki_url: str | None = None, prometheus_url: str | None = None):
        """
        Initialize enhanced dependency enrichment service.

        Args:
            loki_url: Optional Loki server URL
            prometheus_url: Optional Prometheus server URL
        """
        self.connection_parser = ConnectionStringParser()

        # Initialize collectors if URLs provided
        self.loki_collector = LokiCollector(loki_url) if loki_url else None
        self.prometheus_collector = PrometheusCollector(prometheus_url) if prometheus_url else None

        # Initialize monitoring discovery
        self.monitoring_discovery = MonitoringDependencyDiscovery(
            loki_collector=self.loki_collector, prometheus_collector=self.prometheus_collector
        )

    async def enrich_resource_dependencies(
        self,
        resources: list[DiscoveredResource],
        existing_dependencies: list[ResourceDependency] | None = None,
        analyze_monitoring: bool = True,
        monitoring_duration: timedelta = timedelta(hours=24),
    ) -> DependencyEnrichmentResult:
        """
        Enrich resource dependencies using all available methods.

        Args:
            resources: List of discovered resources to analyze
            existing_dependencies: Existing dependencies (optional)
            analyze_monitoring: Whether to analyze monitoring data
            monitoring_duration: How far back to look in monitoring data

        Returns:
            DependencyEnrichmentResult with all discovered dependencies
        """
        existing_dependencies = existing_dependencies or []
        original_count = len(existing_dependencies)

        # 1. Extract dependencies from connection strings
        connection_dependencies = []
        for resource in resources:
            deps = self._extract_connection_string_dependencies(resource)
            connection_dependencies.extend(deps)

        # 2. Analyze monitoring data if enabled
        monitoring_dependencies = []
        if analyze_monitoring and (self.loki_collector or self.prometheus_collector):
            resource_ids = [r.id for r in resources]

            # Get traffic patterns from monitoring
            patterns = await self.monitoring_discovery.analyze_traffic_patterns(
                resource_ids=resource_ids, duration=monitoring_duration
            )

            # Convert patterns to dependencies
            monitoring_dependencies = (
                self.monitoring_discovery.create_dependencies_from_traffic_patterns(
                    patterns=patterns, min_confidence=0.5
                )
            )

        # 3. Combine and deduplicate dependencies
        all_new_dependencies = connection_dependencies + monitoring_dependencies

        # Remove duplicates (same source-target pair)
        seen_pairs = {(d.source_id, d.target_id) for d in existing_dependencies}
        unique_new_dependencies = []

        for dep in all_new_dependencies:
            pair = (dep.source_id, dep.target_id)
            if pair not in seen_pairs:
                unique_new_dependencies.append(dep)
                seen_pairs.add(pair)

        # 4. Create summary
        enrichment_summary = {
            "connection_string_count": len(connection_dependencies),
            "monitoring_count": len(monitoring_dependencies),
            "unique_new_count": len(unique_new_dependencies),
            "duplicate_filtered": len(all_new_dependencies) - len(unique_new_dependencies),
            "methods_used": {
                "connection_strings": True,
                "loki": self.loki_collector is not None and analyze_monitoring,
                "prometheus": self.prometheus_collector is not None and analyze_monitoring,
            },
        }

        return DependencyEnrichmentResult(
            original_dependency_count=original_count,
            connection_string_dependencies=connection_dependencies,
            monitoring_dependencies=monitoring_dependencies,
            total_new_dependencies=len(unique_new_dependencies),
            enrichment_summary=enrichment_summary,
        )

    def _extract_connection_string_dependencies(
        self, resource: DiscoveredResource
    ) -> list[ResourceDependency]:
        """
        Extract dependencies from resource connection strings.

        Args:
            resource: Resource to analyze

        Returns:
            List of discovered dependencies
        """
        dependencies = []

        # Look for connection strings in properties
        properties = resource.properties

        # Common property keys that might contain connection strings
        connection_keys = [
            "connectionString",
            "connection_string",
            "connectionStrings",
            "databaseUrl",
            "database_url",
            "dbConnectionString",
            "storageConnectionString",
            "storage_connection_string",
            "redisConnectionString",
            "redis_connection_string",
            "cacheConnectionString",
            "cache_connection_string",
            "endpoint",
            "endpoints",
            "serviceUrl",
            "service_url",
            "apiUrl",
            "api_url",
            "baseUrl",
            "base_url",
        ]

        # Check all properties for connection strings
        for key, value in properties.items():
            # Check if this is a connection string property
            if any(conn_key in key.lower() for conn_key in connection_keys):
                if isinstance(value, str):
                    conn_info = self.connection_parser.parse_connection_string(value)
                    if conn_info and conn_info.host:
                        target_id = self.connection_parser.extract_host_from_connection_info(
                            conn_info
                        )
                        if target_id and target_id != resource.name:
                            dep = self.connection_parser.create_dependency_from_connection(
                                source_id=resource.id,
                                target_id=target_id,
                                conn_info=conn_info,
                                description=f"Connection from property: {key}",
                            )
                            dependencies.append(dep)

                # Handle arrays of connection strings
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            conn_info = self.connection_parser.parse_connection_string(item)
                            if conn_info and conn_info.host:
                                target_id = (
                                    self.connection_parser.extract_host_from_connection_info(
                                        conn_info
                                    )
                                )
                                if target_id and target_id != resource.name:
                                    dep = self.connection_parser.create_dependency_from_connection(
                                        source_id=resource.id,
                                        target_id=target_id,
                                        conn_info=conn_info,
                                        description=f"Connection from property array: {key}",
                                    )
                                    dependencies.append(dep)

        # Check nested properties (like environment variables, app settings, etc.)
        nested_keys = [
            "environment",
            "env",
            "appSettings",
            "app_settings",
            "config",
            "configuration",
        ]
        for nested_key in nested_keys:
            if nested_key in properties and isinstance(properties[nested_key], dict):
                nested_props = properties[nested_key]
                for key, value in nested_props.items():
                    if isinstance(value, str) and any(
                        pattern in value.lower()
                        for pattern in ["://", "server=", "host=", "endpoint="]
                    ):
                        conn_info = self.connection_parser.parse_connection_string(value)
                        if conn_info and conn_info.host:
                            target_id = self.connection_parser.extract_host_from_connection_info(
                                conn_info
                            )
                            if target_id and target_id != resource.name:
                                dep = self.connection_parser.create_dependency_from_connection(
                                    source_id=resource.id,
                                    target_id=target_id,
                                    conn_info=conn_info,
                                    description=f"Connection from {nested_key}.{key}",
                                )
                                dependencies.append(dep)

        return dependencies

    async def enrich_single_resource(
        self,
        resource: DiscoveredResource,
        analyze_monitoring: bool = True,
        monitoring_duration: timedelta = timedelta(hours=24),
    ) -> list[ResourceDependency]:
        """
        Enrich dependencies for a single resource.

        Args:
            resource: Resource to analyze
            analyze_monitoring: Whether to analyze monitoring data
            monitoring_duration: How far back to look in monitoring data

        Returns:
            List of discovered dependencies for this resource
        """
        result = await self.enrich_resource_dependencies(
            resources=[resource],
            existing_dependencies=[],
            analyze_monitoring=analyze_monitoring,
            monitoring_duration=monitoring_duration,
        )

        return result.connection_string_dependencies + result.monitoring_dependencies

    def get_enrichment_capabilities(self) -> dict[str, bool]:
        """
        Get information about available enrichment capabilities.

        Returns:
            Dictionary of capability names to availability
        """
        return {
            "connection_string_parsing": True,
            "loki_log_analysis": self.loki_collector is not None,
            "prometheus_metrics_analysis": self.prometheus_collector is not None,
            "monitoring_analysis": (
                self.loki_collector is not None or self.prometheus_collector is not None
            ),
        }

    async def close(self):
        """Close collectors and cleanup resources."""
        if self.loki_collector:
            await self.loki_collector.close()
        if self.prometheus_collector:
            await self.prometheus_collector.close()
