"""
Tests for prediction accuracy tracking.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from topdeck.analysis.accuracy.prediction_tracker import PredictionTracker
from topdeck.analysis.accuracy.models import PredictionOutcome


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    return client


@pytest.fixture
def tracker(mock_neo4j_client):
    """Create prediction tracker with mock client."""
    return PredictionTracker(mock_neo4j_client)


@pytest.mark.asyncio
async def test_record_prediction(tracker, mock_neo4j_client):
    """Test recording a prediction."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [{"p": {"id": "test-id"}}]
    
    # Act
    prediction_id = await tracker.record_prediction(
        resource_id="test-resource",
        failure_probability=0.85,
        time_to_failure_hours=24.0,
        confidence="high",
        metadata={"test": "data"},
    )
    
    # Assert
    assert prediction_id is not None
    assert mock_neo4j_client.execute_query.called
    call_args = mock_neo4j_client.execute_query.call_args
    assert "CREATE (p:Prediction" in call_args[0][0]
    assert call_args[0][1]["resource_id"] == "test-resource"
    assert call_args[0][1]["failure_probability"] == 0.85


@pytest.mark.asyncio
async def test_validate_prediction_true_positive(tracker, mock_neo4j_client):
    """Test validating a true positive prediction."""
    # Arrange
    prediction_data = {
        "id": "pred-123",
        "resource_id": "test-resource",
        "failure_probability": 0.85,
        "time_to_failure_hours": 24.0,
        "predicted_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # Mock get prediction
    mock_neo4j_client.execute_query.side_effect = [
        [{"p": prediction_data}],  # Get prediction
        [{"p": prediction_data}],  # Update prediction
    ]
    
    # Act
    validation = await tracker.validate_prediction(
        prediction_id="pred-123",
        actual_outcome="failed",
        notes="Test validation",
    )
    
    # Assert
    assert validation.outcome_type == PredictionOutcome.TRUE_POSITIVE
    assert validation.actual_outcome == "failed"
    assert validation.notes == "Test validation"


@pytest.mark.asyncio
async def test_validate_prediction_false_positive(tracker, mock_neo4j_client):
    """Test validating a false positive prediction."""
    # Arrange
    prediction_data = {
        "id": "pred-124",
        "resource_id": "test-resource",
        "failure_probability": 0.85,  # Predicted failure
        "predicted_at": datetime.now(timezone.utc).isoformat(),
    }
    
    mock_neo4j_client.execute_query.side_effect = [
        [{"p": prediction_data}],
        [{"p": prediction_data}],
    ]
    
    # Act
    validation = await tracker.validate_prediction(
        prediction_id="pred-124",
        actual_outcome="no_failure",  # But didn't fail
    )
    
    # Assert
    assert validation.outcome_type == PredictionOutcome.FALSE_POSITIVE


@pytest.mark.asyncio
async def test_validate_prediction_true_negative(tracker, mock_neo4j_client):
    """Test validating a true negative prediction."""
    # Arrange
    prediction_data = {
        "id": "pred-125",
        "resource_id": "test-resource",
        "failure_probability": 0.25,  # Predicted no failure
        "predicted_at": datetime.now(timezone.utc).isoformat(),
    }
    
    mock_neo4j_client.execute_query.side_effect = [
        [{"p": prediction_data}],
        [{"p": prediction_data}],
    ]
    
    # Act
    validation = await tracker.validate_prediction(
        prediction_id="pred-125",
        actual_outcome="no_failure",  # And didn't fail
    )
    
    # Assert
    assert validation.outcome_type == PredictionOutcome.TRUE_NEGATIVE


@pytest.mark.asyncio
async def test_validate_prediction_false_negative(tracker, mock_neo4j_client):
    """Test validating a false negative prediction."""
    # Arrange
    prediction_data = {
        "id": "pred-126",
        "resource_id": "test-resource",
        "failure_probability": 0.25,  # Predicted no failure
        "predicted_at": datetime.now(timezone.utc).isoformat(),
    }
    
    mock_neo4j_client.execute_query.side_effect = [
        [{"p": prediction_data}],
        [{"p": prediction_data}],
    ]
    
    # Act
    validation = await tracker.validate_prediction(
        prediction_id="pred-126",
        actual_outcome="failed",  # But did fail
    )
    
    # Assert
    assert validation.outcome_type == PredictionOutcome.FALSE_NEGATIVE


@pytest.mark.asyncio
async def test_get_accuracy_metrics(tracker, mock_neo4j_client):
    """Test calculating accuracy metrics."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [
        {"outcome_type": "true_positive", "count": 20},
        {"outcome_type": "true_negative", "count": 30},
        {"outcome_type": "false_positive", "count": 5},
        {"outcome_type": "false_negative", "count": 3},
        {"outcome_type": "pending", "count": 10},
    ]
    
    # Act
    result = await tracker.get_accuracy_metrics()
    
    # Assert
    assert result.validated_count == 58  # 20 + 30 + 5 + 3
    assert result.pending_count == 10
    assert result.metrics.true_positives == 20
    assert result.metrics.true_negatives == 30
    assert result.metrics.false_positives == 5
    assert result.metrics.false_negatives == 3
    
    # Check calculated metrics
    # Precision = TP / (TP + FP) = 20 / 25 = 0.8
    assert abs(result.metrics.precision - 0.8) < 0.01
    # Recall = TP / (TP + FN) = 20 / 23 ≈ 0.87
    assert abs(result.metrics.recall - 0.87) < 0.01
    # Accuracy = (TP + TN) / total = 50 / 58 ≈ 0.86
    assert abs(result.metrics.accuracy - 0.86) < 0.01


@pytest.mark.asyncio
async def test_get_accuracy_metrics_with_filters(tracker, mock_neo4j_client):
    """Test accuracy metrics with date and resource filters."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [
        {"outcome_type": "true_positive", "count": 10},
    ]
    
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    end_date = datetime.now(timezone.utc)
    
    # Act
    result = await tracker.get_accuracy_metrics(
        start_date=start_date,
        end_date=end_date,
        resource_id="specific-resource",
    )
    
    # Assert
    assert mock_neo4j_client.execute_query.called
    call_args = mock_neo4j_client.execute_query.call_args
    assert call_args[0][1]["resource_id"] == "specific-resource"
    assert result.details["resource_id"] == "specific-resource"


@pytest.mark.asyncio
async def test_get_pending_validations(tracker, mock_neo4j_client):
    """Test getting pending validations."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [
        {
            "p": {
                "id": "pred-1",
                "resource_id": "res-1",
                "failure_probability": 0.8,
            }
        },
        {
            "p": {
                "id": "pred-2",
                "resource_id": "res-2",
                "failure_probability": 0.7,
            }
        },
    ]
    
    # Act
    pending = await tracker.get_pending_validations(max_age_hours=72)
    
    # Assert
    assert len(pending) == 2
    assert pending[0]["id"] == "pred-1"
    assert pending[1]["id"] == "pred-2"


@pytest.mark.asyncio
async def test_prediction_not_found_raises_error(tracker, mock_neo4j_client):
    """Test that validating non-existent prediction raises error."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = []
    
    # Act & Assert
    with pytest.raises(ValueError, match="not found"):
        await tracker.validate_prediction(
            prediction_id="non-existent",
            actual_outcome="failed",
        )


@pytest.mark.asyncio
async def test_accuracy_metrics_with_no_data(tracker, mock_neo4j_client):
    """Test accuracy metrics when there's no data."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = []
    
    # Act
    result = await tracker.get_accuracy_metrics()
    
    # Assert
    assert result.validated_count == 0
    assert result.metrics.precision == 0.0
    assert result.metrics.recall == 0.0
    assert result.metrics.accuracy == 0.0
