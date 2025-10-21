"""
Background Scheduler Service for TopDeck.

Handles periodic background tasks like automated resource discovery.
"""

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from topdeck.common.config import settings
from topdeck.discovery.models import DiscoveryResult
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class DiscoveryScheduler:
    """
    Scheduler for automated resource discovery.

    Runs discovery tasks on a configurable interval (default: 8 hours).
    Only runs discovery if credentials are configured and feature is enabled.
    """

    def __init__(self):
        """Initialize the discovery scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.neo4j_client: Neo4jClient | None = None
        self.last_discovery_time: datetime | None = None
        self.discovery_in_progress = False

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
                logger.info("Connected to Neo4j for scheduled discovery")

            # Add discovery job with 8-hour interval
            # Using hours instead of seconds for the interval
            interval_hours = settings.discovery_scan_interval // 3600
            self.scheduler.add_job(
                self._run_discovery,
                trigger=IntervalTrigger(hours=interval_hours),
                id="resource_discovery",
                name="Automated Resource Discovery",
                replace_existing=True,
                max_instances=1,  # Ensure only one discovery runs at a time
            )

            self.scheduler.start()
            logger.info(f"Discovery scheduler started with {interval_hours}-hour interval")

            # Run initial discovery immediately if configured
            if self._should_run_discovery():
                logger.info("Running initial discovery on startup")
                asyncio.create_task(self._run_discovery())

        except Exception as e:
            logger.error(f"Failed to start discovery scheduler: {e}")
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
            logger.info(
                f"Automated discovery completed in {elapsed:.2f}s. "
                f"Next run in {settings.discovery_scan_interval // 3600} hours."
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

    def get_status(self) -> dict:
        """
        Get scheduler status.

        Returns:
            Dictionary with scheduler status information
        """
        return {
            "scheduler_running": self.scheduler.running if self.scheduler else False,
            "discovery_in_progress": self.discovery_in_progress,
            "last_discovery_time": (
                self.last_discovery_time.isoformat() if self.last_discovery_time else None
            ),
            "interval_hours": settings.discovery_scan_interval // 3600,
            "enabled_providers": {
                "azure": settings.enable_azure_discovery and self._has_azure_credentials(),
                "aws": settings.enable_aws_discovery and self._has_aws_credentials(),
                "gcp": settings.enable_gcp_discovery and self._has_gcp_credentials(),
            },
        }


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
