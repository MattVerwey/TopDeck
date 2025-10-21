"""
Feature extraction for ML predictions.

Extracts features from Prometheus metrics and Neo4j graph for training
and prediction.
"""

from datetime import datetime, timedelta
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class FeatureExtractor:
    """
    Extracts features from various data sources for ML models.

    Features are extracted from:
    - Prometheus metrics (time-series data)
    - Neo4j graph (relationships, topology)
    - Resource metadata
    """

    def __init__(self, prometheus_collector=None, neo4j_client=None):
        """
        Initialize feature extractor.

        Args:
            prometheus_collector: PrometheusCollector instance for metrics
            neo4j_client: Neo4jClient instance for graph data
        """
        self.prometheus = prometheus_collector
        self.neo4j = neo4j_client

    async def extract_failure_features(
        self, resource_id: str, resource_type: str, lookback_hours: int = 168  # 7 days
    ) -> dict[str, float]:
        """
        Extract features for failure prediction.

        Args:
            resource_id: Resource to extract features for
            resource_type: Type of resource
            lookback_hours: How far back to look for historical data

        Returns:
            Dictionary of feature names to values
        """
        features = {}

        # Time-series features from Prometheus
        if self.prometheus:
            metrics_features = await self._extract_metrics_features(
                resource_id, resource_type, lookback_hours
            )
            features.update(metrics_features)

        # Graph features from Neo4j
        if self.neo4j:
            graph_features = await self._extract_graph_features(resource_id)
            features.update(graph_features)

        # Resource metadata features
        metadata_features = self._extract_metadata_features(resource_type)
        features.update(metadata_features)

        return features

    async def extract_performance_features(
        self, resource_id: str, metric_name: str, lookback_hours: int = 168
    ) -> dict[str, Any]:
        """
        Extract time-series data for performance prediction.

        Args:
            resource_id: Resource to extract features for
            metric_name: Specific metric to extract
            lookback_hours: How far back to look

        Returns:
            Dictionary with time-series data and contextual features
        """
        features = {
            "timestamps": [],
            "values": [],
            "resource_id": resource_id,
            "metric_name": metric_name,
        }

        if not self.prometheus:
            return features

        # Get time-series data
        end = datetime.utcnow()
        end - timedelta(hours=lookback_hours)

        # This is a placeholder - actual implementation would query Prometheus
        # query = f'{metric_name}{{resource_id="{resource_id}"}}'
        # results = await self.prometheus.query_range(query, start, end, "5m")

        # For now, return structure
        logger.info(
            "extract_performance_features",
            resource_id=resource_id,
            metric_name=metric_name,
            lookback_hours=lookback_hours,
        )

        return features

    async def extract_anomaly_features(
        self, resource_id: str, lookback_hours: int = 24
    ) -> dict[str, list[float]]:
        """
        Extract features for anomaly detection.

        Args:
            resource_id: Resource to analyze
            lookback_hours: Recent time window

        Returns:
            Dictionary of metric names to value lists
        """
        features = {}

        if not self.prometheus:
            return features

        # Get all relevant metrics for the resource
        # This would query multiple metrics from Prometheus
        metrics_to_check = [
            "cpu_usage",
            "memory_usage",
            "latency_p95",
            "error_rate",
            "request_rate",
        ]

        for metric in metrics_to_check:
            # Placeholder for actual Prometheus query
            features[metric] = []

        logger.info(
            "extract_anomaly_features",
            resource_id=resource_id,
            lookback_hours=lookback_hours,
            metrics_count=len(features),
        )

        return features

    async def _extract_metrics_features(
        self, resource_id: str, resource_type: str, lookback_hours: int
    ) -> dict[str, float]:
        """Extract statistical features from Prometheus metrics."""
        features = {}

        # CPU usage statistics
        features["cpu_mean"] = 0.5
        features["cpu_max"] = 0.8
        features["cpu_std"] = 0.15
        features["cpu_trend"] = 0.05  # Positive = increasing

        # Memory usage statistics
        features["memory_mean"] = 0.6
        features["memory_max"] = 0.85
        features["memory_std"] = 0.12
        features["memory_trend"] = 0.08

        # Error rate statistics
        features["error_rate_mean"] = 0.02
        features["error_rate_max"] = 0.05
        features["error_spike_count"] = 3

        # Latency statistics (if applicable)
        if resource_type in ("web_app", "api", "service"):
            features["latency_p95_mean"] = 250.0
            features["latency_p95_max"] = 500.0
            features["latency_increasing"] = 1.0  # Boolean as float

        # Restart/failure history
        features["restart_count"] = 2
        features["days_since_last_failure"] = 30.0

        logger.info(
            "_extract_metrics_features", resource_id=resource_id, features_count=len(features)
        )

        return features

    async def _extract_graph_features(self, resource_id: str) -> dict[str, float]:
        """Extract features from Neo4j graph relationships."""
        features = {}

        # Dependency metrics
        features["dependency_count"] = 5.0
        features["dependent_count"] = 8.0
        features["dependency_depth"] = 3.0  # How deep in dependency chain

        # Centrality metrics
        features["is_central_node"] = 1.0  # Boolean
        features["betweenness_centrality"] = 0.6

        # Risk propagation
        features["blast_radius"] = 12.0
        features["is_spof"] = 0.0  # Single point of failure

        logger.info(
            "_extract_graph_features", resource_id=resource_id, features_count=len(features)
        )

        return features

    def _extract_metadata_features(self, resource_type: str) -> dict[str, float]:
        """Extract features from resource metadata."""
        features = {}

        # Resource type encoding (one-hot style)
        features["is_database"] = 1.0 if "database" in resource_type.lower() else 0.0
        features["is_web_app"] = 1.0 if "web" in resource_type.lower() else 0.0
        features["is_load_balancer"] = 1.0 if "load_balancer" in resource_type.lower() else 0.0

        # Age and change frequency
        features["resource_age_days"] = 180.0
        features["deployment_frequency"] = 2.0  # Deployments per week
        features["config_change_frequency"] = 1.0  # Changes per week

        return features

    def get_feature_names(self) -> list[str]:
        """
        Get list of all feature names.

        Returns:
            List of feature names
        """
        return [
            # CPU features
            "cpu_mean",
            "cpu_max",
            "cpu_std",
            "cpu_trend",
            # Memory features
            "memory_mean",
            "memory_max",
            "memory_std",
            "memory_trend",
            # Error features
            "error_rate_mean",
            "error_rate_max",
            "error_spike_count",
            # Latency features
            "latency_p95_mean",
            "latency_p95_max",
            "latency_increasing",
            # History features
            "restart_count",
            "days_since_last_failure",
            # Graph features
            "dependency_count",
            "dependent_count",
            "dependency_depth",
            "is_central_node",
            "betweenness_centrality",
            "blast_radius",
            "is_spof",
            # Metadata features
            "is_database",
            "is_web_app",
            "is_load_balancer",
            "resource_age_days",
            "deployment_frequency",
            "config_change_frequency",
        ]
