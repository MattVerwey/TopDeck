"""
Connection string parser for discovering dependencies.

Parses connection strings from various cloud resources to identify
dependencies on databases, storage, caches, and other services.
"""

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .models import DependencyCategory, DependencyType, ResourceDependency


@dataclass
class ConnectionInfo:
    """Information extracted from a connection string."""

    protocol: str | None = None
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    service_type: str | None = None  # sql, storage, redis, etc.
    full_endpoint: str | None = None


class ConnectionStringParser:
    """
    Parser for connection strings from cloud resources.
    
    Supports parsing of:
    - SQL Server connection strings
    - PostgreSQL connection strings
    - MySQL connection strings
    - Redis connection strings
    - Azure Storage connection strings
    - HTTP/HTTPS endpoints
    """

    # Azure SQL Server patterns
    AZURE_SQL_PATTERN = re.compile(
        r"Server=tcp:([^,;]+)(?:,(\d+))?;.*Database=([^;]+)",
        re.IGNORECASE
    )
    
    # PostgreSQL connection string
    POSTGRES_PATTERN = re.compile(
        r"(?:postgres(?:ql)?://)?(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?(?:/([^?]+))?",
        re.IGNORECASE
    )
    
    # MySQL connection string
    MYSQL_PATTERN = re.compile(
        r"(?:mysql://)?(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?(?:/([^?]+))?",
        re.IGNORECASE
    )
    
    # Redis connection string
    REDIS_PATTERN = re.compile(
        r"redis(?:s)?://(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?(?:/(\d+))?",
        re.IGNORECASE
    )
    
    # Azure Storage connection string
    AZURE_STORAGE_PATTERN = re.compile(
        r"DefaultEndpointsProtocol=(https?);.*AccountName=([^;]+);.*AccountKey=([^;]+)(?:;EndpointSuffix=([^;]+))?",
        re.IGNORECASE
    )
    
    # AWS S3-style endpoint
    S3_ENDPOINT_PATTERN = re.compile(
        r"https?://([^.]+)\.s3(?:\.([^.]+))?\.amazonaws\.com",
        re.IGNORECASE
    )
    
    # Generic endpoint pattern
    ENDPOINT_PATTERN = re.compile(
        r"(https?://)?([^:/]+)(?::(\d+))?(/.*)?",
        re.IGNORECASE
    )

    @staticmethod
    def parse_connection_string(connection_string: str) -> ConnectionInfo | None:
        """
        Parse a connection string and extract connection information.
        
        Args:
            connection_string: Connection string to parse
            
        Returns:
            ConnectionInfo object or None if parsing fails
        """
        if not connection_string:
            return None
        
        # Try Azure SQL
        if "Server=tcp:" in connection_string or "Database=" in connection_string:
            return ConnectionStringParser._parse_azure_sql(connection_string)
        
        # Try PostgreSQL
        if "postgres" in connection_string.lower():
            return ConnectionStringParser._parse_postgres(connection_string)
        
        # Try MySQL
        if "mysql" in connection_string.lower():
            return ConnectionStringParser._parse_mysql(connection_string)
        
        # Try Redis
        if "redis" in connection_string.lower():
            return ConnectionStringParser._parse_redis(connection_string)
        
        # Try Azure Storage
        if "AccountName=" in connection_string and "AccountKey=" in connection_string:
            return ConnectionStringParser._parse_azure_storage(connection_string)
        
        # Try S3 endpoint
        if ".s3" in connection_string and "amazonaws.com" in connection_string:
            return ConnectionStringParser._parse_s3_endpoint(connection_string)
        
        # Try generic endpoint
        if "://" in connection_string or re.match(r"^[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$", connection_string):
            return ConnectionStringParser._parse_generic_endpoint(connection_string)
        
        return None

    @staticmethod
    def _parse_azure_sql(connection_string: str) -> ConnectionInfo | None:
        """Parse Azure SQL connection string."""
        match = ConnectionStringParser.AZURE_SQL_PATTERN.search(connection_string)
        if match:
            host = match.group(1)
            port = int(match.group(2)) if match.group(2) else 1433
            database = match.group(3)
            
            return ConnectionInfo(
                protocol="tcp",
                host=host,
                port=port,
                database=database,
                service_type="sql",
                full_endpoint=f"{host}:{port}/{database}"
            )
        return None

    @staticmethod
    def _parse_postgres(connection_string: str) -> ConnectionInfo | None:
        """Parse PostgreSQL connection string."""
        match = ConnectionStringParser.POSTGRES_PATTERN.search(connection_string)
        if match:
            username = match.group(1)
            # password = match.group(2)  # Not storing passwords
            host = match.group(3)
            port = int(match.group(4)) if match.group(4) else 5432
            database = match.group(5)
            
            return ConnectionInfo(
                protocol="postgresql",
                host=host,
                port=port,
                database=database,
                username=username,
                service_type="postgresql",
                full_endpoint=f"{host}:{port}/{database}" if database else f"{host}:{port}"
            )
        return None

    @staticmethod
    def _parse_mysql(connection_string: str) -> ConnectionInfo | None:
        """Parse MySQL connection string."""
        match = ConnectionStringParser.MYSQL_PATTERN.search(connection_string)
        if match:
            username = match.group(1)
            host = match.group(3)
            port = int(match.group(4)) if match.group(4) else 3306
            database = match.group(5)
            
            return ConnectionInfo(
                protocol="mysql",
                host=host,
                port=port,
                database=database,
                username=username,
                service_type="mysql",
                full_endpoint=f"{host}:{port}/{database}" if database else f"{host}:{port}"
            )
        return None

    @staticmethod
    def _parse_redis(connection_string: str) -> ConnectionInfo | None:
        """Parse Redis connection string."""
        match = ConnectionStringParser.REDIS_PATTERN.search(connection_string)
        if match:
            username = match.group(1)
            host = match.group(3)
            port = int(match.group(4)) if match.group(4) else 6379
            database = match.group(5)
            
            return ConnectionInfo(
                protocol="redis",
                host=host,
                port=port,
                database=database,
                username=username,
                service_type="redis",
                full_endpoint=f"{host}:{port}/{database}" if database else f"{host}:{port}"
            )
        return None

    @staticmethod
    def _parse_azure_storage(connection_string: str) -> ConnectionInfo | None:
        """Parse Azure Storage connection string."""
        match = ConnectionStringParser.AZURE_STORAGE_PATTERN.search(connection_string)
        if match:
            protocol = match.group(1)
            account_name = match.group(2)
            endpoint_suffix = match.group(4) or "core.windows.net"
            
            host = f"{account_name}.blob.{endpoint_suffix}"
            
            return ConnectionInfo(
                protocol=protocol,
                host=host,
                port=443 if protocol == "https" else 80,
                service_type="storage",
                full_endpoint=f"{protocol}://{host}"
            )
        return None

    @staticmethod
    def _parse_s3_endpoint(connection_string: str) -> ConnectionInfo | None:
        """Parse AWS S3 endpoint."""
        match = ConnectionStringParser.S3_ENDPOINT_PATTERN.search(connection_string)
        if match:
            bucket = match.group(1)
            region = match.group(2) or "us-east-1"
            
            host = f"{bucket}.s3.{region}.amazonaws.com"
            
            return ConnectionInfo(
                protocol="https",
                host=host,
                port=443,
                service_type="storage",
                full_endpoint=f"https://{host}"
            )
        return None

    @staticmethod
    def _parse_generic_endpoint(connection_string: str) -> ConnectionInfo | None:
        """Parse generic HTTP/HTTPS endpoint."""
        try:
            # Try URL parsing first
            if "://" in connection_string:
                parsed = urlparse(connection_string)
                return ConnectionInfo(
                    protocol=parsed.scheme or "https",
                    host=parsed.hostname or parsed.netloc,
                    port=parsed.port,
                    service_type="endpoint",
                    full_endpoint=connection_string
                )
            else:
                # Try regex pattern
                match = ConnectionStringParser.ENDPOINT_PATTERN.search(connection_string)
                if match:
                    protocol = match.group(1).rstrip("://") if match.group(1) else "https"
                    host = match.group(2)
                    port = int(match.group(3)) if match.group(3) else (443 if protocol == "https" else 80)
                    
                    return ConnectionInfo(
                        protocol=protocol,
                        host=host,
                        port=port,
                        service_type="endpoint",
                        full_endpoint=f"{protocol}://{host}:{port}"
                    )
        except Exception:
            pass
        
        return None

    @staticmethod
    def extract_host_from_connection_info(conn_info: ConnectionInfo) -> str | None:
        """
        Extract the primary host/server identifier from connection info.
        
        Args:
            conn_info: Connection information
            
        Returns:
            Host identifier (e.g., server name, storage account name)
        """
        if not conn_info or not conn_info.host:
            return None
        
        # Extract the primary identifier (first part before dots)
        # For Azure: myserver.database.windows.net -> myserver
        # For AWS: mybucket.s3.amazonaws.com -> mybucket
        parts = conn_info.host.split(".")
        return parts[0] if parts else None

    @staticmethod
    def create_dependency_from_connection(
        source_id: str,
        target_id: str,
        conn_info: ConnectionInfo,
        description: str | None = None
    ) -> ResourceDependency:
        """
        Create a ResourceDependency from connection information.
        
        Args:
            source_id: Source resource ID (dependent)
            target_id: Target resource ID (dependency)
            conn_info: Connection information
            description: Optional description
            
        Returns:
            ResourceDependency object
        """
        # Determine category based on service type
        category_map = {
            "sql": DependencyCategory.DATA,
            "postgresql": DependencyCategory.DATA,
            "mysql": DependencyCategory.DATA,
            "redis": DependencyCategory.DATA,
            "storage": DependencyCategory.DATA,
            "endpoint": DependencyCategory.NETWORK,
        }
        
        category = category_map.get(conn_info.service_type or "", DependencyCategory.CONFIGURATION)
        
        # Connection strings indicate strong, required dependencies
        return ResourceDependency(
            source_id=source_id,
            target_id=target_id,
            category=category,
            dependency_type=DependencyType.REQUIRED,
            strength=0.9,  # Connection strings are strong indicators
            discovered_method="connection_string",
            description=description or f"Connection to {conn_info.service_type} at {conn_info.host}"
        )
