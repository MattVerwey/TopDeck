"""
Transaction flow tracing service.

Combines data from multiple observability platforms (Loki, Prometheus, Azure Log Analytics)
to trace transactions through the network and visualize their flow.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from topdeck.monitoring.collectors.azure_log_analytics import (
    AzureLogAnalyticsCollector,
)
from topdeck.monitoring.collectors.loki import LokiCollector
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.storage.neo4j_client import Neo4jClient


@dataclass
class FlowNode:
    """Represents a node in the transaction flow."""

    resource_id: str
    resource_name: str
    resource_type: str
    timestamp: datetime
    duration_ms: float | None = None
    status: str = "success"  # success, error, warning
    log_entries: list[Any] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowEdge:
    """Represents an edge/connection in the transaction flow."""

    source_id: str
    target_id: str
    protocol: str | None = None
    duration_ms: float | None = None
    status_code: int | None = None


@dataclass
class TransactionFlowVisualization:
    """Complete visualization data for a transaction flow."""

    transaction_id: str
    start_time: datetime
    end_time: datetime
    total_duration_ms: float
    nodes: list[FlowNode]
    edges: list[FlowEdge]
    status: str  # success, error, partial
    error_count: int
    warning_count: int
    source: str  # loki, azure_log_analytics, multi
    metadata: dict[str, Any] = field(default_factory=dict)


class TransactionFlowService:
    """Service for tracing and visualizing transaction flows."""

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        loki_url: str | None = None,
        prometheus_url: str | None = None,
        azure_workspace_id: str | None = None,
    ):
        """
        Initialize transaction flow service.

        Args:
            neo4j_client: Neo4j client for topology data
            loki_url: Loki server URL
            prometheus_url: Prometheus server URL
            azure_workspace_id: Azure Log Analytics workspace ID
        """
        self.neo4j_client = neo4j_client
        self.loki_url = loki_url
        self.prometheus_url = prometheus_url
        self.azure_workspace_id = azure_workspace_id

    async def trace_transaction(
        self, correlation_id: str, duration: timedelta = timedelta(hours=1), source: str = "auto"
    ) -> TransactionFlowVisualization | None:
        """
        Trace a transaction through the network.

        Args:
            correlation_id: Transaction/correlation ID to trace
            duration: Time range to search
            source: Data source to use (auto, loki, azure_log_analytics, all)

        Returns:
            TransactionFlowVisualization with complete flow data
        """
        if source == "auto":
            # Try Azure Log Analytics first, then Loki
            if self.azure_workspace_id:
                flow = await self._trace_via_azure(correlation_id, duration)
                if flow:
                    return flow

            if self.loki_url:
                flow = await self._trace_via_loki(correlation_id, duration)
                if flow:
                    return flow

        elif source == "azure_log_analytics" and self.azure_workspace_id:
            return await self._trace_via_azure(correlation_id, duration)

        elif source == "loki" and self.loki_url:
            return await self._trace_via_loki(correlation_id, duration)

        elif source == "all":
            # Combine data from all sources
            flows = []

            if self.azure_workspace_id:
                azure_flow = await self._trace_via_azure(correlation_id, duration)
                if azure_flow:
                    flows.append(azure_flow)

            if self.loki_url:
                loki_flow = await self._trace_via_loki(correlation_id, duration)
                if loki_flow:
                    flows.append(loki_flow)

            if flows:
                return self._merge_flows(flows, correlation_id)

        return None

    async def find_correlation_ids_for_pod(
        self, pod_resource_id: str, duration: timedelta = timedelta(hours=1), limit: int = 50
    ) -> list[str]:
        """
        Find correlation IDs in logs for a specific pod.

        Args:
            pod_resource_id: Pod resource ID
            duration: Time range to search
            limit: Maximum number of correlation IDs

        Returns:
            List of unique correlation IDs
        """
        correlation_ids = set()

        # Try Azure Log Analytics
        if self.azure_workspace_id:
            try:
                collector = AzureLogAnalyticsCollector(self.azure_workspace_id)
                try:
                    ids = await collector.find_correlation_ids_for_resource(
                        pod_resource_id, duration, limit
                    )
                    correlation_ids.update(ids)
                finally:
                    await collector.close()
            except Exception:
                pass

        # Try Loki
        if self.loki_url:
            try:
                collector = LokiCollector(self.loki_url)
                try:
                    ids = await collector.find_correlation_ids_for_resource(
                        pod_resource_id, duration, limit
                    )
                    correlation_ids.update(ids)
                finally:
                    await collector.close()
            except Exception:
                pass

        return list(correlation_ids)[:limit]

    async def get_flow_with_enrichment(
        self, correlation_id: str, duration: timedelta = timedelta(hours=1)
    ) -> TransactionFlowVisualization | None:
        """
        Get transaction flow with topology and metrics enrichment.

        Args:
            correlation_id: Transaction/correlation ID to trace
            duration: Time range to search

        Returns:
            Enriched TransactionFlowVisualization
        """
        # Get base flow
        flow = await self.trace_transaction(correlation_id, duration)
        if not flow:
            return None

        # Enrich with topology data
        flow = await self._enrich_with_topology(flow)

        # Enrich with metrics
        if self.prometheus_url:
            flow = await self._enrich_with_metrics(flow, duration)

        return flow

    async def _trace_via_azure(
        self, correlation_id: str, duration: timedelta
    ) -> TransactionFlowVisualization | None:
        """Trace transaction via Azure Log Analytics."""
        if not self.azure_workspace_id:
            return None

        collector = AzureLogAnalyticsCollector(self.azure_workspace_id)

        try:
            trace = await collector.trace_transaction_flow(correlation_id, duration)
            if not trace:
                return None

            # Convert to FlowNodes
            nodes = []
            resource_ids_seen = {}

            for i, entry in enumerate(trace.entries):
                if entry.resource_id not in resource_ids_seen:
                    node = FlowNode(
                        resource_id=entry.resource_id,
                        resource_name=self._extract_resource_name(entry.resource_id),
                        resource_type=self._infer_resource_type(entry.resource_id),
                        timestamp=entry.timestamp,
                        status="error" if entry.level in ("error", "critical") else "success",
                        log_entries=[entry],
                    )
                    nodes.append(node)
                    resource_ids_seen[entry.resource_id] = len(nodes) - 1
                else:
                    # Add log entry to existing node
                    idx = resource_ids_seen[entry.resource_id]
                    nodes[idx].log_entries.append(entry)
                    if entry.level in ("error", "critical"):
                        nodes[idx].status = "error"

            # Create edges based on sequence
            edges = []
            for i in range(len(nodes) - 1):
                edges.append(
                    FlowEdge(
                        source_id=nodes[i].resource_id,
                        target_id=nodes[i + 1].resource_id,
                    )
                )

            # Determine overall status
            status = "success"
            if trace.error_count > 0:
                status = "error"
            elif trace.warning_count > 0:
                status = "partial"

            return TransactionFlowVisualization(
                transaction_id=correlation_id,
                start_time=trace.start_time,
                end_time=trace.end_time,
                total_duration_ms=trace.duration_ms,
                nodes=nodes,
                edges=edges,
                status=status,
                error_count=trace.error_count,
                warning_count=trace.warning_count,
                source="azure_log_analytics",
                metadata={"resource_path": trace.resource_path},
            )
        finally:
            await collector.close()

    async def _trace_via_loki(
        self, correlation_id: str, duration: timedelta
    ) -> TransactionFlowVisualization | None:
        """Trace transaction via Loki."""
        if not self.loki_url:
            return None

        collector = LokiCollector(self.loki_url)

        try:
            streams = await collector.get_logs_by_correlation_id(correlation_id, duration)
            if not streams:
                return None

            # Flatten all entries
            all_entries = []
            for stream in streams:
                for entry in stream.entries:
                    # Add resource_id from labels
                    resource_id = stream.labels.get("resource_id", "") or stream.labels.get(
                        "pod", ""
                    )
                    all_entries.append((entry, resource_id))

            # Sort by timestamp
            all_entries.sort(key=lambda x: x[0].timestamp)

            if not all_entries:
                return None

            # Group into nodes by resource
            nodes = []
            resource_ids_seen = {}
            error_count = 0
            warning_count = 0

            for entry, resource_id in all_entries:
                if entry.level in ("error", "fatal"):
                    error_count += 1
                elif entry.level == "warn":
                    warning_count += 1

                if resource_id not in resource_ids_seen:
                    node = FlowNode(
                        resource_id=resource_id,
                        resource_name=(
                            resource_id.split("/")[-1] if "/" in resource_id else resource_id
                        ),
                        resource_type="pod",  # Default for Loki
                        timestamp=entry.timestamp,
                        status="error" if entry.level in ("error", "fatal") else "success",
                        log_entries=[entry],
                    )
                    nodes.append(node)
                    resource_ids_seen[resource_id] = len(nodes) - 1
                else:
                    idx = resource_ids_seen[resource_id]
                    nodes[idx].log_entries.append(entry)
                    if entry.level in ("error", "fatal"):
                        nodes[idx].status = "error"

            # Create edges
            edges = []
            for i in range(len(nodes) - 1):
                edges.append(
                    FlowEdge(
                        source_id=nodes[i].resource_id,
                        target_id=nodes[i + 1].resource_id,
                    )
                )

            # Calculate duration
            start_time = all_entries[0][0].timestamp
            end_time = all_entries[-1][0].timestamp
            duration_ms = (end_time - start_time).total_seconds() * 1000

            status = "success"
            if error_count > 0:
                status = "error"
            elif warning_count > 0:
                status = "partial"

            return TransactionFlowVisualization(
                transaction_id=correlation_id,
                start_time=start_time,
                end_time=end_time,
                total_duration_ms=duration_ms,
                nodes=nodes,
                edges=edges,
                status=status,
                error_count=error_count,
                warning_count=warning_count,
                source="loki",
            )
        finally:
            await collector.close()

    async def _enrich_with_topology(
        self, flow: TransactionFlowVisualization
    ) -> TransactionFlowVisualization:
        """Enrich flow with topology data from Neo4j."""
        # Query Neo4j for resource details
        with self.neo4j_client.driver.session() as session:
            for node in flow.nodes:
                result = session.run(
                    """
                    MATCH (r:Resource)
                    WHERE r.id = $resource_id OR r.name = $resource_id
                    RETURN r.name as name, r.resource_type as type, 
                           r.cloud_provider as provider
                    LIMIT 1
                    """,
                    resource_id=node.resource_id,
                )
                record = result.single()
                if record:
                    node.resource_name = record["name"] or node.resource_name
                    node.resource_type = record["type"] or node.resource_type
                    node.metadata["cloud_provider"] = record["provider"]

        # Query for actual edges in topology
        with self.neo4j_client.driver.session() as session:
            for edge in flow.edges:
                result = session.run(
                    """
                    MATCH (a:Resource)-[r]->(b:Resource)
                    WHERE (a.id = $source_id OR a.name = $source_id)
                      AND (b.id = $target_id OR b.name = $target_id)
                    RETURN type(r) as rel_type, r.protocol as protocol
                    LIMIT 1
                    """,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                )
                record = result.single()
                if record:
                    edge.protocol = record["protocol"]

        return flow

    async def _enrich_with_metrics(
        self, flow: TransactionFlowVisualization, duration: timedelta
    ) -> TransactionFlowVisualization:
        """Enrich flow with metrics from Prometheus."""
        if not self.prometheus_url:
            return flow

        collector = PrometheusCollector(self.prometheus_url)

        try:
            for node in flow.nodes:
                try:
                    metrics = await collector.get_resource_metrics(
                        resource_id=node.resource_id,
                        resource_type=node.resource_type,
                        duration=duration,
                    )
                    node.metrics = {
                        "health_score": metrics.health_score,
                        "anomalies": metrics.anomalies,
                    }
                except Exception:
                    pass
        finally:
            await collector.close()

        return flow

    def _merge_flows(
        self, flows: list[TransactionFlowVisualization], correlation_id: str
    ) -> TransactionFlowVisualization:
        """Merge multiple flows from different sources."""
        if not flows:
            return None

        if len(flows) == 1:
            return flows[0]

        # Merge nodes and edges
        all_nodes = []
        all_edges = []
        resource_ids_seen = set()

        for flow in flows:
            for node in flow.nodes:
                if node.resource_id not in resource_ids_seen:
                    all_nodes.append(node)
                    resource_ids_seen.add(node.resource_id)

            all_edges.extend(flow.edges)

        # Sort nodes by timestamp
        all_nodes.sort(key=lambda n: n.timestamp)

        # Remove duplicate edges
        edge_set = set()
        unique_edges = []
        for edge in all_edges:
            edge_key = (edge.source_id, edge.target_id)
            if edge_key not in edge_set:
                unique_edges.append(edge)
                edge_set.add(edge_key)

        # Aggregate metrics
        start_time = min(f.start_time for f in flows)
        end_time = max(f.end_time for f in flows)
        total_duration = (end_time - start_time).total_seconds() * 1000
        error_count = sum(f.error_count for f in flows)
        warning_count = sum(f.warning_count for f in flows)

        status = "success"
        if error_count > 0:
            status = "error"
        elif warning_count > 0:
            status = "partial"

        return TransactionFlowVisualization(
            transaction_id=correlation_id,
            start_time=start_time,
            end_time=end_time,
            total_duration_ms=total_duration,
            nodes=all_nodes,
            edges=unique_edges,
            status=status,
            error_count=error_count,
            warning_count=warning_count,
            source="multi",
        )

    def _extract_resource_name(self, resource_id: str) -> str:
        """Extract resource name from Azure resource ID."""
        if "/" in resource_id:
            return resource_id.split("/")[-1]
        return resource_id

    def _infer_resource_type(self, resource_id: str) -> str:
        """Infer resource type from Azure resource ID."""
        resource_id_lower = resource_id.lower()

        if "/pods/" in resource_id_lower or "/microsoft.containerservice/" in resource_id_lower:
            return "pod"
        elif "/sites/" in resource_id_lower or "/microsoft.web/" in resource_id_lower:
            return "app_service"
        elif "/loadbalancers/" in resource_id_lower:
            return "load_balancer"
        elif "/applicationgateways/" in resource_id_lower:
            return "application_gateway"
        elif "/databases/" in resource_id_lower or "/sqlservers/" in resource_id_lower:
            return "database"
        elif "/storageaccounts/" in resource_id_lower:
            return "storage_account"
        else:
            return "service"
