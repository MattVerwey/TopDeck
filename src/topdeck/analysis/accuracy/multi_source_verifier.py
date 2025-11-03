"""
Multi-source dependency verification.

Verifies and corroborates dependencies using multiple data sources:
1. Azure infrastructure discovery (IPs, backends, resource connections)
2. Azure DevOps code analysis (secrets, config, storage accounts)
3. Prometheus metrics (actual traffic patterns)
4. Tempo traces (transaction flows)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.collectors.tempo import TempoCollector
from topdeck.storage.neo4j_client import Neo4jClient

# AzureDevOpsDiscoverer is an optional dependency for ADO verification
try:
    from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer
except ImportError:
    AzureDevOpsDiscoverer = None

logger = structlog.get_logger(__name__)


@dataclass
class VerificationEvidence:
    """Evidence from a single verification source."""

    source: str  # "azure_infrastructure", "ado_code", "prometheus", "tempo"
    evidence_type: str
    confidence: float
    details: dict[str, Any]
    verified_at: datetime


@dataclass
class DependencyVerificationResult:
    """Result of multi-source dependency verification."""

    source_id: str
    target_id: str
    is_verified: bool
    overall_confidence: float
    evidence: list[VerificationEvidence] = field(default_factory=list)
    verification_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MultiSourceDependencyVerifier:
    """
    Verifies dependencies using multiple independent sources.

    Combines evidence from:
    - Azure infrastructure (IPs, backends, network topology)
    - Azure DevOps code (deployment configs, secrets, storage)
    - Prometheus (actual traffic and metrics)
    - Tempo (distributed traces showing actual calls)
    """

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        ado_discoverer: AzureDevOpsDiscoverer | None = None,
        prometheus_collector: PrometheusCollector | None = None,
        tempo_collector: TempoCollector | None = None,
    ):
        """
        Initialize multi-source verifier.

        Args:
            neo4j_client: Neo4j client for querying stored resources
            ado_discoverer: Azure DevOps discoverer for code analysis
            prometheus_collector: Prometheus collector for metrics
            tempo_collector: Tempo collector for traces
        """
        self.neo4j = neo4j_client
        self.ado_discoverer = ado_discoverer
        self.prometheus = prometheus_collector
        self.tempo = tempo_collector

    async def verify_dependency(
        self,
        source_id: str,
        target_id: str,
        duration: timedelta = timedelta(hours=24),
    ) -> DependencyVerificationResult:
        """
        Verify a dependency using all available sources.

        Args:
            source_id: Source resource ID
            target_id: Target resource ID
            duration: Time range for monitoring data verification

        Returns:
            DependencyVerificationResult with evidence from all sources
        """
        evidence = []
        recommendations = []

        # Get resource details from Neo4j
        source_resource = await self._get_resource(source_id)
        target_resource = await self._get_resource(target_id)

        if not source_resource or not target_resource:
            return DependencyVerificationResult(
                source_id=source_id,
                target_id=target_id,
                is_verified=False,
                overall_confidence=0.0,
                recommendations=["Resources not found in graph database"],
            )

        # 1. Verify from Azure infrastructure (IPs, backends)
        infra_evidence = await self._verify_from_azure_infrastructure(
            source_resource, target_resource
        )
        if infra_evidence:
            evidence.append(infra_evidence)

        # 2. Verify from ADO code analysis
        if self.ado_discoverer:
            ado_evidence = await self._verify_from_ado_code(source_resource, target_resource)
            if ado_evidence:
                evidence.append(ado_evidence)

        # 3. Verify from Prometheus metrics
        if self.prometheus:
            prom_evidence = await self._verify_from_prometheus(
                source_id, target_id, duration
            )
            if prom_evidence:
                evidence.append(prom_evidence)

        # 4. Verify from Tempo traces
        if self.tempo:
            tempo_evidence = await self._verify_from_tempo(source_id, target_id, duration)
            if tempo_evidence:
                evidence.append(tempo_evidence)

        # Calculate verification score and confidence
        verification_score = self._calculate_verification_score(evidence)
        overall_confidence = self._calculate_overall_confidence(evidence)
        is_verified = verification_score >= 0.6  # 60% threshold

        # Generate recommendations
        if not is_verified:
            recommendations.append(
                "Dependency lacks sufficient verification across data sources"
            )
        if len(evidence) < 2:
            recommendations.append(
                "Only single source verification available - consider enabling more data sources"
            )
        if overall_confidence < 0.5:
            recommendations.append(
                "Low confidence - dependency may be incorrect or stale"
            )

        return DependencyVerificationResult(
            source_id=source_id,
            target_id=target_id,
            is_verified=is_verified,
            overall_confidence=overall_confidence,
            evidence=evidence,
            verification_score=verification_score,
            recommendations=recommendations,
        )

    async def _get_resource(self, resource_id: str) -> dict[str, Any] | None:
        """Get resource details from Neo4j."""
        query = """
        MATCH (r:Resource {id: $resource_id})
        RETURN r.id as id,
               r.name as name,
               r.type as type,
               r.properties as properties,
               r.ip_addresses as ip_addresses,
               r.backend_pools as backend_pools,
               r.endpoint as endpoint
        """
        result = await self.neo4j.execute_query(query, {"resource_id": resource_id})
        return result[0] if result else None

    async def _verify_from_azure_infrastructure(
        self, source: dict[str, Any], target: dict[str, Any]
    ) -> VerificationEvidence | None:
        """
        Verify dependency from Azure infrastructure.

        Checks:
        - IP address matches in backend pools
        - Network connections between resources
        - Load balancer backends
        - Application Gateway backends
        """
        details = {}
        confidence = 0.0
        evidence_items = []

        source_ips = source.get("ip_addresses", [])
        target_ips = target.get("ip_addresses", [])
        source_backends = source.get("backend_pools", [])
        target_endpoint = target.get("endpoint")

        # Check if target IPs are in source's backend pools
        if source_backends and target_ips:
            for backend_pool in source_backends:
                backend_ips = backend_pool.get("ip_addresses", [])
                matching_ips = set(backend_ips) & set(target_ips)
                if matching_ips:
                    evidence_items.append(
                        f"Target IPs {matching_ips} found in source backend pool '{backend_pool.get('name')}'"
                    )
                    confidence += 0.3

        # Check if target endpoint is referenced in source properties
        if target_endpoint:
            source_props = source.get("properties", {})
            source_props_str = str(source_props).lower()
            if target_endpoint.lower() in source_props_str:
                evidence_items.append(
                    f"Target endpoint '{target_endpoint}' referenced in source properties"
                )
                confidence += 0.2

        # Check network connectivity (same VNet, peered VNets, etc.)
        source_vnet = source.get("properties", {}).get("virtualNetwork")
        target_vnet = target.get("properties", {}).get("virtualNetwork")
        if source_vnet and target_vnet:
            if source_vnet == target_vnet:
                evidence_items.append("Resources in same Virtual Network")
                confidence += 0.2
            # Check for VNet peering in graph
            peering_exists = await self._check_vnet_peering(source_vnet, target_vnet)
            if peering_exists:
                evidence_items.append("Resources in peered Virtual Networks")
                confidence += 0.15

        if evidence_items:
            details["evidence_items"] = evidence_items
            details["source_ips"] = source_ips
            details["target_ips"] = target_ips
            details["backend_pools_checked"] = len(source_backends)

            return VerificationEvidence(
                source="azure_infrastructure",
                evidence_type="network_topology",
                confidence=min(confidence, 1.0),
                details=details,
                verified_at=datetime.now(timezone.utc),
            )

        return None

    async def _verify_from_ado_code(
        self, source: dict[str, Any], target: dict[str, Any]
    ) -> VerificationEvidence | None:
        """
        Verify dependency from Azure DevOps code analysis.

        Checks:
        - Deployment pipelines referencing both resources
        - Configuration files with connection strings
        - Secret references
        - Storage account references
        """
        if not self.ado_discoverer:
            return None

        details = {}
        confidence = 0.0
        evidence_items = []

        target_name = target.get("name")

        # Query Neo4j for ADO deployments related to source
        query = """
        MATCH (r:Resource {id: $resource_id})-[:DEPLOYED_BY]->(d:Deployment)
        RETURN d.repository as repository,
               d.pipeline as pipeline,
               d.config as config
        LIMIT 10
        """
        deployments = await self.neo4j.execute_query(
            query, {"resource_id": source.get("id")}
        )

        for deployment in deployments:
            config = deployment.get("config", {})
            config_str = str(config).lower()

            # Check for target resource name in config
            if target_name and target_name.lower() in config_str:
                evidence_items.append(
                    f"Target resource '{target_name}' referenced in deployment config"
                )
                confidence += 0.25

            # Check for connection strings
            connection_patterns = [
                r"server=.*" + re.escape(target_name or ""),
                r"endpoint=.*" + re.escape(target_name or ""),
                r"connectionstring.*" + re.escape(target_name or ""),
            ]
            for pattern in connection_patterns:
                if re.search(pattern, config_str, re.IGNORECASE):
                    evidence_items.append(
                        f"Connection string pattern found for target in deployment"
                    )
                    confidence += 0.2
                    break

            # Check for storage account references
            if target.get("type") == "Microsoft.Storage/storageAccounts":
                if "storageaccount" in config_str or "storage" in config_str:
                    evidence_items.append("Storage account reference found in config")
                    confidence += 0.15

            # Check for secret references
            secret_patterns = [r"keyvault", r"secret", r"password", r"key"]
            if any(
                re.search(pattern, config_str, re.IGNORECASE) for pattern in secret_patterns
            ):
                evidence_items.append("Secret/KeyVault references found in config")
                confidence += 0.1

        if evidence_items:
            details["evidence_items"] = evidence_items
            details["deployments_analyzed"] = len(deployments)

            return VerificationEvidence(
                source="ado_code",
                evidence_type="deployment_config",
                confidence=min(confidence, 1.0),
                details=details,
                verified_at=datetime.now(timezone.utc),
            )

        return None

    async def _verify_from_prometheus(
        self, source_id: str, target_id: str, duration: timedelta
    ) -> VerificationEvidence | None:
        """
        Verify dependency from Prometheus metrics.

        Checks:
        - Request counts between services
        - Network traffic patterns
        - Connection pool metrics
        """
        if not self.prometheus:
            return None

        details = {}
        confidence = 0.0
        evidence_items = []

        end_time = datetime.now(timezone.utc)
        start_time = end_time - duration

        # Build Prometheus queries for service-to-service communication
        # Query for HTTP requests from source to target
        http_query = f'rate(http_requests_total{{source_service="{source_id}",target_service="{target_id}"}}[5m])'
        http_results = await self.prometheus.query_range(
            http_query, start_time, end_time, "5m"
        )

        if http_results:
            # Calculate total requests
            total_requests = sum(
                sum(float(value[1]) for value in result.get("values", []))
                for result in http_results
            )
            if total_requests > 0:
                evidence_items.append(
                    f"Detected {total_requests:.0f} HTTP requests from source to target"
                )
                confidence += 0.4

        # Query for connection pool usage
        conn_query = f'avg(connection_pool_active{{source="{source_id}",target="{target_id}"}})'
        conn_results = await self.prometheus.query(conn_query)

        if conn_results:
            evidence_items.append("Active connection pool detected between resources")
            confidence += 0.3

        # Query for network traffic
        network_query = f'rate(network_bytes_sent{{source="{source_id}",destination="{target_id}"}}[5m])'
        network_results = await self.prometheus.query_range(
            network_query, start_time, end_time, "5m"
        )

        if network_results:
            evidence_items.append("Network traffic detected between resources")
            confidence += 0.2

        if evidence_items:
            details["evidence_items"] = evidence_items
            details["time_range_hours"] = duration.total_seconds() / 3600
            details["queries_executed"] = 3

            return VerificationEvidence(
                source="prometheus",
                evidence_type="traffic_metrics",
                confidence=min(confidence, 1.0),
                details=details,
                verified_at=datetime.now(timezone.utc),
            )

        return None

    async def _verify_from_tempo(
        self, source_id: str, target_id: str, duration: timedelta
    ) -> VerificationEvidence | None:
        """
        Verify dependency from Tempo distributed traces.

        Checks:
        - Traces showing source calling target
        - Transaction flows between services
        - Error patterns in service communication
        """
        if not self.tempo:
            return None

        details = {}
        confidence = 0.0
        evidence_items = []

        end_time = datetime.now(timezone.utc)
        start_time = end_time - duration

        # Search for traces involving both services
        traces = await self.tempo.search_traces(
            service_name=source_id,
            start_time=start_time,
            end_time=end_time,
            limit=100,
        )

        matching_traces = []
        for trace in traces:
            # Check if trace contains spans from both source and target
            span_services = {span.service_name for span in trace.spans}
            if source_id in span_services and target_id in span_services:
                matching_traces.append(trace)

                # Check if source calls target (parent-child relationship)
                for span in trace.spans:
                    if span.service_name == source_id:
                        # Look for child spans from target
                        for child_span in trace.spans:
                            if (
                                child_span.service_name == target_id
                                and child_span.parent_span_id == span.span_id
                            ):
                                evidence_items.append(
                                    f"Trace {trace.trace_id[:8]}... shows direct call from source to target"
                                )
                                confidence += 0.1
                                break

        if matching_traces:
            trace_count = len(matching_traces)
            evidence_items.insert(
                0, f"Found {trace_count} distributed traces showing interaction"
            )
            confidence += min(trace_count * 0.05, 0.5)  # Up to 0.5 confidence

            # Calculate average latency
            latencies = [trace.duration_ms for trace in matching_traces]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            details["average_latency_ms"] = avg_latency

        if evidence_items:
            details["evidence_items"] = evidence_items
            details["traces_analyzed"] = len(traces)
            details["matching_traces"] = len(matching_traces)
            details["time_range_hours"] = duration.total_seconds() / 3600

            return VerificationEvidence(
                source="tempo",
                evidence_type="distributed_traces",
                confidence=min(confidence, 1.0),
                details=details,
                verified_at=datetime.now(timezone.utc),
            )

        return None

    async def _check_vnet_peering(
        self, source_vnet: str, target_vnet: str
    ) -> bool:
        """Check if two VNets have peering relationship in graph."""
        query = """
        MATCH (v1:Resource {id: $vnet1})-[:PEERED_WITH]-(v2:Resource {id: $vnet2})
        RETURN count(*) > 0 as exists
        """
        result = await self.neo4j.execute_query(
            query, {"vnet1": source_vnet, "vnet2": target_vnet}
        )
        return result[0].get("exists", False) if result else False

    def _calculate_verification_score(self, evidence: list[VerificationEvidence]) -> float:
        """
        Calculate verification score based on number and quality of evidence.

        Score weights:
        - 4 sources: 1.0 (all sources verified)
        - 3 sources: 0.85
        - 2 sources: 0.70
        - 1 source: 0.50
        - 0 sources: 0.0
        """
        if not evidence:
            return 0.0

        source_count = len(evidence)
        base_score = {
            1: 0.50,
            2: 0.70,
            3: 0.85,
            4: 1.0,
        }.get(source_count, 1.0)

        # Adjust based on individual evidence confidence
        avg_confidence = sum(e.confidence for e in evidence) / len(evidence)
        adjusted_score = base_score * avg_confidence

        return min(adjusted_score, 1.0)

    def _calculate_overall_confidence(
        self, evidence: list[VerificationEvidence]
    ) -> float:
        """
        Calculate overall confidence from multiple evidence sources.

        Uses weighted average based on evidence source reliability:
        - Azure infrastructure: 0.9 (most reliable, actual network config)
        - ADO code: 0.8 (declared dependencies)
        - Tempo traces: 0.85 (actual transaction flows)
        - Prometheus metrics: 0.75 (aggregated traffic patterns)
        """
        if not evidence:
            return 0.0

        weights = {
            "azure_infrastructure": 0.9,
            "ado_code": 0.8,
            "tempo": 0.85,
            "prometheus": 0.75,
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for ev in evidence:
            weight = weights.get(ev.source, 0.5)
            weighted_sum += ev.confidence * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0
