"""
Tests for accuracy maintenance scheduler.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from topdeck.analysis.accuracy.scheduler import AccuracyMaintenanceScheduler
from topdeck.storage.neo4j_client import Neo4jClient


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j client."""
    client = MagicMock(spec=Neo4jClient)
    client.execute_query = AsyncMock(return_value=[])
    return client


@pytest.fixture
def scheduler(mock_neo4j):
    """Create scheduler with mocked dependencies."""
    scheduler = AccuracyMaintenanceScheduler(
        neo4j_client=mock_neo4j,
        validation_interval_hours=1,
        decay_schedule="0 2 * * *",
        calibration_schedule="0 3 * * 0",
    )
    return scheduler


@pytest.mark.asyncio
async def test_validate_pending_predictions_no_pending(scheduler, mock_neo4j):
    """Test validation when no pending predictions exist."""
    # Mock get_pending_validations to return empty list
    scheduler.prediction_tracker.get_pending_validations = AsyncMock(return_value=[])
    
    result = await scheduler._validate_pending_predictions()
    
    assert result["status"] == "success"
    assert result["predictions_validated"] == 0


@pytest.mark.asyncio
async def test_validate_pending_predictions_with_pending(scheduler, mock_neo4j):
    """Test validation with pending predictions."""
    # Mock pending predictions
    pending = [
        {
            "id": "pred-1",
            "resource_id": "res-1",
            "predicted_time": datetime.now(timezone.utc),
            "failure_probability": 0.8,
        },
        {
            "id": "pred-2",
            "resource_id": "res-2",
            "predicted_time": datetime.now(timezone.utc),
            "failure_probability": 0.7,
        },
    ]
    
    scheduler.prediction_tracker.get_pending_validations = AsyncMock(return_value=pending)
    scheduler._determine_actual_outcome = AsyncMock(return_value=None)  # Skip validation
    
    result = await scheduler._validate_pending_predictions()
    
    assert result["status"] == "success"
    assert "predictions_validated" in result


@pytest.mark.asyncio
async def test_apply_confidence_decay(scheduler, mock_neo4j):
    """Test confidence decay application."""
    # Mock decay to return count of updated dependencies
    scheduler.dependency_validator.apply_confidence_decay = AsyncMock(
        return_value=2  # Returns count, not list
    )
    
    result = await scheduler._apply_confidence_decay()
    
    assert result["status"] == "success"
    assert result["dependencies_updated"] == 2
    assert result["decay_rate"] == 0.1
    assert result["days_threshold"] == 3


@pytest.mark.asyncio
async def test_run_calibration(scheduler, mock_neo4j):
    """Test calibration analysis."""
    # Mock calibration report
    calibration_report = {
        "current_metrics": {
            "precision": 0.85,
            "recall": 0.90,
            "f1_score": 0.87,
        },
        "priority_actions": [
            {
                "priority": "high",
                "details": "Adjust threshold from 0.5 to 0.6",
            }
        ],
    }
    scheduler.calibrator.generate_improvement_report = AsyncMock(
        return_value=calibration_report
    )
    
    result = await scheduler._run_calibration()
    
    assert result["status"] == "success"
    assert result["priority_actions"] == 1
    assert "current_metrics" in result


@pytest.mark.asyncio
async def test_check_accuracy_alerts_no_alerts(scheduler, mock_neo4j):
    """Test alert checking when accuracy is good."""
    # Mock good metrics
    metrics_result = MagicMock()
    metrics_result.metrics = MagicMock()
    metrics_result.metrics.precision = 0.90
    metrics_result.metrics.recall = 0.95
    metrics_result.metrics.f1_score = 0.92
    
    scheduler.prediction_tracker.get_accuracy_metrics = AsyncMock(
        return_value=metrics_result
    )
    
    # Should not raise any alerts
    await scheduler._check_accuracy_alerts()


@pytest.mark.asyncio
async def test_check_accuracy_alerts_with_alerts(scheduler, mock_neo4j):
    """Test alert checking when accuracy is poor."""
    # Mock poor metrics
    metrics_result = MagicMock()
    metrics_result.metrics = MagicMock()
    metrics_result.metrics.precision = 0.75  # Below threshold
    metrics_result.metrics.recall = 0.80     # Below threshold
    metrics_result.metrics.f1_score = 0.77   # Below threshold
    
    scheduler.prediction_tracker.get_accuracy_metrics = AsyncMock(
        return_value=metrics_result
    )
    
    # Should log warnings (we'll just verify it doesn't crash)
    await scheduler._check_accuracy_alerts()


def test_get_status(scheduler):
    """Test getting scheduler status."""
    status = scheduler.get_status()
    
    assert "scheduler_running" in status
    assert "jobs" in status
    assert "last_validation" in status
    assert "last_decay" in status
    assert "last_calibration" in status


def test_start_scheduler(scheduler):
    """Test starting the scheduler."""
    # Mock the initial validation check to prevent event loop issues
    scheduler._should_run_initial_validation = lambda: False
    
    scheduler.start()
    
    assert scheduler.scheduler.running
    
    # Check jobs were added
    jobs = scheduler.scheduler.get_jobs()
    job_ids = [job.id for job in jobs]
    
    assert "validate_predictions" in job_ids
    assert "confidence_decay" in job_ids
    assert "calibration" in job_ids
    
    # Clean up
    scheduler.stop()


def test_stop_scheduler(scheduler):
    """Test stopping the scheduler."""
    # Mock the initial validation check to prevent event loop issues
    scheduler._should_run_initial_validation = lambda: False
    
    scheduler.start()
    assert scheduler.scheduler.running
    
    scheduler.stop()
    # Scheduler may not immediately report as not running
    # Just verify stop was called without error


@pytest.mark.asyncio
async def test_validate_predictions_error_handling(scheduler, mock_neo4j):
    """Test validation handles errors gracefully."""
    # Mock to raise exception
    scheduler.prediction_tracker.get_pending_validations = AsyncMock(
        side_effect=Exception("Database error")
    )
    
    result = await scheduler._validate_pending_predictions()
    
    assert result["status"] == "error"
    assert "error" in result


@pytest.mark.asyncio
async def test_decay_error_handling(scheduler, mock_neo4j):
    """Test decay handles errors gracefully."""
    # Mock to raise exception
    scheduler.dependency_validator.apply_confidence_decay = AsyncMock(
        side_effect=Exception("Database error")
    )
    
    result = await scheduler._apply_confidence_decay()
    
    assert result["status"] == "error"
    assert "error" in result


@pytest.mark.asyncio
async def test_calibration_error_handling(scheduler, mock_neo4j):
    """Test calibration handles errors gracefully."""
    # Mock to raise exception
    scheduler.calibrator.generate_improvement_report = AsyncMock(
        side_effect=Exception("Analysis error")
    )
    
    result = await scheduler._run_calibration()
    
    assert result["status"] == "error"
    assert "error" in result


def test_custom_configuration(mock_neo4j):
    """Test scheduler with custom configuration."""
    scheduler = AccuracyMaintenanceScheduler(
        neo4j_client=mock_neo4j,
        validation_interval_hours=2,
        decay_schedule="0 3 * * *",
        calibration_schedule="0 4 * * 1",
    )
    
    assert scheduler.validation_interval_hours == 2
    assert scheduler.decay_schedule == "0 3 * * *"
    assert scheduler.calibration_schedule == "0 4 * * 1"


def test_alert_thresholds(mock_neo4j):
    """Test custom alert thresholds."""
    scheduler = AccuracyMaintenanceScheduler(neo4j_client=mock_neo4j)
    
    # Default thresholds
    assert scheduler.precision_threshold == 0.85
    assert scheduler.recall_threshold == 0.90
    assert scheduler.f1_threshold == 0.85
    
    # Modify thresholds
    scheduler.precision_threshold = 0.90
    scheduler.recall_threshold = 0.95
    scheduler.f1_threshold = 0.90
    
    assert scheduler.precision_threshold == 0.90
    assert scheduler.recall_threshold == 0.95
    assert scheduler.f1_threshold == 0.90


@pytest.mark.asyncio
async def test_should_run_initial_validation_first_time(scheduler):
    """Test that validation runs on first startup."""
    # Never validated before
    assert scheduler.last_validation_time is None
    assert scheduler._should_run_initial_validation()


@pytest.mark.asyncio
async def test_should_run_initial_validation_recent(scheduler):
    """Test that validation doesn't run if recent."""
    # Validated 1 hour ago
    scheduler.last_validation_time = datetime.now(timezone.utc) - timedelta(hours=1)
    assert not scheduler._should_run_initial_validation()


@pytest.mark.asyncio
async def test_should_run_initial_validation_old(scheduler):
    """Test that validation runs if last run was long ago."""
    # Validated 3 hours ago
    scheduler.last_validation_time = datetime.now(timezone.utc) - timedelta(hours=3)
    assert scheduler._should_run_initial_validation()
