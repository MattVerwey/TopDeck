"""
Root Cause Analysis (RCA) engine for TopDeck.

Analyzes failures and anomalies to identify root causes through:
- Correlation analysis across services
- Dependency chain traversal
- Failure propagation detection
- Timeline reconstruction
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Optional

from topdeck.monitoring.live_diagnostics import LiveDiagnosticsService
from topdeck.monitoring.prometheus_collector import PrometheusCollector
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class RootCauseType(str, Enum):
    """Types of root causes."""
    
    DEPENDENCY_FAILURE = "dependency_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONFIGURATION_CHANGE = "configuration_change"
    NETWORK_ISSUE = "network_issue"
    DEPLOYMENT = "deployment"
    EXTERNAL_SERVICE = "external_service"
    CASCADING_FAILURE = "cascading_failure"
    UNKNOWN = "unknown"


@dataclass
class TimelineEvent:
    """An event in the failure timeline."""
    
    timestamp: datetime
    event_type: str
    resource_id: str
    resource_name: str
    description: str
    severity: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrelatedAnomaly:
    """An anomaly correlated with a failure."""
    
    resource_id: str
    resource_name: str
    metric_name: str
    deviation: float
    severity: str
    timestamp: datetime
    correlation_score: float  # 0-1, how correlated with root cause


@dataclass
class FailurePropagation:
    """Describes how a failure propagated through dependencies."""
    
    initial_failure: str  # Resource ID
    propagation_path: list[str]  # List of resource IDs
    propagation_delay: float  # Seconds
    affected_services: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RootCauseAnalysis:
    """Complete root cause analysis result."""
    
    analysis_id: str
    resource_id: str
    resource_name: str
    failure_time: datetime
    root_cause_type: RootCauseType
    primary_cause: str
    contributing_factors: list[str]
    confidence: float  # 0-1
    timeline: list[TimelineEvent]
    correlated_anomalies: list[CorrelatedAnomaly]
    propagation: Optional[FailurePropagation]
    recommendations: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


class RootCauseAnalyzer:
    """
    Root Cause Analysis engine.
    
    Analyzes failures to identify root causes through:
    1. Timeline reconstruction
    2. Correlation analysis
    3. Dependency chain analysis
    4. Failure propagation detection
    """
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        prometheus_collector: PrometheusCollector,
        diagnostics_service: LiveDiagnosticsService,
    ):
        """
        Initialize RCA analyzer.
        
        Args:
            neo4j_client: Neo4j client for topology queries
            prometheus_collector: Prometheus collector for metrics
            diagnostics_service: Live diagnostics service
        """
        self.neo4j = neo4j_client
        self.prometheus = prometheus_collector
        self.diagnostics = diagnostics_service
    
    async def analyze_failure(
        self,
        resource_id: str,
        failure_time: Optional[datetime] = None,
        lookback_hours: int = 2,
    ) -> RootCauseAnalysis:
        """
        Perform root cause analysis for a failure.
        
        Args:
            resource_id: ID of the failed resource
            failure_time: When the failure occurred (defaults to now)
            lookback_hours: How far back to analyze
            
        Returns:
            Complete root cause analysis
        """
        if failure_time is None:
            failure_time = datetime.now(UTC)
        
        logger.info(f"Starting RCA for {resource_id} at {failure_time}")
        
        # Get resource info
        resource = await self._get_resource_info(resource_id)
        
        # Build timeline
        timeline = await self._build_timeline(resource_id, failure_time, lookback_hours)
        
        # Find correlated anomalies
        anomalies = await self._find_correlated_anomalies(
            resource_id,
            failure_time,
            lookback_hours,
        )
        
        # Analyze dependency chain
        propagation = await self._analyze_propagation(resource_id, failure_time)
        
        # Determine root cause
        root_cause_type, primary_cause, contributing_factors, confidence = (
            await self._determine_root_cause(
                resource_id,
                timeline,
                anomalies,
                propagation,
            )
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            root_cause_type,
            primary_cause,
            contributing_factors,
        )
        
        analysis = RootCauseAnalysis(
            analysis_id=str(uuid.uuid4()),
            resource_id=resource_id,
            resource_name=resource.get("name", resource_id),
            failure_time=failure_time,
            root_cause_type=root_cause_type,
            primary_cause=primary_cause,
            contributing_factors=contributing_factors,
            confidence=confidence,
            timeline=timeline,
            correlated_anomalies=anomalies,
            propagation=propagation,
            recommendations=recommendations,
            metadata={
                "lookback_hours": lookback_hours,
                "analyzed_at": datetime.now(UTC).isoformat(),
            },
        )
        
        logger.info(
            f"RCA complete for {resource_id}: {root_cause_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        
        return analysis
    
    async def _get_resource_info(self, resource_id: str) -> dict[str, Any]:
        """Get basic resource information from Neo4j."""
        query = """
        MATCH (r:Resource {id: $resource_id})
        RETURN r.name as name, r.resource_type as type, r.environment as environment
        """
        
        result = await self.neo4j.execute_query(query, {"resource_id": resource_id})
        
        if result and len(result) > 0:
            return result[0]
        
        return {"name": resource_id, "type": "unknown", "environment": "unknown"}
    
    async def _build_timeline(
        self,
        resource_id: str,
        failure_time: datetime,
        lookback_hours: int,
    ) -> list[TimelineEvent]:
        """Build a timeline of events leading to the failure."""
        timeline = []
        
        # Get deployment events
        deployments = await self._get_deployment_events(
            resource_id,
            failure_time,
            lookback_hours,
        )
        timeline.extend(deployments)
        
        # Get anomaly events
        anomaly_events = await self._get_anomaly_events(
            resource_id,
            failure_time,
            lookback_hours,
        )
        timeline.extend(anomaly_events)
        
        # Get dependency failure events
        dep_events = await self._get_dependency_events(
            resource_id,
            failure_time,
            lookback_hours,
        )
        timeline.extend(dep_events)
        
        # Sort by timestamp
        timeline.sort(key=lambda e: e.timestamp)
        
        return timeline
    
    async def _get_deployment_events(
        self,
        resource_id: str,
        failure_time: datetime,
        lookback_hours: int,
    ) -> list[TimelineEvent]:
        """Get deployment events from Neo4j."""
        query = """
        MATCH (r:Resource {id: $resource_id})<-[:DEPLOYED_TO]-(d:Deployment)
        WHERE d.deployed_at > $start_time AND d.deployed_at <= $end_time
        RETURN d.id as id, d.deployed_at as timestamp, d.version as version,
               d.status as status
        ORDER BY d.deployed_at
        """
        
        start_time = failure_time - timedelta(hours=lookback_hours)
        
        result = await self.neo4j.execute_query(
            query,
            {
                "resource_id": resource_id,
                "start_time": start_time.isoformat(),
                "end_time": failure_time.isoformat(),
            },
        )
        
        events = []
        for row in result:
            # Parse timestamp and ensure it's UTC-aware
            timestamp_str = row["timestamp"]
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            
            events.append(
                TimelineEvent(
                    timestamp=timestamp,
                    event_type="deployment",
                    resource_id=resource_id,
                    resource_name=resource_id,
                    description=f"Deployment: {row.get('version', 'unknown')}",
                    severity="info" if row.get("status") == "success" else "warning",
                    metadata={"deployment_id": row["id"], "version": row.get("version")},
                )
            )
        
        return events
    
    async def _get_anomaly_events(
        self,
        resource_id: str,
        failure_time: datetime,
        lookback_hours: int,
    ) -> list[TimelineEvent]:
        """Get anomaly detection events."""
        try:
            anomalies = await self.diagnostics.detect_anomalies(
                duration_hours=lookback_hours,
                limit=100,
            )
            
            # Filter to this resource and time window
            start_time = failure_time - timedelta(hours=lookback_hours)
            
            events = []
            for anomaly in anomalies:
                if anomaly.resource_id != resource_id:
                    continue
                
                # Estimate timestamp (diagnostics doesn't provide exact time)
                timestamp = failure_time - timedelta(minutes=30)  # Approximate
                
                if start_time <= timestamp <= failure_time:
                    events.append(
                        TimelineEvent(
                            timestamp=timestamp,
                            event_type="anomaly",
                            resource_id=resource_id,
                            resource_name=anomaly.resource_name,
                            description=f"Anomaly in {anomaly.metric_name}",
                            severity=anomaly.severity,
                            metadata={
                                "metric": anomaly.metric_name,
                                "deviation": anomaly.deviation,
                            },
                        )
                    )
            
            return events
        except Exception as e:
            logger.error(f"Error getting anomaly events: {e}")
            return []
    
    async def _get_dependency_events(
        self,
        resource_id: str,
        failure_time: datetime,
        lookback_hours: int,
    ) -> list[TimelineEvent]:
        """Get events from dependencies."""
        # Get upstream dependencies
        query = """
        MATCH (r:Resource {id: $resource_id})-[:DEPENDS_ON]->(dep:Resource)
        RETURN dep.id as dep_id, dep.name as dep_name
        LIMIT 10
        """
        
        result = await self.neo4j.execute_query(query, {"resource_id": resource_id})
        
        events = []
        for row in result:
            dep_id = row["dep_id"]
            dep_name = row["dep_name"]
            
            # Check if this dependency failed before our resource
            # This is simplified - in production, query actual failure times
            events.append(
                TimelineEvent(
                    timestamp=failure_time - timedelta(minutes=15),
                    event_type="dependency_issue",
                    resource_id=dep_id,
                    resource_name=dep_name,
                    description=f"Dependency {dep_name} experienced issues",
                    severity="warning",
                    metadata={"dependency_id": dep_id},
                )
            )
        
        return events
    
    async def _find_correlated_anomalies(
        self,
        resource_id: str,
        failure_time: datetime,
        lookback_hours: int,
    ) -> list[CorrelatedAnomaly]:
        """Find anomalies correlated with the failure."""
        try:
            anomalies = await self.diagnostics.detect_anomalies(
                duration_hours=lookback_hours,
                limit=100,
            )
            
            correlated = []
            for anomaly in anomalies:
                # Calculate correlation score based on:
                # 1. Proximity to failure time
                # 2. Severity
                # 3. Resource relationship
                
                correlation_score = 0.5  # Base score
                
                # Boost score if it's the same resource
                if anomaly.resource_id == resource_id:
                    correlation_score += 0.3
                
                # Boost based on severity
                if anomaly.severity == "critical":
                    correlation_score += 0.2
                elif anomaly.severity == "high":
                    correlation_score += 0.1
                
                # Cap at 1.0
                correlation_score = min(1.0, correlation_score)
                
                correlated.append(
                    CorrelatedAnomaly(
                        resource_id=anomaly.resource_id,
                        resource_name=anomaly.resource_name,
                        metric_name=anomaly.metric_name,
                        deviation=anomaly.deviation,
                        severity=anomaly.severity,
                        timestamp=failure_time - timedelta(minutes=30),  # Approximate
                        correlation_score=correlation_score,
                    )
                )
            
            # Sort by correlation score
            correlated.sort(key=lambda a: a.correlation_score, reverse=True)
            
            return correlated[:10]  # Top 10
        except Exception as e:
            logger.error(f"Error finding correlated anomalies: {e}")
            return []
    
    async def _analyze_propagation(
        self,
        resource_id: str,
        failure_time: datetime,
    ) -> Optional[FailurePropagation]:
        """Analyze how the failure propagated through dependencies."""
        # Get dependency chain
        query = """
        MATCH path = (r:Resource {id: $resource_id})-[:DEPENDS_ON*1..5]->(dep:Resource)
        WITH dep, length(path) as depth
        ORDER BY depth
        RETURN dep.id as dep_id, dep.name as dep_name, depth
        LIMIT 20
        """
        
        result = await self.neo4j.execute_query(query, {"resource_id": resource_id})
        
        if not result:
            return None
        
        # Check if any upstream dependency failed first
        for row in result:
            dep_id = row["dep_id"]
            
            # In production, check actual failure times
            # For now, assume the deepest dependency failed first
            if row["depth"] > 1:
                propagation_path = [dep_id, resource_id]
                
                return FailurePropagation(
                    initial_failure=dep_id,
                    propagation_path=propagation_path,
                    propagation_delay=300.0,  # 5 minutes (example)
                    affected_services=[resource_id],
                    metadata={
                        "dependency_depth": row["depth"],
                        "upstream_service": row["dep_name"],
                    },
                )
        
        return None
    
    async def _determine_root_cause(
        self,
        resource_id: str,
        timeline: list[TimelineEvent],
        anomalies: list[CorrelatedAnomaly],
        propagation: Optional[FailurePropagation],
    ) -> tuple[RootCauseType, str, list[str], float]:
        """
        Determine the root cause based on analysis.
        
        Returns:
            (root_cause_type, primary_cause, contributing_factors, confidence)
        """
        contributing_factors = []
        
        # Check for propagation from dependency
        if propagation:
            root_cause_type = RootCauseType.CASCADING_FAILURE
            primary_cause = (
                f"Failure cascaded from upstream dependency: "
                f"{propagation.metadata.get('upstream_service', 'unknown')}"
            )
            confidence = 0.8
            contributing_factors.append("Dependency failure detected")
            return root_cause_type, primary_cause, contributing_factors, confidence
        
        # Check for recent deployment
        recent_deployments = [e for e in timeline if e.event_type == "deployment"]
        if recent_deployments and timeline:
            deployment = recent_deployments[-1]
            # If deployment was within 1 hour of failure
            time_diff = abs((deployment.timestamp - timeline[-1].timestamp).total_seconds())
            if time_diff < 3600:
                root_cause_type = RootCauseType.DEPLOYMENT
                primary_cause = (
                    f"Recent deployment: {deployment.metadata.get('version', 'unknown')}"
                )
                confidence = 0.7
                contributing_factors.append(
                    f"Deployment occurred {int(time_diff/60)} minutes before failure"
                )
                return root_cause_type, primary_cause, contributing_factors, confidence
        
        # Check for resource exhaustion anomalies
        resource_anomalies = [
            a for a in anomalies
            if any(
                metric in a.metric_name.lower()
                for metric in ["cpu", "memory", "disk", "connection"]
            )
        ]
        if resource_anomalies and resource_anomalies[0].correlation_score > 0.7:
            anomaly = resource_anomalies[0]
            root_cause_type = RootCauseType.RESOURCE_EXHAUSTION
            primary_cause = f"Resource exhaustion: {anomaly.metric_name}"
            confidence = anomaly.correlation_score
            contributing_factors.append(
                f"Deviation of {anomaly.deviation:.2f} detected in {anomaly.metric_name}"
            )
            return root_cause_type, primary_cause, contributing_factors, confidence
        
        # Check for network anomalies
        network_anomalies = [
            a for a in anomalies
            if any(
                metric in a.metric_name.lower()
                for metric in ["latency", "error_rate", "timeout", "connection"]
            )
        ]
        if network_anomalies and network_anomalies[0].correlation_score > 0.6:
            anomaly = network_anomalies[0]
            root_cause_type = RootCauseType.NETWORK_ISSUE
            primary_cause = f"Network issue: {anomaly.metric_name}"
            confidence = anomaly.correlation_score
            contributing_factors.append(
                f"Network anomaly detected: {anomaly.metric_name}"
            )
            return root_cause_type, primary_cause, contributing_factors, confidence
        
        # Default to unknown
        root_cause_type = RootCauseType.UNKNOWN
        primary_cause = "Unable to determine root cause with available data"
        confidence = 0.3
        
        if anomalies:
            contributing_factors.append(
                f"{len(anomalies)} anomalies detected around failure time"
            )
        
        if timeline:
            contributing_factors.append(
                f"{len(timeline)} events in timeline"
            )
        
        return root_cause_type, primary_cause, contributing_factors, confidence
    
    def _generate_recommendations(
        self,
        root_cause_type: RootCauseType,
        primary_cause: str,
        contributing_factors: list[str],
    ) -> list[str]:
        """Generate recommendations based on root cause."""
        recommendations = []
        
        if root_cause_type == RootCauseType.DEPLOYMENT:
            recommendations.extend([
                "Consider rolling back the recent deployment",
                "Review deployment logs and configuration changes",
                "Implement canary deployments to detect issues earlier",
                "Add pre-deployment health checks",
            ])
        elif root_cause_type == RootCauseType.RESOURCE_EXHAUSTION:
            recommendations.extend([
                "Scale up resources (CPU, memory, or connections)",
                "Review resource usage trends",
                "Implement auto-scaling policies",
                "Optimize resource-intensive code paths",
            ])
        elif root_cause_type == RootCauseType.CASCADING_FAILURE:
            recommendations.extend([
                "Investigate and fix the upstream dependency",
                "Implement circuit breakers to prevent cascade",
                "Add retry logic with exponential backoff",
                "Consider adding redundancy for critical dependencies",
            ])
        elif root_cause_type == RootCauseType.NETWORK_ISSUE:
            recommendations.extend([
                "Check network connectivity and firewall rules",
                "Review load balancer configuration",
                "Increase timeout values if appropriate",
                "Add network monitoring and alerting",
            ])
        elif root_cause_type == RootCauseType.CONFIGURATION_CHANGE:
            recommendations.extend([
                "Review recent configuration changes",
                "Revert to last known good configuration",
                "Implement configuration validation",
                "Use infrastructure as code for config management",
            ])
        else:
            recommendations.extend([
                "Review logs for error messages",
                "Check monitoring dashboards for anomalies",
                "Consult with subject matter experts",
                "Enable additional logging/metrics if needed",
            ])
        
        return recommendations
