"""
Unit tests for the discovery scheduler.
"""

from contextlib import contextmanager
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from topdeck.common.scheduler import DiscoveryScheduler, get_scheduler
from topdeck.discovery.models import DiscoveryResult


@contextmanager
def mock_scheduler_running(scheduler, is_running: bool = True):
    """
    Context manager to mock the 'running' property of a scheduler.

    This helper simplifies the complex nested patch pattern for mocking
    the scheduler's running state.

    Args:
        scheduler: The scheduler instance
        is_running: The value to return for the running property

    Example:
        >>> with mock_scheduler_running(scheduler, True):
        ...     # scheduler.scheduler.running will return True
        ...     pass
    """
    with patch.object(
        type(scheduler.scheduler), "running", property(lambda self: is_running), create=True
    ):
        yield


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    with patch("topdeck.common.scheduler.settings") as mock:
        mock.neo4j_uri = "bolt://localhost:7687"
        mock.neo4j_username = "neo4j"
        mock.neo4j_password = "password"
        mock.discovery_scan_interval = 28800  # 8 hours
        mock.discovery_parallel_workers = 5

        # Azure credentials
        mock.enable_azure_discovery = True
        mock.azure_tenant_id = "test-tenant"
        mock.azure_client_id = "test-client"
        mock.azure_client_secret = "test-secret"
        mock.azure_subscription_id = "test-subscription"

        # AWS credentials
        mock.enable_aws_discovery = False
        mock.aws_access_key_id = ""
        mock.aws_secret_access_key = ""
        mock.aws_region = "us-east-1"

        # GCP credentials
        mock.enable_gcp_discovery = False
        mock.google_application_credentials = ""
        mock.gcp_project_id = ""

        yield mock


@pytest.fixture
def scheduler(mock_settings):
    """Create a scheduler instance for testing."""
    return DiscoveryScheduler()


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    client = Mock()
    client.connect = Mock()
    client.close = Mock()
    client.upsert_resource = Mock()
    client.create_dependency = Mock()
    return client


def test_scheduler_initialization(scheduler):
    """Test that scheduler initializes correctly."""
    assert scheduler.scheduler is not None
    assert scheduler.neo4j_client is None
    assert scheduler.last_discovery_time is None
    assert scheduler.discovery_in_progress is False


def test_has_azure_credentials(scheduler):
    """Test Azure credential checking."""
    assert scheduler._has_azure_credentials() is True


def test_has_aws_credentials_false(scheduler):
    """Test AWS credential checking when not configured."""
    assert scheduler._has_aws_credentials() is False


def test_has_gcp_credentials_false(scheduler):
    """Test GCP credential checking when not configured."""
    assert scheduler._has_gcp_credentials() is False


def test_should_run_discovery_with_azure(scheduler):
    """Test that discovery should run when Azure is configured."""
    assert scheduler._should_run_discovery() is True


def test_should_run_discovery_no_credentials():
    """Test that discovery should not run without credentials."""
    with patch("topdeck.common.scheduler.settings") as mock_settings:
        mock_settings.enable_azure_discovery = False
        mock_settings.enable_aws_discovery = False
        mock_settings.enable_gcp_discovery = False

        scheduler = DiscoveryScheduler()
        assert scheduler._should_run_discovery() is False


@patch("topdeck.common.scheduler.Neo4jClient")
def test_start_scheduler(mock_neo4j, scheduler, mock_neo4j_client):
    """Test starting the scheduler."""
    mock_neo4j.return_value = mock_neo4j_client

    with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
        with patch.object(scheduler.scheduler, "start") as mock_start:
            with patch.object(scheduler, "_should_run_discovery", return_value=False):
                scheduler.start()

                # Verify Neo4j client was connected
                mock_neo4j_client.connect.assert_called_once()

                # Verify job was added with correct interval
                mock_add_job.assert_called_once()
                call_kwargs = mock_add_job.call_args[1]
                assert call_kwargs["id"] == "resource_discovery"
                assert call_kwargs["max_instances"] == 1

                # Verify scheduler was started
                mock_start.assert_called_once()


def test_stop_scheduler(scheduler, mock_neo4j_client):
    """Test stopping the scheduler."""
    scheduler.neo4j_client = mock_neo4j_client

    with mock_scheduler_running(scheduler, True):
        with patch.object(scheduler.scheduler, "shutdown") as mock_shutdown:
            scheduler.stop()

            # Verify scheduler was shutdown
            mock_shutdown.assert_called_once_with(wait=False)

            # Verify Neo4j client was closed
            mock_neo4j_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_run_discovery_already_in_progress(scheduler):
    """Test that discovery doesn't run if already in progress."""
    scheduler.discovery_in_progress = True

    await scheduler._run_discovery()

    # Should still be in progress (not reset)
    assert scheduler.discovery_in_progress is True


@pytest.mark.asyncio
async def test_run_discovery_no_credentials(scheduler):
    """Test that discovery doesn't run without credentials."""
    with patch.object(scheduler, "_should_run_discovery", return_value=False):
        await scheduler._run_discovery()

        # Should not be in progress
        assert scheduler.discovery_in_progress is False


@pytest.mark.asyncio
async def test_run_discovery_azure_success(scheduler, mock_neo4j_client):
    """Test successful Azure discovery."""
    scheduler.neo4j_client = mock_neo4j_client

    # Create mock discovery result with resources
    mock_resource = Mock()
    mock_resource.name = "test-resource"

    mock_result = DiscoveryResult(
        resources=[mock_resource],
        dependencies=[],
        applications=[],
        repositories=[],
        deployments=[],
        errors=[],
    )

    with patch.object(scheduler, "_discover_azure", return_value=mock_result) as mock_discover:
        with patch.object(scheduler, "_store_results") as mock_store:
            await scheduler._run_discovery()

            # Verify discovery was called
            mock_discover.assert_called_once()

            # Verify results were stored
            mock_store.assert_called_once()

            # Verify last discovery time was updated
            assert scheduler.last_discovery_time is not None
            assert scheduler.discovery_in_progress is False


@pytest.mark.asyncio
async def test_run_discovery_handles_errors(scheduler, mock_neo4j_client):
    """Test that discovery handles errors gracefully."""
    scheduler.neo4j_client = mock_neo4j_client

    with patch.object(scheduler, "_discover_azure", side_effect=Exception("Test error")):
        await scheduler._run_discovery()

        # Should complete and reset flag despite error
        assert scheduler.discovery_in_progress is False


@pytest.mark.asyncio
async def test_store_results(scheduler, mock_neo4j_client):
    """Test storing discovery results in Neo4j."""
    scheduler.neo4j_client = mock_neo4j_client

    # Create mock resources
    mock_resource = Mock()
    mock_resource.name = "test-resource"
    mock_resource.to_neo4j_properties = Mock(return_value={"id": "test-id"})

    # Create mock dependency
    mock_dependency = Mock()
    mock_dependency.source_id = "source-id"
    mock_dependency.target_id = "target-id"
    mock_dependency.to_neo4j_properties = Mock(return_value={})

    # Create discovery result
    mock_result = DiscoveryResult(
        resources=[mock_resource],
        dependencies=[mock_dependency],
        applications=[],
        repositories=[],
        deployments=[],
        errors=[],
    )

    results = {"azure": mock_result}

    await scheduler._store_results(results)

    # Verify resource was stored
    mock_neo4j_client.upsert_resource.assert_called_once_with({"id": "test-id"})

    # Verify dependency was stored
    mock_neo4j_client.create_dependency.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_manual_discovery_already_running(scheduler):
    """Test manual trigger when discovery is already running."""
    scheduler.discovery_in_progress = True

    result = await scheduler.trigger_manual_discovery()

    assert result["status"] == "already_running"
    assert "already in progress" in result["message"]


@pytest.mark.asyncio
async def test_trigger_manual_discovery_scheduled(scheduler):
    """Test manual trigger schedules discovery."""
    scheduler.discovery_in_progress = False

    with patch("asyncio.create_task") as mock_create_task:
        result = await scheduler.trigger_manual_discovery()

        assert result["status"] == "scheduled"
        assert "scheduled to run" in result["message"]
        mock_create_task.assert_called_once()


def test_get_status(scheduler):
    """Test getting scheduler status."""
    scheduler.discovery_in_progress = False
    scheduler.last_discovery_time = datetime(2025, 10, 21, 12, 0, 0)

    with mock_scheduler_running(scheduler, True):
        with patch.object(scheduler, "_has_azure_credentials", return_value=True):
            with patch.object(scheduler, "_has_aws_credentials", return_value=False):
                with patch.object(scheduler, "_has_gcp_credentials", return_value=False):
                    status = scheduler.get_status()

                    assert status["scheduler_running"] is True
                    assert status["discovery_in_progress"] is False
                    assert status["last_discovery_time"] == "2025-10-21T12:00:00"
                    assert status["interval_hours"] == 8  # 28800 seconds / 3600
                    assert status["enabled_providers"]["azure"] is True
                    assert status["enabled_providers"]["aws"] is False
                    assert status["enabled_providers"]["gcp"] is False


def test_get_scheduler_singleton():
    """Test that get_scheduler returns the same instance."""
    scheduler1 = get_scheduler()
    scheduler2 = get_scheduler()

    assert scheduler1 is scheduler2
