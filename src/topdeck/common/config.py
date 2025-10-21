"""Application configuration using Pydantic Settings."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    app_port: int = 8000
    api_key: str = Field(default="", description="API key for authentication")
    jwt_secret: str = Field(default="", description="JWT secret key")

    # Azure Configuration
    azure_tenant_id: str = Field(default="", description="Azure tenant ID")
    azure_client_id: str = Field(default="", description="Azure client ID")
    azure_client_secret: str = Field(default="", description="Azure client secret")
    azure_subscription_id: str = Field(default="", description="Azure subscription ID")

    # Azure DevOps Configuration
    azure_devops_organization: str = Field(default="", description="Azure DevOps organization")
    azure_devops_project: str = Field(default="", description="Azure DevOps project")
    azure_devops_pat: str = Field(default="", description="Azure DevOps PAT")

    # AWS Configuration
    aws_access_key_id: str = Field(default="", description="AWS access key ID")
    aws_secret_access_key: str = Field(default="", description="AWS secret access key")
    aws_region: str = Field(default="us-east-1", description="AWS region")

    # GCP Configuration
    google_application_credentials: str = Field(
        default="", description="Path to GCP service account JSON"
    )
    gcp_project_id: str = Field(default="", description="GCP project ID")

    # GitHub Configuration
    github_token: str = Field(default="", description="GitHub personal access token")
    github_organization: str = Field(default="", description="GitHub organization")

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_username: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="", description="Neo4j password")

    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: str = Field(default="", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")

    # RabbitMQ Configuration
    rabbitmq_host: str = Field(default="localhost", description="RabbitMQ host")
    rabbitmq_port: int = Field(default=5672, description="RabbitMQ port")
    rabbitmq_username: str = Field(default="guest", description="RabbitMQ username")
    rabbitmq_password: str = Field(default="guest", description="RabbitMQ password")

    # Monitoring & Observability Configuration
    prometheus_url: str = Field(
        default="http://prometheus:9090", description="Prometheus server URL"
    )
    loki_url: str = Field(default="http://loki:3100", description="Loki server URL")
    grafana_url: str = Field(default="http://grafana:3000", description="Grafana server URL")
    azure_log_analytics_workspace_id: str = Field(
        default="", description="Azure Log Analytics workspace ID"
    )

    # Feature Flags - Multi-cloud support (can run all simultaneously)
    enable_azure_discovery: bool = Field(default=True, description="Enable Azure discovery")
    enable_aws_discovery: bool = Field(default=True, description="Enable AWS discovery")
    enable_gcp_discovery: bool = Field(default=True, description="Enable GCP discovery")
    enable_github_integration: bool = Field(default=True, description="Enable GitHub integration")
    enable_azure_devops_integration: bool = Field(
        default=True, description="Enable Azure DevOps integration"
    )
    enable_risk_analysis: bool = Field(default=True, description="Enable risk analysis")
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")

    # Discovery Configuration
    discovery_scan_interval: int = Field(
        default=28800,
        description="Discovery scan interval in seconds (default: 8 hours)",
        ge=60,  # Minimum 1 minute
    )
    discovery_parallel_workers: int = Field(
        default=5, description="Number of parallel discovery workers"
    )
    discovery_timeout: int = Field(default=300, description="Discovery timeout in seconds")

    # Cache Configuration
    cache_ttl_resources: int = Field(default=300, description="Cache TTL for resources in seconds")
    cache_ttl_risk_scores: int = Field(
        default=900, description="Cache TTL for risk scores in seconds"
    )
    cache_ttl_topology: int = Field(default=600, description="Cache TTL for topology in seconds")

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # Request Configuration
    request_timeout_seconds: int = Field(
        default=30, description="Default request timeout in seconds"
    )
    max_request_size_mb: int = Field(default=10, description="Maximum request size in MB")

    # Rate Limiting Configuration
    rate_limit_requests_per_minute: int = Field(
        default=60, description="Rate limit: requests per minute per client"
    )
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")


# Global settings instance
settings = Settings()
