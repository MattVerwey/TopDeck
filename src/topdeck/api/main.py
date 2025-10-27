"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from topdeck import __version__
from topdeck.api.routes import discovery, integrations, monitoring, prediction, risk, topology
from topdeck.common.config import settings
from topdeck.common.errors import (
    TopDeckException,
    generic_exception_handler,
    topdeck_exception_handler,
)
from topdeck.common.health import (
    HealthCheckResponse,
    check_neo4j_health,
    check_rabbitmq_health,
    check_redis_health,
    determine_overall_status,
)
from topdeck.common.metrics import get_metrics_handler
from topdeck.common.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from topdeck.common.rate_limiter import RateLimiter, RateLimitMiddleware
from topdeck.common.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.

    Handles startup and shutdown events.
    """
    # Startup
    try:
        start_scheduler()
    except Exception as e:
        print(f"Warning: Failed to start scheduler: {e}")

    yield

    # Shutdown
    stop_scheduler()


# Create FastAPI application
app = FastAPI(
    title="TopDeck API",
    description="Multi-Cloud Integration & Risk Analysis Platform",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Register exception handlers
app.add_exception_handler(TopDeckException, topdeck_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# Add rate limiting middleware (configurable via environment)
if settings.rate_limit_enabled:
    rate_limiter = RateLimiter(requests_per_minute=settings.rate_limit_requests_per_minute)
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=rate_limiter,
        exempt_paths=["/health", "/health/detailed", "/metrics", "/", "/api/info"],
    )

# Include routers
app.include_router(topology.router)
app.include_router(monitoring.router)
app.include_router(risk.router)
app.include_router(integrations.router)
app.include_router(prediction.router)
app.include_router(discovery.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "TopDeck API",
        "version": __version__,
        "environment": settings.app_env,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/detailed", response_model=HealthCheckResponse)
async def detailed_health() -> HealthCheckResponse:
    """
    Detailed health check endpoint.

    Checks the health of all service dependencies:
    - Neo4j database
    - Redis cache
    - RabbitMQ message queue
    """
    components = {
        "neo4j": await check_neo4j_health(),
        "redis": await check_redis_health(),
        "rabbitmq": await check_rabbitmq_health(),
    }

    overall_status = determine_overall_status(components)

    return HealthCheckResponse(
        status=overall_status,
        components=components,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Exposes application metrics in Prometheus format for scraping.
    """
    return get_metrics_handler()


@app.get("/api/info")
async def info() -> dict[str, object]:
    """API information endpoint."""
    return {
        "version": __version__,
        "environment": settings.app_env,
        "features": {
            "azure_discovery": settings.enable_azure_discovery,
            "aws_discovery": settings.enable_aws_discovery,
            "gcp_discovery": settings.enable_gcp_discovery,
            "github_integration": settings.enable_github_integration,
            "azure_devops_integration": settings.enable_azure_devops_integration,
            "risk_analysis": settings.enable_risk_analysis,
            "monitoring": settings.enable_monitoring,
        },
    }
