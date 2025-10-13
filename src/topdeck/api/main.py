"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from topdeck import __version__
from topdeck.common.config import settings
from topdeck.api.routes import topology, monitoring

# Create FastAPI application
app = FastAPI(
    title="TopDeck API",
    description="Multi-Cloud Integration & Risk Analysis Platform",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topology.router)
app.include_router(monitoring.router)


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
    """Health check endpoint."""
    return {"status": "healthy"}


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
