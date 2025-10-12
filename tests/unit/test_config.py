"""Unit tests for configuration."""

from topdeck.common.config import Settings


def test_settings_defaults() -> None:
    """Test that settings have expected defaults."""
    settings = Settings()
    assert settings.app_env in ["development", "staging", "production"]
    assert settings.app_port == 8000
    assert settings.neo4j_uri == "bolt://localhost:7687"
    assert settings.redis_host == "localhost"
    assert settings.redis_port == 6379


def test_settings_feature_flags() -> None:
    """Test feature flag defaults."""
    settings = Settings()
    assert isinstance(settings.enable_azure_discovery, bool)
    assert isinstance(settings.enable_aws_discovery, bool)
    assert isinstance(settings.enable_gcp_discovery, bool)
