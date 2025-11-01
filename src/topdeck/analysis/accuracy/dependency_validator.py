"""
Validate dependency detection accuracy.
"""

from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

from topdeck.storage.neo4j_client import Neo4jClient
from .models import (
    AccuracyMetrics,
    DependencyValidation,
    ValidationResult,
    ValidationStatus,
)

logger = structlog.get_logger(__name__)


class DependencyValidator:
    """
    Validates accuracy of dependency detection.
    
    Cross-validates dependencies from multiple sources and tracks accuracy
    over time to improve confidence scoring.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize dependency validator.
        
        Args:
            neo4j_client: Neo4j client for storage
        """
        self.neo4j = neo4j_client

    async def cross_validate_dependency(
        self, source_id: str, target_id: str
    ) -> DependencyValidation:
        """
        Cross-validate a dependency using multiple evidence sources.
        
        Args:
            source_id: Source resource
            target_id: Target resource
            
        Returns:
            DependencyValidation with validation status
        """
        # Get all evidence for this dependency
        query = """
        MATCH (s:Resource {id: $source_id})-[r:DEPENDS_ON]->(t:Resource {id: $target_id})
        RETURN r.confidence as confidence,
               r.evidence_sources as evidence_sources,
               r.detected_at as detected_at,
               r.last_seen as last_seen
        """
        
        result = await self.neo4j.execute_query(
            query, {"source_id": source_id, "target_id": target_id}
        )
        
        if not result:
            return DependencyValidation(
                source_id=source_id,
                target_id=target_id,
                detected_confidence=0.0,
                evidence_sources=[],
                validation_status=ValidationStatus.PENDING,
                validated_at=None,
                is_correct=None,
            )
        
        dependency = result[0]
        confidence = dependency.get("confidence", 0.0)
        evidence_sources = dependency.get("evidence_sources", [])
        last_seen = dependency.get("last_seen")
        
        # Determine validation status based on evidence
        validation_status = self._determine_validation_status(
            evidence_sources, last_seen
        )
        
        # Determine correctness based on multiple evidence sources
        is_correct = self._determine_correctness(evidence_sources, confidence)
        
        validated_at = datetime.now(timezone.utc)
        
        return DependencyValidation(
            source_id=source_id,
            target_id=target_id,
            detected_confidence=confidence,
            evidence_sources=evidence_sources,
            validation_status=validation_status,
            validated_at=validated_at,
            is_correct=is_correct,
            validation_method="cross_validation",
        )

    def _determine_validation_status(
        self, evidence_sources: list[str], last_seen: str | None
    ) -> ValidationStatus:
        """Determine validation status based on evidence recency."""
        if not evidence_sources:
            return ValidationStatus.PENDING
        
        if last_seen:
            last_seen_dt = datetime.fromisoformat(last_seen)
            age = datetime.now(timezone.utc) - last_seen_dt
            
            # If dependency hasn't been seen in 7 days, mark as expired
            if age > timedelta(days=7):
                return ValidationStatus.EXPIRED
        
        # Multiple evidence sources = validated
        if len(evidence_sources) >= 2:
            return ValidationStatus.VALIDATED
        
        return ValidationStatus.PENDING

    def _determine_correctness(
        self, evidence_sources: list[str], confidence: float
    ) -> bool | None:
        """
        Determine if dependency is correct based on evidence.
        
        Multiple evidence sources and high confidence = correct
        Single source with low confidence = uncertain (None)
        """
        if len(evidence_sources) >= 3 and confidence >= 0.8:
            return True  # High confidence with multiple sources
        elif len(evidence_sources) >= 2 and confidence >= 0.6:
            return True  # Good confidence with 2+ sources
        elif len(evidence_sources) == 1 and confidence < 0.4:
            return False  # Low confidence single source likely false positive
        else:
            return None  # Uncertain

    async def validate_stale_dependencies(
        self, max_age_days: int = 7
    ) -> list[DependencyValidation]:
        """
        Check for stale dependencies that need revalidation.
        
        Dependencies that haven't been confirmed in max_age_days should be
        marked for revalidation or removed.
        
        Args:
            max_age_days: Maximum age before considering stale
            
        Returns:
            List of stale dependencies
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        
        query = """
        MATCH (s:Resource)-[r:DEPENDS_ON]->(t:Resource)
        WHERE datetime(r.last_seen) < datetime($cutoff)
        RETURN s.id as source_id,
               t.id as target_id,
               r.confidence as confidence,
               r.evidence_sources as evidence_sources,
               r.last_seen as last_seen
        """
        
        results = await self.neo4j.execute_query(
            query, {"cutoff": cutoff.isoformat()}
        )
        
        stale_deps = []
        for row in results:
            validation = DependencyValidation(
                source_id=row["source_id"],
                target_id=row["target_id"],
                detected_confidence=row.get("confidence", 0.0),
                evidence_sources=row.get("evidence_sources", []),
                validation_status=ValidationStatus.EXPIRED,
                validated_at=datetime.now(timezone.utc),
                is_correct=False,  # Assume stale = incorrect
                validation_method="staleness_check",
                notes=f"Not seen since {row.get('last_seen')}",
            )
            stale_deps.append(validation)
        
        logger.info("identified_stale_dependencies", count=len(stale_deps))
        
        return stale_deps

    async def apply_confidence_decay(
        self, decay_rate: float = 0.1, days_threshold: int = 3
    ) -> int:
        """
        Apply confidence decay to dependencies not recently confirmed.
        
        Reduces confidence for dependencies that haven't been seen recently,
        reflecting uncertainty about their current state.
        
        Args:
            decay_rate: Rate to decay confidence (0.0-1.0)
            days_threshold: Days before starting decay
            
        Returns:
            Number of dependencies updated
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        
        query = """
        MATCH (s:Resource)-[r:DEPENDS_ON]->(t:Resource)
        WHERE datetime(r.last_seen) < datetime($cutoff)
          AND r.confidence > 0.0
        SET r.confidence = r.confidence * (1.0 - $decay_rate),
            r.confidence_decayed_at = datetime()
        RETURN count(r) as updated_count
        """
        
        result = await self.neo4j.execute_query(
            query, {"cutoff": cutoff.isoformat(), "decay_rate": decay_rate}
        )
        
        updated_count = result[0]["updated_count"] if result else 0
        
        logger.info(
            "applied_confidence_decay",
            updated_count=updated_count,
            decay_rate=decay_rate,
            days_threshold=days_threshold,
        )
        
        return updated_count

    async def get_dependency_accuracy_metrics(
        self, time_range_days: int = 30
    ) -> ValidationResult:
        """
        Calculate accuracy metrics for dependency detection.
        
        Args:
            time_range_days: Time range for analysis
            
        Returns:
            ValidationResult with accuracy metrics
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_range_days)
        
        # Count dependencies by validation status
        query = """
        MATCH (s:Resource)-[r:DEPENDS_ON]->(t:Resource)
        WHERE datetime(r.detected_at) >= datetime($cutoff)
        RETURN 
            CASE
                WHEN size(r.evidence_sources) >= 2 THEN 'validated'
                WHEN datetime(r.last_seen) < datetime($stale_cutoff) THEN 'stale'
                ELSE 'pending'
            END as status,
            count(*) as count,
            avg(r.confidence) as avg_confidence
        """
        
        stale_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        results = await self.neo4j.execute_query(
            query,
            {
                "cutoff": cutoff.isoformat(),
                "stale_cutoff": stale_cutoff.isoformat(),
            },
        )
        
        # Parse results
        validated_count = 0
        pending_count = 0
        stale_count = 0
        
        for row in results:
            status = row["status"]
            count = row["count"]
            
            if status == "validated":
                validated_count = count
            elif status == "pending":
                pending_count = count
            elif status == "stale":
                stale_count = count
        
        total = validated_count + pending_count + stale_count
        
        # Calculate accuracy metrics
        # For dependencies: validated = TP, stale = FP, pending = uncertain
        metrics = AccuracyMetrics.from_counts(
            true_positives=validated_count,  # Multiple evidence sources
            true_negatives=0,  # Hard to measure for dependencies
            false_positives=stale_count,  # Stale dependencies
            false_negatives=0,  # Hard to measure (unknown dependencies)
        )
        
        return ValidationResult(
            metrics=metrics,
            validated_count=validated_count,
            pending_count=pending_count,
            time_range={
                "start": cutoff,
                "end": datetime.now(timezone.utc),
            },
            details={
                "stale_count": stale_count,
                "total_dependencies": total,
            },
        )
