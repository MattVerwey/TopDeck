"""
SPOF (Single Point of Failure) Monitoring Service.

Provides continuous monitoring of single points of failure in the infrastructure,
tracking changes over time and exposing metrics for alerting.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from prometheus_client import Counter, Gauge

from topdeck.analysis.risk import RiskAnalyzer
from topdeck.analysis.risk.models import SinglePointOfFailure
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


# Prometheus metrics for SPOF monitoring
spof_total = Gauge(
    "topdeck_spof_total",
    "Total number of single points of failure detected",
)

spof_by_type = Gauge(
    "topdeck_spof_by_type",
    "Number of SPOFs by resource type",
    ["resource_type"],
)

spof_high_risk = Gauge(
    "topdeck_spof_high_risk",
    "Number of high-risk SPOFs (risk score > 80)",
)

spof_changes = Counter(
    "topdeck_spof_changes_total",
    "Total number of SPOF state changes",
    ["change_type"],  # new, resolved
)


@dataclass
class SPOFSnapshot:
    """
    Snapshot of SPOF state at a point in time.
    
    Attributes:
        timestamp: When this snapshot was taken
        spofs: List of detected SPOFs
        total_count: Total number of SPOFs
        high_risk_count: Number of high-risk SPOFs (risk score > 80)
        by_resource_type: Count by resource type
    """

    timestamp: datetime
    spofs: list[SinglePointOfFailure]
    total_count: int
    high_risk_count: int
    by_resource_type: dict[str, int] = field(default_factory=dict)


@dataclass
class SPOFChange:
    """
    Represents a change in SPOF state.
    
    Attributes:
        change_type: Type of change (new, resolved)
        resource_id: Resource that changed
        resource_name: Name of the resource
        resource_type: Type of resource
        detected_at: When the change was detected
        risk_score: Risk score of the SPOF
        blast_radius: Blast radius if this fails
    """

    change_type: str  # "new" or "resolved"
    resource_id: str
    resource_name: str
    resource_type: str
    detected_at: datetime
    risk_score: float
    blast_radius: int


class SPOFMonitor:
    """
    Monitors single points of failure across the infrastructure.
    
    Tracks SPOF changes over time, stores history, and exports metrics
    for alerting and trending.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize SPOF monitor.
        
        Args:
            neo4j_client: Neo4j client for graph database access
        """
        self.neo4j_client = neo4j_client
        self.risk_analyzer = RiskAnalyzer(neo4j_client)
        self.last_snapshot: SPOFSnapshot | None = None
        self.changes: list[SPOFChange] = []

    def scan(self) -> SPOFSnapshot:
        """
        Perform a SPOF scan across all infrastructure.
        
        Returns:
            SPOFSnapshot with current SPOF state
        """
        logger.info("Starting SPOF scan...")
        
        # Get all current SPOFs from risk analyzer
        spofs = self.risk_analyzer.identify_single_points_of_failure()
        
        # Calculate statistics
        total_count = len(spofs)
        high_risk_count = sum(1 for spof in spofs if spof.risk_score > 80)
        
        # Count by resource type
        by_resource_type: dict[str, int] = {}
        for spof in spofs:
            resource_type = spof.resource_type
            by_resource_type[resource_type] = by_resource_type.get(resource_type, 0) + 1
        
        snapshot = SPOFSnapshot(
            timestamp=datetime.now(UTC),
            spofs=spofs,
            total_count=total_count,
            high_risk_count=high_risk_count,
            by_resource_type=by_resource_type,
        )
        
        # Detect changes if we have a previous snapshot
        if self.last_snapshot:
            self._detect_changes(self.last_snapshot, snapshot)
        
        # Update metrics
        self._update_metrics(snapshot)
        
        # Store snapshot
        self.last_snapshot = snapshot
        
        logger.info(
            f"SPOF scan complete: {total_count} total, "
            f"{high_risk_count} high-risk"
        )
        
        return snapshot

    def _detect_changes(
        self, previous: SPOFSnapshot, current: SPOFSnapshot
    ) -> list[SPOFChange]:
        """
        Detect changes between two snapshots.
        
        Args:
            previous: Previous SPOF snapshot
            current: Current SPOF snapshot
            
        Returns:
            List of detected changes
        """
        changes: list[SPOFChange] = []
        
        # Create sets of resource IDs for comparison
        previous_ids = {spof.resource_id for spof in previous.spofs}
        current_ids = {spof.resource_id for spof in current.spofs}
        
        # Find new SPOFs
        new_spof_ids = current_ids - previous_ids
        for spof in current.spofs:
            if spof.resource_id in new_spof_ids:
                change = SPOFChange(
                    change_type="new",
                    resource_id=spof.resource_id,
                    resource_name=spof.resource_name,
                    resource_type=spof.resource_type,
                    detected_at=current.timestamp,
                    risk_score=spof.risk_score,
                    blast_radius=spof.blast_radius,
                )
                changes.append(change)
                spof_changes.labels(change_type="new").inc()
                logger.warning(
                    f"New SPOF detected: {spof.resource_name} "
                    f"({spof.resource_type}, risk: {spof.risk_score:.1f})"
                )
        
        # Find resolved SPOFs
        resolved_ids = previous_ids - current_ids
        for spof in previous.spofs:
            if spof.resource_id in resolved_ids:
                change = SPOFChange(
                    change_type="resolved",
                    resource_id=spof.resource_id,
                    resource_name=spof.resource_name,
                    resource_type=spof.resource_type,
                    detected_at=current.timestamp,
                    risk_score=spof.risk_score,
                    blast_radius=spof.blast_radius,
                )
                changes.append(change)
                spof_changes.labels(change_type="resolved").inc()
                logger.info(
                    f"SPOF resolved: {spof.resource_name} ({spof.resource_type})"
                )
        
        self.changes.extend(changes)
        return changes

    def _update_metrics(self, snapshot: SPOFSnapshot) -> None:
        """
        Update Prometheus metrics from snapshot.
        
        Args:
            snapshot: SPOF snapshot to export
        """
        # Update total SPOF count
        spof_total.set(snapshot.total_count)
        
        # Update high-risk SPOF count
        spof_high_risk.set(snapshot.high_risk_count)
        
        # Update counts by resource type
        # Note: Prometheus collectors automatically handle label removal
        # We only need to set current values
        for resource_type, count in snapshot.by_resource_type.items():
            spof_by_type.labels(resource_type=resource_type).set(count)

    def get_current_spofs(self) -> list[dict[str, Any]]:
        """
        Get current SPOF state.
        
        Returns:
            List of current SPOFs as dictionaries
        """
        if not self.last_snapshot:
            return []
        
        return [
            {
                "resource_id": spof.resource_id,
                "resource_name": spof.resource_name,
                "resource_type": spof.resource_type,
                "dependents_count": spof.dependents_count,
                "blast_radius": spof.blast_radius,
                "risk_score": spof.risk_score,
                "recommendations": spof.recommendations,
            }
            for spof in self.last_snapshot.spofs
        ]

    def get_recent_changes(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get recent SPOF changes.
        
        Args:
            limit: Maximum number of changes to return (default: 50)
            
        Returns:
            List of recent changes as dictionaries
        """
        recent_changes = self.changes[-limit:] if limit > 0 else []
        
        return [
            {
                "change_type": change.change_type,
                "resource_id": change.resource_id,
                "resource_name": change.resource_name,
                "resource_type": change.resource_type,
                "detected_at": change.detected_at.isoformat(),
                "risk_score": change.risk_score,
                "blast_radius": change.blast_radius,
            }
            for change in reversed(recent_changes)
        ]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get SPOF monitoring statistics.
        
        Returns:
            Dictionary with monitoring statistics
        """
        if not self.last_snapshot:
            return {
                "status": "not_scanned",
                "message": "No SPOF scan has been performed yet",
            }
        
        return {
            "status": "active",
            "last_scan": self.last_snapshot.timestamp.isoformat(),
            "total_spofs": self.last_snapshot.total_count,
            "high_risk_spofs": self.last_snapshot.high_risk_count,
            "by_resource_type": self.last_snapshot.by_resource_type,
            "total_changes": len(self.changes),
            "recent_changes": {
                "new": len([c for c in self.changes[-100:] if c.change_type == "new"]),
                "resolved": len([c for c in self.changes[-100:] if c.change_type == "resolved"]),
            },
        }
