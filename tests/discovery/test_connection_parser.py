"""
Tests for connection string parser.
"""

from topdeck.discovery.connection_parser import ConnectionStringParser
from topdeck.discovery.models import DependencyCategory, DependencyType


class TestConnectionStringParser:
    """Test connection string parsing functionality."""

    def test_parse_azure_sql_connection_string(self):
        """Test parsing Azure SQL connection string."""
        conn_str = (
            "Server=tcp:myserver.database.windows.net,1433;"
            "Database=mydb;User ID=myuser;Password=mypass;"
        )

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.protocol == "tcp"
        assert conn_info.host == "myserver.database.windows.net"
        assert conn_info.port == 1433
        assert conn_info.database == "mydb"
        assert conn_info.service_type == "sql"

    def test_parse_postgresql_connection_string(self):
        """Test parsing PostgreSQL connection string."""
        conn_str = "postgresql://user:password@localhost:5432/mydatabase"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.protocol == "postgresql"
        assert conn_info.host == "localhost"
        assert conn_info.port == 5432
        assert conn_info.database == "mydatabase"
        assert conn_info.username == "user"
        assert conn_info.service_type == "postgresql"

    def test_parse_mysql_connection_string(self):
        """Test parsing MySQL connection string."""
        conn_str = "mysql://admin:pass@db.example.com:3306/production"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.protocol == "mysql"
        assert conn_info.host == "db.example.com"
        assert conn_info.port == 3306
        assert conn_info.database == "production"
        assert conn_info.service_type == "mysql"

    def test_parse_redis_connection_string(self):
        """Test parsing Redis connection string."""
        conn_str = "redis://user:password@cache.example.com:6379/0"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.protocol == "redis"
        assert conn_info.host == "cache.example.com"
        assert conn_info.port == 6379
        assert conn_info.database == "0"
        assert conn_info.service_type == "redis"

    def test_parse_azure_storage_connection_string(self):
        """Test parsing Azure Storage connection string."""
        conn_str = (
            "DefaultEndpointsProtocol=https;"
            "AccountName=mystorageaccount;"
            "AccountKey=myaccountkey123=="
        )

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.protocol == "https"
        assert "mystorageaccount" in conn_info.host
        assert conn_info.port == 443
        assert conn_info.service_type == "storage"

    def test_parse_s3_endpoint(self):
        """Test parsing S3 endpoint."""
        conn_str = "https://mybucket.s3.us-west-2.amazonaws.com"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.protocol == "https"
        assert "mybucket" in conn_info.host
        assert conn_info.service_type == "storage"

    def test_parse_generic_https_endpoint(self):
        """Test parsing generic HTTPS endpoint."""
        conn_str = "https://api.example.com:8443/endpoint"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.protocol == "https"
        assert conn_info.host == "api.example.com"
        assert conn_info.port == 8443
        assert conn_info.service_type == "endpoint"

    def test_parse_generic_hostname(self):
        """Test parsing just a hostname."""
        conn_str = "myserver.example.com"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.host == "myserver.example.com"
        assert conn_info.service_type == "endpoint"

    def test_parse_invalid_connection_string(self):
        """Test parsing invalid connection string."""
        conn_str = "not-a-valid-connection-string"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        # Should return None for invalid strings
        assert conn_info is None

    def test_parse_empty_connection_string(self):
        """Test parsing empty connection string."""
        conn_info = ConnectionStringParser.parse_connection_string("")
        assert conn_info is None

        conn_info = ConnectionStringParser.parse_connection_string(None)
        assert conn_info is None

    def test_extract_host_from_connection_info(self):
        """Test extracting host from connection info."""
        conn_str = "postgresql://user:pass@mydb.database.windows.net:5432/db"
        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        host = ConnectionStringParser.extract_host_from_connection_info(conn_info)

        assert host == "mydb"  # Should extract just the first part

    def test_create_dependency_from_connection(self):
        """Test creating dependency from connection info."""
        conn_str = "postgresql://user:pass@db.example.com:5432/mydb"
        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        dep = ConnectionStringParser.create_dependency_from_connection(
            source_id="app-service-1",
            target_id="postgres-db-1",
            conn_info=conn_info,
            description="Application database connection",
        )

        assert dep.source_id == "app-service-1"
        assert dep.target_id == "postgres-db-1"
        assert dep.category == DependencyCategory.DATA
        assert dep.dependency_type == DependencyType.REQUIRED
        assert dep.strength == 0.9
        assert dep.discovered_method == "connection_string"
        assert "Application database connection" in dep.description

    def test_create_dependency_for_storage(self):
        """Test creating dependency for storage connection."""
        conn_str = (
            "DefaultEndpointsProtocol=https;" "AccountName=mystorageaccount;" "AccountKey=key123=="
        )
        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        dep = ConnectionStringParser.create_dependency_from_connection(
            source_id="app-1", target_id="storage-1", conn_info=conn_info
        )

        assert dep.category == DependencyCategory.DATA
        assert dep.discovered_method == "connection_string"

    def test_create_dependency_for_endpoint(self):
        """Test creating dependency for endpoint connection."""
        conn_str = "https://api.example.com/endpoint"
        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        dep = ConnectionStringParser.create_dependency_from_connection(
            source_id="service-1", target_id="api-1", conn_info=conn_info
        )

        assert dep.category == DependencyCategory.NETWORK
        assert dep.discovered_method == "connection_string"

    def test_parse_postgres_without_port(self):
        """Test parsing PostgreSQL connection without explicit port."""
        conn_str = "postgresql://user:pass@localhost/mydatabase"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.port == 5432  # Should use default port

    def test_parse_mysql_without_database(self):
        """Test parsing MySQL connection without database."""
        conn_str = "mysql://admin:pass@db.example.com:3306"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.host == "db.example.com"
        assert conn_info.database is None

    def test_parse_redis_with_ssl(self):
        """Test parsing Redis SSL connection."""
        conn_str = "rediss://user:password@secure-cache.example.com:6380/0"

        conn_info = ConnectionStringParser.parse_connection_string(conn_str)

        assert conn_info is not None
        assert conn_info.protocol == "redis"
        assert conn_info.service_type == "redis"
