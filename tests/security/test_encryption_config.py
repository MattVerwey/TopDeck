"""
Tests for encryption configuration and security settings.
"""

import os
from unittest.mock import patch

import pytest

from topdeck.common.cache import CacheConfig
from topdeck.common.config import Settings
from topdeck.storage.neo4j_client import Neo4jClient


class TestNeo4jEncryption:
    """Test Neo4j encryption configuration."""

    def test_unencrypted_connection_default(self):
        """Test that unencrypted connection works by default."""
        client = Neo4jClient(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password",
        )

        assert client.uri == "bolt://localhost:7687"
        assert not client.encrypted

    def test_encrypted_connection_with_bolts_uri(self):
        """Test that bolt+s:// URI is recognized as encrypted."""
        client = Neo4jClient(
            uri="bolt+s://remote-host:7687",
            username="neo4j",
            password="password",
        )

        assert client.uri == "bolt+s://remote-host:7687"

    def test_encrypted_flag_upgrades_bolt_to_bolts(self):
        """Test that encrypted=True upgrades bolt:// to bolt+s://."""
        client = Neo4jClient(
            uri="bolt://remote-host:7687",
            username="neo4j",
            password="password",
            encrypted=True,
        )

        assert client.uri == "bolt+s://remote-host:7687"
        assert client.encrypted

    def test_encrypted_flag_upgrades_neo4j_to_neo4js(self):
        """Test that encrypted=True upgrades neo4j:// to neo4j+s://."""
        client = Neo4jClient(
            uri="neo4j://remote-host:7687",
            username="neo4j",
            password="password",
            encrypted=True,
        )

        assert client.uri == "neo4j+s://remote-host:7687"
        assert client.encrypted

    def test_encrypted_flag_does_not_downgrade(self):
        """Test that encrypted=False doesn't downgrade bolt+s:// URI."""
        client = Neo4jClient(
            uri="bolt+s://remote-host:7687",
            username="neo4j",
            password="password",
            encrypted=False,
        )

        # Should keep the URI as-is since it's already encrypted
        assert client.uri == "bolt+s://remote-host:7687"


class TestRedisEncryption:
    """Test Redis SSL/TLS configuration."""

    def test_unencrypted_redis_config(self):
        """Test unencrypted Redis configuration."""
        config = CacheConfig(
            host="localhost",
            port=6379,
            password="password",
            ssl=False,
        )

        assert not config.ssl
        assert config.port == 6379

    def test_encrypted_redis_config(self):
        """Test encrypted Redis configuration."""
        config = CacheConfig(
            host="remote-host",
            port=6380,
            password="password",
            ssl=True,
            ssl_cert_reqs="required",
        )

        assert config.ssl
        assert config.port == 6380
        assert config.ssl_cert_reqs == "required"

    def test_ssl_cert_reqs_options(self):
        """Test different SSL certificate verification options."""
        for cert_reqs in ["none", "optional", "required"]:
            config = CacheConfig(
                host="remote-host",
                port=6380,
                ssl=True,
                ssl_cert_reqs=cert_reqs,
            )
            assert config.ssl_cert_reqs == cert_reqs


class TestProductionSecurityValidation:
    """Test production security validation."""

    def test_production_requires_custom_secret_key(self):
        """Test that production environment requires custom secret key."""
        with pytest.raises(ValueError, match="default secret_key"):
            Settings(
                app_env="production",
                secret_key="change-this-secret-key-in-production",
            )

    def test_production_with_custom_secret_key_succeeds(self):
        """Test that production with custom secret key succeeds."""
        settings = Settings(
            app_env="production",
            secret_key="my-very-secure-secret-key-that-is-long-enough-12345",
        )

        assert settings.app_env == "production"
        assert settings.secret_key != "change-this-secret-key-in-production"

    def test_development_allows_default_secret_key(self):
        """Test that development environment allows default secret key."""
        settings = Settings(
            app_env="development",
            secret_key="change-this-secret-key-in-production",
        )

        assert settings.app_env == "development"

    def test_production_warns_about_unencrypted_neo4j(self):
        """Test that production warns about unencrypted Neo4j."""
        with pytest.warns(UserWarning, match="unencrypted Neo4j"):
            Settings(
                app_env="production",
                secret_key="my-secure-key-12345678901234567890",
                neo4j_uri="bolt://localhost:7687",
                neo4j_encrypted=False,
            )

    def test_production_warns_about_unencrypted_redis(self):
        """Test that production warns about unencrypted Redis."""
        with pytest.warns(UserWarning, match="unencrypted Redis"):
            Settings(
                app_env="production",
                secret_key="my-secure-key-12345678901234567890",
                redis_ssl=False,
            )

    def test_production_warns_about_disabled_ssl(self):
        """Test that production warns about disabled API SSL."""
        with pytest.warns(UserWarning, match="SSL disabled"):
            Settings(
                app_env="production",
                secret_key="my-secure-key-12345678901234567890",
                ssl_enabled=False,
            )

    def test_ssl_enabled_requires_certificates(self):
        """Test that SSL enabled requires certificate paths."""
        with pytest.raises(ValueError, match="ssl_keyfile"):
            Settings(
                app_env="development",
                ssl_enabled=True,
                ssl_keyfile="",
                ssl_certfile="",
            )

    def test_ssl_enabled_with_certificates_succeeds(self):
        """Test that SSL with valid certificate paths succeeds."""
        settings = Settings(
            app_env="development",
            ssl_enabled=True,
            ssl_keyfile="/path/to/key.pem",
            ssl_certfile="/path/to/cert.pem",
        )

        assert settings.ssl_enabled
        assert settings.ssl_keyfile == "/path/to/key.pem"
        assert settings.ssl_certfile == "/path/to/cert.pem"


class TestEncryptionDefaults:
    """Test encryption defaults for different environments."""

    def test_development_defaults_to_unencrypted(self):
        """Test that development environment defaults to unencrypted."""
        settings = Settings(app_env="development")

        assert not settings.neo4j_encrypted
        assert not settings.redis_ssl
        assert not settings.rabbitmq_ssl
        assert not settings.ssl_enabled

    def test_neo4j_encrypted_flag_default(self):
        """Test Neo4j encrypted flag default value."""
        settings = Settings()
        assert not settings.neo4j_encrypted

    def test_redis_ssl_flag_default(self):
        """Test Redis SSL flag default value."""
        settings = Settings()
        assert not settings.redis_ssl

    def test_rabbitmq_ssl_flag_default(self):
        """Test RabbitMQ SSL flag default value."""
        settings = Settings()
        assert not settings.rabbitmq_ssl

    def test_api_ssl_flag_default(self):
        """Test API SSL flag default value."""
        settings = Settings()
        assert not settings.ssl_enabled


class TestConfigurationFromEnv:
    """Test loading encryption configuration from environment variables."""

    @patch.dict(
        os.environ,
        {
            "NEO4J_ENCRYPTED": "true",
            "REDIS_SSL": "true",
            "RABBITMQ_SSL": "true",
            "SSL_ENABLED": "true",
            "SSL_KEYFILE": "/path/to/key.pem",
            "SSL_CERTFILE": "/path/to/cert.pem",
        },
    )
    def test_load_encryption_settings_from_env(self):
        """Test loading encryption settings from environment variables."""
        settings = Settings()

        assert settings.neo4j_encrypted
        assert settings.redis_ssl
        assert settings.rabbitmq_ssl
        assert settings.ssl_enabled
        assert settings.ssl_keyfile == "/path/to/key.pem"
        assert settings.ssl_certfile == "/path/to/cert.pem"

    @patch.dict(
        os.environ,
        {
            "NEO4J_URI": "bolt+s://encrypted-host:7687",
        },
    )
    def test_load_encrypted_neo4j_uri_from_env(self):
        """Test loading encrypted Neo4j URI from environment."""
        settings = Settings()
        assert "bolt+s://" in settings.neo4j_uri

    @patch.dict(
        os.environ,
        {
            "REDIS_SSL_CERT_REQS": "optional",
        },
    )
    def test_load_redis_ssl_cert_reqs_from_env(self):
        """Test loading Redis SSL certificate requirements from environment."""
        settings = Settings()
        assert settings.redis_ssl_cert_reqs == "optional"
