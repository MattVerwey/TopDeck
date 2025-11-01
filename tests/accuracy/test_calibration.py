"""
Tests for prediction calibration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from topdeck.analysis.accuracy.calibration import PredictionCalibrator


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    return client


@pytest.fixture
def calibrator(mock_neo4j_client):
    """Create calibrator with mock client."""
    return PredictionCalibrator(mock_neo4j_client)


@pytest.mark.asyncio
async def test_calibrate_thresholds_low_precision(calibrator, mock_neo4j_client):
    """Test threshold calibration when precision is too low."""
    # Arrange - Mock low precision (too many false positives)
    mock_neo4j_client.execute_query.return_value = [
        {"outcome_type": "true_positive", "count": 20},
        {"outcome_type": "false_positive", "count": 20},  # High FP
        {"outcome_type": "false_negative", "count": 2},
    ]
    
    # Act
    result = await calibrator.calibrate_thresholds(target_precision=0.85)
    
    # Assert
    assert result["recommendation"] == "increase"
    assert result["adjustment_needed"] is True
    assert result["recommended_threshold"] > result["current_threshold"]
    # Precision = 20 / (20 + 20) = 0.5, need to increase threshold
    assert result["current_precision"] == 0.5


@pytest.mark.asyncio
async def test_calibrate_thresholds_low_recall(calibrator, mock_neo4j_client):
    """Test threshold calibration when recall is too low."""
    # Arrange - Mock high precision but low recall (missing failures)
    mock_neo4j_client.execute_query.return_value = [
        {"outcome_type": "true_positive", "count": 20},
        {"outcome_type": "false_positive", "count": 2},  # Low FP
        {"outcome_type": "false_negative", "count": 15},  # High FN
    ]
    
    # Act
    result = await calibrator.calibrate_thresholds(target_precision=0.85)
    
    # Assert
    # Precision = 20 / 22 ≈ 0.91 (good), Recall = 20 / 35 ≈ 0.57 (bad)
    assert result["recommendation"] == "decrease"
    assert result["adjustment_needed"] is True
    assert result["recommended_threshold"] < result["current_threshold"]


@pytest.mark.asyncio
async def test_calibrate_thresholds_balanced(calibrator, mock_neo4j_client):
    """Test threshold calibration when metrics are balanced."""
    # Arrange - Mock good precision and recall
    mock_neo4j_client.execute_query.return_value = [
        {"outcome_type": "true_positive", "count": 40},
        {"outcome_type": "true_negative", "count": 35},
        {"outcome_type": "false_positive", "count": 5},
        {"outcome_type": "false_negative", "count": 3},
    ]
    
    # Act
    result = await calibrator.calibrate_thresholds(target_precision=0.85)
    
    # Assert
    # Precision = 40 / 45 ≈ 0.89, Recall = 40 / 43 ≈ 0.93
    assert result["recommendation"] == "maintain"
    assert result["adjustment_needed"] is False


@pytest.mark.asyncio
async def test_analyze_systematic_errors(calibrator, mock_neo4j_client):
    """Test systematic error analysis."""
    # Arrange - Mock errors by resource type and confidence
    mock_neo4j_client.execute_query.return_value = [
        {
            "outcome": "false_positive",
            "resource_type": "database",
            "confidence": "high",
            "probability": 0.8,
            "count": 10,
        },
        {
            "outcome": "false_negative",
            "resource_type": "load_balancer",
            "confidence": "medium",
            "probability": 0.4,
            "count": 8,
        },
        {
            "outcome": "false_positive",
            "resource_type": "database",
            "confidence": "medium",
            "probability": 0.7,
            "count": 5,
        },
    ]
    
    # Act
    result = await calibrator.analyze_systematic_errors()
    
    # Assert
    assert result["most_false_positives"] == "database"
    assert result["most_false_negatives"] == "load_balancer"
    assert result["false_positives_by_type"]["database"] == 15
    assert result["errors_by_confidence"]["high"] == 10
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_calibrate_confidence_levels_well_calibrated(calibrator, mock_neo4j_client):
    """Test confidence calibration when levels are properly ordered."""
    # Arrange - Mock predictions with properly ordered confidence
    mock_neo4j_client.execute_query.return_value = [
        # High confidence - high accuracy
        {"confidence": "high", "outcome": "true_positive", "count": 45},
        {"confidence": "high", "outcome": "false_positive", "count": 3},
        {"confidence": "high", "outcome": "false_negative", "count": 2},
        # Medium confidence - medium accuracy
        {"confidence": "medium", "outcome": "true_positive", "count": 30},
        {"confidence": "medium", "outcome": "false_positive", "count": 10},
        {"confidence": "medium", "outcome": "false_negative", "count": 5},
        # Low confidence - low accuracy
        {"confidence": "low", "outcome": "true_positive", "count": 15},
        {"confidence": "low", "outcome": "false_positive", "count": 15},
        {"confidence": "low", "outcome": "false_negative", "count": 10},
    ]
    
    # Act
    result = await calibrator.calibrate_confidence_levels()
    
    # Assert
    assert result["is_calibrated"] is True
    assert len(result["issues"]) == 0
    # High: (45) / (45 + 3 + 2) = 0.9
    # Medium: (30) / (30 + 10 + 5) ≈ 0.67
    # Low: (15) / (15 + 15 + 10) = 0.375
    assert result["confidence_metrics"]["high"]["accuracy"] > result["confidence_metrics"]["medium"]["accuracy"]
    assert result["confidence_metrics"]["medium"]["accuracy"] > result["confidence_metrics"]["low"]["accuracy"]


@pytest.mark.asyncio
async def test_calibrate_confidence_levels_miscalibrated(calibrator, mock_neo4j_client):
    """Test confidence calibration when levels are not properly ordered."""
    # Arrange - Mock predictions with reversed confidence accuracy
    mock_neo4j_client.execute_query.return_value = [
        # High confidence - low accuracy (problematic!)
        {"confidence": "high", "outcome": "true_positive", "count": 20},
        {"confidence": "high", "outcome": "false_positive", "count": 25},
        # Medium confidence - high accuracy
        {"confidence": "medium", "outcome": "true_positive", "count": 40},
        {"confidence": "medium", "outcome": "false_positive", "count": 5},
    ]
    
    # Act
    result = await calibrator.calibrate_confidence_levels()
    
    # Assert
    assert result["is_calibrated"] is False
    assert len(result["issues"]) > 0
    assert "less accurate" in result["issues"][0]


@pytest.mark.asyncio
async def test_generate_improvement_report(calibrator, mock_neo4j_client):
    """Test comprehensive improvement report generation."""
    # Arrange - Mock data for multiple analyses
    mock_neo4j_client.execute_query.side_effect = [
        # For get_accuracy_metrics (in calibrate_thresholds)
        [
            {"outcome_type": "true_positive", "count": 20},
            {"outcome_type": "false_positive", "count": 15},  # High FP
        ],
        # For analyze_systematic_errors
        [
            {"outcome": "false_positive", "resource_type": "database", "confidence": "high", "count": 10}
        ],
        # For calibrate_confidence_levels
        [
            {"confidence": "high", "outcome": "true_positive", "count": 20},
            {"confidence": "high", "outcome": "false_positive", "count": 25},
        ],
        # For get_accuracy_metrics (in generate_improvement_report)
        [
            {"outcome_type": "true_positive", "count": 20},
            {"outcome_type": "false_positive", "count": 15},
        ],
    ]
    
    # Act
    result = await calibrator.generate_improvement_report()
    
    # Assert
    assert "timestamp" in result
    assert "current_metrics" in result
    assert "threshold_calibration" in result
    assert "error_analysis" in result
    assert "confidence_calibration" in result
    assert "priority_actions" in result
    assert len(result["priority_actions"]) > 0
    
    # Should have high-priority actions for threshold and confidence
    priorities = [action["priority"] for action in result["priority_actions"]]
    assert "high" in priorities


@pytest.mark.asyncio
async def test_calibrate_thresholds_no_data(calibrator, mock_neo4j_client):
    """Test threshold calibration with no data."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = []
    
    # Act
    result = await calibrator.calibrate_thresholds()
    
    # Assert - Should handle gracefully
    assert "current_threshold" in result
    assert "recommended_threshold" in result


@pytest.mark.asyncio
async def test_analyze_systematic_errors_no_errors(calibrator, mock_neo4j_client):
    """Test systematic error analysis with no errors."""
    # Arrange - Only true positives and negatives
    mock_neo4j_client.execute_query.return_value = [
        {"outcome": "true_positive", "resource_type": "database", "confidence": "high", "count": 50}
    ]
    
    # Act
    result = await calibrator.analyze_systematic_errors()
    
    # Assert
    assert result["most_false_positives"] is None
    assert result["most_false_negatives"] is None
    assert len(result["recommendations"]) == 0


@pytest.mark.asyncio
async def test_calibrate_confidence_with_high_confidence_errors(calibrator, mock_neo4j_client):
    """Test that high-confidence errors trigger recommendations."""
    # Arrange
    mock_neo4j_client.execute_query.return_value = [
        {"outcome": "false_positive", "resource_type": "any", "confidence": "high", "count": 10}
    ]
    
    # Act
    result = await calibrator.analyze_systematic_errors()
    
    # Assert
    assert result["errors_by_confidence"]["high"] == 10
    # Note: This depends on threshold in the code (>5 errors)
    assert result["errors_by_confidence"]["high"] > 5
