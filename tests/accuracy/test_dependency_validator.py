"""
Tests for dependency validation accuracy.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from topdeck.analysis.accuracy.dependency_validator import DependencyValidator
from topdeck.analysis.accuracy.models import ValidationStatus


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    return client


@pytest.fixture
def validator(mock_neo4j_client):
    """Create dependency validator with mock client."""
    return DependencyValidator(mock_neo4j_client)


@pytest.mark.asyncio
async def test_cross_validate_validated_dependency(validator, mock_neo4j_client):
    """Test cross-validating a dependency with multiple evidence sources."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [
        {
            "confidence": 0.9,
            "evidence_sources": ["connection_string", "loki_logs", "prometheus_metrics"],
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
    ]
    
    # Act
    validation = await validator.cross_validate_dependency("source-1", "target-1")
    
    # Assert
    assert validation.source_id == "source-1"
    assert validation.target_id == "target-1"
    assert validation.detected_confidence == 0.9
    assert len(validation.evidence_sources) == 3
    assert validation.validation_status == ValidationStatus.VALIDATED
    assert validation.is_correct is True


@pytest.mark.asyncio
async def test_cross_validate_pending_dependency(validator, mock_neo4j_client):
    """Test cross-validating a dependency with single evidence source."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [
        {
            "confidence": 0.5,
            "evidence_sources": ["loki_logs"],
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
    ]
    
    # Act
    validation = await validator.cross_validate_dependency("source-2", "target-2")
    
    # Assert
    assert validation.validation_status == ValidationStatus.PENDING
    assert validation.is_correct is None  # Uncertain


@pytest.mark.asyncio
async def test_cross_validate_expired_dependency(validator, mock_neo4j_client):
    """Test cross-validating a stale dependency."""
    # Arrange
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    mock_neo4j_client.execute_query.return_value = [
        {
            "confidence": 0.8,
            "evidence_sources": ["connection_string", "loki_logs"],
            "detected_at": old_date,
            "last_seen": old_date,
        }
    ]
    
    # Act
    validation = await validator.cross_validate_dependency("source-3", "target-3")
    
    # Assert
    assert validation.validation_status == ValidationStatus.EXPIRED


@pytest.mark.asyncio
async def test_cross_validate_non_existent_dependency(validator, mock_neo4j_client):
    """Test cross-validating non-existent dependency."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = []
    
    # Act
    validation = await validator.cross_validate_dependency("source-4", "target-4")
    
    # Assert
    assert validation.detected_confidence == 0.0
    assert validation.evidence_sources == []
    assert validation.validation_status == ValidationStatus.PENDING
    assert validation.is_correct is None


@pytest.mark.asyncio
async def test_validate_stale_dependencies(validator, mock_neo4j_client):
    """Test finding stale dependencies."""
    # Arrange
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    mock_neo4j_client.execute_query.return_value = [
        {
            "source_id": "stale-source-1",
            "target_id": "stale-target-1",
            "confidence": 0.7,
            "evidence_sources": ["logs"],
            "last_seen": old_date,
        },
        {
            "source_id": "stale-source-2",
            "target_id": "stale-target-2",
            "confidence": 0.6,
            "evidence_sources": ["metrics"],
            "last_seen": old_date,
        },
    ]
    
    # Act
    stale_deps = await validator.validate_stale_dependencies(max_age_days=7)
    
    # Assert
    assert len(stale_deps) == 2
    assert all(dep.validation_status == ValidationStatus.EXPIRED for dep in stale_deps)
    assert all(dep.is_correct is False for dep in stale_deps)
    assert "Not seen since" in stale_deps[0].notes


@pytest.mark.asyncio
async def test_apply_confidence_decay(validator, mock_neo4j_client):
    """Test applying confidence decay to unconfirmed dependencies."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [{"updated_count": 15}]
    
    # Act
    updated_count = await validator.apply_confidence_decay(
        decay_rate=0.1, days_threshold=3
    )
    
    # Assert
    assert updated_count == 15
    assert mock_neo4j_client.execute_query.called
    call_args = mock_neo4j_client.execute_query.call_args
    assert "confidence * (1.0 - $decay_rate)" in call_args[0][0]


@pytest.mark.asyncio
async def test_get_dependency_accuracy_metrics(validator, mock_neo4j_client):
    """Test calculating dependency accuracy metrics."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [
        {"status": "validated", "count": 100, "avg_confidence": 0.9},
        {"status": "pending", "count": 20, "avg_confidence": 0.6},
        {"status": "stale", "count": 5, "avg_confidence": 0.4},
    ]
    
    # Act
    result = await validator.get_dependency_accuracy_metrics(time_range_days=30)
    
    # Assert
    assert result.validated_count == 100
    assert result.pending_count == 20
    assert result.details["stale_count"] == 5
    assert result.details["total_dependencies"] == 125
    
    # Validated = TP, Stale = FP
    assert result.metrics.true_positives == 100
    assert result.metrics.false_positives == 5
    # Precision = 100 / 105 ≈ 0.95
    assert abs(result.metrics.precision - 0.95) < 0.01


@pytest.mark.asyncio
async def test_confidence_decay_with_zero_rate(validator, mock_neo4j_client):
    """Test that zero decay rate doesn't change anything."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [{"updated_count": 0}]
    
    # Act
    updated_count = await validator.apply_confidence_decay(
        decay_rate=0.0, days_threshold=3
    )
    
    # Assert - zero decay rate means no updates (confidence * 1.0 = confidence)
    assert mock_neo4j_client.execute_query.called


def test_determine_correctness_high_confidence_multiple_sources(validator):
    """Test correctness determination with high confidence and multiple sources."""
    is_correct = validator._determine_correctness(
        evidence_sources=["source1", "source2", "source3"],
        confidence=0.85
    )
    assert is_correct is True


def test_determine_correctness_low_confidence_single_source(validator):
    """Test correctness determination with low confidence single source."""
    is_correct = validator._determine_correctness(
        evidence_sources=["source1"],
        confidence=0.35
    )
    assert is_correct is False


def test_determine_correctness_medium_confidence(validator):
    """Test correctness determination with medium confidence."""
    is_correct = validator._determine_correctness(
        evidence_sources=["source1"],
        confidence=0.6
    )
    assert is_correct is None  # Uncertain


def test_determine_validation_status_multiple_sources(validator):
    """Test validation status with multiple evidence sources."""
    status = validator._determine_validation_status(
        evidence_sources=["source1", "source2"],
        last_seen=datetime.now(timezone.utc).isoformat()
    )
    assert status == ValidationStatus.VALIDATED


def test_determine_validation_status_stale(validator):
    """Test validation status with stale last_seen."""
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    status = validator._determine_validation_status(
        evidence_sources=["source1"],
        last_seen=old_date
    )
    assert status == ValidationStatus.EXPIRED


def test_determine_validation_status_no_evidence(validator):
    """Test validation status with no evidence."""
    status = validator._determine_validation_status(
        evidence_sources=[],
        last_seen=None
    )
    assert status == ValidationStatus.PENDING
