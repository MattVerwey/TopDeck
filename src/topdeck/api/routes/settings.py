"""
Settings API endpoints.

Provides API endpoints for viewing application settings and configuration.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from topdeck import __version__
from topdeck.common.config import settings

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class FeatureFlags(BaseModel):
    """Feature flags configuration."""

    azure_discovery: bool
    aws_discovery: bool
    gcp_discovery: bool
    github_integration: bool
    azure_devops_integration: bool
    risk_analysis: bool
    monitoring: bool


class DiscoverySettings(BaseModel):
    """Discovery configuration settings."""

    scan_interval: int = Field(description="Scan interval in seconds")
    parallel_workers: int = Field(description="Number of parallel workers")
    timeout: int = Field(description="Timeout in seconds")


class CacheSettings(BaseModel):
    """Cache configuration settings."""

    ttl_resources: int = Field(description="Cache TTL for resources in seconds")
    ttl_risk_scores: int = Field(description="Cache TTL for risk scores in seconds")
    ttl_topology: int = Field(description="Cache TTL for topology in seconds")


class SecuritySettings(BaseModel):
    """Security configuration settings."""

    rbac_enabled: bool = Field(description="Role-Based Access Control enabled")
    audit_logging_enabled: bool = Field(description="Audit logging enabled")
    ssl_enabled: bool = Field(description="SSL/TLS enabled for API server")
    neo4j_encrypted: bool = Field(description="Neo4j connection encryption enabled")
    redis_ssl: bool = Field(description="Redis SSL/TLS enabled")
    rabbitmq_ssl: bool = Field(description="RabbitMQ SSL/TLS enabled")


class RateLimitSettings(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = Field(description="Rate limiting enabled")
    requests_per_minute: int = Field(description="Requests per minute per client")


class ApplicationSettings(BaseModel):
    """Complete application settings response."""

    version: str = Field(description="Application version")
    environment: str = Field(description="Current environment (development/staging/production)")
    features: FeatureFlags = Field(description="Feature flags")
    discovery: DiscoverySettings = Field(description="Discovery configuration")
    cache: CacheSettings = Field(description="Cache configuration")
    security: SecuritySettings = Field(description="Security settings")
    rate_limiting: RateLimitSettings = Field(description="Rate limiting configuration")
    integrations: dict[str, bool] = Field(description="Integration status")


class ConnectionStatus(BaseModel):
    """Connection status for external services."""

    neo4j: dict[str, str] = Field(description="Neo4j connection status")
    redis: dict[str, str] = Field(description="Redis connection status")
    rabbitmq: dict[str, str] = Field(description="RabbitMQ connection status")
    monitoring: dict[str, str] = Field(description="Monitoring integrations")


@router.get("", response_model=ApplicationSettings)
async def get_settings() -> ApplicationSettings:
    """
    Get current application settings.

    Returns comprehensive view of all configuration settings including
    feature flags, discovery settings, cache configuration, and security settings.
    """
    return ApplicationSettings(
        version=__version__,
        environment=settings.app_env,
        features=FeatureFlags(
            azure_discovery=settings.enable_azure_discovery,
            aws_discovery=settings.enable_aws_discovery,
            gcp_discovery=settings.enable_gcp_discovery,
            github_integration=settings.enable_github_integration,
            azure_devops_integration=settings.enable_azure_devops_integration,
            risk_analysis=settings.enable_risk_analysis,
            monitoring=settings.enable_monitoring,
        ),
        discovery=DiscoverySettings(
            scan_interval=settings.discovery_scan_interval,
            parallel_workers=settings.discovery_parallel_workers,
            timeout=settings.discovery_timeout,
        ),
        cache=CacheSettings(
            ttl_resources=settings.cache_ttl_resources,
            ttl_risk_scores=settings.cache_ttl_risk_scores,
            ttl_topology=settings.cache_ttl_topology,
        ),
        security=SecuritySettings(
            rbac_enabled=settings.enable_rbac,
            audit_logging_enabled=settings.enable_audit_logging,
            ssl_enabled=settings.ssl_enabled,
            neo4j_encrypted=settings.neo4j_encrypted,
            redis_ssl=settings.redis_ssl,
            rabbitmq_ssl=settings.rabbitmq_ssl,
        ),
        rate_limiting=RateLimitSettings(
            enabled=settings.rate_limit_enabled,
            requests_per_minute=settings.rate_limit_requests_per_minute,
        ),
        integrations={
            "prometheus": bool(settings.prometheus_url),
            "tempo": bool(settings.tempo_url),
            "loki": bool(settings.loki_url),
            "elasticsearch": bool(settings.elasticsearch_url),
            "azure_log_analytics": bool(settings.azure_log_analytics_workspace_id),
        },
    )


@router.get("/connections", response_model=ConnectionStatus)
async def get_connection_status() -> ConnectionStatus:
    """
    Get connection status for external services.

    Returns status and configuration details for database, cache, message queue,
    and monitoring integrations.
    """
    return ConnectionStatus(
        neo4j={
            "uri": settings.neo4j_uri,
            "encrypted": str(settings.neo4j_encrypted),
            "status": "configured",
        },
        redis={
            "host": settings.redis_host,
            "port": str(settings.redis_port),
            "ssl": str(settings.redis_ssl),
            "status": "configured",
        },
        rabbitmq={
            "host": settings.rabbitmq_host,
            "port": str(settings.rabbitmq_port),
            "ssl": str(settings.rabbitmq_ssl),
            "status": "configured",
        },
        monitoring={
            "prometheus": settings.prometheus_url or "not configured",
            "tempo": settings.tempo_url or "not configured",
            "loki": settings.loki_url or "not configured",
            "elasticsearch": settings.elasticsearch_url or "not configured",
            "azure_log_analytics": settings.azure_log_analytics_workspace_id
            or "not configured",
        },
    )


@router.get("/feature-flags", response_model=FeatureFlags)
async def get_feature_flags() -> FeatureFlags:
    """
    Get current feature flags.

    Returns the status of all feature flags controlling which capabilities
    are enabled in the application.
    """
    return FeatureFlags(
        azure_discovery=settings.enable_azure_discovery,
        aws_discovery=settings.enable_aws_discovery,
        gcp_discovery=settings.enable_gcp_discovery,
        github_integration=settings.enable_github_integration,
        azure_devops_integration=settings.enable_azure_devops_integration,
        risk_analysis=settings.enable_risk_analysis,
        monitoring=settings.enable_monitoring,
    )
