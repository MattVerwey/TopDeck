"""
Background Scheduler Service for TopDeck.

Handles periodic background tasks like automated resource discovery and SPOF monitoring.
"""

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from topdeck.common.config import settings
from topdeck.discovery.models import DiscoveryResult
from topdeck.monitoring.spof_monitor import SPOFMonitor
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class DiscoveryScheduler:
    """
    Scheduler for automated resource discovery and SPOF monitoring.

    Runs discovery tasks on a configurable interval (default: 8 hours).
    Runs SPOF monitoring on a configurable interval (default: 15 minutes).
    Only runs discovery if credentials are configured and feature is enabled.
    """

    def __init__(self):
        """Initialize the discovery scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.neo4j_client: Neo4jClient | None = None
        self.spof_monitor: SPOFMonitor | None = None
        self.last_discovery_time: datetime | None = None
        self.last_spof_scan_time: datetime | None = None
        self.discovery_in_progress = False
        self.spof_scan_in_progress = False

    def start(self) -> None:
        """Start the scheduler."""
        try:
            # Initialize Neo4j client if not already initialized
            if not self.neo4j_client:
                self.neo4j_client = Neo4jClient(
                    uri=settings.neo4j_uri,
                    username=settings.neo4j_username,
                    password=settings.neo4j_password,
                )
                self.neo4j_client.connect()
                logger.info("Connected to Neo4j for scheduled tasks")

            # Initialize SPOF monitor
            if not self.spof_monitor:
                self.spof_monitor = SPOFMonitor(
                    self.neo4j_client,
                    high_risk_threshold=settings.spof_high_risk_threshold
                )
                logger.info("Initialized SPOF monitor")

            # Add discovery job with configurable interval
            # Use seconds parameter to support sub-hour intervals
            self.scheduler.add_job(
                self._run_discovery,
                trigger=IntervalTrigger(seconds=settings.discovery_scan_interval),
                id="resource_discovery",
                name="Automated Resource Discovery",
                replace_existing=True,
                max_instances=1,  # Ensure only one discovery runs at a time
            )

            # Add SPOF monitoring job if enabled
            if settings.enable_spof_monitoring:
                self.scheduler.add_job(
                    self._run_spof_scan,
                    trigger=IntervalTrigger(seconds=settings.spof_scan_interval),
                    id="spof_monitoring",
                    name="SPOF Monitoring",
                    replace_existing=True,
                    max_instances=1,  # Ensure only one scan runs at a time
                )

            self.scheduler.start()
            discovery_interval_display = (
                f"{settings.discovery_scan_interval // 3600} hours"
                if settings.discovery_scan_interval >= 3600
                else f"{settings.discovery_scan_interval} seconds"
            )
            
            if settings.enable_spof_monitoring:
                spof_interval_display = (
                    f"{settings.spof_scan_interval // 60} minutes"
                    if settings.spof_scan_interval >= 60
                    else f"{settings.spof_scan_interval} seconds"
                )
                logger.info(
                    f"Scheduler started - Discovery: {discovery_interval_display}, "
                    f"SPOF monitoring: {spof_interval_display}"
                )
            else:
                logger.info(f"Scheduler started - Discovery: {discovery_interval_display}")

            # Run initial discovery immediately if configured
            if self._should_run_discovery():
                logger.info("Running initial discovery on startup")
                asyncio.create_task(self._run_discovery())

            # Run initial SPOF scan on startup if enabled
            if settings.enable_spof_monitoring:
                logger.info("Running initial SPOF scan on startup")
                asyncio.create_task(self._run_spof_scan())

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Discovery scheduler stopped")

        if self.neo4j_client:
            self.neo4j_client.close()
            logger.info("Closed Neo4j connection")

    def _should_run_discovery(self) -> bool:
        """
        Check if discovery should run.

        Returns:
            True if discovery is enabled and credentials are configured
        """
        # Check Azure
        if settings.enable_azure_discovery:
            if (
                settings.azure_tenant_id
                and settings.azure_client_id
                and settings.azure_client_secret
                and settings.azure_subscription_id
            ):
                return True

        # Check AWS
        if settings.enable_aws_discovery:
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                return True

        # Check GCP
        if settings.enable_gcp_discovery:
            if settings.google_application_credentials and settings.gcp_project_id:
                return True

        return False

    async def _run_discovery(self) -> None:
        """
        Run resource discovery for all enabled cloud providers.

        This is the main scheduled task that discovers resources and stores them.
        """
        if self.discovery_in_progress:
            logger.warning("Discovery already in progress, skipping this run")
            return

        if not self._should_run_discovery():
            logger.warning(
                "Discovery triggered but no valid credentials found. "
                "Please configure cloud provider credentials in .env file."
            )
            return

        self.discovery_in_progress = True
        start_time = datetime.now()

        try:
            logger.info("=" * 60)
            logger.info("Starting automated resource discovery")
            logger.info("=" * 60)

            results = {}

            # Discover Azure resources
            if settings.enable_azure_discovery and self._has_azure_credentials():
                logger.info("Discovering Azure resources...")
                try:
                    azure_result = await self._discover_azure()
                    results["azure"] = azure_result
                    logger.info(
                        f"Azure discovery completed: {azure_result.resource_count} resources"
                    )
                except Exception as e:
                    logger.error(f"Azure discovery failed: {e}", exc_info=True)

            # Discover AWS resources
            if settings.enable_aws_discovery and self._has_aws_credentials():
                logger.info("Discovering AWS resources...")
                try:
                    aws_result = await self._discover_aws()
                    results["aws"] = aws_result
                    logger.info(f"AWS discovery completed: {aws_result.resource_count} resources")
                except Exception as e:
                    logger.error(f"AWS discovery failed: {e}", exc_info=True)

            # Discover GCP resources
            if settings.enable_gcp_discovery and self._has_gcp_credentials():
                logger.info("Discovering GCP resources...")
                try:
                    gcp_result = await self._discover_gcp()
                    results["gcp"] = gcp_result
                    logger.info(f"GCP discovery completed: {gcp_result.resource_count} resources")
                except Exception as e:
                    logger.error(f"GCP discovery failed: {e}", exc_info=True)

            # Store results in Neo4j
            if results:
                await self._store_results(results)

            self.last_discovery_time = datetime.now()
            elapsed = (self.last_discovery_time - start_time).total_seconds()

            logger.info("=" * 60)
            next_run_display = (
                f"{settings.discovery_scan_interval // 3600} hours"
                if settings.discovery_scan_interval >= 3600
                else f"{settings.discovery_scan_interval} seconds"
            )
            logger.info(
                f"Automated discovery completed in {elapsed:.2f}s. "
                f"Next run in {next_run_display}."
            )
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Discovery failed: {e}", exc_info=True)
        finally:
            self.discovery_in_progress = False

    def _has_azure_credentials(self) -> bool:
        """Check if Azure credentials are configured."""
        return bool(
            settings.azure_tenant_id
            and settings.azure_client_id
            and settings.azure_client_secret
            and settings.azure_subscription_id
        )

    def _has_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured."""
        return bool(settings.aws_access_key_id and settings.aws_secret_access_key)

    def _has_gcp_credentials(self) -> bool:
        """Check if GCP credentials are configured."""
        return bool(settings.google_application_credentials and settings.gcp_project_id)

    async def _discover_azure(self) -> DiscoveryResult:
        """Discover Azure resources."""
        from azure.identity import ClientSecretCredential

        from topdeck.discovery.azure import AzureDiscoverer

        credential = ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )

        discoverer = AzureDiscoverer(
            subscription_id=settings.azure_subscription_id,
            credential=credential,
            enable_parallel=True,
            max_workers=settings.discovery_parallel_workers,
        )

        return await discoverer.discover_all_resources()

    async def _discover_aws(self) -> DiscoveryResult:
        """Discover AWS resources."""
        from topdeck.discovery.aws import AWSDiscoverer

        discoverer = AWSDiscoverer(
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
            region=settings.aws_region,
        )

        return await discoverer.discover_all_resources()

    async def _discover_gcp(self) -> DiscoveryResult:
        """Discover GCP resources."""
        from topdeck.discovery.gcp import GCPDiscoverer

        discoverer = GCPDiscoverer(
            project_id=settings.gcp_project_id,
            credentials_path=settings.google_application_credentials,
        )

        return await discoverer.discover_all_resources()

    async def _store_results(self, results: dict[str, DiscoveryResult]) -> None:
        """
        Store discovery results in Neo4j.

        Args:
            results: Dictionary mapping cloud provider to discovery result
        """
        if not self.neo4j_client:
            logger.error("Neo4j client not initialized, cannot store results")
            return

        total_stored = 0

        for cloud_provider, result in results.items():
            logger.info(f"Storing {cloud_provider.upper()} resources in Neo4j...")

            # Store resources
            for resource in result.resources:
                try:
                    neo4j_props = resource.to_neo4j_properties()
                    self.neo4j_client.upsert_resource(neo4j_props)
                    total_stored += 1
                except Exception as e:
                    logger.error(
                        f"Failed to store resource {resource.name}: {e}",
                        exc_info=True,
                    )

            # Store dependencies
            for dependency in result.dependencies:
                try:
                    self.neo4j_client.create_dependency(
                        dependency.source_id,
                        dependency.target_id,
                        dependency.to_neo4j_properties(),
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to store dependency: {e}",
                        exc_info=True,
                    )

        logger.info(f"Stored {total_stored} resources in Neo4j")

    async def _run_spof_scan(self) -> None:
        """
        Run SPOF monitoring scan.

        This is the scheduled task that scans for single points of failure.
        """
        if self.spof_scan_in_progress:
            logger.warning("SPOF scan already in progress, skipping this run")
            return

        if not self.spof_monitor:
            logger.error("SPOF monitor not initialized")
            return

        self.spof_scan_in_progress = True
        start_time = datetime.now(UTC)

        try:
            logger.info("Starting SPOF scan...")
            snapshot = self.spof_monitor.scan()
            self.last_spof_scan_time = datetime.now(UTC)
            elapsed = (self.last_spof_scan_time - start_time).total_seconds()

            logger.info(
                f"SPOF scan completed in {elapsed:.2f}s - "
                f"{snapshot.total_count} total SPOFs, "
                f"{snapshot.high_risk_count} high-risk"
            )

        except Exception as e:
            logger.error(f"SPOF scan failed: {e}", exc_info=True)
        finally:
            self.spof_scan_in_progress = False

    async def trigger_manual_discovery(self) -> dict:
        """
        Trigger a manual discovery run.

        Returns:
            Status information about the discovery run
        """
        if self.discovery_in_progress:
            return {
                "status": "already_running",
                "message": "Discovery is already in progress",
            }

        # Schedule the discovery to run immediately
        asyncio.create_task(self._run_discovery())

        return {
            "status": "scheduled",
            "message": "Discovery has been scheduled to run",
            "last_run": (
                self.last_discovery_time.isoformat() if self.last_discovery_time else None
            ),
        }

    async def trigger_manual_spof_scan(self) -> dict:
        """
        Trigger a manual SPOF scan.

        Returns:
            Status information about the scan
        """
        if self.spof_scan_in_progress:
            return {
                "status": "already_running",
                "message": "SPOF scan is already in progress",
            }

        if not self.spof_monitor:
            return {
                "status": "error",
                "message": "SPOF monitor not initialized",
            }

        # Schedule the scan to run immediately
        asyncio.create_task(self._run_spof_scan())

        return {
            "status": "scheduled",
            "message": "SPOF scan has been scheduled to run",
            "last_scan": (
                self.last_spof_scan_time.isoformat() if self.last_spof_scan_time else None
            ),
        }

    def get_status(self) -> dict:
        """
        Get scheduler status.

        Returns:
            Dictionary with scheduler status information
        """
        status = {
            "scheduler_running": self.scheduler.running if self.scheduler else False,
            "discovery": {
                "in_progress": self.discovery_in_progress,
                "last_run": (
                    self.last_discovery_time.isoformat() if self.last_discovery_time else None
                ),
                "interval_seconds": settings.discovery_scan_interval,
                "enabled_providers": {
                    "azure": settings.enable_azure_discovery and self._has_azure_credentials(),
                    "aws": settings.enable_aws_discovery and self._has_aws_credentials(),
                    "gcp": settings.enable_gcp_discovery and self._has_gcp_credentials(),
                },
            },
            "spof_monitoring": {
                "enabled": settings.enable_spof_monitoring,
                "in_progress": self.spof_scan_in_progress,
                "last_scan": (
                    self.last_spof_scan_time.isoformat() if self.last_spof_scan_time else None
                ),
                "interval_seconds": settings.spof_scan_interval,
            },
        }
        
        # Add SPOF statistics if available
        if self.spof_monitor:
            status["spof_monitoring"]["statistics"] = self.spof_monitor.get_statistics()
        
        return status


# Global scheduler instance
_scheduler: DiscoveryScheduler | None = None


def get_scheduler() -> DiscoveryScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = DiscoveryScheduler()
    return _scheduler


def start_scheduler() -> None:
    """Start the global scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler() -> None:
    """Stop the global scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
