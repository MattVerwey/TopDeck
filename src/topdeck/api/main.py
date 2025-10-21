"""FastAPI application entry point."""

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from topdeck import __version__
from topdeck.common.config import settings
from topdeck.common.middleware import RequestLoggingMiddleware, RequestIDMiddleware
from topdeck.common.rate_limiter import RateLimitMiddleware, RateLimiter
from topdeck.common.errors import (
    TopDeckException,
    topdeck_exception_handler,
    generic_exception_handler,
)
from topdeck.common.health import (
    check_neo4j_health,
    check_redis_health,
    check_rabbitmq_health,
    determine_overall_status,
    HealthCheckResponse,
)
from topdeck.common.metrics import get_metrics_handler
from topdeck.api.routes import topology, monitoring, risk, integrations

# Create FastAPI application
app = FastAPI(
    title="TopDeck API",
    description="Multi-Cloud Integration & Risk Analysis Platform",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
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
        timestamp=datetime.utcnow().isoformat(),
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
