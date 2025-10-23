"""
Monitoring-based dependency discovery.

Discovers resource dependencies by analyzing logs from Loki and metrics
from Prometheus to identify actual communication patterns.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ..monitoring.collectors.loki import LokiCollector
from ..monitoring.collectors.prometheus import PrometheusCollector
from .models import DependencyCategory, DependencyType, ResourceDependency


@dataclass
class TrafficPattern:
    """Represents a traffic pattern between resources."""

    source_id: str
    target_id: str
    protocol: str | None = None
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float | None = None
    confidence: float = 0.0  # 0.0-1.0


@dataclass
class DependencyEvidence:
    """Evidence for a dependency relationship."""

    source_id: str
    target_id: str
    evidence_type: str  # "logs", "metrics", "connection_string"
    confidence: float
    details: dict[str, Any]
    discovered_at: datetime


class MonitoringDependencyDiscovery:
    """
    Discovers dependencies by analyzing monitoring data.
    
    Uses:
    - Loki logs to identify service-to-service communication
    - Prometheus metrics to identify connection patterns
    """

    def __init__(
        self,
        loki_collector: LokiCollector | None = None,
        prometheus_collector: PrometheusCollector | None = None
    ):
        """
        Initialize monitoring-based dependency discovery.
        
        Args:
            loki_collector: Loki collector for log analysis
            prometheus_collector: Prometheus collector for metrics analysis
        """
        self.loki_collector = loki_collector
        self.prometheus_collector = prometheus_collector

    async def discover_dependencies_from_logs(
        self,
        resource_ids: list[str],
        duration: timedelta = timedelta(hours=24)
    ) -> list[DependencyEvidence]:
        """
        Discover dependencies by analyzing logs.
        
        Looks for patterns in logs that indicate communication:
        - HTTP requests to other services
        - Database queries
        - Cache operations
        - Message queue operations
        
        Args:
            resource_ids: List of resource IDs to analyze
            duration: Time range to analyze
            
        Returns:
            List of dependency evidence
        """
        if not self.loki_collector:
            return []
        
        evidence_list = []
        
        for resource_id in resource_ids:
            # Get logs for this resource
            try:
                streams = await self.loki_collector.get_resource_logs(
                    resource_id=resource_id,
                    duration=duration
                )
                
                # Analyze logs for dependency patterns
                for stream in streams:
                    for entry in stream.entries:
                        # Extract target services from log messages
                        targets = self._extract_targets_from_log(entry.message)
                        
                        for target in targets:
                            evidence_list.append(
                                DependencyEvidence(
                                    source_id=resource_id,
                                    target_id=target["id"],
                                    evidence_type="logs",
                                    confidence=target["confidence"],
                                    details={
                                        "protocol": target.get("protocol"),
                                        "endpoint": target.get("endpoint"),
                                        "log_timestamp": entry.timestamp.isoformat()
                                    },
                                    discovered_at=datetime.utcnow()
                                )
                            )
            except Exception:
                # Continue even if one resource fails
                continue
        
        # Aggregate evidence by source-target pairs
        return self._aggregate_evidence(evidence_list)

    async def discover_dependencies_from_metrics(
        self,
        resource_ids: list[str],
        duration: timedelta = timedelta(hours=24)
    ) -> list[DependencyEvidence]:
        """
        Discover dependencies by analyzing metrics.
        
        Looks for patterns in metrics that indicate communication:
        - HTTP request counts between services
        - Database connection counts
        - Cache hit/miss patterns
        - Network traffic patterns
        
        Args:
            resource_ids: List of resource IDs to analyze
            duration: Time range to analyze
            
        Returns:
            List of dependency evidence
        """
        if not self.prometheus_collector:
            return []
        
        evidence_list = []
        
        for resource_id in resource_ids:
            try:
                # Get metrics for this resource
                metrics = await self.prometheus_collector.get_resource_metrics(
                    resource_id=resource_id,
                    resource_type="service",
                    duration=duration
                )
                
                # Analyze request patterns
                if "request_rate" in metrics.metrics:
                    series = metrics.metrics["request_rate"]
                    for value in series.values:
                        # Extract target from labels
                        target_id = value.labels.get("target_service") or value.labels.get("destination")
                        if target_id and target_id != resource_id:
                            evidence_list.append(
                                DependencyEvidence(
                                    source_id=resource_id,
                                    target_id=target_id,
                                    evidence_type="metrics",
                                    confidence=0.8,  # Metrics are reliable
                                    details={
                                        "metric": "request_rate",
                                        "avg_value": value.value,
                                        "timestamp": value.timestamp.isoformat()
                                    },
                                    discovered_at=datetime.utcnow()
                                )
                            )
                
                # Analyze connection metrics
                if "connections" in metrics.metrics:
                    series = metrics.metrics["connections"]
                    for value in series.values:
                        target_id = value.labels.get("database") or value.labels.get("cache")
                        if target_id and target_id != resource_id:
                            evidence_list.append(
                                DependencyEvidence(
                                    source_id=resource_id,
                                    target_id=target_id,
                                    evidence_type="metrics",
                                    confidence=0.85,
                                    details={
                                        "metric": "connections",
                                        "avg_value": value.value,
                                        "timestamp": value.timestamp.isoformat()
                                    },
                                    discovered_at=datetime.utcnow()
                                )
                            )
            except Exception:
                continue
        
        return self._aggregate_evidence(evidence_list)

    async def analyze_traffic_patterns(
        self,
        resource_ids: list[str],
        duration: timedelta = timedelta(hours=24)
    ) -> list[TrafficPattern]:
        """
        Analyze traffic patterns between resources.
        
        Combines log and metric data to build a complete picture of
        resource communication patterns.
        
        Args:
            resource_ids: List of resource IDs to analyze
            duration: Time range to analyze
            
        Returns:
            List of traffic patterns
        """
        patterns = []
        
        # Get evidence from both sources
        log_evidence = await self.discover_dependencies_from_logs(resource_ids, duration)
        metric_evidence = await self.discover_dependencies_from_metrics(resource_ids, duration)
        
        # Combine evidence
        all_evidence = log_evidence + metric_evidence
        
        # Group by source-target pairs
        evidence_by_pair: dict[tuple[str, str], list[DependencyEvidence]] = {}
        for evidence in all_evidence:
            key = (evidence.source_id, evidence.target_id)
            if key not in evidence_by_pair:
                evidence_by_pair[key] = []
            evidence_by_pair[key].append(evidence)
        
        # Create traffic patterns
        for (source_id, target_id), evidence_list in evidence_by_pair.items():
            # Calculate aggregate metrics
            request_count = sum(
                1 for e in evidence_list
                if e.evidence_type in ("logs", "metrics")
            )
            
            # Average confidence across all evidence
            avg_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list)
            
            # Extract protocol if available
            protocols = [
                e.details.get("protocol")
                for e in evidence_list
                if e.details.get("protocol")
            ]
            protocol = protocols[0] if protocols else None
            
            patterns.append(
                TrafficPattern(
                    source_id=source_id,
                    target_id=target_id,
                    protocol=protocol,
                    request_count=request_count,
                    confidence=avg_confidence
                )
            )
        
        return patterns

    def create_dependencies_from_traffic_patterns(
        self,
        patterns: list[TrafficPattern],
        min_confidence: float = 0.5
    ) -> list[ResourceDependency]:
        """
        Create ResourceDependency objects from traffic patterns.
        
        Args:
            patterns: Traffic patterns to convert
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of ResourceDependency objects
        """
        dependencies = []
        
        for pattern in patterns:
            # Skip low-confidence patterns
            if pattern.confidence < min_confidence:
                continue
            
            # Determine dependency type based on traffic characteristics
            if pattern.request_count > 100:
                dep_type = DependencyType.REQUIRED
                strength = 0.9
            elif pattern.request_count > 10:
                dep_type = DependencyType.STRONG
                strength = 0.7
            else:
                dep_type = DependencyType.OPTIONAL
                strength = 0.5
            
            # Determine category based on protocol
            if pattern.protocol in ("http", "https"):
                category = DependencyCategory.NETWORK
            elif pattern.protocol in ("sql", "postgresql", "mysql"):
                category = DependencyCategory.DATA
            else:
                category = DependencyCategory.COMPUTE
            
            dependencies.append(
                ResourceDependency(
                    source_id=pattern.source_id,
                    target_id=pattern.target_id,
                    category=category,
                    dependency_type=dep_type,
                    strength=min(strength * pattern.confidence, 1.0),
                    discovered_method="traffic_analysis",
                    description=f"Traffic pattern: {pattern.request_count} requests via {pattern.protocol or 'unknown'}"
                )
            )
        
        return dependencies

    def _extract_targets_from_log(self, message: str) -> list[dict[str, Any]]:
        """
        Extract target service information from a log message.
        
        Looks for patterns like:
        - HTTP requests: "GET https://api.example.com/endpoint"
        - Database queries: "Connecting to postgres://db.example.com:5432"
        - Service calls: "Calling service: order-service"
        
        Args:
            message: Log message
            
        Returns:
            List of target information dictionaries
        """
        targets = []
        
        # HTTP/HTTPS URLs
        http_pattern = re.compile(
            r'(https?://([a-zA-Z0-9\-\.]+(?:\:[0-9]+)?)[^\s]*)',
            re.IGNORECASE
        )
        for match in http_pattern.finditer(message):
            full_url = match.group(1)
            host = match.group(2)
            targets.append({
                "id": host,
                "protocol": "https" if "https" in full_url else "http",
                "endpoint": full_url,
                "confidence": 0.8
            })
        
        # Database connection patterns
        db_pattern = re.compile(
            r'(postgres|mysql|mongodb)://([a-zA-Z0-9\-\.]+)',
            re.IGNORECASE
        )
        for match in db_pattern.finditer(message):
            protocol = match.group(1).lower()
            host = match.group(2)
            targets.append({
                "id": host,
                "protocol": protocol,
                "endpoint": f"{protocol}://{host}",
                "confidence": 0.85
            })
        
        # Service name patterns (e.g., "calling order-service")
        service_pattern = re.compile(
            r'(?:calling|connecting to|requesting)\s+([a-zA-Z0-9\-]+(?:-service)?)',
            re.IGNORECASE
        )
        for match in service_pattern.finditer(message):
            service_name = match.group(1)
            targets.append({
                "id": service_name,
                "protocol": None,
                "endpoint": service_name,
                "confidence": 0.6
            })
        
        return targets

    def _aggregate_evidence(
        self,
        evidence_list: list[DependencyEvidence]
    ) -> list[DependencyEvidence]:
        """
        Aggregate evidence by source-target pairs.
        
        Combines multiple pieces of evidence for the same dependency
        into a single higher-confidence evidence.
        
        Args:
            evidence_list: List of evidence to aggregate
            
        Returns:
            Aggregated evidence list
        """
        # Group by source-target pair
        evidence_by_pair: dict[tuple[str, str], list[DependencyEvidence]] = {}
        for evidence in evidence_list:
            key = (evidence.source_id, evidence.target_id)
            if key not in evidence_by_pair:
                evidence_by_pair[key] = []
            evidence_by_pair[key].append(evidence)
        
        # Aggregate each group
        aggregated = []
        for (source_id, target_id), group in evidence_by_pair.items():
            # Calculate combined confidence (average)
            avg_confidence = sum(e.confidence for e in group) / len(group)
            
            # Boost confidence if we have multiple types of evidence
            evidence_types = set(e.evidence_type for e in group)
            if len(evidence_types) > 1:
                avg_confidence = min(avg_confidence * 1.2, 1.0)
            
            # Combine details
            combined_details = {
                "occurrence_count": len(group),
                "evidence_types": list(evidence_types)
            }
            
            aggregated.append(
                DependencyEvidence(
                    source_id=source_id,
                    target_id=target_id,
                    evidence_type="aggregated",
                    confidence=avg_confidence,
                    details=combined_details,
                    discovered_at=datetime.utcnow()
                )
            )
        
        return aggregated
