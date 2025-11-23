"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from topdeck import __version__
from topdeck.api.routes import (
    alerts,
    change_management,
    discovery,
    error_replay,
    integrations,
    live_diagnostics,
    load_detection,
    monitoring,
    prediction,
    reporting,
    risk,
    settings as settings_router,
    sla,
    topology,
    webhooks,
)
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
from topdeck.common.rate_limiter import RateLimiter, RedisRateLimiter, RateLimitMiddleware
import asyncio
from topdeck.common.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.

    Handles startup and shutdown events.
    """
    # Startup
    print("DEBUG: Starting application lifespan...")
    
    # Initialize Redis client for rate limiting if enabled
    redis_client = None
    if settings.rate_limit_enabled:
        try:
            import redis.asyncio as aioredis
            redis_client = aioredis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password if settings.redis_password else None,
                db=settings.redis_db,
                decode_responses=False,  # We handle encoding in rate limiter
            )
            await redis_client.ping()
            print("DEBUG: Redis connected for rate limiting")
            app.state.redis_client = redis_client
        except Exception as e:
            print(f"Warning: Failed to connect to Redis for rate limiting: {e}")
            app.state.redis_client = None
    
    try:
        print("DEBUG: About to start scheduler...")
        start_scheduler()
        print("DEBUG: Scheduler started successfully")
    except Exception as e:
        print(f"Warning: Failed to start scheduler: {e}")
    
    print("DEBUG: Lifespan startup complete, app is ready")

    yield

    # Shutdown
    print("DEBUG: Shutting down application...")
    stop_scheduler()
    print("DEBUG: Scheduler stopped")
    
    # Close Redis connection
    if redis_client:
        await redis_client.close()
        print("DEBUG: Redis connection closed")


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
    # Create rate limiter based on Redis availability
    # Redis client will be available after lifespan startup
    # Using a factory pattern to defer Redis client initialization
    
    # Define scope mapping for different endpoint types
    scope_mapping = {
        "/api/v1/topology": "topology",
        "/api/v1/risk": "risk",
        "/api/v1/monitoring": "monitoring",
        "/api/v1/prediction": "prediction",
        "/api/v1/changes": "changes",
    }
    
    # Create a lazy rate limiter that checks app.state for Redis client
    class LazyRateLimiterMiddleware(RateLimitMiddleware):
        """Rate limiter middleware that uses Redis if available, falls back to in-memory."""
        
        def __init__(self, app, **kwargs):
            # Start with in-memory limiter
            super().__init__(
                app,
                rate_limiter=RateLimiter(requests_per_minute=settings.rate_limit_requests_per_minute),
                **kwargs
            )
            self._redis_limiter = None
            self._initialized = False
            self._init_lock = asyncio.Lock()
        
        async def dispatch(self, request, call_next):
            # Initialize Redis limiter on first request if available (thread-safe)
            if not self._initialized and hasattr(request.app.state, "redis_client"):
                async with self._init_lock:
                    # Double-check after acquiring lock
                    if not self._initialized:
                        redis_client = request.app.state.redis_client
                        if redis_client and settings.rate_limit_use_redis:
                            # Set burst_size to None so RedisRateLimiter will auto-set to 2x requests_per_minute
                            burst_size = settings.rate_limit_burst_size if settings.rate_limit_burst_size > 0 else None
                            self._redis_limiter = RedisRateLimiter(
                                redis_client=redis_client,
                                requests_per_minute=settings.rate_limit_requests_per_minute,
                                burst_size=burst_size,
                            )
                            self.rate_limiter = self._redis_limiter
                            self.is_redis_limiter = True
                        self._initialized = True
            
            return await super().dispatch(request, call_next)
    
    app.add_middleware(
        LazyRateLimiterMiddleware,
        exempt_paths=["/health", "/health/detailed", "/metrics", "/", "/api/info"],
        scope_mapping=scope_mapping,
    )

# Include routers
app.include_router(topology.router)
app.include_router(monitoring.router)
app.include_router(risk.router)
app.include_router(integrations.router)
app.include_router(prediction.router)
app.include_router(discovery.router)
app.include_router(change_management.router)
app.include_router(webhooks.router)
app.include_router(error_replay.router)
app.include_router(sla.router)
app.include_router(reporting.router)
app.include_router(settings_router.router)
app.include_router(load_detection.router)
app.include_router(live_diagnostics.router)
app.include_router(alerts.router)


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
        timestamp=datetime.now(UTC).isoformat(),
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
