"""
Health check endpoints for monitoring service dependencies.

Provides detailed health information about Neo4j, Redis, and RabbitMQ.
"""

from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health information for a single component."""

    status: HealthStatus
    message: str = ""
    response_time_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class HealthCheckResponse(BaseModel):
    """Overall health check response."""

    status: HealthStatus
    components: dict[str, ComponentHealth]
    timestamp: str


async def check_neo4j_health() -> ComponentHealth:
    """
    Check Neo4j database health.

    Returns:
        ComponentHealth with status and details
    """
    import time

    from topdeck.storage.neo4j_client import Neo4jClient

    start_time = time.time()
    try:
        # Try to create a client and run a simple query
        client = Neo4jClient()
        # Simple query to check connectivity
        client.driver.verify_connectivity()
        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="Neo4j is connected and responsive",
            response_time_ms=round(response_time, 2),
            details={"connected": True},
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error("neo4j_health_check_failed", error=str(e))
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"Neo4j connection failed: {str(e)}",
            response_time_ms=round(response_time, 2),
            details={"error": str(e)},
        )


async def check_redis_health() -> ComponentHealth:
    """
    Check Redis cache health.

    Returns:
        ComponentHealth with status and details
    """
    import time

    import redis

    from topdeck.common.config import settings

    start_time = time.time()
    try:
        # Create Redis client and ping
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            db=settings.redis_db,
            socket_connect_timeout=5,
        )
        client.ping()
        response_time = (time.time() - start_time) * 1000

        # Get some basic info
        info = client.info("server")

        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="Redis is connected and responsive",
            response_time_ms=round(response_time, 2),
            details={
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            },
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error("redis_health_check_failed", error=str(e))
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"Redis connection failed: {str(e)}",
            response_time_ms=round(response_time, 2),
            details={"error": str(e)},
        )


async def check_rabbitmq_health() -> ComponentHealth:
    """
    Check RabbitMQ message queue health.

    Returns:
        ComponentHealth with status and details
    """
    import time

    import pika

    from topdeck.common.config import settings

    start_time = time.time()
    try:
        # Create connection parameters
        credentials = pika.PlainCredentials(settings.rabbitmq_username, settings.rabbitmq_password)
        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=credentials,
            connection_attempts=1,
            socket_timeout=5,
        )

        # Try to connect
        connection = pika.BlockingConnection(parameters)
        connection.close()
        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="RabbitMQ is connected and responsive",
            response_time_ms=round(response_time, 2),
            details={"connected": True},
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error("rabbitmq_health_check_failed", error=str(e))
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"RabbitMQ connection failed: {str(e)}",
            response_time_ms=round(response_time, 2),
            details={"error": str(e)},
        )


def determine_overall_status(components: dict[str, ComponentHealth]) -> HealthStatus:
    """
    Determine the overall health status based on component statuses.

    Args:
        components: Dictionary of component health statuses

    Returns:
        Overall health status
    """
    statuses = [component.status for component in components.values()]

    if all(status == HealthStatus.HEALTHY for status in statuses):
        return HealthStatus.HEALTHY
    elif any(status == HealthStatus.UNHEALTHY for status in statuses):
        return HealthStatus.DEGRADED
    else:
        return HealthStatus.DEGRADED
